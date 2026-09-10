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
