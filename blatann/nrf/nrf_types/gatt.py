from enum import Enum
import logging
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_types.generic import BLEUUID, BLEUUIDBase
from blatann.nrf.nrf_types.smp import *
from blatann.nrf.nrf_types.enums import *
from blatann.utils import repr_format

logger = logging.getLogger(__name__)

NoneType = type(None)


BLE_GATT_HANDLE_INVALID = driver.BLE_GATT_HANDLE_INVALID

"""
GATT Classes
"""
# TODO: BleGattCharExtProps


class BleGattEnableParams(object):
    def __init__(self, max_att_mtu=0):
        self.att_mtu = max_att_mtu

    def to_c(self):
        params = driver.ble_gatt_enable_params_t()
        params.att_mtu = self.att_mtu
        return params


class BLEGattCharacteristicProperties(object):
    def __init__(self, broadcast=False, read=False, write_wo_resp=False,
                 write=False, notify=False, indicate=False, auth_signed_wr=False):
        self.broadcast = broadcast
        self.read = read
        self.write_wo_resp = write_wo_resp
        self.write = write
        self.notify = notify
        self.indicate = indicate
        self.auth_signed_wr = auth_signed_wr

    @classmethod
    def from_c(cls, gattc_char_props):
        return cls(gattc_char_props.broadcast == 1,
                   gattc_char_props.read == 1,
                   gattc_char_props.write_wo_resp == 1,
                   gattc_char_props.write == 1,
                   gattc_char_props.notify == 1,
                   gattc_char_props.indicate == 1,
                   gattc_char_props.auth_signed_wr == 1)

    def to_c(self):
        params = driver.ble_gatt_char_props_t()
        params.broadcast = int(self.broadcast)
        params.read = int(self.read)
        params.write_wo_resp = int(self.write_wo_resp)
        params.write = int(self.write)
        params.notify = int(self.notify)
        params.indicate = int(self.indicate)
        params.auth_signed_wr = int(self.auth_signed_wr)
        return params


class BLEGattExtendedCharacteristicProperties(object):
    def __init__(self, reliable_write=False, writable_aux=False):
        self.reliable_write = reliable_write
        self.writable_aux = writable_aux

    def to_c(self):
        params = driver.ble_gatt_char_ext_props_t()
        params.reliable_wr = int(self.reliable_write)
        params.wr_aux = int(self.writable_aux)
        return params

    @classmethod
    def from_c(cls, params):
        return cls(params.reliable_wr, params.wr_aux)


class BLEGattService(object):
    srvc_uuid = BLEUUID(BLEUUID.Standard.service_primary)

    def __init__(self, uuid, start_handle, end_handle):
        self.uuid = uuid
        self.start_handle = start_handle
        self.end_handle = end_handle
        self.chars = []
        self.attrs = []

    @classmethod
    def from_c(cls, gattc_service):
        return cls(uuid=BLEUUID.from_c(gattc_service.uuid),
                   start_handle=gattc_service.handle_range.start_handle,
                   end_handle=gattc_service.handle_range.end_handle)

    def char_add(self, char):
        char.end_handle = self.end_handle
        self.chars.append(char)
        if len(self.chars) > 1:
            self.chars[-2].end_handle = char.handle_decl - 1

    def __repr__(self):
        return "{}(uuid={}, start_handle={}, end_handle={})".format(self.__class__.__name__, self.uuid,
                                                                    self.start_handle, self.end_handle)


class BLEGattCharacteristic(object):
    char_uuid = BLEUUID(BLEUUID.Standard.characteristic)

    def __init__(self, uuid, handle_decl, handle_value, data_decl=None, data_value=None, char_props=None):
        self.uuid = uuid
        self.handle_decl = handle_decl
        self.handle_value = handle_value
        self.data_decl = data_decl
        self.data_value = data_value
        self.char_props = char_props  # TODO: if None, parse first byte of data_decl?
        self.end_handle = None
        self.descs = list()

    def discovered_handles(self):
        return sorted([self.handle_decl, self.handle_value] + [d.handle for d in self.descs])

    def missing_handles(self):
        all_handles = set(range(self.handle_decl, self.end_handle+1))
        return sorted(all_handles - set(self.discovered_handles()))

    @classmethod
    def from_c(cls, gattc_char):
        return cls(uuid=BLEUUID.from_c(gattc_char.uuid),
                   handle_decl=gattc_char.handle_decl,
                   handle_value=gattc_char.handle_value,
                   char_props=BLEGattCharacteristicProperties.from_c(gattc_char.char_props))

    def __repr__(self):
        return "{}(uuid={}, handle_decl={}, handle_value={}, data_decl={}, data_value={}, end_handle={})".format(
            self.__class__.__name__, self.uuid, self.handle_decl, self.handle_value,
            self.data_decl, self.data_value, self.end_handle
        )


class BleGattHandle(object):
    def __init__(self, handle=BLE_GATT_HANDLE_INVALID):
        self.handle = handle


"""
GATTC Classes
"""


class BLEGattcWriteParams(object):
    def __init__(self, write_op, flags, handle, data, offset):
        assert isinstance(write_op, BLEGattWriteOperation), 'Invalid argument type'
        assert isinstance(flags, BLEGattExecWriteFlag), 'Invalid argument type'
        self.write_op = write_op
        self.flags = flags
        self.handle = handle
        self.data = data
        self.offset = offset

    @classmethod
    def from_c(cls, gattc_write_params):
        return cls(write_op=BLEGattWriteOperation(gattc_write_params.write_op),
                   flags=gattc_write_params.flags,
                   handle=gattc_write_params.handle,
                   data=util.uint8_array_to_list(gattc_write_params.p_value,
                                                 gattc_write_params.len))

    def to_c(self):
        self.__data_array = util.list_to_uint8_array(self.data)
        write_params = driver.ble_gattc_write_params_t()
        write_params.p_value = self.__data_array.cast()
        write_params.flags = self.flags.value
        write_params.handle = self.handle
        write_params.offset = self.offset
        write_params.len = len(self.data)
        write_params.write_op = self.write_op.value

        return write_params

    def __repr__(self):
        return repr_format(self, handle=self.handle, write_op=self.write_op, offset=self.offset,
                           flags=self.flags, data=self.data)


class BLEGattcDescriptor(object):
    def __init__(self, uuid, handle, data=None):
        self.handle = handle
        self.uuid = uuid
        self.data = data

    @classmethod
    def from_c(cls, gattc_desc):
        return cls(uuid=BLEUUID.from_c(gattc_desc.uuid),
                   handle=gattc_desc.handle)

    def __repr__(self):
        return repr_format(self, handle=self.handle, uuid=self.uuid)


class BLEGattcAttrInfo16(object):
    def __init__(self, handle, uuid):
        self.handle = handle
        self.uuid = uuid

    @classmethod
    def from_c(cls, attr_info16):
        handle = attr_info16.handle
        uuid = BLEUUID.from_c(attr_info16.uuid)
        return cls(handle, uuid)

    def __repr__(self):
        return "{}(handle={!r}, uuid={})".format(self.__class__.__name__, self.handle, self.uuid)


class BLEGattcAttrInfo128(object):
    def __init__(self, attr_handle, uuid):
        self.handle = attr_handle
        self.uuid = uuid

    @classmethod
    def from_c(cls, attr_info128):
        uuid = BLEUUID.from_uuid128(attr_info128.uuid)
        attr_handle = attr_info128.handle
        return cls(attr_handle, uuid)

    def __repr__(self):
        return "{}(handle={!r}, uuid={})".format(self.__class__.__name__, self.handle, self.uuid)


"""
GATTS Classes
"""
# TODO: BleGattsCharPf


class BleGattsEnableParams(object):
    def __init__(self, service_changed, attribute_table_size):
        assert attribute_table_size % 4 == 0  # attribute table size must be a multiple of 4
        self.service_changed = service_changed
        self.attribute_table_size = attribute_table_size

    def to_c(self):
        params = driver.ble_gatts_enable_params_t()
        params.service_changed = self.service_changed
        params.attr_tab_size = self.attribute_table_size
        return params


class BLEGattsCharHandles(object):
    def __init__(self, value_handle=0, user_desc_handle=0, cccd_handle=0, sccd_handle=0):
        self.value_handle = value_handle
        self.user_desc_handle = user_desc_handle
        self.cccd_handle = cccd_handle
        self.sccd_handle = sccd_handle

    def to_c(self):
        handle_params = driver.ble_gatts_char_handles_t()
        handle_params.value_handle = self.value_handle
        handle_params.user_desc_handle = self.user_desc_handle
        handle_params.cccd_handle = self.cccd_handle
        handle_params.sccd_handle = self.sccd_handle
        return handle_params

    @classmethod
    def from_c(cls, handle_params):
        return cls(handle_params.value_handle,
                   handle_params.user_desc_handle,
                   handle_params.cccd_handle,
                   handle_params.sccd_handle)


class BLEGattsAttribute(object):
    def __init__(self, uuid, attr_metadata, max_len, value=b""):
        self.uuid = uuid
        self.attribute_metadata = attr_metadata
        self.max_len = max_len
        self.value = value
        self.handle = BLE_GATT_HANDLE_INVALID

    def to_c(self):
        self.__data__array = util.list_to_uint8_array(self.value)
        params = driver.ble_gatts_attr_t()
        params.p_uuid = self.uuid.to_c()
        params.p_attr_md = self.attribute_metadata.to_c()
        params.max_len = self.max_len
        # TODO
        if self.value:
            params.init_len = len(self.value)
            params.init_offs = 0
            params.p_value = self.__data__array.cast()
        return params


class BLEGattsPresentationFormat(object):
    def __init__(self, fmt, exponent, unit, namespace, description):
        self.format = fmt
        self.exponent = exponent
        self.unit = unit
        self.namespace = namespace
        self.description = description

    def to_c(self):
        params = driver.ble_gatts_char_pf_t()
        params.format = int(self.format)
        params.exponent = int(self.exponent)
        params.unit = int(self.unit)
        params.name_space = int(self.namespace)
        params.desc = int(self.description)
        return params

    @classmethod
    def from_c(cls, params):
        return cls(params.format, params.exponent, params.unit, params.name_space, params.desc)


class BLEGattsAttrMetadata(object):
    def __init__(self, read_permissions=BLEGapSecModeType.OPEN, write_permissions=BLEGapSecModeType.OPEN,
                 variable_length=False, read_auth=False, write_auth=False):
        self.read_perm = read_permissions
        self.write_perm = write_permissions
        self.vlen = variable_length
        self.read_auth = read_auth
        self.write_auth = write_auth

    def to_c(self):
        params = driver.ble_gatts_attr_md_t()
        params.read_perm = self.read_perm.to_c()
        params.write_perm = self.write_perm.to_c()
        params.vlen = self.vlen
        params.vloc = 1  # STACK
        params.rd_auth = int(self.read_auth)
        params.wr_auth = int(self.write_auth)
        return params

    @classmethod
    def from_c(cls, params):
        read_perm = BLEGapSecMode.from_c(params.read_perm)
        write_perm = BLEGapSecMode.from_c(params.write_perm)
        vlen = params.vlen
        read_auth = bool(params.rd_auth)
        write_auth = bool(params.wr_auth)
        return cls(read_perm, write_perm, vlen, read_auth, write_auth)


class BLEGattsCharMetadata(object):
    def __init__(self, char_props, user_description="", user_description_max_size=0,
                 user_desc_metadata=None, cccd_metadata=None, sccd_metadata=None, presentation_format=None):
        self.char_props = char_props
        self.user_description = user_description
        self.user_description_max_len = user_description_max_size
        self.user_desc_metadata = user_desc_metadata
        self.cccd_metadata = cccd_metadata
        self.sccd_metadata = sccd_metadata
        self.presentation_format = presentation_format
        self.extended_props = BLEGattExtendedCharacteristicProperties()

    def to_c(self):
        params = driver.ble_gatts_char_md_t()
        params.char_props = self.char_props.to_c()
        params.char_ext_props = self.extended_props.to_c()
        if self.cccd_metadata:
            params.p_cccd_md = self.cccd_metadata.to_c()
        if self.sccd_metadata:
            params.p_sccd_md = self.sccd_metadata.to_c()
        if self.presentation_format:
            params.p_char_pf = self.presentation_format.to_c()
        if self.user_desc_metadata:
            params.p_user_desc_md = self.user_desc_metadata.to_c()
            self.__user_desc_array = util.list_to_uint8_array(self.user_description)
            params.p_char_user_desc = self.__user_desc_array.cast()
            params.char_user_desc_size = len(self.user_description)
            params.char_user_desc_max_size = max(self.user_description_max_len, len(self.user_description))

        return params

    @classmethod
    def from_c(cls, params):
        pass


class BLEGattsAuthorizeParams(object):
    def __init__(self, gatt_status, update, offset=0, data=""):
        assert isinstance(gatt_status, BLEGattStatusCode)
        self.gatt_status = gatt_status
        self.update = update
        self.offset = offset
        self.data = data

    def to_c(self):
        params = driver.ble_gatts_authorize_params_t()
        params.gatt_status = self.gatt_status.value
        params.update = int(self.update)
        params.offset = self.offset

        self.__data_array = util.list_to_uint8_array(self.data)
        params.p_data = self.__data_array.cast()
        params.len = len(self.data)

        return params

    def __repr__(self):
        return repr_format(self, gatt_status=self.gatt_status, update=self.update, offset=self.offset)


class BLEGattsRwAuthorizeReplyParams(object):
    def __init__(self, read=None, write=None):
        assert isinstance(read, (BLEGattsAuthorizeParams, NoneType))
        assert isinstance(write, (BLEGattsAuthorizeParams, NoneType))

        if read is None and write is None:
            raise ValueError("read or write must be set")
        if isinstance(read, BLEGattsAuthorizeParams) and isinstance(write, BLEGattsAuthorizeParams):
            raise ValueError("Both read and write cannot be set at the same time")

        self.read = read
        self.write = write

    def to_c(self):
        params = driver.ble_gatts_rw_authorize_reply_params_t()
        if self.read:
            params.type = driver.BLE_GATTS_AUTHORIZE_TYPE_READ
            params.params.read = self.read.to_c()
        else:
            params.type = driver.BLE_GATTS_AUTHORIZE_TYPE_WRITE
            params.params.write = self.write.to_c()
        return params

    def __repr__(self):
        if self.read:
            return repr_format(self, read=self.read)
        else:
            return repr_format(self, write=self.write)


class BLEGattsValue(object):
    def __init__(self, value, offset=0):
        self.value = value
        self.offset = offset

    def to_c(self):
        self.__data_array = util.list_to_uint8_array(self.value)
        params = driver.ble_gatts_value_t()
        params.offset = self.offset
        params.len = len(self.value)
        params.p_value = self.__data_array.cast()
        return params

    @classmethod
    def from_c(cls, params):
        offset = params.offset
        value = bytearray(util.uint8_array_to_list(params.p_value, params.len))
        return cls(value, offset)


class BLEGattsHvx(object):
    def __init__(self, char_handle, hvx_type, data, offset=0):
        assert isinstance(hvx_type, BLEGattHVXType)

        self.handle = char_handle
        self.type = hvx_type
        self.offset = offset
        self.data = data

    def to_c(self):
        params = driver.ble_gatts_hvx_params_t()

        self._len_ptr = driver.new_uint16()
        if self.data:
            self.__data_array = util.list_to_uint8_array(self.data)
            params.p_data = self.__data_array.cast()
            driver.uint16_assign(self._len_ptr, len(self.data))
        else:
            driver.uint16_assign(self._len_ptr, 0)

        params.handle = self.handle
        params.type = self.type.value
        params.offset = self.offset
        params.p_len = self._len_ptr  # TODO: Not sure if this works
        return params

    def __repr__(self):
        return repr_format(self, handle=self.handle, type=self.type, offset=self.offset, data=self.data)