"""
This example shows how to read descriptors of a peripheral's characteristic.

This can be used with the peripheral_descriptor example running on a separate nordic device.
"""
import binascii

from blatann import BleDevice
from blatann.gatt import PresentationFormat, GattStatusCode
from blatann.examples import example_utils, constants
from blatann.bt_sig.uuids import DescriptorUuid

logger = example_utils.setup_logger(level="INFO")


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.configure()
    ble_device.open()

    ble_device.scanner.set_default_scan_params(timeout_seconds=4)

    # Set the target to the peripheral's advertised name
    target_device_name = constants.PERIPHERAL_NAME

    logger.info("Scanning for '{}'".format(target_device_name))
    target_address = example_utils.find_target_device(ble_device, target_device_name)

    if not target_address:
        logger.info("Did not find target peripheral")
        return

    # Initiate the connection and wait for it to finish
    logger.info("Found match: connecting to address {}".format(target_address))
    peer = ble_device.connect(target_address).wait()
    if not peer:
        logger.warning("Timed out connecting to device")
        return
    logger.info("Connected, conn_handle: {}".format(peer.conn_handle))

    # Wait up to 10 seconds for service discovery to complete
    _, event_args = peer.discover_services().wait(10, exception_on_timeout=False)
    logger.info("Service discovery complete! status: {}".format(event_args.status))

    # Find the Time characteristic
    time_char = peer.database.find_characteristic(constants.DESC_EXAMPLE_CHAR_UUID)
    if not time_char:
        logger.info("Did not find the time characteristic")
    else:
        logger.info("Reading all characteristic attributes")
        for attr in time_char.attributes:
            logger.info(f"Reading UUID {attr.uuid} - {attr.uuid.description or '[unknown]'}")
            _, event_args = attr.read().wait(5)
            if event_args.status == GattStatusCode.success:
                # Show as hex unless it's the user descriptor UUID which should be a string
                if attr.uuid == DescriptorUuid.user_description:
                    value = event_args.value.decode("utf8")
                else:
                    value = binascii.hexlify(event_args.value)
                logger.info(f"    Value: {value}")
            else:
                logger.warning(f"    Failed to read attribute, status: {event_args.status}")

        # Read the characteristic's Presentation Format descriptor directly and decode the value
        presentation_fmt_desc = time_char.find_descriptor(DescriptorUuid.presentation_format)
        if presentation_fmt_desc:
            # Read, then decode the value using the PresentationFormat type
            logger.info("Reading the presentation format descriptor directly")
            _, event_args = presentation_fmt_desc.read().wait(5)
            if event_args.status == GattStatusCode.success:
                try:
                    fmt = PresentationFormat.decode(event_args.value)
                    logger.info(f"Presentation Format: {str(fmt.format)}, Exponent: {fmt.exponent}, Unit: {str(fmt.unit)}")
                except Exception as e:
                    logger.error("Failed to decode the presentation format descriptor")
                    logger.exception(e)
        else:
            logger.info("Failed to find the presentation format descriptor")

    # Clean up
    logger.info("Disconnecting from peripheral")
    peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM11")
