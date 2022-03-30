# -*- coding: utf-8 -*-
from django.contrib import admin

from izumi_infra.blockchain.models import (Blockchain, Contract, AccountContractRelationship,
    Account, TranscationSignInfo)

# Register your models here.

class BlockchainAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['__str__', 'chain_id', 'gas_price_wei']
    readonly_fields = ['create_time', 'update_time']

class ContractAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['id', 'chain', '__str__']
    readonly_fields = ['create_time', 'update_time']

class AccountAdmin(admin.ModelAdmin):
    actions = []
    readonly_fields = ['create_time', 'update_time']

class AccountContractRelationshipAdmin(admin.ModelAdmin):
    actions = []
    readonly_fields = ['create_time', 'update_time']


class TranscationSignInfoAdmin(admin.ModelAdmin):
    actions = []
    list_display = ['__str__', 'r_hex', 'create_time']


admin.site.register(Blockchain, BlockchainAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(AccountContractRelationship, AccountContractRelationshipAdmin)
admin.site.register(TranscationSignInfo, TranscationSignInfoAdmin)
