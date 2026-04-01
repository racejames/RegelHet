from vangrondwelle import service
from vangrondwelle.models import ContactInfo, ProviderSeed


def test_scrape_seeds_returns_results_for_each_seed(monkeypatch) -> None:
    seeds = [
        ProviderSeed(
            provider_name="Zorgbedrijf A",
            website_url="https://www.zorgbedrijfa.nl",
            domain="zorgbedrijfa.nl",
            directory_source="ZorgkaartNederland",
            directory_detail_url="https://www.zorgkaartnederland.nl/a",
        ),
        ProviderSeed(
            provider_name="Zorgbedrijf B",
            website_url="https://www.zorgbedrijfb.nl",
            domain="zorgbedrijfb.nl",
            directory_source="ZorgkaartNederland",
            directory_detail_url="https://www.zorgkaartnederland.nl/b",
        ),
    ]

    def fake_scrape_seed(seed: ProviderSeed) -> ContactInfo:
        return ContactInfo(domain=seed.domain, provider_name=seed.provider_name)

    monkeypatch.setattr(service, "scrape_seed", fake_scrape_seed)

    results = service.scrape_seeds(seeds, max_workers=2)

    assert [result.domain for result in results] == ["zorgbedrijfa.nl", "zorgbedrijfb.nl"]
