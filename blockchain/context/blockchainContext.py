# -*- coding: utf-8 -*-
from izumi_infra.blockchain.constants import BlockChainVmEnum
from izumi_infra.blockchain.facade import BlockchainFacade
from izumi_infra.blockchain.models import Blockchain
from izumi_infra.blockchain.types import ChainMeta
from izumi_infra.utils.base_context import BaseContext

class BlockchainContext(BaseContext):
    """
    Blockchain ability facade context
    """

    def get_facade_by_model(self, blockchain_model: Blockchain) -> BlockchainFacade:
        if not isinstance(blockchain_model, Blockchain):
            raise ValueError("only support for Blockchain model, not {}".format(blockchain_model))
        if blockchain_model.chain_id in self._instances:
            self._instances[blockchain_model.chain_id].set_random_rpc_url()
            return self._instances[blockchain_model.chain_id]

        instance = self._instances.setdefault(blockchain_model.chain_id, self._build_facade(blockchain_model))
        return instance

    def get_facade_by_meta(self, chainMeta: ChainMeta) -> BlockchainFacade:
        instance = self._instances.setdefault(chainMeta['id'], self._simple_build_facade(chainMeta))
        return instance

    def _build_facade(self, blockchain_model: Blockchain) -> BlockchainFacade:
        blockchain_facade = BlockchainFacade(blockchain_model.symbol,
                                             blockchain_model.vm_type,
                                             blockchain_model.get_rpc_url(),
                                             blockchain_model.chain_id,
                                             blockchain_model.gas_price_wei)
        return blockchain_facade

    def _simple_build_facade(self, chainMeta: ChainMeta) -> BlockchainFacade:
        blockchain_facade = BlockchainFacade(None,
                                             BlockChainVmEnum.EVM,
                                             chainMeta['rpc_url'],
                                             chainMeta['id'],
                                             5_000_000_000)
        return blockchain_facade

class BlockchainSimpleContext(BaseContext):
    """
    Blockchain ability facade context
    """

    def get_facade_by_meta(self, chainMeta: ChainMeta) -> BlockchainFacade:
        instance = self._instances.setdefault(chainMeta['id'], self._simple_build_facade(chainMeta))
        return instance

    def _simple_build_facade(self, chainMeta: ChainMeta) -> BlockchainFacade:
        blockchain_facade = BlockchainFacade(None,
                                             BlockChainVmEnum.EVM,
                                             chainMeta['rpc_url'],
                                             chainMeta['id'],
                                             5_000_000_000)
        return blockchain_facade
