import time
from typing import Iterable, List, Dict, Union, Optional, Tuple
import logging

from blatann.gap.gap_types import PeerAddress
from blatann.nrf import nrf_types, nrf_events
from blatann import uuid, exceptions


logger = logging.getLogger(__name__)


class AdvertisingFlags(object):
    LIMITED_DISCOVERY_MODE = 0x01
    GENERAL_DISCOVERY_MODE = 0x02
    BR_EDR_NOT_SUPPORTED = 0x04
    BR_EDR_CONTROLLER = 0x08
    BR_EDR_HOST = 0x10


AdvertisingPacketType = nrf_types.BLEGapAdvType


class AdvertisingData(object):
    """
    Class which represents data that can be advertised
    """
    MAX_ENCODED_LENGTH = 31  # Bluetooth-defined max length that the encoded data can be

    Types = nrf_types.BLEAdvData.Types  # Enum representing the different advertising data types

    def __init__(self, flags=None, local_name=None, local_name_complete=True,
                 service_uuid16s=None, service_uuid128s=None,
                 has_more_uuid16_services=False, has_more_uuid128_services=False,
                 service_data=None, manufacturer_data=None, **other_entries):
        self.entries = {self.Types[k]: v for k, v in other_entries.items()}
        if flags is not None:
            self.entries[self.Types.flags] = flags
        if service_data:
            self.entries[self.Types.service_data] = service_data
        if manufacturer_data:
            self.entries[self.Types.manufacturer_specific_data] = manufacturer_data

        self.local_name = local_name
        self.local_name_complete = local_name_complete
        self.service_uuid16s = service_uuid16s or []
        self.service_uuid128s = service_uuid128s or []
        self.has_more_uuid16_services = has_more_uuid16_services
        self.has_more_uuid128_services = has_more_uuid128_services
        if not isinstance(self.service_uuid16s, (list, tuple)):
            self.service_uuid16s = [self.service_uuid16s]
        if not isinstance(self.service_uuid128s, (list, tuple)):
            self.service_uuid128s = [self.service_uuid128s]

    def _get(self, t, default=None):
        return self.entries.get(t, default)

    def _set(self, t, value):
        self.entries[t] = value

    def _del(self, t):
        if t in self.entries:
            del self.entries[t]

    @property
    def flags(self) -> Optional[int]:
        """
        The advertising flags in the payload, if set

        :getter: Gets the advertising flags in the payload, or None if not set
        :setter: Sets the advertising flags in the payload
        :delete: Removes the advertising flags from the payload
        """
        return self._get(self.Types.flags)

    @flags.setter
    def flags(self, value: int):
        self._set(self.Types.flags, value)

    @flags.deleter
    def flags(self):
        self._del(self.Types.flags)

    @property
    def service_data(self) -> Union[bytes, List[int], None]:
        """
        The service data in the payload, if set

        :getter: Gets the service data in the payload, or None if not set
        :setter: Sets the service data for the payload
        :delete: Removes the service data from the payload
        """
        return self._get(self.Types.service_data, None)

    @service_data.setter
    def service_data(self, value: Union[bytes, List[int]]):
        self._set(self.Types.service_data, value)

    @service_data.deleter
    def service_data(self):
        self._del(self.Types.service_data)

    @property
    def manufacturer_data(self) -> Union[bytes, List[int], None]:
        """
        The manufacturer data in the payload, if set

        :getter: Gets the manufacturer data in the payload, or None if not set
        :setter: Sets the manufacturer data for the payload
        :delete: Removes the manufacturer data from the payload
        """
        return self._get(self.Types.manufacturer_specific_data, None)

    @manufacturer_data.setter
    def manufacturer_data(self, value: Union[bytes, List[int]]):
        self._set(self.Types.manufacturer_specific_data, value)

    @manufacturer_data.deleter
    def manufacturer_data(self):
        self._del(self.Types.manufacturer_specific_data)

    @property
    def service_uuids(self) -> List[uuid.Uuid]:
        """
        Gets all of the 16-bit and 128-bit service UUIDs specified in the advertising data
        """
        return self.service_uuid16s + self.service_uuid128s

    def check_encoded_length(self) -> Tuple[int, bool]:
        """
        Checks if the encoded length of this advertising data payload meets the maximum allowed
        length specified by the Bluetooth specification

        :return: a tuple of the encoded length and a bool result of whether or not it meets requirements
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
        records = self.entries.copy()

        if self.service_uuid128s:
            t = self.Types.service_128bit_uuid_more_available if self.has_more_uuid128_services else self.Types.service_128bit_uuid_complete
            data = [b for u in self.service_uuid128s for b in u.uuid[::-1]]
            records[t] = data
        if self.service_uuid16s:
            t = self.Types.service_16bit_uuid_more_available if self.has_more_uuid16_services else self.Types.service_16bit_uuid_complete
            data = [b for u in self.service_uuid16s for b in [u.uuid & 0xFF, u.uuid >> 8 & 0xFF]]
            records[t] = data
        if self.local_name:
            t = self.Types.complete_local_name if self.local_name_complete else self.Types.short_local_name
            records[t] = self.local_name

        for k, v in records.items():
            if hasattr(v, "as_bytes"):
                records[k] = v.as_bytes()
            elif isinstance(v, int):
                records[k] = [v]
        record_string_keys = {k.name: v for k, v in records.items()}
        return nrf_types.BLEAdvData(**record_string_keys)

    def to_bytes(self) -> bytes:
        """
        Converts the advertising data to the encoded bytes that will be advertised over the air.
        Advertising payloads are encoded in a length-type-value format

        :return: The encoded payload
        """
        adv_data = self.to_ble_adv_data()
        adv_data.to_list()
        return adv_data.raw_bytes

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
            if len(uuid16_data) % 2 != 0:
                logger.debug(f"Got odd number of bytes for UUID16 Data: {uuid16_data}. Stripping last byte")
                uuid16_data = uuid16_data[:-1]
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
            leftover_bytes = len(uuid128_data) % 16
            if leftover_bytes != 0:
                logger.debug(f"Got invalid multiple for UUID128 data: {uuid128_data}. "
                             f"Stripping off {leftover_bytes} bytes")
                uuid128_data = uuid128_data[:-leftover_bytes]
            for i in range(0, len(uuid128_data), 16):
                uuid128 = uuid128_data[i:i+16][::-1]
                service_uuid128s.append(uuid.Uuid128(uuid128))

        record_string_keys = {k.name: bytes(v) for k, v in advertise_records.items()}
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

    def __eq__(self, other):
        if not isinstance(other, AdvertisingData):
            return False
        return (self.entries == other.entries and
                self.local_name == other.local_name and
                self.service_uuid16s == other.service_uuid16s and
                self.service_uuid128s == other.service_uuid128s)


class ScanReport(object):
    """
    Represents a payload and associated metadata that's received during scanning
    """
    def __init__(self, adv_report, resolved_address: Optional[PeerAddress]):
        """
        :type adv_report: blatann.nrf.nrf_events.GapEvtAdvReport
        """
        self.timestamp = time.time()
        self.peer_address = adv_report.peer_addr
        self.packet_type: AdvertisingPacketType = adv_report.adv_type
        self._current_advertise_data = adv_report.adv_data.records.copy()
        self.advertise_data = AdvertisingData.from_ble_adv_records(self._current_advertise_data)
        self.rssi = adv_report.rssi
        self.duplicate = False
        self.raw_bytes = adv_report.adv_data.raw_bytes
        self._resolved_address = resolved_address

    @property
    def device_name(self) -> str:
        """
        **Read Only**

        The name of the device, pulled from the advertising data (if advertised) or uses the Peer's MAC Address if not set
        """
        return self.advertise_data.local_name or str(self.peer_address)

    @property
    def is_bonded_device(self) -> bool:
        """
        If the scan report is from a BLE device that the local device has a matching bond database entry
        """
        return self._resolved_address is not None

    @property
    def resolved_address(self) -> Optional[PeerAddress]:
        """
        If the scan report is from a bonded device, this is the resolved public/static/random BLE address.
        This may be the same as peer_addr if the device is not advertising as a private resolvable address
        """
        return self._resolved_address

    def update(self, adv_report):
        """
        Used internally to merge a new advertising payload that was received into the current scan report

        :type adv_report: nrf_events.GapEvtAdvReport
        """
        if adv_report.peer_addr != self.peer_address:
            raise exceptions.InvalidOperationException("Peer address doesn't match")

        self._current_advertise_data.update(adv_report.adv_data.records.copy())
        self.advertise_data = AdvertisingData.from_ble_adv_records(self._current_advertise_data.copy())
        self.rssi = max(self.rssi, adv_report.rssi)
        self.raw_bytes = b""

    def __eq__(self, other):
        if not isinstance(other, ScanReport):
            return False
        return self.peer_address == other.peer_address and self.advertise_data == other.advertise_data

    def __repr__(self):
        return "{}: {}dBm - {}".format(self.device_name, self.rssi, self.advertise_data)


class ScanReportCollection(object):
    """
    Collection of all the advertising data and scan reports found in a scanning session
    """
    def __init__(self):
        self._all_scans: List[ScanReport] = []
        self._scans_by_peer_address: Dict[PeerAddress, ScanReport] = {}

    @property
    def advertising_peers_found(self) -> Iterable[ScanReport]:
        """
        Gets the list of scans which have been combined and condensed into a list where each entry is a unique peer.
        The scan reports in this list represent aggregated data of each advertising packet received by the advertising
        device, such that later advertising packets will update/overwrite packet attributes received
        from earlier packets, if the data has been modified.

        :return: The list of scan reports, with each being a unique peer
        """
        return self._scans_by_peer_address.values()

    @property
    def all_scan_reports(self) -> Iterable[ScanReport]:
        """
        Gets the list of all of the individual advertising packets received.

        :return: The list of all scan reports
        """
        return self._all_scans[:]

    def get_report_for_peer(self, peer_addr) -> Optional[ScanReport]:
        """
        Gets the combined/aggregated scan report for a given Peer's address.
        If the peer's scan report isn't found, returns None

        :param peer_addr: The peer's address to search for
        :return: The associated scan report, if found
        """
        return self._scans_by_peer_address.get(peer_addr)

    def clear(self):
        """
        Clears out all of the scan reports cached
        """
        self._all_scans = []
        self._scans_by_peer_address = {}

    def update(self, adv_report: nrf_events.GapEvtAdvReport, resolved_peer_addr: PeerAddress = None) -> ScanReport:
        """
        Used internally to update the collection with a new advertising report received

        :return: The Scan Report created from the advertising report
        """
        scan_entry = ScanReport(adv_report, resolved_peer_addr)
        if scan_entry in self._all_scans:
            scan_entry.duplicate = True

        self._all_scans.append(scan_entry)

        addr_key = resolved_peer_addr if resolved_peer_addr is not None else adv_report.peer_addr

        if addr_key in self._scans_by_peer_address.keys():
            self._scans_by_peer_address[addr_key].update(adv_report)
        elif addr_key.addr_type != nrf_types.BLEGapAddrTypes.anonymous:
            self._scans_by_peer_address[addr_key] = ScanReport(adv_report, resolved_peer_addr)
        return scan_entry
