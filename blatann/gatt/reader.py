import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.exceptions import InvalidStateException
from blatann.event_args import EventArgs

logger = logging.getLogger(__name__)


class GattcReadCompleteEventArgs(EventArgs):
    def __init__(self, handle, status, data):
        self.handle = handle
        self.status = status
        self.data = data


class GattcReader(object):
    """
    Class which implements the state machine for completely reading a peripheral's attribute
    """
    _READ_OVERHEAD = 1  # Number of bytes per MTU that are overhead for the read operation

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
        self.peer.driver_event_subscribe(self._on_read_response, nrf_events.GattcEvtReadResponse)

    @property
    def on_read_complete(self):
        """
        Event that is emitted when a read completes on an attribute handle.

        Handler args: (int attribute_handle, gatt.GattStatusCode, bytes data_read)

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_read_complete_event

    def read(self, handle):
        """
        Reads the attribute value from the handle provided. Can only read from a single attribute at a time. If a
        read is in progress, raises an InvalidStateException

        :param handle: the attribute handle to read
        :return: A waitable that will fire when the read finishes.
                 See on_read_complete for the values returned from the waitable
        :rtype: EventWaitable
        """
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
        Handler for GattcEvtReadResponse

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
        event_args = GattcReadCompleteEventArgs(self._handle, status, bytes(self._data))
        self._on_read_complete_event.notify(self, event_args)
