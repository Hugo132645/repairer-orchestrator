from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from common.config import settings

_SECRET_KEYS = {
    "authorization",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "client_secret",
    "cookie",
    "set-cookie",
}

_PATTERNS = [
    re.compile(r"(?i)\b(?:bearer)\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\bAIza[0-9A-Za-z_-]{20,}\b"),
]


def truncate_text(value: str) -> str:
    if len(value) <= settings.max_text_log_chars:
        return value
    return value[: settings.max_text_log_chars] + "...[truncated]"


def redact(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        cleaned = value
        for pattern in _PATTERNS:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        return truncate_text(cleaned)

    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in _SECRET_KEYS:
                output[key_text] = "[REDACTED]"
            else:
                output[key_text] = redact(item)
        return output

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [redact(item) for item in value]

    try:
        return redact(vars(value))
    except TypeError:
        return truncate_text(repr(value))
