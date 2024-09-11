from __future__ import annotations

from blatann.services.device_info.constants import (
    CHARACTERISTICS, DIS_SERVICE_UUID, FirmwareRevisionCharacteristic, HardwareRevisionCharacteristic,
    ManufacturerNameCharacteristic, ModelNumberCharacteristic, PnpIdCharacteristic, RegulatoryCertificateCharacteristic,
    SerialNumberCharacteristic, SoftwareRevisionCharacteristic, SystemIdCharacteristic
)
from blatann.services.device_info.data_types import PnpId, PnpVendorSource, SystemId
from blatann.services.device_info.service import DisClient as _DisClient
from blatann.services.device_info.service import DisServer as _DisServer


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
