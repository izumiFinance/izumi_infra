# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta
from typing import TypedDict

from requests import Request, Session
from cachetools import cached, TTLCache

from izumi_infra.blockchain.constants import ChainIdEnum
from izumi_infra.utils.base_context import BaseContext

logger = logging.getLogger(__name__)

class UniswapPoolData(TypedDict):
    date: int
    liquidity: int
    volumeToken0: int
    volumeToken1: int
    feesUSD: float
    tvlUSD: float
    volumeUSD: float

class UniswapPoolFacade(BaseContext):
    def _init_thegraph_api(self):
        self.thegraph_uniswap3_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        self.thegraph_uniswap2_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'

        self.thegraph_uniswap3_polygon_url = 'https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon'

        self.thegraph_uniswap3_url_mapping = {
            ChainIdEnum.EthereumMainnet.value: self.thegraph_uniswap3_url,
            ChainIdEnum.Matic.value: self.thegraph_uniswap3_polygon_url,
        }
        headers = {
            'Accepts': 'application/json',
        }
        self.thegraph_uniswap3_session = Session()
        self.thegraph_uniswap3_session.headers.update(headers)

        self.thegraph_uniswap3_poolDayData_before = """
        query poolDayDatas($startTime: Int!, $limit: Int!, $skip: Int!, $address: Bytes!) {
                poolDayDatas(
                first: $limit
                skip: $skip
                where: { pool: $address, date_lte: $startTime }
                orderBy: date
                orderDirection: desc
                subgraphError: allow
            ) {
                date
                liquidity
                volumeToken0
                volumeToken1
                volumeUSD
                tvlUSD
                feesUSD
            }
        }
        """

    def query_latest_pool_data(self, chain_id: int, pool_address: str) -> UniswapPoolData:
        lasest_day = datetime.now() - timedelta(days=1)
        daytime = lasest_day.replace(hour=8, minute=0, second=0, microsecond=0)
        payload = {
            "query": self.thegraph_uniswap3_poolDayData_before,
            "variables": {
                "startTime": int(daytime.timestamp()),
                "limit": 1,
                "skip": 0,
                "address": pool_address.lower()
            }
        }
        try:
            query_url = self.thegraph_uniswap3_url_mapping[chain_id]
            response = self.thegraph_uniswap3_session.post(url=query_url, json=payload)
            return json.loads(response.text)['data']['poolDayDatas'][0]
        except Exception as e:
            logger.exception(e)
            return {}

    @cached(cache=TTLCache(maxsize=100, ttl=5 * 60))
    def query_latest_pool_data_with_apr(self, chain_id: int, pool_address: str):
        result = self.query_latest_pool_data(chain_id, pool_address)
        # Fake value
        if not result:
            logger.info("use fake pool data for chainId: %d, pool_addr: %s", chain_id, pool_address)
            return {
                'apr': 1
            }

        result['apr'] = float(result['feesUSD']) / float(result['tvlUSD']) * 365 * 100
        return result

    def __init__(self):
        super().__init__()
        self._init_thegraph_api()
