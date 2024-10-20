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
3. `git tag a v0.0.1 -m 'Your improve message'` then `git push origin --tags`
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
`izumi_infra/blockchain/conf.py` for detail.

### etherscan

#### etherscan conf

support change default conf by set new object named `IZUMI_INFRA_ETHERSCAN`, or set env variable, see
`izumi_infra/etherscan/conf.py` for detail.

### extensions

#### admin login ip limit and captcha

add izumi_infra.extensions at your INSTALLED_APPS.

```py
# add izumi_infra/extensions/templates to TEMPLATES.DIRS
TEMPLATES = [
    {
        ...
        'DIRS': [os.path.join(BASE_DIR, "templates/"), os.path.join(BASE_DIR, "../izumi_infra/extensions/templates/")],
        ...
    },
]

# add url to your root project url setting, remind add this path to your admin nginx proxy
urlpatterns = [
    ...
    path('', include('izumi_infra.extensions.urls')),
]

# custom your Captcha conf, ref: https://django-simple-captcha.readthedocs.io/en/latest/
# like math captcha
CAPTCHA_IMAGE_SIZE = (80, 45)
CAPTCHA_LENGTH = 6
CAPTCHA_TIMEOUT = 1

CAPTCHA_OUTPUT_FORMAT = '%(image)s %(text_field)s %(hidden_field)s '
CAPTCHA_NOISE_FUNCTIONS = (
    'captcha.helpers.noise_null',
    'captcha.helpers.noise_arcs',
    'captcha.helpers.noise_dots',
)
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'

```

Then you may add nginx config like below, if you use nginx.

```conf
location ^~ /admin/ {
    proxy_set_header Host $proxy_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header x-forwarded-for $proxy_add_x_forwarded_for;
    proxy_pass ...
}
```

limit ip and admin site title conf see `izumi_infra/extensions/conf.py`.

#### django manage commands

features:

- `abitypegen` generate typing files of Python by Contract abi file
  - example: `python manage.py abitypegen izumi_infra/blockchain/data/abi/erc/erc20.json`
- `backupdb` backup database as sql file
- `cleanup` reset database for django project initial
- `loaddatax` load fixtures data with ignore
- `sqldiff` show different of schema between database and django model
- `dbshell`
- `iredis`
- `addotp`

#### async log for sending alert email

1. config AsyncEmailAlertLogHandler as FATAL level handlers.

```py
# django config file
LOGGING = {
    'handlers': {
        ...
        'email-alert': {
            'level': 'FATAL',
            'class': 'izumi_infra.extensions.AsyncEmailAlertLogHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'XXX': {
            'handlers': [..., 'email-alert'],
        }
    }
}
```

2. add email which receive alert email to your superuser by admin page, or config at [ADMINS](https://docs.djangoproject.com/en/4.1/ref/settings/#admins). custom email from user will use first not blank value of `extensions_settings.ALERT_FROM_EMAIL`, `settings.SERVER_EMAIL`, `settings.DEFAULT_FROM_EMAIL` or default **alert@notifications.izumi.finance**

3. config django email backend, example

```py
# django config file
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_PORT = XXX
EMAIL_HOST = XXX
EMAIL_HOST_USER = XXX
EMAIL_HOST_PASSWORD = XXX
```

4. set `ENABLE_SEND_ALERT_EMAIL` to `True` at your `IZUMI_INFRA_EXTENSIONS` config

#### system invoke

You can invoke method which register by `SYSTEM_INVOKE_METHOD_LIST` in admin page, required super user permission.

```py
# django config file
IZUMI_INFRA_EXTENSIONS = {
    'SYSTEM_INVOKE_METHOD_LIST': (
        # module path, method name
        ('izumi_infra.extensions.tasks', 'get_superuser_email_list'),
    )
}
```

Then you invoke method at `admin/extensions/system-invoke` page.

#### file browser

At `admin/extensions/file-browser/`, you can list download or delete file in dir by config:

```py
# django config file
IZUMI_INFRA_EXTENSIONS = {
    'FILE_BROWSER_PATH': 'PATH_TO_BROWSER_FILES'
}
```

#### admin login 2FA with OTP

### utils

### middleware

add it to your django conf like

```py
MIDDLEWARE = [
    ...
    'izumi_infra.middleware.exception_handler.ExceptionMiddleware'
]
```
