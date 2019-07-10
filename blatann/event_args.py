from enum import Enum
from blatann.nrf.nrf_types import BLEGattStatusCode as GattStatusCode


class GattOperationCompleteReason(Enum):
    """
    The reason why a GATT operation completed
    """
    # Operation successful
    SUCCESS = 0
    # Queue of queued operations (notifications,reads, writes) was leared
    QUEUE_CLEARED = 1
    # The client disconnected before the operation completed
    CLIENT_DISCONNECTED = 2
    # The server disconnected before the operation completed
    SERVER_DISCONNECTED = 3
    # The client unsubscribed from the characteristic before the notification was sent
    CLIENT_UNSUBSCRIBED = 4
    # Unknown Failure
    FAILED = 4


class EventArgs(object):
    """
    Base Event Arguments class
    """
    pass

# Gap Event Args


class DisconnectionEventArgs(EventArgs):
    """
    Event arguments sent when a peer disconnects
    """
    def __init__(self, reason):
        """
        :param reason: The disconnection reason
        :type reason: blatann.gap.HciStatus
        """
        self.reason = reason


# SMP Event Args

class PairingCompleteEventArgs(EventArgs):
    """
    Event arguments when pairing completes, whether it failed or was successful
    """
    def __init__(self, status, security_level):
        """
        :param status: The pairing status
        :type status: blatann.gap.SecurityStatus
        :param security_level: The security level after pairing/bonding
        :type security_level: blatann.gap.smp.SecurityLevel
        """
        self.status = status
        self.security_level = security_level


class SecurityLevelChangedEventArgs(EventArgs):
    def __init__(self, security_level):
        """
        :param security_level: The new security level
        :type security_level: blatann.gap.smp.SecurityLevel
        """
        self.security_level = security_level


class PasskeyEntryEventArgs(EventArgs):
    """
    Event arguments when a passkey needs to be entered by the user
    """
    def __init__(self, key_type, resolve):
        """
        :param key_type: The type of key to be entered (passcode, or out-of-band)
        :type key_type: blatann.gap.AuthenticationKeyType
        :param resolve: The function that should be called to resolve the passkey. If the key type is passcode,
        parameter should be a 6-digit string, or None to cancel
        :type resolve: function
        """
        self.key_type = key_type
        self.resolve = resolve


class PasskeyDisplayEventArgs(EventArgs):
    """
    Event arguments when a passkey needs to be displayed to the user.
    If match_request is set, the user must confirm that the passkeys match on both devices then send back the confirmation

    """
    def __init__(self, passkey, match_request, match_confirm_callback):
        """
        :param passkey: The passkey to display to the user
        :type passkey: str
        :param match_request: Flag indicating whether or not the user needs to confirm that the passkeys match on both devices
        """
        self.passkey = passkey
        self.match_request = match_request
        self._match_confirm_callback = match_confirm_callback

    def match_confirm(self, keys_match):
        """
        If key matching was requested, this function responds with whether or not the keys matched correctly
        :param keys_match: True if the keys matched, False if not
        """
        if self.match_request:
            self._match_confirm_callback(keys_match)


# Gatt Server Event Args

class WriteEventArgs(EventArgs):
    """
    Event arguments for when a client has written to a characteristic on the local database
    """
    def __init__(self, value):
        """
        :param value: The bytes written to the characteristic
        """
        self.value = value


class DecodedWriteEventArgs(EventArgs):
    """
    Event arguments for when a client has written to a characteristic on the local database
    and the value has been decoded into a data type
    """
    def __init__(self, value, raw_value):
        """
        :param value: The decoded value that was written to the characteristic.
                      This parameter's type depends on the characteristic
        :param raw_value: The raw bytes that were written
        :type raw_value: bytes
        """
        self.value = value
        self.raw_value = raw_value


class SubscriptionStateChangeEventArgs(EventArgs):
    """
    Event arguments for when a client's subscription state has changed
    """
    def __init__(self, subscription_state):
        """
        :type subscription_state: blatann.gatt.SubscriptionState
        """
        self.subscription_state = subscription_state


class NotificationCompleteEventArgs(EventArgs):
    """
    Event arguments for when a notification has been sent to the client from the notification queue
    """
    Reason = GattOperationCompleteReason

    def __init__(self, notification_id, data, reason):
        """
        :param notification_id: The ID of the notification that completed. This will match an ID of a sent notification
        :param data: The data that was sent (or not sent, if failed) to the client
        :param reason: The reason the notification completed
        :type reason: GattOperationCompleteReason
        """
        self.id = notification_id
        self.data = data
        self.reason = reason


# Gatt Client Event Args

class ReadCompleteEventArgs(EventArgs):
    """
    Event arguments for when a read has completed of a peripheral's characteristic
    """
    def __init__(self, read_id, value, status, reason):
        """
        :param read_id: The ID of the read that completed. This will match an id of an initiated read
        :param value: The value read by the characteristic (bytes)
        :param status: The read status
        :type status: blatann.gatt.GattStatusCode
        :param reason: The reason the read completed
        :type reason: GattOperationCompleteReason
        """
        self.id = read_id
        self.value = value
        self.status = status
        self.reason = reason


class WriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when a write has completed on a peripheral's characteristic
    """
    def __init__(self, write_id, value, status, reason):
        """
        :param write_id: the ID of the write that completed. This will match an id of an initiated write
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :type status: blatann.gatt.GattStatusCode
        :param reason: The reason the write completed
        :type reason: GattOperationCompleteReason
        """
        self.id = write_id
        self.value = value
        self.status = status
        self.reason = reason


class SubscriptionWriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when changing the subscription state of a characteristic completes
    """
    def __init__(self, write_id, value, status, reason):
        """
        :param write_id: the ID of the write that completed. This will match an id of an initiated write
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :type status: blatann.gatt.GattStatusCode
        :param reason: The reason the write completed
        :type reason: GattOperationCompleteReason
        """
        self.id = write_id
        self.value = value
        self.status = status
        self.reason = reason


class NotificationReceivedEventArgs(EventArgs):
    """
    Event Arguments for when a notification or indication is received from the peripheral
    """
    def __init__(self, value, is_indication):
        """
        :param value: The data sent in the notification.
                      NOTE: This may not contain the whole characteristic data if more than 1 MTU is required.
                      In that case, a separate read will need to be issued on the characteristic
        :param is_indication: Flag indicating if the event was from an indication or notification
        """
        self.value = value
        self.is_indication = is_indication


class DatabaseDiscoveryCompleteEventArgs(EventArgs):
    """
    Event Arguments for when database discovery completes
    """
    def __init__(self, status):
        """
        :param status: The discovery status
        :type status: blatann.gatt.GattStatusCode
        """
        self.status = status


class DecodedReadCompleteEventArgs(ReadCompleteEventArgs):
    """
    Event Arguments for when a read on a peripheral's characteristic completes and the data stream returned
    is decoded. If unable to decode the value, the bytes read are still returned
    """
    def __init__(self, read_id, value, status, reason, decoded_stream=None):
        """
        :param read_complete_event_args: The read complete event args that this wraps
        :type read_complete_event_args: ReadCompleteEventArgs
        :param decoded_stream: The stream which is decoded into an object. This will vary depending on the decoder
        """
        super(DecodedReadCompleteEventArgs, self).__init__(read_id, value, status, reason)
        self.raw_value = value
        if decoded_stream:
            self.value = decoded_stream

    @staticmethod
    def from_notification_complete_event_args(noti_complete_event_args, decoded_stream=None):
        return DecodedReadCompleteEventArgs(0, noti_complete_event_args.value, GattStatusCode.success,
                                            GattOperationCompleteReason.SUCCESS, decoded_stream)

    @staticmethod
    def from_read_complete_event_args(read_complete_event_args, decoded_stream=None):
        return DecodedReadCompleteEventArgs(read_complete_event_args.id, read_complete_event_args.value,
                                            read_complete_event_args.status, read_complete_event_args.reason,
                                            decoded_stream)


class MtuSizeUpdatedEventArgs(EventArgs):
    """
    Event arguments for when the effective MTU size on a connection is updated
    """
    def __init__(self, previous_mtu_size, current_mtu_size):
        self.previous_mtu_size = previous_mtu_size
        self.current_mtu_size = current_mtu_size
