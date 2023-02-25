# -*- coding: utf-8 -*-
import logging
from random import randrange
from typing import Any, Dict

from eth_typing.encoding import HexStr
from eth_utils import remove_0x_prefix, to_hex
from eth_utils.address import to_checksum_address
from web3 import Web3
from web3.types import TxParams

from izumi_infra.blockchain.conf import blockchain_settings
from izumi_infra.blockchain.facade import BlockchainFacade
from izumi_infra.blockchain.models import TransactionSignInfo

logger = logging.getLogger(__name__)

class AccountFacade():
    """
    Account ability implement
    """

    def __init__(self, blockchainFacadeInst: BlockchainFacade, account_address: str, private_key: str) -> None:
        if not isinstance(blockchainFacadeInst, BlockchainFacade):
            raise ValueError("not validate BlockchainFacade instance")
        self.blockchainFacade = blockchainFacadeInst
        self.account_address = to_checksum_address(account_address)
        self.private_key = private_key

    def sign_and_send_transaction(self, data: Dict[str, Any]) -> HexStr:
        """
        Sign data and send, this method would random change
        gasPrice with offset to avoid same sign v value when conflict
        """
        # TODO 抽象一下
        try_cnt = 0
        origin_gas_price = data['gasPrice']
        while True:
            signed_trans = self.blockchainFacade.w3.eth.account.sign_transaction(data, self.private_key)
            r_hex_str = remove_0x_prefix(to_hex(signed_trans.r)).lower()
            sign_info = TransactionSignInfo(r_hex=r_hex_str)
            if sign_info.insert():
                break
            else:
                data['gasPrice'] = origin_gas_price + randrange(-blockchain_settings.SIGN_RANDOM_GAS_PRICE_WEI_OFFSET,
                                                                blockchain_settings.SIGN_RANDOM_GAS_PRICE_WEI_OFFSET)
                data['gasPrice'] = max(data['gasPrice'], 0)
                try_cnt = try_cnt + 1
                logger.error(f'duplicate trans sign r value: {r_hex_str}, try times: {try_cnt}')
                if try_cnt >= blockchain_settings.SIGN_MAX_RETRY_COUNT:
                    raise Exception("exceed max retry sign trans {} times".format(try_cnt))

        tx_hash_hex_bytes = self.blockchainFacade.w3.eth.send_raw_transaction(signed_trans.rawTransaction)
        return Web3.toHex(tx_hash_hex_bytes)

    def get_account_address(self) -> str:
        return self.account_address

    def get_account_transaction_count(self) -> int:
        return self.blockchainFacade.w3.eth.get_transaction_count(self.account_address)

    def build_transaction_params(self, trans_nonce:int=None) -> TxParams:
        """
        Build trans extra params, nonce will fetch latest value from chain if trans_nonce not set
        """
        nonce = trans_nonce if trans_nonce is not None else self.get_account_transaction_count()
        return {'from': self.account_address, 'nonce': nonce,
                'chainId': self.blockchainFacade.chain_id, 'gasPrice': self.blockchainFacade.gas_price_wei}
