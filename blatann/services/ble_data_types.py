import struct


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


class Uint8(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<B", value)

    @classmethod
    def decode(cls, stream):
        value = struct.unpack("<B", stream[0])[0]
        return value, stream[1:]


class Uint16(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<H", value)

    @classmethod
    def decode(cls, stream):
        value = struct.unpack("<H", stream[:2])[0]
        return value, stream[2:]


class Uint24(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<I")[:3]

    @classmethod
    def decode(cls, stream):
        value_stream = stream[:3] + "\x00"
        value = struct.unpack("<I", value_stream)[0]
        return value, stream[3:]


class Uint32(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<I")

    @classmethod
    def decode(cls, stream):
        value = struct.unpack("<I", stream[:4])[0]
        return value, stream[4:]


class Uint40(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<Q", value)[:5]

    @classmethod
    def decode(cls, stream):
        value_stream = stream[:5] + "\x00"*3
        value = struct.unpack("<Q", value_stream)[0]
        return value, stream[5:]


class Uint48(BleDataType):
    @classmethod
    def encode(cls, value):
        return struct.pack("<Q", value)[:6]

    @classmethod
    def decode(cls, stream):
        value_stream = stream[:6] + "\x00"*2
        value = struct.unpack("<Q", value_stream)[0]
        return value, stream[6:]


class String(BleDataType):
    @classmethod
    def encode(cls, value):
        return unicode(value)

    @classmethod
    def decode(cls, stream):
        return stream, ""
