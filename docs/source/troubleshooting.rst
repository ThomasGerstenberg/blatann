Troubleshooting
===============

This section provides some troubleshooting hints, tips, and tricks
to work with Blatann.


General Debugging
-----------------

Blatann uses the built-in ``logging`` module to log all events and driver calls.
The library also contains a helper function to configure/enable: :meth:`blatann.utils.setup_logger`.

When submitting an issue, please include logs of the behavior at the ``DEBUG`` level.


Error Messages
--------------

Error: Failed to open. Error code: 0x8029
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Failure to open the serial communication with the nRF52 device can manifest
itself with the following error message:

.. code-block:: none

    Failed to open. Error code: 0x8029

Check the communication port settings (baud, port, etc.) in your script.

Note that the nRF52840-Dongle (PCA10059, a nRF52 USB Dongle) will enumerate
two separate ports: one for the bootloader during flashing and one for the
application. Make sure that you check the port number after the bootloader
exits and the application starts.


Error: Failed to open. Error code: NrfError.rpc_h5_transport_state
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following error message can occur when there is no nRF52 device
(not inserted/connected to a USB port), or when present it might not
be detected/authenticated for use by the Operating System (OS).

.. code-block:: none

    pc_ble_driver_py.exceptions.NordicSemiException:
    Failed to open. Error code: NrfError.rpc_h5_transport_state

Check that the nRF52 device is connected (inserted into a USB port):

.. code-block:: bash

    # on Linux, request a list of USB devices
    lsusb
    # for a nRF52840 USB Dongle with the Connectivity firmware
    # already flashed it will show something like:
    #   Bus 00# Device 00#:
    #     ID 1915:c00a Nordic Semiconductor ASA nRF52 Connectivity
    # while a nRF52840 USB Dongle without Connectivity firmware
    # may show (for a new device out-of-the-box) like:
    #   Bus 00# Device 00#:
    #     ID 1915:521f Nordic Semiconductor ASA Open DFU Bootloader

Where the ID "1915:c00a" indicates the VID:PID (Vendor : Product ID)
identifiers of the nRF52840-Dongle when flashed with the Connectivity
firmware from Nordic Semiconductor ASA.

When the Connectivity firmware hasn't been flashed yet, other VID:PID
identifiers may be listed. These may depend on firmware on the nRF52
device. For a nRF52840-Dongle out-of-the-box it may for example show
as "1915:521f" with "Open DFU Bootloader".

Even with the nRF52840-Dongle properly flashed and seen with ``lsusb``,
the above error message that it cannot be openend may show. On the Linux
operating system, this often indicates that you as a user may not have
the proper rights to utilize the USB device. The following will add the
current user to the ``plugdev`` group that can use USB plug-in devices,
add detection/authorization for USB devices with the nRF52 Connectivity
firmware to be used, and then trigger loading the new/adjusted rules.

.. code-block:: bash

    # allow user USB plugin device access
    sudo adduser $USER plugdev
    # add rules to /etc/udev/rules.d/80-usb.rules
    echo 'ATTRS{idVendor}=="1915", ATTRS{idProduct}=="c00a", SUBSYSTEMS=="usb", ACTION=="add", MODE="0666", GROUP="plugdev"' | sudo tee -a /etc/udev/rules.d/80-usb.rules > /dev/null
    # load the new rules
    sudo udevadm trigger


Error: Failed to ble_enable. Error code: NrfError.no_mem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The nRF52 devices have limited Random Access Memory (RAM) and the firmware
pre-allocates all required memory based on the configuration settings.
When exceeding certain limits, this may result in an ``no_mem`` error message
indicating an out-of-memory situation.

.. code-block:: none

    pc_ble_driver_py.exceptions.NordicSemiException:
    Failed to ble_enable. Error code: NrfError.no_mem

This may for example occur when you're trying to increase the number of
connected peripherals.

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

The biggest contributors are clearly the Maximum Transfer Unit (MTU) size,
number of connections, and queue sizes as they are multiplicative.

Based on the above calculation, the magic number found through trial and error
is roughly 15528 bytes (on nRF52840-Dongle with Connectivity firmware v4.1.4).
If you plug your settings into the above calculation and it's below that
number, it will work.

Here's a few tips for modifying the parameters:

- If you're only using the device for central connections, reduce these values:

  - ``notification_hw_queue_size=1``

  - ``attribute_table_size=248`` (minimum allowed value)

  - ``max_connected_clients=0``

- If you're not using write without response messages as a central or don't
  require a very high throughput application,
  set ``write_command_hw_queue_size=1``

  - Note: there is a software queue for writes/notifications already,
    the hardware queues allow multiple packets to be sent in a single
    connection interval if timing permits.

- If you're not sending out notifications in at a high throughput as
  a peripheral, reduce ``notification_hw_queue_size=1``

- If you're not pairing/bonding with devices as a central,
  reduce ``max_secured_peripherals`` to the required number.

- In most cases, queue sizes of 4 or less will suffice.
