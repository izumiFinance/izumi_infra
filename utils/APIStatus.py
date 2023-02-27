# -*- coding: utf-8 -*-
from izumi_infra.utils.enum import StringEnum

class CommonStatus(StringEnum):
    OK = "Ok"

    INTERNAL_ERROR = "Internal error"
    INVALID_PARAMETER = "Invalid parameter"
    NOT_FOUND = "Not found"

    PERMISSION_DENY = "Permission deny"

# TODO other module status

class EthBaseError(StringEnum):
    INVALID_ETH_ADDRESS = 'invalid eth address'
