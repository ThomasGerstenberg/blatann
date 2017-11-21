import logging
from blatann.services.glucose.constants import *
from blatann.services.glucose.data_types import *
from blatann.services.glucose.racp import *
from blatann.services.glucose.database import IGlucoseDatabase
from blatann.gatt import SecurityLevel
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties


logger = logging.getLogger(__name__)


class GlucoseServer(object):
    def __init__(self, service, glucose_database, security_level=SecurityLevel.OPEN):
        """
        :type service: GattsService
        :type glucose_database: IGlucoseDatabase
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
        self._current_command = None
        self._records_to_report = []  # type: list[GlucoseMeasurement]
        self._active_notifications = []
        self.service.peer.on_disconnect.register(self._on_disconnect)
        self.measurement_characteristic.on_notify_complete.register(self._on_notify_complete)
        self.context_characteristic.on_notify_complete.register(self._on_notify_complete)

    def set_features(self, features):
        """
        :type features: GlucoseFeatures
        """
        self.feature_characteristic.set_value(features.encode().value, False)

    def _report_next_record(self):
        if self._current_command:
            if len(self._records_to_report) > 0:
                next_record = self._records_to_report.pop(0)
                noti_id = self.measurement_characteristic.notify(next_record.encode().value).notification_id
                self._active_notifications.append(noti_id)
                if next_record.context:
                    noti_id = self.context_characteristic.notify(next_record.context.encode().value).notification_id
                    self._active_notifications.append(noti_id)
            else:
                # Done reporting
                response = RacpResponse(self._current_command.opcode, RacpResponseCode.success)
                self._current_command = None
                self.racp_characteristic.notify(response.encode().value)
        return None

    def _on_report_records_request(self, command):
        """
        :type command: RacpCommand
        :return:
        """
        if self._current_command is not None:
            return RacpResponseCode.procedure_not_completed
        if command.filter_type not in [None, FilterType.sequence_number]:
            return RacpResponseCode.operand_not_supported

        if command.operator in [RacpOperator.first_record, RacpOperator.last_record]:
            if command.operator == RacpOperator.first_record:
                record = self.database.first_record()
            else:
                record = self.database.last_record()
            records = [record]
        elif command.operator in [RacpOperator.all_records, RacpOperator.less_than_or_equal_to,
                                  RacpOperator.greater_than_or_equal_to, RacpOperator.within_range_inclusive]:
            min_seq, max_seq = command.get_filter_min_max()
            records = self.database.get_records(min_seq, max_seq)
        else:
            return RacpResponseCode.invalid_operator

        if len(records) == 0:
            return RacpResponseCode.no_records_found

        # Start reporting records
        self._records_to_report = sorted(records, key=lambda r: r.sequence_number)
        self._current_command = command

        self._report_next_record()
        # Do not send a response, will be sent once all records reported
        return None

    def _on_report_num_records_request(self, command):
        min_seq, max_seq = command.get_filter_min_max()
        return self.database.record_count(min_seq, max_seq)

    def _on_delete_records_request(self, command):
        min_seq, max_seq = command.get_filter_min_max()
        return self.database.delete_records(min_seq, max_seq)

    def _on_abort_operation(self):
        if self._current_command is not None:
            self._current_command = None
            self._records_to_report = []
            return RacpResponseCode.success
        return RacpResponseCode.abort_not_successful

    def _on_racp_write(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.WriteEventArgs
        """
        stream = ble_data_types.BleDataStream(event_args.value)
        command = RacpCommand.decode(stream)

        response = None

        if command.opcode == RacpOpcode.report_number_of_records:
            record_count = self._on_report_num_records_request(command)
            response = RacpResponse(record_count=record_count)
        else:
            response_code = None
            if command.opcode == RacpOpcode.report_stored_records:
                response_code = self._on_report_records_request(command)
            elif command.opcode == RacpOpcode.delete_stored_records:
                response_code = self._on_delete_records_request(command)
            elif command.opcode == RacpOpcode.abort_operation:
                response_code = self._on_abort_operation()

            if response_code is not None:
                response = RacpResponse(command.opcode, response_code)

        if response:
            self.racp_characteristic.notify(response.encode().value)

    def _on_notify_complete(self, characteristic, event_args):
        """
        :param characteristic:
        :type event_args: blatann.event_args.NotificationCompleteEventArgs
        """
        if event_args.id in self._active_notifications:
            self._active_notifications.remove(event_args.id)

        if self._current_command is not None:
            self._report_next_record()

    def _on_disconnect(self, peer, event_args):
        self._current_command = None
        self._active_notifications = []
        self._records_to_report = []

    @classmethod
    def add_to_database(cls, gatts_database, glucose_database, security_level=SecurityLevel.OPEN):
        """
        :type gatts_database: blatann.gatt.gatts.GattsDatabase
        """
        service = gatts_database.add_service(GLUCOSE_SERVICE_UUID)
        return GlucoseServer(service, glucose_database, security_level)
