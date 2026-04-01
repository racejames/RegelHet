from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import BeautifulSoup

from .models import ContactInfo
from .normalize import normalize_email, normalize_phone, normalize_text

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:(?:\+31|0031|0)\s*(?:\(0\)\s*)?(?:[\d\s\-()]){8,}\d)")
POSTCODE_RE = re.compile(r"\b\d{4}\s?[A-Z]{2}\b")
STREET_NAME_RE = r"(?:[A-ZÀ-ÿ][A-Za-zÀ-ÿ'’.\-]*\s){0,1}[A-ZÀ-ÿ][A-Za-zÀ-ÿ'’.\-]*(?:straat|laan|plein|weg|gracht|hof|kade|markt|park|plantsoen|boulevard|singel|dreef|steeg)"
ADDRESS_RE = re.compile(
    rf"({STREET_NAME_RE}\s+\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?(?:,\s*|\s+)\d{{4}}\s?[A-Z]{{2}}(?:,\s*|\s+)[A-ZÀ-ÿ][A-Za-zÀ-ÿ'’.\- ]+)",
    re.IGNORECASE,
)
ADDRESS_HINTS = (
    "straat",
    "laan",
    "plein",
    "weg",
    "gracht",
    "hof",
    "postbus",
)
PHONE_LABELS = ("telefoon", "tel", "bel", "contact")
EMAIL_LABELS = ("mail", "e-mail", "email", "contact")


def extract_contact_info(html: str, domain: str, source_url: str) -> ContactInfo:
    soup = BeautifulSoup(html, "html.parser")
    text_chunks = list(_iter_text_chunks(soup))
    addresses = _find_addresses(text_chunks)
    phones = _find_phones(soup, text_chunks)
    emails = _find_emails(soup, text_chunks, domain)

    notes: list[str] = []
    if not addresses:
        notes.append("No postal address detected.")
    if not phones:
        notes.append("No central phone number detected.")
    if not emails:
        notes.append("No central email address detected.")

    confidence = 0.0
    confidence += 0.4 if addresses else 0.0
    confidence += 0.3 if phones else 0.0
    confidence += 0.3 if emails else 0.0

    return ContactInfo(
        domain=domain,
        source_url=source_url,
        address=addresses[0] if addresses else None,
        phone=phones[0] if phones else None,
        email=emails[0] if emails else None,
        confidence=confidence,
        notes=notes,
    )


def _iter_text_chunks(soup: BeautifulSoup) -> Iterable[str]:
    for node in soup.find_all(["p", "li", "span", "address", "td"]):
        text = normalize_text(node.get_text(" ", strip=True))
        if text:
            yield text


def _find_addresses(chunks: list[str]) -> list[str]:
    matches: list[str] = []
    for chunk in chunks:
        for raw_match in ADDRESS_RE.findall(chunk):
            candidate = normalize_text(raw_match)
            if candidate:
                matches.append(candidate)

        if not POSTCODE_RE.search(chunk):
            continue

        postcode_match = POSTCODE_RE.search(chunk)
        if postcode_match is None:
            continue

        snippet_start = max(0, postcode_match.start() - 60)
        snippet_end = min(len(chunk), postcode_match.end() + 60)
        candidate = normalize_text(chunk[snippet_start:snippet_end])
        if not candidate:
            continue
        lowered = candidate.lower()
        if any(hint in lowered for hint in ADDRESS_HINTS) or "postbus" in lowered:
            matches.append(candidate)
        elif re.search(r"\b\d{1,4}[a-zA-Z]?\b", candidate):
            matches.append(candidate)
    return _dedupe(matches)


def _find_phones(soup: BeautifulSoup, chunks: list[str]) -> list[str]:
    matches: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith("tel:"):
            normalized = normalize_phone(href.removeprefix("tel:"))
            if normalized and not normalized.startswith("06"):
                matches.append(normalized)

    for chunk in chunks:
        lowered = chunk.lower()
        if not any(label in lowered for label in PHONE_LABELS):
            continue
        for candidate in PHONE_RE.findall(chunk):
            normalized = normalize_phone(candidate)
            if normalized:
                matches.append(normalized)

    return _dedupe(_rank_phones(matches))


def _find_emails(soup: BeautifulSoup, chunks: list[str], domain: str) -> list[str]:
    matches: list[str] = []
    domain_suffix = domain.lower()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith("mailto:"):
            email = normalize_email(href.removeprefix("mailto:").split("?")[0])
            if email:
                matches.append(email)

    for chunk in chunks:
        lowered = chunk.lower()
        if not any(label in lowered for label in EMAIL_LABELS):
            continue
        for candidate in EMAIL_RE.findall(chunk):
            matches.append(candidate)

    ranked = []
    for email in _dedupe(matches):
        if domain_suffix and not email.endswith(domain_suffix):
            continue
        if any(token in email for token in ("noreply", "no-reply", "privacy", "factuur")):
            continue
        ranked.append(email)
    return ranked


def _rank_phones(values: list[str]) -> list[str]:
    def score(value: str) -> tuple[int, int]:
        central_bonus = 1 if value.startswith(("0800", "0900", "+31", "0")) else 0
        mobile_penalty = -1 if value.startswith("06") else 0
        return (central_bonus + mobile_penalty, -len(value))

    return sorted(values, key=score, reverse=True)


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output
