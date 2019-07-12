import logging
import threading
import enum

from blatann.event_type import EventSource
from blatann.gap import smp
from blatann.gatt import gattc, service_discovery, MTU_SIZE_DEFAULT, MTU_SIZE_MINIMUM
from blatann.nrf import nrf_events
from blatann.nrf.nrf_types.enums import BLE_CONN_HANDLE_INVALID
from blatann.waitables import connection_waitable, event_waitable
from blatann.event_args import *

logger = logging.getLogger(__name__)


class PeerState(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class PeerAddress(nrf_events.BLEGapAddr):
    pass


class ConnectionParameters(nrf_events.BLEGapConnParams):
    def __init__(self, min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency=0):
        # TODO: Parameter validation
        super(ConnectionParameters, self).__init__(min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency)


DEFAULT_CONNECTION_PARAMS = ConnectionParameters(15, 30, 4000, 0)
DEFAULT_SECURITY_PARAMS = smp.SecurityParameters(reject_pairing_requests=True)


class Peer(object):
    """
    Object that represents a BLE-connected (or disconnected) peer
    """
    BLE_CONN_HANDLE_INVALID = BLE_CONN_HANDLE_INVALID

    """ Number of bytes that are header/overhead per MTU when sending a notification or indication """
    NOTIFICATION_INDICATION_OVERHEAD_BYTES = 3

    def __init__(self, ble_device, role, connection_params=DEFAULT_CONNECTION_PARAMS,
                 security_params=DEFAULT_SECURITY_PARAMS):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self._ble_device = ble_device
        self._role = role
        self._ideal_connection_params = connection_params
        self._current_connection_params = DEFAULT_CONNECTION_PARAMS
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.peer_address = "",
        self.connection_state = PeerState.DISCONNECTED
        self._on_connect = EventSource("On Connect", logger)
        self._on_disconnect = EventSource("On Disconnect", logger)
        self._on_mtu_exchange_complete = EventSource("On MTU Exchange Complete", logger)
        self._on_mtu_size_updated = EventSource("On MTU Size Updated", logger)
        self._mtu_size = MTU_SIZE_DEFAULT
        self._preferred_mtu_size = MTU_SIZE_DEFAULT
        self._negotiated_mtu_size = None

        self._connection_based_driver_event_handlers = {}
        self._connection_handler_lock = threading.Lock()
        self.security = smp.SecurityManager(self._ble_device, self, security_params)

    """
    Properties
    """

    @property
    def connected(self):
        """
        Gets if this peer is currently connected

        :return: True if connected, False if not
        """
        return self.connection_state == PeerState.CONNECTED

    @property
    def bytes_per_notification(self):
        """
        Gets the maximum number of bytes that can be sent in a single notification/indication

        :return: Number of bytes that can be sent in a notification/indication
        """
        return self._mtu_size - self.NOTIFICATION_INDICATION_OVERHEAD_BYTES

    @property
    def is_peripheral(self):
        """
        Gets if this peer is a Peripheral (the local device acting as a central/client)
        """
        return isinstance(self, Peripheral)

    @property
    def is_client(self):
        """
        Gets if this peer is a Client (the local device acting as a peripheral/server)
        """
        return isinstance(self, Client)

    @property
    def is_previously_bonded(self):
        """
        Gets if the peer this security manager is for was bonded in a previous connection
        """
        return self.security.is_previously_bonded

    @property
    def mtu_size(self):
        """
        Gets the current negotiated size of the MTU for the peer

        :return: The current MTU size
        """
        return self._mtu_size

    @property
    def max_mtu_size(self):
        """
        The maximum allowed MTU size. This is set when initially configuring the BLE Device
        """
        return self._ble_device.max_mtu_size

    @property
    def preferred_mtu_size(self):
        """
        Gets the user-set preferred MTU size. Defaults to the Default MTU size (23)
        """
        return self._preferred_mtu_size

    @preferred_mtu_size.setter
    def preferred_mtu_size(self, mtu_size):
        """
        Sets the preferred MTU size to use when a MTU Exchange Request is received
        """
        self._validate_mtu_size(mtu_size)
        self._preferred_mtu_size = mtu_size

    """
    Events
    """

    @property
    def on_connect(self):
        """
        Event generated when the peer connects to the local device

        Event Args: None

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_connect

    @property
    def on_disconnect(self):
        """
        Event generated when the peer disconnects from the local device

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_disconnect

    @property
    def on_mtu_exchange_complete(self):
        """
        Event generated when an MTU exchange completes with the peer

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_mtu_exchange_complete

    @property
    def on_mtu_size_updated(self):
        """
        Event generated when the effective MTU size has been updated on the connection.

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: blatann.event_type.Event
        """
        return self._on_mtu_size_updated

    """
    Public Methods
    """

    def disconnect(self, status_code=nrf_events.BLEHci.remote_user_terminated_connection):
        """
        Disconnects from the peer, giving the optional status code.
        Returns a waitable that will fire when the disconnection is complete

        :param status_code: The HCI Status code to send back to the peer
        :return: A waitable that will fire when the peer is disconnected
        :rtype: connection_waitable.DisconnectionWaitable
        """
        if self.connection_state != PeerState.CONNECTED:
            return
        self._ble_device.ble_driver.ble_gap_disconnect(self.conn_handle, status_code)
        return self._disconnect_waitable

    def set_connection_parameters(self, min_connection_interval_ms, max_connection_interval_ms, connection_timeout_ms,
                                  slave_latency=0):
        """
        Sets the connection parameters for the peer and starts the connection parameter update process

        :param min_connection_interval_ms: The minimum acceptable connection interval, in milliseconds
        :param max_connection_interval_ms: The maximum acceptable connection interval, in milliseconds
        :param connection_timeout_ms: The connection timeout, in milliseconds
        :param slave_latency: The slave latency allowed
        """
        self._ideal_connection_params = ConnectionParameters(min_connection_interval_ms, max_connection_interval_ms,
                                                             connection_timeout_ms, slave_latency)
        if not self.connected:
            return
        # Do stuff to set the connection parameters
        self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._ideal_connection_params)

    def exchange_mtu(self, mtu_size=None):
        """
        Initiates the MTU Exchange sequence with the peer device.

        If the MTU size is not provided the preferred_mtu_size value will be used.
        If an MTU size is provided the preferred_mtu_size will be updated to this

        :param mtu_size: Optional MTU size to use. If provided, it will also updated the preferred MTU size
        :return: A waitable that will fire when the MTU exchange completes
        :rtype: event_waitable.EventWaitable
        """
        # If the MTU size has already been negotiated we need to use the same value
        # as the previous exchange (Vol 3, Part F 3.4.2.2)
        if self._negotiated_mtu_size is None:
            if mtu_size is not None:
                self._validate_mtu_size(mtu_size)
                self._negotiated_mtu_size = mtu_size
            else:
                self._negotiated_mtu_size = self.preferred_mtu_size

        self._ble_device.ble_driver.ble_gattc_exchange_mtu_req(self.conn_handle, self._negotiated_mtu_size)
        return event_waitable.EventWaitable(self._on_mtu_exchange_complete)

    """
    Internal Library Methods
    """

    def peer_connected(self, conn_handle, peer_address, connection_params):
        """
        Internal method called when the peer connects to set up the object
        """
        self.conn_handle = conn_handle
        self.peer_address = peer_address
        self._mtu_size = MTU_SIZE_DEFAULT
        self._negotiated_mtu_size = None
        self._disconnect_waitable = connection_waitable.DisconnectionWaitable(self)
        self.connection_state = PeerState.CONNECTED
        self._current_connection_params = connection_params

        self._ble_device.ble_driver.event_subscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)
        self._ble_device.ble_driver.event_subscribe(self._on_connection_param_update, nrf_events.GapEvtConnParamUpdate,
                                                    nrf_events.GapEvtConnParamUpdateRequest)
        self.driver_event_subscribe(self._on_mtu_exchange_request, nrf_events.GattsEvtExchangeMtuRequest)
        self.driver_event_subscribe(self._on_mtu_exchange_response, nrf_events.GattcEvtMtuExchangeResponse)
        self._on_connect.notify(self)

    def _check_driver_event_connection_handle_wrapper(self, func):
        def wrapper(driver, event):
            """
            :param driver:
            :type event: blatann.nrf.nrf_events.BLEEvent
            """
            logger.debug("Got event: {} for peer {}".format(event, self.conn_handle))
            if self.connected and self.conn_handle == event.conn_handle:
                func(driver, event)
        return wrapper

    def driver_event_subscribe(self, handler, *event_types):
        """
        Internal method that subscribes handlers to NRF Driver events directed at this peer.
        Handlers are automatically unsubscribed once the peer disconnects

        :param handler: The handler to subscribe
        :param event_types: The NRF Driver event types to subscribe to
        """
        wrapped_handler = self._check_driver_event_connection_handle_wrapper(handler)
        with self._connection_handler_lock:
            if handler not in self._connection_based_driver_event_handlers:
                self._connection_based_driver_event_handlers[handler] = wrapped_handler
                self._ble_device.ble_driver.event_subscribe(wrapped_handler, *event_types)

    def driver_event_unsubscribe(self, handler, *event_types):
        """
        Internal method that unsubscribes handlers from NRF Driver events

        :param handler: The handler to unsubscribe
        :param event_types: The event types to unsubscribe from
        """
        with self._connection_handler_lock:
            wrapped_handler = self._connection_based_driver_event_handlers.get(handler, None)
            logger.debug("Unsubscribing {} ({})".format(handler, wrapped_handler))
            if wrapped_handler:
                self._ble_device.ble_driver.event_unsubscribe(wrapped_handler, *event_types)
                del self._connection_based_driver_event_handlers[handler]

    """
    Private Methods
    """

    def _on_disconnect_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.connection_state = PeerState.DISCONNECTED
        self._on_disconnect.notify(self, DisconnectionEventArgs(event.reason))

        with self._connection_handler_lock:
            for handler in self._connection_based_driver_event_handlers.values():
                self._ble_device.ble_driver.event_unsubscribe_all(handler)
            self._connection_based_driver_event_handlers = {}
        self._ble_device.ble_driver.event_unsubscribe(self._on_disconnect_event)
        self._ble_device.ble_driver.event_unsubscribe(self._on_connection_param_update)

    def _on_connection_param_update(self, driver, event):
        """
        :type event: nrf_events.GapEvtConnParamUpdate
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        if isinstance(event, nrf_events.GapEvtConnParamUpdateRequest):
            logger.debug("[{}] Conn Params updating to {}".format(self.conn_handle, self._ideal_connection_params))
            self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._ideal_connection_params)
        else:
            logger.debug("[{}] Updated to {}".format(self.conn_handle, event.conn_params))
        self._current_connection_params = event.conn_params

    def _validate_mtu_size(self, mtu_size):
        if mtu_size < MTU_SIZE_MINIMUM:
            raise ValueError("Invalid MTU size {}. "
                             "Minimum is {}".format(mtu_size, MTU_SIZE_MINIMUM))
        if mtu_size > self.max_mtu_size:
            raise ValueError("Invalid MTU size {}. "
                             "Maximum configured in the BLE device: {}".format(mtu_size, self._ble_device.max_mtu_size))

    def _resolve_mtu_exchange(self, our_mtu, peer_mtu):
        previous_mtu_size = self._mtu_size
        self._mtu_size = max(min(our_mtu, peer_mtu), MTU_SIZE_MINIMUM)
        logger.debug("[{}] MTU Exchange - Ours: {}, Peers: {}, Effective: {}".format(self.conn_handle,
                                                                                     our_mtu, peer_mtu, self._mtu_size))
        self._on_mtu_size_updated.notify(self, MtuSizeUpdatedEventArgs(previous_mtu_size, self._mtu_size))

        return previous_mtu_size, self._mtu_size

    def _on_mtu_exchange_request(self, driver, event):
        if self._negotiated_mtu_size is None:
            self._negotiated_mtu_size = self.preferred_mtu_size

        self._ble_device.ble_driver.ble_gatts_exchange_mtu_reply(self.conn_handle, self._negotiated_mtu_size)
        self._resolve_mtu_exchange(self._negotiated_mtu_size, event.client_mtu)

    def _on_mtu_exchange_response(self, driver, event):
        previous, current = self._resolve_mtu_exchange(self._negotiated_mtu_size, event.server_mtu)
        self._on_mtu_exchange_complete.notify(self, MtuSizeUpdatedEventArgs(previous, current))

    def __nonzero__(self):
        return self.conn_handle != BLE_CONN_HANDLE_INVALID

    def __bool__(self):
        return self.__nonzero__()


class Peripheral(Peer):
    """
    Object which represents a BLE-connected device that is acting as a peripheral/server (local device is client/central)
    """
    def __init__(self, ble_device, peer_address, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Peripheral, self).__init__(ble_device, nrf_events.BLEGapRoles.central, connection_params)
        self.peer_address = peer_address
        self.connection_state = PeerState.CONNECTING
        self._db = gattc.GattcDatabase(ble_device, self)
        self._discoverer = service_discovery.DatabaseDiscoverer(ble_device, self)

    @property
    def database(self):
        """
        Gets the database on the peripheral.
        NOTE: This is not useful until services are discovered first

        :return: The database instance
        :rtype: gattc.GattcDatabase
        """
        return self._db

    def discover_services(self):
        """
        Starts the database discovery process of the peripheral. This will discover all services, characteristics, and
        descriptors on the remote database.
        Returns an EventWaitable that will fire when the service discovery completes.
        Waitable returns 2  parameters: (Peripheral this, DatabaseDiscoveryCompleteEventArgs event args)

        :return: a Waitable that will fire when service discovery is complete
        :rtype: event_waitable.EventWaitable
        """
        self._discoverer.start()
        return event_waitable.EventWaitable(self._discoverer.on_discovery_complete)


class Client(Peer):
    """
    Object which represents a BLE-connected device that is acting as a client/central (local device is peripheral/server)
    """
    def __init__(self, ble_device, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Client, self).__init__(ble_device, nrf_events.BLEGapRoles.periph, connection_params)
