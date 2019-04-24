import logging
from enum import IntEnum
from blatann.nrf import nrf_events, nrf_types
from blatann import uuid, exceptions
from blatann.waitables.connection_waitable import ClientConnectionWaitable
from blatann.event_type import Event, EventSource


logger = logging.getLogger(__name__)


class AdvertisingFlags(object):
    LIMITED_DISCOVERY_MODE = 0x01
    GENERAL_DISCOVERY_MODE = 0x02
    BR_EDR_NOT_SUPPORTED = 0x04
    BR_EDR_CONTROLLER = 0x08
    BR_EDR_HOST = 0x10


AdvertisingMode = nrf_types.BLEGapAdvType


class AdvertisingData(object):
    """
    Class which represents data that can be advertised
    """
    MAX_ENCODED_LENGTH = 31  # Bluetooth-defined max length that the encoded data can be

    Types = nrf_types.BLEAdvData.Types  # Enum representing the different advertising data types

    def __init__(self, flags=None, local_name=None, local_name_complete=True,
                 service_uuid16s=None, service_uuid128s=None,
                 has_more_uuid16_services=False, has_more_uuid128_services=False,
                 service_data=None, manufacturer_data=None, **other_flags):
        self.flags = flags
        self.local_name = local_name
        self.local_name_complete = local_name_complete
        self.service_uuid16s = service_uuid16s or []
        self.service_uuid128s = service_uuid128s or []
        self.has_more_uuid16_services = has_more_uuid16_services
        self.has_more_uuid128_services = has_more_uuid128_services
        self.service_data = service_data
        self.manufacturer_data = manufacturer_data
        self.other_flags = {self.Types[k]: v for k, v in other_flags.items()}
        if not isinstance(self.service_uuid16s, (list, tuple)):
            self.service_uuid16s = [self.service_uuid16s]
        if not isinstance(self.service_uuid128s, (list, tuple)):
            self.service_uuid128s = [self.service_uuid128s]

    @property
    def service_uuids(self):
        """
        Gets all of the 16-bit and 128-bit service UUIDs specified in the advertising data

        :return: list of the service UUIDs present in the advertising data
        :rtype: list[uuid.Uuid]
        """
        return self.service_uuid16s + self.service_uuid128s

    def check_encoded_length(self):
        """
        Checks if the encoded length of this advertising data payload meets the maximum allowed
        length specified by the Bluetooth spec

        :return: a tuple of the encoded length and a bool result of whether or not it meets requirements
        :rtype: tuple[int, bool]
        """
        ble_adv_data = self.to_ble_adv_data()
        encoded_data = ble_adv_data.to_list()
        return len(encoded_data), len(encoded_data) <= self.MAX_ENCODED_LENGTH

    def to_ble_adv_data(self):
        """
        Converts the advertising data to a BLEAdvData object that can be used by the nRF Driver

        :return: the BLEAdvData object which represents this advertising data
        :rtype: nrf_types.BLEAdvData
        """
        records = self.other_flags.copy()
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
        """
        Converts a dictionary of AdvertisingData.Type: value keypairs into an object of this class

        :param advertise_records: a dictionary mapping the advertise data types to their corresponding values
        :type advertise_records: dict
        :return: the AdvertisingData from the records given
        :rtype: AdvertisingData
        """
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

        record_string_keys = {k.name: bytearray(v) for k, v in advertise_records.items()}
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
    # Constant used to indicate that the BLE device should advertise indefinitely, until
    # connected to or stopped manually
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
        self.client.on_disconnect.register(self._handle_disconnect)
        self._on_advertising_timeout = EventSource("Advertising Timeout", logger)
        self._advertise_interval = 100
        self._timeout = self.ADVERTISE_FOREVER
        self._advertise_mode = AdvertisingMode.connectable_undirected

    @property
    def on_advertising_timeout(self):
        """
        Event generated whenever advertising times out and finishes with no connections made
        Event args: None

        :return: an Event which can have handlers registered to and deregistered from
        :rtype: Event
        """
        return self._on_advertising_timeout

    def set_advertise_data(self, advertise_data=AdvertisingData(), scan_response=AdvertisingData()):
        """
        Sets the advertising and scan response data which will be broadcasted to peers during advertising

        Note: BLE Restricts advertise and scan response data to an encoded length of 31 bytes each.
        Use AdvertisingData.check_encoded_length() to determine if the

        :param advertise_data: The advertise data to use
        :type advertise_data: AdvertisingData
        :param scan_response: The scan response data to use
        :type scan_response: AdvertisingData
        """
        adv_len, adv_pass = advertise_data.check_encoded_length()
        scan_len, scan_pass = advertise_data.check_encoded_length()

        if not adv_pass:
            raise exceptions.InvalidOperationException("Encoded Advertising data length is too long ({} bytes). "
                                                       "Max: {} bytes".format(adv_len, advertise_data.MAX_ENCODED_LENGTH))

        if not scan_pass:
            raise exceptions.InvalidOperationException("Encoded Scan Response data length is too long ({} bytes). "
                                                       "Max: {} bytes".format(scan_len, advertise_data.MAX_ENCODED_LENGTH))

        self.ble_device.ble_driver.ble_gap_adv_data_set(advertise_data.to_ble_adv_data(), scan_response.to_ble_adv_data())

    def set_default_advertise_params(self, advertise_interval_ms, timeout_seconds, advertise_mode=AdvertisingMode.connectable_undirected):
        """
        Sets the default advertising parameters so they do not need to be specified on each start

        :param advertise_interval_ms: The advertising interval, in milliseconds
        :param timeout_seconds: How long to advertise for before timing out, in seconds
        :param advertise_mode: The mode the advertiser should use
        :type advertise_mode: AdvertisingMode
        """
        self._advertise_interval = advertise_interval_ms
        self._timeout = timeout_seconds
        self._advertise_mode = advertise_mode

    def start(self, adv_interval_ms=None, timeout_sec=None, auto_restart=None, advertise_mode=None):
        """
        Starts advertising with the given parameters. If none given, will use the default

        :param adv_interval_ms: The interval at which to send out advertise packets, in milliseconds
        :param timeout_sec: The duration which to advertise for
        :param auto_restart: Flag indicating that advertising should restart automatically when the timeout expires, or
                             when the client disconnects
        :param advertise_mode: The mode the advertiser should use
        :return: A waitable that will expire either when the timeout occurs, or a client connects.
                 Waitable Returns a peer.Client() object
        :rtype: ClientConnectionWaitable
        """
        if self.advertising:
            self._stop()
        if adv_interval_ms is None:
            adv_interval_ms = self._advertise_interval
        if timeout_sec is None:
            timeout_sec = self._timeout
        if advertise_mode is None:
            advertise_mode = self._advertise_mode
        if auto_restart is None:
            auto_restart = self._auto_restart

        self._timeout = timeout_sec
        self._advertise_interval = adv_interval_ms
        self._advertise_mode = advertise_mode
        self._auto_restart = auto_restart

        params = nrf_types.BLEGapAdvParams(adv_interval_ms, timeout_sec, advertise_mode)

        logger.info("Starting advertising, params: {}, auto-restart: {}".format(params, auto_restart))
        self.ble_device.ble_driver.ble_gap_adv_start(params)
        self.advertising = True
        return ClientConnectionWaitable(self.ble_device, self.client)

    def stop(self):
        """
        Stops advertising and disables the auto-restart functionality (if enabled)
        """
        self._auto_restart = False
        self._stop()

    def _stop(self):
        if not self.advertising:
            return
        self.advertising = False
        try:
            self.ble_device.ble_driver.ble_gap_adv_stop()
        except Exception:
            pass

    def _handle_adv_timeout(self, driver, event):
        """
        :type event: nrf_events.GapEvtTimeout
        """
        if event.src == nrf_events.BLEGapTimeoutSrc.advertising:
            self.advertising = False
            self._on_advertising_timeout.notify(self)
            if self._auto_restart:
                self.start()

    def _handle_disconnect(self, driver, event):
        """
        :type event: nrf_events.GapEvtDisconnected
        """
        if self._auto_restart:
            self.start()
