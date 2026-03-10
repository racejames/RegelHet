from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)
DISCOVERY_KEYWORDS = (
    "contact",
    "bereikbaarheid",
    "locatie",
    "locaties",
    "organisatie",
    "over-ons",
)


@dataclass(slots=True)
class CrawledPage:
    url: str
    html: str


def crawl_contact_pages(
    domain: str,
    request_id: str,
    *,
    session: requests.Session | None = None,
    max_pages: int = 8,
    timeout: int = 12,
) -> list[CrawledPage]:
    client = session or requests.Session()
    start_url = f"https://{domain}"
    queue = deque([start_url])
    visited: set[str] = set()
    pages: list[CrawledPage] = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        response = _fetch_url(client, url, request_id, domain, timeout)
        if response is None:
            continue

        pages.append(CrawledPage(url=url, html=response.text))
        for next_url in _discover_contact_links(response.text, url, domain):
            if next_url not in visited and next_url not in queue and len(visited) + len(queue) < max_pages:
                queue.append(next_url)

    return pages


def _fetch_url(
    session: requests.Session,
    url: str,
    request_id: str,
    domain: str,
    timeout: int,
) -> requests.Response | None:
    LOGGER.info(
        "Fetching candidate page.",
        extra={"request_id": request_id, "domain": domain, "url": url},
    )
    try:
        response = session.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "vanGrondwelle/0.1 (+https://github.com/racejames/vanGrondwelle)"},
        )
        LOGGER.info(
            "Fetched page response.",
            extra={
                "request_id": request_id,
                "domain": domain,
                "url": url,
                "status_code": response.status_code,
            },
        )
        if response.status_code >= 400:
            return None
        if "text/html" not in response.headers.get("Content-Type", ""):
            return None
        return response
    except requests.RequestException:
        LOGGER.exception(
            "Failed to fetch page.",
            extra={"request_id": request_id, "domain": domain, "url": url},
        )
        return None


def _discover_contact_links(html: str, base_url: str, domain: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    matches: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        text = anchor.get_text(" ", strip=True).lower()
        target = href.lower()
        if not any(keyword in f"{text} {target}" for keyword in DISCOVERY_KEYWORDS):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc and parsed.netloc.lower().removeprefix("www.") != domain:
            continue
        matches.append(absolute.split("#", 1)[0])
    return list(dict.fromkeys(matches))
