# -*- coding: utf-8 -*-

# TODO continue abstract BaseContext
class BaseContext():
    """
    Base context class
    """
    def __init__(self):
        self._instances = {}

    def get_context_size(self):
        return len(self._instances)

    def clear_context(self):
        self._instances = {}
