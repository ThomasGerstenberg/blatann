from blatann.bt_sig.uuids import ServiceUuid, CharacteristicUuid

# Uuids
DIS_SERVICE_UUID = ServiceUuid.device_information

SYSTEM_ID_UUID = CharacteristicUuid.system_id
MODEL_NUMBER_UUID = CharacteristicUuid.model_number_string
SERIAL_NUMBER_UUID = CharacteristicUuid.serial_number_string
FIRMWARE_REV_UUID = CharacteristicUuid.firmware_revision_string
HARDWARE_REV_UUID = CharacteristicUuid.hardware_revision_string
SOFTWARE_REV_UUID = CharacteristicUuid.software_revision_string
MANUFACTURER_NAME_UUID = CharacteristicUuid.manufacturer_name_string
REGULATORY_CERT_UUID = CharacteristicUuid.ieee11073_20601_regulatory_certification_data_list
PNP_ID_UUID = CharacteristicUuid.pnp_id


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

