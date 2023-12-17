# -*- coding: utf-8 -*-
import json
from functools import reduce
from typing import Dict

import eth_event
from cachetools import LRUCache, cached
from web3.types import LogReceipt

from izumi_infra.utils.abi_helper import get_abi_selector_to_signature


def addr_identity(chainId: int, addr: str) -> str:
    return f"{chainId}-{addr.lower()}"

def __get_dict_from_decode_log_data(data):
    if data['type'] != 'tuple': return {data['name']: data['value']}
    ret = {}
    for i in range(len(data['components'])):
        ret[data['components'][i]['name']] =  data['value'][i]
    return {data['name'] : ret}

@cached(cache=LRUCache(maxsize=512))
def get_event_signature(abi_str: str, event_name: str) -> str:
    sig_to_event = get_abi_selector_to_signature(abi_str)['event']
    for k, v in sig_to_event.items():
        if v.startswith(event_name): return k

def covert_decode_log_to_event(decode_log: Dict) -> Dict:
    """
    convert data decode by eth_event.decode_log to normal event dict
    """
    return reduce(lambda i, d: {**i, **__get_dict_from_decode_log_data(d)}, decode_log['data'], {})

@cached(cache=LRUCache(maxsize=512))
def build_logs_event_decode_tool(abi_str: str, event_name: str):
    event_sig = get_event_signature(abi_str, event_name)
    topic_map = eth_event.get_topic_map(json.loads(abi_str))

    def _selector(topic_sig: str) -> bool:
        return event_sig == topic_sig

    def _decode(log_receipt: LogReceipt):
        decode_log = eth_event.decode_log(log_receipt, topic_map)
        return covert_decode_log_to_event(decode_log)

    return _selector, _decode
