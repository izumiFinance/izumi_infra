# -*- coding: utf-8 -*-
import json
import os
import re
from typing import List, TypedDict

# TODO Solidity list ?
TYPE_MAPPING = {
    re.compile("uint*"): "int",
    re.compile("int*"): "int",
    re.compile("address"): "str",
    re.compile("struct *"): "struct",
    re.compile("tuple\[\]"): "struct",
    re.compile("bool"): "bool",
    re.compile("bytes*"): "str",
    re.compile("string"): "str",
}

TYPE_DICT_DEFINE_SP = os.linesep + "    "
TYPE_DICT_BETWEEN_SP = os.linesep + os.linesep

def abiTypesGenerator(abi_str: str) -> str:
    abi_obj = json.loads(abi_str)
    func_list = [item for item in abi_obj if item["type"] == "function"]

    type_dict_ast = {}
    for f in func_list:
        if len(f["inputs"]) > 1:
            _, param_type_dict_ast = composeParamTypeDictAST(f["name"] + "Param", f["inputs"])
            type_dict_ast = {**type_dict_ast, **param_type_dict_ast}
        if len(f["outputs"]) > 1:
            _, return_type_dict_ast = composeParamTypeDictAST(f["name"] + "Return", f["outputs"])
            type_dict_ast = {**type_dict_ast, **return_type_dict_ast}

    type_dict_content = TYPE_DICT_BETWEEN_SP.join([ TYPE_DICT_DEFINE_SP.join([k, *v]) for k, v in type_dict_ast.items() ])
    type_dict_content = 'from typing import TypedDict' + TYPE_DICT_BETWEEN_SP + type_dict_content

    return type_dict_content

class AbiParamTypeDict(TypedDict):
    name: str
    type: str

    internalType: str
    components: List[TypedDict]

# TODO gen doc
# TODO array type
def composeParamTypeDictAST(name: str, param_type_list: List[AbiParamTypeDict]):
    if len(param_type_list) == 0: return ("", {})
    type_dict_field_list = []
    main_type_dict_name = "{}Dict".format(name[0].upper() + name[1:])
    main_type_dict_define = "class {}(TypedDict):".format(main_type_dict_name)
    result = {main_type_dict_define: type_dict_field_list}
    for i, param_type in enumerate(param_type_list):
        match_type_list = [TYPE_MAPPING[t] for t in TYPE_MAPPING.keys() if t.match(param_type["type"])]
        if not match_type_list: raise Exception("not support type mapping: " + param_type)
        match_type = match_type_list[0]
        if match_type == "struct":
           nested_type_dict_name, nested_type_dict = composeParamTypeDictAST(param_type["name"], param_type["components"])
           result = {**result, **nested_type_dict}
           name = nested_type_dict_name
           match_type = nested_type_dict_name
        else:
            name = param_type["name"] if param_type["name"] else param_type["type"] + str(i)

        type_dict_field_list.append("{}: {}".format(name, match_type))

    return (main_type_dict_name, result)
