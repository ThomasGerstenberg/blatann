import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.exceptions import InvalidStateException
from blatann.event_args import EventArgs

logger = logging.getLogger(__name__)


class GattcWriteCompleteEventArgs(EventArgs):
    def __init__(self, handle, status, data):
        self.handle = handle
        self.status = status
        self.data = data


class GattcWriter(object):
    """
    Class which implements the state machine for writing a value to a peripheral's attribute
    """
    _WRITE_OVERHEAD = 3       # Number of bytes per MTU that are overhead for the write operation
    _LONG_WRITE_OVERHEAD = 5  # Number of bytes per MTU that are overhead for the long write operations

    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self._on_write_complete = EventSource("On Write Complete", logger)
        self._busy = False
        self._data = ""
        self._handle = 0x0000
        self._offset = 0
        self.peer.driver_event_subscribe(self._on_write_response, nrf_events.GattcEvtWriteResponse)
        self._len_bytes_written = 0

    @property
    def on_write_complete(self):
        """
        Event that is emitted when a write completes on an attribute handler

        Handler args: (int attribute_handle, gatt.GattStatusCode, bytearray data_written)

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_write_complete

    def write(self, handle, data):
        """
        Writes data to the attribute at the handle provided. Can only write to a single attribute at a time.
        If a write is in progress, raises an InvalidStateException

        :param handle: The attribute handle to write
        :param data: The data to write
        :return: A Waitable that will fire when the write finishes. see on_write_complete for the values returned from the waitable
        :rtype: EventWaitable
        """
        if self._busy:
            raise InvalidStateException("Gattc Writer is busy")
        if len(data) == 0:
            raise ValueError("Data must be at least one byte")

        self._offset = 0
        self._handle = handle
        self._data = data
        logger.debug("Starting write to handle {}, len: {}".format(self._handle, len(self._data)))
        try:
            self._busy = True
            self._write_next_chunk()
        except Exception:
            self._busy = False
            raise
        return EventWaitable(self.on_write_complete)

    def _write_next_chunk(self):
        flags = nrf_types.BLEGattExecWriteFlag.unused
        if self._offset != 0 or len(self._data) > (self.peer.mtu_size - self._WRITE_OVERHEAD):
            write_operation = nrf_types.BLEGattWriteOperation.prepare_write_req
            self._len_bytes_written = self.peer.mtu_size - self._LONG_WRITE_OVERHEAD
            self._len_bytes_written = min(self._len_bytes_written, len(self._data)-self._offset)
            if self._len_bytes_written <= 0:
                write_operation = nrf_types.BLEGattWriteOperation.execute_write_req
                flags = nrf_types.BLEGattExecWriteFlag.prepared_write
        else:
            # Can write it all in a single
            write_operation = nrf_types.BLEGattWriteOperation.write_req
            self._len_bytes_written = len(self._data)

        data_to_write = self._data[self._offset:self._offset+self._len_bytes_written]
        write_params = nrf_types.BLEGattcWriteParams(write_operation, flags,
                                                     self._handle, data_to_write, self._offset)
        logger.debug("Writing chunk: handle: {}, offset: {}, len: {}, op: {}".format(self._handle, self._offset,
                                                                                     len(data_to_write), write_operation))
        self.ble_device.ble_driver.ble_gattc_write(self.peer.conn_handle, write_params)

    def _on_write_response(self, driver, event: nrf_events.GattcEvtWriteResponse):
        if event.conn_handle != self.peer.conn_handle:
            return
        if event.attr_handle != self._handle and event.write_op != nrf_types.BLEGattWriteOperation.execute_write_req:
            return
        if event.status != nrf_events.BLEGattStatusCode.success:
            self._complete(event.status)
            return

        # Write successful, update offset and check operation
        self._offset += self._len_bytes_written

        if event.write_op in [nrf_types.BLEGattWriteOperation.write_req, nrf_types.BLEGattWriteOperation.execute_write_req]:
            # Completed successfully
            self._complete()
        elif event.write_op == nrf_types.BLEGattWriteOperation.prepare_write_req:
            # Write next chunk (or execute if complete)
            self._write_next_chunk()
        else:
            logger.error("Got unknown write operation: {}".format(event))
            self._complete(nrf_types.BLEGattStatusCode.unknown)

    def _complete(self, status=nrf_events.BLEGattStatusCode.success):
        self._busy = False
        self._on_write_complete.notify(self, GattcWriteCompleteEventArgs(self._handle, status, self._data))
