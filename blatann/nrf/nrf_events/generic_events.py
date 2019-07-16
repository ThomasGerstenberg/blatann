from enum import IntEnum

from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types as util


class BLEEvent(object):
    evt_id = None

    def __init__(self, conn_handle):
        self.conn_handle = conn_handle

    def __str__(self):
        return self.__repr__()


class EvtUserMemoryRequest(BLEEvent):
    evt_id = driver.BLE_EVT_USER_MEM_REQUEST

    def __init__(self, conn_handle, request_type):
        super(EvtUserMemoryRequest, self).__init__(conn_handle)
        self.type = request_type

    @classmethod
    def from_c(cls, event):
        return cls(event.evt.common_evt.conn_handle, event.evt.common_evt.params.user_mem_request.type)

    def __repr__(self):
        return "{}(conn_handle={!r}, type={!r})".format(self.__class__.__name__, self.conn_handle, self.type)


class EvtTxComplete(BLEEvent):
    evt_id = driver.BLE_EVT_TX_COMPLETE

    def __init__(self, conn_handle, count):
        super(EvtTxComplete, self).__init__(conn_handle)
        self.count = count

    @classmethod
    def from_c(cls, event):
        tx_complete_evt = event.evt.common_evt.params.tx_complete
        return cls(conn_handle=event.evt.common_evt.conn_handle,
                   count=tx_complete_evt.count)

    def __repr__(self):
        return "{}(conn_handle={!r}, count={!r})".format(self.__class__.__name__, self.conn_handle, self.count)


class EvtDataLengthChanged(BLEEvent):
    evt_id = driver.BLE_EVT_DATA_LENGTH_CHANGED

    def __init__(self, conn_handle, max_tx_octets, max_tx_time, max_rx_octets, max_rx_time):
        super(EvtDataLengthChanged, self).__init__(conn_handle)
        self.max_tx_octets = max_tx_octets
        self.max_tx_time = max_tx_time
        self.max_rx_octets = max_rx_octets
        self.max_rx_time = max_rx_time

    @classmethod
    def from_c(cls, event):
        evt = event.evt.common_evt.params.data_length_changed
        conn_handle = event.evt.common_evt.conn_handle

        return cls(conn_handle, evt.max_tx_octets, evt.max_tx_time, evt.max_rx_octets, evt.max_rx_time)

    def __repr__(self):
        return "{}(conn_handle={!r}, tx: {} bytes {}us, rx: {} bytes {}us)".format(self.__class__.__name__,
                                                                                   self.conn_handle,
                                                                                   self.max_tx_octets, self.max_tx_time,
                                                                                   self.max_rx_octets, self.max_rx_time)
