from pathlib import Path

from vangrondwelle.extractor import extract_contact_info


def read_fixture(name: str) -> str:
    return Path(__file__).parent.joinpath("fixtures", name).read_text(encoding="utf-8")


def test_extract_contact_info_returns_address_phone_and_email() -> None:
    html = read_fixture("contact_page.html")

    result = extract_contact_info(
        html,
        domain="voorbeeldzorg.nl",
        source_url="https://voorbeeldzorg.nl/contact",
    )

    assert result.address is not None
    assert "Dorpsstraat 12" in result.address
    assert result.phone == "0201234567"
    assert result.email == "info@voorbeeldzorg.nl"
    assert result.confidence == 1.0
