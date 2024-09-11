from __future__ import annotations

import queue
import time
import unittest

from blatann import BleDevice
from blatann.gap import AdvertisingData, ScanParameters
from blatann.gap.gap_types import ConnectionParameters
from blatann.nrf.nrf_types import BLEGapAddrTypes
from blatann.waitables import EventWaitable

from tests.integrated.base import BlatannTestCase, TestParams, long_running
from tests.integrated.helpers import CentralConn, PeriphConn, setup_connection


class TestGap(BlatannTestCase):
    periph_conn = PeriphConn()
    central_conn = CentralConn()
    periph: BleDevice
    central: BleDevice

    @classmethod
    def setUpClass(cls) -> None:
        super(TestGap, cls).setUpClass()
        cls.periph = cls.dev1
        cls.periph_conn.dev = cls.dev1
        cls.central = cls.dev2
        cls.central_conn.dev = cls.dev2

    def setUp(self) -> None:
        self.dev1.set_tx_power(0)
        self.dev2.set_tx_power(0)

    def tearDown(self) -> None:
        self.periph.set_privacy_settings(False)
        if self.central_conn.peer and self.central_conn.peer.connected:
            self.central_conn.peer.disconnect().wait(10)
            time.sleep(0.05)
            self.central_conn.peer = None
            self.periph_conn.peer = None

    def _run_conn_param_test(self, central_initiated, central_reject=False):
        default_conn_params = (10, 30, 4000)
        update_conn_params = (50, 70, 6000)
        # Setup connection with default conn parameters
        initial_conn_params = ConnectionParameters(*default_conn_params)
        self.periph.set_default_peripheral_connection_params(*update_conn_params)
        self.periph.client.set_connection_parameters(*update_conn_params)
        setup_connection(self.periph_conn, self.central_conn, initial_conn_params, discover_services=False)

        # Verify connection was successful
        self.assertTrue(self.periph_conn.peer.connected)
        self.assertTrue(self.central_conn.peer.connected)

        if central_reject:
            self.central_conn.peer.reject_conn_param_requests()
        else:
            self.central_conn.peer.accept_all_conn_param_requests()

        # Determine conn param update initiator/receiver
        initiator = self.central_conn.peer if central_initiated else self.periph_conn.peer
        receiver = self.periph_conn.peer if central_initiated else self.central_conn.peer

        # Create a waitable for the conn param update on the receiver side
        receiver_waitable = EventWaitable(receiver.on_connection_parameters_updated)
        # Initiate conn param update procedure, wait for result
        _, initiator_result = initiator.set_connection_parameters(*update_conn_params).wait(3)
        # Get event on receiver side

        # If central rejection is configured, there shouldn't be an event received on the receiver (central)
        if not central_reject:
            _, receiver_result = receiver_waitable.wait(3)
            receiver_params = receiver_result.active_connection_params
        else:
            _, receiver_result = receiver_waitable.wait(3, exception_on_timeout=False)
            self.assertIsNone(receiver_result)
            receiver_params = receiver.active_connection_params

        initiator_params = initiator_result.active_connection_params

        # Make sure everything matches
        self.assertEqual(receiver_params, initiator_params)
        self.assertEqual(receiver_params, self.central_conn.peer.active_connection_params)
        self.assertEqual(receiver_params, self.periph_conn.peer.active_connection_params)

    def test_connection_parameters_peripheral_initiated_central_accepts(self):
        self._run_conn_param_test(central_initiated=False)

    def test_connection_parameters_peripheral_initiated_central_rejects(self):
        self._run_conn_param_test(central_initiated=False, central_reject=True)

    def test_connection_parameters_central_initiated(self):
        self._run_conn_param_test(central_initiated=True)

    def test_preferred_mtu_size_set_before_connect(self):
        expected_mtu_size = 128
        self.periph_conn.dev.client.preferred_mtu_size = 247  # Set to max

        # Connect and set the preferred MTU size of the central device
        setup_connection(self.periph_conn, self.central_conn, discover_services=False, preferred_mtu=expected_mtu_size)

        # At this point the central device's preferred MTU size should be set
        self.assertEqual(self.central_conn.peer.preferred_mtu_size, expected_mtu_size)
        # Initiate MTU exchange from the peripheral
        self.periph_conn.peer.exchange_mtu().wait()

        self.assertEqual(self.periph_conn.peer.mtu_size, expected_mtu_size)
        self.assertEqual(self.central_conn.peer.mtu_size, expected_mtu_size)

    def test_preferred_default_mtu_size_set_before_connect(self):
        expected_mtu_size = 200
        self.periph_conn.dev.client.preferred_mtu_size = 247  # Set to max

        # Set the default and don't specify in the setup. Value should be used
        self.central_conn.dev.set_default_peripheral_preferred_settings(expected_mtu_size)
        setup_connection(self.periph_conn, self.central_conn, discover_services=False)

        # At this point the central device's preferred MTU size should be set
        self.assertEqual(self.central_conn.peer.preferred_mtu_size, expected_mtu_size)
        # Initiate MTU exchange from the peripheral
        self.periph_conn.peer.exchange_mtu().wait()

        self.assertEqual(self.periph_conn.peer.mtu_size, expected_mtu_size)
        self.assertEqual(self.central_conn.peer.mtu_size, expected_mtu_size)

    def test_get_rssi(self):
        setup_connection(self.periph_conn, self.central_conn, discover_services=False)

        self.assertIsNone(self.periph_conn.peer.rssi)
        self.assertIsNone(self.central_conn.peer.rssi)

        self.periph_conn.peer.start_rssi_reporting()
        self.central_conn.peer.start_rssi_reporting()

        # Sleep some time for a connection interval to pass and get the RSSI value
        time.sleep(0.1)

        periph_rssi = self.periph_conn.peer.rssi
        central_rssi = self.central_conn.peer.rssi

        self.assertIsNotNone(periph_rssi)
        self.assertIsNotNone(central_rssi)
        self.assertLess(periph_rssi, 0)
        self.assertLess(central_rssi, 0)

        rssi_delta = abs(periph_rssi - central_rssi)
        self.assertLess(rssi_delta, 3)

        # Set the tx power of the devices to very low, verify the value drops
        self.periph_conn.dev.set_tx_power(-20)
        self.central_conn.dev.set_tx_power(-20)

        # Wait for another connection interval at the lower power
        time.sleep(0.1)

        new_periph_rssi = self.periph_conn.peer.rssi
        new_central_rssi = self.central_conn.peer.rssi

        self.assertIsNotNone(periph_rssi)
        self.assertIsNotNone(central_rssi)
        self.assertLess(new_periph_rssi, periph_rssi)
        self.assertLess(new_central_rssi, central_rssi)

    def test_rssi_update_event(self):
        setup_connection(self.periph_conn, self.central_conn, discover_services=False)

        # Setup event to trigger after 5 dbm change and delta is held for 3 conn intervals
        _, initial_rssi = self.periph_conn.peer.start_rssi_reporting(threshold_dbm=5, skip_count=3).wait(5)

        # Create a waitable to wait for a new RSSI value to come in after decreasing the centrals Tx power
        waitable = EventWaitable(self.periph_conn.peer.on_rssi_changed)
        self.central_conn.dev.set_tx_power(-20)
        _, low_rssi = waitable.wait(10)

        self.assertLess(low_rssi, initial_rssi)

        # Increase Tx Power. Ensure rssi is greater than previous but less than initial
        waitable = EventWaitable(self.periph_conn.peer.on_rssi_changed)
        self.central_conn.dev.set_tx_power(-8)
        _, medium_rssi = waitable.wait(10)

        self.assertGreater(medium_rssi, low_rssi)
        self.assertLess(medium_rssi, initial_rssi)

    def _run_privacy_test(self, resolvable_address):
        name = "BLATANN TEST"
        expected_addr_type = (BLEGapAddrTypes.random_private_resolvable
                              if resolvable_address else
                              BLEGapAddrTypes.random_private_non_resolvable)

        advertise_data = AdvertisingData(flags=0x06, local_name=name)
        self.periph.set_privacy_settings(enabled=True, resolvable_address=resolvable_address, update_rate_seconds=5)
        self.periph.advertiser.set_advertise_data(advertise_data)
        self.periph.advertiser.start(auto_restart=False)

        # Scan for devices, then filter out ones by the expected name.
        # With privacy update rate 5s and timeout_s 10, should expect at least 2 unique private resolvable peer addresses
        scan_params = ScanParameters(interval_ms=75, window_ms=50, timeout_s=10, active=False)
        scan_reports = self.central.scanner.start_scan(scan_params).wait()
        self.periph.advertiser.stop()

        found_addresses = []
        for report in scan_reports.advertising_peers_found:
            if report.device_name == name:
                found_addresses.append(report.peer_address)

        self.assertGreater(len(found_addresses), 1)
        for addr in found_addresses:
            self.assertEqual(addr.addr_type, expected_addr_type)
        # Ensure they're unique addresses
        self.assertEqual(len(found_addresses), len(set([str(s) for s in found_addresses])))

    def test_advertising_private_resolvable_address(self):
        self._run_privacy_test(resolvable_address=True)

    def test_advertising_private_nonresolvable_address(self):
        self._run_privacy_test(resolvable_address=False)
