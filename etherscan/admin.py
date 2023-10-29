# -*- coding: utf-8 -*-
from typing import List

from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from izumi_infra.etherscan.admin_helper import ScanConfigContractListFilter, TopicOfContractListFilter

from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.etherscan.constants import (INIT_SUB_STATUS,
                                             ProcessingStatusEnum,
                                             ScanTypeEnum)
from izumi_infra.etherscan.facade.scanEventFacade import (
    execute_unfinished_event_scan_task, scan_contract_event_by_config)
from izumi_infra.etherscan.facade.scanTransFacade import (
    execute_unfinished_trans_scan_task, scan_contract_transactions_by_config)
from izumi_infra.etherscan.models import (ContractEvent, ContractEventScanTask,
                                          ContractTransaction,
                                          ContractTransactionScanTask,
                                          EtherScanConfig)
from izumi_infra.etherscan.utils import mark_as_sync_entity
from izumi_infra.extensions.models import ApxTotalCountAdminPaginator


@admin.register(EtherScanConfig)
class EtherScanConfigAdmin(admin.ModelAdmin):
    # TODO action delete data
    actions = ['do_scan_by_config']
    list_filter = [ScanConfigContractListFilter, 'scan_type', 'status']
    list_display = ('__str__', 'contract', 'scan_type', 'scan_mode', 'status', 'max_deliver_retry','create_time')
    list_select_related = ['contract',]

    @admin.action(description='Do scan by config')
    def do_scan_by_config(self, request, queryset: List[EtherScanConfig]):
        for config in queryset:
            if config.scan_type == ScanTypeEnum.Event:
                scan_contract_event_by_config(config)
            elif config.scan_type == ScanTypeEnum.Transaction:
                scan_contract_transactions_by_config(config)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['contract', 'scan_type', 'from_address_filter_list', 'to_address_filter_list', 'topic_filter_list',
                    'function_filter_list', 'create_time', 'update_time']
        else:
            return ['create_time', 'update_time']

@admin.register(ContractTransactionScanTask)
class ContractTransactionScanTaskAdmin(admin.ModelAdmin):
    actions = ['do_scan_by_task']
    list_filter = ['status', 'contract']
    list_display = ('__str__', 'contract', 'block_range', 'status', 'create_time')
    list_select_related = ['contract',]
    readonly_fields = ['create_time', 'update_time']

    search_fields = ['end_block_id']

    @admin.display(ordering='start_block_id', description='Scan block range')
    def block_range(self, instance: ContractTransactionScanTask):
        # TODO text align
        return "[{} ~ {})".format(instance.start_block_id, instance.end_block_id)

    @admin.action(description='Do scan by task')
    def do_scan_by_task(self, request, queryset):
        for task in queryset:
            execute_unfinished_trans_scan_task(task)

    def get_search_results(self, request, queryset, search_term):
        """
        only search block id range in scan task
        """
        if search_term and search_term.isdigit():
            block_id = int(search_term)
            return queryset.filter(end_block_id__gt=block_id, start_block_id__lte=block_id), False
        return queryset, False

@admin.register(ContractEventScanTask)
class ContractEventScanTaskAdmin(admin.ModelAdmin):
    actions = ['do_scan_by_task']
    list_filter = [ScanConfigContractListFilter, 'status']
    list_display = ('__str__', 'contract', 'block_range', 'status', 'create_time')
    list_select_related = ['contract',]
    readonly_fields = ['create_time', 'update_time']

    search_fields = ['end_block_id']

    # avoid count all
    paginator = ApxTotalCountAdminPaginator if etherscan_settings.ADMIN_PAGE_FAKE_COUNT else Paginator
    show_full_result_count = not etherscan_settings.ADMIN_PAGE_FAKE_COUNT

    @admin.display(ordering='start_block_id', description='Scan block range')
    def block_range(self, instance: ContractEventScanTask):
        # TODO text align
        return "[{} ~ {})".format(instance.start_block_id, instance.end_block_id)

    @admin.action(description='Do scan by task')
    def do_scan_by_task(self, request, queryset):
        for task in queryset:
            execute_unfinished_event_scan_task(task)

    def get_search_results(self, request, queryset, search_term):
        """
        only search block id range in scan task
        """
        if search_term and search_term.isdigit():
            block_id = int(search_term)
            return queryset.filter(end_block_id__gt=block_id, start_block_id__lte=block_id), False
        return queryset, False

@admin.register(ContractTransaction)
class ContractTransactionAdmin(admin.ModelAdmin):
    # TODO search for some field
    actions = ['retouch_trans']
    list_display = ['id', 'contract', 'function_name', 'status', 'block_number', 'create_time']
    readonly_fields = ['create_time']
    list_filter = ['status', 'contract']
    list_select_related = ['contract',]

    search_fields = ['transaction_hash__exact']

    @admin.action(description='Retouch trans')
    def retouch_trans(self, request, queryset: List[ContractTransaction]):
        order_queryset: List[ContractTransaction] = queryset.order_by('block_number', 'transaction_index')
        for trans in order_queryset:
            trans.status = ProcessingStatusEnum.INITIAL
            trans.save()


@admin.register(ContractEvent)
class ContractEventAdmin(admin.ModelAdmin):
    actions = ['retouch_event']
    list_display = ['id', 'contract', 'topic', 'status', 'get_sub_status', 'block_number', 'create_time']
    readonly_fields = ['create_time']

    # TODO TopicOfContractListFilter
    list_filter = ['status', ScanConfigContractListFilter]
    list_select_related = ['contract',]

    search_fields = ['transaction_hash__exact']

    inlines = [] if etherscan_settings.EVENT_ADMIN_INLINES_CLASS is None else [etherscan_settings.EVENT_ADMIN_INLINES_CLASS]

    # avoid count all
    paginator = ApxTotalCountAdminPaginator if etherscan_settings.ADMIN_PAGE_FAKE_COUNT else Paginator
    show_full_result_count = not etherscan_settings.ADMIN_PAGE_FAKE_COUNT

    @admin.action(description='Retouch event')
    def retouch_event(self, request, queryset: List[ContractEvent]):
        order_queryset: List[ContractEvent] = queryset.order_by('block_number', 'log_index')
        for event in order_queryset:
            event.status = ProcessingStatusEnum.INITIAL
            mark_as_sync_entity(event)
            event.save()

    @admin.display(description='SubStatus')
    def get_sub_status(self, contractEvent: ContractEvent):
        if contractEvent.sub_status == INIT_SUB_STATUS:
            return 'NO_SUB_TASK'
        elif contractEvent.sub_status == 0:
            return 'ALL_DONE'
        else:
            return format(contractEvent.sub_status, '08b')
