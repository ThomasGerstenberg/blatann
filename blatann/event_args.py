from enum import Enum


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
    def __init__(self, status):
        """
        :param status: The pairing status
        :type status: blatann.gap.SecurityStatus
        """
        self.status = status


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
    Event arguments when a passkey needs to be displayed to the user
    """
    def __init__(self, passkey, match_request):
        """
        :param passkey: The passkey to display to the user
        :type passkey: str
        :param match_request: TODO
        """
        self.passkey = passkey
        self.match_request = match_request


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
    class Reason(Enum):
        """
        The reason why the notification completed
        """
        # Sent Successfully
        SUCCESS = 0
        # Queue was requested to be cleared
        QUEUE_CLEARED = 1
        # The client disconnected before notification sent
        CLIENT_DISCONNECTED = 2
        # The client unsubscribed from the characteristic
        CLIENT_UNSUBSCRIBED = 3
        # Unknown Failure
        FAILED = 4

    def __init__(self, notification_id, data, reason):
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
    def __init__(self, value, status):
        """
        :param value: The value read by the characteristic (bytes)
        :param status: The read status
        :type status: blatann.gatt.GattStatusCode
        """
        self.value = value
        self.status = status


class WriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when a write has completed on a peripheral's characteristic
    """
    def __init__(self, value, status):
        """
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :type status: blatann.gatt.GattStatusCode
        """
        self.value = value
        self.status = status


class SubscriptionWriteCompleteEventArgs(EventArgs):
    """
    Event arguments for when changing the subscription state of a characteristic completes
    """
    def __init__(self, value, status):
        """
        :param value: The value that was written to the characteristic (bytes)
        :param status: The write status
        :type status: blatann.gatt.GattStatusCode
        """
        self.value = value
        self.status = status


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
    def __init__(self, status, raw_value, decoded_stream=None):
        """
        :param status: The status of the read
        :type status: blatann.gatt.GattStatusCode
        :param raw_value: The raw value/bytestream of the characteristic
        :param decoded_stream: The stream which is decoded into an object. This will vary depending on the decoder
        """
        super(DecodedReadCompleteEventArgs, self).__init__(raw_value, status)
        self.raw_value = raw_value
        if decoded_stream:
            self.value = decoded_stream

