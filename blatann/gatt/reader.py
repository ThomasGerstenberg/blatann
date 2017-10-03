import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.exceptions import InvalidStateException

logger = logging.getLogger(__name__)


class GattcReader(object):
    _READ_OVERHEAD = 1

    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self._on_read_complete_event = EventSource("On Read Complete", logger)
        self._busy = False
        self._data = bytearray()
        self._handle = 0x0000
        self._offset = 0
        self.ble_device.ble_driver.event_subscribe(self._on_read_response, nrf_events.GattcEvtReadResponse)

    @property
    def on_read_complete(self):
        """

        :rtype: Event
        """
        return self._on_read_complete_event

    def read(self, handle):
        if self._busy:
            raise InvalidStateException("Gattc Reader is busy")
        self._handle = handle
        self._offset = 0
        self._data = bytearray()
        logger.debug("Starting read from handle {}".format(handle))
        self._read_next_chunk()
        self._busy = True
        return EventWaitable(self.on_read_complete)

    def _read_next_chunk(self):
        self.ble_device.ble_driver.ble_gattc_read(self.peer.conn_handle, self._handle, self._offset)

    def _on_read_response(self, driver, event):
        """
        :type event: nrf_events.GattcEvtReadResponse
        """
        if event.conn_handle != self.peer.conn_handle or event.attr_handle != self._handle:
            return
        if event.status != nrf_events.BLEGattStatusCode.success:
            self._complete(event.status)
            return

        bytes_read = len(event.data)
        self._data += bytearray(event.data)
        self._offset += bytes_read

        if bytes_read == (self.peer.mtu_size - self._READ_OVERHEAD):
            self._read_next_chunk()
        else:
            self._complete()

    def _complete(self, status=nrf_events.BLEGattStatusCode.success):
        self._busy = False
        self._on_read_complete_event.notify(self._handle, status, self._data)