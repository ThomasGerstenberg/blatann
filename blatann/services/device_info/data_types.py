from enum import IntEnum
from blatann.services import ble_data_types


class PnpVendorSource(IntEnum):
    bluetooth_sig = 1
    usb_vendor = 2


class PnpId(ble_data_types.BleCompoundDataType):
    data_stream_types = [ble_data_types.Uint8, ble_data_types.Uint16, ble_data_types.Uint16, ble_data_types.Uint16]

    def __init__(self, vendor_id_source, vendor_id, product_id, product_revision):
        super(PnpId, self).__init__()
        self.vendor_id_source = vendor_id_source
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.product_revision = product_revision

    def encode(self):
        return self.encode_values(self.vendor_id_source, self.vendor_id, self.product_id, self.product_revision)

    @classmethod
    def decode(cls, stream):
        vendor_id_source, vendor_id, product_id, product_version = super(PnpId, cls).decode(stream)
        return PnpId(vendor_id_source, vendor_id, product_id, product_version)

    def __repr__(self):
        return "{}(Vendor ID Source: {}, Vendor ID: {}, Product ID: {}, Product Version: {})".format(
            self.__class__.__name__, self.vendor_id_source, self.vendor_id, self.product_id, self.product_revision)


class SystemId(ble_data_types.BleCompoundDataType):
    data_stream_types = [ble_data_types.Uint40, ble_data_types.Uint24]

    def __init__(self, manufacturer_id, organizationally_unique_id):
        super(SystemId, self).__init__()
        self.manufacturer_id = manufacturer_id
        self.organizationally_unique_id = organizationally_unique_id

    def encode(self):
        """
        :rtype: ble_data_types.BleDataStream
        """
        return self.encode_values(self.manufacturer_id, self.organizationally_unique_id)

    @classmethod
    def decode(cls, stream):
        manufacturer_id, organizationally_unique_id = super(SystemId, cls).decode(stream)
        return SystemId(manufacturer_id, organizationally_unique_id)

    def __repr__(self):
        return "{}(Manufacturer ID: {}, OUI: {})".format(self.__class__.__name__, self.manufacturer_id, self.organizationally_unique_id)
