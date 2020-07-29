"""
This example demonstrates using Bluetooth SIG's Battery service as a peripheral.
The peripheral adds the service, then updates the battery level percentage periodically.

This can be used in conjunction with the nRF Connect apps to explore the functionality demonstrated
"""
import time
from blatann import BleDevice
from blatann.gap import advertising
from blatann.utils import setup_logger
from blatann.services import battery


logger = setup_logger(level="INFO")


def on_connect(peer, event_args):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :type peer: blatann.peer.Client
    :param event_args: None
    """
    if peer:
        logger.info("Connected to peer")
    else:
        logger.warning("Connection timed out")


def on_disconnect(peer, event_args):
    """
    Event callback for when the client disconnects from us (or when we disconnect from the client)

    :param peer: The peer that disconnected
    :type peer: blatann.peer.Client
    :param event_args: The event args
    :type event_args: blatann.event_args.DisconnectionEventArgs
    """
    logger.info("Disconnected from peer, reason: {}".format(event_args.reason))


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Create and add the battery service to the database
    battery_service = battery.add_battery_service(ble_device.database, enable_notifications=True)
    battery_service.set_battery_level(100, False)

    # Register listeners for when the client connects and disconnects
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)

    # Leaving security and connection parameters as defaults (don't care)

    # Advertise the Battery Service
    adv_data = advertising.AdvertisingData(local_name="Battery Test", flags=0x06,
                                           service_uuid16s=battery.BATTERY_SERVICE_UUID)
    ble_device.advertiser.set_advertise_data(adv_data)

    logger.info("Advertising")
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    battery_level = 100
    battery_level_decrement_steps = 1
    time_between_steps = 10

    # Decrement the battery level until it runs out
    while battery_level >= 0:
        time.sleep(time_between_steps)
        battery_level -= battery_level_decrement_steps
        logger.info("Updating battery level to {}".format(battery_level))
        battery_service.set_battery_level(battery_level)

    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM13")
