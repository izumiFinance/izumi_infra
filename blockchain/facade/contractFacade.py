# -*- coding: utf-8 -*-
import json
import logging
from typing import Dict, List, Set, Tuple, Type, TypeVar

import eth_event
from eth_typing.encoding import HexStr
from eth_utils import encode_hex, event_abi_to_log_topic
from hexbytes import HexBytes
from web3.datastructures import AttributeDict
from web3.types import EventData, TxData, TxReceipt

from izumi_infra.blockchain.constants import ZERO_ADDRESS
from izumi_infra.blockchain.facade import BlockchainFacade
from izumi_infra.utils.collection_utils import merge_dict_in_list, tuple_to_typedict
from izumi_infra.utils.eth_utils import covert_decode_log_to_event

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ContractFacade():
    """
    Blockchain ability implement
    """

    def __init__(self, blockchainFacadeInst: BlockchainFacade, contract_abi_json_str: str, contract_address: str) -> None:
        if not isinstance(blockchainFacadeInst, BlockchainFacade):
            logger.info(f"BlockchainFacade instance maybe wrong or unconnected: {blockchainFacadeInst}")
            raise ValueError("not validate BlockchainFacade instance")

        self.blockchainFacade = blockchainFacadeInst
        self.abi_json_str = contract_abi_json_str
        self.contract_address = contract_address

        # TODO valid contract_address
        # zero as fake contact only use abi and blockchain ability
        if not contract_address ==  ZERO_ADDRESS:
            self.contract = self.blockchainFacade.init_contract(self.contract_address, self.abi_json_str)
        # build all event name to topic mapping
        self.topic_name_to_topic_mapping = merge_dict_in_list(ContractFacade.build_all_event_topic(self.abi_json_str))
        self.topic_to_topic_name_mapping = {v: k for k, v in self.topic_name_to_topic_mapping.items()}

        self.topic_map = eth_event.get_topic_map(json.loads(self.abi_json_str))

    def is_connected(self) -> bool:
        """
        Test web3 instance is alive, not necessary to check before operation
        """
        return self.blockchainFacade.is_connected()

    @staticmethod
    def build_all_event_topic(abi_json_str):
        event_abi_list = list(filter(lambda a: a['type'] == 'event', json.loads(abi_json_str)))
        topic_list = list(map(lambda e: { e['name'] : encode_hex(event_abi_to_log_topic({'name': e['name'], 'inputs': e['inputs']})) },
                              event_abi_list))
        return topic_list

    @staticmethod
    def build_event_topic(abi_json_str: str, topic_name) -> HexStr:
        """
        Build topic info used in scan topic which defined in abi_json_str with topic_name
        """
        event_abi = list(filter(lambda a: a['type'] == 'event' and a['name'] == topic_name, json.loads(abi_json_str)))
        if len(event_abi) != 1:
            raise ValueError("found {} event of {} from {}".format(len(event_abi), topic_name, abi_json_str))
        target_event_abi = event_abi[0]
        topic = encode_hex(event_abi_to_log_topic({'name': target_event_abi['name'], 'inputs': target_event_abi['inputs']}))
        return topic

    def get_event_logs(self, from_block: int, to_block: int, topics):
        """
        Get event by topics limit with block_id in [from_block, to_block].
        topic could be build by build_event_topic method
        """
        return self.blockchainFacade.get_event_logs(from_block, to_block, self.contract_address, topics)



    def get_event_logs_by_name(self, from_block: int, to_block: int, topic_name_list: List[str], addr_set: Set[str] = None) -> List[EventData]:
        """
        Get event by topics limit with block_id in [from_block, to_block].
        topic_name_list, default all if missing
        """
        if topic_name_list:
            topics = list(filter(lambda t: t, map(lambda t: self.topic_name_to_topic_mapping.get(t), topic_name_list)))
        else:
            topics = list(self.topic_name_to_topic_mapping.values())

        if addr_set:
            return self.blockchainFacade.get_all_event_logs(from_block, to_block, list(addr_set), topics)
        else:
            filter_contract = [] if self.contract_address.lower() == ZERO_ADDRESS else [self.contract_address]
            return self.blockchainFacade.get_all_event_logs(from_block, to_block, filter_contract, topics)

    def get_contract_transactions(self, from_block: int, to_block: int) -> List[TxData]:
        """
        Get contract transactions
        """
        block_range = range(min(from_block, to_block), max(from_block, to_block))
        transactions = []
        for block_id in block_range:
            full_block_info = self.blockchainFacade.get_full_block_info_by_id(block_id)
            transactions.extend(list(filter(lambda t: t['to'] == self.contract_address, full_block_info.transactions)))

        return transactions

    def decode_event_log(self, event_log: AttributeDict):
        decode_log = eth_event.decode_log(event_log, self.topic_map)
        event_data = covert_decode_log_to_event(decode_log)

        return event_data

    def decode_trans_input(self, input_raw_data: HexStr):
        return self.contract.decode_function_input(input_raw_data)

    def find_fn_trans_input(self, input_raw_data: HexStr, target_fn_name: str, type_class: Type[T]) -> T:
        """
        support multicall(bytes[])
        """
        input_data = self.contract.decode_function_input(input_raw_data)
        fn_name: str = input_data[0].fn_name
        input_param: Dict = input_data[1]
        if fn_name == target_fn_name:
            # type_class name should be input param name
            if len(input_param.keys()) == 1 and list(input_param.keys())[0].lower() == type_class.__name__.lower():
                return tuple_to_typedict(list(input_param.values())[0], type_class)
            return input_param
        elif fn_name.lower() == 'multicall':
            multicall_data_list = input_param['data']
            for single_call in multicall_data_list:
                result = self.find_fn_trans_input(single_call, target_fn_name, type_class)
                if result is not None: return result

        return None

    def get_latest_block_number(self):
        return self.blockchainFacade.get_latest_block_number()

    def get_transaction_by_tx_hash(self, tx_hash: str):
        return self.blockchainFacade.get_transaction_by_tx_hash(tx_hash)

    def get_events_by_tx_hash(self, tx_hash: str) -> List[Tuple[str, int, Dict]]:
        transaction_receipt = self.blockchainFacade.get_transaction_receipt_by_tx_hash(tx_hash)
        return self.decode_events_from_transaction_receipt(transaction_receipt)

    def decode_events_from_transaction_receipt(self, transaction_receipt: TxReceipt) -> List[Tuple[str, int, Dict]]:
        """
        return data: [(topicName, logIndex, event_data),]
        """
        event_list = []
        for log in transaction_receipt.get('logs', []):
            topic_key = HexBytes(log["topics"][0]).hex()
            topic_name = self.topic_to_topic_name_mapping.get(topic_key, None)
            if topic_name is None: continue
            if log['address'].lower() != self.contract_address.lower(): continue
            try:
                event_data = self.decode_event_log(log)
                event_list.append((topic_name, log['logIndex'], event_data))
            except Exception as e:
                logger.error(f'error decode: {log}')
                logger.exception(e)

        return event_list
