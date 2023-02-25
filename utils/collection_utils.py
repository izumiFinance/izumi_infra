# -*- coding: utf-8 -*-
from functools import reduce
from typing import Dict, Any, List, Tuple, TypeVar, Type, _TypedDictMeta, _GenericAlias

def chunks(lst: range, n: int) -> List[range]:
    """
    split range to some max n size sub range
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_dict_diffs(left: Dict[str, Any], right: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    compare two dict by key, return difference
    """
    left_only: Dict[str, Any] = {k: left[k] for k in left.keys() - right.keys()}
    right_only: Dict[str, Any] = {k: right[k] for k in right.keys() - left.keys()}
    return left_only, right_only


def merge_dict_in_list(list_dict: List[Dict[Any, Any]]) -> Dict[Any, Any]:
    """
    merge dict in list
    """
    return reduce(lambda i, d: {**i, **d}, list_dict, {})

T = TypeVar('T')

def tuple_to_typedict(data_tuple: Tuple, type_class: Type[T]) -> T:
    """
    convert web3py contract return tuple data to TypeDict data, support nested TypeDict, List
    """
    if not data_tuple: return {}
    annotations = type_class.__annotations__
    inst = type_class()
    for key, v in zip(annotations.keys(), data_tuple):
        t: _GenericAlias = annotations[key]
        tt = type(t)
        if tt == type:
            inst[key] = v
        elif tt == _TypedDictMeta:
            inst[key] = tuple_to_typedict(v, t)
        elif t.__origin__ == list:
            t_in_list: _GenericAlias = t.__args__[0]
            inst[key] =  [tuple_to_typedict(x, t_in_list) for x in v]
        else:
            inst[key] = v

    return inst
