from blatann.services import ble_data_types

# See https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.service.battery_service.xml
# For more info about the data types and values defined here


class BatteryLevel(ble_data_types.Uint8):
    pass
