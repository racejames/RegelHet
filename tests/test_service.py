from __future__ import annotations

from pathlib import Path

from vangrondwelle import service
from vangrondwelle.crawler import CrawledPage


def read_fixture(name: str) -> str:
    return Path(__file__).parent.joinpath("fixtures", name).read_text(encoding="utf-8")


def test_scrape_domain_returns_best_contact_page(monkeypatch) -> None:
    home_page = read_fixture("home_page.html")
    contact_page = read_fixture("contact_page.html")

    def fake_crawl_contact_pages(domain: str, request_id: str) -> list[CrawledPage]:
        assert domain == "voorbeeldzorg.nl"
        assert request_id
        return [
            CrawledPage(url="https://voorbeeldzorg.nl", html=home_page),
            CrawledPage(url="https://voorbeeldzorg.nl/contact", html=contact_page),
        ]

    monkeypatch.setattr(service, "crawl_contact_pages", fake_crawl_contact_pages)

    result = service.scrape_domain("https://www.voorbeeldzorg.nl")

    assert result.source_url == "https://voorbeeldzorg.nl/contact"
    assert result.phone == "0201234567"
    assert result.email == "info@voorbeeldzorg.nl"
