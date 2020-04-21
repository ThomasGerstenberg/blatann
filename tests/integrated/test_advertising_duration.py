import threading
import unittest

from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags
from blatann.gap.advertising import AdvertisingMode
from blatann.gap.scanning import ScanReport, Scanner
from blatann.utils import Stopwatch

from tests.integrated.base import BlatannTestCase, TestParams, long_running


class TestAdvertisingDuration(BlatannTestCase):
    def setUp(self) -> None:
        self.adv_interval_ms = 50
        self.adv_duration = 5
        self.adv_mode = AdvertisingMode.non_connectable_undirected
        self.adv_data = AdvertisingData(flags=0x06, local_name="Blatann Test")

        self.dev1.advertiser.set_advertise_data(self.adv_data)
        self.dev1.advertiser.set_default_advertise_params(self.adv_interval_ms, self.adv_duration, self.adv_mode)

    def tearDown(self) -> None:
        self.dev1.advertiser.stop()
        self.dev2.scanner.stop()

    @long_running
    @TestParams([dict(duration=x) for x in [1, 4, 8, 10]])
    def test_advertise_duration(self, duration):
        acceptable_delta = 0.100
        acceptable_delta_scan = 1.000
        scan_stopwatch = Stopwatch()
        dev1_addr = self.dev1.address

        def on_scan_report(scanner: Scanner, report: ScanReport):
            if report.peer_address != dev1_addr:
                return
            if scan_stopwatch.is_running:
                scan_stopwatch.mark()
            else:
                scan_stopwatch.start()

        self.dev2.scanner.set_default_scan_params(100, 100, duration+2, False)

        with self.dev2.scanner.on_scan_received.register(on_scan_report):
            self.dev2.scanner.start_scan()
            with Stopwatch() as wait_stopwatch:
                self.dev1.advertiser.start(timeout_sec=duration, auto_restart=False).wait(duration + 2)

        self.assertFalse(wait_stopwatch.is_running)
        self.assertFalse(self.dev1.advertiser.is_advertising)

        wait_delta = abs(duration - wait_stopwatch.elapsed)
        self.assertLessEqual(wait_delta, acceptable_delta)

        scan_delta = abs(duration - scan_stopwatch.elapsed)
        self.assertLessEqual(scan_delta, acceptable_delta_scan)

        self.logger.info("Wait Delta: {:.3f}, Scan Delta: {:.3f}".format(wait_delta, scan_delta))

    @TestParams([dict(duration=x) for x in [1, 2, 4]])
    def test_advertise_duration_timeout_event(self, duration):
        acceptable_delta = 0.100
        on_timeout_event = threading.Event()

        def on_timeout(*args, **kwargs):
            on_timeout_event.set()

        with self.dev1.advertiser.on_advertising_timeout.register(on_timeout):
            with Stopwatch() as stopwatch:
                self.dev1.advertiser.start(timeout_sec=duration, auto_restart=False)
                on_timeout_event.wait(duration + 2)

        self.assertTrue(on_timeout_event.is_set())
        self.assertFalse(self.dev1.advertiser.is_advertising)

        actual_delta = abs(duration - stopwatch.elapsed)
        self.assertLessEqual(actual_delta, acceptable_delta)
        self.logger.info("Delta: {:.3f}".format(actual_delta))

    def test_advertise_auto_restart(self):
        # Scan for longer than the advertising duration,
        # but with auto-restart it should advertise for the full scan duration
        scan_duration = 10
        advertise_duration = 2
        acceptable_delta = 0.500
        dev1_addr = self.dev1.address

        self.dev2.scanner.set_default_scan_params(100, 100, scan_duration, False)

        w = self.dev2.scanner.start_scan()
        self.dev1.advertiser.start(timeout_sec=advertise_duration, auto_restart=True)
        w.wait()

        self.dev1.advertiser.stop()
        self.dev2.scanner.stop()

        report_timestamps = [r.timestamp for r in self.dev2.scanner.scan_report.all_scan_reports
                             if r.peer_address == dev1_addr]
        self.assertGreater(len(report_timestamps), 0)

        report_seen_duration = report_timestamps[-1] - report_timestamps[0]

        delta = abs(report_seen_duration - scan_duration)
        self.assertLessEqual(delta, acceptable_delta)
        self.logger.info("Delta: {:.3f}".format(delta))


if __name__ == '__main__':
    unittest.main()
