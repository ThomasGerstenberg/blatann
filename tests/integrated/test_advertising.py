import threading
import unittest

from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags
from blatann.gap.advertising import AdvertisingMode
from blatann.utils import Stopwatch
from blatann.event_type import event_subscriber

from tests.integrated.base import BlatannTestCase, TestParams, long_running


class TestAdvertising(BlatannTestCase):
    def setUp(self) -> None:
        self.adv_interval_ms = 250
        self.adv_duration = 2
        self.adv_mode = AdvertisingMode.non_connectable_undirected
        self.adv_data = AdvertisingData(flags=0x06, local_name="Blatann Test")

        self.dev1.advertiser.set_advertise_data(self.adv_data)
        self.dev1.advertiser.set_default_advertise_params(self.adv_interval_ms, self.adv_duration, self.adv_mode)

    def tearDown(self) -> None:
        self.dev1.advertiser.stop()

    @long_running
    @TestParams([dict(duration=x) for x in [1, 4, 8, 10, 15, 22, 30, 60]])
    def test_advertise_duration(self, duration):
        acceptable_delta = 0.100

        with Stopwatch() as stopwatch:
            w = self.dev1.advertiser.start(timeout_sec=duration)
            w.wait(duration + 2)

        self.assertFalse(self.dev1.advertiser.is_advertising)

        actual_delta = abs(duration - stopwatch.elapsed)
        self.assertLessEqual(actual_delta, acceptable_delta)

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


if __name__ == '__main__':
    unittest.main()
