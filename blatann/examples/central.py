import time
import struct
from blatann import BleDevice, uuid
from blatann.gap import smp
from blatann.examples import example_utils, constants
from blatann.nrf import nrf_events

logger = example_utils.setup_logger(level="DEBUG")


def find_target_device(ble_device, name):
    scan_report = ble_device.scanner.start_scan().wait()

    for report in scan_report.advertising_peers_found:
        if report.advertise_data.local_name == name:
            return report.peer_address


def on_counting_char_notification(characteristic, value):
    current_count = struct.unpack("<I", value)[0]
    logger.info("Counting char notification. Curent count: {}".format(current_count))


def main(serial_port):
    target_device_name = "Periph Test"

    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)

    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    logger.info("Scanning for '{}'".format(target_device_name))
    while True:
        logger.info("Scanning...")
        target_address = find_target_device(ble_device, target_device_name)

        if not target_address:
            logger.info("Did not find target peripheral")
            continue

        logger.info("Found match: connecting to address {}".format(target_address))
        peer = ble_device.connect(target_address).wait()
        if not peer:
            logger.warning("Timed out connecting to device")
            continue
        logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
        services, status = peer.discover_services().wait(10, exception_on_timeout=False)
        logger.info("Service discovery complete! status: {}".format(status))
        for service in peer.database.services:
            logger.info(service)

        peer.set_connection_parameters(100, 120, 6000)  # Discovery complete, go to a longer connection interval

        # Pair with the peripheral
        def on_passkey_entry(peer, key_type, resolve):
            passkey = raw_input("Enter peripheral passkey: ")
            resolve(passkey)

        peer.security.set_security_params(True, smp.IoCapabilities.KEYBOARD_DISPLAY, False, False)
        peer.security.on_passkey_required.register(on_passkey_entry)
        _, status = peer.security.pair().wait(60)

        # Find the counting characteristic
        counting_char = peer.database.find_characteristic(constants.COUNTING_CHAR_UUID)
        if counting_char:
            logger.info("Subscribing to the counting characteristic")
            counting_char.subscribe(on_counting_char_notification).wait(5)
        else:
            logger.warning("Failed to find counting characteristic")

        hex_convert_char = peer.database.find_characteristic(constants.HEX_CONVERT_CHAR_UUID)
        if hex_convert_char:
            logger.info("Testing writes")
            data_to_convert = bytearray(ord('A') + i for i in range(48))
            for i in range(constants.HEX_CONVERT_CHAR_PROPERTIES.max_len/2):
                data_to_send = data_to_convert[:i+1]
                logger.info("Converting to hex data: '{}'".format(data_to_send))
                if not hex_convert_char.write(data_to_send).wait(5, False):
                    logger.error("Failed to write data, i={}".format(i))
                    break

                char, status, data_read = hex_convert_char.read().wait(5, False)
                logger.info("Hex: '{}'".format(data_read))
        else:
            logger.warning("Failed to find char1")

        logger.info("Disconnecting from peripheral")
        peer.disconnect().wait()


if __name__ == '__main__':
    main("COM4")
