# -*- coding: utf-8 -*-
from izumi_infra.blockchain.context.blockchainContext import BlockchainContext, BaseContext

__all__ = ['BaseContext', 'blockchainHolder', 'contractHolder', 'blockchainSimpleHolder', 'contractMetaHolder']

blockchainHolder = BlockchainContext()
blockchainMetaHolder = BlockchainContext()

from izumi_infra.blockchain.context.contractContext import ContractContext

contractHolder = ContractContext()
contractMetaHolder = ContractContext()
