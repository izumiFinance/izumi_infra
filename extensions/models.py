# -*- coding: utf-8 -*-
import logging
from typing import Union

from django.db import models
from django.db.models.sql.query import Query
from django.core.paginator import Paginator
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from izumi_infra.extensions.conf import extensions_settings

from izumi_infra.extensions.constants import CommonSettingKeyEnum, CommonSettingStatusEnum

logger = logging.getLogger(__name__)

# Create your models here.
class TableHelper():
    @classmethod
    def get_mysql_table_approximate_rows(cls, tableMode: models.Model) -> int:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                db_name = connection.settings_dict['NAME']
                table_name = tableMode._meta.db_table
                cursor.execute(f"SELECT table_rows FROM information_schema.tables WHERE table_schema='{db_name}' and table_name='{table_name}'")
                row = cursor.fetchone()
                return row[0]
        except Exception as e:
            logger.exception(e)
            return 1

    @classmethod
    def get_mysql_table_explain_rows(cls, query: Query) -> int:
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                # str query will get wrong params format sql
                # ref https://code.djangoproject.com/ticket/17741
                sql, params = query.sql_with_params()
                cursor.execute(f"EXPLAIN {sql}", params)
                row = cursor.fetchone()
                # explain rows col as approximate rows
                return row[9]
        except Exception as e:
            logger.exception(e)
            return 1

class ApxTotalCountAdminPaginator(Paginator):
    @cached_property
    def count(self):
        # TODO multi db type support
        if extensions_settings.APX_TOTAL_COUNT_BACKEND == 'default' or extensions_settings.APX_TOTAL_COUNT_BACKEND == 'schema_total':
            return TableHelper.get_mysql_table_approximate_rows(self.object_list.model)
        else:
            return TableHelper.get_mysql_table_explain_rows(self.object_list.query)

class CommonSetting(models.Model):
    id = models.BigAutoField(primary_key=True)
    create_time = models.DateTimeField("CreateTime", auto_now_add=True)
    update_time = models.DateTimeField("UpdateTime", auto_now=True)
    name = models.CharField("Name", max_length=128)

    key = models.CharField("Key", max_length=128, null=False, blank=False, unique=True)
    value = models.TextField("Value", null=True, blank=True)

    status = models.SmallIntegerField("Status", default=CommonSettingStatusEnum.ENABLE.value, choices=CommonSettingStatusEnum.choices())
    value_type = models.CharField("ValueType", max_length=128)
    # TODO type validate

    class Meta:
        verbose_name = _("CommonSetting")

    @classmethod
    def get_setting(cls: 'CommonSetting', key: CommonSettingKeyEnum) -> Union[str, None]:
        setting = cls.objects.filter(key=key, status=CommonSettingStatusEnum.ENABLE).first()
        return None if not setting else setting.value
