from vangrondwelle.models import ContactInfo
from vangrondwelle.output import serialize_csv


def test_serialize_csv_writes_expected_headers_and_values() -> None:
    result = ContactInfo(
        domain="zorgbedrijfa.nl",
        provider_name="Zorgbedrijf A",
        website_url="https://www.zorgbedrijfa.nl",
        directory_source="ZorgkaartNederland",
        directory_detail_url="https://www.zorgkaartnederland.nl/zorginstelling/zorgbedrijf-a",
        source_url="https://www.zorgbedrijfa.nl/contact",
        address="Straat 1, 2511 AA Den Haag",
        phone="0701234567",
        email="info@zorgbedrijfa.nl",
        confidence=1.0,
        notes=[],
    )

    payload = serialize_csv([result])

    assert "provider_name,website_url,domain" in payload
    assert "Zorgbedrijf A,https://www.zorgbedrijfa.nl,zorgbedrijfa.nl" in payload
    assert "0701234567" in payload
