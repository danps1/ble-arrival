"""Authenticated uptime framing, tampering and legacy compatibility."""

import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest

from custom_components.ble_arrival.protocol import AuthenticationError, Challenge

V = json.loads((Path(__file__).parent / "vectors/auth_v2.json").read_text())


def challenge():
    return Challenge(bytes.fromhex(V["nonce"]), time.monotonic() + 5)


def verify(c, response=None, identity=None):
    return c.verify(
        bytes.fromhex(V["key"]),
        V["device_id"],
        bytes.fromhex(V["identity"]) if identity is None else identity,
        bytes.fromhex(V["response"]) if response is None else response,
    )


def test_v2_vector_and_single_use():
    c = challenge()
    assert c.request()[0] == 2
    assert verify(c) == V["uptime_seconds"]
    with pytest.raises(AuthenticationError):
        verify(c)


@pytest.mark.parametrize("offset", [0, 7, 8, 39])
def test_uptime_and_mac_tampering(offset):
    frame = bytearray.fromhex(V["response"])
    frame[offset] ^= 1
    c = challenge()
    with pytest.raises(AuthenticationError):
        verify(c, bytes(frame))
    with pytest.raises(AuthenticationError):
        verify(c)


@pytest.mark.parametrize("seconds", [0, 299, 300, 301, 4294968, 2**32, 2**64 - 1])
def test_seconds_boundaries(seconds):
    identity = bytes.fromhex(V["identity"])
    uptime = seconds.to_bytes(8, "little")
    mac = hmac.digest(
        bytes.fromhex(V["key"]),
        b"BLE-ARRIVAL-AUTH\0" + identity + bytes.fromhex(V["nonce"]) + uptime,
        hashlib.sha256,
    )
    assert verify(challenge(), uptime + mac) == seconds


@pytest.mark.parametrize("size", [0, 8, 32, 39, 41])
def test_v2_rejects_wrong_frame_length(size):
    with pytest.raises(AuthenticationError):
        verify(challenge(), bytes(size))


def test_v2_replay_and_expiry():
    with pytest.raises(AuthenticationError):
        verify(Challenge.create())
    c = challenge()
    c.deadline = time.monotonic() - 1
    with pytest.raises(AuthenticationError):
        verify(c)


def test_cannot_downgrade_challenge():
    identity = b"\x01" + bytes.fromhex(V["identity"])[1:]
    mac = hmac.digest(
        bytes.fromhex(V["key"]),
        b"BLE-ARRIVAL-AUTH\0" + identity + bytes.fromhex(V["nonce"]),
        hashlib.sha256,
    )
    with pytest.raises(AuthenticationError):
        verify(challenge(), mac, identity)


def test_legacy_response_has_no_uptime():
    v = json.loads((Path(__file__).parent / "vectors/auth_v1.json").read_text())
    c = Challenge(bytes.fromhex(v["nonce"]), time.monotonic() + 5, version=1)
    assert c.request()[0] == 1
    assert (
        c.verify(
            bytes.fromhex(v["key"]),
            v["device_id"],
            bytes.fromhex(v["identity"]),
            bytes.fromhex(v["response"]),
        )
        is None
    )
