Changelog
=========

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