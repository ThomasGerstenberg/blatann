import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.exceptions import InvalidStateException

logger = logging.getLogger(__name__)


class GattcWriter(object):
    _WRITE_OVERHEAD = 3
    _LONG_WRITE_OVERHEAD = 5

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
        self.ble_device.ble_driver.event_subscribe(self._on_write_response, nrf_events.GattcEvtWriteResponse)
        self._len_bytes_written = 0

    @property
    def on_write_complete(self):
        """
        :rtype: Event
        """
        return self._on_write_complete

    def write(self, handle, data):
        if self._busy:
            raise InvalidStateException("Gattc Writer is busy")
        if len(data) == 0:
            raise ValueError("Data must be at least one byte")
        self._offset = 0
        self._handle = handle
        self._data = data
        logger.info("Starting write to handle {}, len: {}".format(self._handle, len(self._data)))
        self._write_next_chunk()
        self._busy = True
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
        logger.info("Writing chunk: handle: {}, offset: {}, len: {}, op: {}".format(self._handle, self._offset,
                                                                                    len(data_to_write), write_operation))
        self.ble_device.ble_driver.ble_gattc_write(self.peer.conn_handle, write_params)

    def _on_write_response(self, driver, event):
        """
        :type event: nrf_events.GattcEvtWriteResponse
        """
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
        self._on_write_complete.notify(self._handle, status, self._data)
