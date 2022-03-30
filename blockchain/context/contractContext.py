# -*- coding: utf-8 -*-
from typing import Generic, TypeVar

from izumi_infra.blockchain.conf import blockchain_settings
from izumi_infra.blockchain.context import blockchainHolder, blockchainMetaHolder
from izumi_infra.blockchain.facade.contractFacade import ContractFacade
from izumi_infra.blockchain.models import Blockchain, Contract
from izumi_infra.blockchain.types import ContractMeta
from izumi_infra.utils.base_context import BaseContext


F = TypeVar('F')

class BaseContractContext(BaseContext, Generic[F]):
    def get_contract_type(self) -> str:
        pass

    def get_facade_by_contract_model(self, contract_model: Contract) -> F:
        if not isinstance(contract_model, Contract):
            raise ValueError("only support for Contract model, not {}".format(contract_model))
        if contract_model.type != self.get_contract_type():
            raise ValueError("only support {} type Contract, not {}".format(
                self.get_contract_type(), contract_model.type)
            )

        if contract_model.id in self._instances: return self._instances[contract_model.id]
        instance = self._instances.setdefault(contract_model.id, self._build_facade(contract_model))
        return instance

    def _build_facade(self, contract_model: Contract) -> F:
        pass

class ContractContext(BaseContext):
    """
    Contract ability facade context
    """

    def get_facade_by_model(self, contract_model: Contract) -> ContractFacade:
        if not isinstance(contract_model, Contract):
            raise ValueError("only support for Blockchain model, not {}".format(contract_model))
        if contract_model.id in self._instances:
            return self._instances[contract_model.id]

        instance = self._instances.setdefault(contract_model.id, self._build_facade(contract_model))
        return instance

    def get_facade_by_meta(self, contractMeta: ContractMeta) -> ContractFacade:
        contract_key = '{}-{}'.format(contractMeta['chainMeta']['id'], contractMeta['address'])
        if contract_key in self._instances: return self._instances[contract_key]

        instance = self._instances.setdefault(contract_key, self._simple_build_facade(contractMeta))
        return instance

    def get_facade_by_info(self, blockchain_model: Blockchain, contract_addr: str, contract_abi: str) -> ContractFacade:
        contract_key = '{}-{}'.format(blockchain_model.chain_id, contract_addr)
        if contract_key in self._instances: return self._instances[contract_key]

        instance = self._instances.setdefault(contract_key, self._simple_info_build_facade(blockchain_model, contract_addr, contract_abi))
        return instance

    def _build_facade(self, contract_model: Contract) -> ContractFacade:
        contract_abi_json_str = blockchain_settings.CONTRACT_CHOICES_CLASS[contract_model.type].abi
        if contract_abi_json_str == None:
            raise ValueError("can not found abi define for {} type contract".format(contract_model.type))

        blockchain_facade = blockchainHolder.get_facade_by_model(contract_model.chain)
        contract_facade = ContractFacade(blockchain_facade,
                                         contract_abi_json_str,
                                         contract_model.contract_address)
        return contract_facade

    def _simple_build_facade(self, contractMeta: ContractMeta) -> ContractFacade:
        blockchain_facade = blockchainMetaHolder.get_facade_by_meta(contractMeta['chainMeta'])
        contract_facade = ContractFacade(blockchain_facade, contractMeta['abi'], contractMeta['address'])
        return contract_facade

    def _simple_info_build_facade(self, blockchain_model: Blockchain, contract_addr: str, contract_abi: str) -> ContractFacade:
        blockchain_facade = blockchainMetaHolder.get_facade_by_model(blockchain_model)
        contract_facade = ContractFacade(blockchain_facade, contract_abi, contract_addr)
        return contract_facade

class ContractSimpleContext(BaseContext):
    """
    Contract ability facade context
    """
    def get_facade_by_meta(self, contractMeta: ContractMeta) -> ContractFacade:
        contract_key = '{}-{}'.format(contractMeta['chainMeta']['id'], contractMeta['address'])
        if contract_key in self._instances: return self._instances[contract_key]

        instance = self._instances.setdefault(contract_key, self._simple_build_facade(contractMeta))
        return instance

    def _simple_build_facade(self, contractMeta: ContractMeta) -> ContractFacade:
        blockchain_facade = blockchainMetaHolder.get_facade_by_meta(contractMeta['chainMeta'])
        contract_facade = ContractFacade(blockchain_facade, contractMeta['abi'], contractMeta['address'])
        return contract_facade
