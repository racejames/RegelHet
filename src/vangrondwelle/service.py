from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from uuid import uuid4

from .crawler import crawl_contact_pages
from .extractor import extract_contact_info
from .models import ContactInfo, ProviderSeed
from .normalize import normalize_domain

LOGGER = logging.getLogger(__name__)


def scrape_domain(domain_input: str) -> ContactInfo:
    domain = normalize_domain(domain_input)
    parsed_input = urlparse(domain_input if "://" in domain_input else f"https://{domain}")
    start_url = f"{parsed_input.scheme or 'https'}://{domain}"
    request_id = str(uuid4())
    LOGGER.info(
        "Starting scrape request.",
        extra={"request_id": request_id, "domain": domain},
    )

    best_match = ContactInfo(domain=domain, notes=["No HTML pages were fetched."])
    pages = crawl_contact_pages(domain, request_id, start_url=start_url)
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


def scrape_seed(seed: ProviderSeed) -> ContactInfo:
    result = scrape_domain(seed.website_url)
    result.provider_name = seed.provider_name
    result.website_url = seed.website_url
    result.directory_source = seed.directory_source
    result.directory_detail_url = seed.directory_detail_url
    return result


def scrape_seeds(seeds: list[ProviderSeed], *, max_workers: int = 6) -> list[ContactInfo]:
    LOGGER.info(
        "Starting batch seed scrape.",
        extra={"request_id": "batch", "domain": "multi"},
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(scrape_seed, seeds))
    LOGGER.info(
        "Finished batch seed scrape.",
        extra={"request_id": "batch", "domain": "multi"},
    )
    return results
