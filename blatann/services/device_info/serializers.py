from blatann.services import serializers


class PnpIdSerializer(serializers.BleCompoundSerializer):
    def __init__(self):
        super(PnpIdSerializer, self).__init__(serializers.Uint8, serializers.Uint16, serializers.Uint16, serializers.Uint16)

    def encode(self, vendor_id_source, vendor_id, product_id, product_revision):
        return super(PnpIdSerializer, self).encode(vendor_id_source, vendor_id, product_id, product_revision)

    def decode(self, stream):
        vendor_id_source, vendor_id, product_id, product_version, = super(PnpIdSerializer, self).decode(stream)
        return vendor_id_source, vendor_id, product_id, product_version


class SystemIdSerializer(serializers.BleCompoundSerializer):
    def __init__(self):
        super(SystemIdSerializer, self).__init__(serializers.Uint40, serializers.Uint24)

    def encode(self, manufacturer_id, organizationally_unique_id):
        return super(SystemIdSerializer, self).encode(manufacturer_id, organizationally_unique_id)

    def decode(self, stream):
        manufacturer_id, organizationally_unique_id, = super(SystemIdSerializer, self).decode(stream)
        return manufacturer_id, organizationally_unique_id