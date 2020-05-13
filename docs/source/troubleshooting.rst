Troubleshooting
===============

*This section is a work in progress*

**General Debugging**

Blatann uses the built-in ``logging`` module to log all events and driver calls.
The library also contains a helper function to configure/enable: :meth:`blatann.utils.setup_logger`.

When submitting an issue, please include logs of the behavior at the ``DEBUG`` level.

**Specific Error Messages**

Error message ``Failed to open. Error code: 0x8029`` - Check your comport settings (baud, port, etc.).

Note that the nRF52840 USB dongle will enumerate 2 separate ports: one for the bootloader during flashing and one for the application.
Make sure that you check the port number after the bootloader exits and application starts.

