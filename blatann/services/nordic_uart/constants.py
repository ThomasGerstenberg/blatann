from blatann.uuid import Uuid128

NORDIC_UART_SERVICE_UUID = Uuid128("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")

# TX and RX characteristics are from the perspective of the client. The server will receive on TX and transmit on RX
NORDIC_UART_TX_CHARACTERISTIC_UUID = NORDIC_UART_SERVICE_UUID.new_uuid_from_base(0x0002)
NORDIC_UART_RX_CHARACTERISTIC_UUID = NORDIC_UART_SERVICE_UUID.new_uuid_from_base(0x0003)
# Slight deviation from Nordic's implementation so the client can read the server's characteristic size
NORDIC_UART_FEATURE_CHARACTERISTIC_UUID = NORDIC_UART_SERVICE_UUID.new_uuid_from_base(0x0004)
