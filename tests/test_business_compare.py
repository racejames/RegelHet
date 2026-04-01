import requests

from vangrondwelle.business_compare import BusinessComparisonRow, render_comparison_table
from vangrondwelle.business_sources import build_business_comparison


def test_render_comparison_table_shows_all_scenarios() -> None:
    rows = [
        BusinessComparisonRow(
            scenario="Open source",
            source="OpenStreetMap",
            business_name="Installatieburo Hevi BV",
            street_address="Dorpsstraat 1",
            postcode="3981 AA",
            city="Bunnik",
            business_type="installatiebedrijf",
            confidence="medium",
            notes=["Matched by name."],
        ),
        BusinessComparisonRow(
            scenario="Places",
            source="Google Places",
            business_name="Installatieburo Hevi BV",
            street_address=None,
            postcode=None,
            city="Bunnik",
            business_type=None,
            confidence="low",
            notes=["Address missing from provider payload."],
        ),
    ]

    table = render_comparison_table(rows)

    assert "Installatieburo Hevi BV" in table
    assert "OpenStreetMap" in table
    assert "Google Places" in table
    assert "Address missing from provider payload." in table
    assert "missing" in table.lower()


def test_render_comparison_table_uses_side_by_side_columns() -> None:
    rows = [
        BusinessComparisonRow(
            scenario="Open source",
            source="OpenStreetMap",
            business_name="Installatieburo Hevi BV",
            street_address="Dorpsstraat 1",
            postcode="3981 AA",
            city="Bunnik",
            business_type="installatiebedrijf",
            confidence="medium",
            notes=["Matched by name."],
        ),
        BusinessComparisonRow(
            scenario="Places",
            source="Google Places",
            business_name="Installatieburo Hevi BV",
            street_address="Dorpsstraat 1",
            postcode="3981 AA",
            city="Bunnik",
            business_type="electrician",
            confidence="medium",
            notes=["Matched by Google Places text search."],
        ),
        BusinessComparisonRow(
            scenario="Places + KVK",
            source="Google Places + KVK",
            business_name="Installatieburo Hevi BV",
            street_address="Dorpsstraat 1",
            postcode="3981 AA",
            city="Bunnik",
            business_type="Elektrotechnische bouwinstallatie",
            confidence="high",
            notes=["KVK reports 8 working people."],
        ),
    ]

    table = render_comparison_table(rows)

    assert "| Field | Open source | Places | Places + KVK |" in table
    assert "| Bron | OpenStreetMap | Google Places | Google Places + KVK |" in table


def test_build_business_comparison_returns_three_rows_with_provider_notes(monkeypatch) -> None:
    def fake_open_source(*args, **kwargs) -> dict[str, object]:
        return {
            "tags": {
                "name": "Installatieburo Hevi BV",
                "addr:street": "Dorpsstraat",
                "addr:housenumber": "1",
                "addr:postcode": "3981 AA",
                "addr:city": "Bunnik",
                "craft": "electrician",
            }
        }

    def fake_places(*args, **kwargs) -> dict[str, object]:
        return {
            "displayName": {"text": "Installatieburo Hevi BV"},
            "formattedAddress": "Dorpsstraat 1, 3981 AA Bunnik, Netherlands",
            "addressComponents": [
                {"longText": "Dorpsstraat", "types": ["route"]},
                {"longText": "1", "types": ["street_number"]},
                {"longText": "3981 AA", "types": ["postal_code"]},
                {"longText": "Bunnik", "types": ["locality"]},
            ],
            "types": ["electrician"],
        }

    def fake_kvk(*args, **kwargs) -> dict[str, object]:
        return {
            "eersteHandelsnaam": "Installatieburo Hevi BV",
            "totaalWerkzamePersonen": 8,
            "adressen": [
                {
                    "type": "bezoekadres",
                    "straatnaam": "Dorpsstraat",
                    "huisnummer": "1",
                    "postcode": "3981 AA",
                    "plaats": "Bunnik",
                    "volledigAdres": "Dorpsstraat 1, 3981 AA Bunnik",
                }
            ],
            "sbiActiviteiten": [
                {
                    "sbiCode": "4321",
                    "sbiOmschrijving": "Elektrotechnische bouwinstallatie",
                    "indHoofdactiviteit": "Ja",
                }
            ],
        }

    monkeypatch.setattr("vangrondwelle.business_sources.fetch_osm_business", fake_open_source)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_google_places_business", fake_places)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_kvk_business", fake_kvk)
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-google-key")
    monkeypatch.setenv("KVK_API_KEY", "test-kvk-key")

    rows = build_business_comparison(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=requests.Session(),
    )

    assert [row.scenario for row in rows] == [
        "Open source",
        "Places",
        "Places + KVK",
    ]
    assert rows[0].business_name == "Installatieburo Hevi BV"
    assert rows[1].source == "Google Places"
    assert rows[2].business_type == "Elektrotechnische bouwinstallatie"
    assert "8" in " ".join(rows[2].notes)


def test_build_business_comparison_marks_missing_api_credentials(monkeypatch) -> None:
    def fake_open_source(*args, **kwargs) -> dict[str, object]:
        return {"tags": {"name": "Installatieburo Hevi BV", "addr:city": "Bunnik"}}

    monkeypatch.setattr("vangrondwelle.business_sources.fetch_osm_business", fake_open_source)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("KVK_API_KEY", raising=False)

    rows = build_business_comparison(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=requests.Session(),
    )

    assert rows[1].confidence == "low"
    assert "api key" in " ".join(rows[1].notes).lower()
    assert rows[2].confidence == "low"
    assert "api key" in " ".join(rows[2].notes).lower()


def test_build_business_comparison_marks_no_provider_match(monkeypatch) -> None:
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_osm_business", lambda *args, **kwargs: None)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_google_places_business", lambda *args, **kwargs: None)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_kvk_business", lambda *args, **kwargs: None)
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test-google-key")
    monkeypatch.setenv("KVK_API_KEY", "test-kvk-key")

    rows = build_business_comparison(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=requests.Session(),
    )

    assert "no openstreetmap match" in " ".join(rows[0].notes).lower()
    assert "no match" in " ".join(rows[1].notes).lower()
    assert "no matching company profile" in " ".join(rows[2].notes).lower()


def test_build_business_comparison_recovers_from_provider_failure(monkeypatch) -> None:
    def failing_osm(*args, **kwargs) -> None:
        raise requests.RequestException("timed out")

    monkeypatch.setattr("vangrondwelle.business_sources.fetch_osm_business", failing_osm)
    monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
    monkeypatch.delenv("KVK_API_KEY", raising=False)

    rows = build_business_comparison(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=requests.Session(),
    )

    assert rows[0].confidence == "low"
    assert "timed out" in " ".join(rows[0].notes).lower()
