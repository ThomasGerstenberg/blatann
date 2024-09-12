from __future__ import annotations

import time
import unittest

from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags, AdvertisingPacketType
from blatann.gap.advertising import AdvertisingMode
from blatann.gap.scanning import Scanner, ScanReport
from blatann.services.nordic_uart import NORDIC_UART_SERVICE_UUID
from blatann.uuid import Uuid16

from tests.integrated.base import BlatannTestCase, TestParams, long_running


class TestAdvertisingData(BlatannTestCase):
    def setUp(self) -> None:
        self.adv_interval_ms = 50
        self.adv_duration = 5
        self.adv_mode = AdvertisingMode.scanable_undirected
        self.flags = AdvertisingFlags.GENERAL_DISCOVERY_MODE | AdvertisingFlags.BR_EDR_NOT_SUPPORTED
        self._configure_adv()
        self._configure_scan()
        self.adv_mac_addr = self.dev1.address
        self.uuid16s = [Uuid16(0xABCD), Uuid16(0xDEF0)]
        self.uuid128 = NORDIC_UART_SERVICE_UUID
        self.default_adv_data = AdvertisingData(flags=self.flags, local_name="Blatann Test")
        self.default_adv_data_bytes = self.default_adv_data.to_bytes()
        self.default_scan_data = AdvertisingData(service_uuid16s=self.uuid16s)
        self.default_scan_data_bytes = self.default_scan_data.to_bytes()

    def _configure_adv(self, duration=10, adv_mode=AdvertisingMode.scanable_undirected):
        self.adv_mode = adv_mode
        self.dev1.advertiser.set_default_advertise_params(25, duration, self.adv_mode)

    def _configure_scan(self, duration=4, active_scan=True):
        self.dev2.scanner.set_default_scan_params(100, 100, duration, True)

    def _get_packets_for_adv(self, results):
        all_packets = [p for p in results.all_scan_reports if p.peer_address == self.adv_mac_addr]
        adv_packets = [p for p in all_packets if p.packet_type == self.adv_mode]
        scan_response_packets = [p for p in all_packets if p.packet_type == AdvertisingPacketType.scan_response]

        return all_packets, adv_packets, scan_response_packets

    def tearDown(self) -> None:
        self.dev1.advertiser.stop()
        self.dev2.scanner.stop()
        time.sleep(0.5)

    def test_advertising_no_scan_data(self):
        self.dev1.advertiser.set_advertise_data(self.default_adv_data)
        self.dev1.advertiser.start()
        results = self.dev2.scanner.start_scan(clear_scan_reports=True).wait(10)

        # Get the list of all advertising packets from the advertiser
        all_packets, adv_packets, scan_response_packets = self._get_packets_for_adv(results)
        self.assertGreater(len(all_packets), 0)
        self.assertGreater(len(adv_packets), 0)
        self.assertGreater(len(scan_response_packets), 0)
        self.assertEqual(len(scan_response_packets), len(all_packets) - len(adv_packets))

        # Check the contents of the received advertising packets to make sure they are the same
        for packet in adv_packets:
            if packet.packet_type == AdvertisingPacketType.scan_response:
                # Scan responses should be empty
                self.assertEqual(b"", packet.raw_bytes)
            else:
                self.assertEqual(self.default_adv_data_bytes, packet.raw_bytes)

    def test_advertising_scan_data(self):
        self.dev1.advertiser.set_advertise_data(self.default_adv_data, self.default_scan_data)
        self.dev1.advertiser.start()

        results = self.dev2.scanner.start_scan(clear_scan_reports=True).wait(10)

        # Get the list of all advertising packets from the advertiser
        all_packets, adv_packets, scan_response_packets = self._get_packets_for_adv(results)
        self.assertGreater(len(all_packets), 0)
        self.assertGreater(len(adv_packets), 0)
        self.assertGreater(len(scan_response_packets), 0)
        self.assertEqual(len(scan_response_packets), len(all_packets) - len(adv_packets))

        # Check the contents of the received advertising packets to make sure they are the same
        for packet in adv_packets:
            if packet.packet_type == AdvertisingPacketType.scan_response:
                self.assertEqual(self.default_scan_data_bytes, packet.raw_bytes)
            else:
                self.assertEqual(self.default_adv_data_bytes, packet.raw_bytes)

        # Check the combined report that all the fields are included
        combined_report = [p for p in results.advertising_peers_found if p.peer_address == self.adv_mac_addr]
        self.assertEqual(1, len(combined_report))
        adv_data = combined_report[0].advertise_data
        self.assertEqual(self.default_adv_data.flags, adv_data.flags)
        self.assertEqual(self.default_adv_data.local_name, adv_data.local_name)
        self.assertEqual(self.default_scan_data.service_uuid16s, adv_data.service_uuid16s)

    def test_non_connectable_undirected_no_scan_response_packets_received(self):
        self._configure_adv(adv_mode=AdvertisingMode.non_connectable_undirected)
        self.dev1.advertiser.set_advertise_data(self.default_adv_data, self.default_scan_data)
        self.dev1.advertiser.start()
        self.dev2.scanner.set_default_scan_params(100, 100, 5, active_scanning=True)
        results = self.dev2.scanner.start_scan().wait(10)

        # Get the list of all advertising packets from the advertiser
        all_packets, adv_packets, scan_response_packets = self._get_packets_for_adv(results)
        self.assertGreater(len(all_packets), 0)
        self.assertEqual(len(all_packets), len(adv_packets))
        self.assertEqual(0, len(scan_response_packets))

        for p in adv_packets:
            self.assertEqual(self.default_adv_data_bytes, p.raw_bytes)

    def test_dynamic_adv_data_update(self):
        self._configure_adv(duration=20, adv_mode=AdvertisingMode.non_connectable_undirected)
        self._configure_scan(10)
        service_data = [0xAB, 0xCD, 0x00]
        service_data_preamble = service_data[:-1]
        iterations = 10
        adv_data = AdvertisingData(service_data=service_data)
        self.dev1.advertiser.set_advertise_data(adv_data)
        self.dev1.advertiser.start()
        self.dev2.scanner.start_scan()

        for i in range(iterations):
            time.sleep(0.5)
            adv_data.service_data[-1] += 1
            self.dev1.advertiser.set_advertise_data(adv_data)

        time.sleep(0.5)
        self.dev2.scanner.stop()
        self.dev1.advertiser.stop()

        results = self.dev2.scanner.scan_report

        all_packets, adv_packets, scan_response_packets = self._get_packets_for_adv(results)
        self.assertGreater(len(all_packets), 0)
        self.assertEqual(len(all_packets), len(adv_packets))
        self.assertEqual(0, len(scan_response_packets))
        non_dupes = [p for p in adv_packets if not p.duplicate]

        self.assertEqual(iterations+1, len(non_dupes))
        for i, packet in enumerate(non_dupes):
            expected_service_data = bytes(service_data_preamble + [i])  # noqa: RUF005
            self.assertEqual(expected_service_data, packet.advertise_data.service_data)

    # TODO 04.20.20: Add more tests around data content (128-bit uuid, service data, mfg data, etc.)


if __name__ == '__main__':
    unittest.main()
