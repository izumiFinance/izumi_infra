# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
import time

from celery.app import shared_task
from celery_once import QueueOnce

from izumi_infra.etherscan.facade.auditEventFacade import audit_event_entry
from izumi_infra.etherscan.facade.auditTransFacade import audit_trans_entry
from izumi_infra.etherscan.facade.scanEntityFacade import scan_and_touch_entity
from izumi_infra.etherscan.facade.scanEventFacade import (
    fetch_all_contract_event_chain, insert_contract_event_from_dict, scan_all_contract_event, scan_all_contract_event_isolate, scan_contract_event_by_chain)
from izumi_infra.etherscan.facade.scanTransFacade import \
    scan_all_contract_transactions
from izumi_infra.utils.date_utils import PYTHON_DATE_FORMAT, dayRange
from izumi_infra.utils.task_utils import IzumiQueueOnce

logger = logging.getLogger(__name__)

@shared_task(base=IzumiQueueOnce, once={'log_critical': False}, name='etherscan_contract_trans_scan_task')
def contract_trans_scan_task():
    logger.info("start etherscan contract trans scan task")
    scan_all_contract_transactions()


@shared_task(base=IzumiQueueOnce, once={'log_critical': False}, name='etherscan_contract_event_scan_task')
def contract_event_scan_task(*args, **kwargs):
    exclude_chains = kwargs.get('exclude_chains', [])
    logger.info(f"start etherscan contract event scan task, {exclude_chains=}")
    scan_all_contract_event(exclude_chains)

@shared_task(base=IzumiQueueOnce, once={'log_critical': False}, name='etherscan_contract_event_scan_task_isolate')
def contract_event_scan_task_isolate(*args, **kwargs):
    include_chains = kwargs.get('include_chains', [])
    logger.info(f"start etherscan contract event scan task isolate, {include_chains=}")
    scan_all_contract_event_isolate(include_chains)

@shared_task(base=IzumiQueueOnce, name='etherscan_touch_unprocessed_entity_task')
def etherscan_touch_unprocessed_entity_task():
    logger.info("start etherscan touch unprocessed entity task task")
    scan_and_touch_entity()


@shared_task(base=IzumiQueueOnce, once={'log_critical': False}, name='etherscan_audit_event_scan_task')
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

@shared_task(base=IzumiQueueOnce, once={'log_critical': False}, name='etherscan_audit_trans_scan_task')
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

# default priority may set lower than 10, avoid busy scan task use out of worker
@shared_task(priority=10, base=IzumiQueueOnce, once={'log_critical': False, 'timeout': 60 * 60}, name='contract_event_of_chain_scan_task')
def contract_event_of_chain_scan_task(chain_id: int) -> None:
    logger.info(f"start contract event of {chain_id=} task")
    tic = time.perf_counter()
    # TODO force time out exit? celery soft_time_limit not working when -P thread mode
    scan_contract_event_by_chain(chain_id)
    cost = time.perf_counter() - tic
    logger.info(f"end contract event of {chain_id=} task, cost: {cost:0.4f} s")

@shared_task(name='contract_event_scan_dispatch_task')
def contract_event_scan_dispatch_task(exclude_chains=[]) -> None:
    """
    start async task for event info sync from blockchain by chain dimension.
    """
    logger.info("start contract event scan task dispatcher")
    chain_set = fetch_all_contract_event_chain(exclude_chains)
    for chain_id in chain_set:
        try:
            contract_event_of_chain_scan_task.delay(chain_id)
        except Exception as e:
            logger.error(f'fail dispatch chain of {chain_id=}')
            logger.exception(e)
