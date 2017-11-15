from blatann import BleDevice
from blatann.examples import example_utils
from blatann.services import device_info
from blatann.nrf import nrf_events


logger = example_utils.setup_logger(level="INFO")


def main(serial_port):
    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    logger.info("Scanning for peripherals advertising UUID {}".format(device_info.DIS_SERVICE_UUID))

    target_address = None
    scan_report = ble_device.scanner.start_scan().wait()
    for report in scan_report.advertising_peers_found:
        # Look for the Device Info Service UUID to be advertised
        if device_info.DIS_SERVICE_UUID in report.advertise_data.service_uuid16s:
            target_address = report.peer_address
            break

    if not target_address:
        logger.info("Did not find target peripheral")
        return

    logger.info("Found match: connecting to address {}".format(target_address))
    peer = ble_device.connect(target_address).wait()
    if not peer:
        logger.warning("Timed out connecting to device")
        return

    logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
    _, event_args = peer.discover_services().wait(10, exception_on_timeout=False)
    logger.info("Service discovery complete! status: {}".format(event_args.status))

    dis = device_info.find_device_info_service(peer.database)
    if not dis:
        logger.info("Failed to find Device Info Service in peripheral database")
        peer.disconnect().wait()
        return

    # Iterate through all possible device info characteristics, read the value if defined
    for char in device_info.CHARACTERISTICS:
        if dis.has(char):
            logger.info("Reading characteristic: {}...".format(char))
            char, event_args = dis.get(char).wait()
            logger.info("Value: {}".format(event_args.value))

    # Examples of reading individual characteristics (if present)

    if dis.has_software_revision:
        char, event_args = dis.get_software_revision().wait()
        sw_version = event_args.value
        logger.info("Software Version: {}".format(sw_version))
    if dis.has_pnp_id:
        char, event_args = dis.get_pnp_id().wait()
        pnp_id = event_args.value
        logger.info("Vendor ID: {}".format(pnp_id.vendor_id))
    if dis.has_system_id:
        char, event_args = dis.get_system_id().wait()
        system_id = event_args.value
        logger.info("System ID: {}".format(system_id))

    peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM4")
