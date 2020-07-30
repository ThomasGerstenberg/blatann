Core Classes
============

Below are quick descriptions and links to the primary/core classes that are used to perform the various
Bluetooth operations. This information, including more thorough usage, can be found within example code (:doc:`./examples`)

Events
------

The :class:`~blatann.event_type.Event` type is the basic building block of the blatann library.

Bluetooth operations are inherently asynchronous, thus asynchronous events must be used in order to communicate when things happen.

Almost all of the classes below implement one or more Events which can have multiple handler functions registered to process incoming data.
Event properties are commonly named in the format of ``on_*``, such as ``on_timeout`` or ``on_read_complete``.
The event properties also document the parameter types that the handler should accept. Majority of the events emit two parameters,
a sender parameter, which provides the event source, and an event_args parameter, which provides the data associated with the event.
Those familiar with C#/.NET, this should look very similar.

.. code-block:: python

   def my_handler(sender, event_args):
       # Handle the event
   some_object.on_some_event.register(my_handler)

Waitables
---------

:class:`~blatann.waitables.waitable.Waitable`, :class:`~blatann.waitables.event_waitable.EventWaitable`

Waitables are the solution to providing an API which supports synchronous, procedural code given the asynchronous nature of Bluetooth.
For every asynchronous Bluetooth operation that is performed a ``Waitable`` object is returned which the user can then :meth:`~blatann.waitables.waitable.Waitable.wait` on
to block the current thread until the operation completes.

.. code-block:: python

   sender, event_args = characteristic.read().wait(timeout=5)

.. note::
   Take care to not call ``wait()`` within an event handler as the system will deadlock
   (see Threading section under :doc:`./architecture` for more info).

Asynchronous paradigms are also supported through waitables where the user can register a handler to be called when the operation completes:

.. code-block:: python

   def my_characteristic_read_handler(sender, event_args):
       # Handle read complete
   characteristic.read().then(my_characteristic_read_handler)


BLE Device
----------

The :class:`~blatann.device.BleDevice` represents Nordic Bluetooth microcontroller itself. It is the root object of everything within this library.

To get started, instantiate a ``BleDevice`` and open it:

.. code-block:: python

   from blatann import BleDevice

   ble_device = BleDevice("COM1")
   ble_device.configure()
   ble_device.open()
   # Ready to use

The BLE Device is also responsible for initiating connections to peripheral devices and managing the local GATT database.

Advertising
-----------

The :class:`~blatann.gap.advertising.Advertiser` component is accessed through the ``ble_device.advertiser`` attribute.
It is configured using :class:`~blatann.gap.advertise_data.AdvertisingData` objects to set the payloads to advertise

.. code-block:: python

   from blatann.gap.advertising import AdvertisingData
   adv_data = AdvertisingData(flags=0x06, local_name="My Name")
   scan_data = AdvertisingData(service_uuid16s="123F")
   ble_device.advertiser.set_advertise_data(adv_data, scan_data)
   ble_device.advertiser.start(adv_interval_ms=50)

Scanning
--------

The :class:`~blatann.gap.scanning.Scanner` component is accessed through the ``ble_device.scanner`` attribute.

The scanner output consists of a :class:`~blatann.gap.advertise_data.ScanReportCollection`, which is comprised of
:class:`~blatann.gap.advertise_data.ScanReport` objects that represent advertising packets discovered.

.. code-block:: python

   scan_report_collection = ble_device.scanner.start_scan().wait(timeout=20)

Peer
----

The :class:`~blatann.peer.Peer` class represents a Bluetooth connection to another device.

For connections as a peripheral to a central device, this peer object is static and accessed via the
``ble_device.client`` attribute. For connections as a central to a peripheral device, the peer is created
as a result of :meth:`BleDevice.connect <blatann.device.BleDevice.connect>`.

Regardless of the connection type, the Peer is the basis for any connection-oriented Bluetooth operation,
such as configuring the MTU, discovering databases, reading/writing characteristics, etc.

.. code-block:: python

   # Connect to a peripheral and exchange MTU
   peer = ble_device.connect(peer_address).wait()
   peer.exchange_mtu(144).wait()
   # Exchange the MTU with a client
   ble_device.client.exchange_mtu(183).wait()

Security
--------

The processes for pairing and bonding is managed by a peer's :class:`~blatann.gap.smp.SecurityManager`,
accessed via the ``peer.security`` attribute.

Local GATT Database
-------------------

The :class:`~blatann.gatt.gatts.GattsDatabase` is accessed through the ``ble_device.database`` attribute.
The database holds all of the services and characteristics that can be discovered and interacted with by a client.

:class:`~blatann.gatt.gatts.GattsService` s can be added to the database and :class:`~blatann.gatt.gatts.GattsCharacteristic` s are added to the services.
The primary interaction point is through characteristics, which provides methods for setting values, handling writes, and notifying values to the client.

Remote GATT Database
--------------------

The peer's :class:`~blatann.gatt.gattc.GattcDatabase` is accessed through the ``peer.database`` attribute.
The database is populated through the :meth:`peer.discover_services <blatann.peer.Peer.discover_services>` procedure. From there,
the Peer's :class:`~blatann.gatt.gattc.GattcCharacteristic` s can be read, written, and subscribed to.
