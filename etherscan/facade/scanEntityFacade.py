# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from time import sleep
from izumi_infra.etherscan.constants import ProcessingStatusEnum

from django.db.models import F
from izumi_infra.etherscan.models import ContractEvent, ContractTransaction
from izumi_infra.etherscan.conf import etherscan_settings

from izumi_infra.utils.db_utils import order_chunked_iterator

def scan_and_touch_entity():
    """
    retry task for post_save signal
    """
    offset_time = datetime.now() - timedelta(minutes=etherscan_settings.ENTITY_TOUCH_OFFSET_MINUTES)

    unprocessed_event_query = ContractEvent.objects.filter(
        create_time__lt=offset_time,
        status=ProcessingStatusEnum.INITIAL,
        touch_count_remain__gt=0
    )

    unprocessed_trans_query = ContractTransaction.objects.filter(
        create_time__lt=offset_time,
        status=ProcessingStatusEnum.INITIAL,
        touch_count_remain__gt=0
    )

    for entity_list in order_chunked_iterator(unprocessed_event_query, chunk_size=20):
        for entity in entity_list:
        # touch by order
            entity.touch_count_remain = F('touch_count_remain') - 1
            entity.save()
        sleep(1)

    for entity_list in order_chunked_iterator(unprocessed_trans_query, chunk_size=20):
        for entity in entity_list:
        # touch by order
            entity.touch_count_remain = F('touch_count_remain') - 1
            entity.save()
        sleep(1)
