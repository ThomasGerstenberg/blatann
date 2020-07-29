import binascii

from blatann.event_args import (ReadCompleteEventArgs, DecodedReadCompleteEventArgs,
                                WriteEventArgs, DecodedWriteEventArgs,
                                NotificationReceivedEventArgs)
from blatann.services import ble_data_types
from blatann.gatt import GattStatusCode


class DecodedReadWriteEventDispatcher(object):
    def __init__(self, owner, ble_type, event_to_raise, logger=None):
        self.owner = owner
        self.ble_type = ble_type
        self.event_to_raise = event_to_raise
        self.logger = logger

    def decode(self, data):
        try:
            stream = ble_data_types.BleDataStream(data)
            return self.ble_type.decode(stream)
        except Exception as e:
            if self.logger:
                self.logger.error("Failed to decode into {} type, stream: [{}]".format(self.ble_type.__name__,
                                                                                       binascii.hexlify(data)))
                self.logger.exception(e)
        return None

    def __call__(self, characteristic, event_args):

        if isinstance(event_args, ReadCompleteEventArgs):
            if event_args.status == GattStatusCode.success:
                decoded_value = self.decode(event_args.value)
            else:
                decoded_value = None
            decoded_event_args = DecodedReadCompleteEventArgs.from_read_complete_event_args(event_args, decoded_value)

        elif isinstance(event_args, NotificationReceivedEventArgs):
            decoded_value = self.decode(event_args.value)
            decoded_event_args = DecodedReadCompleteEventArgs.from_notification_complete_event_args(event_args, decoded_value)
        elif isinstance(event_args, WriteEventArgs):
            decoded_value = self.decode(event_args.value)
            decoded_event_args = DecodedWriteEventArgs(decoded_value, event_args.value)
        else:
            if self.logger:
                self.logger.error("Unable to handle unknown event args {}".format(event_args))
            return

        self.event_to_raise.notify(self.owner, decoded_event_args)