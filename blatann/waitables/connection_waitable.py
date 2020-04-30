from blatann.waitables.waitable import Waitable
from blatann.nrf.nrf_events import GapEvtConnected, GapEvtTimeout, BLEGapRoles, BLEGapTimeoutSrc, GapEvtDisconnected
from blatann.exceptions import InvalidStateException


class ConnectionWaitable(Waitable):
    def __init__(self, ble_device, current_peer, role=BLEGapRoles.periph):
        """
        :type ble_driver: blatann.device.BleDevice
        :type current_peer: blatann.peer.Peer
        """
        super(ConnectionWaitable, self).__init__()
        self._peer = current_peer
        self._role = role
        self.ble_driver = ble_device.ble_driver
        ble_device.ble_driver.event_subscribe(self._on_connected_event, GapEvtConnected)
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)

    def wait(self, timeout=None, exception_on_timeout=True):
        """
        :rtype: blatann.peer.Peer
        """
        return super(ConnectionWaitable, self).wait(timeout, exception_on_timeout)

    def _event_occured(self, ble_driver, result):
        ble_driver.event_unsubscribe(self._on_connected_event, GapEvtConnected)
        ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self._notify(result)

    def _on_timeout(self):
        self.ble_driver.event_unsubscribe(self._on_connected_event, GapEvtConnected)
        self.ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)

    def _on_timeout_event(self, ble_driver, event):
        """
        :type event: GapEvtTimeout
        """
        if self._role == BLEGapRoles.periph:
            expected_source = BLEGapTimeoutSrc.advertising
        else:
            expected_source = BLEGapTimeoutSrc.conn
        if event.src == expected_source:
            self._event_occured(ble_driver, None)

    def _on_connected_event(self, ble_driver, event):
        """
        :type event: GapEvtConnected
        """
        if event.role != self._role:
            return
        self._event_occured(ble_driver, self._peer)


class ClientConnectionWaitable(ConnectionWaitable):
    def __init__(self, ble_device, peer):
        super(ClientConnectionWaitable, self).__init__(ble_device, peer, BLEGapRoles.periph)

    def wait(self, timeout=None, exception_on_timeout=True):
        """
        :rtype: blatann.peer.Client
        """
        return super(ClientConnectionWaitable, self).wait(timeout, exception_on_timeout)


class PeripheralConnectionWaitable(ConnectionWaitable):
    def __init__(self, ble_device, peer):
        super(PeripheralConnectionWaitable, self).__init__(ble_device, peer, BLEGapRoles.central)

    def wait(self, timeout=None, exception_on_timeout=True):
        """
        :rtype: blatann.peer.Peripheral
        """
        return super(PeripheralConnectionWaitable, self).wait(timeout, exception_on_timeout)


class DisconnectionWaitable(Waitable):
    def __init__(self, connected_peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type connected_peer: blatann.peer.Peer
        """
        super(DisconnectionWaitable, self).__init__(n_args=2)
        if not connected_peer:
            raise InvalidStateException("Peer already disconnected")
        connected_peer.on_disconnect.register(self._on_disconnect)

    def _on_disconnect(self, disconnected_peer, event_args):
        disconnected_peer.on_disconnect.deregister(self._on_disconnect)
        self._notify(disconnected_peer, event_args)

