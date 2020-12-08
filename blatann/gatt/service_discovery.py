import logging

from blatann.event_type import EventSource, Event
from blatann.gatt import gattc
from blatann.nrf import nrf_events
from blatann.waitables.event_waitable import EventWaitable
from blatann.event_args import EventArgs, DatabaseDiscoveryCompleteEventArgs


logger = logging.getLogger(__name__)


class _DiscoveryEventArgs(EventArgs):
    def __init__(self, services, status):
        """
        :type services: list[gattc.GattcService]
        :type status: nrf_events.BLEGattStatusCode
        """
        self.services = services
        self.status = status


class _DiscoveryState(object):
    def __init__(self):
        self.current_handle = 0x0001
        self.services = []
        self.characteristics = []
        self.service_index = 0
        self.char_index = 0
        self.iterate_by_chars = False

    def reset(self):
        self.current_handle = 0x0001
        self.services = []
        self.characteristics = []
        self.service_index = 0
        self.char_index = 0

    @property
    def end_of_services(self):
        return self.service_index >= len(self.services)

    @property
    def end_of_characteristics(self):
        if self.iterate_by_chars:
            return self.char_index >= len(self.characteristics)
        return self.char_index >= len(self.current_service.chars)

    @property
    def current_characteristic(self):
        """
        :rtype: nrf_events.BLEGattCharacteristic
        """
        if self.iterate_by_chars:
            return self.characteristics[self.char_index]
        return self.current_service.chars[self.char_index]

    @property
    def current_service(self):
        """
        :rtype: nrf_events.BLEGattService
        """
        return self.services[self.service_index]

    def iter_remaining(self):
        first_service = True
        for service in self.services[self.service_index:]:
            start_char_index = self.char_index if first_service else 0
            first_service = False
            for c in service.chars[start_char_index:]:
                yield service, c


class _Discoverer(object):
    def __init__(self, name, ble_device, peer):
        """
        :type ble_device: blatann.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self._state = _DiscoveryState()
        self._on_complete_event = EventSource("{} Complete".format(name), logger)

    def start(self, services):
        raise NotImplementedError

    @property
    def on_complete(self):
        """
        :rtype: Event
        """
        return self._on_complete_event


class _ServiceDiscoverer(_Discoverer):
    def __init__(self, ble_device, peer):
        super(_ServiceDiscoverer, self).__init__("Service Discovery", ble_device, peer)

    def start(self, services=None):
        self._state.reset()

        self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, None,
                                                            self._state.current_handle)

        self.peer.driver_event_subscribe(self._on_primary_service_discovery, nrf_events.GattcEvtPrimaryServiceDiscoveryResponse)
        self.peer.driver_event_subscribe(self._on_service_uuid_read, nrf_events.GattcEvtReadResponse)
        return EventWaitable(self.on_complete)

    def _on_complete(self, status=nrf_events.BLEGattStatusCode.success):
        self.peer.driver_event_unsubscribe(self._on_primary_service_discovery)
        self.peer.driver_event_unsubscribe(self._on_service_uuid_read)
        self._on_complete_event.notify(self, _DiscoveryEventArgs(self._state.services, status))

    def _on_primary_service_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtPrimaryServiceDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status == nrf_events.BLEGattStatusCode.success:
            # Add the services discovered and check to see if there's more
            self._state.services.extend(event.services)
            end_handle = event.services[-1].end_handle
            if end_handle != 0xFFFF:
                # Continue service discovery
                self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, None, end_handle+1)
            else:
                # Reached the end of the handle range, now discover their UUIDs
                self._discover_uuids()
        elif event.status == nrf_events.BLEGattStatusCode.attribute_not_found:
            # No other attributes/services are found, continue on to discover UUIDs
            self._discover_uuids()
        else:
            # Other non-successful error codes should terminate service discovery
            self._on_complete(event.status)

    def _discover_uuids(self):
        while not self._state.end_of_services:
            service = self._state.current_service
            if service.uuid.base.type == 0:  # Unknown base, register
                self.ble_device.ble_driver.ble_gattc_read(self.peer.conn_handle, service.start_handle)
                return
            self._state.service_index += 1
        self._on_complete()

    def _on_service_uuid_read(self, driver, event):
        """
        :type event: nrf_events.GattcEvtReadResponse
        """
        if self.peer.conn_handle != event.conn_handle:
            return

        logger.debug(("Got gattc read: {}".format(event)))
        service = self._state.current_service

        if event.attr_handle != service.start_handle:
            return

        # Length should be 16 for 128-bit uuids
        if len(event.data) != 16:
            logger.error("Service UUID not 16 bytes: {}".format(event.data))
        else:
            nrf_uuid = nrf_events.BLEUUID.from_array(event.data)
            self.ble_device.uuid_manager.register_uuid(nrf_uuid)
            logger.info("Discovered UUID: {}".format(nrf_uuid))
            self._state.current_service.uuid = nrf_uuid

        self._state.service_index += 1
        self._discover_uuids()


class _CharacteristicDiscoverer(_Discoverer):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        super(_CharacteristicDiscoverer, self).__init__("Characteristic Discovery", ble_device, peer)

    def start(self, services):
        self._state.reset()
        self._state.services = services

        self.peer.driver_event_subscribe(self._on_characteristic_discovery, nrf_events.GattcEvtCharacteristicDiscoveryResponse)
        self.peer.driver_event_subscribe(self._on_char_uuid_read, nrf_events.GattcEvtReadResponse)

        self._discover_characteristics()
        return EventWaitable(self.on_complete)

    def _on_complete(self, status=nrf_events.BLEGattStatusCode.success):
        self.peer.driver_event_unsubscribe(self._on_characteristic_discovery)
        self.peer.driver_event_unsubscribe(self._on_char_uuid_read)
        self._on_complete_event.notify(self, _DiscoveryEventArgs(self._state.services, status))

    def _discover_characteristics(self):
        service = self._state.current_service
        self.ble_device.ble_driver.ble_gattc_char_disc(self.peer.conn_handle, service.start_handle, service.end_handle)

    def _on_characteristic_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtCharacteristicDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status == nrf_events.BLEGattStatusCode.attribute_not_found:
            # Done discovering characteristics in this service, discover next service or unknown UUIDs
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_uuids()
            else:
                self._discover_characteristics()
            return
        elif event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)
            return

        service = self._state.current_service
        for c in event.characteristics:
            service.char_add(c)
        last_char = event.characteristics[-1]
        if last_char.handle_value == service.end_handle:
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_uuids()
            else:
                self._discover_characteristics()
            return
        else:
            self.ble_device.ble_driver.ble_gattc_char_disc(self.peer.conn_handle, last_char.handle_decl + 1, service.end_handle)

    def _discover_uuids(self):
        while not self._state.end_of_services:
            while not self._state.end_of_characteristics:
                # Check uuid
                char = self._state.current_characteristic
                if char.uuid.base.type == 0:
                    self.ble_device.ble_driver.ble_gattc_read(self.peer.conn_handle, char.handle_decl)
                    return
                self._state.char_index += 1
            self._state.char_index = 0
            self._state.service_index += 1
        self._on_complete()

    def _on_char_uuid_read(self, driver, event):
        """
        :type event: nrf_events.GattcEvtReadResponse
        """
        if self.peer.conn_handle != event.conn_handle:
            return

        logger.debug(("Got gattc read: {}".format(event)))
        char = self._state.current_characteristic

        if event.attr_handle != char.handle_decl:
            return

        # First 3 bytes are [permissions (1 byte), value handle (2 bytes)]
        uuid_bytes = event.data[3:]
        # Length should be 16 for 128-bit uuids
        if len(uuid_bytes) != 16:
            logger.error("Characteristic UUID not 16 bytes: {}".format(uuid_bytes))
        else:
            nrf_uuid = nrf_events.BLEUUID.from_array(uuid_bytes)
            self.ble_device.uuid_manager.register_uuid(nrf_uuid)
            logger.info("Discovered UUID: {}".format(nrf_uuid))
            char.uuid = nrf_uuid

        self._state.char_index += 1
        if self._state.end_of_characteristics:
            self._state.service_index += 1
            self._state.char_index = 0
        self._discover_uuids()


class _DescriptorDiscoverer(_Discoverer):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        super(_DescriptorDiscoverer, self).__init__("Descriptor Discovery", ble_device, peer)

    def start(self, services):
        self._state.reset()
        self._state.services = services
        self.peer.driver_event_subscribe(self._on_descriptor_discovery, nrf_events.GattcEvtDescriptorDiscoveryResponse)
        on_complete_waitable = EventWaitable(self.on_complete)
        if not self._state.services:
            self._on_complete()
        else:
            self._discover_next_handle_range()
        return on_complete_waitable

    def _on_complete(self, status=nrf_events.BLEGattStatusCode.success):
        self.peer.driver_event_unsubscribe(self._on_descriptor_discovery)
        self._on_complete_event.notify(self, _DiscoveryEventArgs(self._state.services, status))

    def _discover_descriptors(self):
        starting_handle = self._state.current_handle
        ending_handle = self._state.services[-1].end_handle
        self.peer.driver_event_subscribe(self._on_descriptor_discovery, nrf_events.GattcEvtDescriptorDiscoveryResponse)
        self.ble_device.ble_driver.ble_gattc_desc_disc(self.peer.conn_handle, starting_handle, ending_handle)

    def _discover_next_handle_range(self):
        for service, characteristic in self._state.iter_remaining():
            missing_handles = characteristic.missing_handles()
            if missing_handles:
                self._state.current_handle = missing_handles[0]
                self._discover_descriptors()
                return
        logger.info("No more handles left to discover!")
        self._on_complete()

    def _find_descriptor_owner(self, desc):
        if self._state.end_of_services:
            return

        service = self._state.current_service
        if desc.handle < service.start_handle:
            logger.error(f"Got attribute handle {desc.handle} which is before service handle {service.start_handle}")
            return
        if desc.handle > service.end_handle:
            self._state.service_index += 1
            self._state.char_index = 0
            return self._find_descriptor_owner(desc)
        if desc.handle == service.start_handle:
            service.attrs.append(desc)
            return
        for char in service.chars:
            if char.handle_decl <= desc.handle <= char.end_handle:
                char.descs.append(desc)
                return
        logger.error(f"Unable to find characteristic for attr handle {desc.handle}")

    def _on_descriptor_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtDescriptorDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status == nrf_events.BLEGattStatusCode.attribute_not_found:
            self._on_complete()
            return
        elif event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)
            return

        for desc in event.descriptions:
            self._find_descriptor_owner(desc)

        # Check if everything has been found
        if self._state.end_of_services:
            self._on_complete()
            return

        last_handle = event.descriptions[-1].handle
        self._state.current_handle = last_handle + 1

        if last_handle >= self._state.services[-1].end_handle:
            self._on_complete()

        self._discover_next_handle_range()


class DatabaseDiscoverer(object):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        self.ble_device = ble_device
        self.peer = peer
        self._on_discovery_complete = EventSource("Service Discovery Complete", logger)
        self._on_database_discovery_complete = EventSource("Service Discovery Complete", logger)
        self._state = _DiscoveryState()
        self._service_discoverer = _ServiceDiscoverer(ble_device, peer)
        self._characteristic_discoverer = _CharacteristicDiscoverer(ble_device, peer)
        self._descriptor_discoverer = _DescriptorDiscoverer(ble_device, peer)

    @property
    def on_discovery_complete(self):
        """
        :rtype: Event[blatann.peer.Peripheral, DatabaseDiscoveryCompleteEventArgs]
        """
        return self._on_discovery_complete

    def _on_service_discovery_complete(self, sender, event_args):
        """
        :type sender: _ServiceDiscoverer
        :type event_args: _DiscoveryEventArgs
        """
        logger.info("Service Discovery complete")
        if event_args.status != nrf_events.BLEGattStatusCode.success:
            logger.error("Error discovering services: {}".format(event_args.status))
            self._on_complete([], event_args.status)
        else:
            self._characteristic_discoverer.start(event_args.services).then(self._on_characteristic_discovery_complete)

    def _on_characteristic_discovery_complete(self, sender, event_args):
        """
        :type sender: _CharacteristicDiscoverer
        :type event_args: _DiscoveryEventArgs
        """
        logger.info("Characteristic Discovery complete")
        if event_args.status != nrf_events.BLEGattStatusCode.success:
            logger.error("Error discovering characteristics: {}".format(event_args.status))
            self._on_complete([], event_args.status)
        else:
            self._descriptor_discoverer.start(event_args.services).then(self._on_descriptor_discovery_complete)

    def _on_descriptor_discovery_complete(self, sender, event_args):
        """
        :type sender: _DescriptorDiscoverer
        :type event_args: _DiscoveryEventArgs
        """
        logger.info("Descriptor Discovery complete")
        self._on_complete(event_args.services, event_args.status)

    def _on_complete(self, services, status):
        self.peer.database.add_discovered_services(services)
        self._on_discovery_complete.notify(self.peer, DatabaseDiscoveryCompleteEventArgs(status))
        logger.info("Database Discovery complete")

    def start(self):
        logger.info("Starting discovery..")
        self._service_discoverer.start().then(self._on_service_discovery_complete)
