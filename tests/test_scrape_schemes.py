from __future__ import annotations

from pathlib import Path

from vangrondwelle import service
from vangrondwelle.crawler import CrawledPage


def read_fixture(name: str) -> str:
    return Path(__file__).parent.joinpath("fixtures", name).read_text(encoding="utf-8")


def test_scrape_domain_preserves_http_scheme_for_start_url(monkeypatch) -> None:
    contact_page = read_fixture("contact_page.html")
    captured_start_urls: list[str] = []

    def fake_crawl_contact_pages(domain: str, request_id: str, *, start_url: str | None = None) -> list[CrawledPage]:
        assert domain == "voorbeeldzorg.nl"
        assert request_id
        captured_start_urls.append(start_url or "")
        return [CrawledPage(url="http://voorbeeldzorg.nl/contact", html=contact_page)]

    monkeypatch.setattr(service, "crawl_contact_pages", fake_crawl_contact_pages)

    result = service.scrape_domain("http://voorbeeldzorg.nl")

    assert captured_start_urls == ["http://voorbeeldzorg.nl"]
    assert result.source_url == "http://voorbeeldzorg.nl/contact"
