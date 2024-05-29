# -*- coding: utf-8 -*-
import logging

from cachetools import LRUCache, cached
from eth_utils import to_checksum_address

from izumi_infra.blockchain.conf import blockchain_settings
from izumi_infra.blockchain.constants import BaseContractInfoEnum
from izumi_infra.blockchain.context import blockchainHolder, contractHolder
from izumi_infra.blockchain.models import Blockchain, Contract
from izumi_infra.blockchain.types import Erc20TokenInfo
from izumi_infra.blockchain.utils import ascii_escape_str

logger = logging.getLogger(__name__)

@cached(cache=LRUCache(maxsize=2048))
def get_erc20_token_info(chain_id: int, token_addr: str) -> Erc20TokenInfo:
    blockchain = Blockchain.objects.get(chain_id=chain_id)
    tokenContract = contractHolder.get_facade_by_info(blockchain, to_checksum_address(token_addr), BaseContractInfoEnum.ERC20.abi)
    token_symbol = ascii_escape_str(tokenContract.contract.functions.symbol().call())
    token_decimals = tokenContract.contract.functions.decimals().call()
    name = ascii_escape_str(tokenContract.contract.functions.name().call())
    totalSupply = tokenContract.contract.functions.totalSupply().call()
    return Erc20TokenInfo(address=token_addr, symbol=token_symbol, decimals=token_decimals,
                          name=name, totalSupply=totalSupply)

def get_erc20_token_balance(chain_id: int, token_addr: str, account_addr: str, decimal: int=None) -> float:
    try:
        blockchain = Blockchain.objects.get(chain_id=chain_id)
        tokenContract = contractHolder.get_facade_by_info(blockchain, to_checksum_address(token_addr), BaseContractInfoEnum.ERC20.abi)
        balance_decimal = tokenContract.contract.functions.balanceOf(to_checksum_address(account_addr)).call()
        if decimal:
            token_decimal = decimal
        else:
            token_info = get_erc20_token_info(chain_id, token_addr)
            token_decimal = token_info['decimals']

        return balance_decimal / (10 ** token_decimal)
    except Exception as e:
        logger.exception(e)
        logger.warn(f'get_erc20_token_balance error: {chain_id}, {token_addr}, {account_addr}')
        raise e

@cached(cache=LRUCache(maxsize=1024))
def get_erc20_token_hist_balance(chain_id: int, token_addr: str, account_addr: str, block_id: int) -> float:
    blockchain = Blockchain.objects.get(chain_id=chain_id)
    tokenContract = contractHolder.get_facade_by_info(blockchain, to_checksum_address(token_addr), BaseContractInfoEnum.ERC20.abi)

    try:
        balance_decimal = tokenContract.contract.functions.balanceOf(to_checksum_address(account_addr)).call(block_identifier=block_id)
        token_info = get_erc20_token_info(chain_id, token_addr)
    except Exception as e:
        # may raise error when account not exist
        logger.exception(e)
        logger.warn(f'get_erc20_token_hist_balance error: {chain_id}, {token_addr}, {account_addr}, {block_id}')
        return 0

    return balance_decimal / (10 ** token_info['decimals'])

def block_near_time(target_stamp, get_block_timestamp, block_pre, block_post, max_block):
    block_pre = max(1, block_pre)
    block_post = min(max_block, block_post)

    if abs(block_pre - block_post) <= blockchain_settings.BLOCK_NEAR_TIME_TOLERANCE_BLOCK:
        return block_pre

    t0, t1 = get_block_timestamp(block_pre), get_block_timestamp(block_post)

    av_block_time = (t1 - t0) / (block_post - block_pre)

    # if block-times were evenly-spaced, get expected block number
    k = (target_stamp - t0) / (t1 - t0)
    block_expected = int(block_pre + k * (block_post - block_pre))
    block_expected = min(block_expected, max_block)

    # get the ACTUAL time for that block
    texpected = get_block_timestamp(block_expected)

    # use the discrepancy to improve our guess
    est_nblocks_from_expected_to_target = int((target_stamp - texpected) / av_block_time)
    iexpected_adj = block_expected + est_nblocks_from_expected_to_target

    r = abs(est_nblocks_from_expected_to_target)

    return block_near_time(target_stamp, get_block_timestamp, iexpected_adj - r, iexpected_adj + r, max_block)

@cached(cache=LRUCache(maxsize=1024))
def estimate_block_number_by_time(chain_id: int, timestamp: int):
    blockchain = blockchainHolder.get_facade_by_model(Blockchain.objects.get(chain_id=chain_id))
    ilatest = blockchain.w3.eth.get_block('latest')['number']
    def get_block_timestamp(block_number: int):
        try:
            block = blockchain.w3.eth.getBlock(block_number)
            return block.timestamp
        except Exception as e:
            logger.error(f"block number: {block_number}")

    return block_near_time(timestamp, get_block_timestamp, 1, ilatest, ilatest)
