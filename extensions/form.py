from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
from django.core.exceptions import ValidationError

from captcha.fields import CaptchaField

from izumi_infra.extensions.conf import extensions_settings

import logging

logger = logging.getLogger(__name__)

class IzumiAuthenticationForm(AuthenticationForm):
    captcha = CaptchaField()

    def confirm_login_allowed(self, user):
        if extensions_settings.ADMIN_SITE_LOGIN_WHITELIST:
            x_forward = self.request.META.get('HTTP_X_FORWARDED_FOR')
            request_ip = self.request.META.get('REMOTE_ADDR') if not x_forward else x_forward.split(',')[0]
            logger.info(f"admin login with ip: {request_ip}")
            if request_ip not in extensions_settings.ADMIN_SITE_LOGIN_WHITELIST:
                logger.warn(f"admin login forbidden by ip: {request_ip}")
                raise ValidationError(
                    'forbidden login',
                    code='forbidden',
                )

        return super().confirm_login_allowed(user)
