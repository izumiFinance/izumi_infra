# -*- coding: utf-8 -*-
from enum import Enum


class NoEntriesFound(ValueError):
    """
    Raised when obj not found
    """
    pass

class BizException(Exception):

    def __init__(self, error_enum: Enum, override_error_msg=None, *args: object) -> None:
        self.error_code = error_enum.name
        self.error_msg = error_enum.value if override_error_msg is None else override_error_msg
        super().__init__(*args)
