import threading
import unittest

from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags
from blatann.gap.advertising import AdvertisingMode
from blatann.gap.scanning import ScanReport, Scanner
from blatann.utils import Stopwatch
from blatann.event_type import event_subscriber

from tests.integrated.base import BlatannTestCase, TestParams, long_running


class TestAdvertising(BlatannTestCase):
    def setUp(self) -> None:
        self.adv_interval_ms = 250
        self.adv_duration = 5
        self.adv_mode = AdvertisingMode.non_connectable_undirected
        self.adv_data = AdvertisingData(flags=0x06, local_name="Blatann Test")

        self.dev1.advertiser.set_advertise_data(self.adv_data)
        self.dev1.advertiser.set_default_advertise_params(self.adv_interval_ms, self.adv_duration, self.adv_mode)

    def tearDown(self) -> None:
        self.dev1.advertiser.stop()
        self.dev2.scanner.stop()

    @long_running
    @TestParams([dict(duration=x) for x in [1, 4, 8, 10, 15, 22, 30, 60]])
    def test_advertise_duration(self, duration):
        acceptable_delta = 0.100
        scan_stopwatch = Stopwatch()
        dev1_addr = self.dev1.address

        def on_scan_report(scanner: Scanner, report: ScanReport):
            if report.peer_address != dev1_addr:
                return
            if scan_stopwatch.is_running:
                scan_stopwatch.mark()
            else:
                scan_stopwatch.start()

        self.dev2.scanner.set_default_scan_params(50, 50, duration+2)

        with event_subscriber(self.dev2.scanner.on_scan_received, on_scan_report):
            self.dev2.scanner.start_scan()
            with Stopwatch() as stopwatch:
                w = self.dev1.advertiser.start(timeout_sec=duration)
                w.wait(duration + 2)
            self.dev2.scanner.stop()

        self.assertFalse(self.dev1.advertiser.is_advertising)

        wait_delta = abs(duration - stopwatch.elapsed)
        self.assertLessEqual(wait_delta, acceptable_delta)

        scan_delta = abs(duration - scan_stopwatch.elapsed)
        self.assertLessEqual(scan_delta, acceptable_delta)

    @TestParams([dict(duration=x) for x in [1, 2, 4]])
    def test_advertise_duration_timeout_event(self, duration):
        acceptable_delta = 0.100
        on_timeout_event = threading.Event()

        def on_timeout(*args, **kwargs):
            on_timeout_event.set()

        with event_subscriber(self.dev1.advertiser.on_advertising_timeout, on_timeout):
            with Stopwatch() as stopwatch:
                self.dev1.advertiser.start(timeout_sec=duration)
                on_timeout_event.wait(duration + 2)

        self.assertTrue(on_timeout_event.is_set())
        self.assertFalse(self.dev1.advertiser.is_advertising)

        actual_delta = abs(duration - stopwatch.elapsed)
        self.assertLessEqual(actual_delta, acceptable_delta)

    @TestParams([dict(interval_ms=x) for x in [50, 100, 200]])
    def test_advertising_interval(self, interval_ms):
        self.dev2.scanner.set_default_scan_params(50, 50, self.adv_duration + 2)



if __name__ == '__main__':
    unittest.main()
