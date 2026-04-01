from __future__ import annotations

import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import ProviderSeed
from .normalize import normalize_domain

LOGGER = logging.getLogger(__name__)
ZORGKAART_BASE_URL = "https://www.zorgkaartnederland.nl"
DEN_HAAG_LISTING_PATH = "/den-haag"
ZORGKAART_SOURCE_NAME = "ZorgkaartNederland"


def discover_den_haag_provider_seeds(
    *,
    max_pages: int | None = None,
    max_providers: int | None = None,
    delay_seconds: float = 0.2,
    session: requests.Session | None = None,
) -> list[ProviderSeed]:
    client = session or requests.Session()
    total_pages = _discover_total_pages(client)
    page_limit = min(max_pages, total_pages) if max_pages is not None else total_pages
    detail_urls: list[str] = []

    for page_number in range(1, page_limit + 1):
        list_url = _build_page_url(page_number)
        LOGGER.info(
            "Fetching directory page.",
            extra={"domain": "zorgkaartnederland.nl", "url": list_url, "request_id": "discovery"},
        )
        response = client.get(list_url, timeout=20, headers={"User-Agent": "vanGrondwelle/0.2"})
        response.raise_for_status()
        detail_urls.extend(_extract_detail_urls(response.text))
        if delay_seconds:
            time.sleep(delay_seconds)

    seeds: list[ProviderSeed] = []
    seen_domains: set[str] = set()
    for detail_url in detail_urls:
        LOGGER.info(
            "Fetching directory detail page.",
            extra={"domain": "zorgkaartnederland.nl", "url": detail_url, "request_id": "discovery"},
        )
        response = client.get(detail_url, timeout=20, headers={"User-Agent": "vanGrondwelle/0.2"})
        response.raise_for_status()
        seed = _extract_provider_seed(response.text, detail_url)
        if delay_seconds:
            time.sleep(delay_seconds)
        if seed is None or seed.domain in seen_domains:
            continue
        seen_domains.add(seed.domain)
        seeds.append(seed)
        if max_providers is not None and len(seeds) >= max_providers:
            break

    return seeds


def _discover_total_pages(session: requests.Session) -> int:
    response = session.get(
        urljoin(ZORGKAART_BASE_URL, DEN_HAAG_LISTING_PATH),
        timeout=20,
        headers={"User-Agent": "vanGrondwelle/0.2"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    page_numbers: list[int] = [1]
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if "/den-haag/pagina" not in href:
            continue
        suffix = href.rsplit("pagina", 1)[-1]
        if suffix.isdigit():
            page_numbers.append(int(suffix))
    return max(page_numbers)


def _build_page_url(page_number: int) -> str:
    if page_number == 1:
        return urljoin(ZORGKAART_BASE_URL, DEN_HAAG_LISTING_PATH)
    return urljoin(ZORGKAART_BASE_URL, f"{DEN_HAAG_LISTING_PATH}/pagina{page_number}")


def _extract_detail_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not href.startswith("/zorginstelling/"):
            continue
        if "/wachttijden" in href:
            continue
        urls.append(urljoin(ZORGKAART_BASE_URL, href.split("#", 1)[0]))
    return list(dict.fromkeys(urls))


def _extract_provider_seed(html: str, detail_url: str) -> ProviderSeed | None:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1")
    provider_name = title.get_text(" ", strip=True) if title else ""
    website_url = ""

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        text = anchor.get_text(" ", strip=True)
        if text.lower() == "bezoek website":
            website_url = href
            break

    if not provider_name or not website_url:
        return None

    domain = normalize_domain(website_url)
    if not domain:
        return None

    return ProviderSeed(
        provider_name=provider_name,
        website_url=website_url,
        domain=domain,
        directory_source=ZORGKAART_SOURCE_NAME,
        directory_detail_url=detail_url,
    )
