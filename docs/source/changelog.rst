Changelog
=========


v0.6.0
------

v0.6.0 is mostly a maintenance release and adds support for some new experimental async APIs.
Full list of issues and PRs for this release can be found here: `0.6.0 Milestone`_

**Highlights**

- *[Experimental]* Adds async support to waitables for use in asyncio event loops.

  - See the new ``peripheral_async.py`` and ``central_async.py`` examples for usage,
    but generally any invocation of ``ble_operation().wait()`` can be modified to ``await ble_operation().as_async()``

  - **Note:** this API is only *partially* async.
    The USB communications to the BLE device is still synchronous (blocking), but the longer BLE operations can now be async.

- Adds convenience method to the client to wait for an incoming connection as a peripheral (ex: ``ble_device.client.wait_for_connection(timeout)``)

**Fixes**

- Fixes a warning emitted by a recent version of the cryptography library (thanks @AnatoleMombrun)

- Fixes issue with the Nordic UART Client not respecting the negotiated MTU size (thanks @linuslundin)

- Fixes a few minor bugs uncovered through linting

- Fixes issue with incorrect response when requesting a record from an empty glucose database in the glucose service

**Changes**

- **[Potential Breaking Change]** The import structure for some non-public-facing files have been adjusted for correctness.
  Typical usage of the API should not be affected, likely only affected if importing types from the inner ``blatann.nrf`` package

- Miscellaneous documentation updates (thanks @mdxs)

- Adds optional parameters when connecting as a client to set the preferred MTU size and PHY in case the peripheral initiates those BLE operations first


v0.5.0
------

v0.5.0 reworks bonding database to JSON, adds a few features, and fixes a few bugs.
Full list of issues and PRs for this release can be found here: `0.5.0 Milestone`_

**Highlights**

- Adds support for the scanner to resolve peer addresses.

  - :class:`~blatann.gap.advertise_data.ScanReport` has 2 new properties: ``is_bonded_device: bool`` and ``resolved_address: Optional[PeerAddress]``

- Adds support for privacy settings to advertise with a private resolvable or non-resolvable address

- Adds parameter to device configuration to set a different connection event length

**Fixes**

- Fixes incorrect variable name when a queued GATT operation times out (thanks @klow68)

- Fixes incorrect key length when converting an LESC private key to a raw bytearray (thanks @klow68). Function is unused within blatann

- Fixes issue where the service changed characteristic was not correctly getting added to the GATT server when configured

**Changes**

- Reworks the bond database to be saved using JSON instead of pickle.

  - Existing ``"system"`` and ``"user"`` database files configured in the BLE device will automatically be migrated to JSON

  - Other database files configured by filepath will continue to use pickle and can be updated manually using :meth:`~blatann.gap.default_bond_db.migrate_bond_database`

- Bond DB entries will now save the local BLE address that was used to generate the bonding data.

  - This will allow multiple nRF boards to use the same DB file and not resolve bond entries if it was not created with that board/address. This fixes potential issues where restoring a connection to a peer that was bonded to a different nRF board can cause the local device to think it has a bond, however the peer has bond info with a different, mismatched address.

- Moves bond-related resolve logic out of the security manager and into the bond database


v0.4.0
------

v0.4.0 introduces some new features and fixes a couple of issues.
Full list of issues and PRs for this release can be found here: `0.4.0 Milestone`_

**Highlights**

- Adds support for reading RSSI of an active connection, plus example usage of API

- Adds Event+Waitable for Connection Parameter Update procedures

  - Additionally adds support for accepting/rejecting update requests as a central

- Adds support for setting the device's transmit power

- Adds support for setting advertising channel masks

**Fixes**

- Fixes issues seen when performing certain pairing routines on linux

- Fixes for misc. advertising corner cases

- Fixes an issue with ``BasicGlucoseDatabase`` introduced in the python 3 migration


v0.3.6
------

v0.3.6 is a minor bugfix update and some small improvements

**Fixes**

- Fixes an uncaught exception caused when handling a failed bond database load (thanks @dkkeller)

- Fixes an issue where waiting on indications to be confirmed did not work. Regression introduced in v0.3.4

**Changes**

- Updates the descriptor discovery portion of service discovery to be more efficient, speeding up service discovery times

- Updates the API lock at the driver layer to be per-device. This will reduce lock contention when using multiple BLE Devices in different threads


v0.3.5
------

v0.3.5 is a small update that primarily provides some bug fixes and cleanup to the bonding process.

**Highlights**

- Overall increased stability when restoring encryption using long-term keys for a previously-bonded device

- Adds param to set the CCCD write security level for a characteristic

**Fixes**

- Restoring legacy bonding LTKs as a central now works correctly

**Changes**

- `Issue 60`_ - The default bonding database file has been moved into the user directory instead of within the package contents (``~/.blatann/bonding_db.pkl``).

  - An optional parameter has been added to the :class:`~blatann.device.BleDevice` constructor for specifying the file to use for convenience

  - To revert to the previous implementation, specify ``bond_db_filename="system"`` when creating the BleDevice object

  - To use the new storage location but keep the bonding data from previous version,
    copy over the database file from ``<blatann_install_loc>/.user/bonding_db.pkl`` to the location noted above


v0.3.4
------

v0.3.4 brings several new features (including characteristic descriptors) and a couple bug fixes.
A fairly large refactoring of the GATT layer took place ot make room for the descriptors, however no public-facing APIs were modified.

**Highlights**

- `Issue 11`_ - Adds support for adding descriptor attributes to characteristics

  - See the `Central Descriptor Example`_ and `Peripheral Descriptor Example`_ for how they can be used

- Adds a new ``bt_sig`` sub-package which provides constants and UUIDs defined by Bluetooth SIG.

- Adds visibility to the device's Generic Access Service: :attr:`BleDevice.generic_access_service <blatann.device.BleDevice.generic_access_service>`

  - Example usage has been added to the peripheral example

- Adds support for performing PHY channel updates

  - **Note**: Coded PHY is currently not supported, only 1Mbps and 2Mbps PHYs

- Adds a description attribute to the UUID class. The standard UUIDs have descriptions filled out, custom UUIDs can be set by the user.

**Fixes**

- Fixes an issue with bonding failing on linux

- Fixes an issue where the ``sys_attr_missing`` event was not being handled

- Adds missing low-level error codes for the RPC layer

- Fixes race condition when waiting on ID-based events causing an ``AttributeError``.
  Event subscription previously occurred before the ID was set and there was a window where the callback could be triggered before the ID
  was set in the object instance.
  This issue was most prominent after introducing the write/notification queuing changes in combination with a short connection interval.

**Changes**

- The ``device_name`` parameter has been removed from :meth:`BleDevice.configure() <blatann.device.BleDevice.configure>`.
  This wasn't working before and has been added into the Generic Access Service.

- Write, notification, and indication queuing has been tweaked such that non-ack operations (write w/o response, notifications)
  now take advantage of a hardware queue independent of the acked counterparts (write request, indications)

- Service discovery was modified to allow descriptor discovery and in some cases (depending on peripheral stack) run faster

- ``DecodedReadWriteEventDispatcher`` has been moved from ``blatann.services`` to ``blatann.services.decoded_event_dispatcher``.
  This was to solve a circular dependency issue once new features were added in.

- The glucose service has been updated to make better use of the notification queuing mechanism. Glucose record transmission is sped up greatly


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

.. _0.4.0 Milestone: https://github.com/ThomasGerstenberg/blatann/milestone/7?closed=1
.. _0.5.0 Milestone: https://github.com/ThomasGerstenberg/blatann/milestone/8?closed=1
.. _0.6.0 Milestone: https://github.com/ThomasGerstenberg/blatann/milestone/9?closed=1
.. _Event callback example: https://github.com/ThomasGerstenberg/blatann/blob/1f85c68cf6db84ba731a55d3d22b8c2eb0d2779b/tests/integrated/test_advertising_duration.py#L48
.. _ScanFinishedWaitable example: https://github.com/ThomasGerstenberg/blatann/blob/1f85c68cf6db84ba731a55d3d22b8c2eb0d2779b/blatann/examples/scanner.py#L20
.. _Peripheral Descriptor Example: https://github.com/ThomasGerstenberg/blatann/blob/master/blatann/examples/peripheral_descriptors.py
.. _Central Descriptor Example: https://github.com/ThomasGerstenberg/blatann/blob/master/blatann/examples/central_descriptors.py
.. _Issue 11: https://github.com/ThomasGerstenberg/blatann/issues/11
.. _Issue 40: https://github.com/ThomasGerstenberg/blatann/issues/40
.. _Issue 42: https://github.com/ThomasGerstenberg/blatann/issues/42
.. _Issue 60: https://github.com/ThomasGerstenberg/blatann/issues/60