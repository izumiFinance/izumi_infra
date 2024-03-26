# -*- coding: utf-8 -*-
from django.contrib import admin

from izumi_infra.blockchain.models import (Blockchain, Contract, AccountContractRelationship,
    Account, TransactionSignInfo)

# Register your models here.

@admin.register(Blockchain)
class BlockchainAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['__str__', 'chain_id', 'gas_price_wei']
    readonly_fields = ['create_time', 'update_time']

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    actions = None
    list_display = ['id', 'chain', '__str__', 'contract_address']
    list_select_related = ['chain',]
    readonly_fields = ['create_time', 'update_time']
    list_filter = ['chain', 'type']

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    actions = []
    readonly_fields = ['create_time', 'update_time']

@admin.register(AccountContractRelationship)
class AccountContractRelationshipAdmin(admin.ModelAdmin):
    actions = []
    readonly_fields = ['create_time', 'update_time']


@admin.register(TransactionSignInfo)
class TransactionSignInfoAdmin(admin.ModelAdmin):
    actions = []
    list_display = ['__str__', 'r_hex', 'create_time']
