import logging

import pyotp
from captcha.fields import CaptchaField
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from izumi_infra.extensions.conf import extensions_settings
from izumi_infra.extensions.constants import CommonSettingKeyEnum
from izumi_infra.extensions.models import CommonSetting

logger = logging.getLogger(__name__)

class TOTPField(forms.CharField):
    def clean(self, value):
        if not self.required: return
        # use add otp command to add otp
        totp_secret = CommonSetting.get_setting(CommonSettingKeyEnum.InfraExtTOTP)
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(value):
            raise ValidationError("Invalid TOTP code, please retry")
        return value

class IzumiAuthenticationForm(AuthenticationForm):
    captcha = CaptchaField()
    totp = TOTPField(label="TOTP Code", help_text="Enable")

    def __init__(self, request=None, *args, **kwargs) -> None:
        super().__init__(request, *args, **kwargs)
        if CommonSetting.get_setting(CommonSettingKeyEnum.InfraExtTOTP) is None:
            self.fields["totp"].help_text = None
            self.fields["totp"].required = False

    def confirm_login_allowed(self, user):
        if extensions_settings.ADMIN_SITE_LOGIN_WHITELIST:
            x_forward = self.request.META.get('HTTP_X_FORWARDED_FOR')
            request_ip = self.request.META.get('REMOTE_ADDR') if not x_forward else x_forward.split(',')[0]
            logger.info(f"admin login with ip: {request_ip}")
            if request_ip not in extensions_settings.ADMIN_SITE_LOGIN_WHITELIST:
                logger.warning(f"admin login forbidden by ip: {request_ip}")
                raise ValidationError(
                    'forbidden login',
                    code='forbidden',
                )

        return super().confirm_login_allowed(user)
