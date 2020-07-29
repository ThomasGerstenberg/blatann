"""
This example shows how to implement a Device Info Service on a peripheral.

This example can be used alongside the central_device_info_service example running on another nordic device,
or using the Nordic nRF Connect app to connect and browse the peripheral's service data
"""
from blatann import BleDevice
from blatann.examples import example_utils
from blatann.gap import advertising
from blatann.services import device_info
from blatann.waitables import GenericWaitable

logger = example_utils.setup_logger(level="DEBUG")


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
    # Create and open te device
    ble_device = BleDevice(serial_port)
    ble_device.open()

    # Create and add the Device Info Service to the database
    dis = device_info.add_device_info_service(ble_device.database)

    # Set some characteristics in the DIS. The service only contains characteristics which
    # have values set. The other ones are not present
    dis.set_software_revision("14.2.1")
    dis.set_hardware_revision("A")
    dis.set_firmware_revision("1.0.4")
    dis.set_serial_number("AB1234")
    pnp_id = device_info.PnpId(device_info.PnpVendorSource.bluetooth_sig, 0x0058, 0x0002, 0x0013)
    dis.set_pnp_id(pnp_id)

    # Initiate the advertising data. Advertise the name and DIS service UUID
    name = "Peripheral DIS"
    adv_data = advertising.AdvertisingData(local_name=name, service_uuid16s=device_info.DIS_SERVICE_UUID)
    ble_device.advertiser.set_advertise_data(adv_data)

    # Start advertising
    logger.info("Advertising")
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that will never fire, and wait for some time
    w = GenericWaitable()
    w.wait(60*30, exception_on_timeout=False)  # Keep device active for 30 mins

    # Cleanup
    logger.info("Done")
    ble_device.close()


if __name__ == '__main__':
    main("COM13")
