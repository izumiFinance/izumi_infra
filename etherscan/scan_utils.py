# -*- coding: utf-8 -*-
from typing import Dict, Set, List, Any

from izumi_infra.etherscan.constants import FILTER_SPLIT_CHAR, SCAN_CONFIG_NO_GROUP
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


def get_sorted_chain_group_config(event_scan_config_list: List[Any]) -> Dict[int, List[Any]]:
    """
    group by [chain, group] and sort by config id
    """
    event_scan_config_list_group = {}
    for scan_config in event_scan_config_list:
        if scan_config.scan_group == SCAN_CONFIG_NO_GROUP:
            event_scan_config_list_group[f'i-{scan_config.id}'] = [scan_config]
            continue

        chain_id = scan_config.contract.chain.chain_id
        scan_group_key = f'{chain_id}-{scan_config.scan_group}'
        if scan_group_key not in event_scan_config_list_group:
            event_scan_config_list_group[scan_group_key] = []
        event_scan_config_list_group[scan_group_key].append(scan_config)

    for _, config_group_list in event_scan_config_list_group.items():
        sorted(config_group_list, key=lambda x: x.id)

    return event_scan_config_list_group
