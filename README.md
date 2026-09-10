# BLE Arrival

Authenticated Bluetooth detection for cars using an ESPHome USB dongle and Home Assistant's existing active Bluetooth proxies.

**Experimental v0.2.0. Software tests are included; a real T-Dongle-S3 and proxy installation must be tested before relying on detections. This project does not operate doors and includes no garage automation or blueprint.**

## What it does

- One public repository: ESPHome external component and a HACS custom integration.
- A separate random credential for every car.
- Resumable setup with copyable ESPHome YAML and secrets entries.
- No WiFi connection required on the dongle; no custom software on your proxies.
- Fresh HMAC-SHA256 challenge-response over BLE, with no clock or flash counter requirement.
- Per-car recent-authentication sensor, timestamp, authenticated uptime in seconds, last-authenticating-proxy sensor, authentication event and test button.
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

Version 0.2.0 passes 62 automated tests covering protocol framing, replay rejection, Python/C++ message agreement, GATT authentication failures and cleanup, resumable configuration, and credential revocation. The ESP32-S3 firmware compiles with ESPHome 2026.8.2. These checks run locally against Home Assistant 2026.9.1 libraries. User-reported smoke testing of v0.1.0 confirmed USB flashing, successful verification and recovery of detection after moving the dongle. Full hardware acceptance testing remains necessary. Development does not modify a live Home Assistant instance.

## Authenticated uptime and updating to v0.2.0

Update the HACS integration and restart HA **before** reflashing dongles. Existing protocol 1 dongles continue authenticating but their uptime is unknown. In your existing ESPHome YAML change the external-component tag from `@v0.1.0` to `@v0.2.0`, keeping your device ID and secret unchanged, then compile and flash over USB. Alternatively reopen Configure > Show ESPHome configuration for the new pinned tag. Do not revoke or regenerate credentials for this update. Generic ESP32-S3 devices do not need the LilyGO display package.

The diagnostic sensor **Uptime at last authentication** stores an integer number of seconds measured at the last verified handshake. It is a historical snapshot, not an increasing clock; it stays unchanged on failed exchanges and becomes unknown after HA restart or a successful legacy exchange. Its `authenticated_at` attribute identifies the sample time. Each Authentication event also contains `uptime_seconds` from that same verified exchange, avoiding sensor-update ordering races.

For a five-minute rule, require a fresh arrival and `uptime_seconds > 300`. Exactly 300 seconds does not pass a strict greater-than rule. Reject missing/unknown uptime. Authentication events repeat while a car is present: **do not trigger solely on every authentication plus the uptime threshold**, or a car started in the garage could open the door after five minutes. Your automation must independently establish an arrival, evaluate that arrival's authenticated uptime, and suppress subsequent checks while the car remains present. Uptime does not replace presence/departure tracking. This release adds data only, with no garage automation or blueprint.

Uptime resets on any dongle reboot, including power interruptions. A USB port that remains powered while parked can defeat this startup filter, while a journey shorter than the chosen threshold will be excluded. Live relay and physical credential extraction remain limitations.

## Optional LilyGO T-Dongle-S3 display

Add this to your existing personalised dongle YAML, merging existing `packages` and `substitutions` sections:

```yaml
packages:
  dongle_display: github://danps1/ble-arrival/packages/t-dongle-s3-display.yaml@v0.2.0
substitutions:
  ble_arrival_display_name: "MY CAR"
```

Use a short plain-text label without quotes or backslashes inside it. The HA-generated complete configuration includes these optional lines as comments for LilyGO boards. If you already pasted the standalone display configuration, keep it or replace it with this package; do not include both, as they share pins and IDs.

The screen starts dark. Press the GPIO0 button for 20 seconds of backlight at 60%; pressing again restarts the timer. It shows your label, BLE connection state, time since the last BLE connection and uptime. BLE continues while the screen is dark. Connection activity is not authenticated HA acceptance, and the dongle cannot show the proxy's HA name. The package uses the hardware-tested display layout reported by a user, with an optional label. Its Google font is fetched at build time; runtime WiFi is not needed.

The public `examples/t-dongle-s3-display.yaml` builds the combined firmware and display in CI. It contains a public test credential through its base example: never flash it to a real car.
