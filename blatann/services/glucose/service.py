import logging
from blatann.services import ble_data_types
from blatann.services.glucose.constants import *
from blatann.services.glucose.data_types import *
from blatann.services.glucose.database import AbstractGlucoseDatabase
from blatann.event_type import EventSource
from blatann.event_args import DecodedReadCompleteEventArgs
from blatann.waitables import EventWaitable
from blatann.gatt import GattStatusCode, SecurityLevel
from blatann.gatt.gattc import GattcService
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


logger = logging.getLogger(__name__)


class BloodGlucoseServer(object):
    def __init__(self, service, glucose_database, security_level=SecurityLevel.OPEN):
        """
        :type service: GattsService
        :type glucose_database: AbstractGlucoseDatabase
        :param security_level:
        """
        self.service = service
        self.database = glucose_database

        measurement_char_props = GattsCharacteristicProperties(read=False, notify=True, max_length=20)
        feature_props = GattsCharacteristicProperties(read=True, max_length=GlucoseFeatures.byte_count(),
                                                      variable_length=False)
        racp_props = GattsCharacteristicProperties(read=False, write=True, indicate=True, max_length=20,
                                                   variable_length=True, security_level=security_level)
        self.measurement_characteristic = service.add_characteristic(MEASUREMENT_CHARACTERISTIC_UUID, measurement_char_props)
        self.context_characteristic = service.add_characteristic(MEASUREMENT_CONTEXT_CHARACTERISTIC_UUID, measurement_char_props)
        self.feature_characteristic = service.add_characteristic(FEATURE_CHARACTERISTIC_UUID, feature_props)
        self.racp_characteristic = service.add_characteristic(RACP_CHARACTERISTIC_UUID, racp_props)
        self.racp_characteristic.on_write.register(self._on_racp_write)

    def set_features(self, features):
        """
        :type features: GlucoseFeatures
        """
        self.feature_characteristic.set_value(features.encode(), False)

    def _on_racp_write(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.WriteEventArgs
        """
        stream = ble_data_types.BleDataStream(event_args.value)
        command = RacpCommand.decode(stream)

        min_seq, max_seq = command.get_filter_min_max()

        if command.opcode == RacpOpcode.report_stored_records:
            pass
        elif command.opcode == RacpOpcode.report_number_of_records:
            pass
        


    @classmethod
    def add_to_database(cls, gatts_database, glucose_database, security_level=SecurityLevel.OPEN):
        """
        :type gatts_database: blatann.gatt.gatts.GattsDatabase
        """
        service = gatts_database.add_service(GLUCOSE_SERVICE_UUID)
        return BloodGlucoseServer(service, glucose_database, security_level)
