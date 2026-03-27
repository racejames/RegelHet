from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable

import requests

from .app_metadata import USER_AGENT
from .business_compare import BusinessComparisonRow
from .normalize import normalize_text

LOGGER = logging.getLogger(__name__)
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
GOOGLE_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
KVK_SEARCH_URL = "https://api.kvk.nl/api/v2/zoeken"


def build_business_comparison(
    business_name: str,
    location: str,
    *,
    session: requests.Session | None = None,
) -> list[BusinessComparisonRow]:
    client = session or requests.Session()
    osm_result, osm_error = _safe_provider_call(
        "osm",
        business_name,
        location,
        lambda: fetch_osm_business(business_name, location, session=client),
    )
    places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    kvk_api_key = os.getenv("KVK_API_KEY")

    places_result = None
    places_error = None
    if places_api_key:
        places_result, places_error = _safe_provider_call(
            "google_places",
            business_name,
            location,
            lambda: fetch_google_places_business(
                business_name,
                location,
                session=client,
                api_key=places_api_key,
            ),
        )

    kvk_result = None
    kvk_error = None
    if places_api_key and kvk_api_key:
        kvk_result, kvk_error = _safe_provider_call(
            "kvk",
            business_name,
            location,
            lambda: fetch_kvk_business(
                business_name,
                location,
                session=client,
                api_key=kvk_api_key,
            ),
        )

    return [
        _build_osm_row(osm_result, error=osm_error),
        _build_places_row(places_result, api_key_present=bool(places_api_key), error=places_error),
        _build_places_kvk_row(
            places_result,
            kvk_result,
            places_api_key_present=bool(places_api_key),
            kvk_api_key_present=bool(kvk_api_key),
            places_error=places_error,
            kvk_error=kvk_error,
        ),
    ]


def fetch_osm_business(
    business_name: str,
    location: str,
    *,
    session: requests.Session | None = None,
    timeout: int = 20,
) -> dict[str, object] | None:
    client = session or requests.Session()
    query = _build_overpass_query(business_name, location)
    LOGGER.info(
        "Fetching business from OSM.",
        extra={"provider": "osm", "location": location, "business_name": business_name},
    )
    response = client.post(
        OVERPASS_API_URL,
        data={"data": query},
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    payload = response.json()
    elements = payload.get("elements", [])
    if not isinstance(elements, list) or not elements:
        return None
    return _select_osm_match(elements, business_name, location)


def fetch_google_places_business(
    business_name: str,
    location: str,
    *,
    session: requests.Session | None = None,
    api_key: str,
    timeout: int = 20,
) -> dict[str, object] | None:
    client = session or requests.Session()
    LOGGER.info(
        "Fetching business from Google Places.",
        extra={"provider": "google_places", "location": location, "business_name": business_name},
    )
    response = client.post(
        GOOGLE_PLACES_URL,
        json={
            "textQuery": f"{business_name}, {location}, Netherlands",
            "languageCode": "nl",
            "regionCode": "NL",
        },
        timeout=timeout,
        headers={
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": ",".join(
                [
                    "places.displayName",
                    "places.formattedAddress",
                    "places.addressComponents",
                    "places.types",
                    "places.businessStatus",
                    "places.googleMapsUri",
                ]
            ),
        },
    )
    response.raise_for_status()
    places = response.json().get("places", [])
    if not isinstance(places, list) or not places:
        return None
    return places[0]


def fetch_kvk_business(
    business_name: str,
    location: str,
    *,
    session: requests.Session | None = None,
    api_key: str,
    timeout: int = 20,
) -> dict[str, object] | None:
    client = session or requests.Session()
    search_url = os.getenv("KVK_SEARCH_URL", KVK_SEARCH_URL)
    LOGGER.info(
        "Fetching business from KVK.",
        extra={"provider": "kvk", "location": location, "business_name": business_name},
    )
    response = client.get(
        search_url,
        params={"naam": business_name, "plaats": location, "resultatenPerPagina": 5, "pagina": 1},
        timeout=timeout,
        headers={"apikey": api_key, "User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    results = response.json().get("resultaten", [])
    if not isinstance(results, list) or not results:
        return None

    best_match = _select_kvk_match(results, business_name, location)
    if best_match is None:
        return None

    detail_url = _extract_kvk_detail_url(best_match)
    if not detail_url:
        return best_match

    detail_response = client.get(
        detail_url,
        timeout=timeout,
        headers={"apikey": api_key, "User-Agent": USER_AGENT},
    )
    detail_response.raise_for_status()
    return detail_response.json()


def _build_osm_row(
    result: dict[str, object] | None,
    *,
    error: str | None = None,
) -> BusinessComparisonRow:
    if error:
        return BusinessComparisonRow(
            scenario="Open source",
            source="OpenStreetMap",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=[f"OpenStreetMap request failed: {error}"],
        )
    if result is None:
        return BusinessComparisonRow(
            scenario="Open source",
            source="OpenStreetMap",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=["No OpenStreetMap match found for the target business."],
        )

    tags = result.get("tags", {}) if isinstance(result, dict) else {}
    if not isinstance(tags, dict):
        tags = {}
    return BusinessComparisonRow(
        scenario="Open source",
        source="OpenStreetMap",
        business_name=_string(tags.get("name")),
        street_address=_compose_address(_string(tags.get("addr:street")), _string(tags.get("addr:housenumber"))),
        postcode=_string(tags.get("addr:postcode")),
        city=_string(tags.get("addr:city")) or _string(tags.get("addr:place")),
        business_type=_first_text(tags, ("shop", "amenity", "office", "craft", "tourism")),
        confidence="medium",
        notes=["Matched by business name in OpenStreetMap."],
    )


def _build_places_row(
    result: dict[str, object] | None,
    *,
    api_key_present: bool,
    error: str | None = None,
) -> BusinessComparisonRow:
    if not api_key_present:
        return BusinessComparisonRow(
            scenario="Places",
            source="Google Places",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=["Google Places API key missing."],
        )
    if error:
        return BusinessComparisonRow(
            scenario="Places",
            source="Google Places",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=[f"Google Places request failed: {error}"],
        )
    if result is None:
        return BusinessComparisonRow(
            scenario="Places",
            source="Google Places",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=["Google Places returned no match for the target business."],
        )

    components = _index_address_components(result.get("addressComponents"))
    return BusinessComparisonRow(
        scenario="Places",
        source="Google Places",
        business_name=_place_display_name(result),
        street_address=_compose_address(components.get("route"), components.get("street_number")),
        postcode=components.get("postal_code"),
        city=components.get("locality") or components.get("postal_town"),
        business_type=_first_sequence_value(result.get("types")),
        confidence="medium",
        notes=["Matched by Google Places text search."],
    )


def _build_places_kvk_row(
    places_result: dict[str, object] | None,
    kvk_result: dict[str, object] | None,
    *,
    places_api_key_present: bool,
    kvk_api_key_present: bool,
    places_error: str | None = None,
    kvk_error: str | None = None,
) -> BusinessComparisonRow:
    if not places_api_key_present:
        return BusinessComparisonRow(
            scenario="Places + KVK",
            source="Google Places + KVK",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=["Google Places API key missing."],
        )
    if places_error:
        return BusinessComparisonRow(
            scenario="Places + KVK",
            source="Google Places + KVK",
            business_name=None,
            street_address=None,
            postcode=None,
            city=None,
            business_type=None,
            confidence="low",
            notes=[f"Google Places request failed: {places_error}"],
        )

    base_row = _build_places_row(places_result, api_key_present=True)
    if not kvk_api_key_present:
        base_row.scenario = "Places + KVK"
        base_row.source = "Google Places + KVK"
        base_row.confidence = "low"
        base_row.notes.append("KVK API key missing.")
        return base_row

    if kvk_error:
        base_row.scenario = "Places + KVK"
        base_row.source = "Google Places + KVK"
        base_row.confidence = "low"
        base_row.notes.append(f"KVK request failed: {kvk_error}")
        return base_row

    if kvk_result is None:
        base_row.scenario = "Places + KVK"
        base_row.source = "Google Places + KVK"
        base_row.notes.append("KVK returned no matching company profile.")
        return base_row

    address = _kvk_address(kvk_result)
    business_type = _kvk_business_type(kvk_result) or base_row.business_type
    notes = list(base_row.notes)
    employee_count = kvk_result.get("totaalWerkzamePersonen") if isinstance(kvk_result, dict) else None
    if employee_count is not None:
        notes.append(f"KVK reports {employee_count} working people.")
    else:
        notes.append("KVK did not return a working people count.")

    return BusinessComparisonRow(
        scenario="Places + KVK",
        source="Google Places + KVK",
        business_name=_string(kvk_result.get("eersteHandelsnaam")) or base_row.business_name,
        street_address=address.get("street_address") or base_row.street_address,
        postcode=address.get("postcode") or base_row.postcode,
        city=address.get("city") or base_row.city,
        business_type=business_type,
        confidence="high",
        notes=notes,
    )


def _build_overpass_query(business_name: str, location: str) -> str:
    escaped_name = re.escape(business_name)
    escaped_location = location.replace('"', '\\"')
    return f"""
[out:json][timeout:15];
area["name"="{escaped_location}"]["boundary"="administrative"]->.searchArea;
(
  node["name"~"^{escaped_name}$",i](area.searchArea);
  way["name"~"^{escaped_name}$",i](area.searchArea);
  relation["name"~"^{escaped_name}$",i](area.searchArea);
);
out tags center;
""".strip()


def _select_osm_match(
    elements: list[object],
    business_name: str,
    location: str,
) -> dict[str, object] | None:
    normalized_name = _normalized_token(business_name)
    normalized_location = _normalized_token(location)
    for element in elements:
        if not isinstance(element, dict):
            continue
        tags = element.get("tags", {})
        if not isinstance(tags, dict):
            continue
        candidate_name = _normalized_token(_string(tags.get("name")))
        candidate_city = _normalized_token(_string(tags.get("addr:city")) or _string(tags.get("addr:place")))
        if candidate_name == normalized_name and (not candidate_city or candidate_city == normalized_location):
            return element
    for element in elements:
        if isinstance(element, dict):
            return element
    return None


def _select_kvk_match(
    results: list[object],
    business_name: str,
    location: str,
) -> dict[str, object] | None:
    normalized_name = _normalized_token(business_name)
    normalized_location = _normalized_token(location)
    for result in results:
        if not isinstance(result, dict):
            continue
        name = _normalized_token(_string(result.get("naam")))
        address = result.get("adres", {}) if isinstance(result, dict) else {}
        if not isinstance(address, dict):
            address = {}
        domestic = address.get("binnenlandsAdres", {})
        if not isinstance(domestic, dict):
            domestic = {}
        city = _normalized_token(_string(domestic.get("plaats")) or _string(result.get("plaats")))
        if name == normalized_name and (not city or city == normalized_location):
            return result
    for result in results:
        if isinstance(result, dict):
            return result
    return None


def _extract_kvk_detail_url(result: dict[str, object]) -> str | None:
    links = result.get("links", [])
    if not isinstance(links, list):
        return None
    for link in links:
        if not isinstance(link, dict):
            continue
        if link.get("rel") == "vestigingsprofiel":
            return _string(link.get("href"))
    for link in links:
        if not isinstance(link, dict):
            continue
        if link.get("rel") == "basisprofiel":
            return _string(link.get("href"))
    return None


def _place_display_name(result: dict[str, object]) -> str | None:
    display_name = result.get("displayName", {})
    if isinstance(display_name, dict):
        return _string(display_name.get("text"))
    return _string(display_name)


def _index_address_components(components: object) -> dict[str, str]:
    indexed: dict[str, str] = {}
    if not isinstance(components, list):
        return indexed
    for component in components:
        if not isinstance(component, dict):
            continue
        value = _string(component.get("longText")) or _string(component.get("shortText"))
        types = component.get("types", [])
        if not value or not isinstance(types, list):
            continue
        for component_type in types:
            if isinstance(component_type, str) and component_type not in indexed:
                indexed[component_type] = value
    return indexed


def _kvk_address(result: dict[str, object]) -> dict[str, str | None]:
    addresses = result.get("adressen", [])
    if not isinstance(addresses, list):
        return {"street_address": None, "postcode": None, "city": None}
    visit_address = None
    for address in addresses:
        if isinstance(address, dict) and address.get("type") == "bezoekadres":
            visit_address = address
            break
    if visit_address is None:
        visit_address = addresses[0] if addresses and isinstance(addresses[0], dict) else {}
    if not isinstance(visit_address, dict):
        visit_address = {}
    return {
        "street_address": _string(visit_address.get("volledigAdres"))
        or _compose_address(_string(visit_address.get("straatnaam")), _string(visit_address.get("huisnummer"))),
        "postcode": _string(visit_address.get("postcode")),
        "city": _string(visit_address.get("plaats")),
    }


def _kvk_business_type(result: dict[str, object]) -> str | None:
    activities = result.get("sbiActiviteiten", [])
    if not isinstance(activities, list):
        return None
    for activity in activities:
        if not isinstance(activity, dict):
            continue
        if _string(activity.get("indHoofdactiviteit")) == "Ja":
            return _string(activity.get("sbiOmschrijving"))
    for activity in activities:
        if isinstance(activity, dict):
            return _string(activity.get("sbiOmschrijving"))
    return None


def _compose_address(street: str | None, house_number: str | None) -> str | None:
    parts = [part for part in (normalize_text(street), normalize_text(house_number)) if part]
    if not parts:
        return None
    return " ".join(parts)


def _first_text(mapping: dict[str, object], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = _string(mapping.get(key))
        if value:
            return value
    return None


def _first_sequence_value(values: object) -> str | None:
    if not isinstance(values, list):
        return None
    for value in values:
        if isinstance(value, str):
            return value
    return None


def _normalized_token(value: str | None) -> str:
    text = normalize_text(value) or ""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _string(value: object) -> str | None:
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, int):
        return str(value)
    return None


def _safe_provider_call(
    provider: str,
    business_name: str,
    location: str,
    callback,
) -> tuple[dict[str, object] | None, str | None]:
    try:
        return callback(), None
    except requests.RequestException as exc:
        LOGGER.exception(
            "Business provider request failed.",
            extra={"provider": provider, "location": location, "business_name": business_name},
        )
        return None, str(exc)
