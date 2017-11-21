from enum import IntEnum
from blatann.services import ble_data_types
from blatann.exceptions import DecodeError


class RacpOpcode(IntEnum):
    report_stored_records = 1
    delete_stored_records = 2
    abort_operation = 3
    report_number_of_records = 4
    number_of_records_response = 5
    response_code = 6


class RacpOperator(IntEnum):
    null = 0
    all_records = 1
    less_than_or_equal_to = 2
    greater_than_or_equal_to = 3
    within_range_inclusive = 4
    first_record = 5
    last_record = 6


class FilterType(IntEnum):
    sequence_number = 1
    user_facing_time = 2


class RacpResponseCode(IntEnum):
    success = 1
    not_supported = 2
    invalid_operator = 3
    operator_not_supported = 4
    invalid_operand = 5
    no_records_found = 6
    abort_not_successful = 7
    procedure_not_completed = 8
    operand_not_supported = 9


class RacpCommand(ble_data_types.BleCompoundDataType):
    def __init__(self, opcode, operator, filter_type=None, filter_params=None):
        """
        :type opcode: RacpOpcode
        :type operator: RacpOperator
        :type filter_type: FilterType
        :param filter_params:
        """
        self.opcode = opcode
        self.operator = operator
        self.filter_type = filter_type
        if filter_params is None:
            filter_params = []
        self.filter_params = filter_params

    def get_filter_min_max(self):
        if self.operator == RacpOperator.all_records:
            return None, None
        if self.operator == RacpOperator.less_than_or_equal_to:
            return None, self.filter_params[0]
        if self.operator == RacpOperator.greater_than_or_equal_to:
            return self.filter_params[0], None
        if self.operator == RacpOperator.within_range_inclusive:
            return self.filter_params[0], self.filter_params[1]
        # First/Last record, return Nones
        return None, None

    def encode(self):
        stream = ble_data_types.BleDataStream()
        stream.encode(ble_data_types.Uint8, self.opcode)
        stream.encode(ble_data_types.Uint8, self.operator)
        if self.filter_type is not None:
            stream.encode(ble_data_types.Uint8, self.filter_type)
            for f in self.filter_params:
                stream.encode(ble_data_types.Uint16, f)
        return stream

    @classmethod
    def decode(cls, stream):
        opcode = stream.decode(ble_data_types.Uint8)
        operator = stream.decode(ble_data_types.Uint8)
        if len(stream) > 0:
            filter_type = stream.decode(ble_data_types.Uint8)
            filter_params = []
            while len(stream) >= 2:
                filter_params.append(stream.decode(ble_data_types.Uint16))
        else:
            filter_type = None
            filter_params = None

        return RacpCommand(opcode, operator, filter_type, filter_params)


class RacpResponse(ble_data_types.BleCompoundDataType):
    def __init__(self, request_opcode=None, response_code=None, record_count=None):
        """
        :type request_opcode: RacpOpcode
        :type response_code: RacpResponseCode
        :type record_count: int
        """
        self.request_code = request_opcode
        self.response_code = response_code
        self.record_count = record_count

    def encode(self):
        stream = ble_data_types.BleDataStream()
        if self.record_count is None:
            stream.encode_multiple([ble_data_types.Uint8, RacpOpcode.response_code],
                                   [ble_data_types.Uint8, RacpOperator.null],
                                   [ble_data_types.Uint8, self.request_code],
                                   [ble_data_types.Uint8, self.response_code])
        else:
            stream.encode_multiple([ble_data_types.Uint8, RacpOpcode.number_of_records_response],
                                   [ble_data_types.Uint8, RacpOperator.null],
                                   [ble_data_types.Uint16, self.record_count])
        return stream

    @classmethod
    def decode(cls, stream):
        opcode = RacpOpcode(stream.decode(ble_data_types.Uint8))
        _ = RacpOperator(stream.decode(ble_data_types.Uint8))

        if opcode == RacpOpcode.response_code:
            request_opcode, response_code = stream.decode_multiple(ble_data_types.Uint8, ble_data_types.Uint8)
            record_count = None
        elif opcode == RacpOpcode.number_of_records_response:
            request_opcode = None
            response_code = None
            record_count = stream.decode(ble_data_types.Uint16)
        else:
            raise DecodeError("Unable to decode RACP Response, got opcode: {}".format(opcode))

        return RacpResponse(request_opcode, response_code, record_count)
