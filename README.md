# Blatann

blåtann: Norwegian word for "blue tooth"

Blatann aims to provide a high-level, object-oriented interface for interacting
with Bluetooth Low Energy (BLE) devices through Python. It operates using
the Nordic Semiconductor nRF52 through Nordic's ``pc-ble-driver-py`` library
and the associated Connectivity firmware for the device.

Documentation is available on [ReadTheDocs](https://blatann.readthedocs.io)

### Install

`pip install blatann`

#### Using with macOS brew python

`pc-ble-driver-py` consists of a shared object which is linked to mac's system python.
In order to use it with brew's python install, you'll need to run `install_name_tool` to modify the `.so` to 
point to brew python instead of system python.

_Note: This is the case with any custom-installed python on mac (like anaconda), brew is the most popular and what has been tested_

An example shell script to do so can be found [here](./tools/macos_retarget_pc_ble_driver_py.sh)  

#### Supported Devices/Software

This library has been tested with the following hardware:

- the [nRF52-DK](https://www.nordicsemi.com/Products/Development-hardware/nrf52-dk): a Dev Kit for the nRF52832 (PCA10040)
- the [nRF52840-DK](https://www.nordicsemi.com/Products/Development-hardware/nRF52840-DK): a Dev Kit for the nRF52840 (PCA10056)
- the [nRF52840-Dongle](https://www.nordicsemi.com/Products/Development-hardware/nrf52840-dongle): a nRF52840 USB Dongle (PCA10059)
- the [ABSniffer-528](https://wiki.aprbrother.com/en/ABSniffer_USB_Dongle_528.html): a nRF52832 USB Dongle

Flashed with specific Connectivity firmware released by Nordic Semiconductor.

When using the nRF52840, it should be flashed using the S132/SoftDevice v5 connectivity images. Both the hex files and DFU packages are distributed
with v4.1.4 of [pc-ble-driver](https://github.com/NordicSemiconductor/pc-ble-driver/releases/tag/v4.1.4) and is also provided in the `pc-ble-driver-py` install.

The Nordic devices can be flashed using [nRF Connect Desktop App](https://www.nordicsemi.com/Software-and-Tools/Development-Tools/nRF-Connect-for-desktop) or the `nrfutil` CLI tool.

### Roadmap/Supported BLE Features

As of v0.3.0, the public-facing API of Blatann is stable. There will not
likely be any major changes in method/property naming or functionality
and all features added will aim to maintain backwards compatibility.

Below lists the supported BLE features and ones that are on the roadmap to implement (eventually)

- [X] GAP
    - [X] BLE Enable parameters
    - [X] BLE Connection parameters (functional, needs some work)
    - [X] Advertising
    - [X] Data Length Extensions
    - [X] PHY selection
      - Coded PHY not supported, only 1 and 2 Mbps PHYs
    - [X] Scanning
    - [X] Documentation
    - [X] RSSI
    - [X] Transmit Power
    - [X] Advertising channel selection
- [X] SMP
    - [X] Private resolvable/non-resolvable advertising 
    - [X] Encryption/Authentication process
    - [X] MITM/Passcode pairing support
    - [X] Store bonding info
    - [X] Identity resolve
    - [X] Bonding as Peripheral
    - [X] Bonding as Central
    - [X] LESC pairing
    - [X] Documentation
- [ ] GATT
    - [X] Configurable MTU
    - [X] Generic Access service configuration
    - [ ] Service Changed characteristic
- [ ] GATT Server
    - [X] Characteristic Reads
    - [X] Characteristic Writes
    - [X] Notifications/Indications
    - [X] Long reads/writes
    - [X] Characteristic User Description/Presentation format
    - [ ] CCCD Caching
    - [ ] Custom Read/Write authorization (#10)
    - [X] Documentation
- [ ] GATT Client
    - [X] Database Discovery procedure
    - [X] Client reads
    - [X] Client writes
    - [X] Client long writes
    - [X] Notifications/Indications
    - [ ] CCCD Caching
    - [ ] Service Discovery Caching (#89)
    - [X] Documentation
- [ ] Examples
    - [X] Advertiser/Broadcaster
    - [X] Scanner/Observer
    - [X] Central, Procedural
    - [X] Central, Event Driven
    - [ ] Central, Multiple Connections (#77)
    - [X] Peripheral
    - [ ] Multi-role
    - [X] Passcode Pairing
    - [X] LESC Numeric Comparison Pairing (glucose peripheral, no central example)
    - [X] Bonding (glucose peripheral, no central example)
- [ ] Bluetooth Services
    - [X] Device Info Service
    - [X] Battery Service
    - [ ] Current Time Service
       - [X] Peripheral
       - [ ] Central (Partially implemented)
    - [ ] Glucose Service
       - [X] Peripheral
       - [ ] Central
    - [X] Nordic UART Service
    - More TBD (or on request)
- [X] License
- [ ] Unit Tests
- [X] Integration Tests (partial -- below are implemented)
    - Advertising
    - Scanning
    - GATT Writes/Reads
    - GATT throughput testing/benchmarks
    - Pairing/Bonding

The library aims to support both event-driven and procedural program styles. It takes similar paradigms from C#/.NET's event function signatures,
where event handlers are passed  `object sender, EventArgs e` parameters.
Additionally, all asynchronous function calls return a `Waitable` object which can be waited on (with timeout)
until the event associated with the function call returns.

### Examples

There are several example scripts which showcase different functionality of the library under `blatann/examples`.
Examples can be run using `python -m blatann.examples [example_filename] [device_comport]`.

Example usage: `python -m blatann.examples scanner COM3`

### Running Tests

The integrated tests can be ran using the builtin `unittest` runner and depends on a few environment variables to find the connected Nordic devices.

At a minimum, two nordic devices are required to run the unit tests. These are specified using environment variables:

- `BLATANN_DEV_1` - Serial port of the first Nordic device
- `BLATANN_DEV_2` - Serial port of the second Nordic device

Optionally a third `BLATANN_DEV_3` can be specified to run tests which require more than two devices. If this environment variable is not defined, tests which require 3 devices are skipped.

In order to speed up the tests, `BLATANN_TEST_QUICK=1` can be defined to skip long-running tests. 
Note that test cases which are defined as "long-running" is subjective and relative--the test suite will still take awhile to run, 
but in general test cases which take longer than 20 seconds are skipped.

The tests can also be ran through the makefile using `make run-tests`.
