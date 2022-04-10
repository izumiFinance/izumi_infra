# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Dict, List, NewType, TypedDict
from eth_typing.evm import ChecksumAddress

from izumi_infra.blockchain.constants import ChainIdEnum, BaseContractABI, TokenSymbol

class ChainMeta(TypedDict):
    id: ChainIdEnum
    rpc_url: str

class ContractMeta(TypedDict):
    address: ChecksumAddress
    chainMeta: ChainMeta
    abi: BaseContractABI

class TokenMeta(ContractMeta):
    symbol: TokenSymbol
    decimal: int

class TokenInfo(TypedDict):
    chainId: int
    address: str
    symbol: str
    name: str
    decimals: int

class Erc20TokenInfo(TypedDict):
    name: str
    address: str
    symbol: str
    decimals: int

class TokenData(TypedDict):
    address: str
    symbol: str
    name: str
    price: float
    price_time: datetime

TokenConfigType = NewType('TokenConfigType', Dict[ChainIdEnum, Dict[TokenSymbol, TokenMeta]])
