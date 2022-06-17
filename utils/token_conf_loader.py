# -*- coding: utf-8 -*-
import json
import logging
from typing import Dict, List, TypedDict
from cachetools import TTLCache, cached
import requests

from izumi_infra.blockchain.types import TokenConfigType, TokenMeta

logger = logging.getLogger(__name__)

PROD_TOKEN_LIST_URL = 'https://raw.githubusercontent.com/izumiFinance/izumi-tokenList/main/build/tokenList.json';
DEV_TOKEN_LIST_URL = 'https://raw.githubusercontent.com/izumiFinance/izumi-tokenList/main/build/tokenListDev.json';

class GithubContractConfig(TypedDict):
    address: str
    decimal: str

class GithubTokenConfig(TypedDict):
    chains: List[int]
    name: str
    symbol: str
    icon: str
    contracts: Dict[str, GithubContractConfig]

def token_config_loader(url: str) -> TokenConfigType:
    data: List[GithubTokenConfig] = {}
    response = None
    try:
        response = requests.get(url)
        data: List[GithubTokenConfig] = json.loads(response.text)
    except Exception as e:
        logger.exception(e)
        logger.error(f'token_config_loader error, response: {response.content}')

    all_token_config: TokenConfigType = {}
    for tokenConfig in data:
        for chainId, token in tokenConfig['contracts'].items():
            chain_token_config = all_token_config.setdefault(int(chainId), {})
            chain_token_config[tokenConfig['symbol']] = TokenMeta(
                address=token['address'],
                symbol=tokenConfig['symbol'],
                decimal=token['decimal']
            )

    return all_token_config

@cached(cache=TTLCache(maxsize=10, ttl=60 * 60))
def get_github_token_config() -> TokenConfigType:
    return token_config_loader(PROD_TOKEN_LIST_URL)

@cached(cache=TTLCache(maxsize=10, ttl=30 * 60))
def get_github_dev_token_config() -> TokenConfigType:
    return token_config_loader(DEV_TOKEN_LIST_URL)

