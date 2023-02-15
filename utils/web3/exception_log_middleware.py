# -*- coding: utf-8 -*-
import logging
from typing import Any, Callable, Collection, Type
from web3.types import RPCEndpoint, RPCResponse
from requests import HTTPError, TooManyRedirects, Timeout

logger = logging.getLogger(__name__)

def exception_log_middleware(
    make_request: Callable[[RPCEndpoint, Any], RPCResponse],
    web3: "Web3",
    errors: Collection[Type[BaseException]],
) -> Callable[[RPCEndpoint, Any], RPCResponse]:
    """
    Creates middleware that record exception requests.
    """
    def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
        try:
            return make_request(method, params)
        except errors:
            logger.critical(f"method: {method}, params: {params}, errors: {errors}")
            # errors will caused: exceptions must derive from BaseException
            raise
    return middleware

# see web web3.middleware.exception_retry_request
def rpc_exception_log_middleware(
    make_request: Callable[[RPCEndpoint, Any], Any], web3: "Web3"
) -> Callable[[RPCEndpoint, Any], Any]:
    return exception_log_middleware(
        make_request,
        web3,
        (ConnectionError, HTTPError, Timeout, TooManyRedirects)
    )
