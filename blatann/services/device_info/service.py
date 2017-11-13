import struct
from blatann.services.device_info.constants import *
from blatann.services.device_info.serializers import PnpIdSerializer, SystemIdSerializer
from blatann.gatt.gattc import GattcService
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


class _DisCharacteristic(object):
    def __init__(self, service, uuid):
        self.service = service
        self.uuid = uuid
        self._char = None

    @property
    def is_defined(self):
        return self._char is not None

    @property
    def value(self):
        if self._char:
            return self._char.value
        return None


class _DisServerCharacteristic(_DisCharacteristic):
    def set_value(self, value, max_len=None):
        if not self._char:
            props = GattsCharacteristicProperties(read=True, max_length=max_len or len(value))
            self._char = self.service.add_characteristic(self.uuid, props, value)
        else:
            self._char.set_value(value)


class _DisClientCharacteristic(_DisCharacteristic):
    def __init__(self, service, uuid):
        super(_DisClientCharacteristic, self).__init__(service, uuid)
        self._char = service.find_characteristic(uuid)

    def read(self):
        if not self.is_defined:
            raise AttributeError("Characteristic {} is not present in the Device Info Service".format(self.uuid))
        return self._char.read()


class _DeviceInfoService(object):
    def __init__(self, service):
        if isinstance(service, GattsService):
            char_cls = _DisServerCharacteristic
        elif isinstance(service, GattcService):
            char_cls = _DisClientCharacteristic
        else:
            raise ValueError("Service must be a Gatt Server or Client")

        self._service = service
        self._system_id_char = char_cls(service, SYSTEM_ID_UUID)
        self._model_number_char = char_cls(service, MODEL_NUMBER_UUID)
        self._serial_no_char = char_cls(service, SERIAL_NUMBER_UUID)
        self._firmware_rev_char = char_cls(service, FIRMWARE_REV_UUID)
        self._hardware_rev_char = char_cls(service, HARDWARE_REV_UUID)
        self._software_rev_char = char_cls(service, SOFTWARE_REV_UUID)
        self._mfg_name_char = char_cls(service, MANUFACTURER_NAME_UUID)
        self._regulatory_cert_char = char_cls(service, REGULATORY_CERT_UUID)
        self._pnp_id_char = char_cls(service, PNP_ID_UUID)

        self._characteristics = {
            SystemIdCharacteristic: self._system_id_char,
            ModelNumberCharacteristic: self._model_number_char,
            SerialNumberCharacteristic: self._serial_no_char,
            FirmwareRevisionCharacteristic: self._firmware_rev_char,
            HardwareRevisionCharacteristic: self._hardware_rev_char,
            SoftwareRevisionCharacteristic: self._software_rev_char,
            ManufacturerNameCharacteristic: self._mfg_name_char,
            RegulatoryCertificateCharacteristic: self._regulatory_cert_char,
            PnpIdCharacteristic: self._pnp_id_char
        }

    def has(self, characteristic):
        char = self._characteristics.get(characteristic, None)
        if not char:
            return False
        return char.is_defined

    @property
    def has_system_id(self):
        return self.has(SystemIdCharacteristic)

    @property
    def has_model_number(self):
        return self.has(ModelNumberCharacteristic)

    @property
    def has_serial_number(self):
        return self.has(SerialNumberCharacteristic)

    @property
    def has_firmware_revision(self):
        return self.has(FirmwareRevisionCharacteristic)

    @property
    def has_hardware_revision(self):
        return self.has(HardwareRevisionCharacteristic)

    @property
    def has_software_revision(self):
        return self.has(SoftwareRevisionCharacteristic)

    @property
    def has_manufacturer_name(self):
        return self.has(ManufacturerNameCharacteristic)

    @property
    def has_regulatory_certificate(self):
        return self.has(RegulatoryCertificateCharacteristic)

    @property
    def has_pnp_id(self):
        return self.has(PnpIdCharacteristic)


class DisClient(_DeviceInfoService):
    def __init__(self, gattc_service):
        """
        :type gattc_service: blatann.gatt.gattc.GattcService
        """
        super(DisClient, self).__init__(gattc_service)

    def get(self, characteristic):
        return self._characteristics[characteristic].read()

    def get_system_id(self):
        return self.get(SystemIdCharacteristic)

    def get_model_number(self):
        return self.get(ModelNumberCharacteristic)

    def get_serial_number(self):
        return self.get(SerialNumberCharacteristic)

    def get_firmware_revision(self):
        return self.get(FirmwareRevisionCharacteristic)

    def get_hardware_revision(self):
        return self.get(HardwareRevisionCharacteristic)

    def get_software_revision(self):
        return self.get(SoftwareRevisionCharacteristic)

    def get_manufacturer_name(self):
        return self.get(ManufacturerNameCharacteristic)

    def get_regulatory_certifications(self):
        return self.get(RegulatoryCertificateCharacteristic)

    def get_pnp_id(self):
        return self.get(PnpIdCharacteristic)

    @classmethod
    def find_in_database(cls, gattc_database):
        """
        :type gattc_database: blatann.gatt.gattc.GattcDatabase
        :rtype: DisClient
        """
        service = gattc_database.find_service(DIS_SERVICE_UUID)
        if service:
            return DisClient(service)


class DisServer(_DeviceInfoService):
    def set(self, characteristic, value, max_len=None):
        self._characteristics[characteristic].set_value(value, max_len)

    def set_system_id(self, manufacturer_id, oui, max_len=None):
        value = SystemIdSerializer().encode(manufacturer_id, oui)
        self.set(SystemIdCharacteristic, value, max_len)

    def set_model_number(self, model_number, max_len=None):
        self.set(ModelNumberCharacteristic, model_number, max_len)

    def set_serial_number(self, serial_number, max_len=None):
        self.set(SerialNumberCharacteristic, serial_number, max_len)

    def set_firmware_revision(self, firmware_revision, max_len=None):
        self.set(FirmwareRevisionCharacteristic, firmware_revision, max_len)

    def set_hardware_revision(self, hardware_revision, max_len=None):
        self.set(HardwareRevisionCharacteristic, hardware_revision, max_len)

    def set_software_revision(self, software_revision, max_len=None):
        self.set(SoftwareRevisionCharacteristic, software_revision, max_len)

    def set_manufacturer_name(self, manufacturer_name, max_len=None):
        self.set(ManufacturerNameCharacteristic, manufacturer_name, max_len)

    def set_regulatory_certifications(self, certs):
        raise NotImplementedError()

    def set_pnp_id(self, vendor_id_source, vendor_id, product_id, product_revision):
        value = PnpIdSerializer().encode(vendor_id_source, vendor_id, product_id, product_revision)
        self.set(PnpIdCharacteristic, value)

    @classmethod
    def add_to_database(cls, gatts_database):
        """
        :type gatts_database: blatann.gatt.gatts.GattsDatabase
        """
        service = gatts_database.add_service(DIS_SERVICE_UUID)
        return DisServer(service)
