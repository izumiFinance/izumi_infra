from enum import Enum

def extend_enum(inherited_enum, EnumClz=None):
    def wrapper(added_enum):
        joined = {}
        for item in inherited_enum:
            joined[item.name] = item.value
        for item in added_enum:
            joined[item.name] = item.value
        if EnumClz:
            return EnumClz(added_enum.__name__, joined)
        else:
            return added_enum.__bases__[0](added_enum.__name__, joined)
    return wrapper
