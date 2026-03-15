import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from src.config.settings import settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def verify_admin_password(password: str) -> bool:
    return hmac.compare_digest(password, settings.ADMIN_PASSWORD)


def create_session_token(subject: str = "owner") -> str:
    payload = {
        "sub": subject,
        "exp": int(time.time()) + settings.session_max_age_days * 24 * 60 * 60,
    }
    payload_encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.SESSION_SECRET.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{payload_encoded}.{_b64encode(signature)}"


def decode_session_token(token: str) -> Optional[dict]:
    try:
        payload_encoded, signature_encoded = token.split(".", 1)
    except ValueError:
        return None

    expected_signature = hmac.new(
        settings.SESSION_SECRET.encode("utf-8"),
        payload_encoded.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(_b64encode(expected_signature), signature_encoded):
        return None

    try:
        payload = json.loads(_b64decode(payload_encoded).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("exp", 0) < int(time.time()):
        return None

    return payload
