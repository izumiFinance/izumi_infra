# -*- coding: utf-8 -*-
import logging
from izumi_infra.etherscan.constants import INIT_SUB_STATUS, ProcessingStatusEnum, SubReceiverGroupEnum

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
            logger.info(f'detect entity: {instance} change for {func.__name__}')

            return func(*args, **kwargs)

        return wrapper
    return decorator

def multi_entity_filter(group_enum: SubReceiverGroupEnum, contract_type: str, topic: str = None, function_name: str = None, **kwargs):
    def decorator(func):
        def wrapper(*args, **kwargs):
            instance = kwargs['instance']
            if instance.status == ProcessingStatusEnum.PROCESSEDONE: return
            if topic is not None and instance.topic != topic: return
            if function_name is not None and instance.function_name != function_name: return
            if instance.contract.type != contract_type: return

            if instance.sub_status == INIT_SUB_STATUS:
                # TODO nested signal
                sub_task_mark = 2**group_enum.value[0] - 1
                instance.update_fields(sub_status=sub_task_mark)

            if instance.sub_status & (1 << group_enum.value[1]) == 0: return
            logger.info(f'detect entity: {instance} change for sub {func.__name__}')

            return func(*args, **kwargs)

        return wrapper
    return decorator

SIGNAL_PARAM_SYNC_TASK = 'signal_param_sync_task'

def mark_as_sync_entity(entity):
    """
    set extra sync_task param to signal receiver
    """
    setattr(entity, SIGNAL_PARAM_SYNC_TASK, True)

def is_sync_entity(entity) -> bool:
    """
    check extra sync_task param to signal receiver
    """
    return getattr(entity, SIGNAL_PARAM_SYNC_TASK, False)
