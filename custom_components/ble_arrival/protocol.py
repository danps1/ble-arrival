"""Small, transport-independent protocol. Never log keys or response frames."""

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

PROTOCOL_VERSION = 2
CONTEXT = b"BLE-ARRIVAL-AUTH\x00"


class AuthenticationError(ValueError):
    """A response cannot establish current possession of the credential."""


def decode_hex(value: str, length: int) -> bytes:
    """Strict canonical hex; reject whitespace and weak example credentials."""
    if len(value) != length * 2 or any(c not in "0123456789abcdefABCDEF" for c in value):
        raise ValueError("Invalid hexadecimal value")
    return bytes.fromhex(value)


def parse_identity(value: bytes) -> tuple[str, str]:
    if len(value) != 20 or value[0] not in (1, PROTOCOL_VERSION):
        raise AuthenticationError("Unsupported identity or protocol")
    return value[1:17].hex(), ".".join(str(x) for x in value[17:20])


@dataclass
class Challenge:
    """One local attempt, consumed on its first verification, including failure."""

    nonce: bytes
    deadline: float
    consumed: bool = False
    version: int = PROTOCOL_VERSION

    @classmethod
    def create(cls, timeout: float = 5.0, *, version: int = PROTOCOL_VERSION):
        if version not in (1, PROTOCOL_VERSION):
            raise AuthenticationError("Unsupported challenge protocol")
        return cls(secrets.token_bytes(16), time.monotonic() + timeout, version=version)

    def request(self) -> bytes:
        return bytes([self.version]) + self.nonce

    def verify(self, key: bytes, expected_id: str, identity: bytes, response: bytes) -> int | None:
        if self.consumed:
            raise AuthenticationError("Challenge already consumed")
        self.consumed = True
        if time.monotonic() >= self.deadline:
            raise AuthenticationError("Challenge expired")
        device_id, _ = parse_identity(identity)
        if (
            identity[0] != self.version
            or device_id != expected_id
            or len(key) != 32
            or len(response) != (40 if self.version == 2 else 32)
        ):
            raise AuthenticationError("Identity or response mismatch")
        uptime = response[:8] if self.version == 2 else b""
        mac = response[8:] if self.version == 2 else response
        expected = hmac.new(key, CONTEXT + identity + self.nonce + uptime, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, mac):
            raise AuthenticationError("Authentication failed")
        return int.from_bytes(uptime, "little") if uptime else None
