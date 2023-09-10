# -*- coding: utf-8 -*-
import django_filters
import eth_utils

from django_filters.constants import EMPTY_VALUES
from eth_utils import to_checksum_address

class EthChecksumAddressFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()

        address = value if not eth_utils.address.is_address(value) else to_checksum_address(value)
        lookup = '%s__%s' % (self.field_name, self.lookup_expr)
        qs = self.get_method(qs)(**{lookup: address})
        return qs
