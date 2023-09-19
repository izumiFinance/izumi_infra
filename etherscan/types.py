# -*- coding: utf-8 -*-
from typing import Dict, List, TypedDict
from eth_typing.encoding import HexStr
from eth_typing.evm import ChecksumAddress
from hexbytes import (
    HexBytes,
)
from web3.types import TxData

class EventData(TypedDict):
    address: ChecksumAddress
    topics: List[HexBytes]
    data: HexStr
    blockNumber: int
    blockHash: HexBytes
    transactionHash: HexBytes
    transactionIndex: int
    logIndex: int
    removed: bool

class EventExtraData(TypedDict):
    data: Dict
    fromAddress: ChecksumAddress
    timestamp: int

class EventExtra(TypedDict):
    event: EventData
    extra: EventExtraData


class TransExtraData(TypedDict):
    fn_name: str

class TransExtra(TypedDict):
    trans: TxData
    extra: TransExtraData

# Custom
class TokenInfo(TypedDict):
    # USD price
    price: float

class  WhiteListPoolAdditionalInfo(TypedDict):
    tokenX: str
    tokenY: str
    fee: int