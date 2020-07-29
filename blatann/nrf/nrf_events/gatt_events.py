from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util
from blatann.nrf.nrf_events.generic_events import BLEEvent


"""
Base Event Classes
"""


class GattEvt(BLEEvent):
    pass


class GattcEvt(GattEvt):
    pass


class GattsEvt(GattEvt):
    pass


"""
GATTC Events
"""


class GattcEvtReadResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_READ_RSP

    def __init__(self, conn_handle, status, error_handle, attr_handle, offset, data):
        super(GattcEvtReadResponse, self).__init__(conn_handle)
        self.status = status
        self.error_handle = error_handle
        self.attr_handle = attr_handle
        self.offset = offset
        if status == BLEGattStatusCode.read_not_permitted:
            self.data = None
        elif isinstance(data, str):
            self.data = list(map(ord, data))
        else:
            self.data = data

    @classmethod
    def from_c(cls, event):
        read_rsp = event.evt.gattc_evt.params.read_rsp
        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   error_handle=event.evt.gattc_evt.error_handle,
                   attr_handle=read_rsp.handle,
                   offset=read_rsp.offset,
                   data=util.uint8_array_to_list(read_rsp.data, read_rsp.len))

    def __repr__(self):
        data = None
        if self.data is not None:
            data = ''.join(map(chr, self.data))
        return self._repr_format(status=self.status, error_handle=self.error_handle, attr_handle=self.attr_handle,
                                 offset=self.offset, data=data)


class GattcEvtHvx(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_HVX

    def __init__(self, conn_handle, status, error_handle, attr_handle, hvx_type, data):
        super(GattcEvtHvx, self).__init__(conn_handle)
        self.status = status
        self.error_handle = error_handle
        self.attr_handle = attr_handle
        self.hvx_type = hvx_type
        if isinstance(data, str):
            self.data = list(map(ord, data))
        else:
            self.data = data

    @classmethod
    def from_c(cls, event):
        hvx_evt = event.evt.gattc_evt.params.hvx
        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   error_handle=event.evt.gattc_evt.error_handle,
                   attr_handle=hvx_evt.handle,
                   hvx_type=BLEGattHVXType(hvx_evt.type),
                   data=util.uint8_array_to_list(hvx_evt.data, hvx_evt.len))

    def __repr__(self):
        data = ''.join(map(chr, self.data))
        return self._repr_format(status=self.status, error_handle=self.error_handle,
                                 attr_handle=self.attr_handle,
                                 hvx_type=self.hvx_type, data=data)


class GattcEvtWriteCmdTxComplete(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_WRITE_CMD_TX_COMPLETE

    def __init__(self, conn_handle, count):
        super(GattcEvtWriteCmdTxComplete, self).__init__(conn_handle)
        self.count = count

    @classmethod
    def from_c(cls, event):
        tx_evt = event.evt.gattc_evt.params.write_cmd_tx_complete
        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   count=tx_evt.count)

    def __repr__(self):
        return self._repr_format(count=self.count)


class GattcEvtWriteResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_WRITE_RSP

    def __init__(self, conn_handle, status, error_handle, attr_handle, write_op, offset, data):
        super(GattcEvtWriteResponse, self).__init__(conn_handle)
        self.status = status
        self.error_handle = error_handle
        self.attr_handle = attr_handle
        self.write_op = write_op
        self.offset = offset
        if isinstance(data, str):
            self.data = list(map(ord, data))
        else:
            self.data = data

    @classmethod
    def from_c(cls, event):
        write_rsp_evt = event.evt.gattc_evt.params.write_rsp
        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   error_handle=event.evt.gattc_evt.error_handle,
                   attr_handle=write_rsp_evt.handle,
                   write_op=BLEGattWriteOperation(write_rsp_evt.write_op),
                   offset=write_rsp_evt.offset,
                   data=util.uint8_array_to_list(write_rsp_evt.data, write_rsp_evt.len))

    def __repr__(self):
        data = ''.join(map(chr, self.data))
        return self._repr_format(status=self.status, error_handle=self.error_handle, attr_handle=self.attr_handle,
                                 write_of=self.write_op, offset=self.offset, data=data)


class GattcEvtPrimaryServiceDiscoveryResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_PRIM_SRVC_DISC_RSP

    def __init__(self, conn_handle, status, services):
        super(GattcEvtPrimaryServiceDiscoveryResponse, self).__init__(conn_handle)
        self.status = status
        self.services = services

    @classmethod
    def from_c(cls, event):
        prim_srvc_disc_rsp_evt = event.evt.gattc_evt.params.prim_srvc_disc_rsp

        services = list()
        for s in util.service_array_to_list(prim_srvc_disc_rsp_evt.services, prim_srvc_disc_rsp_evt.count):
            services.append(BLEGattService.from_c(s))

        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   services=services)

    def __repr__(self):
        return self._repr_format(status=self.status, services=self.services)


class GattcEvtCharacteristicDiscoveryResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_CHAR_DISC_RSP

    def __init__(self, conn_handle, status, characteristics):
        super(GattcEvtCharacteristicDiscoveryResponse, self).__init__(conn_handle)
        self.status = status
        self.characteristics = characteristics

    @classmethod
    def from_c(cls, event):
        char_disc_rsp_evt = event.evt.gattc_evt.params.char_disc_rsp

        characteristics = list()
        for ch in util.ble_gattc_char_array_to_list(char_disc_rsp_evt.chars, char_disc_rsp_evt.count):
            characteristics.append(BLEGattCharacteristic.from_c(ch))

        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   characteristics=characteristics)

    def __repr__(self):
        return "{}(conn_handle={!r}, status={!r}, characteristics={!r})".format(self.__class__.__name__,
                                                                                self.conn_handle,
                                                                                self.status, self.characteristics)


class GattcEvtDescriptorDiscoveryResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_DESC_DISC_RSP

    def __init__(self, conn_handle, status, descriptions):
        super(GattcEvtDescriptorDiscoveryResponse, self).__init__(conn_handle)
        self.status = status
        self.descriptions = descriptions

    @classmethod
    def from_c(cls, event):
        desc_disc_rsp_evt = event.evt.gattc_evt.params.desc_disc_rsp

        descriptions = list()
        for d in util.desc_array_to_list(desc_disc_rsp_evt.descs, desc_disc_rsp_evt.count):
            descriptions.append(BLEGattcDescriptor.from_c(d))

        return cls(conn_handle=event.evt.gattc_evt.conn_handle,
                   status=BLEGattStatusCode(event.evt.gattc_evt.gatt_status),
                   descriptions=descriptions)

    def __repr__(self):
        return "{}(conn_handle={!r}, status={!r}, descriptions={!r})".format(self.__class__.__name__, self.conn_handle,
                                                                             self.status, self.descriptions)


class GattcEvtAttrInfoDiscoveryResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_ATTR_INFO_DISC_RSP

    def __init__(self, conn_handle, status, attr_info16=None, attr_info128=None):
        super(GattcEvtAttrInfoDiscoveryResponse, self).__init__(conn_handle)
        self.status = status
        self.attr_info16 = attr_info16
        self.attr_info128 = attr_info128

    @classmethod
    def from_c(cls, event):
        status = event.evt.gattc_evt.gatt_status
        attr_info_rsp = event.evt.gattc_evt.params.attr_info_disc_rsp
        if attr_info_rsp.format == driver.BLE_GATTC_ATTR_INFO_FORMAT_16BIT:
            attr16_array = util.attr_info16_array_to_list(attr_info_rsp.info.attr_info16, attr_info_rsp.count)
            attr16 = [BLEGattcAttrInfo16.from_c(a) for a in attr16_array]
            attr128 = None
        else:
            attr16 = None
            attr128_array = util.attr_info128_array_to_list(attr_info_rsp.info.attr_info128, attr_info_rsp.count)
            attr128 = [BLEGattcAttrInfo128.from_c(a) for a in attr128_array]

        return cls(event.evt.gattc_evt.conn_handle, status, attr16, attr128)

    def __repr__(self):
        return "{}(conn_handle={!r}, status: {!r} uuid_info:{})".format(self.__class__.__name__,
                                                                        self.conn_handle, self.status,
                                                                        self.attr_info16 or self.attr_info128)


class GattcEvtMtuExchangeResponse(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_EXCHANGE_MTU_RSP

    def __init__(self, conn_handle, server_mtu):
        super(GattcEvtMtuExchangeResponse, self).__init__(conn_handle)
        self.server_mtu = server_mtu

    @classmethod
    def from_c(cls, event):
        server_mtu_size = event.evt.gattc_evt.params.exchange_mtu_rsp.server_rx_mtu
        return cls(event.evt.gattc_evt.conn_handle, server_mtu_size)

    def __repr__(self):
        return "{}(conn_handle={!r}, server_mtu={})".format(self.__class__.__name__, self.conn_handle, self.server_mtu)


class GattcEvtTimeout(GattcEvt):
    evt_id = driver.BLE_GATTC_EVT_TIMEOUT

    def __init__(self, conn_handle, source):
        super(GattcEvtTimeout, self).__init__(conn_handle)
        self.source = source

    @classmethod
    def from_c(cls, event):
        source = event.evt.gattc_evt.params.timeout.src
        return cls(event.evt.gattc_evt.conn_handle, source)

    def __repr__(self):
        return self._repr_format(source=self.source)


"""
GATTS Events
"""

# TODO: SC_CONFIRM


class GattsEvtSysAttrMissing(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_SYS_ATTR_MISSING

    def __init__(self, conn_handle, hint):
        super(GattsEvtSysAttrMissing, self).__init__(conn_handle)

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gatts_evt.conn_handle
        sys_attr_event = event.evt.gatts_evt.params.sys_attr_missing
        return cls(conn_handle, sys_attr_event.hint)

    def __repr__(self):
        return self._repr_format()


class GattsEvtWrite(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_WRITE

    def __init__(self, conn_handle, attr_handle, uuid, write_operand, auth_required, offset, data):
        super(GattsEvtWrite, self).__init__(conn_handle)
        self.attribute_handle = attr_handle
        self.uuid = uuid
        self.write_op = write_operand
        self.auth_required = auth_required
        self.offset = offset
        self.data = data

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gatts_evt.conn_handle
        write_event = event.evt.gatts_evt.params.write
        return cls.from_auth_request(conn_handle, write_event)

    @classmethod
    def from_auth_request(cls, conn_handle, write_event):
        attr_handle = write_event.handle
        uuid = BLEUUID.from_c(write_event.uuid)
        write_operand = BLEGattsWriteOperation(write_event.op)
        auth_required = bool(write_event.auth_required)
        offset = write_event.offset
        data = util.uint8_array_to_list(write_event.data, write_event.len)

        return cls(conn_handle, attr_handle, uuid, write_operand, auth_required, offset, data)

    def __repr__(self):
        return self._repr_format(attr_handle=self.attribute_handle, uuid=self.uuid, write_op=self.write_op,
                                 auth_required=self.auth_required, offset=self.offset, data=bytes(self.data))


class GattsEvtRead(GattsEvt):  # Not a _true_ event, but is used for the Read/Write event class
    def __init__(self, conn_handle, attr_handle, uuid, offset):
        super(GattsEvtRead, self).__init__(conn_handle)
        self.attribute_handle = attr_handle
        self.uuid = uuid
        self.offset = offset

    @classmethod
    def from_auth_request(cls, conn_handle, read_event):
        attr_handle = read_event.handle
        uuid = BLEUUID.from_c(read_event.uuid)
        offset = read_event.offset

        return cls(conn_handle, attr_handle, uuid, offset)

    def __repr__(self):
        return "{}(conn_handle={!r}, attr_handle={!r}, uuid={!r}, offset={!r}, )".format(self.__class__.__name__,
                                                                                         self.conn_handle,
                                                                                         self.attribute_handle,
                                                                                         self.uuid, self.offset)


class GattsEvtReadWriteAuthorizeRequest(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_RW_AUTHORIZE_REQUEST

    def __init__(self, conn_handle, read=None, write=None):
        super(GattsEvtReadWriteAuthorizeRequest, self).__init__(conn_handle)
        self.read = read
        self.write = write

    @classmethod
    def from_c(cls, event):
        auth_event = event.evt.gatts_evt.params.authorize_request
        conn_handle = event.evt.gatts_evt.conn_handle
        read = None
        write = None
        if auth_event.type == driver.BLE_GATTS_AUTHORIZE_TYPE_READ:
            read = GattsEvtRead.from_auth_request(conn_handle, auth_event.request.read)
        elif auth_event.type == driver.BLE_GATTS_AUTHORIZE_TYPE_WRITE:
            write = GattsEvtWrite.from_auth_request(conn_handle, auth_event.request.write)
        else:
            raise NordicSemiException("Unknown authorize request type: {}".format(auth_event.type))
        return cls(conn_handle, read, write)

    def __repr__(self):
        if self.read is not None:
            txt = "read"
            data = self.read
        else:
            txt = "write"
            data = self.write

        return "{}(conn_handle={!r}, {}={!r})".format(self.__class__.__name__, self.conn_handle, txt, data)


class GattsEvtHandleValueConfirm(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_HVC

    def __init__(self, conn_handle, attr_handle):
        super(GattsEvtHandleValueConfirm, self).__init__(conn_handle)
        self.attribute_handle = attr_handle

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gatts_evt.conn_handle
        return cls(conn_handle, event.evt.gatts_evt.params.hvc.handle)

    def __repr__(self):
        return "{}(conn_handle={!r}, attr_handle={!r})".format(self.__class__.__name__, self.conn_handle, self.attribute_handle)


class GattsEvtNotificationTxComplete(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_HVN_TX_COMPLETE

    def __init__(self, conn_handle, tx_count):
        super(GattsEvtNotificationTxComplete, self).__init__(conn_handle)
        self.tx_count = tx_count

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gatts_evt.conn_handle
        return cls(conn_handle, event.evt.gatts_evt.params.hvn_tx_complete.count)

    def __repr__(self):
        return self._repr_format(tx_count=self.tx_count)


class GattsEvtExchangeMtuRequest(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_EXCHANGE_MTU_REQUEST

    def __init__(self, conn_handle, client_mtu):
        super(GattsEvtExchangeMtuRequest, self).__init__(conn_handle)
        self.client_mtu = client_mtu

    @classmethod
    def from_c(cls, event):
        conn_handle = event.evt.gatts_evt.conn_handle
        return cls(conn_handle, event.evt.gatts_evt.params.exchange_mtu_request.client_rx_mtu)

    def __repr__(self):
        return "{}(conn_handle={!r}, client_mtu={!r})".format(self.__class__.__name__, self.conn_handle, self.client_mtu)


class GattsEvtTimeout(GattsEvt):
    evt_id = driver.BLE_GATTS_EVT_TIMEOUT

    def __init__(self, conn_handle, source):
        super(GattsEvtTimeout, self).__init__(conn_handle)
        self.source = source

    @classmethod
    def from_c(cls, event):
        source = event.evt.gatts_evt.params.timeout.src
        return cls(event.evt.gatts_evt.conn_handle, source)

    def __repr__(self):
        return self._repr_format(source=self.source)