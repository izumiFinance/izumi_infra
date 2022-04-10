# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from eth_utils import is_address
from eth_utils.address import is_checksum_address


class UppercaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(UppercaseCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).upper()

class LowercaseCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(LowercaseCharField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower()

def validate_eth_address(address):
    # see EIP55
    if not is_address(address):
        raise ValidationError(
            _('%(value)s is not an valid eth address'),
            params={'value': address},
        )

def validate_checksum_address_list(address_list: str):
    addr_list = address_list.split(',')
    for addr in addr_list:
        if addr.strip() and not is_checksum_address(addr):
            raise ValidationError(
                _('%(value)s is not an valid eth checksum address'),
                params={'value': addr},
            )
