from django.db import models
from django.db.models import F, Case, When
from django.utils.translation import gettext as _

from izumi_infra.blockchain.models import Contract
from izumi_infra.etherscan.conf import etherscan_settings
from izumi_infra.etherscan.constants import (INIT_SUB_STATUS, MAX_SUB_STATUS_BIT, ProcessingStatusEnum,
                                             ScanConfigAuditLevelEnum,
                                             ScanConfigStatusEnum, ScanModeEnum,
                                             ScanTaskStatusEnum, ScanTypeEnum)
from izumi_infra.utils.model_utils import validate_checksum_address_list

# Create your models here.

class EtherScanConfig(models.Model):
    id = models.BigAutoField(primary_key=True)

    # 如果是 0 地址的合约，地址过滤时将使用本合约的地址
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name = 'RelatedEtherScanConfig')
    scan_type = models.SmallIntegerField("ScanType", default=ScanTypeEnum.Event.value, choices=ScanTypeEnum.choices())
    scan_mode = models.SmallIntegerField("ScanMode", default=ScanModeEnum.Basic.value, choices=ScanModeEnum.choices())

    stable_block_offset = models.PositiveSmallIntegerField("StableBlockOffset", default=etherscan_settings.SAFE_BLOCK_NUM_OFFSET)

    # 如果有这，替代默认的 contract 字段作为过滤地址的地址集合
    to_address_filter_list = models.TextField("ToAddressFilterList", blank=True, default="", validators=[validate_checksum_address_list])

    from_address_filter_list = models.CharField("FromAddressFilterList", max_length=512, blank=True, default="", validators=[validate_checksum_address_list])
    topic_filter_list = models.CharField("TopicFilterList", max_length=256, blank=True, default="")
    function_filter_list = models.CharField("FunctionFilterList", max_length=256, blank=True, default="")

    # 最大重试交付次数，0 不重试
    max_deliver_retry = models.IntegerField("MaxRetryDeliver", default=etherscan_settings.DEFAULT_MAX_DELIVER_RETRY)
    audit_level = models.PositiveIntegerField("AuditLevel", default=ScanConfigAuditLevelEnum.ENABLE.value, choices=ScanConfigAuditLevelEnum.choices())

    status = models.SmallIntegerField("Status", default=ScanConfigStatusEnum.ENABLE.value, choices=ScanConfigStatusEnum.choices())

    create_time = models.DateTimeField("CreateTime", db_index=True, auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    def save(self, *args, **kwargs) -> None:
        # 不允许状态激活的存在多个
        if self.status == ScanConfigStatusEnum.ENABLE:
            EtherScanConfig.objects.filter(
                contract=self.contract,
                scan_type=self.scan_type,
                status=ScanConfigStatusEnum.ENABLE
            ).update(status=ScanConfigStatusEnum.DISABLE)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> None:
        # soft delete, for audit old data
        self.status = ScanConfigStatusEnum.DISABLE
        self.save()

    class Meta:
        verbose_name = _("EtherScanConfig")
        verbose_name_plural = _("EtherScanConfigs")
        index_together = [['scan_type', 'status']]

    def __str__(self):
        return f'EthScanCfg-{self.id}-{getattr(self.contract, "type", "None")}-{ScanTypeEnum(self.scan_type).name}'

class ContractTransactionScanTask(models.Model):
    # TODO 索引
    id = models.BigAutoField(primary_key=True)

    scan_config = models.ForeignKey(EtherScanConfig, on_delete=models.SET_NULL, null=True,
                                    related_name='RelatedTransScanTask', limit_choices_to={'status': ScanConfigStatusEnum.ENABLE})
    contract = models.ForeignKey(
        Contract, on_delete=models.SET_NULL, null=True, related_name='RelatedTransScanTask')

    # 左闭右开
    start_block_id = models.PositiveBigIntegerField("StartBlockId")
    end_block_id = models.PositiveBigIntegerField("EndBlockId", db_index=True)

    status = models.SmallIntegerField("Status", default=ScanTaskStatusEnum.INITIAL.value, choices=ScanTaskStatusEnum.choices())

    create_time = models.DateTimeField("CreateTime", db_index=True, auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    class Meta:
        verbose_name = _("ContractTransactionScanTask")
        verbose_name_plural = _("ContractTransactionScanTask")

    def __str__(self):
        return f'TransScTsk-{self.id}'

class ContractEventScanTask(models.Model):
    id = models.BigAutoField(primary_key=True)

    scan_config = models.ForeignKey(EtherScanConfig, on_delete=models.SET_NULL, null=True,
                                    related_name='RelatedEventScanTask', limit_choices_to={'status': ScanConfigStatusEnum.ENABLE})
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name='RelatedEventScanTask')

    # 左闭右开
    start_block_id = models.PositiveBigIntegerField("StartBlockId")
    end_block_id = models.PositiveBigIntegerField("EndBlockId", db_index=True)

    status = models.SmallIntegerField("Status", default=ScanTaskStatusEnum.INITIAL.value, choices=ScanTaskStatusEnum.choices())

    create_time = models.DateTimeField("CreateTime", db_index=True, auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    def update_as_fail(self, error_info):
        self.error_info = error_info[:1023]
        self.retry_count = self.retry_count + 1
        self.save(update_fields=['error_info', 'retry_count'])

    class Meta:
        verbose_name = _("ContractEventScanTask")
        verbose_name_plural = _("ContractEventScanTasks")
        index_together = [['contract', 'status']]

    def __str__(self):
        return f'EventScanTsk-{self.id}'

class ContractTransaction(models.Model):
    # TODO 索引
    id = models.BigAutoField(primary_key=True)

    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name = 'RelatedContractTrans')
    function_name = models.CharField("FunctionName", max_length=128)

    block_hash = models.CharField("blockHash", max_length=66)
    block_number = models.PositiveBigIntegerField("blockNumber")

    from_address = models.CharField("from", max_length=42)
    to_address = models.CharField("to", max_length=42)

    transaction_hash = models.CharField("hash", max_length=66)
    transaction_index = models.PositiveSmallIntegerField("transactionIndex")

    value = models.CharField("value", max_length=128)
    input_data = models.TextField("input")

    status = models.SmallIntegerField("ProcessStatusStatus", default=ProcessingStatusEnum.INITIAL.value, choices=ProcessingStatusEnum.choices())
    sub_status = models.SmallIntegerField("ProcessSubStatus", default=INIT_SUB_STATUS)
    touch_count_remain = models.IntegerField("TouchCountRemain", default=0)
    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    # block_time = models.DateTimeField("BlockTime")

    def update_status(self, status_enum: ProcessingStatusEnum):
        # avoid trigger signal
        ContractTransaction.objects.filter(id=self.id).update(status=status_enum)

    def update_fields(self, **kwargs):
        # avoid trigger signal
        ContractTransaction.objects.filter(id=self.id).update(**kwargs)

    def mark_sub_status_success(self, sub_status_bit: int):
        update_data = {}
        set_mask = 1 << sub_status_bit
        clean_mask = MAX_SUB_STATUS_BIT ^ set_mask
        update_data['status'] = Case(
            When(sub_status__exact=set_mask, then=ProcessingStatusEnum.PROCESSEDONE),
            default=ProcessingStatusEnum.INITIAL
        )
        update_data['sub_status'] = F('sub_status').bitand(clean_mask)
        ContractTransaction.objects.filter(id=self.id).update(**update_data)

    class Meta:
        verbose_name = _("ContractTransaction")
        verbose_name_plural = _("ContractTransaction")
        index_together = [
            ['contract', 'function_name', 'status'],
            ['status', 'touch_count_remain', 'create_time']
        ]
        unique_together = [['transaction_hash', 'function_name']]

    def __str__(self):
        return f"ContractTrans-{self.id}"

class ContractEvent(models.Model):
    # TODO 索引
    id = models.BigAutoField(primary_key=True)

    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name = 'RelatedEvent')
    topic = models.CharField("Topic", max_length=128)

    block_hash = models.CharField("blockHash", max_length=66)
    block_number = models.PositiveBigIntegerField("blockNumber")

    # address which emit event
    address = models.CharField("emitAddress", max_length=42, blank=True, default="")
    # transaction info from and to
    from_address = models.CharField("fromAddress", max_length=42, blank=True, default="")

    # TODO 关联 ContractTransaction
    transaction_hash = models.CharField("hash", max_length=66)
    log_index = models.PositiveSmallIntegerField("logIndex")

    data = models.TextField("data")

    status = models.SmallIntegerField("ProcessStatus", default=ProcessingStatusEnum.INITIAL.value, choices=ProcessingStatusEnum.choices())
    sub_status = models.IntegerField("ProcessSubStatus", default=INIT_SUB_STATUS)
    touch_count_remain = models.IntegerField("TouchCountRemain", default=0)
    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    # block_time = models.DateTimeField("BlockTime")

    def update_status(self, status_enum: ProcessingStatusEnum):
        # avoid trigger signal
        ContractEvent.objects.filter(id=self.id).update(status=status_enum)

    def update_fields(self, **kwargs):
        # avoid trigger signal
        ContractEvent.objects.filter(id=self.id).update(**kwargs)

    def mark_sub_status_success(self, sub_status_bit: int):
        update_data = {}
        set_mask = 1 << sub_status_bit
        clean_mask = MAX_SUB_STATUS_BIT ^ set_mask
        update_data['status'] = Case(
            When(sub_status__exact=set_mask, then=ProcessingStatusEnum.PROCESSEDONE),
            default=ProcessingStatusEnum.INITIAL
        )
        update_data['sub_status'] = F('sub_status').bitand(clean_mask)
        ContractEvent.objects.filter(id=self.id).update(**update_data)

    class Meta:
        verbose_name = _("ContractEvent")
        verbose_name_plural = _("ContractEvent")
        index_together = [
            ['contract', 'topic', 'status'],
            ['status', 'touch_count_remain', 'create_time']
        ]
        unique_together = [['transaction_hash', 'log_index']]

    def __str__(self):
        return f"ContractEvent-{self.id}"
