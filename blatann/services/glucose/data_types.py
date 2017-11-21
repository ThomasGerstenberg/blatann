from enum import IntEnum
from blatann.services import ble_data_types


# See https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.service.glucose.xml
# For more info about the data types and values defined here


class GlucoseConcentrationUnits(IntEnum):
    """
    The concentration units available for reporting glucose levels
    """
    kg_per_liter = 0
    mol_per_liter = 1


class GlucoseType(IntEnum):
    """
    The glucose types available
    """
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
    """
    Location which the blood sample was taken
    """
    finger = 1
    alternate_test_site = 2
    earlobe = 3
    control_solution = 4
    unknown = 15


class MedicationUnits(IntEnum):
    """
    Available units to report medication values in
    """
    milligrams = 0
    milliliters = 1


class CarbohydrateType(IntEnum):
    """
    The type of carbohydrate consumed by the user
    """
    breakfast = 1
    lunch = 2
    dinner = 3
    snack = 4
    drink = 5
    supper = 6
    brunch = 7


class MealType(IntEnum):
    """
    The type of meal consumed
    """
    preprandial = 1   # Before Meal
    postprandial = 2  # After Meal
    fasting = 3
    casual = 4        # Snacks, drinks, etc.
    bedtime = 5


class TesterType(IntEnum):
    """
    Information about who tested the glucose levels
    """
    self = 1
    health_care_professional = 2
    lab_test = 3
    not_available = 15


class HealthStatus(IntEnum):
    """
    Current health status of the user
    """
    minor_issues = 1
    major_issues = 2
    during_menses = 3
    under_stress = 4
    normal = 5
    not_available = 15


class MedicationType(IntEnum):
    """
    Medication type consumed
    """
    rapid_acting_insulin = 1
    short_acting_insulin = 2
    intermediate_acting_insulin = 3
    long_acting_insulin = 4
    premixed_insulin = 5


class SensorStatusType(IntEnum):
    """
    The types of sensor statuses that can be communicated
    """
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
    """
    Class which holds the current sensor status information
    """
    bitfield_width = 16
    bitfield_enum = SensorStatusType

    def __init__(self, *sensor_statuses):
        """
        :param sensor_statuses: The list of SensorStatusTypes that are currently active on the device
        :type sensor_statuses: SensorStatusType
        """
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


class GlucoseFeatureType(IntEnum):
    """
    Enumeration of the supported feature types to be reported
    using the Feature characteristic
    """
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
    """
    Class which holds the features of the glucose sensor and is reported to over bluetooth.
    This is the class used for the Feature characteristic.
    """
    bitfield_width = 16
    bitfield_enum = GlucoseFeatureType

    def __init__(self, *supported_features):
        """
        :param supported_features: The features that are supported by the sensor
        :type supported_features: GlucoseFeatureType
        """
        # Field names must match enum names exactly
        self.low_battery_detection = GlucoseFeatureType.low_battery_detection in supported_features
        self.sensor_malfunction_detection = GlucoseFeatureType.sensor_malfunction_detection in supported_features
        self.sensor_sample_size = GlucoseFeatureType.sensor_sample_size in supported_features
        self.strip_insertion_error_detection = GlucoseFeatureType.strip_insertion_error_detection in supported_features
        self.strip_type_error_detection = GlucoseFeatureType.strip_type_error_detection in supported_features
        self.sensor_result_high_low_detection = GlucoseFeatureType.sensor_result_high_low_detection in supported_features
        self.sensor_temp_high_low_detection = GlucoseFeatureType.sensor_temp_high_low_detection in supported_features
        self.sensor_read_interrupt_detection = GlucoseFeatureType.sensor_read_interrupt_detection in supported_features
        self.general_device_fault = GlucoseFeatureType.general_device_fault in supported_features
        self.time_fault = GlucoseFeatureType.time_fault in supported_features
        self.multiple_bond = GlucoseFeatureType.multiple_bond in supported_features

        super(GlucoseFeatures, self).__init__()


class _MeasurementFlags(ble_data_types.Bitfield):
    """
    Bitfield used in the GlucoseMeasurement struct which defines
    which fields are present in the message
    """
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


class GlucoseSample(ble_data_types.BleCompoundDataType):
    """
    Holds the info about a glucose sample to be reported through the Glucose Measurement characteristic
    """
    def __init__(self, glucose_type, sample_location, value, units=GlucoseConcentrationUnits.kg_per_liter):
        """
        :param glucose_type: The type of blood the glucose sample is from
        :type glucose_type: GlucoseType
        :param sample_location: the body location the sample was taken from
        :type sample_location: SampleLocation
        :param value: The glucose reading taken, in units specified by the units parameter
        :type value: float
        :param units: The units of the glucose sample
        :type units: GlucoseConcentrationUnits
        """
        self.type = glucose_type
        self.value = value
        self.sample_location = sample_location
        # Units are specified in a separate bitfield, not encoded or decoded
        self.units = units

    def encode(self):
        stream = ble_data_types.BleDataStream()
        stream.encode(ble_data_types.SFloat, self.value)
        stream.encode(ble_data_types.DoubleNibble, [self.type, self.sample_location])
        return stream

    @classmethod
    def decode(cls, stream):
        value = stream.decode(ble_data_types.SFloat)
        glucose_type, location = stream.decode(ble_data_types.DoubleNibble)

        return GlucoseSample(glucose_type, location, value)

    def __repr__(self):
        return "{}({}, {}, {}, {})".format(self.__class__.__name__, str(self.type), self.value,
                                           str(self.units), str(self.sample_location))


class GlucoseMeasurement(ble_data_types.BleCompoundDataType):
    """
    Represents a single measurement taken and can be reported over BLE
    """
    def __init__(self, sequence_number, measurement_time, time_offset_minutes=None,
                 sample=None, sensor_status=None, context=None):
        """
        :param sequence_number: the sequence number of the measurement. Mandatory.
        :type sequence_number: int
        :param measurement_time: The time at which the measurement occurred. Must be a datetime struct. Mandatory.
        :type measurement_time: datetime.datetime
        :param time_offset_minutes: The time offset of the measurement, in minutes. Optional.
        :type time_offset_minutes: int
        :param sample: The blood glucose reading. Optional.
        :type sample: GlucoseSample
        :param sensor_status: The status of the glucose sensor. Optional.
        :type sensor_status: SensorStatus
        :param context: The glucose context to be reported with the measurement. Optional
        :type context: GlucoseContext
        """
        self.sequence_number = sequence_number
        self.measurement_time = measurement_time
        self.time_offset_minutes = time_offset_minutes
        self.sample = sample
        self.sensor_status = sensor_status
        self.context = context

    def encode(self):
        stream = ble_data_types.BleDataStream()

        flags = _MeasurementFlags()
        flags.time_offset_present = self.time_offset_minutes is not None
        flags.sample_present = self.sample is not None
        if flags.sample_present:
            flags.concentration_units = int(self.sample.units)
        flags.sensor_status = self.sensor_status is not None
        flags.has_context = self.context is not None

        stream.encode(flags)
        stream.encode(ble_data_types.Uint16, self.sequence_number)
        stream.encode(ble_data_types.DateTime(self.measurement_time))
        stream.encode_if(flags.time_offset_present, ble_data_types.Int16, self.time_offset_minutes)
        stream.encode_if(flags.sample_present, self.sample)
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
        reading = stream.decode_if(flags.sample_present, GlucoseSample)
        if reading:
            reading.units = units
        sensor_status = stream.decode_if(flags.sensor_status, SensorStatus)

        return GlucoseMeasurement(sequence_number, time, time_offset, reading, sensor_status, has_context)

    def __repr__(self):
        params = ["seq: {}".format(self.sequence_number), "time: {}".format(self.measurement_time)]
        if self.time_offset_minutes is not None:
            params.append("time offset: {}".format(self.time_offset_minutes))
        if self.sample:
            params.append(str(self.sample))
        if self.sensor_status:
            params.append(str(self.sensor_status))
        if self.context:
            params.append(str(self.context))

        return "{}({})".format(self.__class__.__name__, ", ".join(params))


class CarbsInfo(ble_data_types.BleCompoundDataType):
    """
    Holds information about the carbs consumed
    """
    def __init__(self, carbs_grams, carb_type):
        """
        :param carbs_grams: The amount of carbs consumed, in grams
        :type carbs_grams: float
        :param carb_type: The type of carbs consumed
        :type carb_type: CarbohydrateType
        """
        self.carbs_grams = carbs_grams
        self.carb_type = carb_type

    def encode(self):
        stream = ble_data_types.BleDataStream()
        stream.encode(ble_data_types.Uint8, self.carb_type)
        stream.encode(ble_data_types.SFloat, self.carbs_grams)
        return stream

    @classmethod
    def decode(cls, stream):
        carb_type, carbs_grams = stream.decode_multiple(ble_data_types.Uint8, ble_data_types.SFloat)
        return CarbsInfo(carb_type, carbs_grams)

    def __repr__(self):
        return "{}({}g, {})".format(self.__class__.__name__, self.carbs_grams, str(self.carb_type))


class ExerciseInfo(ble_data_types.BleCompoundDataType):
    """
    Holds information about the exercise performed with the glucose sample
    """
    # Special value which represents that the exercise duration was longer than what can be reported (uint16 max)
    EXERCISE_DURATION_OVERRUN = 65535

    def __init__(self, duration_seconds, intensity_percent):
        """
        :param duration_seconds: The duration of exercise, in seconds. Can only report up to 65534 seconds over BLE
        :type duration_seconds: int
        :param intensity_percent: The exercise intensity, expressed as a percentage
        :type intensity_percent: int
        """
        self.duration_seconds = duration_seconds
        self.intensity_percent = intensity_percent

    def encode(self):
        stream = ble_data_types.BleDataStream()

        # Clamp duration to max 16-bit, max value means overrun
        duration = max(self.duration_seconds, self.EXERCISE_DURATION_OVERRUN)
        stream.encode(ble_data_types.Uint16, duration)
        stream.encode(ble_data_types.Uint8, self.intensity_percent)
        return stream

    @classmethod
    def decode(cls, stream):
        duration, intensity = stream.decode_multiple(ble_data_types.Uint16, ble_data_types.Uint8)
        return ExerciseInfo(duration, intensity)

    def __repr__(self):
        return "{}({} seconds, {}% intensity)".format(self.__class__.__name__,
                                                      self.duration_seconds, self.intensity_percent)


class MedicationInfo(ble_data_types.BleCompoundDataType):
    """
    Holds information about the medication administered
    """
    def __init__(self, med_type, med_value, med_units=MedicationUnits.milligrams):
        """
        :param med_type: The type of medication administered
        :type med_type: MedicationType
        :param med_value: The amount of medication administered, expressed in units specified
        :type med_value: float
        :param med_units: The units of medication
        :type med_units: MedicationUnits
        """
        self.type = med_type
        self.value = med_value
        # Units are specified in a separate bitfield, not encoded or decoded
        self.units = med_units

    def encode(self):
        stream = ble_data_types.BleDataStream()
        stream.encode(ble_data_types.Uint8, self.type)
        stream.encode(ble_data_types.SFloat, self.value)
        return stream

    @classmethod
    def decode(cls, stream):
        med_type, med_value = stream.decode_multiple(ble_data_types.Uint8, ble_data_types.SFloat)
        return MedicationInfo(med_type, med_value)

    def __repr__(self):
        return "{}({}, {} {})".format(self.__class__.__name__, self.value, str(self.units), str(self.type))


class _GlucoseContextFlags(ble_data_types.Bitfield):
    """
    Bitfield used in the GlucoseContext struct which defines
    which fields are present in the message
    """
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
        self.medication_units = MedicationUnits.milligrams
        self.hba1c_present = False
        self.extended_flags_present = False

        super(_GlucoseContextFlags, self).__init__()


class GlucoseContext(ble_data_types.BleCompoundDataType):
    """
    Class which holds the extra glucose context data associated with the glucose measurement
    """

    def __init__(self, sequence_number, carbs=None, meal_type=None, tester=None, health_status=None,
                 exercise=None, medication=None, hba1c_percent=None, extra_flags=None):
        """
        :param sequence_number: The sequence number that the context corresponds to. Must match the GlucoseMeasurement sequence number
        :type sequence_number: int
        :param carbs: Information about the carbs consumed. Optional.
        :type carbs: CarbsInfo
        :param meal_type: The type of meal the reading was taken with. Optional
        :type meal_type: MealType
        :param tester: Who tested the glucose levels. Optional, must be present if health_status is specified.
        :type tester: TesterType
        :param health_status: The health status of the patient. Optional, must be present if tester is specified.
        :type health_status: HealthStatus
        :param exercise: Information about the exercise performed at time of sample. Optional.
        :type exercise: ExerciseInfo
        :param medication: Information about the medication administered to the patient. Optional.
        :type medication: MedicationInfo
        :param hba1c_percent:
        :param extra_flags:
        """
        self.sequence_number = sequence_number
        self.carbs = carbs
        self.meal_type = meal_type
        self.tester = tester
        self.health_status = health_status
        self.exercise = exercise
        self.medication = medication
        self.hba1c_percent = hba1c_percent
        self.extra_flags = extra_flags

    def encode(self):
        stream = ble_data_types.BleDataStream()

        flags = _GlucoseContextFlags()
        flags.carb_present = self.carbs is not None
        flags.meal_present = self.meal_type is not None
        flags.tester_health_present = self.tester is not None
        flags.exercise_present = self.exercise is not None
        flags.medication_present = self.medication is not None
        if flags.medication_present:
            flags.medication_units = self.medication.units
        flags.hba1c_present = self.hba1c_percent is not None
        flags.extended_flags_present = self.extra_flags is not None

        stream.encode(flags)
        stream.encode(ble_data_types.Uint16, self.sequence_number)

        stream.encode_if(flags.extended_flags_present, ble_data_types.Uint8, self.extra_flags)
        stream.encode_if(flags.carb_present, self.carbs)

        stream.encode_if(flags.meal_present, ble_data_types.Uint8, self.meal_type)
        stream.encode_if(flags.tester_health_present, ble_data_types.DoubleNibble, [self.tester, self.health_status])

        stream.encode_if(flags.exercise_present, self.exercise)

        stream.encode_if(flags.medication_present, self.medication)
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
        carbs = stream.decode_if(flags.carb_present, CarbsInfo)
        meal_type = stream.decode_if(flags.meal_present, ble_data_types.Uint8)
        tester, health = stream.decode_if(flags.tester_health_present, ble_data_types.DoubleNibble)
        exercise = stream.decode_if(flags.exercise_present, ExerciseInfo)
        medication = stream.decode_if(flags.medication_present, MedicationInfo)
        if medication:
            medication.units = med_units
        hba1c = stream.decode_if(flags.hba1c_present, ble_data_types.SFloat)

        return GlucoseContext(sequence_number, carbs, meal_type, tester, health, exercise, medication, hba1c, extended_flags)

    def __repr__(self):
        params = ["seq: {}".format(self.sequence_number)]
        if self.carbs:
            params.append(str(self.carbs))
        if self.meal_type:
            params.append(str(self.meal_type))
        if self.tester:
            params.append(str(self.tester))
        if self.health_status:
            params.append(str(self.health_status))
        if self.exercise:
            params.append(str(self.exercise))
        if self.medication:
            params.append(str(self.medication))
        if self.hba1c_percent:
            params.append("hba1c: {}%".format(self.hba1c_percent))
        if self.extra_flags:
            params.append("extra_flags: {}".format(self.extra_flags))
        return "{}({})".format(self.__class__.__name__, ", ".join(params))
