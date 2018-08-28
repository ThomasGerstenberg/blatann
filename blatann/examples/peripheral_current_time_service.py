from blatann import BleDevice
from blatann.gap import advertising
from blatann.utils import setup_logger
from blatann.services import current_time
from blatann.waitables import GenericWaitable


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

    # Create and add the current time service to the database
    current_time_service = current_time.add_current_time_service(ble_device.database, enable_writes=False,
                                                                 enable_local_time_info=True, enable_reference_info=False)
    current_time_service.configure_automatic()

    # Register listeners for when the client connects and disconnects
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)

    # Advertise the Current Time service
    adv_data = advertising.AdvertisingData(local_name="Current Time", flags=0x06,
                                           service_uuid16s=current_time.CURRENT_TIME_SERVICE_UUID)
    ble_device.advertiser.set_advertise_data(adv_data)

    logger.info("Advertising")
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that waits 5 minutes, then exits
    w = GenericWaitable()
    w.wait(5 * 60, exception_on_timeout=False)

    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM4")
