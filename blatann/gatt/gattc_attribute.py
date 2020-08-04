from __future__ import annotations

import logging

from blatann.gatt import Attribute
from blatann.gatt.managers import GattcOperationManager
from blatann.nrf import nrf_types
from blatann.waitables.event_waitable import EventWaitable, IdBasedEventWaitable
from blatann.event_args import ReadCompleteEventArgs, WriteCompleteEventArgs
from blatann.event_type import EventSource, Event
from blatann.uuid import Uuid


logger = logging.getLogger(__name__)


class GattcAttribute(Attribute):
    """
    Represents a client-side interface to a single attribute which lives inside a Characteristic
    """
    def __init__(self, uuid: Uuid, handle: int, read_write_manager: GattcOperationManager,
                 initial_value=b"", string_encoding="utf8"):
        super(GattcAttribute, self).__init__(uuid, handle, initial_value, string_encoding)
        self._manager = read_write_manager

        self._on_read_complete_event = EventSource(f"[{handle}/{uuid}] On Read Complete", logger)
        self._on_write_complete_event = EventSource(f"[{handle}/{uuid}] On Write Complete", logger)

    """
    Events
    """

    @property
    def on_read_complete(self) -> Event[GattcAttribute, ReadCompleteEventArgs]:
        """
        Event that is triggered when a read from the attribute is completed
        """
        return self._on_read_complete_event

    @property
    def on_write_complete(self) -> Event[GattcAttribute, WriteCompleteEventArgs]:
        """
        Event that is triggered when a write to the attribute is completed
        """
        return self._on_write_complete_event

    """
    Public Methods
    """

    def read(self) -> IdBasedEventWaitable[GattcAttribute, ReadCompleteEventArgs]:
        """
        Performs a read of the attribute and returns a Waitable that executes when the read finishes
        with the data read.

        :return: A waitable that will trigger when the read finishes
        """
        read_id = self._manager.read(self._handle, self._read_complete)
        return IdBasedEventWaitable(self._on_read_complete_event, read_id)

    def write(self, data, with_response=True) -> IdBasedEventWaitable[GattcAttribute, WriteCompleteEventArgs]:
        """
        Initiates a write of the data provided to the attribute and returns a Waitable that executes
        when the write completes and the confirmation response is received from the other device.

        :param data: The data to write. Can be a string, bytes, or anything that can be converted to bytes
        :type data: str or bytes or bytearray
        :param with_response: Used internally for characteristics that support write without responses.
                              Should always be true for any other case (descriptors, etc.).
        :return: A waitable that returns when the write finishes
        """
        if isinstance(data, str):
            data = data.encode(self._string_encoding)
        write_id = self._manager.write(self._handle, bytes(data), self._write_complete, with_response)
        return IdBasedEventWaitable(self._on_write_complete_event, write_id)

    def update(self, value):
        """
        Used internally to update the value after data is received from another means, i.e. Indication/notification.
        Should not be called by the user.
        """
        self._value = bytes(value)

    def _read_complete(self, sender, event_args):
        if event_args.handle == self._handle:
            if event_args.status == nrf_types.BLEGattStatusCode.success:
                self._value = event_args.data
            args = ReadCompleteEventArgs(event_args.id, self._value, event_args.status, event_args.reason)
            self._on_read_complete_event.notify(self, args)

    def _write_complete(self, sender, event_args):
        # Success, update the local value
        if event_args.handle == self._handle:
            if event_args.status == nrf_types.BLEGattStatusCode.success:
                self._value = event_args.data
            args = WriteCompleteEventArgs(event_args.id, self._value, event_args.status, event_args.reason)
            self._on_write_complete_event.notify(self, args)
