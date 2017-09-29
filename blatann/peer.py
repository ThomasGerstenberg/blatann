import enum
import logging
from blatann.nrf.nrf_types.enums import BLE_CONN_HANDLE_INVALID
from blatann.nrf import nrf_events
from blatann.event_type import Event, EventSource
from blatann.waitables import connection_waitable
from blatann import gattc, service_discovery


logger = logging.getLogger(__name__)


class PeerState(enum.Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class PeerAddress(nrf_events.BLEGapAddr):
    pass


class ConnectionParameters(nrf_events.BLEGapConnParams):
    def __init__(self, min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency=0):
        super(ConnectionParameters, self).__init__(min_conn_interval_ms, max_conn_interval_ms, timeout_ms, slave_latency)


DEFAULT_CONNECTION_PARAMS = ConnectionParameters(15, 30, 4000, 0)


class Peer(object):
    BLE_CONN_HANDLE_INVALID = BLE_CONN_HANDLE_INVALID

    def __init__(self, ble_device, role, connection_params=DEFAULT_CONNECTION_PARAMS):
        """
        :type ble_device: blatann.device.BleDevice
        """
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.peer_address = "",
        self.connection_state = PeerState.DISCONNECTED
        self._role = role
        self._on_disconnect = EventSource("On Disconnect", logger)
        self._ble_device = ble_device
        self._ideal_connection_params = connection_params
        self._current_connection_params = DEFAULT_CONNECTION_PARAMS

    @property
    def connected(self):
        return self.connection_state == PeerState.CONNECTED

    @property
    def on_disconnect(self):
        return self._on_disconnect

    def disconnect(self, status_code=nrf_events.BLEHci.remote_user_terminated_connection):
        if self.connection_state != PeerState.CONNECTED:
            return
        self._ble_device.ble_driver.ble_gap_disconnect(self.conn_handle, status_code)
        return self._disconnect_waitable

    def set_connection_parameters(self, connection_params=None):
        if connection_params:
            self._ideal_connection_params = connection_params
        if not self.connected:
            return
        # Do stuff to set the connection parameters
        self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._ideal_connection_params)

    def peer_connected(self, conn_handle, peer_address, connection_params):
        self.conn_handle = conn_handle
        self.peer_address = peer_address
        self._disconnect_waitable = connection_waitable.DisconnectionWaitable(self)
        self.connection_state = PeerState.CONNECTED
        self._current_connection_params = connection_params
        self._ble_device.ble_driver.event_subscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)
        self._ble_device.ble_driver.event_subscribe(self._on_connection_param_update, nrf_events.GapEvtConnParamUpdate,
                                                    nrf_events.GapEvtConnParamUpdateRequest)

    def _on_disconnect_event(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        self.conn_handle = BLE_CONN_HANDLE_INVALID
        self.connection_state = PeerState.DISCONNECTED
        self._ble_device.ble_driver.event_unsubscribe(self._on_disconnect_event, nrf_events.GapEvtDisconnected)
        self._ble_device.ble_driver.event_unsubscribe(self._on_connection_param_update,
                                                      nrf_events.GapEvtConnParamUpdate,
                                                      nrf_events.GapEvtConnParamUpdateRequest)
        self._on_disconnect.notify(self, event.reason)

    def _on_connection_param_update(self, driver, event):
        """
        :type event: nrf_events.GapEvtConnParamUpdate
        """
        if not self.connected or self.conn_handle != event.conn_handle:
            return
        if isinstance(event, nrf_events.GapEvtConnParamUpdateRequest) or self._role == nrf_events.BLEGapRoles.periph:
            logger.debug("[{}] Conn Params updating to {}".format(self.conn_handle, self._ideal_connection_params))
            self._ble_device.ble_driver.ble_gap_conn_param_update(self.conn_handle, self._ideal_connection_params)
        else:
            logger.debug("[{}] Updated to {}".format(self.conn_handle, event.conn_params))
        self._current_connection_params = event.conn_params

    def __nonzero__(self):
        return self.conn_handle != BLE_CONN_HANDLE_INVALID

    def __bool__(self):
        return self.__nonzero__()


class Peripheral(Peer):
    def __init__(self, ble_device, peer_address, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Peripheral, self).__init__(ble_device, nrf_events.BLEGapRoles.central, connection_params)
        self.peer_address = peer_address
        self.connection_state = PeerState.CONNECTING
        self._db = gattc.GattcDatabase(ble_device, self)
        self._discoverer = service_discovery.DatabaseDiscoverer(ble_device, self)

    @property
    def database(self):
        return self._db

    def discover_services(self, service_uuid=None):
        self._discoverer.discover_services(service_uuid)


class Client(Peer):
    def __init__(self, ble_device, connection_params=DEFAULT_CONNECTION_PARAMS):
        super(Client, self).__init__(ble_device, nrf_events.BLEGapRoles.periph, connection_params)
        self._on_connect = EventSource("On Connect", logger)

    @property
    def on_connect(self):
        return self._on_connect

    def peer_connected(self, conn_handle, peer_address, connection_params):
        super(Client, self).peer_connected(conn_handle, peer_address, connection_params)
        self._on_connect.notify(self)
