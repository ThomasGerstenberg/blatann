import logging
from enum import IntEnum
from blatann.nrf import nrf_events, nrf_types
from blatann import uuid
from blatann.waitables.connection_waitable import ConnectionWaitable
from blatann.event_type import Event, EventSource


logger = logging.getLogger(__name__)


class AdvertisingFlags(IntEnum):
    # TODO: Not working as expected, IntFlag isn't available
    LIMITED_DISCOVERY_MODE = 0x01
    GENERAL_DISCOVERY_MODE = 0x02
    BR_EDR_NOT_SUPPORTED = 0x04
    BR_EDR_CONTROLLER = 0x08
    BR_EDR_HOST = 0x10


class AdvertisingData(object):
    MAX_ENCODED_LENGTH = 31

    Types = nrf_types.BLEAdvData.Types

    def __init__(self, flags=None, local_name=None, local_name_complete=True,
                 service_uuid16s=None, service_uuid128s=None,
                 has_more_uuid16_services=False, has_more_uuid128_services=False,
                 service_data=None, manufacturer_data=None, **kwargs):
        self.flags = flags
        self.local_name = local_name
        self.local_name_complete = local_name_complete
        self.service_uuid16s = service_uuid16s or []
        self.service_uuid128s = service_uuid128s or []
        self.has_more_uuid16_services = has_more_uuid16_services
        self.has_more_uuid128_services = has_more_uuid128_services
        self.service_data = service_data
        self.manufacturer_data = manufacturer_data
        self.other_records = {self.Types[k]: v for k, v in kwargs.items()}
        if not isinstance(self.service_uuid16s, (list, tuple)):
            self.service_uuid16s = [self.service_uuid16s]
        if not isinstance(self.service_uuid128s, (list, tuple)):
            self.service_uuid128s = [self.service_uuid128s]

    @property
    def service_uuids(self):
        return self.service_uuid16s + self.service_uuid128s

    def check_encoded_length(self):
        ble_adv_data = self.to_ble_adv_data()
        encoded_data = ble_adv_data.to_list()
        return len(encoded_data), len(encoded_data) <= self.MAX_ENCODED_LENGTH

    def to_ble_adv_data(self):
        records = self.other_records.copy()
        if self.flags:
            records[self.Types.flags] = [int(self.flags)]
        if self.local_name:
            name_type = self.Types.complete_local_name if self.local_name_complete else self.Types.short_local_name
            records[name_type] = self.local_name
        if self.service_uuid128s:
            uuid_type = self.Types.service_128bit_uuid_more_available if self.has_more_uuid128_services else self.Types.service_128bit_uuid_complete
            # UUID data is little-endian, reverse the lists and concatenate
            uuid_data = []
            for u in self.service_uuid128s:
                uuid_data.extend(u.uuid[::-1])
            records[uuid_type] = uuid_data
        if self.service_uuid16s:
            uuid_type = self.Types.service_16bit_uuid_more_available if self.has_more_uuid16_services else self.Types.service_16bit_uuid_complete
            uuid_data = []
            for u in self.service_uuid16s:
                uuid_data.append(u.uuid & 0xFF)
                uuid_data.append((u.uuid >> 8) & 0xFF)
            records[uuid_type] = uuid_data
        if self.service_data:
            records[self.Types.service_data] = self.service_data
        if self.manufacturer_data:
            records[self.Types.manufacturer_specific_data] = self.manufacturer_data

        record_string_keys = {k.name: v for k, v in records.items()}
        return nrf_types.BLEAdvData(**record_string_keys)

    @classmethod
    def from_ble_adv_records(cls, advertise_records):
        flags = advertise_records.pop(cls.Types.flags, None)
        if flags:
            flags = flags[0]

        local_name_complete = False
        local_name = advertise_records.pop(cls.Types.complete_local_name, None)
        if local_name:
            local_name_complete = True
        else:
            local_name = advertise_records.pop(cls.Types.short_local_name, None)
        if local_name:
            local_name = str("".join(chr(c) for c in local_name))

        manufacturer_data = advertise_records.pop(cls.Types.manufacturer_specific_data, None)
        if manufacturer_data:
            manufacturer_data = bytearray(manufacturer_data)

        service_data = advertise_records.pop(cls.Types.service_data, None)
        if service_data:
            service_data = bytearray(service_data)

        more_16bit_services = False
        uuid16_data = advertise_records.pop(cls.Types.service_16bit_uuid_more_available, None)
        if uuid16_data:
            more_16bit_services = True
        else:
            uuid16_data = advertise_records.pop(cls.Types.service_16bit_uuid_complete, None)

        service_uuid16s = []
        if uuid16_data:
            for i in range(0, len(uuid16_data), 2):
                uuid16 = (uuid16_data[i+1] << 8) | uuid16_data[i]
                service_uuid16s.append(uuid.Uuid16(uuid16))

        more_128bit_services = False
        uuid128_data = advertise_records.pop(cls.Types.service_128bit_uuid_more_available, None)
        if uuid128_data:
            more_128bit_services = True
        else:
            uuid128_data = advertise_records.pop(cls.Types.service_128bit_uuid_complete, None)

        service_uuid128s = []
        if uuid128_data:
            for i in range(0, len(uuid128_data), 16):
                uuid128 = uuid128_data[i:i+16][::-1]
                service_uuid128s.append(uuid.Uuid128(uuid128))
        record_string_keys = {k.name: v for k, v in advertise_records.items()}
        return AdvertisingData(flags=flags, local_name=local_name, local_name_complete=local_name_complete,
                               service_uuid16s=service_uuid16s, service_uuid128s=service_uuid128s,
                               has_more_uuid16_services=more_16bit_services, has_more_uuid128_services=more_128bit_services,
                               service_data=service_data, manufacturer_data=manufacturer_data, **record_string_keys)

    def __repr__(self):
        params = []
        if self.local_name:
            name_str = "Name: {}".format(self.local_name)
            if not self.local_name_complete:
                name_str += "(short)"
            params.append(name_str)
        if self.flags:
            params.append("Flags: {}".format(self.flags))
        if self.service_uuid16s:
            param_str = "16-bit Services: [{}]".format(", ".join(str(u) for u in self.service_uuid16s))
            if self.has_more_uuid16_services:
                param_str += "+ more"
            params.append(param_str)
        if self.service_uuid128s:
            param_str = "128-bit Services: [{}]".format(", ".join(str(u) for u in self.service_uuid128s))
            if self.has_more_uuid128_services:
                param_str += "+ more"
            params.append(param_str)
        if self.service_data:
            params.append("Service Data: {}".format(self.service_data))

        return "{}({})".format(self.__class__.__name__, ", ".join(params))


class Advertiser(object):
    ADVERTISE_FOREVER = 0

    def __init__(self, ble_device, client):
        """
        :type ble_device: blatann.device.BleDevice
        :type client: blatann.peer.Client
        """
        self.ble_device = ble_device
        self.advertising = False
        self._auto_restart = False
        self.client = client
        self.ble_device.ble_driver.event_subscribe(self._handle_adv_timeout, nrf_events.GapEvtTimeout)
        self.ble_device.ble_driver.event_subscribe(self._handle_disconnect, nrf_events.GapEvtDisconnected)
        self._on_advertising_timeout = EventSource("Advertising Timeout", logger)
        self._advertise_interval = 100
        self._timeout = self.ADVERTISE_FOREVER

    @property
    def on_advertising_timeout(self):
        return self._on_advertising_timeout

    def set_advertise_data(self, advertise_data=AdvertisingData(), scan_data=AdvertisingData()):
        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data.to_ble_adv_data(), scan_data.to_ble_adv_data())

    def set_default_advertise_params(self, advertise_interval, timeout_seconds):
        self._advertise_interval = advertise_interval
        self._timeout = timeout_seconds

    def start(self, adv_interval_ms=None, timeout_sec=None, auto_restart=False):
        """
        Starts advertising with the given parameters. If none given, will use the default

        :param adv_interval_ms: The interval at which to send out advertise packets, in milliseconds
        :param timeout_sec: The duration which to advertise for
        :param auto_restart: Flag indicating that advertising should restart automatically when the timeout expires, or
                             when the client disconnects
        :return: A waitable that will expire either when the timeout occurs, or a client connects.
                 Waitable Returns a peer.Client() object
        """
        if self.advertising:
            self._stop()
        if adv_interval_ms is None:
            adv_interval_ms = self._advertise_interval
        if timeout_sec is None:
            timeout_sec = self._timeout
        self._timeout = timeout_sec
        self._advertise_interval = adv_interval_ms

        params = nrf_types.BLEGapAdvParams(adv_interval_ms, timeout_sec)
        self._auto_restart = auto_restart
        logger.info("Starting advertising, params: {}, auto-restart: {}".format(params, auto_restart))
        self.ble_device.ble_driver.ble_gap_adv_start(params)
        self.advertising = True
        return ConnectionWaitable(self.ble_device, self.client)

    def _stop(self):
        if not self.advertising:
            return
        self.advertising = False
        try:
            self.ble_device.ble_driver.ble_gap_adv_stop()
        except Exception:
            pass

    def stop(self):
        self._auto_restart = False
        self._stop()

    def _handle_adv_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.advertising:
            self.advertising = False
            self._on_advertising_timeout.notify()
            if self._auto_restart:
                self.start()

    def _handle_disconnect(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if event.conn_handle == self.client.conn_handle or not self.client.connected and self._auto_restart:
            self.start()
