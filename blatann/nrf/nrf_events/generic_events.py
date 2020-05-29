from enum import IntEnum

from blatann.nrf.nrf_types import *
from blatann.nrf.nrf_dll_load import driver
import blatann.nrf.nrf_driver_types
from blatann.utils import repr_format


class BLEEvent(object):
    evt_id = None

    def __init__(self, conn_handle):
        self.conn_handle = conn_handle

    def __str__(self):
        return self.__repr__()

    def _repr_format(self, **kwargs):
        """
        Helper method to format __repr__ for BLE events
        """
        return repr_format(self, conn_handle=self.conn_handle, **kwargs)


class EvtUserMemoryRequest(BLEEvent):
    evt_id = driver.BLE_EVT_USER_MEM_REQUEST

    def __init__(self, conn_handle, request_type):
        super(EvtUserMemoryRequest, self).__init__(conn_handle)
        self.type = request_type

    @classmethod
    def from_c(cls, event):
        return cls(event.evt.common_evt.conn_handle, event.evt.common_evt.params.user_mem_request.type)

    def __repr__(self):
        return self._repr_format(type=self.type)
