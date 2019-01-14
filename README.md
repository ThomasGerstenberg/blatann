# Blatann

blåtann: Norwegian word for "blue tooth"

The goal of this library is to provide a high-level, object-oriented interface
for performing bluetooth operations using the Nordic nRF52 through Nordic's `pc-ble-driver-py` library
and the associated Connectivity firmware.

### Install

`pip install blatann`

#### Supported Devices/Software

This has been tested using both the nRF52832 Dev Kit and the [ABSniffer 528](https://blog.aprbrother.com/product/absniffer-usb-dongle-528) flashed with Connectivity Firmware

This API implements against Connectivity Firmware for SoftDevice v3. This does NOT support the nRF51 or SoftDevice v2.

Currently only Python 2.7 is supported. This is a limitation of the `pc-ble-driver-py` library only building the SWIG modules for v2.
If the aforementioned library ever supports Python 3+, this library will be updated also. Or, if I find spare time and this library
is stable I'll work on building the modules myself and remove pc-ble-driver-py as a dependency altogether.


### Roadmap

- [ ] GAP
    - [X] BLE Enable parameters
    - [X] BLE Connection parameters (functional, needs some work)
    - [x] Advertising
    - [ ] Scanning (functional, needs some refactoring)
    - [ ] Documentation
- [ ] SMP
    - [X] Encryption/Authentication process
    - [X] MITM/Passcode pairing support
    - (WIP) Store bonding info
    - (WIP) Identity resolve
    - [ ] Documentation
- [ ] GATT Server
    - [x] Characteristic Reads
    - [x] Characteristic Writes
    - [x] Notifications/Indications
    - [x] Long reads/writes
    - [ ] Characteristic User Description/Presentation format
    - [ ] CCCD Caching
    - [ ] Documentation (partial)
- [ ] GATT Client
    - [X] Database Discovery procedure
    - [X] Client reads
    - [X] Client writes
    - [X] Client long writes
    - [X] Notifications/Indications
    - [ ] CCCD Caching
    - [ ] Documentation
- [ ] Examples
    - [X] Advertiser/Broadcaster
    - [X] Scanner/Observer
    - [X] Central, Procedural
    - [X] Central, Event Driven
    - [ ] Central, Multiple Connections
    - [X] Peripheral
    - [ ] Multi-role
    - [X] Passcode Pairing
    - [ ] Bonding
- [ ] Bluetooth Services
    - [X] Device Info Service
    - [ ] Glucose Service (Peripheral done, Central untested)
    - [ ] Nordic UART Service
    - More TBD (or on request)
- [X] License
- [ ] Unit Tests
- [ ] Integration Tests


The library aims to support both event-driven and procedural program styles. It takes similar paradigms from C#/.NET's event function signatures,
where event handlers are passed  `object sender, EventArgs e`. In addition, asynchronous function calls return a `Waitable` object which
can be waited on (with timeout) until the event associated with the function call returns.

**NOTE**

This library is very much a work in progress. Interfaces, objects, method names **will** change.
