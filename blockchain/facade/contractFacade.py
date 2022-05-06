# -*- coding: utf-8 -*-
import logging
from functools import reduce
import json
from typing import List, Set
import eth_event
from eth_typing.encoding import HexStr

from eth_utils import encode_hex, event_abi_to_log_topic
from web3.datastructures import AttributeDict
from web3.types import EventData, TxData
from izumi_infra.blockchain.constants import ZERO_ADDRESS
from izumi_infra.blockchain.facade import BlockchainFacade
from izumi_infra.utils.collection_util import merge_dict_in_list

logger = logging.getLogger(__name__)



class ContractFacade():
    """
    Blockchain ability implement
    """

    def __init__(self, blockchainFacadeInst: BlockchainFacade, contract_abi_json_str: str, contract_address: str) -> None:
        if not isinstance(blockchainFacadeInst, BlockchainFacade):
            logger.info("BlockchainFacade instance maybe wrong or unconnected: %s", blockchainFacadeInst)
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
        event_data = reduce(lambda i, d: {**i, **self.__get_dict_from_decode_log_data(d)}, decode_log['data'], {})

        return event_data

    def __get_dict_from_decode_log_data(self, data):
        if data['type'] != 'tuple': return {data['name']: data['value']}
        ret = {}
        for i in range(len(data['components'])):
            ret[data['components'][i]['name']] =  data['value'][i]
        return {data['name'] : ret}

    def decode_trans_input(self, input_raw_data: HexStr):
        return self.contract.decode_function_input(input_raw_data)

    def get_lastest_block_number(self):
        return self.blockchainFacade.get_lastest_block_number()

    def get_transaction_by_tx_hash(self, tx_hash: str):
        return self.blockchainFacade.get_transaction_by_tx_hash(tx_hash)
