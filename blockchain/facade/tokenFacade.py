# -*- coding: utf-8 -*-
import abc

from izumi_infra.blockchain.constants import ContractABI
from izumi_infra.blockchain.types import TokenInfo

class TokenHolderContractFacade(metaclass=abc.ABCMeta):

    @staticmethod
    def is_valid_token(token_info):
        # see struct Token, ERC20 token address is not 0 maybe valid
        return int(token_info[0], 0) != 0

    @abc.abstractmethod
    def _get_w3(self):
        pass

    def get_token_info_from_erc20_contract(self, erc20_contract_address: str) -> TokenInfo:
        # TODO token facade
        erc20_contract = self._get_w3().eth.contract(address=erc20_contract_address, abi=ContractABI.ERC20_ABI.value)
        symbol = erc20_contract.functions.symbol().call()
        name = erc20_contract.functions.name().call()
        decimals = erc20_contract.functions.decimals().call()
        token_info = TokenInfo(
            chainId=1,
            address=erc20_contract_address,
            symbol=symbol,
            name=name,
            decimals=decimals
        )

        return token_info
