# -*- coding: utf-8 -*-
import logging
from enum import Enum
from django.http import JsonResponse
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework import pagination
from django.conf import settings
from izumi_infra.utils.APIStatus import CommonStatus

from utils.exceptions import BizException

logger = logging.getLogger(__name__)

class ResponseUtil(Response):
    """
    Utils for normal data structure of RESTful response
    """

    def __init__(self, is_success: bool, data=None, is_idempotent: bool=False, total: int=-1,
                       error_code: str=None, error_msg: str=None, debug_msg: str=None):
        if debug_msg and not settings.DEBUG:
            logger.exception("{}".format(debug_msg))

        content = {
                    "is_success": is_success,
                    "data": data if data is not None else {},
                    "is_idempotent": is_idempotent,
                    "error_code": error_code,
                    "error_msg": error_msg,
                    "total": total,
                  }
        if settings.DEBUG: content["debug_msg"] = debug_msg
        super(ResponseUtil, self).__init__(content, 200)

    def to_jsonresponse(self):
        return JsonResponse(data=self.data)

    @staticmethod
    def success(data=None):
        return ResponseUtil(is_success=True, data=data)

    @staticmethod
    def success_with_list(data, total):
        return ResponseUtil(is_success=True, data=data, total=total)

    @staticmethod
    def fail(error_code, error_msg, debug_msg=None):
        return ResponseUtil(is_success=False, data=None, is_idempotent=False,
                error_code=error_code, error_msg=error_msg, debug_msg=debug_msg)

    @staticmethod
    def fail_with_enum(error_enum: Enum, override_error_msg=None, debug_msg=None):
        error_msg = error_enum.value if override_error_msg is None else override_error_msg
        return ResponseUtil(is_success=False, data=None, is_idempotent=False,
                error_code=error_enum.name, error_msg=error_msg, debug_msg=debug_msg)

    @staticmethod
    def fail_with_exception(exception: BizException, debug_msg=None):
        return ResponseUtil(is_success=False, data=None, is_idempotent=False,
                error_code=exception.error_code, error_msg=exception.error_msg, debug_msg=debug_msg)

class CommonPagination(pagination.PageNumberPagination):
    """
    Custom Pagination
    """
    page_size_query_param = 'page_size'
    page_size = 10
    max_page_size = 100
    max_page_num = 100

    def paginate_queryset(self, queryset, request, view=None):
        try:
            page_number = request.query_params.get(self.page_query_param, None)
            if page_number and int(page_number) > self.max_page_num:
                raise ValidationError('over max page limit')

            return super(CommonPagination, self).paginate_queryset(queryset, request, view=None)
        except NotFound:
            raise BizException(CommonStatus.INVALID_PARAMETER, "Invalid page")
        except ValidationError as e:
            raise BizException(CommonStatus.INVALID_PARAMETER, e.detail[0])
        except Exception as e:
            logger.exception(e)
            raise BizException(CommonStatus.INTERNAL_ERROR)

    def get_paginated_response(self, data):
        return ResponseUtil.success_with_list(data=data, total=self.page.paginator.count)
