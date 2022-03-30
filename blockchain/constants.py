# -*- coding: utf-8 -*-
from enum import Enum
from typing import List, Tuple
from izumi_infra.utils.enum import StringFieldEnum, IntegerFieldEnum
from izumi_infra.utils import abiJsonLoader

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

class BlockChainVmEnum(StringFieldEnum):
    EVM = "EVM"

class ChainIdEnum(IntegerFieldEnum):
    EthereumMainnet = 1
    Rinkeby = 4
    Optimism = 10
    BSC = 56
    Gatechain = 86
    BSCTestnet = 97
    Heco = 128
    Matic = 137
    Fantom = 250
    Izumi = 1337
    Arbitrum = 42161
    MaticTestnet = 80001
    Harmony = 1666600000
    HarmonyTestnet = 1666700000

# ChainMeta like
ChainConfig = {
    ChainIdEnum.EthereumMainnet: {
        'id': ChainIdEnum.EthereumMainnet,
        'rpc_url': 'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161'
    }
}

class TokenSymbol(StringFieldEnum):
    USDC = 'USDC'
    ETH = 'ETH'
    USDT = 'USDT'
    DAI = 'DAI'
    BIT = 'BIT'
    iZi = 'iZi'
    MIM = 'MIM'
    stETH = 'STETH'
    SPELL = 'SPELL'
    LIDO = 'LIDO'
    WETH = 'WETH'
    YIN = 'YIN'

    RDT = 'RDT'
    RDT2 = 'RDT2'

UPPER_SYMBOL_MAPPING = { t.value.upper(): t.value for t in TokenSymbol }

def correct_symbol(symbol: str):
    symbol_upper = symbol.upper()
    return UPPER_SYMBOL_MAPPING.get(symbol_upper, symbol_upper)

# basic TokenMeta like
TokenConfig = {
    ChainIdEnum.EthereumMainnet: {
        TokenSymbol.USDT: {
            'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'symbol': TokenSymbol.USDT,
            'decimal': 6
        },
        TokenSymbol.USDC: {
            'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'symbol': TokenSymbol.USDC,
            'decimal': 6
        },
        TokenSymbol.iZi: {
            'address': '0x9ad37205d608B8b219e6a2573f922094CEc5c200',
            'symbol': TokenSymbol.iZi,
            'decimal': 18
        },
        TokenSymbol.WETH: {
            'address': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'symbol': TokenSymbol.WETH,
            'decimal': 18
        },
        TokenSymbol.YIN: {
            'address': '0x794Baab6b878467F93EF17e2f2851ce04E3E34C8',
            'symbol': TokenSymbol.YIN,
            'decimal': 18
        },
    },
    ChainIdEnum.Matic: {
        TokenSymbol.USDT: {
            'address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            'symbol': TokenSymbol.USDT,
            'decimal': 6
        },
        TokenSymbol.USDC: {
            'address': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            'symbol': TokenSymbol.USDC,
            'decimal': 6
        },
        TokenSymbol.iZi: {
            'address': '0x60D01EC2D5E98Ac51C8B4cF84DfCCE98D527c747',
            'symbol': TokenSymbol.iZi,
            'decimal': 18
        },
        TokenSymbol.YIN: {
            'address': '0x794Baab6b878467F93EF17e2f2851ce04E3E34C8',
            'symbol': TokenSymbol.YIN,
            'decimal': 18
        },
    },
     ChainIdEnum.Arbitrum: {
        TokenSymbol.USDT: {
            'address': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'symbol': TokenSymbol.USDT,
            'decimal': 6
        },
        TokenSymbol.USDC: {
            'address': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
            'symbol': TokenSymbol.USDC,
            'decimal': 6
        },
        TokenSymbol.iZi: {
            'address': '0x60D01EC2D5E98Ac51C8B4cF84DfCCE98D527c747',
            'symbol': TokenSymbol.iZi,
            'decimal': 18
        },
    }
}

TokenConfigAddrMapping = { c: { t['address']: t for t in v.values() } for c, v in TokenConfig.items() }

class AccountContractRelationshipTypeEnum(StringFieldEnum):
    OWNER = "Account is the contract owner"
    TRUSTED = "Account trusted by contract"

    @staticmethod
    def get_trusted_above():
        return [AccountContractRelationshipTypeEnum.OWNER, AccountContractRelationshipTypeEnum.TRUSTED]

class ContractStatusEnum(IntegerFieldEnum):
    INITIAL = 0
    DEPLOYED = 1
    ACTIVATED = 2
    DISCARDED = -1

class BaseTopicEnum(StringFieldEnum):
    @classmethod
    def topic_list(cls):
        return [key.name for key in cls]

class ERC20TopicEnum(BaseTopicEnum):
    Transfer = 'Transfer'
    Approval = 'Approval'

class UniswapNonfungiblePositionManagerTopicEnum(BaseTopicEnum):
    IncreaseLiquidity = 'IncreaseLiquidity'
    DecreaseLiquidity = 'DecreaseLiquidity'
    Collect = 'Collect'

class UniswapV3PoolTopicEnum(BaseTopicEnum):
    Burn = 'Burn'
    Collect = 'Collect'
    CollectProtocol = 'CollectProtocol'
    Flash = 'Flash'
    IncreaseObservationCardinalityNext = 'IncreaseObservationCardinalityNext'
    Initialize = 'Initialize'
    Mint = 'Mint'
    SetFeeProtocol = 'SetFeeProtocol'
    Swap = 'Swap'


class BaseContractABI(Enum):
    # ERC
    ERC20_ABI = abiJsonLoader.get('izumi_infra.blockchain.erc.erc20.json')

    # Unisawp v3
    UNISWAP_SWAP_ROUTER_ABI = abiJsonLoader.get('izumi_infra.blockchain.uniswap.UniswapV3SwapRouter.json')
    UNISWAP_NONFUNGIBLE_POSITION_MANAGER_ABI = abiJsonLoader.get('izumi_infra.blockchain.uniswap.UniswapPositionManager.json')
    UNISWAP_POOL_ABI = abiJsonLoader.get('izumi_infra.blockchain.uniswap.UniswapV3Pool.json')
    UNISWAP_FACTORY_ABI = abiJsonLoader.get('izumi_infra.blockchain.uniswap.UniswapV3Factory.json')

class BasicContractInfoEnum(Enum):
    def __str__(self) -> str:
        return self._name_

    def __eq__(self, o: object) -> bool:
        return self._name_.__eq__(o)

    @classmethod
    def contract_type_choices(cls):
        return [(key.name, key.value['desc']) for key in cls]

    @classmethod
    def all_topic_choices(cls):
        all = []
        for i in cls: all.extend(i.topic_choices)
        return all

    @property
    def topic_choices(self) -> List[Tuple]:
        return [(value, "{} - {}".format(self.name, value)) for value in self.value['topic']]

    @property
    def contract_name(self) -> str:
        # TODO contract_name filed ?
        return self.name

    @property
    def desc(self) -> str:
        return self.value["desc"]

    @property
    def topic(self) -> List[str]:
        return self.value["topic"]

    @property
    def abi(self) -> str:
        return self.value['abi']


class BaseContractInfoEnum(BasicContractInfoEnum):
    ERC20 = {
        "desc": "ERC20 Token",
        "topic": ERC20TopicEnum.topic_list(),
        "abi": BaseContractABI.ERC20_ABI.value
    }

    NonfungiblePositionManager = {
        "desc": "Uniswap NonfungiblePositionManager Contract",
        "topic": UniswapNonfungiblePositionManagerTopicEnum.topic_list(),
        "abi": BaseContractABI.UNISWAP_NONFUNGIBLE_POSITION_MANAGER_ABI.value
    }

    SwapRouter = {
        "desc": "Uniswap SwapRouter Contract",
        "topic": [],
        "abi": BaseContractABI.UNISWAP_SWAP_ROUTER_ABI.value
    }

    UniswapV3Pool = {
        "desc": "Uniswap UniswapV3Pool Contract",
        "topic": UniswapV3PoolTopicEnum.topic_list(),
        "abi": BaseContractABI.UNISWAP_POOL_ABI.value
    }

    UniswapV3Factory = {
        "desc": "Uniswap UniswapV3Factory Contract",
        "topic": BaseTopicEnum.topic_list(),
        "abi": BaseContractABI.UNISWAP_FACTORY_ABI.value
    }
