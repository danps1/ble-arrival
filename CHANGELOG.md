# Changelog

## 0.2.0 (pre-release)

- Adds cryptographically authenticated boot uptime in whole seconds to protocol 2, without an extra GATT exchange.
- Adds an uptime diagnostic sensor and matching `uptime_seconds` authentication-event attribute. Legacy firmware authenticates with unknown uptime.
- Uses a 64-bit firmware timer; reboots reset uptime without persistent counters or flash writes.
- Adds the optional, button-activated LilyGO T-Dongle-S3 display package, with 20-second backlight timeout and commented installation lines in generated LilyGO YAML.
- Adds protocol tampering, replay, framing, boundary, backwards-compatibility, event and sensor tests.
- Update HA first; reflash dongles with the same credentials for uptime. Existing display snippets remain usable. No proxy changes or garage automation.


## 0.1.1

- Add a diagnostic **Last authenticated via** sensor with the connected proxy/adapter name, source identifier and authentication timestamp. It updates only after a successful exchange; unavailable route metadata is reported as unknown.
- Fix delayed freshness expiry when a failed connection changes the connection status before the 30-second timeout. Expiry now publishes independently of retry status.
- Add regression coverage for expiry during failures, route selection, failed-exchange preservation, missing metadata and HA wrapper compatibility.
- HA integration update only. Firmware and protocol are unchanged; existing v0.1.0 dongles do not need reflashing. Generated ESPHome configuration continues to pin firmware v0.1.0.
- Temporary duplicate setup rows remain an unconfirmed frontend/setup observation; no automatic entry deletion is introduced.

## 0.1.0

Initial experimental release: ESPHome BLE credential service; Home Assistant verification through standard Bluetooth routing; resumable per-car provisioning; copyable configuration; authentication entities and credential revocation. No garage control or automation blueprint.
