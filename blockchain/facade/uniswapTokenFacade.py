# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Set
from requests import Request, Session
import json
from izumi_infra.blockchain.facade.swapFacade import SwapPriceFacade
from izumi_infra.blockchain.types import TokenData
from izumi_infra.blockchain.utils import sort_addr

logger = logging.getLogger(__name__)

class UniswapTokenPriceFacade(SwapPriceFacade):
    """
    Token ability facade context
    thegraph playground: https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
                         https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2
    repo: https://github.com/Uniswap/v3-subgraph
    """

    def _init_thegraph_api(self):
        self.thegraph_uniswap3_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        self.thegraph_uniswap2_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'
        self.thegraph_uniswap3_token_graphql = """query tokenPrice($mainAddress: String, $targetTokenList: [String]){
            as0: pools(where: { token0: $mainAddress, token1_in: $targetTokenList }) {
                feeTier
                targetPrice: token0Price
                targetVolume: volumeToken1
                token: token1 {
                    id
                    symbol
                    name
                }
            }
            as1: pools(where: { token1: $mainAddress, token0_in: $targetTokenList }) {
                feeTier
                targetPrice: token1Price
                targetVolume: volumeToken0
                token: token0 {
                    id
                    symbol
                    name
                }
            }
        }
        """

        self.thegraph_uniswap2_token_graphql="""query tokenPrice($mainAddress: String, $targetTokenList: [String]){
            as0: pairs (where: { token0: $mainAddress, token1_in: $targetTokenList }){
                targetPrice: token0Price
                targetVolume: volumeToken0
                token: token1 {
                    id
                    symbol
                    name
                }
            },
            as1: pairs (where: { token1: $mainAddress, token0_in: $targetTokenList }){
                targetPrice: token1Price
                targetVolume: volumeToken1
                token: token0 {
                    id
                    symbol
                    name
                }
            }
        }
        """

        headers = {
            'Accepts': 'application/json',
        }
        self.thegraph_uniswap3_session = Session()
        self.thegraph_uniswap3_session.headers.update(headers)

    def __init__(self):
        super().__init__()
        self._init_thegraph_api()
        self.main_usdc_addr = '0x99c9fc46f92e8a1c0dec1b1747d010903e884be1'
        self.main_weth_addr = '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
        self.main_token_addr_list = [ self.main_usdc_addr, self.main_weth_addr ]
        self.token_addr_set = set()

    def sync_uniswap_pool(self, main_token_addr, target_addr_list: List[str], version=3):
        payload = {
            "query": self.thegraph_uniswap3_token_graphql if version == 3 else self.thegraph_uniswap2_token_graphql,
            "variables": {
                "mainAddress": main_token_addr.lower(),
                "targetTokenList": [t.lower() for t in target_addr_list]
            }
        }
        try:
            query_url = self.thegraph_uniswap3_url if version == 3 else self.thegraph_uniswap2_url
            response = self.thegraph_uniswap3_session.post(url=query_url, json=payload)
            data = json.loads(response.text)
            all_token = [*data['data']['as0'], *data['data']['as1']]

            all_token_info = {}
            for token in all_token:
                if float(token['targetVolume']) <= 0: continue
                token_addr = token['token']['symbol']
                token['price'] = float(token['targetPrice']) if token_addr > main_token_addr else 1/float(token['targetPrice'])
                all_token_info.setdefault(token_addr, token)
                if float(all_token_info[token_addr]['targetVolume']) < float(token['targetVolume']):
                    all_token_info[token_addr] = token

            for addr, info in all_token_info.items():
                tokenX, tokenY = sort_addr(main_token_addr, addr)
                self.set_or_update_pool_price(tokenX, tokenY, info['price'])

        except Exception as e:
            logger.exception(e)
            return {}

    def sync_uniswap_pool_all(self, token_addr_list):
        for main_token_addr in self.main_token_addr_list:
            self.sync_uniswap_pool(main_token_addr, token_addr_list, version=2)
            self.sync_uniswap_pool(main_token_addr, token_addr_list)

    def get_token_price_by_addr_list(self, addr_list_param: List[str]):
        missing_token = set(addr_list_param) - self.token_addr_set
        if missing_token:
            self.token_addr_set = self.token_addr_set.union(missing_token)
            self.sync_uniswap_pool_all(list(self.token_addr_set))

        return { t: {'price': self.get_token_usd_price(self.main_usdc_addr, t)} for t in addr_list_param }

    def get_token_price_by_addr(self, token_addr: str):
        token_info = self.get_token_price_by_addr_list([token_addr])
        return token_info

    def refresh_cache_token(self):
        if len(self.token_addr_set) == 0: return
        logger.info("refresh all cache token balance")
        self.sync_uniswap_pool_all(list(self.token_addr_set))


class UniswapTokenHourDataFacade():
    def _init_thegraph_api(self):
        self.thegraph_uniswap3_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        self.thegraph_uniswap2_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'

        # periodStartUnix: unix timestamp for start of hour
        # use hour open price as price
        self.thegraph_uniswap3_token_hour_graphql="""
        query tokenHourDatas($tokenList: [String], $hourEnd: Int) {
            tokenHourDatas(where: { token_in: $tokenList, periodStartUnix: $hourEnd }) {
                periodStartUnix
                open
                token {
                    id
                    symbol
                    name
                }
            }
        }
        """

        headers = {
            'Accepts': 'application/json',
        }
        self.thegraph_uniswap3_session = Session()
        self.thegraph_uniswap3_session.headers.update(headers)

    def __init__(self):
        super().__init__()
        self._init_thegraph_api()
        self.token_addr_set = set()
        # thegraph 产出时间设定
        self.hour_data_offset = timedelta(minutes=5)

    def time_to_hour_end_timestamp(self, time: datetime = None) -> int:
        hour_time = (time if time else datetime.now() - self.hour_data_offset).replace(minute=0, second=0, microsecond=0)
        return int(hour_time.timestamp())

    def get_token_data_hour(self, token_addr_list: List[str], time: datetime = None, version=3) -> Dict[str, TokenData]:
        hour_end_timestamp = self.time_to_hour_end_timestamp(time)
        payload = {
            "query": self.thegraph_uniswap3_token_hour_graphql if version == 3 else None,
            "variables": {
                "tokenList": [t.lower() for t in token_addr_list],
                "hourEnd": hour_end_timestamp,
            }
        }

        try:
            query_url = self.thegraph_uniswap3_url if version == 3 else self.thegraph_uniswap2_url
            response = self.thegraph_uniswap3_session.post(url=query_url, json=payload)
            tokenHourDataList = json.loads(response.text)['data']['tokenHourDatas']

            result: Dict[str, TokenData] = {}
            for data in tokenHourDataList:
                token_data = data['token']
                result[token_data['id']] = TokenData(
                    address=token_data['id'],
                    symbol=token_data['symbol'],
                    name=token_data['name'],
                    price=float(data['open']),
                    price_time=datetime.fromtimestamp(data['periodStartUnix'])
                )

            return result

        except Exception as e:
            logger.exception(e)
            return {}

    # TODO cache with time
    def get_single_token_price_hour(self, token_addr: str, time: datetime = None, default_price: float = 0, mapping: Dict[str, str] = {}):
        token_addr_lower = token_addr.lower()
        target_addr = mapping.get(token_addr_lower, token_addr_lower)
        return self.get_token_data_hour([target_addr], time).get(target_addr, {}).get('price', default_price)

class FakeTokenHolder():
    def get_token_info_by_symbol(p):
        return {'price': 1}
