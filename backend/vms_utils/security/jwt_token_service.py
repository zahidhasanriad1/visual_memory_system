import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


class JwtTokenService:
    """
    Lightweight HS256 JWT service without external dependency.
    """

    def __init__(self) -> None:
        self.secret_key = os.getenv(
            "JWT_SECRET_KEY",
            "change-this-secret-key-for-vms-x-development",
        )
        self.expires_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    def create_access_token(self, claims: dict[str, Any]) -> str:
        now = int(time.time())

        payload = {
            **claims,
            "iat": now,
            "exp": now + self.expires_minutes * 60,
        }

        header = {
            "alg": "HS256",
            "typ": "JWT",
        }

        header_b64 = self._base64url_encode_json(header)
        payload_b64 = self._base64url_encode_json(payload)

        signing_input = f"{header_b64}.{payload_b64}"
        signature = self._sign(signing_input)

        return f"{signing_input}.{signature}"

    def verify_access_token(self, token: str) -> dict[str, Any]:
        parts = token.split(".")

        if len(parts) != 3:
            raise ValueError("Invalid token format.")

        header_b64, payload_b64, signature = parts
        signing_input = f"{header_b64}.{payload_b64}"

        expected_signature = self._sign(signing_input)

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature.")

        payload = json.loads(self._base64url_decode(payload_b64).decode("utf-8"))

        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token expired.")

        return payload

    def _sign(self, signing_input: str) -> str:
        digest = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        return self._base64url_encode_bytes(digest)

    def _base64url_encode_json(self, value: dict[str, Any]) -> str:
        raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
        return self._base64url_encode_bytes(raw)

    def _base64url_encode_bytes(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")

    def _base64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("utf-8"))