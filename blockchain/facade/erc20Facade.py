# -*- coding: utf-8 -*-

from typing import Tuple
from eth_utils import to_checksum_address
from izumi_infra.blockchain.constants import ContractInfoEnum
from izumi_infra.blockchain.models import Blockchain, Contract
from izumi_infra.blockchain.context import contractHolder
from cachetools import cached, LRUCache

from izumi_infra.blockchain.types import Erc20TokenInfo


@cached(cache=LRUCache(maxsize=1024))
def get_erc20_token_info(chain_id: int, token_addr: str) -> Erc20TokenInfo:
    blockchain = Blockchain.objects.get(chain_id=chain_id)
    tokenContract = contractHolder.get_facade_by_info(blockchain, to_checksum_address(token_addr), ContractInfoEnum.ERC20.abi)
    token_symbol = tokenContract.contract.functions.symbol().call()
    token_decimals = tokenContract.contract.functions.decimals().call()
    name = tokenContract.contract.functions.name().call()
    return Erc20TokenInfo(address=token_addr, symbol=token_symbol, decimals=token_decimals, name=name)

def get_erc20_token_balance(chain_id: int, token_addr: str, account_addr: str) -> float:
    blockchain = Blockchain.objects.get(chain_id=chain_id)
    tokenContract = contractHolder.get_facade_by_info(blockchain, to_checksum_address(token_addr), ContractInfoEnum.ERC20.abi)
    balance_decimal = tokenContract.contract.functions.balanceOf(to_checksum_address(account_addr)).call()
    token_info = get_erc20_token_info(chain_id, token_addr)

    return balance_decimal / (10 ** token_info['decimals'])
