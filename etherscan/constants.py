# -*- coding: utf-8 -*-
from enum import Enum
from izumi_infra.utils.enum import IntegerFieldEnum, StringFieldEnum

class ScanTypeEnum(IntegerFieldEnum):
    # contract base scan
    Transaction = 0
    Event = 1

class ScanConfigStatusEnum(IntegerFieldEnum):
    DISABLE = 0
    ENABLE = 1

class ScanConfigAuditLevelEnum(IntegerFieldEnum):
    DISABLE = 0
    ENABLE = 1

class ScanTaskStatusEnum(IntegerFieldEnum):
    INITIAL = 0
    FINISHED = 1
    ARCHIVED = 2
    CLOSED = -1

class ProcessingStatusEnum(IntegerFieldEnum):
    INITIAL = 0
    PROCESSEDONE = 1

class ScanFilterTypeEnum(StringFieldEnum):
    from_addr = 'from_addr'
    fn_name = 'fn_name'
    topic = 'topic'

FILTER_SPLIT_CHAR = ','

INIT_SUB_STATUS = -1
# small signed int max 15 bit
MAX_SUB_STATUS_BIT = 0xFF

class SubReceiverGroupEnum(Enum):
    MAX_2_OF_0 = (2, 0)
    MAX_2_OF_1 = (2, 1)

    MAX_3_OF_0 = (3, 0)
    MAX_3_OF_1 = (3, 1)
    MAX_3_OF_2 = (3, 2)
