# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from celery.app import shared_task
from celery_once import QueueOnce
from izumi_infra.etherscan.facade.auditEventFacade import audit_event_entry
from izumi_infra.etherscan.facade.auditTransFacade import audit_trans_entry
from izumi_infra.etherscan.facade.scanEntityFacade import scan_and_touch_entity

from izumi_infra.etherscan.facade.scanEventFacade import insert_contract_event_from_dict, scan_all_contract_event
from izumi_infra.etherscan.facade.scanTransFacade import scan_all_contract_transactions
from izumi_infra.utils.date_utils import PYTHON_DATE_FORMAT, dayRange

logger = logging.getLogger(__name__)

# TODO 多线程

@shared_task(base=QueueOnce, name='etherscan_contract_trans_scan_task')
def contract_trans_scan_task():
    logger.info("start etherscan contract trans scan task")
    scan_all_contract_transactions()


@shared_task(base=QueueOnce, name='etherscan_contract_event_scan_task')
def contract_event_scan_task():
    logger.info("start etherscan contract event scan task")
    scan_all_contract_event()


@shared_task(base=QueueOnce, name='etherscan_touch_unprocessed_entity_task')
def etherscan_touch_unprocessed_entity_task():
    logger.info("start etherscan touch unprocessed entity task task")
    scan_and_touch_entity()


@shared_task(base=QueueOnce, name='etherscan_audit_event_scan_task')
def etherscan_audit_event_scan_task(*args, **kwargs):
    audit_slice_hours = kwargs.get('audit_slice_hours', 24)

    startDate = kwargs.get('startDate', None)
    endDate = kwargs.get('endDate', None)
    # default audit last day
    audit_start_time_list = [datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(days=1)]
    if startDate and endDate:
        logger.info(f"audit event param: [{startDate}, {endDate})")
        start_date = datetime.strptime(startDate, PYTHON_DATE_FORMAT)
        end_date = datetime.strptime(endDate, PYTHON_DATE_FORMAT)
        audit_start_time_list = list(dayRange(start_date, end_date))

    for audit_start_time in audit_start_time_list:
        logger.info(f"start audit event day: {datetime.strftime(audit_start_time, PYTHON_DATE_FORMAT)}")
        audit_event_entry(audit_start_time, audit_slice_hours)

@shared_task(base=QueueOnce, name='etherscan_audit_trans_scan_task')
def etherscan_audit_trans_scan_task(*args, **kwargs):
    audit_slice_hours = kwargs.get('audit_slice_hours', 24)

    startDate = kwargs.get('startDate', None)
    endDate = kwargs.get('endDate', None)
    # default audit last day
    audit_start_time_list = [datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(days=1)]
    if startDate and endDate:
        logger.info(f"audit trans param: [{startDate}, {endDate})")
        start_date = datetime.strptime(startDate, PYTHON_DATE_FORMAT)
        end_date = datetime.strptime(endDate, PYTHON_DATE_FORMAT)
        audit_start_time_list = list(dayRange(start_date, end_date))

    for audit_start_time in audit_start_time_list:
        logger.info(f"start audit trans day: {datetime.strftime(audit_start_time, PYTHON_DATE_FORMAT)}")
        audit_trans_entry(audit_start_time, audit_slice_hours)

### async event
@shared_task()
def etherscan_async_event_save(scanConfigId: int, eventDataResult: str):
    logger.info(f"etherscan_async_event_save, scanConfigId: {scanConfigId}")
    insert_contract_event_from_dict(scanConfigId, eventDataResult)
