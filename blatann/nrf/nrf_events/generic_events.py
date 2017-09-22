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
