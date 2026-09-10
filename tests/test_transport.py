"""Exercise the real HA transport with a simulated remote GATT client."""

import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.ble_arrival import transport
from custom_components.ble_arrival.const import IDENTITY_UUID
from custom_components.ble_arrival.protocol import AuthenticationError

KEY = bytes(range(32))
ID = bytes(range(16))
IDENTITY = b"\x01" + ID + b"\x00\x01\x00"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [None, "wrong_id", "bad_mac", "timeout"])
async def test_exchange_disconnects_and_rejects(monkeypatch, failure):
    client = AsyncMock()
    client._connected_scanner = SimpleNamespace(source="proxy-b", name="Garage proxy")

    async def disconnect():
        client._connected_scanner = None

    client.disconnect.side_effect = disconnect
    request = None

    async def write(uuid, value, response):
        nonlocal request
        assert response is True
        request = value

    async def read(uuid):
        if uuid == IDENTITY_UUID:
            return IDENTITY
        if failure == "timeout":
            raise TimeoutError
        if failure == "bad_mac":
            return bytes(32)
        return hmac.digest(KEY, b"BLE-ARRIVAL-AUTH\0" + IDENTITY + request[1:], hashlib.sha256)

    client.write_gatt_char.side_effect = write
    client.read_gatt_char.side_effect = read
    monkeypatch.setattr(
        transport.bluetooth,
        "async_ble_device_from_address",
        lambda *a, **k: SimpleNamespace(details={"source": "proxy-a"}),
    )
    monkeypatch.setattr(transport, "establish_connection", AsyncMock(return_value=client))
    expected_id = bytes(16).hex() if failure == "wrong_id" else ID.hex()
    if failure:
        expected_error = (
            transport.DeviceUnavailable if failure == "timeout" else AuthenticationError
        )
        with pytest.raises(expected_error):
            await transport.authenticate(None, "address", expected_id, KEY.hex())
    else:
        assert await transport.authenticate(
            None, "address", expected_id, KEY.hex()
        ) == transport.AuthenticationResult(ID.hex(), "0.1.0", "proxy-b", "Garage proxy")
    client.disconnect.assert_awaited_once()
    if failure == "wrong_id":
        client.write_gatt_char.assert_not_awaited()


@pytest.mark.parametrize(
    "scanner", [None, object(), SimpleNamespace(source=None), SimpleNamespace(source=42)]
)
def test_missing_route_is_unknown(scanner):
    assert transport._connection_route(SimpleNamespace(_connected_scanner=scanner)) == (None, None)


def test_route_without_name_uses_source():
    assert transport._connection_route(
        SimpleNamespace(_connected_scanner=SimpleNamespace(source="proxy-b"))
    ) == ("proxy-b", "proxy-b")


def test_real_ha_wrapper_tracks_and_clears_route(monkeypatch):
    from bleak.backends.device import BLEDevice
    from habluetooth import wrappers
    from habluetooth.usage import HaBleakClientWithServiceCache

    monkeypatch.setattr(wrappers, "get_manager", lambda: object())
    device = BLEDevice("00:11:22:33:44:55", "Test dongle", {})
    client = HaBleakClientWithServiceCache(device)
    scanner = SimpleNamespace(source="proxy-b", name="Garage", _clients=set())
    client._track(scanner, device)
    assert transport._connection_route(client) == ("proxy-b", "Garage")
    client._untrack()
    assert transport._connection_route(client) == (None, None)
