# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from celery.app import shared_task
from celery_once import QueueOnce
from izumi_infra.etherscan.facade.auditEventFacade import audit_event_entry
from izumi_infra.etherscan.facade.auditTransFacade import audit_trans_entry
from izumi_infra.etherscan.facade.scanEntityFacade import scan_and_touch_entity

from izumi_infra.etherscan.facade.scanEventFacade import scan_all_contract_event
from izumi_infra.etherscan.facade.scanTransFacade import scan_all_contract_transactions

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
    offset_trigger_hours = kwargs.get('offset_trigger_hours', 6)
    trigger_time = datetime.now()
    audit_start_time = trigger_time - timedelta(hours=(audit_slice_hours+offset_trigger_hours))
    logger.info("start etherscan_audit_event_scan_task at %s", trigger_time)

    audit_event_entry(audit_start_time, audit_slice_hours)

@shared_task(base=QueueOnce, name='etherscan_audit_trans_scan_task')
def etherscan_audit_trans_scan_task(*args, **kwargs):
    audit_slice_hours = kwargs.get('audit_slice_hours', 24)
    offset_trigger_hours = kwargs.get('offset_trigger_hours', 6)
    trigger_time = datetime.now()
    audit_start_time = trigger_time - timedelta(hours=(audit_slice_hours+offset_trigger_hours))
    logger.info("start etherscan_audit_trans_scan_task at %s", trigger_time)

    audit_trans_entry(audit_start_time, audit_slice_hours)
