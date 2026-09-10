"""Generate copyable YAML without reading or transmitting user credentials."""

import json
import secrets

from .const import FIRMWARE_REF, REPOSITORY
from .protocol import decode_hex

BOARDS = {"t_dongle_s3": "LILYGO T-Dongle-S3", "esp32_s3": "Generic ESP32-S3"}


def new_car(name: str, board: str) -> dict:
    if board not in BOARDS or not name.strip() or len(name) > 64:
        raise ValueError("Invalid car name or board")
    return {
        "name": name.strip(),
        "board": board,
        "device_id": secrets.token_hex(16),
        "key": secrets.token_hex(32),
        "verified": False,
    }


def configuration(data: dict) -> tuple[str, str, str]:
    """Return full USB-only config, component-only snippet and secrets entry."""
    device_id = data["device_id"]
    decode_hex(device_id, 16)
    decode_hex(data["key"], 32)
    secret_name = "ble_arrival_" + device_id
    snippet = f"""external_components:
  - source: github://{REPOSITORY}@{FIRMWARE_REF}
    components: [ble_arrival]

ble_arrival:
  device_id: "{device_id}"
  secret_key: !secret {secret_name}
"""
    full = f"""esphome:
  name: ble-arrival-{device_id[:8]}
  friendly_name: {json.dumps(data["name"])}
  min_version: 2026.8.2

esp32:
  board: esp32-s3-devkitc-1
  variant: esp32s3
  flash_mode: dio
  framework:
    type: esp-idf

logger:

{snippet}"""
    if data.get("board") == "t_dongle_s3":
        full += f"""
# Optional button-activated display (20 seconds):
# packages:
#   dongle_display: github://{REPOSITORY}/packages/t-dongle-s3-display.yaml@{FIRMWARE_REF}
# substitutions:
#   ble_arrival_display_name: "MY CAR"
"""
    return full, snippet, f'{secret_name}: "{data["key"]}"'
