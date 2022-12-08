import logging
from typing import Union

from blatann.gatt.writer import GattcWriter
from blatann.gatt.reader import GattcReader
from blatann.exceptions import InvalidStateException, InvalidOperationException
from blatann.utils.queued_tasks_manager import QueuedTasksManagerBase
from blatann import gatt
from blatann.utils import SynchronousMonotonicCounter
from blatann.nrf import nrf_events, nrf_types, nrf_driver
from blatann.event_type import EventSource
from blatann.event_args import GattOperationCompleteReason, NotificationCompleteEventArgs

logger = logging.getLogger(__name__)


class _ReadTask(object):
    _id_generator = SynchronousMonotonicCounter(1)

    def __init__(self, handle, callback):
        self.id = _ReadTask._id_generator.next()
        self.handle = handle
        self.data = b""
        self.status = gatt.GattStatusCode.unknown
        self.reason = GattOperationCompleteReason.FAILED
        self.callback = callback

    def notify_complete(self, sender):
        self.callback(sender, self)


class _WriteTask(object):
    _id_generator = SynchronousMonotonicCounter(1)

    def __init__(self, handle, data, callback, with_response=True):
        self.id = _WriteTask._id_generator.next()
        self.handle = handle
        self.data = data
        self.with_response = with_response
        self.status = gatt.GattStatusCode.unknown
        self.reason = GattOperationCompleteReason.FAILED
        self.callback = callback

    def notify_complete(self, sender):
        self.callback(sender, self)


class _ReadWriteManager(QueuedTasksManagerBase[Union[_ReadTask, _WriteTask]]):
    def __init__(self, reader: GattcReader, writer: GattcWriter):
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
        self._reader.peer.driver_event_subscribe(self._on_timeout, nrf_events.GattcEvtTimeout)

    def read(self, handle, callback):
        read_task = _ReadTask(handle, callback)
        self._add_task(read_task)
        return read_task.id

    def write(self, handle, value, callback):
        write_task = _WriteTask(handle, value, callback, True)
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
        failure = self.TaskFailure(GattOperationCompleteReason.FAILED)
        if isinstance(e, nrf_driver.NordicSemiException):
            if e.error_code == nrf_types.NrfError.ble_invalid_conn_handle.value:
                failure.reason = GattOperationCompleteReason.SERVER_DISCONNECTED
                failure.ignore_stack_trace = True
                failure.clear_all = True

        if isinstance(task, _ReadTask):
            task.reason = failure.reason
            task.notify_complete(self)
        elif isinstance(task, _WriteTask):
            task.reason = failure.reason
            task.notify_complete(self)
        return failure

    def _handle_task_cleared(self, task, reason):
        if isinstance(task, _ReadTask):
            task.reason = reason
            task.notify_complete(self)
        elif isinstance(task, _WriteTask):
            task.reason = reason
            task.notify_complete(self)

    def _on_disconnect(self, sender, event_args):
        self._clear_all(GattOperationCompleteReason.SERVER_DISCONNECTED)

    def _on_timeout(self, sender, event_args):
        self._clear_all(GattOperationCompleteReason.TIMED_OUT)

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
        self._pop_task_in_process()
        self._task_completed(self._cur_read_task)

        task.data = event_args.data
        task.status = event_args.status
        task.notify_complete(self)

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
        self._pop_task_in_process()
        self._task_completed(self._cur_write_task)

        task.status = event_args.status
        task.notify_complete(self)


class _WriteWithoutResponseManager(QueuedTasksManagerBase[_WriteTask]):
    _WRITE_OVERHEAD = 3

    def __init__(self, ble_device, peer, hardware_queue_size=1):
        """
        :type ble_device: blatann.device.BleDevice
        :type peer: blatann.peer.Peer
        """
        super(_WriteWithoutResponseManager, self).__init__(hardware_queue_size)
        self.ble_device = ble_device
        self.peer = peer

        self.peer.driver_event_subscribe(self._on_write_tx_complete, nrf_events.GattcEvtWriteCmdTxComplete)

    def write(self, handle, value, callback):
        data_len = len(value)
        if data_len == 0:
            raise ValueError("Data must be at least one byte")
        if data_len > self.peer.mtu_size - self._WRITE_OVERHEAD:
            raise InvalidOperationException(f"Writing data without response must fit within a "
                                            f"single MTU minus the write overhead ({self._WRITE_OVERHEAD} bytes). "
                                            f"MTU: {self.peer.mtu_size}bytes, data: {data_len}bytes")

        write_task = _WriteTask(handle, value, callback, False)
        self._add_task(write_task)
        return write_task.id

    def clear_all(self):
        self._clear_all(GattOperationCompleteReason.QUEUE_CLEARED)

    def _handle_task(self, task: _WriteTask):
        write_operation = nrf_types.BLEGattWriteOperation.write_cmd
        flags = nrf_types.BLEGattExecWriteFlag.unused
        write_params = nrf_types.BLEGattcWriteParams(write_operation, flags, task.handle, task.data, 0)
        self.ble_device.ble_driver.ble_gattc_write(self.peer.conn_handle, write_params)

    def _handle_task_failure(self, task: _WriteTask, e):
        failure = self.TaskFailure(GattOperationCompleteReason.FAILED)
        if isinstance(e, nrf_driver.NordicSemiException):
            if e.error_code == nrf_types.NrfError.ble_invalid_conn_handle.value:
                failure.reason = GattOperationCompleteReason.SERVER_DISCONNECTED
                failure.ignore_stack_trace = True
                failure.clear_all = True

        task.reason = failure.reason
        task.notify_complete(self)
        return failure

    def _handle_task_cleared(self, task: _WriteTask, reason):
        task.reason = reason
        task.notify_complete(self)

    def _on_write_tx_complete(self, driver, event: nrf_events.GattcEvtWriteCmdTxComplete):
        for _ in range(event.count):
            task = self._pop_task_in_process()
            if task:
                task.status = gatt.GattStatusCode.success
                task.notify_complete(self)
                self._task_completed(task)


class GattcOperationManager:
    def __init__(self, ble_device, peer, reader, writer, write_no_response_queue_size=1):
        self._read_write_manager = _ReadWriteManager(reader, writer)
        self._write_no_response_manager = _WriteWithoutResponseManager(ble_device, peer, write_no_response_queue_size)

    def read(self, handle, callback):
        return self._read_write_manager.read(handle, callback)

    def write(self, handle, value, callback, with_response=True):
        if with_response:
            return self._read_write_manager.write(handle, value, callback)
        else:
            return self._write_no_response_manager.write(handle, value, callback)

    def clear_all(self):
        self._read_write_manager.clear_all()
        self._write_no_response_manager.clear_all()


class _Notification(object):
    _id_generator = SynchronousMonotonicCounter(1)

    def __init__(self, characteristic, handle, on_complete, data):
        self.id = _Notification._id_generator.next()
        self.char = characteristic
        self.handle = handle
        self.on_complete = on_complete
        self.data = data

    def notify_complete(self, reason):
        self.on_complete.notify(self.char, NotificationCompleteEventArgs(self.id, self.data, reason))

    @property
    def type(self):
        if self.char.cccd_state == gatt.SubscriptionState.INDICATION:
            return nrf_types.BLEGattHVXType.indication
        elif self.char.cccd_state == gatt.SubscriptionState.NOTIFY:
            return nrf_types.BLEGattHVXType.notification
        else:
            raise InvalidStateException("Client not subscribed")


class _NotificationManager(QueuedTasksManagerBase[_Notification]):
    """
    Handles queuing of notifications to the client
    """

    def __init__(self, ble_device, peer, hardware_queue_size=1, for_indications=False):
        super(_NotificationManager, self).__init__(hardware_queue_size)
        self.ble_device = ble_device
        self.peer = peer
        self._cur_notification = None
        self.ble_device.ble_driver.event_subscribe(self._on_disconnect, nrf_events.GapEvtDisconnected)
        self.ble_device.ble_driver.event_subscribe(self._on_timeout, nrf_events.GattsEvtTimeout)

        if for_indications:
            self.ble_device.ble_driver.event_subscribe(self._on_hvc, nrf_events.GattsEvtHandleValueConfirm)
            self.hvx_type = nrf_types.BLEGattHVXType.indication
        else:
            self.ble_device.ble_driver.event_subscribe(self._on_notify_complete, nrf_events.GattsEvtNotificationTxComplete)
            self.hvx_type = nrf_types.BLEGattHVXType.notification

    def notify(self, characteristic, handle, event_on_complete, data=None):
        notification = _Notification(characteristic, handle, event_on_complete, data)
        self._add_task(notification)
        return notification.id

    def clear_all(self):
        self._clear_all(NotificationCompleteEventArgs.Reason.QUEUE_CLEARED)

    def _handle_task(self, notification: _Notification):
        if not notification.char.client_subscribed:
            notification.notify_complete(NotificationCompleteEventArgs.Reason.CLIENT_UNSUBSCRIBED)
            return True
        hvx_params = nrf_types.BLEGattsHvx(notification.handle, self.hvx_type, notification.data)
        self.ble_device.ble_driver.ble_gatts_hvx(self.peer.conn_handle, hvx_params)

    def _handle_task_failure(self, notification: _Notification, e):
        failure = self.TaskFailure(NotificationCompleteEventArgs.Reason.FAILED)
        if isinstance(e, nrf_driver.NordicSemiException):
            if e.error_code == nrf_types.NrfError.ble_invalid_conn_handle.value:
                failure.reason = NotificationCompleteEventArgs.Reason.CLIENT_DISCONNECTED
                failure.ignore_stack_trace = True
                failure.clear_all = True
            elif e.error_code == nrf_types.NrfError.invalid_state.value:
                failure.reason = GattOperationCompleteReason.CLIENT_UNSUBSCRIBED
                failure.ignore_stack_trace = True
                failure.clear_all = True

        notification.notify_complete(failure.reason)
        return failure

    def _handle_task_cleared(self, notification: _Notification, reason):
        notification.notify_complete(reason)

    def _on_hvc(self, driver, event):
        notification = self._pop_task_in_process()
        if notification:
            notification.notify_complete(NotificationCompleteEventArgs.Reason.SUCCESS)
            self._task_completed(notification)

    def _on_notify_complete(self, driver, event: nrf_events.GattsEvtNotificationTxComplete):
        for _ in range(event.tx_count):
            notification = self._pop_task_in_process()
            if notification:
                notification.notify_complete(NotificationCompleteEventArgs.Reason.SUCCESS)
                self._task_completed(notification)

    def _on_disconnect(self, driver, event):
        self._clear_all(NotificationCompleteEventArgs.Reason.CLIENT_DISCONNECTED)

    def _on_timeout(self, driver, event):
        self._clear_all(NotificationCompleteEventArgs.Reason.TIMED_OUT)


class GattsOperationManager:
    def __init__(self, ble_device, peer, notification_queue_size=1):
        self._notification_manager = _NotificationManager(ble_device, peer, notification_queue_size)
        self._indication_manager = _NotificationManager(ble_device, peer, hardware_queue_size=1, for_indications=True)

    def notify(self, characteristic, handle, event_on_complete, data=None):
        if characteristic.cccd_state == gatt.SubscriptionState.INDICATION:
            manager = self._indication_manager
        elif characteristic.cccd_state == gatt.SubscriptionState.NOTIFY:
            manager = self._notification_manager
        else:
            raise InvalidStateException("Client not subscribed")
        return manager.notify(characteristic, handle, event_on_complete, data)

    def clear_all(self):
        self._notification_manager.clear_all()
        self._indication_manager.clear_all()
