# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from threading import Thread
from typing import Dict, List, TypedDict

from websockets import connect

from izumi_infra.blockchain.constants import ZERO_ADDRESS
from izumi_infra.etherscan.constants import (ScanConfigStatusEnum,
                                             ScanModeEnum, ScanTypeEnum)
from izumi_infra.etherscan.scan_utils import get_filter_set_from_str
from izumi_infra.utils.abi_helper import get_event_topic_to_selector
from izumi_infra.utils.task_utils import is_celery_worker_mode


# from asgiref.sync import sync_to_async
# https://stackoverflow.com/questions/61926359/django-synchronousonlyoperation-you-cannot-call-this-from-an-async-context-u
class AsyncEventScantItem(TypedDict):
    scan_config_id: int
    ws_rpc_url: str
    topic_to_selector: Dict[str, str]
    contract_address: str
    topic_filter_list: List[str]

class AsyncEthScanThread(Thread):
    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        # must import django related things here
        from izumi_infra.blockchain.conf import blockchain_settings
        from izumi_infra.etherscan.conf import etherscan_settings
        from izumi_infra.etherscan.models import EtherScanConfig
        from izumi_infra.etherscan.tasks import etherscan_async_event_save

        if not etherscan_settings.ENABLE_ASYNC_EVENT_SCANT: return

        logger = logging.getLogger(__name__)
        logger.info('AsyncEthScanThread Start')

        async def subscribe_and_recv_event(scanItem: AsyncEventScantItem) -> None:
            ws_rpc_url = scanItem['ws_rpc_url']
            scan_config_id = scanItem['scan_config_id']
            if not ws_rpc_url:
                logger.error(f'invalid ws_rpc_url for {scan_config_id}')
                return

            subscribe_filter = {}
            if scanItem['contract_address'] != ZERO_ADDRESS:
                subscribe_filter['address'] = [scanItem['contract_address'].lower()]

            if scanItem['topic_filter_list']:
                topics = [scanItem['topic_to_selector'][topic_name] for topic_name in scanItem['topic_filter_list']]
            else:
                topics = list(scanItem['topic_to_selector'].values())

            # 2 dem array as or condition
            subscribe_filter['topics'] = [topics]

            while True:
                async with connect(ws_rpc_url, ping_interval=None) as ws:
                    await ws.send(json.dumps({"id": 1, "method": "eth_subscribe", "params": ["logs", subscribe_filter]}))
                    subscription_response = await ws.recv()
                    logger.info(f'scan_config_id: {scan_config_id}, subscription response: {subscription_response}')
                    subscription_data = json.loads(subscription_response)
                    if 'result' not in subscription_data:
                        logger.error(f'scan_config_id: {scan_config_id}, subscribe_filter: {subscribe_filter}, subscribe fail with: {subscription_response}')
                        return

                    while True:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=etherscan_settings.ASYNC_EVENT_SCANT_CONN_TIMEOUT_SEC)

                            # TODO: reactor pass msg to another thread?
                            etherscan_async_event_save.delay(scan_config_id, message)

                            # recv_subscription_id = message_dict['params']['subscription']
                            # if subscription_id != recv_subscription_id:
                            #     response = await ws.send(json.dumps({"id": 2, "method": "eth_unsubscribe", "params": [recv_subscription_id]}))
                            #     logger.warning(f'eth_unsubscribe: {recv_subscription_id} diff current: {subscription_id}, result {response}')
                        except asyncio.TimeoutError as e:
                            # timeout to re-connect
                            logger.error('SubscriptionTimeout, start reSubscription')
                            break
                        except Exception as e:
                            logger.error(f'exception when recv for eth_subscribe')
                            logger.exception(e)
                            break

        def event_scan_config_to_item(eventScanConfig: EtherScanConfig) -> AsyncEventScantItem:
            return AsyncEventScantItem(
                scan_config_id=eventScanConfig.id,
                ws_rpc_url=eventScanConfig.contract.chain.ws_rpc_url,
                topic_to_selector=get_event_topic_to_selector(blockchain_settings.CONTRACT_CHOICES_CLASS[eventScanConfig.contract.type].abi),
                contract_address=eventScanConfig.contract.contract_address.lower(),
                topic_filter_list=list(get_filter_set_from_str(eventScanConfig.topic_filter_list))
            )

        realtimeEventScanConfig = EtherScanConfig.objects.filter(
            status=ScanConfigStatusEnum.ENABLE,
            scan_type=ScanTypeEnum.Event,
            scan_mode=ScanModeEnum.RealtimeEventScan
        ).all()

        if not realtimeEventScanConfig:
            return

        async_tasks = [subscribe_and_recv_event(event_scan_config_to_item(scanConfig)) for scanConfig in realtimeEventScanConfig]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(asyncio.gather(*async_tasks))
        except Exception as e:
            logger.exception(e)

    def start(self) -> None:
        if not is_celery_worker_mode(): return
        return super().start()
