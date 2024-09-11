import threading
import unittest

from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags, AdvertisingPacketType
from blatann.gap.advertising import AdvertisingMode
from blatann.gap.scanning import MIN_SCAN_INTERVAL_MS, MIN_SCAN_WINDOW_MS, ScanParameters
from blatann.utils import Stopwatch
from blatann.uuid import Uuid16

from tests.integrated.base import BlatannTestCase, TestParams, long_running


class TestScanner(BlatannTestCase):
    def setUp(self) -> None:
        self.adv_interval_ms = 20
        self.adv_mac_addr = self.dev1.address
        self.adv_mode = AdvertisingMode.scanable_undirected
        self.scan_params = ScanParameters(MIN_SCAN_INTERVAL_MS, MIN_SCAN_WINDOW_MS, 4)
        self.flags = AdvertisingFlags.GENERAL_DISCOVERY_MODE | AdvertisingFlags.BR_EDR_NOT_SUPPORTED
        self.uuid16s = [Uuid16(0xABCD), Uuid16(0xDEF0)]
        self.default_adv_data = AdvertisingData(flags=self.flags, local_name="Blatann Test")
        self.default_adv_data_bytes = self.default_adv_data.to_bytes()
        self.default_scan_data = AdvertisingData(service_uuid16s=self.uuid16s)
        self.default_scan_data_bytes = self.default_scan_data.to_bytes()

    def tearDown(self) -> None:
        self.dev1.advertiser.stop()
        self.dev2.scanner.stop()

    def _get_packets_for_adv(self, results):
        all_packets = [p for p in results.all_scan_reports if p.peer_address == self.adv_mac_addr]
        adv_packets = [p for p in all_packets if p.packet_type == self.adv_mode]
        scan_response_packets = [p for p in all_packets if p.packet_type == AdvertisingPacketType.scan_response]
        return all_packets, adv_packets, scan_response_packets

    @TestParams([dict(duration=x) for x in [1, 2, 4, 10]], long_running_params=
                [dict(duration=x) for x in [60, 120]])
    def test_scan_duration(self, duration):
        acceptable_delta = 0.100
        on_timeout_event = threading.Event()
        self.scan_params.timeout_s = duration

        self.dev1.advertiser.start(self.adv_interval_ms, duration+2)

        def on_timeout(*args, **kwargs):
            on_timeout_event.set()

        with self.dev2.scanner.on_scan_timeout.register(on_timeout):
            with Stopwatch() as stopwatch:
                self.dev2.scanner.start_scan(self.scan_params)
                on_timeout_event.wait(duration + 2)

        self.assertTrue(on_timeout_event.is_set())
        self.assertFalse(self.dev2.scanner.is_scanning)

        actual_delta = abs(duration - stopwatch.elapsed)
        self.assertLessEqual(actual_delta, acceptable_delta)
        self.logger.info("Delta: {:.3f}".format(actual_delta))

    def test_scan_iterator(self):
        acceptable_delta = 0.100
        self.scan_params.timeout_s = 5

        self.dev1.advertiser.start(self.adv_interval_ms, self.scan_params.timeout_s+2)

        adv_address = self.dev1.address
        report_count_from_advertiser = 0
        with Stopwatch() as stopwatch:
            for report in self.dev2.scanner.start_scan(self.scan_params).scan_reports:
                if report.peer_address == adv_address:
                    report_count_from_advertiser += 1

        self.assertGreater(report_count_from_advertiser, 0)
        self.assertDeltaWithin(self.scan_params.timeout_s, stopwatch.elapsed, acceptable_delta)

    def test_non_active_scanning_no_scan_response_packets_received(self):
        self.dev1.advertiser.set_advertise_data(self.default_adv_data, self.default_scan_data)
        self.dev1.advertiser.start(advertise_mode=self.adv_mode)
        self.scan_params.active = False
        results = self.dev2.scanner.start_scan(self.scan_params).wait(10)

        # Get the list of all advertising packets from the advertiser
        all_packets, adv_packets, scan_response_packets = self._get_packets_for_adv(results)
        self.assertGreater(len(all_packets), 0)
        self.assertEqual(len(all_packets), len(adv_packets))
        self.assertEqual(0, len(scan_response_packets))

        for p in adv_packets:
            self.assertEqual(self.default_adv_data_bytes, p.raw_bytes)


if __name__ == '__main__':
    unittest.main()
