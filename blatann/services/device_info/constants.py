from blatann.uuid import Uuid16

# Uuids
DIS_SERVICE_UUID = Uuid16(0x180A)

SYSTEM_ID_UUID = Uuid16(0x2A23)
MODEL_NUMBER_UUID = Uuid16(0x2A24)
SERIAL_NUMBER_UUID = Uuid16(0x2A25)
FIRMWARE_REV_UUID = Uuid16(0x2A26)
HARDWARE_REV_UUID = Uuid16(0x2A27)
SOFTWARE_REV_UUID = Uuid16(0x2A28)
MANUFACTURER_NAME_UUID = Uuid16(0x2A29)
REGULATORY_CERT_UUID = Uuid16(0x2A2A)
PNP_ID_UUID = Uuid16(0x2A50)


class _Characteristic(object):
    def __init__(self, name, uuid):
        self.uuid = uuid
        self.name = name

    def __str__(self):
        return "{} ({})".format(self.name, self.uuid)


SystemIdCharacteristic = _Characteristic("System Id", SYSTEM_ID_UUID)
ModelNumberCharacteristic = _Characteristic("Model Number", MODEL_NUMBER_UUID)
SerialNumberCharacteristic = _Characteristic("Serial Number", SERIAL_NUMBER_UUID)
FirmwareRevisionCharacteristic = _Characteristic("Firmware Revision", FIRMWARE_REV_UUID)
HardwareRevisionCharacteristic = _Characteristic("Hardware Revision", HARDWARE_REV_UUID)
SoftwareRevisionCharacteristic = _Characteristic("Software Revision", SOFTWARE_REV_UUID)
ManufacturerNameCharacteristic = _Characteristic("Manufacturer Name", MANUFACTURER_NAME_UUID)
RegulatoryCertificateCharacteristic = _Characteristic("Regulatory Certificate", REGULATORY_CERT_UUID)
PnpIdCharacteristic = _Characteristic("PNP Id", PNP_ID_UUID)


CHARACTERISTICS = [
    SystemIdCharacteristic,
    ModelNumberCharacteristic,
    SerialNumberCharacteristic,
    FirmwareRevisionCharacteristic,
    HardwareRevisionCharacteristic,
    SoftwareRevisionCharacteristic,
    ManufacturerNameCharacteristic,
    RegulatoryCertificateCharacteristic,
    PnpIdCharacteristic
]

