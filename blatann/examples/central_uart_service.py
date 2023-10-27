"""
This example implements Nordic's custom UART service and demonstrates how to configure the MTU size.
It is configured to use an MTU size based on the Data Length Extensions feature of BLE for maximum throughput.
This is compatible with the peripheral_uart_service example.

This is a simple example which just echos back any data that the client sends to it.
"""
from builtins import input
from blatann import BleDevice
from blatann.nrf import nrf_events
from blatann.utils import setup_logger
from blatann.services import nordic_uart
from blatann.gatt import MTU_SIZE_FOR_MAX_DLE


logger = setup_logger(level="DEBUG")


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


def on_mtu_size_update(peer, event_args):
    """
    Callback for when the peer's MTU size has been updated/negotiated

    :param peer: The peer the MTU was updated on
    :type peer: blatann.peer.Client
    :type event_args: blatann.event_args.MtuSizeUpdatedEventArgs
    """
    logger.info("MTU size updated from {} to {}".format(event_args.previous_mtu_size, event_args.current_mtu_size))


def on_data_rx(service, data):
    """
    Called whenever data is received on the RX line of the Nordic UART Service

    :param service: the service the data was received from
    :type service: nordic_uart.service.NordicUartClient
    :param data: The data that was received
    :type data: bytes
    """
    logger.info("Received data (len {}): '{}'".format(len(data), data))


def main(serial_port):
    # Open the BLE Device and suppress spammy log messages
    ble_device = BleDevice(serial_port)
    ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
    # Configure the BLE device to support MTU sizes which allow the max data length extension PDU size
    # Note this isn't 100% necessary as the default configuration sets the max to this value also
    ble_device.configure(att_mtu_max_size=MTU_SIZE_FOR_MAX_DLE)
    ble_device.open()

    # Set scan duration for 4 seconds
    ble_device.scanner.set_default_scan_params(timeout_seconds=4)
    ble_device.set_default_peripheral_connection_params(7.5, 15, 4000)
    logger.info("Scanning for peripherals advertising UUID {}".format(nordic_uart.NORDIC_UART_SERVICE_UUID))

    target_address = None
    # Start scan and wait for it to complete
    scan_report = ble_device.scanner.start_scan().wait()
    # Search each peer's advertising data for the Nordic UART Service UUID to be advertised
    for report in scan_report.advertising_peers_found:
        if nordic_uart.NORDIC_UART_SERVICE_UUID in report.advertise_data.service_uuid128s and report.device_name == "Nordic UART Server":
            target_address = report.peer_address
            break

    if not target_address:
        logger.info("Did not find peripheral advertising Nordic UART service")
        return

    # Initiate connection and wait for it to finish
    logger.info("Found match: connecting to address {}".format(target_address))
    peer = ble_device.connect(target_address).wait()
    if not peer:
        logger.warning("Timed out connecting to device")
        return

    logger.info("Connected, conn_handle: {}".format(peer.conn_handle))

    logger.info("Exchanging MTU")
    peer.exchange_mtu(peer.max_mtu_size).wait(10)
    logger.info("MTU Exchange complete, discovering services")

    # Initiate service discovery and wait for it to complete
    _, event_args = peer.discover_services().wait(exception_on_timeout=False)
    logger.info("Service discovery complete! status: {}".format(event_args.status))

    uart_service = nordic_uart.find_nordic_uart_service(peer.database)
    if not uart_service:
        logger.info("Failed to find Nordic UART service in peripheral database")
        peer.disconnect().wait()
        ble_device.close()
        return

    # Initialize the service
    uart_service.initialize().wait(5)
    uart_service.on_data_received.register(on_data_rx)

    while True:
        data = input("Enter data to send to peripheral (q to exit): ")
        if data == "q":
            break
        uart_service.write(data).wait(10)

    peer.disconnect().wait()
    ble_device.close()


if __name__ == '__main__':
    main("COM9")



