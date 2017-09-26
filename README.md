# Blatann

blåtann: "blue tooth" in Norwegian


The goal of this library is to provide a high-level, object-oriented interface
for performing bluetooth operations using the Nordic nRF52 through Nordic's `pc-ble-driver-py` library
and the associated Connectivity firmware


Roadmap:

- [ ] GAP
    - [ ] BLE Enable parameters
    - [ ] BLE Connection parameters
    - [x] Advertising
    - [ ] Scanning (in progress)
- [ ] SMP
    - [ ] Encryption/Authentication process
    - [ ] MITM/Passcode pairing support
    - [ ] Store bonding info
- [ ] GATT Server
    - [x] Characteristic Reads
    - [x] Characteristic Writes
    - [x] Notifications/Indications
    - [x] Long reads/writes
    - [ ] Characteristic User Description/Presentation format
    - [ ] CCCD Caching
- [ ] GATT Client
    - [ ] Database Discovery procedure
    - [ ] Client reads
    - [ ] Client writes
    - [ ] Client long writes
    - [ ] Notifications/Indications

The library aims to support both event-driven and procedural program styles. Initially the library
will primarily support procedural, with some hooks to make it event-driven.

**NOTE**

This library is very much a work in progress. Interfaces, objects, method names **will** change.
Semantic versioning has not been implemented
