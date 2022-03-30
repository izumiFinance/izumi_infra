# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models.query import QuerySet
from intervaltree import Interval, IntervalTree

from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.etherscan.constants import (ScanConfigAuditLevelEnum, ScanTaskStatusEnum)
from izumi_infra.etherscan.facade.scanTransFacade import scan_trans_by_task
from izumi_infra.etherscan.models import (ContractTransaction, ContractTransactionScanTask,
                                   EtherScanConfig)
from izumi_infra.utils.collection_util import chunks


logger = logging.getLogger(__name__)

def audit_trans_entry(audit_start_datetime: datetime, audit_slice_hours=24):
    """
    Entry for auditing event
    """
    audit_min = audit_slice_hours * 60
    merge_min = etherscan_settings.ETHERSCAN_AUDIT_TASK_MERGE_MINUTES
    if audit_min < merge_min or (audit_min % merge_min) != 0:
        logger.error("invalid trans audit slice range: %d min and merge slice range: %d min", audit_min, merge_min)

    start_time = audit_start_datetime.replace(minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=audit_slice_hours)
    logger.info("start audit trans: [%s, %s)", start_time, end_time)

    timestamp_range_partion = list(chunks(range(int(start_time.timestamp()), int(end_time.timestamp())), merge_min * 60))
    merge_slice_tuple_partion = list(map(lambda t: (datetime.fromtimestamp(t.start), datetime.fromtimestamp(t.stop)), timestamp_range_partion))

    for merge_slice_tuple in merge_slice_tuple_partion:
        try:
            merge_trans_scan_tasks(merge_slice_tuple[0], merge_slice_tuple[1])
        except Exception as e:
            logger.exception(e)


MERGE_TASK_STATUS_TUPLE = (ScanTaskStatusEnum.INITIAL, ScanTaskStatusEnum.FINISHED)

def merge_trans_scan_tasks(start_time: datetime, end_time: datetime) -> None:
    """
    Merge continuous success task into one task after check, archive task data.
    """

    slice_start_time = min(start_time, end_time)
    slice_end_time = max(start_time, end_time)
    audit_scan_config_group = ContractTransactionScanTask.objects.filter(
        create_time__gte=slice_start_time,
        create_time__lt=slice_end_time,
        status__in=MERGE_TASK_STATUS_TUPLE
    ).values('scan_config', 'contract').distinct()

    for scan_config_group in audit_scan_config_group:
        scan_config: EtherScanConfig = EtherScanConfig.objects.get(pk=scan_config_group['scan_config'])
        if scan_config.audit_level == ScanConfigAuditLevelEnum.DISABLE:
            continue

        audit_task_group = ContractTransactionScanTask.objects.filter(
            create_time__gte=slice_start_time,
            create_time__lt=slice_end_time,
            scan_config__pk=scan_config_group['scan_config'],
            contract__pk=scan_config_group['contract'],
            status__in=MERGE_TASK_STATUS_TUPLE
        ).order_by('end_block_id')

        if len(audit_task_group) == 0: continue

        audit_block_id_range = range(audit_task_group.first().start_block_id, audit_task_group.last().end_block_id)

        is_all_covered = check_uncover_scan_tasks(audit_task_group, audit_block_id_range)
        if not is_all_covered: continue

        is_all_undetected = check_undetected_trans(audit_task_group, audit_block_id_range)
        if not is_all_undetected: continue

        template_task: ContractTransactionScanTask = audit_task_group.first()
        merge_task = ContractTransactionScanTask(
                id=template_task.id,
                scan_config=template_task.scan_config,
                contract=template_task.contract,
                start_block_id=audit_block_id_range.start,
                end_block_id=audit_block_id_range.stop,
                status=ScanTaskStatusEnum.ARCHIVED
        )

        with transaction.atomic():
            audit_task_group.delete()
            merge_task.save()
            # force set time for auto_now and auto_now_add
            ContractTransactionScanTask.objects.filter(pk=merge_task.pk).update(create_time=slice_start_time, update_time=slice_end_time)


def check_uncover_scan_tasks(scan_tasks: QuerySet[ContractTransactionScanTask], audit_block_id_range: range) -> bool:
    """
    Check bridge_scan_tasks is continuous and valid
    """
    if len(scan_tasks) < 1: return True
    if len(scan_tasks) == 1: return scan_tasks.first().status == ScanTaskStatusEnum.FINISHED
    template_task = scan_tasks.first()
    audit_block_range = IntervalTree([Interval(audit_block_id_range.start, audit_block_id_range.stop, 'main')])
    for scan_task in scan_tasks:
        if scan_task.status != ScanTaskStatusEnum.FINISHED:
            logger.error("contain unfinished scan task: %s, abort merge", scan_task)
            return False

        audit_block_range.chop(scan_task.start_block_id, scan_task.end_block_id)

    if audit_block_range.is_empty():
        return True

    logger.error("uncover scan block id range: %s, for scan task like: %s",
                    audit_block_range, template_task)

    if not audit_block_range.is_empty() and etherscan_settings.ETHERSCAN_AUDIT_AUTO_FIX_MISSING_TASK:
        for missing_range in audit_block_range:
            missing_task = ContractTransactionScanTask(
                scan_config=template_task.scan_config,
                contract=template_task.contract,
                start_block_id=missing_range.begin,
                end_block_id=missing_range.end
            )
            missing_task.save()
            # force fix create_time
            ContractTransactionScanTask.objects.filter(pk=missing_task.id).update(create_time=template_task.create_time)

    return False


def check_undetected_trans(scan_tasks: QuerySet[ContractTransactionScanTask], audit_block_id_range: range):
    """
    Check chain side and database side transaction diff.
    Try to fix database side missing by rescan task if enable.
    """
    template_task = scan_tasks.first()
    template_task.start_block_id = audit_block_id_range.start
    template_task.end_block_id = audit_block_id_range.stop

    # TODO 很慢
    trans = scan_trans_by_task(template_task)
    if not trans: return True

    trans_hash_to_trans_dict = dict(map(lambda t: (t['trans']['hash'] .hex(), t), trans))
    detected_trans = ContractTransaction.objects.filter(
        transaction_hash__in=trans_hash_to_trans_dict.keys()
    ).values('transaction_hash').all()

    if len(detected_trans) == len(trans_hash_to_trans_dict):
        return True

    detected_trans_hash_set = set(map(lambda t: t['transaction_hash'], detected_trans))
    undetected_trans_trans_hash = set(trans_hash_to_trans_dict.keys()).difference(detected_trans_hash_set)
    logger.error("undetected trans trans hash: %s, for scan taks like: %s",
                undetected_trans_trans_hash, template_task)

    if etherscan_settings.ETHERSCAN_AUDIT_AUTO_FIX_MISSING_TASK:
        for trans_hash in undetected_trans_trans_hash:
            trans_extra = trans_hash_to_trans_dict[trans_hash]
            block_number = trans_extra['trans']['blockNumber']
            # reopen scan task
            scan_tasks.filter(
                end_block_id__gt=block_number,
                start_block_id__lte=block_number
            ).update(status=ScanTaskStatusEnum.INITIAL)

    return False
