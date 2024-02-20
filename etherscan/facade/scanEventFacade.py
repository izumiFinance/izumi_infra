# -*- coding: utf-8 -*-
import json
import logging
import time
import traceback
from concurrent.futures import wait
from typing import List

from django.db.utils import IntegrityError

from izumi_infra.blockchain.context import contractHolder
from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.etherscan.constants import (FILTER_SPLIT_CHAR,
                                             ScanConfigStatusEnum,
                                             ScanTaskStatusEnum, ScanTypeEnum)
from izumi_infra.etherscan.models import (ContractEvent, ContractEventScanTask,
                                          EtherScanConfig)
from izumi_infra.etherscan.scan_utils import (dict_to_EventData,
                                              get_filter_set_from_str,
                                              get_sorted_chain_group_config)
from izumi_infra.etherscan.types import EventExtra, EventExtraData
from izumi_infra.etherscan.utils import execute_filter_func_chain, mark_as_sync_entity
from izumi_infra.utils.collection_utils import chunks
from izumi_infra.utils.db_utils import DjangoDbConnSafeThreadPoolExecutor

logger = logging.getLogger(__name__)


def scan_all_contract_event(exclude_chains=[]) -> None:
    """
    Entry for the event info sync from blockchain.
    """

    event_scan_config_list = EtherScanConfig.objects.select_related("contract__chain").filter(
        scan_type=ScanTypeEnum.Event,
        status=ScanConfigStatusEnum.ENABLE,
    ).exclude(contract__chain_id__in=exclude_chains).all()
    event_scan_config_group = get_sorted_chain_group_config(event_scan_config_list)

    max_workers = min(etherscan_settings.EVENT_SCAN_MAX_WORKERS, len(event_scan_config_group.keys()))
    with DjangoDbConnSafeThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='InfraEventScan') as e:
        result = []
        for _, config_group_list in event_scan_config_group.items():
            r = e.submit(scan_contract_event_group, config_group_list)
            result.append(r)

        wait(result)

def scan_all_contract_event_isolate(include_chains=[]) -> None:
    """
    Entry for the event info sync from blockchain.
    """
    event_scan_config_list = EtherScanConfig.objects.select_related("contract__chain").filter(
        scan_type=ScanTypeEnum.Event,
        status=ScanConfigStatusEnum.ENABLE,
        contract__chain_id__in=include_chains
    ).all()

    max_workers = min(etherscan_settings.EVENT_SCAN_MAX_WORKERS, len(event_scan_config_list))
    with DjangoDbConnSafeThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='InfraEventScanIso') as e:
        result = []
        for event_scan_config in event_scan_config_list:
            tasks = get_scan_contract_event_by_config(event_scan_config)
            logger.info(f'put {len(tasks)} task to scan_all_contract_event_isolate for {event_scan_config}')
            for task in tasks:
                r = e.submit(execute_unfinished_event_scan_task_wrapper, task)
                result.append(r)

        wait(result)

def scan_contract_event_group(event_scan_config_group: List[EtherScanConfig]):
    for scan_config in event_scan_config_group:
        tic = time.perf_counter()

        scan_contract_event_by_config(scan_config)

        toc = time.perf_counter()
        cost = toc - tic
        if cost > etherscan_settings.EVENT_SCAN_COST_THR:
            logger.info(f"event scan {scan_config=}, cost: {cost:0.4f} s")

def get_scan_contract_event_by_config(event_scan_config: EtherScanConfig):
    try:
        add_event_scan_task(event_scan_config)
    except Exception as e:
        logger.error(f"scan_contract_event_by_config exception for task: {event_scan_config}")
        logger.exception(e)

    return ContractEventScanTask.objects.filter(
        contract=event_scan_config.contract,
        status=ScanTaskStatusEnum.INITIAL
    )

def execute_unfinished_event_scan_task_wrapper(task: ContractEventScanTask) -> None:
    try:
        execute_unfinished_event_scan_task(task)
    except Exception as e:
        logger.error(f"execute_unfinished_event_scan_task_wrapper error, task: {task}")
        logger.exception(e)
        logger.critical(f'event scan exception: {traceback.format_exc(limit=1)}')

def scan_contract_event_by_config(event_scan_config: EtherScanConfig):
    try:
        add_event_scan_task(event_scan_config)
    except Exception as e:
        logger.error(f"scan_contract_event_by_config exception for task: {event_scan_config}")
        logger.exception(e)

    unfinished_tasks = ContractEventScanTask.objects.filter(
        contract=event_scan_config.contract,
        status=ScanTaskStatusEnum.INITIAL
    )

    for task in unfinished_tasks:
        try:
            execute_unfinished_event_scan_task(task)
        except Exception as e:
            logger.error(f"execute_unfinished_event_scan_task error, task: {task}")
            logger.exception(e)
            logger.critical(f'event scan exception: {traceback.format_exc(limit=1)}')

            fallback_list = etherscan_settings.EVENT_SCAN_FALLBACK_FUNCTION_LIST
            is_continue = execute_filter_func_chain(e, fallback_list)
            if not is_continue:
                logger.info(f'trigger fallback force abort task: {task}')
                return

def add_event_scan_task(event_scan_config: EtherScanConfig):
    """
    Add scan task according to config
    """
    event_contract = event_scan_config.contract

    contract_facade = contractHolder.get_facade_by_model(event_contract)

    block_id_now = contract_facade.get_latest_block_number()
    end_block_id = block_id_now - event_scan_config.stable_block_offset
    last_task = ContractEventScanTask.objects.filter(contract=event_contract).order_by('-end_block_id').first()
    start_block_id = last_task.end_block_id if last_task else max(end_block_id - etherscan_settings.TASK_BATCH_SCAN_BLOCK, 0)

    if start_block_id >= end_block_id: return []

    block_range_partition = list(chunks(range(start_block_id, end_block_id), etherscan_settings.TASK_BATCH_SCAN_BLOCK))
    new_event_scan_task = list(map(lambda br:  ContractEventScanTask(scan_config=event_scan_config, contract=event_contract,
                                        start_block_id=br.start, end_block_id=br.stop), block_range_partition))

    ContractEventScanTask.objects.bulk_create(new_event_scan_task)
    return new_event_scan_task


def execute_unfinished_event_scan_task(unfinished_task: ContractEventScanTask) -> None:
    if unfinished_task.status != ScanTaskStatusEnum.INITIAL: return

    event_extra = scan_event_by_task(unfinished_task)
    is_all_success = insert_contract_event(unfinished_task.scan_config, event_extra)

    if is_all_success:
        unfinished_task.status = ScanTaskStatusEnum.FINISHED
        unfinished_task.save()

# TODO group chain scan
def scan_event_by_task(unfinished_task: ContractEventScanTask) -> List[EventExtra]:
    contract_facade = contractHolder.get_facade_by_model(unfinished_task.contract)
    from_address_filter_list = unfinished_task.scan_config.from_address_filter_list
    to_address_filter_list = unfinished_task.scan_config.to_address_filter_list
    topic_filter_list = unfinished_task.scan_config.topic_filter_list
    topic_filter_set = get_filter_set_from_str(topic_filter_list)
    to_address_set = get_filter_set_from_str(to_address_filter_list)

    event_logs = contract_facade.get_event_logs_by_name(unfinished_task.start_block_id,
                                    unfinished_task.end_block_id - 1, topic_filter_set, to_address_set)
    # TODO timestamp ?
    # block_numbers = set([e['blockNumber'] for e in event_logs])
    # get block by block_numbers

    event_extra = [ EventExtra(event=e, extra=EventExtraData(data=contract_facade.decode_event_log(e))) for e in event_logs ]

    # fromAddress if filter
    if from_address_filter_list:
        from_address_set = get_filter_set_from_str(from_address_filter_list)
        for ex in event_extra:
            from_address = contract_facade.get_transaction_by_tx_hash(ex['event']['transactionHash'])['from']
            ex['extra']['fromAddress'] = from_address

        event_extra = list(filter(lambda ex: ex['extra']['fromAddress'] in from_address_set, event_extra))

    return event_extra

def insert_contract_event_from_dict(scanConfigId: int, eventDataResult: str) -> bool:
    try:
        event_dict = json.loads(eventDataResult)['params']['result']
        scan_config = EtherScanConfig.objects.get(id=scanConfigId)
        contract_facade = contractHolder.get_facade_by_model(scan_config.contract)
        eventData = dict_to_EventData(event_dict)
        eventExtra = EventExtra(event=eventData, extra=EventExtraData(data=contract_facade.decode_event_log(eventData)))
        insert_contract_event(scan_config, [eventExtra])
    except Exception as e:
        logger.error(f"insert_contract_event_from_dict error, scanConfigId: {scanConfigId}, {eventDataResult}")
        logger.exception(e)

def insert_contract_event(scan_config: EtherScanConfig, event_extra: List[EventExtra]) -> bool:
    """
    Insert event logs scanned in blockchain event which topic is OrderCreated
    """
    failed_count = 0
    contract_facade = contractHolder.get_facade_by_model(scan_config.contract)
    max_deliver_retry = scan_config.max_deliver_retry

    filter_list = etherscan_settings.EVENT_FILTER_FUNCTION_LIST

    for event in event_extra:
        try:
            event_log = event['event']
            extra = event['extra']
            event_record = {
                'contract': scan_config.contract,
                'topic': contract_facade.topic_to_topic_name_mapping.get(event_log['topics'][0].hex()),
                'block_hash': event_log['blockHash'].hex(),
                'block_number': event_log['blockNumber'],
                'from_address': extra.get('fromAddress', ''),
                'address': event_log['address'],
                'transaction_hash': event_log['transactionHash'].hex(),
                'log_index': event_log['logIndex'],
                'data': json.dumps(extra['data']),
                'touch_count_remain': max_deliver_retry
            }

            is_continue = execute_filter_func_chain(event_record, filter_list)
            if not is_continue:
                logger.info(f'event is not pass filter, event: {event_record}')
                continue

            entity = ContractEvent(**event_record)
            if not etherscan_settings.EVENT_SCAN_ENABLE_ASYNC_SIGNAL:
                mark_as_sync_entity(entity)
            entity.save()
        except IntegrityError:
            logger.warn(f'ignore duplicate event, block: {event_record["block_number"]}, ' \
                        f'hash: {event_record["block_hash"]}, logIndex: {event_record["log_index"]}, topic: {event_record["topic"]}')
        except Exception as e:
            failed_count = failed_count + 1
            logger.exception(e)

    return (failed_count == 0)
