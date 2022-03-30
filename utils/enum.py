# -*- coding: utf-8 -*-
from enum import Enum, IntEnum

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

    def __hash__(self) -> int:
        return self.value
