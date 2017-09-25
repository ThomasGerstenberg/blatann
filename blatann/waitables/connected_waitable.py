import queue
from blatann.waitables.waitable import Waitable
from blatann import peer
from blatann.nrf.nrf_events import GapEvtConnected, GapEvtTimeout, BLEGapRoles, BLEGapTimeoutSrc


class ConnectionWaitable(Waitable):
    def __init__(self, ble_device, current_peer=None, role=BLEGapRoles.periph):
        """
        :type ble_driver: blatann.device.BleDevice
        :param current_peer:
        """
        self._callback = None
        self._peer = current_peer or peer.Peer()
        self._queue = queue.Queue()
        self._role = role
        ble_device.ble_driver.event_subscribe(self._on_connected_event, GapEvtConnected)
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, GapEvtTimeout)

    def _event_occured(self, ble_driver, result):
        ble_driver.event_unsubscribe(self._on_connected_event, GapEvtConnected)
        ble_driver.event_unsubscribe(self._on_timeout_event, GapEvtTimeout)
        self._queue.put(result)
        if self._callback:
            self._callback(result)

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

    def wait(self, timeout=None, exception_on_timeout=True):
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            if exception_on_timeout:
                raise
        return None

    def then(self, func_to_execute):
        self._callback = func_to_execute
        return self
