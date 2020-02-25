"""
This example demonstrates programming with blatann in an event-driven, object-oriented manner.
The BLE device is set up in the main context, however all logic past that point is done using
event callbacks.
The main context is blocked by a "GenericWaitable", which is notified when the program
completes its intended function.

The program's logic itself is equivalent to the central example, where it connects and pairs to a device,
registers a notification callback for the counting characteristic, then tests out the conversion of strings to hex.

One thing to note: when using event-driven callbacks, it is imperative that the callbacks themselves do
not ever block on events (i.e. use the .wait() functionality). If this happens, you are essentially blocking
the event thread from processing any more events and will wait indefinitely.
A good rule of thumb when using blatann is just to not mix blocking and non-blocking calls.

This is designed to work alongside the peripheral example running on a separate nordic chip
"""
import struct
from blatann import BleDevice
from blatann.gap import smp
from blatann.examples import example_utils, constants
from blatann.waitables import GenericWaitable
from blatann.nrf import nrf_events

logger = example_utils.setup_logger(level="DEBUG")


class HexConverterTest(object):
    """
    Class to perform the hex conversion process. It is passed in the hex conversion characteristic
    and the waitable to signal when the process completes
    """
    def __init__(self, characteristic, waitable):
        """
        :param characteristic: The hex conversion characteristic to use
        :type characteristic: blatann.gatt.gattc.GattcCharacteristic
        :param waitable: The waitable to notify when the testing ends
        :type waitable: GenericWaitable
        """
        self.char = characteristic
        self.waitable = waitable
        self.i = 1
        # Generate some data, "ABCDEFG..."
        self.data_to_convert = bytes(ord('A') + i for i in range(12))

    def start(self):
        """
        Starts a new hex conversion process by writing the data to the peripheral's characteristic
        """
        data_to_send = self.data_to_convert[:self.i]
        logger.info("Converting to hex data: '{}'".format(data_to_send))
        # Write the data, and setup the _write_complete callback to be executed when the write finishes
        self.char.write(data_to_send).then(self._write_complete)

    def _write_complete(self, characteristic, event_args):
        """
        Event callback for when the hex data write completes.
        Initiates the read on the characteristic

        :param characteristic: The characteristic itself (hex converter characteristic, should always match self.char)
        :param event_args: The write event args
        :type event_args: blatann.event_args.WriteCompleteEventArgs
        """
        # At this point we should probably check event_args.status to make sure it was written successfully
        # Initiate the read, and setup _read_complete to be called when it finishes
        self.char.read().then(self._read_complete)

    def _read_complete(self, characteristic, event_args):
        """
        Event callback for when the hex characteristic read completes.
        Checks to see if the process is complete, if not starts another conversion

        :param characteristic: The characteristic itself (hex converter characteristic, should always match self.char)
        :param event_args: The read event args
        :type event_args: blatann.event_args.ReadCompleteEventArgs
        """
        logger.info("Hex: '{}'".format(event_args.value.decode("ascii")))
        self.i += 1
        if self.i > len(self.data_to_convert):
            # Done, notify the main thread that we are done
            self.waitable.notify()
        else:
            # Not done, start the next conversion
            self.start()


class MyPeripheralConnection(object):
    """
    Class to handle the post-connection database discovery and pairing process
    """
    def __init__(self, peer, waitable):
        """
        :param peer: The peer that was connected to
        :type peer: blatann.peer.Peripheral
        :param waitable: The waitable to notify to end the process
        :type waitable: GenericWaitable
        """
        self.peer = peer
        self.waitable = waitable
        self._start_db_discovery()

    def _start_db_discovery(self):
        """
        Initiates database discovery
        """
        self.peer.discover_services().then(self._on_db_discovery)

    def _on_db_discovery(self, peer, event_args):
        """
        Event callback for when database discovery completes

        :param peer: The peer the database discovery completed on (should equal self.peer)
        :type peer: blatann.peer.Peripheral
        :param event_args: The event arguments
        :type event_args: blatann.event_args.DatabaseDiscoveryCompleteEventArgs
        """

        logger.info("Service discovery complete! status: {}".format(event_args.status))
        # The peer's database is now current, log out the services found
        for service in peer.database.services:
            logger.info(service)

        # Find and subscribe to the counting characteristic
        counting_char = self.peer.database.find_characteristic(constants.COUNTING_CHAR_UUID)
        if counting_char:
            logger.info("Subscribing to the counting characteristic")
            counting_char.subscribe(self._on_counting_char_notification)
        else:
            logger.warning("Failed to find counting characteristic")

        # Initiate the pairing process
        self._start_pairing()

    def _start_pairing(self):
        """
        Sets up the security parameters and starts the pairing process
        """
        self.peer.security.set_security_params(passcode_pairing=True, io_capabilities=smp.IoCapabilities.KEYBOARD_DISPLAY,
                                               bond=False, out_of_band=False)
        self.peer.security.on_passkey_required.register(self._on_passkey_entry)
        self.peer.security.pair().then(self._on_pair_complete)

    def _on_passkey_entry(self, peer, event_args):
        """
        Event callback for when a passkey is required to be entered by the user
        Requests the user to enter the passkey and resolves the event with the passkey entered

        :param peer: the peer the passkey is for
        :param event_args: The event args
        :type event_args: blatann.event_args.PasskeyEntryEventArgs
        """
        passkey = input("Enter peripheral passkey: ")
        event_args.resolve(passkey)

    def _on_pair_complete(self, peer, event_args):
        """
        Event callback for when pairing completes. Finds the hex conversion characteristic in the database
        and starts the hex converter testing

        :param peer: The peer the pairing completed on
        :param event_args: The event args
        :type event_args: blatann.event_args.PairingCompleteEventArgs
        """
        # At this point, we should probably check event_args.status to verify that pairing completed successfully

        # Find the hex converter char. If found, start the testing. Otherwise, notify the main thread to exit
        hex_convert_char = self.peer.database.find_characteristic(constants.HEX_CONVERT_CHAR_UUID)
        if hex_convert_char:
            self.hex_counter = HexConverterTest(hex_convert_char, self.waitable)
            self.hex_counter.start()
        else:
            logger.warning("Failed to find hex convert char")
            self.waitable.notify()

    def _on_counting_char_notification(self, characteristic, event_args):
        """
            Callback for when a notification is received from the peripheral's counting characteristic.
            The peripheral will periodically notify a monotonically increasing, 4-byte integer. This callback unpacks
            the value and logs it out

            :param characteristic: The characteristic the notification was on (counting characteristic)
            :param event_args: The event arguments
            :type event_args: blatann.event_args.NotificationReceivedEventArgs
            """
        # Unpack as a little-endian, 4-byte integer
        current_count = struct.unpack("<I", event_args.value)[0]
        logger.info("Counting char notification. Current count: {}".format(current_count))


class ConnectionManager(object):
    """
    Manages scanning and connecting to the target peripheral
    """
    def __init__(self, ble_device, exit_waitable):
        """
        :param ble_device: The BLE Device to operate
        :type ble_device: BleDevice
        :param exit_waitable: The waitiable to notify to exit the program
        :type exit_waitable: GenericWaitable
        """
        self.ble_device = ble_device
        self.exit_waitable = exit_waitable
        self.target_device_name = ""
        self.connection = None
        self.peer = None

    def _on_connect(self, peer):
        """
        Event callback for when the peer's connection process completes.
        If the connection failed, will exit the program. Otherwise, will create
        a MyPeripheralConnection to manage the connection process

        :param peer: The peer that connected, or None if the connection process failed
        :type peer: blatann.peer.Peripheral
        """
        if not peer:
            logger.warning("Timed out connecting to device")
            self.exit_waitable.notify()
        else:
            logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
            self.peer = peer
            # Connect the disconnect event to the exit waitable, so if
            # the peripheral disconnects from us unexpectedly the program terminates
            peer.on_disconnect.register(self.exit_waitable.notify)
            # Create the connection
            self.connection = MyPeripheralConnection(peer, self.exit_waitable)

    def _on_scan_report(self, scan_report):
        """
        Event callback when a scan report completes.
        Searches for the target advertised peripheral name. If found, starts the connection process.
        Otherwise, the program terminates

        :param scan_report: The complete scan report from the scanning session
        :type scan_report: blatann.gap.scanning.ScanReportCollection
        """
        for report in scan_report.advertising_peers_found:
            if report.advertise_data.local_name == self.target_device_name:
                logger.info("Found match: connecting to address {}".format(report.peer_address))
                self.ble_device.connect(report.peer_address).then(self._on_connect)
                return

        logger.info("Did not find target peripheral")
        self.exit_waitable.notify()

    def scan_and_connect(self, name, timeout=4):
        """
        Starts the scanning process and sets up the callback for when scanning completes

        :param name: The name of the peripheral to look for
        :param timeout: How long to scan for
        """
        logger.info("Scanning for '{}'".format(name))
        self.target_device_name = name
        self.ble_device.scanner.set_default_scan_params(timeout_seconds=timeout)
        self.ble_device.scanner.start_scan().then(self._on_scan_report)


def main(serial_port):
    target_device_name = constants.PERIPHERAL_NAME
    # Create a waitable that will block the main thread until notified by one of the classes above
    main_thread_waitable = GenericWaitable()

    # Create and open the BLE device (and suppress spammy logs)
    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    # Create the connection manager and start the scanning process
    s = ConnectionManager(ble_device, main_thread_waitable)
    s.scan_and_connect(target_device_name)

    # Block the main thread indefinitely until the program finishes
    main_thread_waitable.wait()

    # Clean up, disconnect if a peer was connected to
    if s.peer:
        s.peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM9")
