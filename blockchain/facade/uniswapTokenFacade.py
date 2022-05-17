# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Set
from requests import Request, Session
import json
from izumi_infra.blockchain.types import TokenData
from izumi_infra.blockchain.utils import sort_addr

logger = logging.getLogger(__name__)

class UniswapTokenPriceFacade():
    """
    Token ability facade context
    thegraph playground: https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3
                         https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v2
    repo: https://github.com/Uniswap/v3-subgraph
    """

    def _init_thegraph_api(self):
        self.thegraph_uniswap3_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        self.thegraph_uniswap2_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2'
        self.thegraph_uniswap3_token_graphql = """query tokenPrice($targetTokenList: [String]){
            tokens(where: { id_in: $targetTokenList }) {
                id
                derivedETH
            }
            ethUsdcPool: pools(where: { token0: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                            token1: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
                            orderBy: volumeToken0, orderDirection: desc, first: 1) {
                ethUSDPrice: token0Price
            }
        }
        """

        self.thegraph_uniswap2_token_graphql="""query tokenPrice($mainAddress: String, $targetTokenList: [String]){
            tokens(where: { id_in: $targetTokenList }) {
                id
                derivedETH
            }
            ethUsdcPool: pairs(where: { token0: "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                            token1: "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
                            orderBy: volumeToken0, orderDirection: desc, first: 1) {
                ethUSDPrice: token0Price
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
        self.token_price_info = {}

    def fetch_uniswap_token_price(self, target_addr_list: List[str], version=3) -> Dict[str, float]:
        payload = {
            "query": self.thegraph_uniswap3_token_graphql if version == 3 else self.thegraph_uniswap2_token_graphql,
            "variables": {
                "targetTokenList": [t.lower() for t in target_addr_list]
            }
        }
        response = None
        try:
            query_url = self.thegraph_uniswap3_url if version == 3 else self.thegraph_uniswap2_url
            response = self.thegraph_uniswap3_session.post(url=query_url, json=payload)
            data = json.loads(response.text)
            tokens = data["data"]["tokens"]
            ethUSDPrice = float(data["data"]["ethUsdcPool"][0]['ethUSDPrice'])

            all_token_info = {token['id']: float(token['derivedETH']) * ethUSDPrice for token in tokens}
            return all_token_info
        except Exception as e:
            logger.error(f"fetch_uniswap_token_price error, response: {response}")
            logger.exception(e)
            return {}

    def sync_uniswap_pool_all(self, token_addr_list: List[str]) -> None:
        """
        cache missing as 0
        """
        logger.info(f'fetch uniswap token price size: {len(token_addr_list)}')
        v2_info = self.fetch_uniswap_token_price(token_addr_list, version=2)
        v3_info = self.fetch_uniswap_token_price(token_addr_list)
        default_info = {addr: 0 for addr in token_addr_list}
        self.token_price_info = { **default_info , **self.token_price_info, **v2_info, **v3_info}

    def get_token_price_by_addr_list(self, addr_list_param: List[str]) -> Dict[str, float]:
        param_token_addr_set = set([addr.lower() for addr in addr_list_param])
        missing_token = param_token_addr_set - self.token_price_info.keys()
        if missing_token:
            self.sync_uniswap_pool_all(list(missing_token))

        return { addr: self.token_price_info.get(addr, 0) for addr in param_token_addr_set }

    def get_token_price_by_addr(self, token_addr: str) -> float:
        token_addr_lower = token_addr.lower()
        token_info = self.get_token_price_by_addr_list([token_addr_lower])
        return token_info.get(token_addr_lower, 0)

    def refresh_cache_token(self) -> None:
        if len(self.token_price_info) == 0: return
        logger.info("UniswapTokenPriceFacade refresh all cache token price")
        self.sync_uniswap_pool_all(list(self.token_price_info.keys()))


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
        # uniswap hour data 产出安全时间 10 minutes
        hour_time = (time if time else datetime.now() - self.hour_data_offset) - timedelta(minutes=10)
        return int(hour_time.replace(minute=0, second=0, microsecond=0).timestamp())

    def get_token_data_hour(self, token_addr_list: List[str], time: datetime = None, version=3) -> Dict[str, TokenData]:
        hour_end_timestamp = self.time_to_hour_end_timestamp(time)
        payload = {
            "query": self.thegraph_uniswap3_token_hour_graphql if version == 3 else None,
            "variables": {
                "tokenList": [t.lower() for t in token_addr_list],
                "hourEnd": hour_end_timestamp,
            }
        }

        response = None
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
            logger.error(f"get_token_data_hour error, response: {response}")
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
