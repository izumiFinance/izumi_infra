# -*- coding: utf-8 -*-
from typing import Dict, Set

from izumi_infra.etherscan.constants import FILTER_SPLIT_CHAR
from izumi_infra.etherscan.types import EventData

from hexbytes import (
    HexBytes,
)
from eth_utils import to_checksum_address

def get_filter_set_from_str(string: str) -> Set[str]:
    return set([t.strip() for t in string.split(FILTER_SPLIT_CHAR) if t.strip()])

def dict_to_EventData(data: EventData) -> EventData:
    return EventData(
        address=to_checksum_address(data['address']),
        topics=[HexBytes(t) for t in data['topics']],
        data=HexBytes(data['data']),
        blockNumber=int(data['blockNumber'], 16),
        blockHash=HexBytes(data['blockHash']),
        transactionHash=HexBytes(data['transactionHash']),
        transactionIndex=int(data['transactionIndex'], 16),
        logIndex=int(data['logIndex'], 16),
    )
