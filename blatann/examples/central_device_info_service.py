"""
This example demonstrates reading a peripheral's Device Info Service using blatann's device_info service module.
The operations here are programmed in a procedural manner.

This can be used alongside any peripheral which implements the DIS and advertises the 16-bit DIS service UUID.
The peripheral_device_info_service example can be used with this.
"""
from blatann import BleDevice
from blatann.examples import example_utils
from blatann.services import device_info
from blatann.nrf import nrf_events


logger = example_utils.setup_logger(level="INFO")


def main(serial_port):
    # Open the BLE Device and suppress spammy log messages
    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    # Set scan duration to 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    logger.info("Scanning for peripherals advertising UUID {}".format(device_info.DIS_SERVICE_UUID))

    target_address = None
    # Start scan and wait for it to complete
    scan_report = ble_device.scanner.start_scan().wait()
    # Search each peer's advertising data for the DIS Service UUID to be advertised
    for report in scan_report.advertising_peers_found:
        if device_info.DIS_SERVICE_UUID in report.advertise_data.service_uuid16s:
            target_address = report.peer_address
            break

    if not target_address:
        logger.info("Did not find peripheral advertising DIS service")
        return

    # Initiate connection and wait for it to finish
    logger.info("Found match: connecting to address {}".format(target_address))
    peer = ble_device.connect(target_address).wait()
    if not peer:
        logger.warning("Timed out connecting to device")
        return

    logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
    # Initiate service discovery and wait for it to complete
    _, event_args = peer.discover_services().wait(10, exception_on_timeout=False)
    logger.info("Service discovery complete! status: {}".format(event_args.status))

    # Find the device info service in the peer's database
    dis = device_info.find_device_info_service(peer.database)
    if not dis:
        logger.info("Failed to find Device Info Service in peripheral database")
        peer.disconnect().wait()
        return

    # Example 1:
    # Iterate through all possible device info characteristics, read the value if present in service
    for char in device_info.CHARACTERISTICS:
        if dis.has(char):
            logger.info("Reading characteristic: {}...".format(char))
            char, event_args = dis.get(char).wait()
            if isinstance(event_args.value, bytes):
                value = event_args.value.decode("utf8")
            else:
                value = event_args.value
            logger.info("Value: {}".format(value))

    # Example 2:
    # Read specific characteristics, if present in the service
    if dis.has_software_revision:
        char, event_args = dis.get_software_revision().wait()
        sw_version = event_args.value
        logger.info("Software Version: {}".format(sw_version.decode("utf8")))
    if dis.has_pnp_id:
        char, event_args = dis.get_pnp_id().wait()
        pnp_id = event_args.value  # type: device_info.PnpId
        logger.info("Vendor ID: {}".format(pnp_id.vendor_id))
    if dis.has_system_id:
        char, event_args = dis.get_system_id().wait()
        system_id = event_args.value  # type: device_info.SystemId
        logger.info("System ID: {}".format(system_id))

    # Disconnect and close device
    peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM9")
