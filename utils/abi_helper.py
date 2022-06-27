import json
from typing import Dict
from eth_utils import function_abi_to_4byte_selector, event_abi_to_log_topic, function_signature_to_4byte_selector
from eth_utils import to_hex
from eth_utils.abi import _abi_to_signature

def get_abi_selector_to_signature(abi_str: str) -> Dict[str, str]:
    """
    get function or event selector to signature mapping
    """
    abi_all = json.loads(abi_str)
    fn_mapping = { to_hex(function_abi_to_4byte_selector(e)): _abi_to_signature(e) for e in abi_all if e['type'] == 'function' }
    event_mapping = { to_hex(event_abi_to_log_topic(e)): _abi_to_signature(e) for e in abi_all if e['type'] == 'event' }

    return {**fn_mapping, **event_mapping}

def get_fn_selector_by_signature(fn_signature) -> str:
    return to_hex(function_signature_to_4byte_selector(fn_signature))
