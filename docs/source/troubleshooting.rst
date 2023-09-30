Troubleshooting
===============

*This section is a work in progress*

**General Debugging**

Blatann uses the built-in ``logging`` module to log all events and driver calls.
The library also contains a helper function to configure/enable: :meth:`blatann.utils.setup_logger`.

When submitting an issue, please include logs of the behavior at the ``DEBUG`` level.

**Error message: Failed to open. Error code: 0x8029**

Check your comport settings (baud, port, etc.).

Note that the nRF52840 USB dongle will enumerate 2 separate ports: one for the bootloader during flashing and one for the application.
Make sure that you check the port number after the bootloader exits and application starts.

**I'm trying to increase the number of connected peripherals and getting a no_mem error**

The nRF52 device has limited RAM and the firmware pre-allocates all required memory needed based on the configuration settings.
The primary configuration settings that impact RAM usage are:

- ``notification_hw_queue_size`` (default=16, in BleDevice constructor)

- ``write_command_hw_queue_size`` (default=16, in BleDevice constructor)

- ``vendor_specific_uuid_count`` (default=10)

- ``max_connected_centrals`` (default=1)

- ``max_connected_peripherals`` (default=1)

- ``max_secured_peripherals`` (default=1)

- ``attribute_table_size`` (default=1408)

- ``att_mtu_max_size`` (default=247)

A very roughly estimated calculation of the memory usage is:

.. code-block:: python

    attribute_table_size +
    vendor_specific_uuid_count * 20 +
    max_connected_centrals * notification_hw_queue_size * att_mtu_max_size +
    max_connected_peripherals * write_command_hw_queue_size * att_mtu_max_size +
    max_secured_peripherals * 48

The biggest contributors are clearly the MTU size, # connections, and queue sizes as they are multiplicative.

Based on the above calculation, the magic number found through trial and error is roughly 15528 bytes (on nRF52 USB dongle w/ connectivity FW v4.1.4).
If you plug your settings into the above calc and it's below that number, it will work.

Here's a few tips for modifying the parameters:

- If you're only using the device for central connections, reduce these values:

  - ``notification_hw_queue_size=1``

  - ``attribute_table_size=248`` (minimum allowed value)

  - ``max_connected_clients=0``

- If you're not using write without response messages as a central or don't require a very high throughput application, set ``write_command_hw_queue_size=1``

  - Note: there's an software queue for writes/notifications already, the hardware queues allow multiple packets to be sent in a single connection interval if timing permits

- If you're not sending out notifications in at a high throughput as a peripheral, reduce ``notification_hw_queue_size=1``

- If you're not pairing/bonding with devices as a central, reduce ``max_secured_peripherals`` to the required number

- In most cases, queue sizes of 4 or less will suffice
