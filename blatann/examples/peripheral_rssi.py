"""
This is a simple example which demonstrates enabling RSSI updates for active connections.
"""
import blatann.peer
from blatann import BleDevice
from blatann.examples import example_utils, constants
from blatann.gap import AdvertisingData
from blatann.waitables import GenericWaitable


logger = example_utils.setup_logger(level="INFO")


def on_rssi_changed(peer, rssi: int):
    """
    Event callback for when the RSSI with the central device changes by
    the configured dBm threshold

    :param peer: The peer object
    :param rssi: The new RSSI for the connection
    """
    logger.info(f"RSSI changed to {rssi}dBm")


def on_connect(peer, event_args):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :type peer: blatann.peer.Client
    :param event_args: None
    """
    if peer:
        logger.info("Starting RSSI reporting")
        # Start reporting RSSI. The RSSI Changed event will be triggered if the dBm delta is >= 5
        # and is sustained for at least 3 RSSI samples. Modify these values to your liking.
        # Setting threshold_dbm=None will disable the on_rssi_changed event and RSSI can be polled using peer.rssi
        peer.start_rssi_reporting(threshold_dbm=5, skip_count=3)


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
    ble_device.configure()
    ble_device.open()

    ble_device.generic_access_service.device_name = "RSSI Example"

    # Setup event callbacks
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.client.on_rssi_changed.register(on_rssi_changed)

    adv_data = AdvertisingData(local_name="RSSI Test", flags=0x06)
    ble_device.advertiser.set_advertise_data(adv_data)

    logger.info("Advertising")
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that will never fire, and wait for some time
    w = GenericWaitable()
    w.wait(60*10, exception_on_timeout=False)  # Keep device active for 10 mins

    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM3")