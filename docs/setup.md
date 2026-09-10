# Setup and recovery

Install the HACS integration once. Each car is a separate integration entry. The New car flow commits its random credential before showing instructions, so flash time and HA restarts cannot silently replace it. Open Configure to display the full USB-only YAML, an existing-device snippet and the separate secrets entry.

The full YAML targets ESP32-S3 and requires no WiFi secrets. The snippet retains your own board/network configuration; remove the old beacon component and use ESP-IDF. Compile and flash via ESPHome Device Builder. This integration does not connect to Device Builder or flash devices.

Verification reads and authenticates the expected ID. Several nearby dongles are checked in a bounded scan; if setup is ambiguous, power only the dongle being enrolled. An existing-device flow requires the existing key and proves possession before committing its identity.

A wrong key, incompatible protocol, unavailable proxy or full connection slots must leave setup unverified. Check power, range and active connections, then retry. No connection-capable discovery is different from a successfully authenticated dongle.

Revoke and re-provision when replacing a key. Retaining the same provisioned device ID preserves entity IDs, but retire the old key and do not run two dongles with the same identity. For a second car use Add integration again.

Use the normal HA rename control for display naming. Changing a display name does not change the credential or require a reflash. The BLE name may continue showing the old firmware name.
