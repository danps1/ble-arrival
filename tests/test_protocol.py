import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest

from custom_components.ble_arrival.protocol import (
    AuthenticationError,
    Challenge,
    decode_hex,
    parse_identity,
)
from custom_components.ble_arrival.provisioning import configuration, new_car

VECTOR = json.loads((Path(__file__).parent / "vectors/auth_v1.json").read_text())


def attempt():
    return Challenge(bytes.fromhex(VECTOR["nonce"]), time.monotonic() + 5, version=1)


def verify(c, **changes):
    args = dict(
        key=bytes.fromhex(VECTOR["key"]),
        expected_id=VECTOR["device_id"],
        identity=bytes.fromhex(VECTOR["identity"]),
        response=bytes.fromhex(VECTOR["response"]),
    )
    args.update(changes)
    return c.verify(**args)


def test_vector_and_single_use():
    c = attempt()
    verify(c)
    with pytest.raises(AuthenticationError):
        verify(c)


@pytest.mark.parametrize("field", ["key", "identity", "response"])
def test_tampering_and_consumption(field):
    c = attempt()
    value = bytearray.fromhex(VECTOR[field])
    value[-1] ^= 1
    with pytest.raises(AuthenticationError):
        verify(c, **{field: bytes(value)})
    with pytest.raises(AuthenticationError):
        verify(c)


def test_wrong_car():
    with pytest.raises(AuthenticationError):
        verify(attempt(), expected_id="ab" * 16)


def test_replay_across_new_attempt():
    with pytest.raises(AuthenticationError):
        verify(Challenge.create())


def test_expired_challenge():
    c = attempt()
    c.deadline = time.monotonic() - 1
    with pytest.raises(AuthenticationError):
        verify(c)


@pytest.mark.parametrize("size", [0, 16, 31, 33, 64])
def test_response_length(size):
    with pytest.raises(AuthenticationError):
        verify(attempt(), response=b"a" * size)


@pytest.mark.parametrize("value", [b"", b"a" * 19, b"a" * 21, bytes([3]) + b"a" * 19])
def test_identity_validation(value):
    with pytest.raises(AuthenticationError):
        parse_identity(value)


def test_hex_is_strict():
    with pytest.raises(ValueError):
        decode_hex("aa " * 32, 32)
    with pytest.raises(ValueError):
        decode_hex("gg" * 32, 32)


def test_independent_cars_and_repeatable_configuration():
    first = new_car('Family "car"\nname', "t_dongle_s3")
    second = new_car("Other", "t_dongle_s3")
    assert first["key"] != second["key"] and first["device_id"] != second["device_id"]
    assert configuration(first) == configuration(first)
    full, snippet, secret = configuration(first)
    assert first["key"] not in full and first["key"] not in snippet
    assert first["key"] in secret and "!secret" in full
    assert 'friendly_name: "Family "car"\nname"' not in full  # literal line break is escaped


def test_vector_message():
    message = bytes.fromhex(VECTOR["message"])
    assert (
        hmac.new(bytes.fromhex(VECTOR["key"]), message, hashlib.sha256).hexdigest()
        == VECTOR["response"]
    )
