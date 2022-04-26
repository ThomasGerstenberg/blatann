from typing import TypeVar, Generic, Callable, Union
from enum import Enum, auto

from blatann.gap.gap_types import ActiveConnectionParameters
from blatann.utils import repr_format

from blatann.nrf.nrf_types import BLEGattStatusCode as GattStatusCode


TDecodedValue = TypeVar("TDecodedValue")


class GattOperationCompleteReason(Enum):
    """
    The reason why a GATT operation completed
    """
    # Operation successful
    SUCCESS = 0
    # Queue of queued operations (notifications,reads, writes) was cleared
    QUEUE_CLEARED = 1
    # The client disconnected before the operation completed
    CLIENT_DISCONNECTED = 2
    # The server disconnected before the operation completed
    SERVER_DISCONNECTED = 3
    # The client unsubscribed from the characteristic before the notification was sent
    CLIENT_UNSUBSCRIBED = 4
    # Unknown Failure
    FAILED = 5
    # The peer failed to respond to the ATT operation
    TIMED_OUT = 6


class EventArgs(object):
    """
    Base Event Arguments class
    """
    def __repr__(self):
        # Get all public attributes
        attrs = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return repr_format(self, **attrs)

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


class MtuSizeUpdatedEventArgs(EventArgs):
    """
    Event arguments for when the effective MTU size on a connection is updated
    """
    def __init__(self, previous_mtu_size: int, current_mtu_size: int):
        self.previous_mtu_size = previous_mtu_size
        self.current_mtu_size = current_mtu_size


class DataLengthUpdatedEventArgs(EventArgs):
    """
    Event arguments for when the Data Length of the link layer has been changed
    """
    def __init__(self, tx_bytes: int, rx_bytes: int, tx_time_us: int, rx_time_us: int):
        self.tx_bytes = tx_bytes
        self.rx_bytes = rx_bytes
        self.tx_time_us = tx_time_us
        self.rx_time_us = rx_time_us


class PhyUpdatedEventArgs(EventArgs):
    """
    Event arguments for when the phy channel is updated
    """
    def __init__(self, status, phy_channel):
        self.status = status
        self.phy_channel = phy_channel


class ConnectionParametersUpdatedEventArgs(EventArgs):
    """
    Event arguments for when connection parameters between peers are updated
    """
    def __init__(self, active_connection_params: ActiveConnectionParameters):
        """
        :param active_connection_params: The newly configured connection parameters
        """
        self.active_connection_params = active_connection_params


# SMP Event Args

class SecurityProcess(Enum):
    ENCRYPTION = 0  # Re-established security using existing long-term keys
    PAIRING = 1     # Created new short-term keys, but no bonding performed
    BONDING = 1     # Created new long-term keys


class PairingCompleteEventArgs(EventArgs):
    """
    Event arguments when pairing completes, whether it failed or was successful
    """
    def __init__(self, status, security_level, security_process):
        """
        :param status: The pairing status
        :type status: blatann.gap.SecurityStatus
        :param security_level: The security level after pairing/bonding
        :type security_level: blatann.gap.smp.SecurityLevel
        :param security_process: The process that was performed
        :type security_process: SecurityProcess
        """
        self.status = status
        self.security_level = security_level
        self.security_process = security_process


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
    def __init__(self, key_type, resolve: Callable[[Union[str, int]], None]):
        """
        :param key_type: The type of key to be entered (passcode, or out-of-band)
        :type key_type: blatann.gap.AuthenticationKeyType
        :param resolve: The function that should be called to resolve the passkey. If the key type is passcode,
        parameter should be a 6-digit string, or None to cancel
        :type resolve: function
        """
        self.key_type = key_type
        self._resolver = resolve

    def resolve(self, passkey: Union[str, int] = None):
        """
        Submits the passkey entered by the user to the peer

        :param passkey: The passkey entered by the user.
                        If the key type is passcode, should be a 6-digit string or integer.
                        Use ``None`` or an empty string to cancel.
        """
        self._resolver(passkey)


class PasskeyDisplayEventArgs(EventArgs):
    """
    Event arguments when a passkey needs to be displayed to the user.
    If match_request is set, the user must confirm that the passkeys match on both devices then send back the confirmation

    """
    def __init__(self, passkey: str, match_request: bool, match_confirm_callback: Callable[[bool], None]):
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


class PeripheralSecurityRequestEventArgs(EventArgs):
    """
    Event arguments for when a peripheral requests security to be enabled on the connection.
    The application must choose how to handle the request: accept, reject,
    or force re-pairing (if device is bonded).
    """
    class Response(Enum):
        accept = 1
        reject = 2
        force_repair = 3

    def __init__(self, bond, mitm, lesc, keypress, is_bonded_device, resolver: Callable[[Response], None]):
        self.bond = bond
        self.mitm = mitm
        self.lesc = lesc
        self.keypress = keypress
        self.is_bonded_device = is_bonded_device
        self._resolver = resolver

    def accept(self):
        """
        Accepts the security request. If device is already bonded will initiate encryption, otherwise
        will start the pairing process
        """
        self._resolver(self.Response.accept)

    def reject(self):
        """
        Rejects the security request
        """
        self._resolver(self.Response.reject)

    def force_repair(self):
        """
        Accepts the security request and initiates the pairing process, even if the device is already bonded
        """
        self._resolver(self.Response.force_repair)


class PairingRejectedReason(Enum):
    """
    Reason why pairing was rejected
    """
    non_bonded_central_request = auto()
    non_bonded_peripheral_request = auto()
    bonded_peripheral_request = auto()
    bonded_device_repairing = auto()
    user_rejected = auto()


class PairingRejectedEventArgs(EventArgs):
    """
    Event arguments for when a pairing request was rejected locally
    """
    def __init__(self, reason: PairingRejectedReason):
        self.reason = reason


# Gatt Server Event Args

class WriteEventArgs(EventArgs):
    """
    Event arguments for when a client has written to a characteristic on the local database
    """
    def __init__(self, value: bytes):
        """
        :param value: The bytes written to the characteristic
        """
        self.value = value


class DecodedWriteEventArgs(EventArgs, Generic[TDecodedValue]):
    """
    Event arguments for when a client has written to a characteristic on the local database
    and the value has been decoded into a data type
    """
    def __init__(self, value: TDecodedValue, raw_value: bytes):
        """
        :param value: The decoded value that was written to the characteristic.
                      This parameter's type depends on the characteristic
        :param raw_value: The raw bytes that were written
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

    def __init__(self, notification_id: int, data: bytes, reason: GattOperationCompleteReason):
        """
        :param notification_id: The ID of the notification that completed. This will match an ID of a sent notification
        :param data: The data that was sent (or not sent, if failed) to the client
        :param reason: The reason the notification completed
        """
        self.id = notification_id
        self.data = data
        self.reason = reason


# Gatt Client Event Args

class ReadCompleteEventArgs(EventArgs):
    """
    Event arguments for when a read has completed of a peripheral's characteristic
    """
    def __init__(self, read_id: int, value: bytes, status: GattStatusCode, reason: GattOperationCompleteReason):
        """
        :param read_id: The ID of the read that completed. This will match an id of an initiated read
        :param value: The value read by the characteristic (bytes)
        :param status: The read status
        :param reason: The reason the read completed
        """
        self.id = read_id
        self.value = value
        self.status = status
        self.reason = reason


class WriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when a write has completed on a peripheral's characteristic
    """
    def __init__(self, write_id: int, value: bytes, status: GattStatusCode, reason: GattOperationCompleteReason):
        """
        :param write_id: the ID of the write that completed. This will match an id of an initiated write
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :param reason: The reason the write completed
        """
        self.id = write_id
        self.value = value
        self.status = status
        self.reason = reason


class SubscriptionWriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when changing the subscription state of a characteristic completes
    """
    def __init__(self, write_id: int, value: bytes, status: GattStatusCode, reason: GattOperationCompleteReason):
        """
        :param write_id: the ID of the write that completed. This will match an id of an initiated write
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :param reason: The reason the write completed
        """
        self.id = write_id
        self.value = value
        self.status = status
        self.reason = reason


class NotificationReceivedEventArgs(EventArgs):
    """
    Event Arguments for when a notification or indication is received from the peripheral
    """
    def __init__(self, value: bytes, is_indication: bool):
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
    def __init__(self, status: GattStatusCode):
        """
        :param status: The discovery status
        """
        self.status = status


class DecodedReadCompleteEventArgs(ReadCompleteEventArgs, Generic[TDecodedValue]):
    """
    Event Arguments for when a read on a peripheral's characteristic completes and the data stream returned
    is decoded. If unable to decode the value, the bytes read are still returned
    """
    def __init__(self, read_id: int, value: bytes, status: GattStatusCode, reason: GattOperationCompleteReason,
                 decoded_stream: TDecodedValue = None):
        """
        :param decoded_stream: The stream which is decoded into an object. This will vary depending on the decoder
        """
        super(DecodedReadCompleteEventArgs, self).__init__(read_id, value, status, reason)
        self.raw_value = value
        self.decode_successful = decoded_stream is not None
        if self.decode_successful:
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
