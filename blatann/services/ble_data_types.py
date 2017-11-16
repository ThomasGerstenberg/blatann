import math
import struct
import datetime


class BleCompoundDataType(object):
    data_stream_types = []

    def encode(self, *values):
        stream = ""
        for value, data_type in zip(values, self.data_stream_types):
            stream += data_type.encode(value)
        return stream

    @classmethod
    def decode(cls, stream):
        values = []
        for data_type in cls.data_stream_types:
            value, stream = data_type.decode(stream)
            values.append(value)
        return values, stream


class BleDataType(object):
    @classmethod
    def encode(cls, value):
        raise NotImplementedError()

    @classmethod
    def decode(cls, stream):
        raise NotImplementedError()


class DoubleNibble(BleDataType):
    @classmethod
    def encode(cls, value):
        # value should be a list of two integers
        v = (value[0] & 0xF0) | (value[1] & 0x0F)
        return struct.pack("<B", v)

    @classmethod
    def decode(cls, stream):
        value = struct.unpack("<B", stream[0])[0]
        return [value >> 4 & 0x0F, value & 0x0F], stream[1:]


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
        value_stream = stream[:cls.byte_count] + "\x00" * (cls._decode_size()-cls.byte_count)
        value = struct.unpack(cls._formatter(), value_stream)[0]
        return value, stream[cls.byte_count:]


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


class Uint40(UnsignedIntegerBase):
    byte_count = 5


class Uint48(UnsignedIntegerBase):
    byte_count = 6


class Uint56(UnsignedIntegerBase):
    byte_count = 7


class Uint64(UnsignedIntegerBase):
    byte_count = 8


class String(BleDataType):
    @classmethod
    def encode(cls, value):
        return unicode(value)

    @classmethod
    def decode(cls, stream):
        return stream, ""


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
        value_int = struct.unpack("<H", stream[:2])[0]
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

        return value, stream[2:]


class DateTime(BleCompoundDataType):
    data_stream_types = [Uint16, Uint8, Uint8, Uint8, Uint8, Uint8]

    @classmethod
    def encode(cls, dt):
        """
        :type dt: datetime.datetime
        """
        return super(DateTime, cls).encode(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    @classmethod
    def decode(cls, stream):
        [y, mo, d, h, m, s], stream = super(DateTime, cls).decode(stream)
        return datetime.datetime(y, mo, d, h, m, s), stream


class Bitfield(BleCompoundDataType):
    bitfield_width = 8

    _width_encoder_map = {
        8: Uint8,
        16: Uint16,
        24: Uint24,
        32: Uint32,
        40: Uint40,
        48: Uint48,
        56: Uint56,
        64: Uint64,
    }

    def __init__(self, bit_to_field_name_mapping):
        assert self.bitfield_width % 8 == 0
        assert(max(bit_to_field_name_mapping.keys()) < self.bitfield_width)
        self._mapping = bit_to_field_name_mapping

    def encode(self):
        value = 0
        for bit, attr_name in self._mapping.items():
            bit_value = getattr(self, attr_name)
            if bit_value:
                value |= 1 << bit

        return self._width_encoder_map[self.bitfield_width].encode(value)

    @classmethod
    def decode(cls, stream):
        bitfield = cls()
        value, stream = cls._width_encoder_map[cls.bitfield_width].decode(stream)

        for bit, attr_name in bitfield._mapping.items():
            if ((value & 1) << bit) > 0:
                setattr(bitfield, attr_name, True)

        return bitfield, stream
