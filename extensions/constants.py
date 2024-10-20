
from izumi_infra.utils.enum import IntegerFieldEnum, StringFieldEnum


class CommonSettingStatusEnum(IntegerFieldEnum):
    DISABLE = 0
    ENABLE = 1

class CommonSettingKeyEnum(StringFieldEnum):
    InfraExtTOTP = 'Infra_Ext_TOTP'

    def __str__(self) -> str:
        return self._value_
