from __future__ import annotations

import asyncio
import typing

from blatann.exceptions import InvalidStateException
from blatann.nrf import nrf_events, nrf_types
from blatann.waitables.waitable import Waitable

if typing.TYPE_CHECKING:
    from blatann.device import BleDevice
    from blatann.event_args import DisconnectionEventArgs
    from blatann.peer import Client, Peer, Peripheral


class ConnectionWaitable(Waitable):
    def __init__(self, ble_device: BleDevice, current_peer: Peer, role=nrf_types.BLEGapRoles.periph):
        super().__init__()
        self._peer = current_peer
        self._role = role
        self.ble_driver = ble_device.ble_driver
        ble_device.ble_driver.event_subscribe(self._on_connected_event, nrf_events.GapEvtConnected)
        ble_device.ble_driver.event_subscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)

    def wait(self, timeout: float = None, exception_on_timeout=True) -> Peer:
        return super().wait(timeout, exception_on_timeout)

    async def as_async(self, timeout: float = None, exception_on_timeout=True, loop: asyncio.AbstractEventLoop = None) -> Peer:
        return await super().as_async(timeout, exception_on_timeout, loop)

    def _event_occured(self, ble_driver, result):
        ble_driver.event_unsubscribe(self._on_connected_event, nrf_events.GapEvtConnected)
        ble_driver.event_unsubscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)
        self._notify(result)

    def _on_timeout(self):
        self.ble_driver.event_unsubscribe(self._on_connected_event, nrf_events.GapEvtConnected)
        self.ble_driver.event_unsubscribe(self._on_timeout_event, nrf_events.GapEvtTimeout)

    def _on_timeout_event(self, ble_driver, event: nrf_events.GapEvtTimeout):
        if self._role == nrf_types.BLEGapRoles.periph:
            expected_source = nrf_types.BLEGapTimeoutSrc.advertising
        else:
            expected_source = nrf_types.BLEGapTimeoutSrc.conn
        if event.src == expected_source:
            self._event_occured(ble_driver, None)

    def _on_connected_event(self, ble_driver, event: nrf_events.GapEvtConnected):
        if event.role != self._role:
            return
        self._event_occured(ble_driver, self._peer)


class ClientConnectionWaitable(ConnectionWaitable):
    def __init__(self, ble_device: BleDevice, peer: Peer):
        super().__init__(ble_device, peer, nrf_types.BLEGapRoles.periph)

    def wait(self, timeout=None, exception_on_timeout=True) -> Client:
        return super().wait(timeout, exception_on_timeout)


class PeripheralConnectionWaitable(ConnectionWaitable):
    def __init__(self, ble_device, peer):
        super().__init__(ble_device, peer, nrf_types.BLEGapRoles.central)

    def wait(self, timeout=None, exception_on_timeout=True) -> Peripheral:
        return super().wait(timeout, exception_on_timeout)


class DisconnectionWaitable(Waitable):
    def __init__(self, connected_peer: Peer):
        super().__init__(n_args=2)
        if not connected_peer:
            raise InvalidStateException("Peer already disconnected")
        connected_peer.on_disconnect.register(self._on_disconnect)

    def _on_disconnect(self, disconnected_peer: Peer, event_args: DisconnectionEventArgs):
        disconnected_peer.on_disconnect.deregister(self._on_disconnect)
        self._notify(disconnected_peer, event_args)
