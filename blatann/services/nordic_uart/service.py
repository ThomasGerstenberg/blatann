import logging
from blatann.gatt import MTU_SIZE_DEFAULT, WRITE_BYTE_OVERHEAD
from blatann.gatt.gatts import GattsService, GattsCharacteristicProperties
from blatann.event_type import EventSource, Event
from blatann import exceptions
from blatann.services.ble_data_types import Uint16, BleDataStream
from blatann.services.nordic_uart.constants import *
from blatann.waitables.event_waitable import EventWaitable


logger = logging.getLogger(__name__)


class NordicUartServer(object):
    def __init__(self, service, max_characteristic_size=None):
        """
        :type service: GattsService
        """
        self._service = service
        if max_characteristic_size is None:
            max_characteristic_size = self._service.peer.max_mtu_size - WRITE_BYTE_OVERHEAD

        rx_props = GattsCharacteristicProperties(read=False, write=False, notify=True, indicate=False,
                                                 variable_length=True, max_length=max_characteristic_size)

        self._rx_char = service.add_characteristic(NORDIC_UART_RX_CHARACTERISTIC_UUID, rx_props)

        tx_props = GattsCharacteristicProperties(read=False, write=True, notify=False, indicate=False,
                                                 variable_length=True, max_length=max_characteristic_size)

        self._tx_char = service.add_characteristic(NORDIC_UART_TX_CHARACTERISTIC_UUID, tx_props)

        feature_props = GattsCharacteristicProperties(read=True, write=False, notify=False, indicate=False,
                                                      variable_length=False, max_length=Uint16.byte_count)
        self._feature_char = service.add_characteristic(NORDIC_UART_FEATURE_CHARACTERISTIC_UUID, feature_props,
                                                        Uint16.encode(max_characteristic_size))

        self._on_data_received = EventSource("Data Received", logger)
        self._on_write_complete = EventSource("Write Complete", logger)
        self._tx_char.on_write.register(self._on_write)

    @property
    def on_data_received(self):
        """
        :rtype: Event
        """
        return self._on_data_received

    @property
    def on_write_complete(self):
        """
        :rtype: Event
        """
        return self._rx_char.on_notify_complete

    @property
    def max_write_length(self):
        return self._rx_char.max_length

    def write(self, data):
        if len(data) > self.max_write_length:
            raise ValueError("Can only write max {} bytes at a time".format(self.max_write_length))
        return self._rx_char.notify(data)

    def _on_write(self, characteristic, event_args):
        self._on_data_received.notify(self, event_args.value)

    @classmethod
    def add_to_database(cls, gatts_database, max_characteristic_size=None):
        service = gatts_database.add_service(NORDIC_UART_SERVICE_UUID)
        return cls(service, max_characteristic_size)


class NordicUartClient(object):
    def __init__(self, service):
        """
        :type service: blatann.gatt.gattc.GattcService
        """
        self._service = service
        self._server_characteristic_size = MTU_SIZE_DEFAULT
        self._tx_char = self._service.find_characteristic(NORDIC_UART_TX_CHARACTERISTIC_UUID)
        self._rx_char = self._service.find_characteristic(NORDIC_UART_RX_CHARACTERISTIC_UUID)
        self._feature_char = self._service.find_characteristic(NORDIC_UART_FEATURE_CHARACTERISTIC_UUID)
        self._init_complete_event = EventSource("Init Complete", logger)
        self._on_data_received = EventSource("Data Received", logger)
        self._on_write_complete = EventSource("Write Complete", logger)

    @property
    def on_data_received(self):
        """
        :rtype: Event
        """
        return self._on_data_received

    @property
    def on_write_complete(self):
        """
        :rtype: Event
        """
        return self._tx_char.on_write_complete

    @property
    def max_write_length(self):
        return self._server_characteristic_size

    @property
    def is_initialized(self):
        return self._rx_char.subscribed

    def initialize(self):
        self._rx_char.subscribe(self._on_notify_received).then(self._check_feature_characteristic)
        return EventWaitable(self._init_complete_event)

    def write(self, data):
        if not self.is_initialized:
            raise exceptions.InvalidStateException("Service must be initialized before write")
        if len(data) > self.max_write_length:
            raise ValueError("Can only write max {} bytes at a time".format(self.max_write_length))
        return self._tx_char.write(data)

    def _check_feature_characteristic(self, characteristic, event_args):
        if not self._feature_char:
            self._init_complete_event.notify(self, event_args.value)
        else:
            self._feature_char.read().then(self._process_feature_value)

    def _process_feature_value(self, characteristic, event_args):
        self._server_characteristic_size = Uint16.decode(BleDataStream(event_args.value))
        self._init_complete_event.notify(self, None)

    def _on_notify_received(self, characteristic, event_args):
        self._on_data_received.notify(self, event_args.value)

    @classmethod
    def find_in_database(cls, gattc_database):
        """
        :type gattc_database: blatann.gatt.gattc.GattcDatabase
        :rtype: NordicUartClient
        """
        service = gattc_database.find_service(NORDIC_UART_SERVICE_UUID)
        if service:
            return cls(service)
