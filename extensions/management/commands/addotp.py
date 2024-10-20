import logging
import pyotp

from django.core.management.base import BaseCommand, CommandParser

from izumi_infra.extensions.conf import extensions_settings
from izumi_infra.extensions.constants import CommonSettingKeyEnum
from izumi_infra.extensions.models import CommonSetting

def get_otp_uri(secret: str):
    return pyotp.totp.TOTP(secret).provisioning_uri(name='admin', issuer_name=extensions_settings.ADMIN_SITE_NAME)

class Command(BaseCommand):
    """createsuperuser can not be override, separate otp to this command
    """
    help = 'Override properties and methods to customize the command behavior'

    def handle(self, *args, **options):
        logging.info('welcome iZiCreateSuperUser')
        # generate otp by pyotp
        # create model ref to user, and store otp
        # convert otp url to terminal qr code, https://github.com/alishtory/qrcode-terminal
        otp = CommonSetting.objects.filter(key=CommonSettingKeyEnum.InfraExtTOTP).first()
        if otp:
            logging.info(f'OTP already exist, Secret: {otp.value} \r\nURI: {get_otp_uri(otp.value)}')
            return

        # generate and save new otp
        secret =  pyotp.random_base32()
        otp = CommonSetting(
            name='One-Time Password Secret',
            key=CommonSettingKeyEnum.InfraExtTOTP,
            value=secret,
            value_type='string'
        )
        otp.save()

        logging.info(f'Generate OTP success, Secret: {otp.value} \r\nURI: {get_otp_uri(otp.value)}')
