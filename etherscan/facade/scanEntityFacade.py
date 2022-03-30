# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from izumi_infra.etherscan.constants import ProcessingStatusEnum

from django.conf import settings
from django.db.models import F
from izumi_infra.etherscan.models import ContractEvent, ContractTransaction
from izumi_infra.etherscan.conf import etherscan_settings

from itertools import chain
from operator import attrgetter

def scan_and_touch_entity():
    """
    retry task for post_save singal
    """
    offset_time = datetime.now() - timedelta(minutes=etherscan_settings.ENTITY_TOUCH_OFFSET_MINUTES)

    unprocessed_event_entity = ContractEvent.objects.filter(
        create_time__lt=offset_time,
        status=ProcessingStatusEnum.INITIAL,
        touch_count_remain__gt=0
    ).order_by('create_time')

    unprocessed_trans_entity = ContractTransaction.objects.filter(
        create_time__lt=offset_time,
        status=ProcessingStatusEnum.INITIAL,
        touch_count_remain__gt=0
    ).order_by('create_time')

    order_unprocessed_entity = sorted(
        chain(unprocessed_event_entity, unprocessed_trans_entity),
        key=attrgetter('create_time')
    )

    # touch by order
    for entity in order_unprocessed_entity:
        entity.touch_count_remain = F('touch_count_remain') - 1
        entity.save()

