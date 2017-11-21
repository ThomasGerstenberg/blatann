from enum import IntEnum

from blatann.exceptions import DecodeError
from blatann.services import ble_data_types


class GlucoseConcentrationUnits(IntEnum):
    kg_per_liter = 0
    mol_per_liter = 1


class GlucoseType(IntEnum):
    capillary_whole_blood = 1
    capillary_plasma = 2
    venous_whole_blood = 3
    venous_plasma = 4
    arterial_whole_blood = 5
    arterial_plasma = 6
    undetermined_whole_blood = 7
    undetermined_plasma = 8
    interstitial_fluid = 9
    control_solution = 10


class SampleLocation(IntEnum):
    finger = 1
    alternate_test_site = 2
    earlobe = 3
    control_solution = 4
    unknown = 15


class SensorStatusType(IntEnum):
    battery_low = 0
    sensor_malfunction = 1
    sample_size_insufficient = 2
    strip_insertion_error = 3
    incorrect_strip_type = 4
    result_above_range = 5
    result_below_range = 6
    sensor_temp_high = 7
    sensor_temp_low = 8
    sensor_read_interrupted = 9
    general_device_fault = 10
    time_fault = 11


class SensorStatus(ble_data_types.Bitfield):
    bitfield_width = 16
    bitfield_enum = SensorStatusType

    def __init__(self, *sensor_statuses):
        # Field names must match enum names exactly
        self.battery_low = SensorStatusType.battery_low in sensor_statuses
        self.sensor_malfunction = SensorStatusType.sensor_malfunction in sensor_statuses
        self.sample_size_insufficient = SensorStatusType.sample_size_insufficient in sensor_statuses
        self.strip_insertion_error = SensorStatusType.strip_insertion_error in sensor_statuses
        self.incorrect_strip_type = SensorStatusType.incorrect_strip_type in sensor_statuses
        self.result_above_range = SensorStatusType.result_above_range in sensor_statuses
        self.result_below_range = SensorStatusType.result_below_range in sensor_statuses
        self.sensor_temp_high = SensorStatusType.sensor_temp_high in sensor_statuses
        self.sensor_temp_low = SensorStatusType.sensor_temp_low in sensor_statuses
        self.sensor_read_interrupted = SensorStatusType.sensor_read_interrupted in sensor_statuses
        self.general_device_fault = SensorStatusType.general_device_fault in sensor_statuses
        self.time_fault = SensorStatusType.time_fault in sensor_statuses

        super(SensorStatus, self).__init__()


class MedicationUnits(IntEnum):
    kilograms = 0
    liters = 1


class CarbohydrateType(IntEnum):
    breakfast = 1
    lunch = 2
    dinner = 3
    snack = 4
    drink = 5
    supper = 6
    brunch = 7


class MealType(IntEnum):
    preprandial = 1
    postprandial = 2
    fasting = 3
    casual = 4
    bedtime = 5


class TesterType(IntEnum):
    self = 1
    health_care_professional = 2
    lab_test = 3
    not_available = 15


class HealthStatus(IntEnum):
    minor_issues = 1
    major_issues = 2
    during_menses = 3
    under_stress = 4
    normal = 5
    not_available = 15


class MedicationType(IntEnum):
    rapid_acting_insulin = 1
    short_acting_insulin = 2
    intermediate_acting_insulin = 3
    long_acting_insulin =4
    premixed_insulin = 5


class GlucoseFeatureTypes(IntEnum):
    low_battery_detection = 0
    sensor_malfunction_detection = 1
    sensor_sample_size = 2
    strip_insertion_error_detection = 3
    strip_type_error_detection = 4
    sensor_result_high_low_detection = 5
    sensor_temp_high_low_detection = 6
    sensor_read_interrupt_detection = 7
    general_device_fault = 8
    time_fault = 9
    multiple_bond = 10


class GlucoseFeatures(ble_data_types.Bitfield):
    bitfield_width = 16
    bitfield_enum = GlucoseFeatureTypes

    def __init__(self, *supported_features):
        # Field names must match enum names exactly
        self.low_battery_detection = GlucoseFeatureTypes.low_battery_detection in supported_features
        self.sensor_malfunction_detection = GlucoseFeatureTypes.sensor_malfunction_detection in supported_features
        self.sensor_sample_size = GlucoseFeatureTypes.sensor_sample_size in supported_features
        self.strip_insertion_error_detection = GlucoseFeatureTypes.strip_insertion_error_detection in supported_features
        self.strip_type_error_detection = GlucoseFeatureTypes.strip_type_error_detection in supported_features
        self.sensor_result_high_low_detection = GlucoseFeatureTypes.sensor_result_high_low_detection in supported_features
        self.sensor_temp_high_low_detection = GlucoseFeatureTypes.sensor_temp_high_low_detection in supported_features
        self.sensor_read_interrupt_detection = GlucoseFeatureTypes.sensor_read_interrupt_detection in supported_features
        self.general_device_fault = GlucoseFeatureTypes.general_device_fault in supported_features
        self.time_fault = GlucoseFeatureTypes.time_fault in supported_features
        self.multiple_bond = GlucoseFeatureTypes.multiple_bond in supported_features

        super(GlucoseFeatures, self).__init__()


class _MeasurementFlags(ble_data_types.Bitfield):
    class Bits(IntEnum):
        time_offset_present = 0
        sample_present = 1
        concentration_units = 2
        sensor_status = 3
        has_context = 4

    bitfield_width = 8
    bitfield_enum = Bits

    def __init__(self):
        self.time_offset_present = False
        self.sample_present = False
        self.concentration_units = GlucoseConcentrationUnits.kg_per_liter
        self.sensor_status = False
        self.has_context = False

        super(_MeasurementFlags, self).__init__()


class GlucoseMeasurement(ble_data_types.BleCompoundDataType):
    def __init__(self, sequence_number, measurement_time, time_offset_minutes=None,
                 value=None, units=GlucoseConcentrationUnits.kg_per_liter,
                 glucose_type=GlucoseType.undetermined_whole_blood, location=SampleLocation.unknown,
                 sensor_status=None, has_context=False):
        self.sequence_number = sequence_number
        self.measurement_time = measurement_time
        self.time_offset_minutes = time_offset_minutes
        self.value = value
        self.units = units
        self.type = glucose_type
        self.location = location
        self.sensor_status = sensor_status
        self.has_context = has_context

    def encode(self):
        stream = ble_data_types.BleDataStream()

        flags = _MeasurementFlags()
        flags.time_offset_present = self.time_offset_minutes is not None
        flags.sample_present = self.value is not None
        flags.concentration_units = int(self.units)
        flags.sensor_status = self.sensor_status is not None
        flags.has_context = self.has_context

        stream.encode(flags)
        stream.encode(ble_data_types.Uint16, self.sequence_number)
        stream.encode(ble_data_types.DateTime, self.measurement_time)

        stream.encode_if(flags.time_offset_present, ble_data_types.Int16, self.time_offset_minutes)

        stream.encode_if_multiple(flags.sample_present,
                                  [ble_data_types.SFloat, self.value],
                                  [ble_data_types.DoubleNibble, [self.type, self.location]])

        stream.encode_if(flags.sensor_status, self.sensor_status)

        return stream

    @classmethod
    def decode(cls, stream):
        flags = stream.decode(_MeasurementFlags)
        sequence_number = stream.decode(ble_data_types.Uint16)
        time = stream.decode(ble_data_types.DateTime)
        units = GlucoseConcentrationUnits(int(flags.concentration_units))
        has_context = flags.has_context

        time_offset = stream.decode_if(flags.time_offset_present, ble_data_types.Int16)
        glucose_value, (glucose_type, location) = stream.decode_if_multiple(flags.sample_present, ble_data_types.SFloat, ble_data_types.DoubleNibble)
        sensor_status = stream.decode_if(flags.sensor_status, SensorStatus)

        measurement = GlucoseMeasurement(sequence_number, time, time_offset, glucose_value, units, glucose_type,
                                         location, sensor_status, has_context)
        return measurement


class _GlucoseContextFlags(ble_data_types.Bitfield):
    class Bits(IntEnum):
        carb_present = 0
        meal_present = 1
        tester_health_present = 2
        exercise_present = 3
        medication_present = 4
        medication_units = 5
        hba1c_present = 6
        extended_flags_present = 7

    bitfield_width = 8
    bitfield_enum = Bits

    def __init__(self):
        self.carb_present = False
        self.meal_present = False
        self.tester_health_present = False
        self.exercise_present = False
        self.medication_present = False
        self.medication_units = MedicationUnits.kilograms
        self.hba1c_present = False
        self.extended_flags_present = False

        super(_GlucoseContextFlags, self).__init__()


class GlucoseContext(ble_data_types.BleCompoundDataType):
    EXERCISE_DURATION_OVERRUN = 65535

    def __init__(self, sequence_number, carb_type=None, carbs_mg=None, meal_type=None,
                 tester=None, health_status=None, exercise_duration_seconds=None, exercise_intensity_percent=None,
                 medication_type=None, medication_value=None, medication_units=MedicationUnits.kilograms,
                 hba1c_percent=None, extra_flags=None):
        self.sequence_number = sequence_number
        self.carb_type = carb_type
        self.carbs_mg = carbs_mg
        self.meal_type = meal_type
        self.tester = tester
        self.health_status = health_status
        self.exercise_duration_seconds = exercise_duration_seconds
        self.exercise_intensity_percent = exercise_intensity_percent
        self.medication_type = medication_type
        self.medication_value = medication_value
        self.medication_units = medication_units
        self.hba1c_percent = hba1c_percent
        self.extra_flags = extra_flags

    def encode(self):
        stream = ble_data_types.BleDataStream()

        flags = _GlucoseContextFlags()
        flags.carb_present = self.carbs_mg is not None
        flags.meal_present = self.meal_type is not None
        flags.tester_health_present = self.tester is not None
        flags.exercise_present = self.exercise_duration_seconds is not None
        flags.medication_present = self.medication_value is not None
        flags.medication_units = self.medication_units
        flags.hba1c_present = self.hba1c_percent is not None
        flags.extended_flags_present = self.extra_flags is not None

        stream.encode(flags)
        stream.encode(ble_data_types.Uint16, self.sequence_number)

        stream.encode_if(flags.extended_flags_present, ble_data_types.Uint8, self.extra_flags)

        stream.encode_if_multiple(flags.carb_present,
                                  [ble_data_types.Uint8, self.carb_type],
                                  [ble_data_types.SFloat, self.carbs_mg])

        stream.encode_if(flags.meal_present, ble_data_types.Uint8, self.meal_type)
        stream.encode_if(flags.tester_health_present, ble_data_types.DoubleNibble, [self.tester, self.health_status])

        duration = max(self.exercise_duration_seconds or 0, self.EXERCISE_DURATION_OVERRUN)  # Clamp to max 16-bit, max value means overrun

        stream.encode_if_multiple(flags.exercise_present,
                                  [ble_data_types.Uint16, duration],
                                  [ble_data_types.Uint8, self.exercise_intensity_percent])

        stream.encode_if_multiple(flags.medication_present,
                                  [ble_data_types.Uint8, self.medication_type],
                                  [ble_data_types.SFloat, self.medication_value])
        stream.encode_if(flags.hba1c_present, ble_data_types.SFloat, self.hba1c_percent)

        return stream

    @classmethod
    def decode(cls, stream):
        """
        :type stream: ble_data_types.BleDataStream
        """
        flags = stream.decode(_GlucoseContextFlags)
        med_units = MedicationUnits(int(flags.medication_units))

        sequence_number = stream.decode(ble_data_types.Uint16)
        extended_flags = stream.decode_if(flags.extended_flags_present, ble_data_types.Uint8)
        carb_type, carbs_mg = stream.decode_multiple(flags.carb_present, ble_data_types.Uint8, ble_data_types.SFloat)
        meal_type = stream.decode_if(flags.meal_present, ble_data_types.Uint8)
        tester, health = stream.decode_if(flags.tester_health_present, ble_data_types.DoubleNibble)
        exercise_duration, exercise_intensity = stream.decode_if_multiple(flags.exercise_present, ble_data_types.Uint16, ble_data_types.Uint8)
        med_type, med_value = stream.decode_if_multiple(flags.medication_present, ble_data_types.Uint8, ble_data_types.SFloat)
        hba1c = stream.decode_if(flags.hba1c_present, ble_data_types.SFloat)

        return GlucoseContext(sequence_number, carb_type, carbs_mg, meal_type, tester, health,
                              exercise_duration, exercise_intensity,
                              med_type, med_value, med_units, hba1c, extended_flags)


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
        if self.record_count is not None:
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
