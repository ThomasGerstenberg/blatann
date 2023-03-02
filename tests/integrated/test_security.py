import queue
import threading
import time
import unittest
from typing import Union

from blatann.event_args import PasskeyDisplayEventArgs, PasskeyEntryEventArgs, SecurityProcess

from blatann.gap import SecurityStatus, SecurityLevel, IoCapabilities, PairingPolicy, SecurityParameters
from blatann.peer import Client, Peripheral, PairingRejectedReason, DEFAULT_SECURITY_PARAMS

from blatann import BleDevice
from blatann.gap.advertise_data import AdvertisingData, AdvertisingFlags, AdvertisingPacketType
from blatann.waitables import EventWaitable

from tests.integrated.base import BlatannTestCase, TestParams, long_running


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
        cls.periph_dev.advertiser.set_default_advertise_params(100, 0)
        cls.central_dev.scanner.set_default_scan_params(125, 75, 10, False)
        cls.central_dev.set_default_peripheral_connection_params(50, 100, 4000)
        cls.peer_cen = cls.periph_dev.client

    def setUp(self) -> None:
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()

        self.assertFalse(self.peer_per.is_previously_bonded)
        self.assertFalse(self.peer_cen.is_previously_bonded)

    def tearDown(self) -> None:
        self._disconnect()
        time.sleep(0.5)

    def _connect(self, scan_for_address=False, should_be_bonded=False):
        event = threading.Event()
        def on_connect(*args):
            event.set()

        self.periph_dev.advertiser.start()
        if scan_for_address:
            addr = self._scan_for_address(should_be_bonded)
        else:
            time.sleep(0.5)
            addr = self.periph_dev.address

        with self.peer_cen.on_connect.register(on_connect):
            self.peer_per = self.central_dev.connect(addr).wait(5)
            event.wait(5)
        self.assertTrue(event.is_set())

    def _scan_for_address(self, should_be_bonded):
        for scan_report in self.central_dev.scanner.start_scan(clear_scan_reports=True).scan_reports:
            if scan_report.device_name == "BlatannTest":
                if should_be_bonded:
                    self.assertTrue(scan_report.is_bonded_device)
                return scan_report.peer_address
        return None

    def _disconnect(self, clear_peer=True):
        event = threading.Event()
        def on_disconnect(*args):
            event.set()

        if self.peer_per:
            with self.peer_cen.on_disconnect.register(on_disconnect):
                self.peer_per.disconnect().wait(5)
                event.wait(15)
                time.sleep(0.5)
            if clear_peer:
                self.peer_per = None

    def _reconnect(self, should_be_bonded, scan_for_address=False):
        time.sleep(0.5)
        self._disconnect(clear_peer=False)
        self._connect(scan_for_address, should_be_bonded)
        if should_be_bonded:
            self.assertTrue(self.peer_per.is_previously_bonded)
            self.assertTrue(self.peer_cen.is_previously_bonded)
        else:
            self.assertFalse(self.peer_per.is_previously_bonded)
            self.assertFalse(self.peer_cen.is_previously_bonded)

    def _set_security_parameters(self, passcode_pairing: bool,
                                 io_capabilities: IoCapabilities,
                                 bond: bool,
                                 reject_pairing_requests: Union[bool, PairingPolicy] = False,
                                 lesc_pairing: bool = False):
        security_params1 = SecurityParameters(passcode_pairing, io_capabilities, bond, False, reject_pairing_requests, lesc_pairing)
        security_params2 = SecurityParameters(passcode_pairing, io_capabilities, bond, False, reject_pairing_requests, lesc_pairing)
        self.peer_per.security.security_params = security_params1
        self.peer_cen.security.security_params = security_params2

    def _perform_pairing(self, initiate_using_central: bool,
                         passcode_pairing: bool,
                         io_capabilities: IoCapabilities,
                         bond: bool,
                         reject_pairing_requests: Union[bool, PairingPolicy] = False,
                         lesc_pairing: bool = False,
                         peer_io_caps: IoCapabilities = None):
        if self.peer_per.is_previously_bonded:
            expected_process = SecurityProcess.ENCRYPTION
        elif bond:
            expected_process = SecurityProcess.BONDING
        else:
            expected_process = SecurityProcess.PAIRING

        if passcode_pairing:
            if lesc_pairing:
                expected_level = SecurityLevel.LESC_MITM
            else:
                expected_level = SecurityLevel.MITM
        else:
            expected_level = SecurityLevel.JUST_WORKS

        self._set_security_parameters(passcode_pairing, io_capabilities, bond, reject_pairing_requests, lesc_pairing)
        if peer_io_caps is not None:
            self.peer_per.security.security_params.io_capabilities = peer_io_caps

        initiator = self.peer_per if initiate_using_central else self.peer_cen

        _, result = initiator.security.pair().wait(10)

        time.sleep(0.5)
        self.assertEqual(SecurityStatus.success, result.status)
        self.assertEqual(expected_process, result.security_process)
        self.assertEqual(expected_level, self.peer_per.security.security_level)
        self.assertEqual(expected_level, self.peer_cen.security.security_level)

    def test_nonbonded_devices_rejects_by_default(self):
        self.peer_per.security.security_params = DEFAULT_SECURITY_PARAMS
        self.peer_cen.security.security_params = DEFAULT_SECURITY_PARAMS

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

    def test_bonding_just_works_lesc_happy_path(self):
        initiate_using_central = True
        use_passcode = False
        io_caps = IoCapabilities.NONE
        bond = True
        reject = False
        lesc = True

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        # Reconnect and pair again. Should be able to re-establish security using previous encryption
        self._reconnect(bond)

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

    def test_bonding_just_works_legacy_happy_path(self):
        initiate_using_central = True
        use_passcode = False
        io_caps = IoCapabilities.NONE
        bond = True
        reject = False
        lesc = False

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        # Reconnect and pair again. Should be able to re-establish security using previous encryption
        self._reconnect(bond)

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

    def test_bonding_passcode_match_lesc_happy_path(self):
        initiate_using_central = True
        use_passcode = True
        io_caps = IoCapabilities.DISPLAY_YESNO
        bond = True
        reject = False
        lesc = True

        per_passcode_q = queue.Queue()
        cen_passcode_q = queue.Queue()
        per_event = threading.Event()
        cen_event = threading.Event()

        def on_display_request(peer, event_args: PasskeyDisplayEventArgs):
            if peer == self.peer_cen:
                our_q, their_q, event = cen_passcode_q, per_passcode_q, cen_event
            else:
                our_q, their_q, event = per_passcode_q, cen_passcode_q, per_event

            event.set()
            their_q.put(event_args.passkey)
            passkey = our_q.get()

            if passkey != event_args.passkey:
                self.logger.error(f"Passkeys did not match! {passkey}/{event_args.passkey}")
            event_args.match_confirm(passkey == event_args.passkey)

        with self.peer_cen.security.on_passkey_display_required.register(on_display_request):
            with self.peer_per.security.on_passkey_display_required.register(on_display_request):
                self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        self.assertTrue(per_event.is_set())
        self.assertTrue(cen_event.is_set())

        # Reconnect and pair again. Should be able to re-establish security using previous encryption
        self._reconnect(bond)
        per_event.clear()
        cen_event.clear()

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        self.assertFalse(per_event.is_set())
        self.assertFalse(cen_event.is_set())

    def test_bonding_passkey_entry_lesc_happy_path(self):
        initiate_using_central = True
        use_passcode = True
        io_caps = IoCapabilities.DISPLAY_ONLY
        bond = True
        reject = False
        lesc = True
        per_io_caps = IoCapabilities.KEYBOARD_DISPLAY

        passcode_q = queue.Queue()
        display_event = threading.Event()
        entry_event = threading.Event()

        def on_display_request(peer, event_args: PasskeyDisplayEventArgs):
            self.logger.info("Got display request")
            passcode_q.put(event_args.passkey)
            display_event.set()

        def on_entry_request(peer, event_args: PasskeyEntryEventArgs):
            self.logger.info("Got entry request")
            passkey = passcode_q.get()
            entry_event.set()
            event_args.resolve(passkey)

        with self.peer_cen.security.on_passkey_display_required.register(on_display_request):
            with self.peer_per.security.on_passkey_required.register(on_entry_request):
                self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc, per_io_caps)

        self.assertTrue(display_event.is_set())
        self.assertTrue(entry_event.is_set())

        # Reconnect and pair again. Should be able to re-establish security using previous encryption
        self._reconnect(bond)
        display_event.clear()
        entry_event.clear()

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc, per_io_caps)

        self.assertFalse(display_event.is_set())
        self.assertFalse(entry_event.is_set())

    def test_pairing_peripheral_initiated_just_works_lesc_happy_path(self):
        initiate_using_central = False
        use_passcode = False
        io_caps = IoCapabilities.NONE
        bond = True
        reject = False
        lesc = True

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        # Reconnect and pair again. Should be able to re-establish security using previous encryption
        self._reconnect(bond)

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

    def test_pairing_peripheral_private_resolvable_address(self):
        self.periph_dev.set_privacy_settings(enabled=True, resolvable_address=True)

        initiate_using_central = True
        use_passcode = False
        io_caps = IoCapabilities.NONE
        bond = True
        reject = False
        lesc = True

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

        # Reconnect and pair again,
        # will need to scan for the address since it'll be advertising in private non-resolvable mode
        self._reconnect(bond, scan_for_address=True)

        self._perform_pairing(initiate_using_central, use_passcode, io_caps, bond, reject, lesc)

    # TODO: Add more tests
