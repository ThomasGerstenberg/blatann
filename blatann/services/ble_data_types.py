from enum import IntEnum
import math
import struct
import datetime


class BleDataStream(object):
    def __init__(self, value=b""):
        self.value = value
        self.decode_index = 0

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return repr(self.value)

    def __getitem__(self, item):
        return self.value[item]

    def __len__(self):
        return len(self.value) - self.decode_index

    def encode(self, ble_type, *values):
        stream = ble_type.encode(*values)
        if isinstance(stream, BleDataStream):
            self.value += stream.value
        else:
            self.value += stream

    def encode_multiple(self, *ble_type_value_pairs):
        for type_values in ble_type_value_pairs:
            self.encode(type_values[0], *type_values[1:])

    def encode_if(self, conditional, ble_type, *values):
        if conditional:
            self.encode(ble_type, *values)

    def encode_if_multiple(self, conditional, *ble_type_value_pairs):
        if conditional:
            self.encode_multiple(*ble_type_value_pairs)

    def decode(self, ble_type):
        return ble_type.decode(self)

    def decode_if(self, conditional, ble_type):
        if conditional:
            return self.decode(ble_type)

    def decode_multiple(self, *ble_types):
        return map(self.decode, ble_types)

    def decode_if_multiple(self, conditional, *ble_types):
        if conditional:
            return self.decode_multiple(*ble_types)
        return [None] * len(ble_types)

    def take(self, num_bytes):
        s = self.value[self.decode_index:self.decode_index + num_bytes]
        self.decode_index += num_bytes
        return s

    def take_all(self):
        s = self.value[self.decode_index:]
        self.decode_index = len(self.value)
        return s


class BleCompoundDataType(object):
    data_stream_types = []

    def encode_values(self, *values):
        """
        :rtype: BleDataStream
        """
        stream = BleDataStream()
        for value, data_type in zip(values, self.data_stream_types):
            stream.encode(data_type, value)
        return stream

    def encode(self):
        """
        :rtype: BleDataStream
        """
        raise NotImplementedError()

    @classmethod
    def decode(cls, stream):
        """
        :type stream: BleDataStream or bytes
        :return: The values decoded from the stream
        :rtype: tuple
        """
        if isinstance(stream, bytes):
            stream = BleDataStream(stream)
        values = []
        for data_type in cls.data_stream_types:
            value = stream.decode(data_type)
            values.append(value)
        return values

    @classmethod
    def encoded_size(cls):
        size = 0
        for t in cls.data_stream_types:
            size += t.encoded_size()
        return size


class BleDataType(object):
    @classmethod
    def encode(cls, value):
        raise NotImplementedError()

    @classmethod
    def decode(cls, stream):
        """
        :type stream: BleDataStream
        """
        raise NotImplementedError()

    @classmethod
    def encoded_size(cls):
        raise NotImplementedError()


class DoubleNibble(BleDataType):
    @classmethod
    def encode(cls, value):
        # value should be a list of two integers
        v = ((value[0] & 0x0F) << 4) | (value[1] & 0x0F)
        return struct.pack("<B", v)

    @classmethod
    def decode(cls, stream):
        """
        :type stream: BleDataStream
        """
        value = struct.unpack("<B", stream.take(1))[0]
        return [value >> 4 & 0x0F, value & 0x0F]

    @classmethod
    def encoded_size(cls):
        return 1


class UnsignedIntegerBase(BleDataType):
    signed = False
    byte_count = 1
    _bytes_to_struct_formats = {
        1: "b",
        2: "h",
        4: "i",
        8: "q"
    }

    @classmethod
    def _decode_size(cls):
        return 2**(cls.byte_count - 1).bit_length()

    @classmethod
    def _formatter(cls):
        f = cls._bytes_to_struct_formats[cls._decode_size()]
        return "<{}".format(f if cls.signed else f.upper())

    @classmethod
    def encode(cls, value):
        return struct.pack(cls._formatter(), value)[:cls.byte_count]

    @classmethod
    def decode(cls, stream):
        """
        :type stream: BleDataStream
        """
        value_stream = stream.take(cls.byte_count) + b"\x00" * (cls._decode_size()-cls.byte_count)
        value = struct.unpack(cls._formatter(), value_stream)[0]
        return value

    @classmethod
    def encoded_size(cls):
        return cls.byte_count


class SignedIntegerBase(UnsignedIntegerBase):
    signed = True


class Int8(SignedIntegerBase):
    byte_count = 1


class Uint8(UnsignedIntegerBase):
    byte_count = 1


class Int16(SignedIntegerBase):
    byte_count = 2


class Uint16(UnsignedIntegerBase):
    byte_count = 2


class Uint24(UnsignedIntegerBase):
    byte_count = 3


class Uint32(UnsignedIntegerBase):
    byte_count = 4


class Int32(SignedIntegerBase):
    byte_count = 4


class Uint40(UnsignedIntegerBase):
    byte_count = 5


class Uint48(UnsignedIntegerBase):
    byte_count = 6


class Uint56(UnsignedIntegerBase):
    byte_count = 7


class Uint64(UnsignedIntegerBase):
    byte_count = 8


class Int64(SignedIntegerBase):
    byte_count = 8


class String(BleDataType):
    @classmethod
    def encode(cls, value):
        return value.encode("utf8")

    @classmethod
    def decode(cls, stream):
        # TODO: Are strings null-terminated in BLE types?
        return stream.take_all()


class SFloat(BleDataType):
    class ReservedMantissaValues(object):
        POS_INFINITY = 0x07FE
        NEG_INFINITY = 0x0802
        NAN = 0x07FF
        NRES = 0x0800
        RESERVED = 0x0801

        ALL_NAN = [NAN, NRES, RESERVED]

    _mantissa_max = 0x07FD
    _exponent_max = 7
    _exponent_min = -8
    _sfloat_max = 20450000000
    _sfloat_min = -_sfloat_max
    _epsilon = 1e-8
    _precision = 10000

    @classmethod
    def _encode_value(cls, value):
        # Function taken from here: https://github.com/signove/antidote/blob/master/src/util/bytelib.c#L491
        value = float(value)
        sign = 1.0 if value >= 0 else -1.0
        mantissa = abs(value)
        exponent = 0

        # Convert float into the exponent-mantissa pair.  Exponent is base-10
        while mantissa > cls._mantissa_max:
            mantissa /= 10.0
            exponent += 1

            # Secondary check to ensure exponent is in bounds
            if exponent > cls._exponent_max:
                return cls.ReservedMantissaValues.POS_INFINITY if sign > 0 else cls.ReservedMantissaValues.NEG_INFINITY

        while mantissa < 1:
            mantissa *= 10.0
            exponent -= 1

            # Secondary check to ensure exponent is in bounds
            if exponent < cls._exponent_min:
                return 0

        # scale down if number needs more precision
        s_mantissa = round(mantissa * cls._precision)
        r_mantissa = round(mantissa) * cls._precision
        diff = abs(s_mantissa - r_mantissa)

        while diff > 0.5 and exponent > cls._exponent_min and mantissa*10 <= cls._mantissa_max:
            mantissa *= 10.0
            exponent -= 1
            s_mantissa = round(mantissa * cls._precision)
            r_mantissa = round(mantissa) * cls._precision
            diff = abs(s_mantissa - r_mantissa)

        int_mantissa = int(round(sign * mantissa))
        value = ((exponent & 0x000F) << 12) | (int_mantissa & 0x0FFF)
        return value

    @classmethod
    def encode(cls, value):
        if math.isnan(value):
            value = cls.ReservedMantissaValues.NAN
        if value > cls._sfloat_max:
            value = cls.ReservedMantissaValues.POS_INFINITY
        elif value < cls._sfloat_min:
            value = cls.ReservedMantissaValues.NEG_INFINITY
        else:
            value = cls._encode_value(value)

        return struct.pack("<H", value)

    @classmethod
    def decode(cls, stream):
        # Function taken from here: https://github.com/signove/antidote/blob/master/src/util/bytelib.c#L281
        value_int = struct.unpack("<H", stream.take(2))[0]
        mantissa = value_int & 0x0FFF
        exponent = value_int >> 12

        # Get the 2s complement if the value is greater than 8
        if exponent > cls._exponent_max:
            exponent = -(0x10 - exponent)

        if mantissa >= 0x0800:
            mantissa = -((0x0FFF+1) - mantissa)

        if mantissa == cls.ReservedMantissaValues.POS_INFINITY:
            value = float("inf")
        elif mantissa == cls.ReservedMantissaValues.NEG_INFINITY:
            value = float("-inf")
        elif mantissa in cls.ReservedMantissaValues.ALL_NAN:
            value = float("nan")
        else:
            value = mantissa * 10.0**exponent

        return value

    @classmethod
    def encoded_size(cls):
        return 2  # 16-bit


class DateTime(BleCompoundDataType):
    data_stream_types = [Uint16, Uint8, Uint8, Uint8, Uint8, Uint8]

    def __init__(self, dt):
        """
        :type dt: datetime.datetime
        """
        self.dt = dt

    def encode(self):
        return self.encode_values(self.dt.year, self.dt.month, self.dt.day,
                                  self.dt.hour, self.dt.minute, self.dt.second)

    @classmethod
    def decode(cls, stream):
        y, mo, d, h, m, s = super(DateTime, cls).decode(stream)
        return datetime.datetime(y, mo, d, h, m, s)


class DayOfWeek(IntEnum):
    unknown = 0
    monday = 1
    tuesday = 2
    wednesday = 3
    thursday = 4
    friday = 5
    saturday = 6
    sunday = 7


class DayDateTime(BleCompoundDataType):
    data_stream_types = [DateTime, Uint8]

    def __init__(self, dt):
        """
        :type dt: datetime.datetime
        """
        self.dt = dt

    def encode(self):
        stream = DateTime(self.dt).encode()
        # datetime weekdays are 0-6 (mon-sun), convert to 1-7 (mon-sun)
        weekday = self.dt.weekday() + 1
        stream.encode(Uint8, weekday)
        return stream

    @classmethod
    def decode(cls, stream):
        """
        :rtype: datetime.datetime
        """
        dt, day_of_week = super(DayDateTime, cls).decode(stream)
        return dt  # Do we care about the day of week at this point?


class Bitfield(BleCompoundDataType):
    bitfield_width = 8
    bitfield_enum = None

    _width_type_map = {
        8: Uint8,
        16: Uint16,
        24: Uint24,
        32: Uint32,
        40: Uint40,
        48: Uint48,
        56: Uint56,
        64: Uint64,
    }

    def __init__(self):
        assert self.bitfield_width % 8 == 0
        assert type(self.bitfield_enum), IntEnum
        self._mapping = {enum.value: enum.name for enum in self.bitfield_enum}
        assert max(self._mapping.keys()) < self.bitfield_width

    def _iter_bits(self):
        for bit, attr_name in sorted(self._mapping.items()):
            yield bit, attr_name

    def encode(self):
        stream = BleDataStream()
        value = 0
        for bit, attr_name in self._iter_bits():
            bit_value = getattr(self, attr_name)
            if bit_value:
                value |= 1 << bit
        stream.encode(self._encoder_class(), value)
        return stream

    @classmethod
    def _encoder_class(cls):
        return cls._width_type_map[cls.bitfield_width]

    @classmethod
    def decode(cls, stream):
        value = cls._encoder_class().decode(stream)
        return cls.from_integer_value(value)

    @classmethod
    def from_integer_value(cls, value):
        bitfield = cls()
        for bit, attr_name in bitfield._iter_bits():
            if (value & (1 << bit)) > 0:
                setattr(bitfield, attr_name, True)

        return bitfield

    @classmethod
    def byte_count(cls):
        return cls._encoder_class().byte_count

    @classmethod
    def encoded_size(cls):
        return cls.byte_count()

    def __repr__(self):
        set_bit_strs = []

        for bit, attr_name in self._iter_bits():
            if getattr(self, attr_name):
                set_bit_strs.append("{}({})".format(attr_name, bit))
        return "{}({})".format(self.__class__.__name__, ", ".join(set_bit_strs))


