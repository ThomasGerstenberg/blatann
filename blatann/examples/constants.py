from blatann.uuid import Uuid128
from blatann import gatts

PERIPHERAL_NAME = "Periph Test"


# Miscellaneous service, used for testing
SERVICE1_UUID = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")
CHAR1_UUID = SERVICE1_UUID.new_uuid_from_base(0xbeaa)
COUNTING_CHAR_UUID = SERVICE1_UUID.new_uuid_from_base("1234")

# Miscellaneous service characteristic properties
CHAR1_PROPERTIES = gatts.GattsCharacteristicProperties(read=True, notify=True, indicate=True, write=True, max_length=96,
                                                       variable_length=True)
COUNTING_CHAR_PROPERTIES = gatts.GattsCharacteristicProperties(read=False, notify=True, max_length=4,
                                                               variable_length=False)

# Time service, report's the current time
_TIME_SERVICE_BASE_UUID = "beef0000-0123-4567-89ab-cdef01234567"

TIME_SERVICE_UUID = Uuid128.combine_with_base("dead", _TIME_SERVICE_BASE_UUID)
TIME_CHAR_UUID = TIME_SERVICE_UUID.new_uuid_from_base("dddd")

TIME_CHAR_PROPERTIES = gatts.GattsCharacteristicProperties(read=True, max_length=30, variable_length=True)