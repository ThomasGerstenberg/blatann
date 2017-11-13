import struct


class BleDataTypeSerializer(object):
    @staticmethod
    def encode(value):
        raise NotImplementedError()

    @staticmethod
    def decode(stream):
        raise NotImplementedError()


class BleCompoundSerializer(object):
    def __init__(self, *serializers):
        self.serializers = serializers

    def encode(self, *values):
        stream = ""
        for value, serializer in zip(values, self.serializers):
            stream += serializer.encode(value)
        return stream

    def decode(self, stream):
        values = []
        for serializer in self.serializers:
            value, stream = serializer.decode(stream)
            values.append(value)
        return values, stream


class Uint8(BleDataTypeSerializer):
    @staticmethod
    def encode(value):
        return struct.pack("<B", value)

    @staticmethod
    def decode(stream):
        value = struct.unpack("<B", stream[0])[0]
        return value, stream[1:]


class Uint16(BleDataTypeSerializer):
    @staticmethod
    def encode(value):
        return struct.pack("<H", value)

    @staticmethod
    def decode(stream):
        value = struct.unpack("<H", stream[:2])[0]
        return value, stream[2:]


class Uint24(BleDataTypeSerializer):
    @staticmethod
    def encode(value):
        return struct.pack("<I")[:3]

    @staticmethod
    def decode(stream):
        value_stream = stream[:3] + "\x00"
        value = struct.unpack("<I", value_stream)[0]
        return value, stream[3:]


class Uint32(BleDataTypeSerializer):
    @staticmethod
    def encode(value):
        return struct.pack("<I")

    @staticmethod
    def decode(stream):
        value = struct.unpack("<I", stream[:4])[0]
        return value, stream[4:]


class Uint40(BleDataTypeSerializer):
    @staticmethod
    def encode(value):
        return struct.pack("<Q", value)[:5]

    @staticmethod
    def decode(stream):
        value_stream = stream[:5] + "\x00"*3
        value = struct.unpack("<Q", value_stream)[0]
        return value, stream[5:]