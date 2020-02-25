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

    def _repr_format(self, *args, **kwargs):
        kwargs["conn_handle"] = self.conn_handle
        items = list(args) + ["{}={}".format(k, v) for k, v in kwargs.items()]
        inner = ", ".join(items)
        return "{}({})".format(self.__class__.__name__, inner)


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
