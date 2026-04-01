from vangrondwelle.business_sources import fetch_google_places_business
from vangrondwelle.business_sources import fetch_kvk_business
from vangrondwelle.business_sources import resolve_bunnik_geography
from vangrondwelle.business_sources import _select_osm_match
from vangrondwelle.business_sources import _select_kvk_match


def test_bunnik_filter_resolves_provider_specific_locality_fallbacks() -> None:
    osm_candidate = {
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
            "addr:city": "Bunnik",
        }
    }
    places_candidate = {
        "displayName": {"text": "Installatieburo Hevi BV"},
        "addressComponents": [
            {"longText": "Dorpsstraat", "types": ["route"]},
            {"longText": "1", "types": ["street_number"]},
            {"longText": "3981 AA", "types": ["postal_code"]},
            {"longText": "Bunnik", "types": ["postal_town"]},
        ],
    }
    kvk_candidate = {
        "plaats": "Bunnik",
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3981 AA",
            }
        ]
    }

    osm = resolve_bunnik_geography(osm_candidate, provider="osm")
    places = resolve_bunnik_geography(places_candidate, provider="google_places")
    kvk = resolve_bunnik_geography(kvk_candidate, provider="kvk")

    assert osm.boundary_name == "Bunnik"
    assert osm.inside_bunnik is True
    assert osm.city == "Bunnik"
    assert osm.street_address == "Dorpsstraat 1"

    assert places.boundary_name == "Bunnik"
    assert places.inside_bunnik is True
    assert places.city == "Bunnik"
    assert places.street_address == "Dorpsstraat 1"

    assert kvk.boundary_name == "Bunnik"
    assert kvk.inside_bunnik is True
    assert kvk.city == "Bunnik"
    assert kvk.street_address == "Dorpsstraat 1"


def test_bunnik_filter_rejects_candidate_outside_bunnik() -> None:
    candidate = {
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3011 AA",
            "addr:city": "Rotterdam",
        }
    }

    resolution = resolve_bunnik_geography(candidate, provider="osm")

    assert resolution.boundary_name == "Bunnik"
    assert resolution.inside_bunnik is False
    assert resolution.city == "Rotterdam"
    assert resolution.postcode == "3011 AA"


def test_bunnik_filter_rejects_fallback_candidate_outside_bunnik() -> None:
    rotterdam_candidate = {
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3011 AA",
            "addr:city": "Rotterdam",
        }
    }

    match = _select_osm_match([rotterdam_candidate], "Installatieburo Hevi BV", "Bunnik")

    assert match is None


def test_bunnik_filter_rejects_unrelated_osm_fallback_for_non_bunnik_location() -> None:
    candidate = {
        "tags": {
            "name": "Other Business",
            "addr:city": "Utrecht",
        }
    }

    match = _select_osm_match([candidate], "Installatieburo Hevi BV", "Utrecht")

    assert match is None


def test_bunnik_filter_accepts_later_exact_name_osm_fallback_for_non_bunnik_location() -> None:
    candidates = [
        {
            "tags": {
                "name": "Other Business",
                "addr:city": "Utrecht",
            }
        },
        {
            "tags": {
                "name": "Installatieburo Hevi BV",
                "addr:city": "Amsterdam",
            }
        },
    ]

    match = _select_osm_match(candidates, "Installatieburo Hevi BV", "Utrecht")

    assert match is candidates[1]


def test_bunnik_filter_accepts_exact_name_osm_candidate_without_city() -> None:
    candidate = {
        "center": {"lat": 52.061, "lon": 5.189},
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
        }
    }

    match = _select_osm_match([candidate], "Installatieburo Hevi BV", "Bunnik")

    assert match is candidate


def test_bunnik_filter_accepts_geometry_backed_osm_candidate_without_city() -> None:
    candidate = {
        "lat": 52.061,
        "lon": 5.189,
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
        },
    }

    match = _select_osm_match([candidate], "Installatieburo Hevi BV", "Bunnik")

    assert match is candidate


def test_bunnik_filter_rejects_geometry_backed_osm_candidate_outside_bunnik() -> None:
    candidate = {
        "lat": 52.01,
        "lon": 5.18,
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
        },
    }

    match = _select_osm_match([candidate], "Installatieburo Hevi BV", "Bunnik")

    assert match is None


def test_bunnik_filter_uses_updated_bunnik_south_boundary() -> None:
    outside_candidate = {
        "lat": 52.0455,
        "lon": 5.189,
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
        },
    }
    inside_candidate = {
        "lat": 52.0465,
        "lon": 5.189,
        "tags": {
            "name": "Installatieburo Hevi BV",
            "addr:street": "Dorpsstraat",
            "addr:housenumber": "1",
            "addr:postcode": "3981 AA",
        },
    }

    outside_match = _select_osm_match([outside_candidate], "Installatieburo Hevi BV", "Bunnik")
    inside_match = _select_osm_match([inside_candidate], "Installatieburo Hevi BV", "Bunnik")

    assert outside_match is None
    assert inside_match is inside_candidate


def test_bunnik_filter_does_not_treat_name_or_street_mentions_as_inside_boundary() -> None:
    candidate = {
        "tags": {
            "name": "Bunnik Bouw BV",
            "addr:street": "Bunnikstraat",
            "addr:housenumber": "12",
            "addr:postcode": "3581 AA",
            "addr:city": "Utrecht",
        }
    }

    resolution = resolve_bunnik_geography(candidate, provider="osm")

    assert resolution.city == "Utrecht"
    assert resolution.inside_bunnik is False


def test_bunnik_filter_rejects_fallback_kvk_candidate_outside_bunnik() -> None:
    rotterdam_candidate = {
        "naam": "Installatieburo Hevi BV",
        "plaats": "Rotterdam",
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3011 AA",
            }
        ],
    }

    match = _select_kvk_match([rotterdam_candidate], "Installatieburo Hevi BV", "Bunnik")

    assert match is None


def test_bunnik_filter_rejects_unrelated_kvk_fallback_for_non_bunnik_location() -> None:
    candidate = {
        "naam": "Other Business",
        "plaats": "Utrecht",
    }

    match = _select_kvk_match([candidate], "Installatieburo Hevi BV", "Utrecht")

    assert match is None


def test_bunnik_filter_accepts_later_exact_name_kvk_fallback_for_non_bunnik_location() -> None:
    candidates = [
        {
            "naam": "Other Business",
            "plaats": "Utrecht",
        },
        {
            "naam": "Installatieburo Hevi BV",
            "plaats": "Amsterdam",
        },
    ]

    match = _select_kvk_match(candidates, "Installatieburo Hevi BV", "Utrecht")

    assert match is candidates[1]


def test_bunnik_filter_rejects_google_places_first_outside_bunnik_result() -> None:
    outside_candidate = {
        "displayName": {"text": "Installatieburo Hevi BV"},
        "addressComponents": [
            {"longText": "Dorpsstraat", "types": ["route"]},
            {"longText": "1", "types": ["street_number"]},
            {"longText": "3011 AA", "types": ["postal_code"]},
            {"longText": "Rotterdam", "types": ["locality"]},
        ],
    }
    inside_candidate = {
        "displayName": {"text": "Installatieburo Hevi BV"},
        "addressComponents": [
            {"longText": "Dorpsstraat", "types": ["route"]},
            {"longText": "1", "types": ["street_number"]},
            {"longText": "3981 AA", "types": ["postal_code"]},
            {"longText": "Bunnik", "types": ["locality"]},
        ],
    }

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeSession:
        def post(self, *args, **kwargs) -> FakeResponse:
            return FakeResponse({"places": [outside_candidate, inside_candidate]})

    match = fetch_google_places_business(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=FakeSession(),
        api_key="test-google-key",
    )

    assert match is inside_candidate


def test_bunnik_filter_accepts_google_places_address_text_fallback_for_bunnik() -> None:
    outside_candidate = {
        "displayName": {"text": "Installatieburo Hevi BV"},
        "formattedAddress": "Dorpsstraat 1, 3011 AA Rotterdam, Netherlands",
        "addressComponents": [
            {"longText": "Dorpsstraat", "types": ["route"]},
            {"longText": "1", "types": ["street_number"]},
            {"longText": "3011 AA", "types": ["postal_code"]},
        ],
    }
    inside_candidate = {
        "displayName": {"text": "Installatieburo Hevi BV"},
        "formattedAddress": "Dorpsstraat 1, 3981 AA Bunnik, Netherlands",
        "addressComponents": [
            {"longText": "Dorpsstraat", "types": ["route"]},
            {"longText": "1", "types": ["street_number"]},
            {"longText": "3981 AA", "types": ["postal_code"]},
        ],
    }

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeSession:
        def post(self, *args, **kwargs) -> FakeResponse:
            return FakeResponse({"places": [outside_candidate, inside_candidate]})

    match = fetch_google_places_business(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=FakeSession(),
        api_key="test-google-key",
    )

    assert match is inside_candidate


def test_bunnik_filter_rejects_kvk_detail_outside_bunnik_after_profile_fetch(monkeypatch) -> None:
    search_result = {
        "naam": "Installatieburo Hevi BV",
        "plaats": "Bunnik",
        "links": [{"rel": "vestigingsprofiel", "href": "https://example.test/kvk/detail"}],
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3981 AA",
                "plaats": "Bunnik",
            }
        ],
    }
    detail_result = {
        "naam": "Installatieburo Hevi BV",
        "plaats": "Rotterdam",
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3011 AA",
                "plaats": "Rotterdam",
            }
        ],
    }

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def get(self, url, *args, **kwargs) -> FakeResponse:
            self.calls.append(url)
            if url == "https://kvk.example.test/search":
                return FakeResponse({"resultaten": [search_result]})
            assert url == "https://example.test/kvk/detail"
            return FakeResponse(detail_result)

    monkeypatch.setenv("KVK_SEARCH_URL", "https://kvk.example.test/search")

    match = fetch_kvk_business(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=FakeSession(),
        api_key="test-kvk-key",
    )

    assert match is None


def test_bunnik_filter_keeps_kvk_detail_in_bunnik_after_profile_fetch(monkeypatch) -> None:
    search_result = {
        "naam": "Installatieburo Hevi BV",
        "plaats": "Bunnik",
        "links": [{"rel": "vestigingsprofiel", "href": "https://example.test/kvk/detail"}],
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3981 AA",
                "plaats": "Bunnik",
            }
        ],
    }
    detail_result = {
        "naam": "Installatieburo Hevi BV",
        "volledigAdres": "Dorpsstraat 1, 3981 AA Bunnik",
        "adressen": [
            {
                "type": "bezoekadres",
                "straatnaam": "Dorpsstraat",
                "huisnummer": "1",
                "postcode": "3981 AA",
            }
        ],
    }

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return self._payload

    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def get(self, url, *args, **kwargs) -> FakeResponse:
            self.calls.append(url)
            if url == "https://kvk.example.test/search":
                return FakeResponse({"resultaten": [search_result]})
            assert url == "https://example.test/kvk/detail"
            return FakeResponse(detail_result)

    monkeypatch.setenv("KVK_SEARCH_URL", "https://kvk.example.test/search")

    match = fetch_kvk_business(
        "Installatieburo Hevi BV",
        "Bunnik",
        session=FakeSession(),
        api_key="test-kvk-key",
    )

    assert match is detail_result
