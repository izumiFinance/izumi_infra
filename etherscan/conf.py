# -*- coding: utf-8 -*-
import os

from django.test.signals import setting_changed

from izumi_infra.utils.setting_helper import AppSettings

DEFAULTS = {
    'DEFAULT_MAX_DELIVER_RETRY': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.DEFAULT_MAX_DELIVER_RETRY", 15)),
    'ENTITY_TOUCH_OFFSET_MINUTES': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.ENTITY_TOUCH_OFFSET_MINUTES", 10)),
    'ETHERSCAN_AUDIT_AUTO_FIX_MISSING_TASK': os.environ.get("IZUMI_INFRA_ETHERSCAN.ETHERSCAN_AUDIT_AUTO_FIX_MISSING_TASK", "True") == 'True',
    'ETHERSCAN_AUDIT_TASK_MERGE_MINUTES': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.ETHERSCAN_AUDIT_TASK_MERGE_MINUTES", 60)),
    'ETH_MAX_SCAN_BLOCK': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.ETH_MAX_SCAN_BLOCK", 1000)),
    'SAFE_BLOCK_NUM_OFFSET': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.SAFE_BLOCK_NUM_OFFSET", 6)),
    'TASK_BATCH_SCAN_BLOCK': int(os.environ.get("IZUMI_INFRA_ETHERSCAN.TASK_BATCH_SCAN_BLOCK", 100)),
}

IMPORT_STRINGS = {
}

USER_SETTING_KEY = 'IZUMI_INFRA_ETHERSCAN'

etherscan_settings = AppSettings(USER_SETTING_KEY, DEFAULTS, import_strings=IMPORT_STRINGS)

def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == USER_SETTING_KEY:
        etherscan_settings.reload()

setting_changed.connect(reload_api_settings)
