Getting Started
===============

Introduction
^^^^^^^^^^^^

This library relies on a Nordic nRF52 connected via USB to the PC and flashed with the
Nordic Connectivity firmware in order to operate.

.. note:: This is not meant to work with any generic Bluetooth HCI USB device nor built-in Bluetooth radios.

Below are the known supported devices:

* nRF52832 Development Kit (PCA10040)
* nRF52840 Development Kit (PCA10056)
* nRF52840 USB Dongle (PCA10059)

Install
^^^^^^^

Blatann can be installed through pip: ``pip install blatann``

Setting up Hardware
^^^^^^^^^^^^^^^^^^^

Once one of the hardware devices above is connected via USB, the Nordic Connectivity firmware can be flashed using
Nordic's `nRF Connect`_ Application.
There are other methods you can use (such as ``nrfutil``), however this is the least-complicated way. Further instructions
for using nRF Connect are out of scope for this as Nordic has great documentation for using their app already.

The firmware image to use can be found within the installed ``pc-ble-driver-py`` python package under the ``hex/`` directory.
From there, it's a drag and drop operation to get the image onto the firmware.

See the :doc:`./compatibility_matrix` which lists what software, firmware, and hardware components work together.

Smoke Test the Setup
^^^^^^^^^^^^^^^^^^^^

Once the hardware is flashed and Blatann is installed,
the Scanner example can be executed to ensure everything is working.
Blatann's examples can be executed from the command line using

``python -m blatann.examples <example_name> <comport>``

For the smoke test, use the ``scanner`` example which will stream any advertising packets found for about 4 seconds:
``python -m blatann.examples scanner <comport>``

If everything goes well, head on over to :doc:`./examples` to look at the library in action.
If this does not seem to be working, check out the :doc:`./troubleshooting` page.


.. _nRF Connect: https://www.nordicsemi.com/Software-and-tools/Development-Tools/nRF-Connect-for-desktop