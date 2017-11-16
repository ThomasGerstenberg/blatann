from blatann.services.device_info.service import DisClient as _DisClient, DisServer as _DisServer
from blatann.services.device_info.constants import (
    DIS_SERVICE_UUID, CHARACTERISTICS,
    SystemIdCharacteristic, ModelNumberCharacteristic, SerialNumberCharacteristic, FirmwareRevisionCharacteristic,
    HardwareRevisionCharacteristic, SoftwareRevisionCharacteristic, ManufacturerNameCharacteristic,
    RegulatoryCertificateCharacteristic, PnpIdCharacteristic
)
from blatann.services.device_info.data_types import PnpId, SystemId, PnpVendorSource


def add_device_info_service(gatts_database):
    """
    :rtype: _DisServer
    """
    return _DisServer.add_to_database(gatts_database)


def find_device_info_service(gattc_database):
    """
    :type gattc_database: blatann.gatt.gattc.GattcDatabase
    :rtype: _DisClient
    """
    return _DisClient.find_in_database(gattc_database)
