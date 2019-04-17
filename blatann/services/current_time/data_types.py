import datetime
from enum import IntEnum
from blatann.services import ble_data_types

# See https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.service.current_time.xml
# For more info about the data types and values defined here


class DaylightSavingsTimeOffset(IntEnum):
    standard_time = 0
    half_hour_dst = 2
    full_hour_dst = 4
    two_hour_dst = 8
    unknown = 255

    @staticmethod
    def from_seconds(seconds):
        """
        Converts the DST offset in seconds to one of the above enums.
        Values which do not map directly to an above enum will be mapped to unknown.
        Valid values are essentially 0, 1800 (1/2 hr), 3600 (1 hr), and 7200 (2 hr)

        :param seconds: DST offset in seconds
        :return: The corresponding enum value
        """
        # Figure out what DST enum to use
        dst_15_min_incrs = int((seconds / 3600.0) * 4)
        try:
            return DaylightSavingsTimeOffset(dst_15_min_incrs)
        except:
            # Cannot convert to one of the standard enums, use unknown
            return DaylightSavingsTimeOffset.unknown


class AdjustmentReasonType(IntEnum):
    manual_time_update = 0
    external_time_reference_update = 1
    time_zone_change = 2
    dst_change = 3


class TimeSource(IntEnum):
    unknown = 0
    network_time_protocol = 1
    gps = 2
    radio_time_signal = 3
    manual = 4
    atomic_clock = 5
    cellular_network = 6


class TimeAccuracy(IntEnum):
    out_of_range = 254
    unknown = 255


class AdjustmentReason(ble_data_types.Bitfield):
    bitfield_width = 8
    bitfield_enum = AdjustmentReasonType

    def __init__(self, *adjustment_reasons):
        """
        :param adjustment_reasons: The list of reasons for the time adjustment
        :type adjustment_reasons: AdjustmentReasonType
        """
        self.manual_time_update = AdjustmentReasonType.manual_time_update in adjustment_reasons
        self.external_time_reference_update = AdjustmentReasonType.external_time_reference_update in adjustment_reasons
        self.time_zone_change = AdjustmentReasonType.time_zone_change in adjustment_reasons
        self.dst_change = AdjustmentReasonType.dst_change in adjustment_reasons

        super(AdjustmentReason, self).__init__()


class ExactTime256(ble_data_types.BleCompoundDataType):
    data_stream_types = [ble_data_types.DayDateTime, ble_data_types.Uint8]

    def __init__(self, date):
        """
        :type date: datetime.datetime
        """
        self.datetime = date

    def encode(self):
        stream = ble_data_types.DayDateTime(self.datetime).encode()
        fraction_sec_256 = self.datetime.microsecond * 256.0 / 1E6
        stream.encode(ble_data_types.Uint8, int(fraction_sec_256))
        return stream

    @classmethod
    def decode(cls, stream):
        dt, fraction_sec_256 = super(ExactTime256, cls).decode(stream)  # type: datetime.datetime, int
        dt += datetime.timedelta(microseconds=(1.0E6/256) * fraction_sec_256)
        return dt


class CurrentTime(ble_data_types.BleCompoundDataType):
    """
    Class used to report the current time and reason for adjustment
    """
    data_stream_types = [ExactTime256, AdjustmentReason]

    def __init__(self, date, adjustment_reason=None):
        """
        :type date: datetime.datetime
        """
        self.datetime = date
        self.adjustment_reason = adjustment_reason or AdjustmentReason()

    def encode(self):
        stream = ExactTime256(self.datetime).encode()
        stream.encode(AdjustmentReason, self.adjustment_reason)
        return stream

    @classmethod
    def decode(cls, stream):
        date, adjustment_reason = super(CurrentTime, cls).decode(stream)
        return CurrentTime(date, adjustment_reason)

    def __repr__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.datetime.isoformat(), self.adjustment_reason)


class LocalTimeInfo(ble_data_types.BleCompoundDataType):
    data_stream_types = [ble_data_types.Int8, ble_data_types.Uint8]

    def __init__(self, timezone_offset_hrs=0.0, dst_offset=DaylightSavingsTimeOffset.standard_time):
        self.timezone_offset = timezone_offset_hrs
        self.dst_offset = dst_offset

    def encode(self):
        # Timezone is in 15-min increments, convert from hours to 15-min increments
        tz_offset = int(self.timezone_offset * 4)
        return self.encode_values(tz_offset, self.dst_offset)

    @classmethod
    def decode(cls, stream):
        tz_offset_15min, dst_offset = super(LocalTimeInfo, cls).decode(stream)
        # Convert from 15min increments to hours
        tz_offset_hrs = tz_offset_15min / 4.0
        try:
            dst_offset = DaylightSavingsTimeOffset(dst_offset)
        except:
            pass
        return LocalTimeInfo(tz_offset_hrs, dst_offset)

    def __repr__(self):
        return "{}(Timezone: {}, DST: {})".format(self.__class__.__name__, self.timezone_offset, str(self.dst_offset))


class ReferenceTimeInfo(ble_data_types.BleCompoundDataType):
    data_stream_types = [ble_data_types.Uint8, ble_data_types.Uint8,
                         ble_data_types.Uint8, ble_data_types.Uint8]

    def __init__(self, source=TimeSource.unknown, accuracy_seconds=TimeAccuracy.unknown, hours_since_update=None):
        self.source = source
        self.accuracy = accuracy_seconds
        self.hours_since_update = hours_since_update

    def encode(self):
        if self.accuracy not in [TimeAccuracy.unknown, TimeAccuracy.out_of_range]:
            # Accuracy is reported in 125ms increments (1/8 second)
            accuracy = int(self.accuracy * 8)
        else:
            # Special enum, leave as-is
            accuracy = self.accuracy

        if self.hours_since_update is None:
            days_since_update = 255
            hours_since_update = 255
        else:
            days_since_update = int(self.hours_since_update / 24)
            hours_since_update = int(self.hours_since_update) % 24
            if days_since_update > 255:
                days_since_update = 255
                hours_since_update = 255

        return self.encode_values(self.source, accuracy, days_since_update, hours_since_update)

    @classmethod
    def decode(cls, stream):
        src, accuracy, days_since_update, hrs_since_update = super(ReferenceTimeInfo, cls).decode(stream)

        if hrs_since_update == 255 or days_since_update == 255:
            hrs_since_update = None
        else:
            hrs_since_update += days_since_update*24

        if accuracy not in [TimeAccuracy.unknown, TimeAccuracy.out_of_range]:
            accuracy = accuracy / 8.0
        else:
            accuracy = TimeAccuracy(accuracy)

        try:
            src = TimeSource(src)
        except:
            pass

        return ReferenceTimeInfo(src, accuracy, hrs_since_update)

    def __repr__(self):
        return "{}({}, Accuracy (sec): {}, last update (hrs): {})".format(self.__class__.__name__,
                                                                          str(self.source), str(self.accuracy),
                                                                          self.hours_since_update)
