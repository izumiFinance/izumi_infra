# -*- coding: utf-8 -*-
from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext as _
from django.core.validators import MaxValueValidator

from izumi_infra.blockchain.constants import ContractStatusEnum, BlockChainVmEnum, AccountContractRelationshipTypeEnum
from izumi_infra.blockchain.conf import blockchain_settings
from izumi_infra.utils.model_utils import validate_eth_address


class Blockchain(models.Model):
    fullname = models.CharField("Name", max_length=128, default="")
    symbol = models.CharField("Symbol", unique=True, max_length=30, default="")
    vm_type = models.CharField("VmType", max_length=30, default=BlockChainVmEnum.EVM.value, choices=BlockChainVmEnum.choices())

    rpc_url = models.CharField("RPCUrl", max_length=300, default="")
    ws_rpc_url = models.CharField("WebsocketRPCUrl", max_length=300, default="", blank=True)
    scan_url = models.CharField("ScanUrl", max_length=300, default="", blank=True)
    chain_id = models.PositiveBigIntegerField("ChainId", unique=True, primary_key=True)

    gas_price_wei = models.PositiveBigIntegerField("GasPriceWei", default=5_000_000_000, validators=[MaxValueValidator(100_000_000_000)])

    token_note = models.JSONField("TokenNote", default=dict, blank=True)

    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    def __str__(self):
        return f"Blockchain-{self.symbol}"

class Contract(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField("Name", unique=True, max_length=128)
    type = models.CharField("Type", max_length=64, choices=blockchain_settings.CONTRACT_CHOICES_CLASS.contract_type_choices())
    status = models.SmallIntegerField("Status", default=ContractStatusEnum.INITIAL.value, choices=ContractStatusEnum.choices())

    chain = models.ForeignKey(Blockchain, on_delete=models.SET_NULL, null=True, related_name='RelatedContract')

    contract_address = models.CharField("ContractAddress", max_length=128, default="", validators=[validate_eth_address])

    accounts = models.ManyToManyField('Account', through='AccountContractRelationship')

    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    class Meta:
        verbose_name = _("contract")
        verbose_name_plural = _("contract")
        unique_together = [['chain', 'contract_address', 'type']]

    def __str__(self):
        return self.name

class Account(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField("Name", unique=True, max_length=64)
    account_address = models.CharField("AccountAddress", max_length=128, default="", validators=[validate_eth_address])
    private_key = models.CharField("PrivateKey", max_length=128, default="")
    contracts = models.ManyToManyField(Contract, through='AccountContractRelationship')

    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")

    def __str__(self):
        return self.name

# TODO non-bridge refactor
class AccountContractRelationship(models.Model):
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name = 'Relation')
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, related_name = 'Relation')
    relation_type = models.CharField("RelationType", max_length=32, choices=AccountContractRelationshipTypeEnum.choices())

    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)

    class Meta:
        verbose_name = _("AccountContractRelationship")
        verbose_name_plural = _("AccountContractRelationships")
        unique_together = [['account', 'relation_type', 'contract']]

    def __str__(self):
        return f"{self.account} <--{self.relation_type}--> {self.contract}"

class TransactionSignInfo(models.Model):
    # 32 byte, 64 hex, add 0x then 66
    r_hex = models.CharField("rHex", unique=True, max_length=66)
    create_time = models.DateTimeField("CreateTime", auto_now_add=True)

    def insert(self):
        try:
            self.save()
            return True
        except IntegrityError:
            return False

    class Meta:
        verbose_name = _("TransactionSignInfo")
        verbose_name_plural = _("TransactionSignInfo")

    def __str__(self):
        return self.r_hex[:8]
