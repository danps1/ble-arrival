# Compatibility and releases

| Project | Protocol | HA baseline | ESPHome baseline | Target |
| --- | --- | --- | --- | --- |
| 0.2.0 | HA: 1 and 2; firmware: 2 | 2026.9.0 | 2026.8.2, ESP-IDF | ESP32-S3 |
| 0.1.1 | 1 | 2026.9.0 | 2026.8.2, ESP-IDF | ESP32-S3 |
| 0.1.0 | 1 | 2026.9.0 | 2026.8.2, ESP-IDF | ESP32-S3 |

The release bundles a matching integration and external component. HACS installs only the HA integration. ESPHome pulls `components/ble_arrival` from the release tag when you compile. Neither tool automatically upgrades the other component.

Backward-compatible HA changes should continue accepting protocol 1. Unknown protocol versions fail closed. Release notes must specify whether a firmware reflash is required. Do not move published tags.

The initial version is experimental. Compilation and simulated tests cannot establish real proxy latency, RF range, hardware reliability or physical-access resistance. Consult hardware-testing.md for deployment acceptance.

Version 0.1.1 changes only the HA integration and continues using firmware v0.1.0. No dongle reflash is required.

The route sensor reads the connected scanner from Home Assistant's habluetooth client wrapper before disconnect. This metadata has been verified against habluetooth 6.26.11, including a test against the actual wrapper class. The wrapper currently exposes this through private `_connected_scanner` metadata, so access is isolated and missing data produces an unknown route without affecting authentication. Scanner interfaces can change across Home Assistant releases; see [HA Bluetooth API guidance](https://developers.home-assistant.io/docs/core/bluetooth/api/). Advertisements are never used to guess the route.

Version 0.2.0 adds authenticated uptime. Install HA first, then reflash each dongle to v0.2.0 to obtain uptime. HA accepts old dongles with unknown uptime; old HA cannot authenticate new protocol 2 firmware. Existing credentials are retained. Optional LilyGO display support is a separate ESPHome package.
