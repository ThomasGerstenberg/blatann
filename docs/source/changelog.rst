Changelog
=========

v0.3.3
------

v0.3.3 fixes a couple issues and adds some enhancements to the security manager.

**Highlights**

- Adds handling for peripheral-initiated security/pairings

- Adds finer control over accepting/rejecting pairing requests based on the peer's role, whether or not it's already bonded, etc.

- Adds more events and properties to expose the connection's security state

- Adds method to delete a connected peer's bonding data for future connections


**Fixes**

- Fixes issue where the length of the scan response payload was not correctly being checked against the maximum 31-byte length

- Fixes issue that was not allowing central devices to initiate encryption to an already-bonded peripheral device

- Fixes issue that wasn't allowing time to be read from the Current Time service as a client

**Changes**

- Advertising payloads received that are padded with 0's at the end are now ignored and do not produce spammy logs

- Adds a device-level method to set the default security level to use for all subsequent connections to peripheral devices

- Adds a ``name`` property to the ``Peer`` class. This is auto-populated from the scan report (if connecting to a peripheral)
  and can be set manually if desired.

v0.3.2
------

v0.3.2 is a bug fix release

**Fixes**

- `Issue 40`_ - Fixes issue where service discovery fails if the server returns ``attribute_not_found`` while discovering services

- `Issue 42`_ - Fixes issue where :attr:`Advertiser.is_advertising <blatann.gap.advertising.Advertiser.is_advertising>` could
  return false if ``auto_restart`` is enabled and advertising times out

**Added Features**

- Exposes a new :attr:`Advertiser.auto_restart <blatann.gap.advertising.Advertiser.auto_restart>`
  property so it can be get/set outside of :meth:`Advertiser.start() <blatann.gap.advertising.Advertiser.start>`

v0.3.1
------

v0.3.1 provides a few enhancements and features from the previous release.

**Highlights**

- Adds the ability to discover, read, and write a connected central device's GATT database as a peripheral.

  - Example usage has been added to the peripheral example where it will discover the connected device's database after pairing completes

  - **NOTE:** The inverse of this should be considered experimental (i.e. acting as a central and having a peripheral read/write the local database).

- Adds the ability to perform writes without responses, both as a client and as a peripheral

  - New APIs have been added to the :class:`~blatann.gatt.gattc.GattcCharacteristic` class:
    :meth:`~blatann.gatt.gattc.GattcCharacteristic.write_without_response` and
    :attr:`~blatann.gatt.gattc.GattcCharacteristic.writable_without_response`

- Adds API to trigger data length update procedures (with corresponding event) on
  the :class:`~blatann.peer.Peer` class

  - The API does not allow the user to select a data length to use,
    i.e. the optimal data length is chosen by the SoftDevice firmware


**Changes**

- The connection event length has been updated to support the max-length DLE value (251bytes) at the shortest connection interval (7.5ms)

- Updates to documentation and type hinting

- Minor changes to logging, including removing spammy/duplicate logs when numerous characteristics exist in the GATT database

**Fixes**

- Fixes issue where iterating over the scan report in real-time was not returning the recently read packet
  and instead was returning the combined packet for the device's address. This was causing duplicate packets to not be marked in the scanner example.


v0.3.0
------

v0.3.0 marks the first stable release for Python 3.7+.

Unfortunately a comprehensive changelog is not available for this release as a lot went in to migrate to Py3/Softdevice v5. That said,
public API should be mostly unchanged except for the noted changes below.

**Highlights**

- Python 3.7+ only
- Requires ``pc-ble-driver-py`` v0.12.0+
- Requires Nordic Connectivity firmware v4.1.1 (Softdevice v5)

**Changes**

- ``Scanner.scanning`` field was replaced with read-only property ``Scanner.is_scanning``

- Parameter validation was added for Advertising interval, Scan window/interval/timeout, and connection interval/timeout.

  - Will raise ``ValueError`` exceptions when provided parameters are out of range

- With Python 3, converting from ``bytes`` to ``str`` (and vice-versa) requires an encoding format.
  By default, the encoding scheme is ``utf-8`` and can be set per-characteristic using the ``string_encoding`` property

- ``peer.disconnect()`` will now always return a ``Waitable`` object. Before it would return ``None`` if not connected to the peer.
  If ``disconnect()`` is called when the peer is not connected, it will return a Waitable object that expires immediately

**Fixes**

- Fixes an issue where unsubscribing from a driver event while processing the event was causing the
  the next handler for the driver event to be skipped

  - Back-ported to v0.2.9

**Features**

(This list is not comprehensive)

- Driver now property works with 2 devices simultaneously

- Event callbacks can now be used in a ``with`` context so the handler can be deregistered at the end of a block

  - `Event callback example`_

- The ``ScanFinishedWaitable`` now provides a ``scan_reports`` iterable which can be used to iterate on advertising packets
  as they're seen in real-time

  - `ScanFinishedWaitable example`_

- The ``Peer`` object now exposes properties for the active connection parameters and configured/preferred
  connection parameters

- The ``Peripheral`` object exposes an ``on_service_discovery_complete`` event

- Added ``AdvertisingData.to_bytes()`` to retrieve the data packet that will be advertised over the air

.. _Event callback example: https://github.com/ThomasGerstenberg/blatann/blob/1f85c68cf6db84ba731a55d3d22b8c2eb0d2779b/tests/integrated/test_advertising_duration.py#L48
.. _ScanFinishedWaitable example: https://github.com/ThomasGerstenberg/blatann/blob/1f85c68cf6db84ba731a55d3d22b8c2eb0d2779b/blatann/examples/scanner.py#L20
.. _Issue 40: https://github.com/ThomasGerstenberg/blatann/issues/40
.. _Issue 42: https://github.com/ThomasGerstenberg/blatann/issues/42