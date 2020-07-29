"""
This example demonstrates using Bluetooth SIG's defined Current Time service as a peripheral.
"""
import binascii
import datetime
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


def on_current_time_write(characteristic, event_args):
    """
    Callback registered to be triggered whenever the Current Time characteristic is written to

    :param characteristic:
    :param event_args: The write event args
    :type event_args: blatann.event_args.DecodedWriteEventArgs
    """
    # event_args.value is of type current_time.CurrentTime
    logger.info("Current time written to, new value: {}. "
                "Raw: {}".format(event_args.value, binascii.hexlify(event_args.raw_value)))


def on_local_time_info_write(characteristic, event_args):
    """
    Callback registered to be triggered whenever the Local Time Info characteristic is written to

    :param characteristic:
    :param event_args: The write event args
    :type event_args: blatann.event_args.DecodedWriteEventArgs
    """
    # event_args.value is of type current_time.LocalTimeInfo
    logger.info("Local Time info written to, new value: {}. "
                "Raw: {}".format(event_args.value, binascii.hexlify(event_args.raw_value)))


def main(serial_port):
    # Create and open the device
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Create and add the current time service to the database.
    # Tweak the flags below to change how the service is set up
    current_time_service = current_time.add_current_time_service(ble_device.database,
                                                                 enable_writes=True,
                                                                 enable_local_time_info=True,
                                                                 enable_reference_info=False)

    # Register handlers for when the characteristics are written to.
    # These will only be triggered if enable_writes above is true
    current_time_service.on_current_time_write.register(on_current_time_write)
    current_time_service.on_local_time_info_write.register(on_local_time_info_write)

    # Demo of the different ways to manually or automatically control the reported time

    # Example 1: Automatically reference system time.
    #            All logic is handled within the service and reports the time whenever the characteristic is read
    # Example 2: Manually report the time 1 day behind using callback method.
    #            Register a user-defined callback to retrieve the current time to report back to the client
    # Example 3: Manually report the time 1 hour ahead by setting the base time
    #            Set the characteristic's base time to 1 day ahead and allow the service to auto-increment from there
    example_mode = 1

    if example_mode == 1:
        # configure_automatic() also sets up the Local Time characteristic (if enabled)
        # to just set the automatic time and leave Local Time unconfigured, use set_time() with no parameters
        current_time_service.configure_automatic()
    elif example_mode == 2:
        def on_time_read():
            d = datetime.datetime.now() - datetime.timedelta(days=1)
            logger.info("Getting time: {}".format(d))
            return d
        current_time_service.set_time(characteristic_read_callback=on_time_read)
    elif example_mode == 3:
        base_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        current_time_service.set_time(base_time)

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
    main("COM13")
