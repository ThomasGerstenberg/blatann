import queue
import threading
import time
import unittest
from typing import Union

from blatann.event_args import PasskeyDisplayEventArgs, PasskeyEntryEventArgs

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

    def _set_security_parameters(self, passcode_pairing: bool,
                            io_capabilities: IoCapabilities,
                            bond: bool,
                            reject_pairing_requests: Union[bool, PairingPolicy] = False,
                            lesc_pairing: bool = False):
        security_params1 = SecurityParameters(passcode_pairing, io_capabilities, bond, False, reject_pairing_requests, lesc_pairing)
        security_params2 = SecurityParameters(passcode_pairing, io_capabilities, bond, False, reject_pairing_requests, lesc_pairing)
        self.peer_per.security.security_params = security_params1
        self.peer_cen.security.security_params = security_params2

    def test_nonbonded_devices_rejects_by_default(self):
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()
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

    def test_bonding_no_mitm_happy_path(self):
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()

        self.assertFalse(self.peer_per.is_previously_bonded)
        self.assertFalse(self.peer_cen.is_previously_bonded)

        self._set_security_parameters(False, IoCapabilities.NONE, True, False, True)

        _, result = self.peer_per.security.pair().wait(10)

        self.assertEqual(SecurityStatus.success, result.status)
        self.assertEqual(SecurityLevel.JUST_WORKS, self.peer_per.security.security_level)
        self.assertEqual(SecurityLevel.JUST_WORKS, self.peer_cen.security.security_level)

    def test_bonding_passcode_match_happy_path(self):
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()

        self.assertFalse(self.peer_per.is_previously_bonded)
        self.assertFalse(self.peer_cen.is_previously_bonded)

        self._set_security_parameters(True, IoCapabilities.DISPLAY_YESNO, True, False, True)
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
                _, result = self.peer_per.security.pair().wait(10)

        self.assertEqual(SecurityStatus.success, result.status)
        self.assertEqual(SecurityLevel.LESC_MITM, self.peer_per.security.security_level)
        self.assertEqual(SecurityLevel.LESC_MITM, self.peer_cen.security.security_level)
        self.assertTrue(per_event.is_set())
        self.assertTrue(cen_event.is_set())

    def test_bonding_passkey_entry_happy_path(self):
        self.periph_dev.clear_bonding_data()
        self.central_dev.clear_bonding_data()

        self._connect()

        self.assertFalse(self.peer_per.is_previously_bonded)
        self.assertFalse(self.peer_cen.is_previously_bonded)

        self._set_security_parameters(True, IoCapabilities.DISPLAY_ONLY, True, False, True)
        self.peer_per.security.security_params.io_capabilities = IoCapabilities.KEYBOARD_DISPLAY
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
                _, result = self.peer_per.security.pair().wait(10)

        self.assertEqual(SecurityStatus.success, result.status)
        self.assertEqual(SecurityLevel.LESC_MITM, self.peer_per.security.security_level)
        self.assertEqual(SecurityLevel.LESC_MITM, self.peer_cen.security.security_level)
        self.assertTrue(display_event.is_set())
        self.assertTrue(entry_event.is_set())

    # TODO: Add more tests
