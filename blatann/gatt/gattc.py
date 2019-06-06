import logging
import threading

from blatann import gatt
from blatann.event_type import EventSource, Event
from blatann.gatt.reader import GattcReader
from blatann.gatt.writer import GattcWriter
from blatann.nrf import nrf_types, nrf_events
from blatann.waitables.event_waitable import EventWaitable, IdBasedEventWaitable
from blatann.exceptions import InvalidOperationException, InvalidStateException
from blatann.event_args import *
from blatann.utils.queued_tasks_manager import QueuedTasksManagerBase

logger = logging.getLogger(__name__)


class GattcCharacteristic(gatt.Characteristic):
    def __init__(self, ble_device, peer, read_write_manager, uuid, properties,
                 declaration_handle, value_handle, cccd_handle=None):
        """
        :type ble_device: blatann.BleDevice
        :type peer: blatann.peer.Peripheral
        :type read_write_manager: _ReadWriteManager
        :type uuid: blatann.uuid.Uuid
        :type properties: gatt.CharacteristicProperties
        :param declaration_handle:
        :param value_handle:
        :param cccd_handle:
        """
        super(GattcCharacteristic, self).__init__(ble_device, peer, uuid, properties)
        self.declaration_handle = declaration_handle
        self.value_handle = value_handle
        self.cccd_handle = cccd_handle
        self._manager = read_write_manager
        self._value = ""

        self._on_notification_event = EventSource("On Notification", logger)
        self._on_read_complete_event = EventSource("On Read Complete", logger)
        self._on_write_complete_event = EventSource("Write Complete", logger)
        self._on_cccd_write_complete_event = EventSource("CCCD Write Complete", logger)

        self.peer.driver_event_subscribe(self._on_indication_notification, nrf_events.GattcEvtHvx)
        self._manager.on_write_complete.register(self._write_complete)
        self._manager.on_read_complete.register(self._read_complete)

    """
    Properties
    """

    @property
    def value(self):
        """
        The current value of the characteristic

        :return: The last known value of the characteristic
        """
        return self._value

    @property
    def readable(self):
        """
        Gets if the characteristic can be read from
        """
        return self._properties.read

    @property
    def writable(self):
        """
        Gets if the characteristic can be written to
        """
        return self._properties.write

    @property
    def subscribable(self):
        """
        Gets if the characteristic can be subscribed to
        """
        return self._properties.notify or self._properties.indicate

    @property
    def subscribed(self):
        """
        Gets if the characteristic is currently subscribed to
        """
        return self.cccd_state != gatt.SubscriptionState.NOT_SUBSCRIBED

    """
    Events
    """

    @property
    def on_read_complete(self):
        return self._on_read_complete_event

    @property
    def on_write_complete(self):
        return self._on_write_complete_event

    """
    Public Methods
    """

    def subscribe(self, on_notification_handler, prefer_indications=False):
        """
        Subscribes to the characteristic's indications or notifications, depending on what's available and the
        prefer_indications setting. Returns a Waitable that executes when the subscription on the peripheral finishes.

        The Waitable returns two parameters: (GattcCharacteristic this, SubscriptionWriteCompleteEventArgs event args)

        :param on_notification_handler: The handler to be called when an indication or notification is received from
            the peripheral. Must take three parameters: (GattcCharacteristic this, gatt.GattNotificationType, bytearray data)
        :param prefer_indications: If the peripheral supports both indications and notifications,
            will subscribe to indications instead of notifications
        :return: A Waitable that will fire when the subscription finishes
        :rtype: blatann.waitables.EventWaitable
        :raises: InvalidOperationException if the characteristic cannot be subscribed to
            (characteristic does not support indications or notifications)
        """
        if not self.subscribable:
            raise InvalidOperationException("Cannot subscribe to Characteristic {}".format(self.uuid))
        if prefer_indications and self._properties.indicate or not self._properties.notify:
            value = gatt.SubscriptionState.INDICATION
        else:
            value = gatt.SubscriptionState.NOTIFY
        self._on_notification_event.register(on_notification_handler)

        write_id = self._manager.write(self.cccd_handle, gatt.SubscriptionState.to_buffer(value))
        return IdBasedEventWaitable(self._on_cccd_write_complete_event, write_id)

    def unsubscribe(self):
        """
        Unsubscribes from indications and notifications from the characteristic and clears out all handlers
        for the characteristic's on_notification event handler. Returns a Waitable that executes when the unsubscription
        finishes.

        The Waitable returns two parameters: (GattcCharacteristic this, SubscriptionWriteCompleteEventArgs event args)

        :return: A Waitable that will fire when the unsubscription finishes
        :rtype: blatann.waitables.EventWaitable
        """
        if not self.subscribable:
            raise InvalidOperationException("Cannot subscribe to Characteristic {}".format(self.uuid))
        value = gatt.SubscriptionState.NOT_SUBSCRIBED
        write_id = self._manager.write(self.cccd_handle, gatt.SubscriptionState.to_buffer(value))
        self._on_notification_event.clear_handlers()

        return IdBasedEventWaitable(self._on_cccd_write_complete_event, write_id)

    def read(self):
        """
        Initiates a read of the characteristic and returns a Waitable that executes when the read finishes with
        the data read.

        The Waitable returns two parameters: (GattcCharacteristic this, ReadCompleteEventArgs event args)

        :return: A waitable that will fire when the read finishes
        :rtype: blatann.waitables.EventWaitable
        :raises: InvalidOperationException if characteristic not readable
        """
        if not self.readable:
            raise InvalidOperationException("Characteristic {} is not readable".format(self.uuid))
        read_id = self._manager.read(self.value_handle)
        return IdBasedEventWaitable(self._on_read_complete_event, read_id)

    def write(self, data):
        """
        Initiates a write of the data provided to the characteristic and returns a Waitable that executes
        when the write completes.

        The Waitable returns two parameters: (GattcCharacteristic this, WriteCompleteEventArgs event args)

        :param data: The data to write. Can be a string, bytearray, or anything that can be converted to a bytearray
        :return: A waitable that returns when the write finishes
        :rtype: blatann.waitables.EventWaitable
        :raises: InvalidOperationException if characteristic is not writable
        """
        if not self.writable:
            raise InvalidOperationException("Characteristic {} is not writable".format(self.uuid))
        write_id = self._manager.write(self.value_handle, bytearray(data))
        return IdBasedEventWaitable(self._on_write_complete_event, write_id)

    """
    Event Handlers
    """

    def _read_complete(self, sender, event_args):
        """
        Handler for _ReadWriteManager.on_read_complete.
        Dispatches the on_read_complete event and updates the internal value if read was successful

        :param sender: The reader that the read completed on
        :type sender: _ReadWriteManager
        :param event_args: The event arguments
        :type event_args: _ReadTask
        """
        if event_args.handle == self.value_handle:
            if event_args.status == nrf_types.BLEGattStatusCode.success:
                self._value = event_args.data
            args = ReadCompleteEventArgs(event_args.id, self._value, event_args.status, event_args.reason)
            self._on_read_complete_event.notify(self, args)

    def _write_complete(self, sender, event_args):
        """
        Handler for _ReadWriteManager.on_write_complete. Dispatches on_write_complete or on_cccd_write_complete
        depending on the handle the write finished on.

        :param sender: The writer that the write completed on
        :type sender: _ReadWriteManager
        :param event_args: The event arguments
        :type event_args: _WriteTask
        """
        # Success, update the local value
        if event_args.handle == self.value_handle:
            if event_args.status == nrf_types.BLEGattStatusCode.success:
                self._value = event_args.data
            args = WriteCompleteEventArgs(event_args.id, self._value, event_args.status, event_args.reason)
            self._on_write_complete_event.notify(self, args)
        elif event_args.handle == self.cccd_handle:
            if event_args.status == nrf_types.BLEGattStatusCode.success:
                self.cccd_state = gatt.SubscriptionState.from_buffer(bytearray(event_args.data))
            args = SubscriptionWriteCompleteEventArgs(event_args.id, self.cccd_state,
                                                      event_args.status, event_args.reason)
            self._on_cccd_write_complete_event.notify(self, args)

    def _on_indication_notification(self, driver, event):
        """
        Handler for GattcEvtHvx. Dispatches the on_notification_event to listeners

        :type event: nrf_events.GattcEvtHvx
        """
        if event.conn_handle != self.peer.conn_handle or event.attr_handle != self.value_handle:
            return

        is_indication = False
        if event.hvx_type == nrf_events.BLEGattHVXType.indication:
            is_indication = True
            self.ble_device.ble_driver.ble_gattc_hv_confirm(event.conn_handle, event.attr_handle)
        self._value = bytearray(event.data)
        self._on_notification_event.notify(self, NotificationReceivedEventArgs(self._value, is_indication))

    """
    Factory methods
    """

    @classmethod
    def from_discovered_characteristic(cls, ble_device, peer, read_write_manager, nrf_characteristic):
        """
        Internal factory method used to create a new characteristic from a discovered nRF Characteristic

        :type nrf_characteristic: nrf_types.BLEGattCharacteristic
        """
        char_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_characteristic.uuid)
        properties = gatt.CharacteristicProperties.from_nrf_properties(nrf_characteristic.char_props)
        cccd_handle_list = [d.handle for d in nrf_characteristic.descs
                            if d.uuid == nrf_types.BLEUUID.Standard.cccd]
        cccd_handle = cccd_handle_list[0] if cccd_handle_list else None
        return GattcCharacteristic(ble_device, peer, read_write_manager, char_uuid, properties,
                                   nrf_characteristic.handle_decl, nrf_characteristic.handle_value, cccd_handle)


class GattcService(gatt.Service):
    @property
    def characteristics(self):
        """
        Gets the list of characteristics within the service

        :rtype: list of GattcCharacteristic
        """
        return self._characteristics

    def find_characteristic(self, characteristic_uuid):
        """
        Finds the characteristic matching the given UUID inside the service. If not found, returns None

        :param characteristic_uuid: The UUID of the characteristic to find
        :type characteristic_uuid: blatann.uuid.Uuid
        :return: The characteristic if found, otherwise None
        :rtype: GattcCharacteristic
        """
        for c in self.characteristics:
            if c.uuid == characteristic_uuid:
                return c

    @classmethod
    def from_discovered_service(cls, ble_device, peer, read_write_manager, nrf_service):
        """
        Internal factory method used to create a new service from a discovered nRF Service.
        Also takes care of creating and adding all characteristics within the service

        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peripheral
        :type read_write_manager: _ReadWriteManager
        :type nrf_service: nrf_types.BLEGattService
        """
        service_uuid = ble_device.uuid_manager.nrf_uuid_to_uuid(nrf_service.uuid)
        service = GattcService(ble_device, peer, service_uuid, gatt.ServiceType.PRIMARY,
                               nrf_service.start_handle, nrf_service.end_handle)
        for c in nrf_service.chars:
            char = GattcCharacteristic.from_discovered_characteristic(ble_device, peer, read_write_manager, c)
            service.characteristics.append(char)
        return service


class GattcDatabase(gatt.GattDatabase):
    """
    Represents a remote GATT Database which lives on a connected peripheral. Contains all discovered services,
    characteristics, and descriptors
    """
    def __init__(self, ble_device, peer):
        super(GattcDatabase, self).__init__(ble_device, peer)
        self._writer = GattcWriter(ble_device, peer)
        self._reader = GattcReader(ble_device, peer)
        self._read_write_manager = _ReadWriteManager(self._reader, self._writer)

    @property
    def services(self):
        """
        :rtype: list of GattcService
        """
        return self._services

    def find_service(self, service_uuid):
        """
        Finds the characteristic matching the given UUID inside the database. If not found, returns None

        :param service_uuid: The UUID of the service to find
        :type service_uuid: blatann.uuid.Uuid
        :return: The service if found, otherwise None
        :rtype: GattcService
        """
        for s in self.services:
            if s.uuid == service_uuid:
                return s

    def find_characteristic(self, characteristic_uuid):
        """
        Finds the characteristic matching the given UUID inside the database. If not found, returns None

        :param characteristic_uuid: The UUID of the characteristic to find
        :type characteristic_uuid: blatann.uuid.Uuid
        :return: The characteristic if found, otherwise None
        :rtype: GattcCharacteristic
        """
        for c in self.iter_characteristics():
            if c.uuid == characteristic_uuid:
                return c

    def iter_characteristics(self):
        """
        Iterates through all the characteristics in the database

        :return: An iterable of the characterisitcs in the database
        :rtype: collections.Iterable[GattcCharacteristic]
        """
        for s in self.services:
            for c in s.characteristics:
                yield c

    def add_discovered_services(self, nrf_services):
        """
        Adds the discovered NRF services from the service_discovery module.
        Used for internal purposes primarily.

        :param nrf_services: The discovered services with all the characteristics and descriptors
        :type nrf_services: list of nrf_types.BLEGattService
        """
        for service in nrf_services:
            self.services.append(GattcService.from_discovered_service(self.ble_device, self.peer,
                                                                      self._read_write_manager, service))


class _ReadTask(object):
    _id_counter = 1
    _lock = threading.Lock()

    def __init__(self, handle):
        with _ReadTask._lock:
            self.id = _ReadTask._id_counter
            _ReadTask._id_counter += 1
        self.handle = handle
        self.data = ""
        self.status = gatt.GattStatusCode.unknown
        self.reason = GattOperationCompleteReason.FAILED


class _WriteTask(object):
    _id_counter = 1
    _lock = threading.Lock()

    def __init__(self, handle, data):
        with _WriteTask._lock:
            self.id = _WriteTask._id_counter
            _WriteTask._id_counter += 1
        self.handle = handle
        self.data = data
        self.status = gatt.GattStatusCode.unknown
        self.reason = GattOperationCompleteReason.FAILED


class _ReadWriteManager(QueuedTasksManagerBase):
    def __init__(self, reader, writer):
        """
        :type reader: GattcReader
        :type writer: GattcWriter
        """
        super(_ReadWriteManager, self).__init__()
        self._reader = reader
        self._writer = writer
        self._reader.peer.on_disconnect.register(self._on_disconnect)
        self._cur_read_task = None
        self._cur_write_task = None
        self.on_read_complete = EventSource("Gattc Read Complete", logger)
        self.on_write_complete = EventSource("Gattc Write Complete", logger)
        self._reader.on_read_complete.register(self._read_complete)
        self._writer.on_write_complete.register(self._write_complete)

    def read(self, handle):
        read_task = _ReadTask(handle)
        self._add_task(read_task)
        return read_task.id

    def write(self, handle, value):
        write_task = _WriteTask(handle, value)
        self._add_task(write_task)
        return write_task.id

    def clear_all(self):
        self._clear_all(GattOperationCompleteReason.QUEUE_CLEARED)

    def _handle_task(self, task):
        if isinstance(task, _ReadTask):
            self._reader.read(task.handle)
            self._cur_read_task = task
        elif isinstance(task, _WriteTask):
            self._writer.write(task.handle, task.data)
            self._cur_write_task = task
        else:
            return True

    def _handle_task_failure(self, task, e):
        if isinstance(task, _ReadTask):
            self.on_read_complete.notify(self, task)
        elif isinstance(task, _WriteTask):
            self.on_write_complete.notify(self, task)

    def _handle_task_cleared(self, task, reason):
        if isinstance(task, _ReadTask):
            task.reason = reason
            self.on_read_complete.notify(self, task)
        elif isinstance(task, _WriteTask):
            task.reason = reason
            self.on_write_complete.notify(self, task)

    def _on_disconnect(self, sender, event_args):
        self._clear_all(GattOperationCompleteReason.SERVER_DISCONNECTED)

    def _read_complete(self, sender, event_args):
        """
        Handler for GattcReader.on_read_complete.
        Dispatches the on_read_complete event and updates the internal value if read was successful

        :param sender: The reader that the read completed on
        :type sender: blatann.gatt.reader.GattcReader
        :param event_args: The event arguments
        :type event_args: blatann.gatt.reader.GattcReadCompleteEventArgs
        """
        task = self._cur_read_task
        self._task_completed(self._cur_read_task)

        task.data = event_args.data
        task.status = event_args.status
        self.on_read_complete.notify(sender, task)

    def _write_complete(self, sender, event_args):
        """
        Handler for GattcWriter.on_write_complete. Dispatches on_write_complete or on_cccd_write_complete
        depending on the handle the write finished on.

        :param sender: The writer that the write completed on
        :type sender: blatann.gatt.writer.GattcWriter
        :param event_args: The event arguments
        :type event_args: blatann.gatt.writer.GattcWriteCompleteEventArgs
        """
        task = self._cur_write_task
        self._task_completed(self._cur_write_task)

        task.status = event_args.status
        self.on_write_complete.notify(sender, task)
