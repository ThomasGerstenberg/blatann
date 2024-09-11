from __future__ import annotations

import logging
import math
import time
import unittest

from blatann import BleDevice
from blatann.event_args import WriteEventArgs
from blatann.gatt.gattc import GattcCharacteristic
from blatann.gatt.gatts import GattsCharacteristic, GattsCharacteristicProperties
from blatann.peer import Phy
from blatann.utils import Stopwatch
from blatann.uuid import Uuid128

from tests.integrated.base import BlatannTestCase, TestParams, long_running
from tests.integrated.helpers import CentralConn, PeriphConn, rand_bytes, setup_connection


class _PeriphConn(PeriphConn):
    def __init__(self):
        super(_PeriphConn, self).__init__()
        self.write_char: GattsCharacteristic = None
        self.write_no_resp_char: GattsCharacteristic = None


class _CentralConn(CentralConn):
    def __init__(self):
        super(_CentralConn, self).__init__()
        self.write_char: GattcCharacteristic = None
        self.write_no_resp_char: GattcCharacteristic = None


class TestGattWrites(BlatannTestCase):
    periph_conn = _PeriphConn()
    central_conn = _CentralConn()
    periph: BleDevice
    central: BleDevice
    write_size: int
    service_uuid: Uuid128
    write_char_uuid: Uuid128
    write_no_resp_char_uuid: Uuid128

    @classmethod
    def setUpClass(cls) -> None:
        super(TestGattWrites, cls).setUpClass()
        cls.periph_conn.dev = cls.dev1
        cls.central_conn.dev = cls.dev2
        cls.periph = cls.dev1
        cls.central = cls.dev2
        cls.periph.client.preferred_mtu_size = cls.periph.max_mtu_size
        cls.write_size = cls.periph.client.preferred_mtu_size - 3
        cls.service_uuid = Uuid128("00112233-4455-6677-8899-aabbccddeeff")
        cls.write_char_uuid = cls.service_uuid.new_uuid_from_base(0x0000)
        cls.write_no_resp_char_uuid = cls.service_uuid.new_uuid_from_base(0x0001)
        cls._setup_database()
        cls._setup_connection()
        # Up minimum log level to increase throughput (less writing to console)
        cls.prev_log_level = logging.root.level
        logging.root.setLevel("INFO")

    @classmethod
    def tearDownClass(cls) -> None:
        logging.root.setLevel(cls.prev_log_level)
        super(TestGattWrites, cls).tearDownClass()

    @classmethod
    def _setup_database(cls):
        w_props = GattsCharacteristicProperties(read=False, write=True,
                                                max_length=cls.write_size, variable_length=True)
        w_no_resp_props = GattsCharacteristicProperties(read=False, write_no_response=True,
                                                        max_length=cls.write_size, variable_length=True)
        svc = cls.periph.database.add_service(cls.service_uuid)
        cls.periph_conn.write_char = svc.add_characteristic(cls.write_char_uuid, w_props)
        cls.periph_conn.write_no_resp_char = svc.add_characteristic(cls.write_no_resp_char_uuid, w_no_resp_props)

    @classmethod
    def _setup_connection(cls):
        cls.periph.client.preferred_mtu_size = cls.periph.max_mtu_size

        setup_connection(cls.periph_conn, cls.central_conn)

        cls.central_conn.peer.exchange_mtu(cls.central_conn.dev.max_mtu_size).wait(10)
        cls.central_conn.peer.update_data_length().wait(10)
        cls.central_conn.peer.update_phy(Phy.two_mbps).wait(10)
        cls.central_conn.write_char = cls.central_conn.db.find_characteristic(cls.write_char_uuid)
        cls.central_conn.write_no_resp_char = cls.central_conn.db.find_characteristic(cls.write_no_resp_char_uuid)

    def setUp(self) -> None:
        # Verify connection was setup correctly before executing any tests
        self.assertIsNotNone(self.central_conn.peer)
        self.assertIsNotNone(self.periph_conn.peer)

        self.assertIsNotNone(self.central_conn.write_char)
        self.assertIsNotNone(self.central_conn.write_no_resp_char)
        self.assertTrue(self.central_conn.write_char.writable)
        self.assertTrue(self.central_conn.write_no_resp_char.writable_without_response)
        self.write_size = self.periph_conn.peer.mtu_size - 3

    def _run_throughput_test(self, periph_char: GattsCharacteristic, central_char: GattcCharacteristic, data_size=20000):
        # Queue up 20k of data, track the time it takes to send
        periph_stopwatch = Stopwatch()
        central_stopwatch = Stopwatch()

        n_packets = math.ceil(data_size / self.write_size)
        bytes_to_send = n_packets * self.write_size
        bytes_sent = 0
        bytes_received = [0]
        packets_received = [0]

        data = rand_bytes(self.write_size)

        def on_write_received(char: GattsCharacteristic, event_data: WriteEventArgs):
            if periph_stopwatch.is_running:
                periph_stopwatch.mark()
            else:
                periph_stopwatch.start()
            packets_received[0] += 1
            bytes_received[0] += len(event_data.value)

        write_func = central_char.write if central_char.writable else central_char.write_without_response

        with periph_char.on_write.register(on_write_received):
            central_stopwatch.start()
            while bytes_sent < bytes_to_send:
                waitable = write_func(data)
                bytes_sent += self.write_size
            waitable.wait(60)
            central_stopwatch.stop()
            time.sleep(0.5)

        self.logger.info(f"{bytes_sent} bytes sent in {periph_stopwatch.elapsed:.3f}s/{central_stopwatch.elapsed:.3f}. "
                         f"Bytes Received: {bytes_received[0]}, Packets: {packets_received[0]}")
        self.logger.info(f"Throughput: {bytes_sent/central_stopwatch.elapsed/1024.0:.3f}kB/s")
        # Verify all the bytes sent were received by the peripheral
        self.assertEqual(bytes_sent, bytes_received[0])

    def test_write_with_response_throughput(self):
        self._run_throughput_test(self.periph_conn.write_char, self.central_conn.write_char, 50000)

    def test_write_without_response_throughput(self):
        self._run_throughput_test(self.periph_conn.write_no_resp_char,
                                  self.central_conn.write_no_resp_char, 200000)
