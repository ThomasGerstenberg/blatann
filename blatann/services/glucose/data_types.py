from enum import IntEnum
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

    def __init__(self, *sensor_statuses):
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

        bit_mapping = {
            int(SensorStatusType.battery_low): "battery_low",
            int(SensorStatusType.sensor_malfunction): "sensor_malfunction",
            int(SensorStatusType.sample_size_insufficient): "sample_size_insufficient",
            int(SensorStatusType.strip_insertion_error): "strip_insertion_error",
            int(SensorStatusType.incorrect_strip_type): "incorrect_strip_type",
            int(SensorStatusType.result_above_range): "result_above_range",
            int(SensorStatusType.result_below_range): "result_below_range",
            int(SensorStatusType.sensor_temp_high): "sensor_temp_high",
            int(SensorStatusType.sensor_temp_low): "sensor_temp_low",
            int(SensorStatusType.sensor_read_interrupted): "sensor_read_interrupted",
            int(SensorStatusType.general_device_fault): "general_device_fault",
            int(SensorStatusType.time_fault): "time_fault",
        }

        super(SensorStatus, self).__init__(bit_mapping)


class _MeasurementFlags(ble_data_types.Bitfield):
    bitfield_width = 8

    def __init__(self):
        self.time_offset_present = False
        self.sample_present = False
        self.concentration_units = GlucoseConcentrationUnits.kg_per_liter
        self.sensor_status = False
        self.has_context = False

        bit_mapping = {
            0: "time_offset_present",
            1: "sample_present",
            2: "concentration_units",
            3: "sensor_status",
            4: "has_context"
        }

        super(_MeasurementFlags, self).__init__(bit_mapping)


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
        flags = _MeasurementFlags()
        flags.time_offset_present = self.time_offset_minutes is not None
        flags.sample_present = self.value is not None
        flags.concentration_units = int(self.units)
        flags.sensor_status = self.sensor_status is not None
        flags.has_context = self.has_context

        stream = flags.encode() + ble_data_types.Uint16.encode(self.sequence_number) + ble_data_types.DateTime.encode(self.measurement_time)

        if flags.time_offset_present:
            stream += ble_data_types.Int16.encode(self.time_offset_minutes)

        if flags.sample_present:
            stream += ble_data_types.SFloat.encode(self.value)
            stream += ble_data_types.DoubleNibble.encode([self.type, self.location])

        if flags.sensor_status:
            stream += self.sensor_status.encode()

        return stream

    @classmethod
    def decode(cls, stream):
        flags, stream = _MeasurementFlags().decode(stream)
        sequence_number, stream = ble_data_types.Uint16.decode(stream)
        time = ble_data_types.DateTime.decode(stream)

        units = GlucoseConcentrationUnits(int(flags.concentration_units))
        glucose_value = None
        glucose_type = GlucoseType.undetermined_whole_blood
        location = SampleLocation.unknown
        time_offset = None
        has_context = flags.has_context

        if flags.time_offset_present:
            time_offset, stream = ble_data_types.Int16.decode(stream)

        if flags.sample_present:
            glucose_value, stream = ble_data_types.SFloat.decode(stream)
            (glucose_type, location), stream = ble_data_types.DoubleNibble.decode(stream)

        sensor_status = None
        if flags.sensor_status:
            sensor_status, stream = SensorStatus.decode(stream)

        measurement = GlucoseMeasurement(sequence_number, time, time_offset, glucose_value, units, glucose_type,
                                         location, sensor_status, has_context)
        return measurement

