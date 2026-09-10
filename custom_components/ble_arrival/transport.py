"""Authenticated GATT exchange through Home Assistant's Bluetooth manager."""

import asyncio

from bleak import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth

from .const import CHALLENGE_UUID, IDENTITY_UUID, RESPONSE_UUID, SERVICE_UUID
from .protocol import AuthenticationError, Challenge, decode_hex, parse_identity


class DeviceUnavailable(Exception):
    """No usable Bluetooth route, or the connection failed."""


def candidates(hass, address: str | None = None) -> list:
    """Advertisements are discovery hints only, never credentials."""
    infos = bluetooth.async_discovered_service_info(hass, connectable=True)
    matching = [i for i in infos if SERVICE_UUID in [u.lower() for u in i.service_uuids]]
    matching.sort(key=lambda i: (i.address != address, -i.rssi))
    return matching


async def authenticate(hass, address: str, device_id: str | None, key: str) -> tuple[str, str]:
    """Return authenticated device identity and firmware; close every connection."""
    key_bytes = decode_hex(key, 32)
    device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if device is None:
        raise DeviceUnavailable("No connection-capable proxy can reach this dongle")
    client = None
    try:
        async with asyncio.timeout(20):
            client = await establish_connection(
                BleakClientWithServiceCache,
                device,
                "BLE Arrival",
                max_attempts=2,
                ble_device_callback=lambda: bluetooth.async_ble_device_from_address(
                    hass, address, connectable=True
                ),
            )
            identity = bytes(await client.read_gatt_char(IDENTITY_UUID))
            actual_id, firmware = parse_identity(identity)
            if device_id is not None and actual_id != device_id:
                raise AuthenticationError("Different dongle")
            challenge = Challenge.create()
            async with asyncio.timeout(5):
                await client.write_gatt_char(CHALLENGE_UUID, challenge.request(), response=True)
                response = bytes(await client.read_gatt_char(RESPONSE_UUID))
                challenge.verify(key_bytes, device_id or actual_id, identity, response)
            return actual_id, firmware
    except (TimeoutError, BleakError) as err:
        raise DeviceUnavailable("Bluetooth connection failed or timed out") from err
    finally:
        if client is not None:
            try:
                async with asyncio.timeout(3):
                    await client.disconnect()
            except TimeoutError, BleakError:
                pass
