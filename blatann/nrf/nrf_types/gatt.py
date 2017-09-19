from enum import Enum
import logging
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_types.generic import BLEUUID
from blatann.nrf.nrf_types.smp import *

logger = logging.getLogger(__name__)


class BLEGattWriteOperation(Enum):
    invalid = driver.BLE_GATT_OP_INVALID
    write_req = driver.BLE_GATT_OP_WRITE_REQ
    write_cmd = driver.BLE_GATT_OP_WRITE_CMD
    singed_write_cmd = driver.BLE_GATT_OP_SIGN_WRITE_CMD
    prepare_write_req = driver.BLE_GATT_OP_PREP_WRITE_REQ
    execute_write_req = driver.BLE_GATT_OP_EXEC_WRITE_REQ


class BLEGattHVXType(Enum):
    invalid = driver.BLE_GATT_HVX_INVALID
    notification = driver.BLE_GATT_HVX_NOTIFICATION
    indication = driver.BLE_GATT_HVX_INDICATION


class BLEGattStatusCode(Enum):
    success = driver.BLE_GATT_STATUS_SUCCESS
    unknown = driver.BLE_GATT_STATUS_UNKNOWN
    invalid = driver.BLE_GATT_STATUS_ATTERR_INVALID
    invalid_handle = driver.BLE_GATT_STATUS_ATTERR_INVALID_HANDLE
    read_not_permitted = driver.BLE_GATT_STATUS_ATTERR_READ_NOT_PERMITTED
    write_not_permitted = driver.BLE_GATT_STATUS_ATTERR_WRITE_NOT_PERMITTED
    invalid_pdu = driver.BLE_GATT_STATUS_ATTERR_INVALID_PDU
    insuf_authentication = driver.BLE_GATT_STATUS_ATTERR_INSUF_AUTHENTICATION
    request_not_supported = driver.BLE_GATT_STATUS_ATTERR_REQUEST_NOT_SUPPORTED
    invalid_offset = driver.BLE_GATT_STATUS_ATTERR_INVALID_OFFSET
    insuf_authorization = driver.BLE_GATT_STATUS_ATTERR_INSUF_AUTHORIZATION
    prepare_queue_full = driver.BLE_GATT_STATUS_ATTERR_PREPARE_QUEUE_FULL
    attribute_not_found = driver.BLE_GATT_STATUS_ATTERR_ATTRIBUTE_NOT_FOUND
    attribute_not_long = driver.BLE_GATT_STATUS_ATTERR_ATTRIBUTE_NOT_LONG
    insuf_enc_key_size = driver.BLE_GATT_STATUS_ATTERR_INSUF_ENC_KEY_SIZE
    invalid_att_val_length = driver.BLE_GATT_STATUS_ATTERR_INVALID_ATT_VAL_LENGTH
    unlikely_error = driver.BLE_GATT_STATUS_ATTERR_UNLIKELY_ERROR
    insuf_encryption = driver.BLE_GATT_STATUS_ATTERR_INSUF_ENCRYPTION
    unsupported_group_type = driver.BLE_GATT_STATUS_ATTERR_UNSUPPORTED_GROUP_TYPE
    insuf_resources = driver.BLE_GATT_STATUS_ATTERR_INSUF_RESOURCES
    rfu_range1_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE1_BEGIN
    rfu_range1_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE1_END
    app_begin = driver.BLE_GATT_STATUS_ATTERR_APP_BEGIN
    app_end = driver.BLE_GATT_STATUS_ATTERR_APP_END
    rfu_range2_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE2_BEGIN
    rfu_range2_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE2_END
    rfu_range3_begin = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE3_BEGIN
    rfu_range3_end = driver.BLE_GATT_STATUS_ATTERR_RFU_RANGE3_END
    cps_cccd_config_error = driver.BLE_GATT_STATUS_ATTERR_CPS_CCCD_CONFIG_ERROR
    cps_proc_alr_in_prog = driver.BLE_GATT_STATUS_ATTERR_CPS_PROC_ALR_IN_PROG
    cps_out_of_range = driver.BLE_GATT_STATUS_ATTERR_CPS_OUT_OF_RANGE


class BLEGattExecWriteFlag(Enum):
    prepared_cancel = driver.BLE_GATT_EXEC_WRITE_FLAG_PREPARED_CANCEL
    prepared_write = driver.BLE_GATT_EXEC_WRITE_FLAG_PREPARED_WRITE
    unused = 0x00


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
    def __init__(self, uuid, attr_metadata, max_len, value=""):
        self.uuid = uuid
        self.attribute_metadata = attr_metadata
        self.max_len = max_len
        self.value = [1]

    def to_c(self):
        params = driver.ble_gatts_attr_t()
        params.p_uuid = self.uuid.to_c()
        params.p_attr_md = self.attribute_metadata.to_c()
        params.init_len = len(self.value)
        params.init_offs = 0
        params.max_len = self.max_len
        # TODO
        # if self.value:
        #     params.p_value = util.list_to_uint8_array(self.value)
        return params


class BLEGattsAttrMetadata(object):
    def __init__(self, read_permissions=BLEGapSecModeType.OPEN, write_permissions=BLEGapSecModeType.OPEN,
                 variable_length=False):
        self.read_perm = read_permissions
        self.write_perm = write_permissions
        self.vlen = variable_length

    def to_c(self):
        params = driver.ble_gatts_attr_md_t()
        params.read_perm = self.read_perm.to_c()
        params.write_perm = self.write_perm.to_c()
        params.vlen = self.vlen
        params.vloc = 1  # STACK
        params.rd_auth = 1
        params.wr_auth = 1
        return params

    @classmethod
    def from_c(cls, params):
        read_perm = BLEGapSecMode.from_c(params.read_perm)
        write_perm = BLEGapSecMode.from_c(params.write_perm)
        vlen = params.vlen
        return cls(read_perm, write_perm, vlen)


class BLEGattsCharMetadata(object):
    def __init__(self, char_props, user_description="", user_description_max_size=0,
                 user_desc_metadata=None, cccd_metadata=None, sccd_metadata=None):
        self.char_props = char_props
        self.user_description = user_description
        self.user_description_max_len = user_description_max_size
        self.user_desc_metadata = user_desc_metadata
        self.cccd_metadata = cccd_metadata
        self.sccd_metadata = sccd_metadata

    def to_c(self):
        params = driver.ble_gatts_char_md_t()
        params.char_props = self.char_props.to_c()
        # if self.user_description:
        #     params.p_char_user_desc = util.list_to_char_array(self.user_description)
        #     params.char_user_desc_size = len(self.user_description)
        # else:
        #     params.char_user_desc_size = 0
        # params.char_user_desc_max_size = self.user_description_max_len
        # if self.user_desc_metadata:
        #     params.p_user_desc_md = self.user_desc_metadata.to_c()
        # if self.cccd_metadata:
        #     params.p_cccd_md = self.cccd_metadata.to_c()
        # if self.sccd_metadata:
        #     params.p_sccd_md = self.sccd_metadata.to_c()
        return params

    @classmethod
    def from_c(cls, params):
        pass


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


class BLEDescriptor(object):
    def __init__(self, uuid, handle, data=None):
        self.handle = handle
        self.uuid = uuid
        self.data = data

    @classmethod
    def from_c(cls, gattc_desc):
        return cls(uuid=BLEUUID.from_c(gattc_desc.uuid),
                   handle=gattc_desc.handle)


class BLECharacteristicProperties(object):
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


class BLECharacteristic(object):
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

    @classmethod
    def from_c(cls, gattc_char):
        return cls(uuid=BLEUUID.from_c(gattc_char.uuid),
                   handle_decl=gattc_char.handle_decl,
                   handle_value=gattc_char.handle_value,
                   char_props=BLECharacteristicProperties.from_c(gattc_char.char_props))


class BLEService(object):
    srvc_uuid = BLEUUID(BLEUUID.Standard.service_primary)

    def __init__(self, uuid, start_handle, end_handle):
        self.uuid = uuid
        self.start_handle = start_handle
        self.end_handle = end_handle
        self.chars = list()

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


class BleGattHandle(object):
    def __init__(self, handle=-1):
        self.handle = handle