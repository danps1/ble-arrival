# BLE Arrival

Authenticated Bluetooth detection for cars using an ESPHome USB dongle and Home Assistant's existing active Bluetooth proxies.

**Experimental v0.1.1. Software tests are included; a real T-Dongle-S3 and proxy installation must be tested before relying on detections. This project does not operate doors and includes no garage automation or blueprint.**

## What it does

- One public repository: ESPHome external component and a HACS custom integration.
- A separate random credential for every car.
- Resumable setup with copyable ESPHome YAML and secrets entries.
- No WiFi connection required on the dongle; no custom software on your proxies.
- Fresh HMAC-SHA256 challenge-response over BLE, with no clock or flash counter requirement.
- Per-car recent-authentication sensor, timestamp, last-authenticating-proxy sensor, authentication event and test button.
- Standard Home Assistant Bluetooth routing and connection retry support.

A received advertisement only starts discovery. The integration reports authentication only after verifying a response to a fresh challenge. Authentication proves possession of a credential, not distance, arrival or permission to open a door. Live relay attacks and physical key extraction remain possible.

## Requirements

- Home Assistant 2026.9.0 or newer; Bluetooth integration configured.
- ESPHome 2026.8.2 or newer, ESP-IDF framework.
- An ESP32-S3 dongle (initial target: LILYGO T-Dongle-S3).
- An active-connection-capable ESPHome Bluetooth proxy or local Bluetooth adapter, with a free slot. Advertisement-only proxies cannot authenticate a dongle.

## Install and add a car

1. In HACS, add `https://github.com/danps1/ble-arrival` as a custom repository, category **Integration**. Install and restart Home Assistant.
2. Go to **Settings > Devices & services > Add integration > BLE Arrival**.
3. Select **Set up a new car**, enter its name and choose the board. Finish to save the pending car.
4. On that integration entry, select **Configure > Show ESPHome configuration**.
5. Copy either the complete new-device YAML or the existing-device snippet. Copy the separate credential entry into ESPHome's `secrets.yaml`.
6. Compile and flash the dongle over USB yourself. New-device YAML is USB/Bluetooth only. WiFi/API/OTA are optional additions for maintenance.
7. Power the dongle near a proxy. Select **Configure > Verify dongle** and submit.
8. Entities appear only after successful authentication. Use **Test connection** and inspect the authentication event and timestamp.

Close and resume Configure at any time. The credential is already saved before you copy it, including across HA restarts. Add another car by repeating the flow; credentials and verification state are independent.

For an existing dongle, select **Add an already configured dongle**, select the device and supply its existing 64-character key. Never use the public test credential in `examples/`.

## Existing ESPHome configuration

Merge the generated snippet into your existing YAML. Remove `esp32_ble_beacon` and any other custom BLE server setup. This component owns its GATT service and requires one client at a time. If retaining WiFi and native API, set both `reboot_timeout: 0s` because the car will routinely be away from your network. Do not add a WiFi wait to boot automation.

## State and multiple cars

Each car has its own HA config entry. A pending entry intentionally has no entities. Authenticated state is not restored from disk: it starts false after HA reload/restart. Freshness expires after 30 seconds without a successful exchange. Checks run at most every 10 seconds per car, with up to two cars connecting concurrently. A test button requests an immediate check; repeated button presses do not create overlapping requests.

**Last authenticated via** shows the proxy or local adapter that handled the last successful exchange. Its attributes include the source identifier and authentication timestamp. It retains that historical route when the car disappears; use **Recently authenticated** for freshness. Before a new success after HA restart, or when HA does not expose the connected route, it is unknown. It never substitutes the strongest advertisement receiver for the actual connection route.

Multiple proxies can hear a dongle. HA's Bluetooth manager and bleak-retry-connector handle route selection and retries; this project does not implement a guarantee that every failing proxy will be tried. Test failover on your network. A fixed dongle address is only a routing hint, not a credential.

## Revoke, replace and update

**Configure > Revoke credential and prepare a new one** retires the old key and returns the car to pending setup. Reopen configuration, flash the new credential over USB and verify. Other cars are unaffected. Removing the integration entry also stops its authentication checks. Revocation does not erase the old device's flash.

Updating from v0.1.0 to v0.1.1 needs only a HACS update and HA restart. Your dongles keep firmware v0.1.0 and do not need reflashing.

HACS updates the HA integration, not the dongle. Generated YAML pins the firmware component to a release tag. The protocol version is independent of the project version; incompatible protocol versions fail verification. See [compatibility](docs/compatibility.md).

Secrets remain in HA config storage and ESPHome secrets/build output. Protect backups and never publish personalised YAML, firmware images, setup screenshots or diagnostics containing credentials. Built-in diagnostics use an allowlist and exclude keys, car names, IDs, addresses and raw Bluetooth frames.

## Development

Use Python 3.14. Install `requirements-dev.txt` and run `pytest` and `ruff check .`. In a separate environment install `requirements-firmware.txt`, then run `esphome compile examples/t-dongle-s3.yaml`. The example is for compilation only.

Read [setup](docs/setup.md), [protocol](docs/protocol.md), [security](SECURITY.md), and the [hardware test checklist](docs/hardware-testing.md) before deployment.

## Verification status

Version 0.1.1 passes 38 automated tests covering protocol framing, replay rejection, Python/C++ message agreement, GATT authentication failures and cleanup, resumable configuration, and credential revocation. The ESP32-S3 firmware compiles with ESPHome 2026.8.2. These checks run locally against Home Assistant 2026.9.1 libraries. User-reported smoke testing of v0.1.0 confirmed USB flashing, successful verification and recovery of detection after moving the dongle. Full hardware acceptance testing remains necessary. Development does not modify a live Home Assistant instance.
