# -*- coding: utf-8 -*-
from enum import Enum, IntEnum
from typing import List

class StringEnum(Enum):
    def __str__(self) -> str:
        return self._name_

    def __eq__(self, o: object) -> bool:
        return self._name_.__eq__(o)

class IntegerEnum(IntEnum):
    def __eq__(self, o: object) -> bool:
        return self._value_.__eq__(o)

class StringFieldEnum(StringEnum):
    @classmethod
    def choices(cls):
        return [(key.name, key.value) for key in cls]

    def __hash__(self) -> int:
        return self.value.__hash__()

class IntegerFieldEnum(IntegerEnum):
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @classmethod
    def flags(cls):
        return {key.value: key.name for key in cls}

    @classmethod
    def full_flags(cls):
        max_value = max([key.value for key in cls])
        return 2**(max_value + 1) - 1

    @classmethod
    def mark_flags(cls, enum_list: List['IntegerFieldEnum']):
        flags = 0
        for e in enum_list:
            flags = flags | (1 << e.value)
        return flags

    def __hash__(self) -> int:
        return self.value
