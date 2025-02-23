# -*- coding: utf-8 -*-
import os

from django.test.signals import setting_changed

from izumi_infra.utils.setting_helper import AppSettings

DEFAULTS = {
    'ADMIN_SITE_NAME': os.environ.get("IZUMI_INFRA_EXTENSIONS.ADMIN_SITE_NAME", 'iZUMi Finance'),
    # '1.2.3.4,2.3.4.5' like, split with comma
    'ADMIN_SITE_LOGIN_WHITELIST': [ip.strip() for ip in os.environ.get("IZUMI_INFRA_EXTENSIONS.ADMIN_SITE_LOGIN_WHITELIST", '').split(',') if ip.strip()],
    'ALERT_FROM_EMAIL': os.environ.get("IZUMI_INFRA_EXTENSIONS.ALERT_FROM_EMAIL", ''),
    'ENABLE_SEND_ALERT_EMAIL': os.environ.get("IZUMI_INFRA_EXTENSIONS.ENABLE_SEND_ALERT_EMAIL", False),
    'APX_TOTAL_COUNT_BACKEND': os.environ.get("IZUMI_INFRA_ETHERSCAN.APX_TOTAL_COUNT_BACKEND", "default"),

    'SYSTEM_INVOKE_METHOD_LIST': (
        # modulePath.methodName
        ('izumi_infra.extensions.tasks.get_superuser_email_list'),
    ),
    'FILE_BROWSER_PATH': os.environ.get("IZUMI_INFRA_EXTENSIONS.FILE_BROWSER_PATH", '../volumes/store/'),
}

IMPORT_STRINGS = {
    'SYSTEM_INVOKE_METHOD_LIST'
}

USER_SETTING_KEY = 'IZUMI_INFRA_EXTENSIONS'

extensions_settings = AppSettings(USER_SETTING_KEY, DEFAULTS, import_strings=IMPORT_STRINGS)

def reload_api_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == USER_SETTING_KEY:
        extensions_settings.reload()

setting_changed.connect(reload_api_settings)
