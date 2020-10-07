import queue
import unittest

from blatann import BleDevice, gatt
from blatann.bt_sig.uuids import DescriptorUuid
from blatann.event_args import WriteEventArgs
from blatann.gatt import PresentationFormat
from blatann.gatt.gattc import GattcCharacteristic
from blatann.gatt.gatts import GattsCharacteristicProperties, GattsCharacteristic, GattsUserDescriptionProperties
from blatann.uuid import Uuid128, generate_random_uuid128

from tests.integrated.base import BlatannTestCase, TestParams, long_running
from tests.integrated.helpers import PeriphConn, CentralConn, setup_connection, rand_bytes


def _generate_char(svc, uuid, *prop_names, init_value=b"", max_length=20):
    prop_args = dict(read=False, write=False, notify=False, indicate=False, broadcast=False, write_no_response=False,
                     max_length=max_length)
    prop_args.update({p: True for p in prop_names})
    properties = GattsCharacteristicProperties(**prop_args)
    return svc.add_characteristic(uuid, properties, init_value)


class _PeriphConn(PeriphConn):
    def __init__(self):
        super(_PeriphConn, self).__init__()
        self.all_char: GattsCharacteristic = None
        self.write_char: GattsCharacteristic = None
        self.write_no_resp_char: GattsCharacteristic = None
        self.read_char: GattsCharacteristic = None
        self.indicate_char: GattsCharacteristic = None
        self.notify_char: GattsCharacteristic = None
        self.large_char: GattsCharacteristic = None


class _CentralConn(CentralConn):
    def __init__(self):
        super(_CentralConn, self).__init__()
        self.all_char: GattcCharacteristic = None
        self.write_char: GattcCharacteristic = None
        self.write_no_resp_char: GattcCharacteristic = None
        self.read_char: GattcCharacteristic = None
        self.indicate_char: GattcCharacteristic = None
        self.notify_char: GattcCharacteristic = None
        self.large_char: GattcCharacteristic = None


class TestGatt(BlatannTestCase):
    periph_conn = _PeriphConn()
    central_conn = _CentralConn()
    periph: BleDevice
    central: BleDevice

    service_1_uuid = generate_random_uuid128().new_uuid_from_base(0)
    all_char_uuid = service_1_uuid.new_uuid_from_base(1)

    service_2_uuid = generate_random_uuid128().new_uuid_from_base(0)
    write_char_uuid = service_2_uuid.new_uuid_from_base(1)
    write_no_resp_char_uuid = service_2_uuid.new_uuid_from_base(2)
    read_char_uuid = service_2_uuid.new_uuid_from_base(3)
    indicate_char_uuid = service_2_uuid.new_uuid_from_base(4)
    notify_char_uuid = service_2_uuid.new_uuid_from_base(5)
    large_char_uuid = service_2_uuid.new_uuid_from_base(6)

    large_char_size = 512

    sender_q = queue.Queue
    received_value_q: queue.Queue

    @classmethod
    def setUpClass(cls) -> None:
        super(TestGatt, cls).setUpClass()
        cls.periph = cls.dev1
        cls.periph_conn.dev = cls.dev1
        cls.central = cls.dev2
        cls.central_conn.dev = cls.dev2

        cls.periph.client.preferred_mtu_size = cls.periph.max_mtu_size
        cls._setup_database()
        cls._setup_connection()

    @classmethod
    def _setup_database(cls):
        svc = cls.periph.database.add_service(cls.service_1_uuid)

        all_props = GattsCharacteristicProperties(read=True, write=True, notify=True, indicate=True, write_no_response=True, broadcast=True,
                                                  max_length=20, variable_length=True, sccd=True,
                                                  user_description=GattsUserDescriptionProperties("Everything"),
                                                  presentation_format=PresentationFormat(8, 0, 0x2700))
        cls.periph_conn.all_char = svc.add_characteristic(cls.all_char_uuid, all_props, b"0" * 20)

        svc = cls.periph.database.add_service(cls.service_2_uuid)
        cls.periph_conn.write_char = _generate_char(svc, cls.write_char_uuid, "write")
        cls.periph_conn.read_char = _generate_char(svc, cls.read_char_uuid, "read", init_value=b"1234" * 5)
        cls.periph_conn.notify_char = _generate_char(svc, cls.notify_char_uuid, "notify")
        cls.periph_conn.indicate_char = _generate_char(svc, cls.indicate_char_uuid, "indicate")
        cls.periph_conn.write_no_resp_char = _generate_char(svc, cls.write_no_resp_char_uuid, "write_no_response")
        cls.periph_conn.large_char = _generate_char(svc, cls.large_char_uuid, "read", "write", max_length=cls.large_char_size)

    @classmethod
    def _setup_connection(cls):
        cls.periph.client.preferred_mtu_size = gatt.MTU_SIZE_DEFAULT
        setup_connection(cls.periph_conn, cls.central_conn)
        db = cls.central_conn.db
        cls.central_conn.all_char = db.find_characteristic(cls.all_char_uuid)
        cls.central_conn.write_char = db.find_characteristic(cls.write_char_uuid)
        cls.central_conn.read_char = db.find_characteristic(cls.read_char_uuid)
        cls.central_conn.notify_char = db.find_characteristic(cls.notify_char_uuid)
        cls.central_conn.indicate_char = db.find_characteristic(cls.indicate_char_uuid)
        cls.central_conn.write_no_resp_char = db.find_characteristic(cls.write_no_resp_char_uuid)
        cls.central_conn.large_char = db.find_characteristic(cls.large_char_uuid)

    def setUp(self) -> None:
        # Verify connection was setup correctly before executing any tests
        self.assertIsNotNone(self.central_conn.peer)
        self.assertIsNotNone(self.periph_conn.peer)
        self.sender_q = queue.Queue()
        self.received_value_q = queue.Queue()

    def _on_write(self, sender: GattcCharacteristic, event_args: WriteEventArgs):
        self.sender_q.put(sender)
        self.received_value_q.put(event_args.value)

    def _get_received_value(self, timeout=10):
        return self.received_value_q.get(timeout=timeout)

    def test_0_property_discovery(self):
        # Verify all the characteristics were discovered
        self.assertIsNotNone(self.central_conn.write_char)
        self.assertIsNotNone(self.central_conn.read_char)
        self.assertIsNotNone(self.central_conn.notify_char)
        self.assertIsNotNone(self.central_conn.indicate_char)
        self.assertIsNotNone(self.central_conn.write_no_resp_char)
        self.assertIsNotNone(self.central_conn.large_char)
        # Verify UUIDs are correct
        self.assertEqual(self.central_conn.write_char.uuid, self.write_char_uuid)
        self.assertEqual(self.central_conn.read_char.uuid, self.read_char_uuid)
        self.assertEqual(self.central_conn.notify_char.uuid, self.notify_char_uuid)
        self.assertEqual(self.central_conn.indicate_char.uuid, self.indicate_char_uuid)
        self.assertEqual(self.central_conn.write_no_resp_char.uuid, self.write_no_resp_char_uuid)
        self.assertEqual(self.central_conn.large_char.uuid, self.large_char_uuid)

        def check_char_props(char, read=False, write=False, notify=False,
                             indicate=False, write_no_response=False):
            self.assertEqual(read, char.readable)
            self.assertEqual(write, char.writable)
            self.assertEqual(notify or indicate, char.subscribable)
            self.assertEqual(notify, char.subscribable_notifications)
            self.assertEqual(indicate, char.subscribable_indications)
            self.assertEqual(write_no_response, char.writable_without_response)

        # Check the properties of all the characteristics
        check_char_props(self.central_conn.all_char, read=True, write=True, notify=True, indicate=True, write_no_response=True)
        check_char_props(self.central_conn.write_char, write=True)
        check_char_props(self.central_conn.read_char, read=True)
        check_char_props(self.central_conn.notify_char, notify=True)
        check_char_props(self.central_conn.indicate_char, indicate=True)
        check_char_props(self.central_conn.write_no_resp_char, write_no_response=True)
        check_char_props(self.central_conn.large_char, read=True, write=True)

    def test_descriptor_discovery(self):
        # all_char should have CCCD, SCCD, User Description, Presentation Format attributes
        c = self.central_conn.all_char

        def get_descriptor(uuid):
            desc = c.find_descriptor(uuid)
            self.assertIsNotNone(desc)
            return desc

        cccd = get_descriptor(DescriptorUuid.cccd)
        sccd = get_descriptor(DescriptorUuid.sccd)
        user_desc = get_descriptor(DescriptorUuid.user_description)
        pf = get_descriptor(DescriptorUuid.presentation_format)

        # Notify and indicate should also have cccds
        self.assertIsNotNone(self.central_conn.notify_char.find_descriptor(DescriptorUuid.cccd))
        self.assertIsNotNone(self.central_conn.indicate_char.find_descriptor(DescriptorUuid.cccd))

        # Try reading each of the descriptors
        _, cccd_resp = cccd.read().wait(10)
        self.assertEqual(b"\x00\x00", cccd_resp.value)

        _, sccd_resp = sccd.read().wait(10)

        _, user_desc_resp = user_desc.read().wait(10)
        self.assertEqual(b"Everything", user_desc_resp.value)

        _, pf_resp = pf.read().wait(10)
        pf_val = PresentationFormat.decode(pf_resp.value)
        self.assertEqual(8, pf_val.format)
        self.assertEqual(0, pf_val.exponent)
        self.assertEqual(0x2700, pf_val.unit)

    def test_writes(self):
        # Subscribe for when the peripheral's all_char is written to
        with self.periph_conn.all_char.on_write.register(self._on_write):
            # Write some bytes
            value = rand_bytes(20)
            self.central_conn.all_char.write(value).wait(10)
            # Check that the peripheral got the correct value
            self.assertEqual(value, self._get_received_value())

            # Repeat for write_without_response operation
            value = rand_bytes(20)
            self.central_conn.all_char.write_without_response(value).wait(10)
            self.assertEqual(value, self._get_received_value())

        # repeat for write_char
        with self.periph_conn.write_char.on_write.register(self._on_write):
            value = rand_bytes(20)
            self.central_conn.write_char.write(value).wait(10)
            self.assertEqual(value, self._get_received_value())

        # repeat for write_no_resp_char
        with self.periph_conn.write_no_resp_char.on_write.register(self._on_write):
            value = rand_bytes(20)
            self.central_conn.write_no_resp_char.write_without_response(value).wait(10)
            self.assertEqual(value, self._get_received_value())

    def test_read(self):
        # Standard read. Set value before read
        value = rand_bytes(20)
        self.periph_conn.read_char.set_value(value)

        # Initiate read
        _, read_resp = self.central_conn.read_char.read().wait(10)

        # Verify returned value
        self.assertEqual(value, read_resp.value)

    def test_lazy_read(self):
        set_value = [b""]

        def on_read(char, event_args):
            # Set the value when a read is initiated instead of beforehand
            v = rand_bytes(20)
            set_value[0] = v
            char.set_value(v)

        # Subscribe to on_read event
        with self.periph_conn.read_char.on_read.register(on_read):
            # Initiate read from central
            _, read_resp = self.central_conn.read_char.read().wait(10)

        # Verify the value set in the on_read handler matches the value read
        self.assertEqual(set_value[0], read_resp.value)

    def test_long_reads_writes(self):
        # Writes larger than one MTU
        with self.periph_conn.large_char.on_write.register(self._on_write):
            value = rand_bytes(self.large_char_size)
            self.central_conn.large_char.write(value).wait(10)
            self.assertEqual(value, self._get_received_value())

        # Reads larger than one MTU
        value = rand_bytes(self.large_char_size)
        self.periph_conn.large_char.set_value(value)

        _, read_resp = self.central_conn.large_char.read().wait(10)
        self.assertEqual(value, read_resp.value)
