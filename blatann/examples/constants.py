from blatann.gatt import gatts
from blatann.uuid import Uuid128

PERIPHERAL_NAME = "Periph Test"


# Miscellaneous service, used for testing
MATH_SERVICE_UUID = Uuid128("deadbeef-0011-2345-6679-ab12ccd4f550")

# Hex conversion characteristic. A central writes a byte sequence to this characteristic
# and the peripheral will convert it to its hex representation. e.g. "0123" -> "30313233"
HEX_CONVERT_CHAR_UUID = MATH_SERVICE_UUID.new_uuid_from_base(0xbeaa)

# Counting characteristic. The peripheral will periodically send out a notification on this characteristic
# With a monotonically-increasing, 4-byte little-endian number
COUNTING_CHAR_UUID = MATH_SERVICE_UUID.new_uuid_from_base("1234")

# Properties for the hex conversion and counting characteristics
_HEX_CONVERT_USER_DESC = gatts.GattsUserDescriptionProperties("Hex Converter")
HEX_CONVERT_CHAR_PROPERTIES = gatts.GattsCharacteristicProperties(read=True, notify=True, indicate=True, write=True,
                                                                  max_length=128, variable_length=True,
                                                                  user_description=_HEX_CONVERT_USER_DESC)

_COUNTING_CHAR_USER_DESC = gatts.GattsUserDescriptionProperties("Counter")
COUNTING_CHAR_PROPERTIES = gatts.GattsCharacteristicProperties(read=False, notify=True, max_length=4, variable_length=False,
                                                               user_description=_COUNTING_CHAR_USER_DESC)

# Time service, report's the current time. Also demonstrating another wait to create a UUID
_TIME_SERVICE_BASE_UUID = "beef0000-0123-4567-89ab-cdef01234567"
TIME_SERVICE_UUID = Uuid128.combine_with_base("dead", _TIME_SERVICE_BASE_UUID)

# Time characteristic. When read, reports the peripheral's current time in a human-readable string
TIME_CHAR_UUID = TIME_SERVICE_UUID.new_uuid_from_base("dddd")

# Properties for the time characteristic
_TIME_CHAR_USER_DESC = gatts.GattsUserDescriptionProperties("Current Time")
TIME_CHAR_PROPERTIES = gatts.GattsCharacteristicProperties(read=True, max_length=30, variable_length=True, user_description=_TIME_CHAR_USER_DESC)


DESC_EXAMPLE_SERVICE_UUID = Uuid128("12340000-5678-90ab-cdef-001122334455")
DESC_EXAMPLE_CHAR_UUID = DESC_EXAMPLE_SERVICE_UUID.new_uuid_from_base("0001")
