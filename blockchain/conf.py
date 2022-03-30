from django.test.signals import setting_changed
from izumi_infra.utils.setting_helper import AppSettings
import os

DEFAULTS = {
    'CONTRACT_CHOICES_CLASS': 'izumi_infra.blockchain.constants.BaseContractInfoEnum',
    'SIGN_MAX_RETRY_COUNT': int(os.environ.get("IZUMI_INFRA_BLOCKCHAIN.SIGN_MAX_RETRY_COUNT", 3)),
    'SIGN_RANDOM_GAS_PRICE_WEI_OFFSET': int(os.environ.get("IZUMI_INFRA_BLOCKCHAIN.SIGN_RANDOM_GAS_PRICE_WEI_OFFSET", 10_000)),
}

IMPORT_STRINGS = {
    'CONTRACT_CHOICES_CLASS'
}

USER_SETTING_KEY = 'IZUMI_INFRA_BLOCKCHAIN'

blockchain_settings = AppSettings(USER_SETTING_KEY, DEFAULTS, import_strings=IMPORT_STRINGS)

def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == USER_SETTING_KEY:
        blockchain_settings.reload()

setting_changed.connect(reload_api_settings)
