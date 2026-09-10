# Compatibility and releases

| Project | Protocol | HA baseline | ESPHome baseline | Target |
| --- | --- | --- | --- | --- |
| 0.1.0 | 1 | 2026.9.0 | 2026.8.2, ESP-IDF | ESP32-S3 |

The release bundles a matching integration and external component. HACS installs only the HA integration. ESPHome pulls `components/ble_arrival` from the release tag when you compile. Neither tool automatically upgrades the other component.

Backward-compatible HA changes should continue accepting protocol 1. Unknown protocol versions fail closed. Release notes must specify whether a firmware reflash is required. Do not move published tags.

The initial version is experimental. Compilation and simulated tests cannot establish real proxy latency, RF range, hardware reliability or physical-access resistance. Consult hardware-testing.md for deployment acceptance.
