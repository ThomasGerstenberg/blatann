Compatibility Matrix
====================

.. list-table:: Software/Firmware Compatibility Matrix
   :header-rows: 1

   * - | Blatann
       | Version
     - | Python
       | Version
     - | Connectivity Firmware
       | Version
     - | SoftDevice
       | Version
     - | pc-ble-driver-py
       | Version
   * - v0.2.x
     - 2.7 Only
     - v1.2.x
     - v3
     - <= 0.11.4
   * - v0.3+
     - 3.7+
     - v4.1.x
     - v5
     - >= 0.12.0

Firmware images are shipped within the ``pc-ble-driver-py`` package under the ``hex/`` directory.
Below maps which firmware images to use for which devices.
For Blatann v0.2.x, firmware images are under subdir ``sd_api_v3``.
For Blatann v0.3+, firmware images are under subdir ``sd_api_v5``.

.. list-table:: Firmware/Hardware Compatibility Matrix
   :header-rows: 1

   * - Hardware
     - Firmware Image
   * - nRF52832 Dev Kit
     - connectivity_x.y.z_<baud>_with_s132_x.y.hex (note the baud rate in use!)
   * - nRF52840 Dev Kit
     - | connectivity_x.y.z_<baud>_with_s132_x.y.hex (note the baud rate in use!) **or**
       | connectivity_x.y.z_usb_with_s132_x.y.hex if using the USB port on the side
   * - nRF52840 USB Dongle
     - connectivity_x.y.z_usb_with_s132_x.y.hex

.. note::
   Blatann provides a default setting for the baud rate to use with the device.
   For v0.2.x, the default baud is 115200 whereas for v0.3+ the default is 1M (and USB doesn't care).
   This is only an issue when running examples through the command line as it
   doesn't expose a setting for the baud rate. When writing your own script, it can be configured however it's needed.
