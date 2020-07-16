import threading
import time
import unittest

from blatann.gap import SecurityStatus, SecurityLevel
from blatann.peer import Client, Peripheral, PairingRejectedReason

from blatann import BleDevice
from blatann.gap.advertising import AdvertisingMode
from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags, AdvertisingPacketType
from blatann.gap.scanning import MIN_SCAN_WINDOW_MS, MIN_SCAN_INTERVAL_MS, ScanParameters
from blatann.uuid import Uuid16
from blatann.utils import Stopwatch
from blatann.waitables import EventWaitable

from tests.integrated.base import BlatannTestCase, TestParams, long_running, EventCollector


class TestSecurity(BlatannTestCase):
    periph_dev: BleDevice
    central_dev: BleDevice
    peer_cen: Client
    peer_per: Peripheral

    @classmethod
    def setUpClass(cls) -> None:
        super(TestSecurity, cls).setUpClass()
        cls.periph_dev = cls.dev1
        cls.central_dev = cls.dev2
        cls.periph_dev.advertiser.set_advertise_data(AdvertisingData(flags=0x06, local_name="BlatannTest"))
        cls.periph_dev.advertiser.set_default_advertise_params(30, 0)
        cls.central_dev.scanner.set_default_scan_params(50, 50, 10, False)
        cls.central_dev.set_default_peripheral_connection_params(10, 10, 4000)
        cls.peer_cen = cls.periph_dev.client

    def tearDown(self) -> None:
        self._disconnect()

    def _connect(self):
        addr = self.periph_dev.address
        self.periph_dev.advertiser.start()
        self.peer_per = self.central_dev.connect(addr).wait(5)

    def _disconnect(self):
        if self.peer_per:
            self.peer_per.disconnect().wait(5)
            self.peer_per = None

    def test_nonbonded_devices_peripheral_rejects_by_default(self):
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()

        self.assertFalse(self.peer_per.is_previously_bonded)
        self.assertFalse(self.peer_cen.is_previously_bonded)

        # Initiate pairing to peripheral, peripheral should reject
        reject_waitable = EventWaitable(self.peer_cen.security.on_pairing_request_rejected)
        _, result = self.peer_per.security.pair().wait(10)
        _, rejection = reject_waitable.wait(1)

        self.assertEqual(SecurityStatus.pairing_not_supp, result.status)
        self.assertEqual(SecurityLevel.OPEN, result.security_level)
        self.assertEqual(PairingRejectedReason.non_bonded_central_request, rejection.reason)

        time.sleep(0.25)

        # Initiate pairing request to central, central should reject
        reject_waitable = EventWaitable(self.peer_per.security.on_pairing_request_rejected)
        _, result = self.peer_cen.security.pair().wait(10)
        _, rejection = reject_waitable.wait(1)

        self.assertEqual(SecurityStatus.pairing_not_supp, result.status)
        self.assertEqual(SecurityLevel.OPEN, result.security_level)
        self.assertEqual(PairingRejectedReason.non_bonded_peripheral_request, rejection.reason)

