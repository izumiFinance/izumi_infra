# izumi-infra

## Integrated

1. goto your project src dir
2. `git submodule add git@github.com:izumiFinance/izumi_infra.git`
3. add django app under izumi_infra to `INSTALLED_APPS`, such as `izumi_infra.blockchain` `izumi_infra.etherscan`
4. optional, you can load base fixture data from app fixture dir by `python manage.py loaddata xxx`

## Develop

update izumi_infra package version

1. rewire izumi_infra code until finished
2. izumi_infra submodule git commit
3. `git tag a 'v0.0.1 -m 'Your improve message'` then `git push origin --tags`
4. `git checkout v0.0.1`
5. top git project commit

## Infrastructure App Doc

### blockchain

#### Extend ContractInfoEnum for Contract model type select choice

1. create file `apps/utils/blockchain_const.py` like below:

```py
# -*- coding: utf-8 -*-
from enum import Enum
from izumi_infra.blockchain.constants import BaseContractInfoEnum, BaseTopicEnum, BasicContractInfoEnum
from izumi_infra.utils import abiJsonLoader
from izumi_infra.utils.enum_utils import extend_enum

class ContractABI(Enum):
    HOURAI_ABI = abiJsonLoader.get('apps.gallery.hourai.json')

@extend_enum(BaseContractInfoEnum)
class ContractInfoEnum(BasicContractInfoEnum):
    Hourai = {
        "desc": "Hourai Contract",
        "topic": BaseTopicEnum.topic_list(),
        "abi": ContractABI.HOURAI_ABI.value
    }
```

2. override default enum class for blockchain in `setting.py`

```py
IZUMI_INFRA_BLOCKCHAIN = {
    'CONTRACT_CHOICES_CLASS': 'apps.utils.blockchain_const.ContractInfoEnum'
}
```

#### blockchain conf & fixture

support change default conf by set new object named `IZUMI_INFRA_BLOCKCHAIN`, or set env variable, see
`src/izumi_infra/blockchain/conf.py` for detail.


### etherscan

#### etherscan conf

support change default conf by set new object named `IZUMI_INFRA_ETHERSCAN`, or set env variable, see
`src/izumi_infra/etherscan/conf.py` for detail.

### utils
