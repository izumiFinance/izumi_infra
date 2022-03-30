# -*- coding: utf-8 -*-
from enum import Enum
import logging
from izumi_infra.etherscan.constants import ProcessingStatusEnum, SubReceiverGroupEnum

logger = logging.getLogger(__name__)

# TODO 参数类型支持列表?
def entity_filter(contract_type: str, topic: str = None, function_name: str = None, **kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            instance = kwargs['instance']
            if instance.status == ProcessingStatusEnum.PROCESSEDONE: return
            if topic is not None and instance.topic != topic: return
            if function_name is not None and instance.function_name != function_name: return
            if instance.contract.type != contract_type: return
            logger.info('detect entity: %s chanage for %s', instance, func.__name__)

            return func(*args, **kwargs)

        return wrapper
    return decorator

# def multi_entity_filter(group_enum: SubReceiverGroupEnum, contract_type: str, topic: str = None, function_name: str = None, **kwargs):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             instance = kwargs['instance']
#             if instance.status == ProcessingStatusEnum.PROCESSEDONE: return
#             if instance.sub_status == 0:
#                 # TODO netest signal
#                 instance.update(sub_status=2 ** group_enum[0])
#             if topic is not None and instance.topic != topic: return
#             if function_name is not None and instance.function_name != function_name: return
#             if instance.contract.type != contract_type: return
#             logger.info('detect entity: %s chanage for %s', instance, func.__name__)

#             return func(*args, **kwargs)

#         return wrapper
#     return decorator
