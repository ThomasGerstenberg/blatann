import struct
from blatann import BleDevice
from blatann.gap import smp
from blatann.examples import example_utils, constants
from blatann.waitables import GenericWaitable
from blatann.nrf import nrf_events

logger = example_utils.setup_logger(level="DEBUG")


class HexConverterTest(object):
    def __init__(self, characteristic, waitable):
        self.char = characteristic
        self.waitable = waitable
        self.i = 1
        self.data_to_convert = bytearray(ord('A') + i for i in range(12))

    def start(self):
        data_to_send = self.data_to_convert[:self.i]
        logger.info("Converting to hex data: '{}'".format(data_to_send))
        self.char.write(data_to_send).then(self._write_complete)

    def _write_complete(self, characteristic, event_args):
        self.char.read().then(self._read_complete)

    def _read_complete(self, characteristic, event_args):
        logger.info("Hex: '{}'".format(event_args.value))
        self.i += 1
        if self.i > len(self.data_to_convert):
            self.waitable.notify()
        else:
            self.start()


class MyPeripheralConnection(object):
    def __init__(self, peer, waitable):
        """
        :type peer: blatann.peer.Peripheral
        :param waitable:
        """
        self.peer = peer
        self.waitable = waitable
        self._start_db_discovery()

    def _start_db_discovery(self):
        self.peer.discover_services().then(self._on_db_discovery)

    def _on_db_discovery(self, peer, event_args):
        logger.info("Service discovery complete! status: {}".format(event_args.status))
        for service in peer.database.services:
            logger.info(service)

        counting_char = self.peer.database.find_characteristic(constants.COUNTING_CHAR_UUID)
        if counting_char:
            logger.info("Subscribing to the counting characteristic")
            counting_char.subscribe(self._on_counting_char_notification)
        else:
            logger.warning("Failed to find counting characteristic")
        self._start_pairing()

    def _start_pairing(self):
        self.peer.security.set_security_params(True, smp.IoCapabilities.KEYBOARD_DISPLAY, False, False)
        self.peer.security.on_passkey_required.register(self._on_passkey_entry)
        self.peer.security.pair().then(self._on_pair_complete)

    def _on_passkey_entry(self, peer, event_args):
        passkey = raw_input("Enter peripheral passkey: ")
        event_args.resolve(passkey)

    def _on_pair_complete(self, peer, event_args):
        hex_convert_char = self.peer.database.find_characteristic(constants.HEX_CONVERT_CHAR_UUID)
        if hex_convert_char:
            self.hex_counter = HexConverterTest(hex_convert_char, self.waitable)
            self.hex_counter.start()
        else:
            logger.warning("Failed to find hex convert char")
            self.waitable.notify()

    def _on_counting_char_notification(self, characteristic, event_args):
        current_count = struct.unpack("<I", event_args.value)[0]
        logger.info("Counting char notification. Curent count: {}".format(current_count))


class ConnectionManager(object):
    def __init__(self, ble_device, exit_waitable):
        """
        :type ble_device: BleDevice
        """
        self.ble_device = ble_device
        self.exit_waitable = exit_waitable
        self.target_device_name = ""
        self.connection = None
        self.peer = None

    def _on_connect(self, peer):
        if not peer:
            logger.warning("Timed out connecting to device")
            self.exit_waitable.notify()
        else:
            logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
            self.peer = peer
            peer.on_disconnect.register(self.exit_waitable.notify)
            self.connection = MyPeripheralConnection(peer, self.exit_waitable)

    def _on_scan_report(self, scan_report):
        for report in scan_report.advertising_peers_found:
            if report.advertise_data.local_name == self.target_device_name:
                logger.info("Found match: connecting to address {}".format(report.peer_address))
                self.ble_device.connect(report.peer_address).then(self._on_connect)
                return

        logger.info("Did not find target peripheral")
        self.exit_waitable.notify()

    def scan_and_connect(self, name, timeout=4):
        logger.info("Scanning for '{}'".format(name))
        self.target_device_name = name
        self.ble_device.scanner.set_default_scan_params(timeout_seconds=timeout)
        self.ble_device.scanner.start_scan().then(self._on_scan_report)


def main(serial_port):
    target_device_name = constants.PERIPHERAL_NAME
    main_thread_waitable = GenericWaitable()

    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    s = ConnectionManager(ble_device, main_thread_waitable)
    s.scan_and_connect(target_device_name)

    main_thread_waitable.wait()
    if s.peer:
        s.peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM4")
