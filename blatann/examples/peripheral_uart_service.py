"""
This example implements Nordic's custom UART service and demonstrates how to configure the MTU size.
It is configured to use an MTU size based on the Data Length Extensions feature of BLE for maximum throughput.
This is compatible with the nRF Connect app (Android version tested) and the central_uart_service example.

This is a simple example which just echos back any data that the client sends to it.
"""
from blatann import BleDevice
from blatann.gap import advertising
from blatann.utils import setup_logger
from blatann.services import nordic_uart
from blatann.gatt import MTU_SIZE_FOR_MAX_DLE
from blatann.waitables import GenericWaitable


logger = setup_logger(level="DEBUG")


def on_connect(peer, event_args):
    """
    Event callback for when a central device connects to us

    :param peer: The peer that connected to us
    :type peer: blatann.peer.Client
    :param event_args: None
    """
    if peer:
        logger.info("Connected to peer, initiating MTU exchange")
        peer.exchange_mtu()
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


def on_mtu_size_update(peer, event_args):
    """
    Callback for when the peer's MTU size has been updated/negotiated

    :param peer: The peer the MTU was updated on
    :type peer: blatann.peer.Client
    :type event_args: blatann.event_args.MtuSizeUpdatedEventArgs
    """
    logger.info("MTU size updated from {} to {}".format(event_args.previous_mtu_size, event_args.current_mtu_size))
    # Request that the connection parameters be re-negotiated using our preferred parameters
    peer.update_connection_parameters()


def on_data_rx(service, data):
    """
    Called whenever data is received on the RX line of the Nordic UART Service

    :param service: the service the data was received from
    :type service: nordic_uart.service.NordicUartServer
    :param data: The data that was received
    :type data: bytes
    """
    logger.info("Received data (len {}): '{}'".format(len(data), data))
    logger.info("Echoing data back to client")
    # Echo it back to the client
    service.write(data)


def on_tx_complete(service, event_args):
    logger.info("Write Complete")


def main(serial_port):
    ble_device = BleDevice(serial_port)
    # Configure the BLE device to support MTU sizes which allow the max data length extension PDU size
    # Note this isn't 100% necessary as the default configuration sets the max to this value also
    ble_device.configure(att_mtu_max_size=MTU_SIZE_FOR_MAX_DLE)
    ble_device.open()

    # Create and add the Nordic UART service
    nus = nordic_uart.add_nordic_uart_service(ble_device.database)
    nus.on_data_received.register(on_data_rx)
    nus.on_write_complete.register(on_tx_complete)

    # Register listeners for when the client connects and disconnects
    ble_device.client.on_connect.register(on_connect)
    ble_device.client.on_disconnect.register(on_disconnect)
    ble_device.client.on_mtu_size_updated.register(on_mtu_size_update)

    # Configure the client to prefer the max MTU size
    ble_device.client.preferred_mtu_size = ble_device.max_mtu_size
    ble_device.client.set_connection_parameters(7.5, 15, 4000)

    # Advertise the service UUID
    adv_data = advertising.AdvertisingData(flags=0x06, local_name="Nordic UART Server")
    scan_data = advertising.AdvertisingData(service_uuid128s=nordic_uart.NORDIC_UART_SERVICE_UUID)

    ble_device.advertiser.set_advertise_data(adv_data, scan_data)

    logger.info("Advertising")

    ble_device.advertiser.start(timeout_sec=0, auto_restart=True)

    # Create a waitable that waits 5 minutes then exits
    w = GenericWaitable()
    try:
        w.wait(5 * 60, exception_on_timeout=False)
    except KeyboardInterrupt:
        pass
    finally:
        ble_device.close()


if __name__ == '__main__':
    main("COM7")
