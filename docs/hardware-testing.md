# Hardware acceptance checklist

Run this with notifications only. No garage automation is included.

- Flash generated configuration into a T-Dongle-S3 and verify through a real active ESPHome proxy.
- Confirm authentication with the default ATT MTU, including the full 32-byte response read.
- Power-cycle the dongle and restart HA; require a new authentication before recent status becomes true.
- Close the setup wizard and restart HA before flashing; confirm the same pending credential is shown afterward.
- Verify wrong keys, wrong device IDs, malformed challenges and old captured responses never produce an authenticated event.
- Leave the radio range and confirm recent authentication expires within 30 seconds plus scheduler delay, including when connection status changes to connection_failed first.
- With v0.1.1, confirm Last authenticated via names the active proxy. Move between coverage areas and check it changes after successful authentication. It should retain the previous successful route during failures or absence.
- If duplicate setup rows appear, refresh the browser and confirm whether they persist before removing any entries. The temporary duplicate report has not been reproduced in the backend.
- Test two cars simultaneously. Check separate credentials and avoid sustained connection-slot exhaustion.
- Disable one of two proxies and verify recovery through the other. Test occupied connection slots and WiFi roaming.
- Revoke during an in-flight exchange and confirm no subsequent event from the retired entry.
- Revoke/reflash one car and confirm another remains operational.
- Confirm Bluetooth operation with WiFi unavailable and USB power supplied by the car.
- Record actual arrival latency, RF range and ESPHome/HA/proxy versions in your own private deployment notes.

Authentication of a stationary or relayed dongle is not an arrival signal. Keep any later door automation separate and require independent arrival policy.

## v0.2.0 acceptance

- Update HA first: verify an old dongle still authenticates with unknown uptime.
- Flash new firmware with the existing credentials. Verify uptime appears as seconds in both the diagnostic sensor and Authentication event attributes.
- Power-cycle the dongle: the next authenticated reading should return close to zero. Check values on both sides of 300 seconds.
- Unplug or block reception: no new events, no increasing extrapolated uptime, and recent-authentication expires after about 30 seconds.
- Reconnect via different proxies and check protocol 2 long reads succeed.
- Test multiple cars, each with its independent uptime and key.
- Optional screen: dark on boot, button lights it for 20 seconds, repeat press extends the timeout, BLE authentication continues while dark or lit.
- Test the intended arrival condition in notification-only mode. Leaving a started car in the garage beyond five minutes must not produce an arrival action. A short journey may fail your uptime threshold.

Earlier user-provided v0.1.1 logs confirmed route changes among Bluetooth sources, approximately 31-second freshness expiry despite a connection failure, and recovery. The standalone display snippet was reported working on a LilyGO dongle. Protocol 2 and the combined release require new hardware testing.
