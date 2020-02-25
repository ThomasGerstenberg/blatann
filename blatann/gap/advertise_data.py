from typing import Iterable, List
import logging
from blatann.nrf import nrf_types
from blatann import uuid, exceptions


logger = logging.getLogger(__name__)


class AdvertisingFlags(object):
    LIMITED_DISCOVERY_MODE = 0x01
    GENERAL_DISCOVERY_MODE = 0x02
    BR_EDR_NOT_SUPPORTED = 0x04
    BR_EDR_CONTROLLER = 0x08
    BR_EDR_HOST = 0x10


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


class ScanReport(object):
    def __init__(self, adv_report):
        """
        :type adv_report: blatann.nrf.nrf_events.GapEvtAdvReport
        """
        self.peer_address = adv_report.peer_addr
        self._current_advertise_data = adv_report.adv_data.records.copy()
        self.advertise_data = AdvertisingData.from_ble_adv_records(self._current_advertise_data)
        self.rssi = adv_report.rssi
        self.duplicate = False

    @property
    def device_name(self):
        return self.advertise_data.local_name or str(self.peer_address)

    def update(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        if adv_report.peer_addr != self.peer_address:
            raise exceptions.InvalidOperationException("Peer address doesn't match")
        self._current_advertise_data.update(adv_report.adv_data.records)
        self.advertise_data = AdvertisingData.from_ble_adv_records(self._current_advertise_data.copy())
        self.rssi = max(self.rssi, adv_report.rssi)

    def __eq__(self, other):
        return self.peer_address == other.peer_address and self._current_advertise_data == other._current_advertise_data

    def __repr__(self):
        return "{}: {}dBm - {}".format(self.device_name, self.rssi, self.advertise_data)


class ScanReportCollection(object):
    """
    Collection of all the advertising data and scan reports found in a scanning session
    """
    def __init__(self):
        self._all_scans = []
        self._scans_by_peer_address = {}

    @property
    def advertising_peers_found(self) -> Iterable[ScanReport]:
        """
        Gets the list of scans which have been combined and condensed into a list where each entry is a unique peer

        :return: The list of scan reports, with each being a unique peer
        :rtype: list of ScanReport
        """
        return self._scans_by_peer_address.values()

    @property
    def all_scan_reports(self) -> List[ScanReport]:
        """
        Gets the list of all scanned advertising data found.

        :return: The list of all scan reports
        :rtype: list of ScanReport
        """
        return self._all_scans

    def clear(self):
        """
        Clears out all of the scan reports cached
        """
        self._all_scans = []
        self._scans_by_peer_address = {}

    def update(self, adv_report):
        """
        :type adv_report: nrf_events.GapEvtAdvReport
        """
        scan_entry = ScanReport(adv_report)
        if scan_entry in self._all_scans:
            scan_entry.duplicate = True
        self._all_scans.append(scan_entry)
        if adv_report.peer_addr in self._scans_by_peer_address.keys():
            self._scans_by_peer_address[adv_report.peer_addr].update(adv_report)
        else:
            self._scans_by_peer_address[adv_report.peer_addr] = scan_entry
        return self._scans_by_peer_address[adv_report.peer_addr]
