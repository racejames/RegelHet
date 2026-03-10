from __future__ import annotations

import logging
from uuid import uuid4

from .crawler import crawl_contact_pages
from .extractor import extract_contact_info
from .models import ContactInfo
from .normalize import normalize_domain

LOGGER = logging.getLogger(__name__)


def scrape_domain(domain_input: str) -> ContactInfo:
    domain = normalize_domain(domain_input)
    request_id = str(uuid4())
    LOGGER.info(
        "Starting scrape request.",
        extra={"request_id": request_id, "domain": domain},
    )

    best_match = ContactInfo(domain=domain, notes=["No HTML pages were fetched."])
    pages = crawl_contact_pages(domain, request_id)
    for page in pages:
        candidate = extract_contact_info(page.html, domain, page.url)
        if candidate.confidence > best_match.confidence:
            best_match = candidate

    LOGGER.info(
        "Finished scrape request.",
        extra={
            "request_id": request_id,
            "domain": domain,
            "url": best_match.source_url,
        },
    )
    return best_match
