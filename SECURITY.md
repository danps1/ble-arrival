# Security

This experimental project authenticates a Bluetooth credential. It is not a certified access-control system and does not prove arrival, distance, driver identity or authorisation to operate a door.

## Intended properties

A fresh 128-bit random HA challenge, strict framing, full HMAC-SHA256, per-car 256-bit keys, constant-time comparison, a short verification deadline and single-use local challenge state protect against passive copying and later replay of an old response. HA never treats advertisements as authenticated detections. Restart/reload discards successful state. Invalid or unavailable exchanges do not create success events.

## Boundaries

- A live relay to the genuine dongle can succeed. RSSI does not provide secure distance measurement.
- A stolen dongle can act as the credential; extracting flash may disclose its key. Secure boot and flash encryption are not provisioned by this project.
- Compromise of HA, ESPHome build output, backups or a secret invalidates the security assumptions. Keys are stored in ordinary HA config storage, not a separate vault.
- BLE connection flooding, jamming and interference can deny service. Rate limits and connection timeouts bound ordinary resource usage but cannot prevent RF denial of service.
- A static discovery identity permits tracking. Advertisement privacy is not a goal of version 1.
- The verifier accepts one response per short-lived challenge. The dongle is a signing oracle for this narrowly domain-separated protocol; it does not authenticate HA.
- Two copies of the same credential cannot be distinguished. Provision one key per car and revoke a lost credential.

## Reporting

Use GitHub's private vulnerability reporting if it is enabled for this repository. If unavailable, open an issue asking for a private contact channel without posting exploit details or credentials. Never attach personalised configuration, firmware binaries or setup screenshots containing secrets.

## Review status

Tests cover framing, cross-language message construction, replay, expiry, identity binding and selected lifecycle paths. They do not constitute an independent security audit. Real-device and multi-proxy acceptance remains necessary.
