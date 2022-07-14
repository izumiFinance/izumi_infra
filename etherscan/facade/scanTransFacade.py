# -*- coding: utf-8 -*-
import logging
from typing import Dict, List, Tuple

from django.conf import settings
from django.db.utils import IntegrityError
from web3.types import TxData

from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.blockchain.context import contractHolder
from izumi_infra.etherscan.constants import FILTER_SPLIT_CHAR, ScanConfigStatusEnum, ScanTaskStatusEnum, ScanTypeEnum
from izumi_infra.etherscan.models import ContractTransaction, ContractTransactionScanTask, EtherScanConfig
from izumi_infra.etherscan.types import TransExtra, TransExtraData
from izumi_infra.utils.collection_util import chunks

logger = logging.getLogger(__name__)

def scan_all_contract_transactions() -> None:
    """
    Entry for the uniswap contract info sync from blockchain.
    """

    trans_scan_config_list = EtherScanConfig.objects.filter(
        scan_type=ScanTypeEnum.Transaction,
        status=ScanConfigStatusEnum.ENABLE
    ).all()

    # TODO 根据下面的场景加索引
    for trans_scan_config in trans_scan_config_list:
        scan_contract_transactions_by_config(trans_scan_config)


def scan_contract_transactions_by_config(trans_scan_config: ContractTransactionScanTask):
    try:
        add_trans_scan_task(trans_scan_config)
    except Exception as e:
        logger.error(f"scan_contract_transactions_by_config exception for task: {trans_scan_config}")
        logger.exception(e)

    unfinished_tasks = ContractTransactionScanTask.objects.filter(
        contract=trans_scan_config.contract,
        status=ScanTaskStatusEnum.INITIAL
    )

    for task in unfinished_tasks:
        try:
            execute_unfinished_trans_scan_task(task)
        except Exception as e:
            logger.error(f"execute_unfinished_trans_scan_task error, task: {task}")
            logger.exception(e)

def add_trans_scan_task(trans_scan_config: EtherScanConfig):
    # TODO contract status?
    trans_contract = trans_scan_config.contract
    contract_facade = contractHolder.get_facade_by_model(trans_contract)

    block_id_now = contract_facade.get_latest_block_number()
    end_block_id = block_id_now - trans_scan_config.stable_block_offset
    last_task = ContractTransactionScanTask.objects.filter(contract=trans_contract).order_by('-end_block_id').first()
    start_block_id = last_task.end_block_id if last_task else max(end_block_id - etherscan_settings.TASK_BATCH_SCAN_BLOCK, 0)

    if start_block_id >= end_block_id: return []

    block_range_partition = list(chunks(range(start_block_id, end_block_id), etherscan_settings.TASK_BATCH_SCAN_BLOCK))
    new_trans_scan_task = list(map(lambda br:  ContractTransactionScanTask(scan_config=trans_scan_config , contract=trans_contract,
                                        start_block_id=br.start, end_block_id=br.stop), block_range_partition))

    ContractTransactionScanTask.objects.bulk_create(new_trans_scan_task)
    return new_trans_scan_task

def execute_unfinished_trans_scan_task(unfinished_task :ContractTransactionScanTask) -> None:
    if unfinished_task.status != ScanTaskStatusEnum.INITIAL: return

    trans_extra = scan_trans_by_task(unfinished_task)
    is_all_success = insert_contract_transactions(unfinished_task, trans_extra)

    if is_all_success:
        unfinished_task.status = ScanTaskStatusEnum.FINISHED
        unfinished_task.save()

# TODO group chain scan
def scan_trans_by_task(unfinished_task: ContractTransactionScanTask) -> List[TransExtra]:
    contract_facade = contractHolder.get_facade_by_model(unfinished_task.contract)
    from_address_filter_list = unfinished_task.scan_config.from_address_filter_list
    to_address_filter_list = unfinished_task.scan_config.to_address_filter_list
    function_filter_list = unfinished_task.scan_config.function_filter_list

    if to_address_filter_list:
        to_address_set = set([a.strip() for a in to_address_filter_list.split(FILTER_SPLIT_CHAR) if a.strip()])
        trans = contract_facade.blockchainFacade.get_transactions_by_to_set(unfinished_task.start_block_id,
                                                                            unfinished_task.end_block_id,
                                                                            to_address_set)
    else:
        trans = contract_facade.get_contract_transactions(unfinished_task.start_block_id,
                                                          unfinished_task.end_block_id)

    if from_address_filter_list:
        from_address_set = set(map(lambda a: a.strip(), from_address_filter_list.split(FILTER_SPLIT_CHAR)))
        trans = list(filter(lambda t: t['from'] in from_address_set, trans))

    trans_extra: List[TransExtra] = []
    for t in trans:
        func_obj, _ = contract_facade.decode_trans_input(t['input'])
        trans_extra.append(TransExtra(trans=t, extra=TransExtraData(fn_name=func_obj.fn_name)))

    if function_filter_list:
        function_filter_set = set(map(lambda f: f.strip(), function_filter_list.split(FILTER_SPLIT_CHAR)))
        trans_extra = list(filter(lambda t: t['extra']['fn_name'] in function_filter_set, trans_extra))

    return trans_extra

def insert_contract_transactions(unfinished_task :ContractTransactionScanTask, transactions: List[TransExtra]) -> bool:
    max_deliver_retry = unfinished_task.scan_config.max_deliver_retry
    failed_count = 0

    for trans_extra in transactions:
        try:
            trans = trans_extra['trans']
            function_name = trans_extra['extra']['fn_name']
            trans_record = {
                'contract': unfinished_task.contract,
                'function_name': function_name,
                'block_hash': trans['blockHash'].hex(),
                'block_number': trans['blockNumber'],
                'from_address': trans['from'],
                'to_address': trans['to'],
                'transaction_hash': trans['hash'].hex(),
                'transaction_index': trans['transactionIndex'],
                'value': trans['value'],
                'input_data': trans['input'],
                'touch_count_remain': max_deliver_retry
            }
            ContractTransaction.objects.create(**trans_record)
        except IntegrityError:
            # TODO 除了约束冲突，其他情况梳理
            logger.warn(f'ignore duplicate block: {trans["blockNumber"]}, '\
                f'trans: {trans["hash"].hex()}, transIndex: {trans["transactionIndex"]}')
        except Exception as e:
            failed_count = failed_count + 1
            logger.exception(e)

    return failed_count == 0
