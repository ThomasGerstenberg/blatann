import queue
import unittest

from blatann import BleDevice
from blatann.gap.gap_types import ConnectionParameters
from blatann.waitables import EventWaitable

from tests.integrated.base import BlatannTestCase, TestParams, long_running
from tests.integrated.helpers import PeriphConn, CentralConn, setup_connection


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

    def tearDown(self) -> None:
        if self.central_conn.peer.connected:
            self.central_conn.peer.disconnect().wait(10)

    def _run_conn_param_test(self, central_initiated, central_reject=False):
        conn_event_queue = queue.Queue()
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
