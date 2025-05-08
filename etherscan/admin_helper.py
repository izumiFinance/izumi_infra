# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from izumi_infra.etherscan.models import ContractEvent, EtherScanConfig


class TopicOfContractListFilter(admin.SimpleListFilter):
    """
    admin will opt filter with ChoicesFieldListFilter、RelatedFieldListFilter,
    but topic will distinct all data.
    This class show topic selection only on contract is selected according to db index
    """
    title = _('topicOfContract')
    parameter_name = 'contract__topic__exact'

    def lookups(self, request, model_admin):
        # get contract filter data, return topic filter option
        contract = request.GET.get('contract__id__exact', '')
        if contract:
            contract_query = ContractEvent.objects.filter(contract=contract)
        else:
            contract_query = ContractEvent.objects.none()

        return contract_query.values_list('topic', 'topic').distinct()

    def queryset(self, request, queryset):
        # get contract filter data, filter by contract and topic according to db index
        contract = request.GET.get('contract__id__exact', '')
        if contract and self.value():
            return queryset.filter(topic=self.value())

        return queryset

class ScanConfigContractListFilter(admin.SimpleListFilter):
    title = _('contract')
    parameter_name = 'contract__id__exact'

    def lookups(self, request, model_admin):
        return EtherScanConfig.objects.select_related('contract').values_list('contract__id', 'contract__name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(contract__id=self.value())
        return queryset
