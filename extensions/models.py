# -*- coding: utf-8 -*-
import logging
from django.db import models
from django.core.paginator import Paginator
from django.utils.functional import cached_property

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

class ApxTotalCountAdminPaginator(Paginator):
    @cached_property
    def count(self):
        # TODO multi db type support
        return TableHelper.get_mysql_table_approximate_rows(self.object_list.model)
