from __future__ import annotations

import re
from urllib.parse import urlparse

WHITESPACE_RE = re.compile(r"\s+")
PHONE_CLEAN_RE = re.compile(r"[^\d+]")


def normalize_domain(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        return ""

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    return host.lower().removeprefix("www.")


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = WHITESPACE_RE.sub(" ", value).strip(" ,;\n\t")
    return cleaned or None


def normalize_phone(value: str | None) -> str | None:
    text = normalize_text(value)
    if not text:
        return None

    compact = PHONE_CLEAN_RE.sub("", text)
    compact = compact.replace("0031", "+31")
    if compact.startswith("31") and not compact.startswith("+31"):
        compact = f"+{compact}"
    if compact.startswith("06"):
        return None
    if compact.startswith("0800") or compact.startswith("0900"):
        return compact
    if compact.startswith("0"):
        return compact
    if compact.startswith("+31"):
        return compact
    return text


def normalize_email(value: str | None) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    return text.lower()
