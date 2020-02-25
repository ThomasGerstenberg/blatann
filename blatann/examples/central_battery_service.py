"""
This example demonstrates reading and subscribing to a peripheral's Battery service to get
updates on the peripheral's current battery levels.
The operations here are programmed in a procedural manner.

This can be used alongside any peripheral which implements the Battery Service and
advertises the 16-bit Battery Service UUID.
The peripheral_battery_service example can be used with this.
"""
import time
from blatann import BleDevice
from blatann.utils import setup_logger
from blatann.services import battery
from blatann.nrf import nrf_events


logger = setup_logger(level="INFO")


def on_battery_level_update(battery_service, event_args):
    """
    :param battery_service:
    :type event_args: blatann.event_args.DecodedReadCompleteEventArgs
    """
    battery_percent = event_args.value
    logger.info("Battery: {}%".format(battery_percent))


def main(serial_port):
    # Open the BLE Device and suppress spammy log messages
    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    ble_device.open()

    # Set scan duration for 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    logger.info("Scanning for peripherals advertising UUID {}".format(battery.BATTERY_SERVICE_UUID))

    target_address = None
    # Start scan and wait for it to complete
    scan_report = ble_device.scanner.start_scan().wait()
    # Search each peer's advertising data for the Battery Service UUID to be advertised
    for report in scan_report.advertising_peers_found:
        if battery.BATTERY_SERVICE_UUID in report.advertise_data.service_uuid16s:
            target_address = report.peer_address
            break

    if not target_address:
        logger.info("Did not find peripheral advertising battery service")
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

    # Find the battery service within the peer's database
    battery_service = battery.find_battery_service(peer.database)
    if not battery_service:
        logger.info("Failed to find Battery Service in peripheral database")
        peer.disconnect().wait()
        return

    # Read out the battery level
    logger.info("Reading battery level...")
    _, event_args = battery_service.read().wait()
    battery_percent = event_args.value
    logger.info("Battery: {}%".format(battery_percent))

    if battery_service.can_enable_notifications:
        battery_service.on_battery_level_updated.register(on_battery_level_update)
        battery_service.enable_notifications().wait()

        wait_duration = 30
        logger.info("Waiting {} seconds for any battery notifications".format(wait_duration))
        time.sleep(wait_duration)

    # Clean up
    logger.info("Disconnecting from peripheral")
    peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM9")
