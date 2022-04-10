# -*- coding: utf-8 -*-
import logging

from izumi_infra.utils.APIStatus import CommonStatus
from izumi_infra.utils.response_util import ResponseUtil
from izumi_infra.utils.exceptions import BizException

logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    """
    Root exception middleware, wrap uncached exception as http response
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Wrap BizException as normal error http response, wrap others as unknown error
        """
        if isinstance(exception, BizException):
            return ResponseUtil.fail_with_exception(exception).to_jsonresponse()

        logger.exception(exception)
        return ResponseUtil.fail_with_enum(CommonStatus.INTERNAL_ERROR).to_jsonresponse()
