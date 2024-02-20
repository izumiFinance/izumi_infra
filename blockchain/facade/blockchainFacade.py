# -*- coding: utf-8 -*-
from typing import List, Set, Type

from eth_typing.encoding import HexStr
from web3 import Web3
from web3.contract import Contract
from web3.middleware import geth_poa_middleware
from web3.types import TxData, TxReceipt

from izumi_infra.blockchain.conf import blockchain_settings
from izumi_infra.blockchain.constants import BlockChainVmEnum
from izumi_infra.blockchain.types import ContractMeta
from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.utils.collection_utils import chunks
from izumi_infra.utils.exceptions import NoEntriesFound
from izumi_infra.utils.web3.exception_log_middleware import rpc_exception_log_middleware


class BlockchainFacade():
    """
    Blockchain ability implement
    """

    def __init__(self, chain_symbol: str, vm_type: str, rpc_url: str, chain_id: int, gas_price_wei: int) -> None:
        self.chain_symbol = chain_symbol
        self.vm_type = vm_type
        self.rpc_url = rpc_url
        self.chain_id = chain_id
        self.gas_price_wei = gas_price_wei

        if vm_type == BlockChainVmEnum.EVM:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={'timeout': blockchain_settings.WEB3_HTTP_RPC_TIMEOUT}))
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.w3.middleware_onion.inject(rpc_exception_log_middleware, layer=0)
        else:
            raise NoEntriesFound("No matching entries for '{}'".format(chain_symbol))

    def is_connected(self) -> bool:
        return self.w3.isConnected()

    def init_contract(self, contract_address: str, abi_json_str: str) -> Type[Contract]:
        return self.w3.eth.contract(address=contract_address, abi=abi_json_str)

    def get_latest_block_number(self) -> int:
        return self.w3.eth.block_number

    def get_event_logs(self, from_block: int, to_block: int, contract_address: str, topics: List[HexStr]):
        return self.get_all_event_logs(from_block, to_block, [contract_address], topics)

    # https://docs.alchemy.com/alchemy/guides/eth_getlogs#making-a-request-to-eth-get-logs
    # A note on specifying topic filters
    def get_all_event_logs(self, from_block: int, to_block: int, contract_addr_list: List[str], topics: List[HexStr]):
        block_range_partition = list(chunks(range(from_block, to_block), etherscan_settings.ETH_MAX_SCAN_BLOCK))
        all_info = []
        if from_block == to_block: block_range_partition = [range(from_block, to_block)]
        for block_range in block_range_partition:
            event_logs = self.w3.eth.get_logs({
                'fromBlock': block_range.start,
                'toBlock': block_range.stop,
                'address': contract_addr_list,
                'topics': [topics]
            })
            all_info.extend(event_logs)

        return all_info

    def get_full_block_info_by_id(self, block_id: int):
        return self.w3.eth.get_block(block_id, full_transactions=True)

    def get_block_info_by_id(self, block_id: int):
        return self.w3.eth.get_block(block_id, full_transactions=False)

    def get_transactions_by_to_set(self, from_block: int, to_block: int, to_set: Set[str]) -> List[TxData]:
        """
        Get contract transactions
        """
        block_range = range(min(from_block, to_block), max(from_block, to_block))
        transactions = []
        for block_id in block_range:
            full_block_info = self.get_full_block_info_by_id(block_id)
            # timestamp???
            transactions.extend(list(filter(lambda t: t['to'] in to_set, full_block_info.transactions)))

        return transactions


    def get_transaction_by_tx_hash(self, tx_hash: str) -> TxData:
        return self.w3.eth.get_transaction(tx_hash)

    def build_contract_from_meta(self, contactMeta: ContractMeta) -> Contract:
        return self.w3.eth.contract(address=contactMeta['address'], abi=contactMeta['abi'])

    def build_contract(self, address: str, abi: str) -> Contract:
        return self.w3.eth.contract(address=address, abi=abi)

    def get_transaction_receipt_by_tx_hash(self, tx_hash: str) -> TxReceipt:
        return self.w3.eth.get_transaction_receipt(tx_hash)
