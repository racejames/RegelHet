from pathlib import Path

from vangrondwelle.discovery import _discover_total_pages, _extract_detail_urls, _extract_provider_seed


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, html: str) -> None:
        self.html = html

    def get(self, url: str, timeout: int, headers: dict[str, str]) -> FakeResponse:
        return FakeResponse(self.html)


def read_fixture(name: str) -> str:
    return Path(__file__).parent.joinpath("fixtures", name).read_text(encoding="utf-8")


def test_extract_detail_urls_filters_to_unique_organization_pages() -> None:
    html = read_fixture("zorgkaart_listing_den_haag.html")

    urls = _extract_detail_urls(html)

    assert urls == [
        "https://www.zorgkaartnederland.nl/zorginstelling/fysiotherapiepraktijk-zorgbedrijf-a-den-haag-1001",
        "https://www.zorgkaartnederland.nl/zorginstelling/thuiszorg-zorgbedrijf-b-den-haag-1002",
    ]


def test_extract_provider_seed_returns_provider_metadata() -> None:
    html = read_fixture("zorgkaart_detail_den_haag.html")

    seed = _extract_provider_seed(
        html,
        "https://www.zorgkaartnederland.nl/zorginstelling/fysiotherapiepraktijk-zorgbedrijf-a-den-haag-1001",
    )

    assert seed is not None
    assert seed.provider_name == "Zorgbedrijf A"
    assert seed.domain == "zorgbedrijfa.nl"
    assert seed.website_url == "https://www.zorgbedrijfa.nl"


def test_discover_total_pages_reads_last_pagination_number() -> None:
    html = read_fixture("zorgkaart_listing_den_haag.html")

    total_pages = _discover_total_pages(FakeSession(html))

    assert total_pages == 12
