import logging
from blatann.event_type import EventSource, Event
from blatann.nrf import nrf_events
from blatann import gatt, gattc, uuid

logger = logging.getLogger(__name__)


class _DiscoveryState(object):
    def __init__(self):
        self.current_handle = 0x0001
        self.services = []
        self.service_index = 0
        self.char_index = 0
        self.desc_index = 0
        self.current_uuid = None

    def reset(self):
        self.current_handle = 0x0001
        self.services = []
        self.service_index = 0
        self.char_index = 0
        self.desc_index = 0
        self.current_uuid = None

    @property
    def end_of_services(self):
        return self.service_index >= len(self.services)

    @property
    def end_of_characteristics(self):
        return self.char_index >= len(self.current_service.chars)

    @property
    def current_characteristic(self):
        return self.current_service.chars[self.char_index]

    @property
    def current_service(self):
        return self.services[self.service_index]


class ServiceDiscoverer(object):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        """
        self.ble_device = ble_device
        self.peer = peer
        self._state = _DiscoveryState()
        self._service_disc_on_complete = EventSource("Service Discovery Complete", logger)
        self._services_discovered = []

    def start(self, service_uuid):
        if service_uuid:
            self.ble_device.uuid_manager.register_uuid(service_uuid)

        self._state.current_uuid = service_uuid
        self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, self._state.current_uuid,
                                                            self._state.current_handle)

        self.ble_device.ble_driver.event_subscribe(self._on_primary_service_discovery,
                                                   nrf_events.GattcEvtPrimaryServiceDiscoveryResponse)
        self.ble_device.ble_driver.event_subscribe(self._on_service_uuid_read,
                                                   nrf_events.GattcEvtReadResponse)

    def _on_complete(self, status):
        self.ble_device.ble_driver.event_unsubscribe(self._on_primary_service_discovery,
                                                     nrf_events.GattcEvtPrimaryServiceDiscoveryResponse)
        self.ble_device.ble_driver.event_unsubscribe(self._on_service_uuid_read,
                                                     nrf_events.GattcEvtReadResponse)
        self._service_disc_on_complete.notify(self._services_discovered, status)

    def _on_primary_service_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtPrimaryServiceDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)  # Not found, done
            return

        self._state.services.extend(event.services)
        end_handle = event.services[-1].end_handle
        if end_handle != 0xFFFF:
            # Continue service discovery
            self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, self._state.current_uuid,
                                                                end_handle+1)
            return

        # Done discovering services, now discover their attributes
        self._discover_uuids()

    def _discover_uuids(self):
        while self._state.service_index < len(self._state.services):
            service = self._state.current_service
            if service.uuid.base.type == 0:  # Unknown base, register
                self.ble_device.ble_driver.ble_gattc_read(self.peer.conn_handle, service.start_handle)
                return
            service_uuid = self.ble_device.uuid_manager.nrf_uuid_to_uuid(service.uuid)
            self._services_discovered.append(gattc.GattcService(self.ble_device, self.peer, service_uuid,
                                                                gatt.ServiceType.PRIMARY,
                                                                service.start_handle, service.end_handle))
            self._state.service_index += 1
        logger.info("Service discovery complete")
        self._on_complete(nrf_events.BLEGattStatusCode.success)

    def _on_service_uuid_read(self, driver, event):
        """
        :type event: nrf_events.GattcEvtReadResponse
        """
        logger.info(("Got gattc read"))
        logger.info("{}".format(event))
        # Length should be 16 for 128-bit uuids
        if len(event.data) != 16:
            logger.error("Service UUID not 16 bytes")
        else:
            service = self._state.current_service
            nrf_uuid128 = nrf_events.BLEUUID.from_array(event.data)
            # Register UUID, assign to service
            uuid128 = uuid.Uuid128.combine_with_base(nrf_uuid128.get_value(), nrf_uuid128.base.base)
            self.ble_device.uuid_manager.register_uuid(uuid128)
            service_discovered = gattc.GattcService(self.ble_device, self.peer, uuid128, gatt.ServiceType.PRIMARY,
                                                    service.start_handle, service.end_handle)
            self._services_discovered.append(service_discovered)
            logger.info("Discovered UUID: {}".format(uuid128))
        self._state.service_index += 1
        self._discover_uuids()


class CharacteristicDiscoverer(object):
    def __init__(self, ble_device, peer, services=None):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        """
        self.ble_device = ble_device
        self.peer = peer
        self._state = _DiscoveryState()
        self._state.services = services or []
        self._on_characteristic_complete = EventSource("Characteristic Discovery Complete", logger)

    def _on_complete(self, status):
        self.ble_device.ble_driver.event_unsubscribe(self._on_characteristic_discovery,
                                                     nrf_events.GattcEvtCharacteristicDiscoveryResponse)
        self.ble_device.ble_driver.event_unsubscribe(self._on_descriptor_discovery,
                                                     nrf_events.GattcEvtDescriptorDiscoveryResponse)

    def start(self, *services):
        if services:
            self._state.services = services

        self.ble_device.ble_driver.event_subscribe(self._on_characteristic_discovery,
                                                   nrf_events.GattcEvtCharacteristicDiscoveryResponse)
        self.ble_device.ble_driver.event_subscribe(self._on_descriptor_discovery,
                                                   nrf_events.GattcEvtDescriptorDiscoveryResponse)

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
            # Done discovering characteristics, discover next service or descriptors
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_descriptors()
            else:
                self._discover_characteristics()
            return
        elif event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)
            return

        service = self._state.current_service
        map(service.char_add, event.characteristics)
        last_char = event.characteristics[-1]
        if last_char.handle_value == service.end_handle:
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_descriptors()
                return
            self._discover_characteristics()
        else:
            self.ble_device.ble_driver.ble_gattc_char_disc(self.peer.conn_handle, last_char.handle_decl + 1, service.end_handle)


class DatabaseDiscoverer(object):
    def __init__(self, ble_device, peer):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        """
        self.ble_device = ble_device
        self.peer = peer
        self._on_discovery_complete = EventSource("Service Discovery Complete", logger)
        self._on_service_discovery_complete = EventSource("Service Discovery Complete", logger)
        self._state = _DiscoveryState()
        self.db = gattc.GattcDatabase(ble_device, peer)
        self._service_discoverer = ServiceDiscoverer(ble_device, peer)

    def _on_complete(self, status):
        self.ble_device.ble_driver.event_unsubscribe(self._on_primary_service_discovery,
                                                     nrf_events.GattcEvtPrimaryServiceDiscoveryResponse)
        self.ble_device.ble_driver.event_unsubscribe(self._on_characteristic_discovery,
                                                     nrf_events.GattcEvtCharacteristicDiscoveryResponse)
        self.ble_device.ble_driver.event_unsubscribe(self._on_descriptor_discovery,
                                                     nrf_events.GattcEvtDescriptorDiscoveryResponse)

    def discover_services(self, service_uuid=None):
        # self.ble_device.ble_driver.event_subscribe(self._on_primary_service_discovery,
        #                                            nrf_events.GattcEvtPrimaryServiceDiscoveryResponse)
        # self.ble_device.ble_driver.event_subscribe(self._on_characteristic_discovery,
        #                                            nrf_events.GattcEvtCharacteristicDiscoveryResponse)
        # self.ble_device.ble_driver.event_subscribe(self._on_descriptor_discovery,
        #                                            nrf_events.GattcEvtDescriptorDiscoveryResponse)
        # self._state.reset()
        #
        # if service_uuid:
        #     self.ble_device.uuid_manager.register_uuid(service_uuid)
        # self._state.current_uuid = service_uuid
        # self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, self._state.current_uuid,
        #                                                     self._state.current_handle)
        self._service_discoverer.start(service_uuid)

    def _on_primary_service_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtPrimaryServiceDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)  # Not found, done
            return
        self._state.services.extend(event.services)
        end_handle = event.services[-1].end_handle
        if end_handle != 0xFFFF:
            # Continue service discovery
            self.ble_device.ble_driver.ble_gattc_prim_srvc_disc(self.peer.conn_handle, self._state.current_uuid,
                                                                end_handle+1)
            return

        # Start characteristic discovery
        self._state.service_index = 0
        self._discover_characteristics()

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
            # Done discovering characteristics, discover next service or descriptors
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_descriptors()
            else:
                self._discover_characteristics()
            return
        elif event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)
            return

        service = self._state.current_service
        map(service.char_add, event.characteristics)
        last_char = event.characteristics[-1]
        if last_char.handle_value == service.end_handle:
            self._state.service_index += 1
            self._state.char_index = 0
            if self._state.end_of_services:
                self._state.service_index = 0
                self._discover_descriptors()
                return
            self._discover_characteristics()
        else:
            self.ble_device.ble_driver.ble_gattc_char_disc(self.peer.conn_handle, last_char.handle_decl + 1, service.end_handle)

    def _discover_descriptors(self):
        char = self._state.current_characteristic
        self.ble_device.ble_driver.ble_gattc_desc_disc(self.peer.conn_handle, char.handle_value, char.end_handle)

    def _on_descriptor_discovery(self, driver, event):
        """
        :type event: nrf_events.GattcEvtDescriptorDiscoveryResponse
        """
        if not self.peer.connected:
            logger.warning("Primary service discovery for a disconnected peer")
        if event.conn_handle != self.peer.conn_handle:
            return

        if event.status == nrf_events.BLEGattStatusCode.attribute_not_found:
            self._state.char_index += 1
            if self._state.end_of_characteristics:
                self._state.service_index += 1
                self._state.char_index = 0
                if self._state.end_of_services:
                    self._state.service_index = 0
                    self._attr_discover()
                    return
        elif event.status != nrf_events.BLEGattStatusCode.success:
            self._on_complete(event.status)
            return

        char = self._state.current_characteristic
        char.descs.extend(event.descriptions)

        last_desc = event.descriptions[-1]
        if last_desc.handle == char.end_handle:
            self._state.char_index += 1
            if self._state.end_of_characteristics:
                self._state.service_index += 1
                self._state.char_index = 0
                if self._state.end_of_services:
                    self._state.service_index = 0
                    self._attr_discover()
                    return

    def _attr_discover(self):
        pass
