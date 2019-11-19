import binascii
import logging
from blatann.services import ble_data_types
from blatann.services.device_info.constants import *
from blatann.services.device_info.data_types import PnpId, SystemId
from blatann.event_type import EventSource
from blatann.event_args import DecodedReadCompleteEventArgs
from blatann.waitables import EventWaitable
from blatann.gatt import GattStatusCode
from blatann.gatt.gattc import GattcService
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


logger = logging.getLogger(__name__)


class _DisCharacteristic(object):
    def __init__(self, service, uuid, data_class):
        self.service = service
        self.uuid = uuid
        self._char = None
        self.data_class = data_class

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
    def __init__(self, service, uuid, data_class):
        super(_DisClientCharacteristic, self).__init__(service, uuid, data_class)
        self._char = service.find_characteristic(uuid)
        self._on_read_complete_event = EventSource("Char {} Read Complete".format(self.uuid))

    def _read_complete(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.ReadCompleteEventArgs
        """
        decoded_value = None
        if event_args.status == GattStatusCode.success:
            try:
                stream = ble_data_types.BleDataStream(event_args.value)
                decoded_value = self.data_class.decode(stream)
            except Exception as e:  # TODO not so generic
                logger.error("Service {}, Characteristic {} failed to decode value on read. "
                             "Stream: [{}]".format(self.service.uuid, self.uuid, binascii.hexlify(event_args.value)))
                logger.exception(e)

        decoded_event_args = DecodedReadCompleteEventArgs.from_read_complete_event_args(event_args, decoded_value)
        self._on_read_complete_event.notify(characteristic, decoded_event_args)

    def read(self):
        if not self.is_defined:
            raise AttributeError("Characteristic {} is not present in the Device Info Service".format(self.uuid))
        self._char.read().then(self._read_complete)
        return EventWaitable(self._on_read_complete_event)


class _DeviceInfoService(object):
    def __init__(self, service):
        if isinstance(service, GattsService):
            char_cls = _DisServerCharacteristic
        elif isinstance(service, GattcService):
            char_cls = _DisClientCharacteristic
        else:
            raise ValueError("Service must be a Gatt Server or Client")

        self._service = service
        self._system_id_char = char_cls(service, SYSTEM_ID_UUID, SystemId)
        self._model_number_char = char_cls(service, MODEL_NUMBER_UUID, ble_data_types.String)
        self._serial_no_char = char_cls(service, SERIAL_NUMBER_UUID, ble_data_types.String)
        self._firmware_rev_char = char_cls(service, FIRMWARE_REV_UUID, ble_data_types.String)
        self._hardware_rev_char = char_cls(service, HARDWARE_REV_UUID, ble_data_types.String)
        self._software_rev_char = char_cls(service, SOFTWARE_REV_UUID, ble_data_types.String)
        self._mfg_name_char = char_cls(service, MANUFACTURER_NAME_UUID, ble_data_types.String)
        self._regulatory_cert_char = char_cls(service, REGULATORY_CERT_UUID, ble_data_types.String)
        self._pnp_id_char = char_cls(service, PNP_ID_UUID, PnpId)

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

    def set_system_id(self, system_id):
        """
        :type system_id: SystemId
        """
        if not isinstance(system_id, SystemId):
            raise ValueError("Value must be of type {}".format(SystemId.__name__))
        value = system_id.encode().value
        self.set(SystemIdCharacteristic, value)

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

    def set_pnp_id(self, pnp_id):
        """
        :type pnp_id: PnpId
        """
        assert isinstance(pnp_id, PnpId)
        value = pnp_id.encode().value
        self.set(PnpIdCharacteristic, value)

    @classmethod
    def add_to_database(cls, gatts_database):
        """
        :type gatts_database: blatann.gatt.gatts.GattsDatabase
        """
        service = gatts_database.add_service(DIS_SERVICE_UUID)
        return DisServer(service)
