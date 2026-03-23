import sys

from vangrondwelle import cli
from vangrondwelle.business_compare import BusinessComparisonRow


def test_main_supports_compare_business_command(monkeypatch, capsys) -> None:
    def fake_build_business_comparison(
        name: str,
        location: str,
    ) -> list[BusinessComparisonRow]:
        assert name == "Installatieburo Hevi BV"
        assert location == "Bunnik"
        return [
            BusinessComparisonRow(
                scenario="Open source",
                source="OpenStreetMap",
                business_name=name,
                street_address="Dorpsstraat 1",
                postcode="3981 AA",
                city=location,
                business_type="installatiebedrijf",
                confidence="medium",
                notes=["Matched by name."],
            )
        ]

    monkeypatch.setattr(cli, "build_business_comparison", fake_build_business_comparison)
    monkeypatch.setattr(cli, "render_comparison_table", lambda rows: "table output")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "vangrondwelle",
            "compare-business",
            "--name",
            "Installatieburo Hevi BV",
            "--location",
            "Bunnik",
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "table output" in captured.out


def test_main_keeps_domain_scrape_mode(monkeypatch, capsys) -> None:
    class FakeContactResult:
        def to_dict(self) -> dict[str, object]:
            return {"domain": "voorbeeldzorg.nl", "confidence": 1.0}

    monkeypatch.setattr(cli, "scrape_domain", lambda domain: FakeContactResult())
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "vangrondwelle",
            "--pretty",
            "voorbeeldzorg.nl",
        ],
    )

    exit_code = cli.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"domain": "voorbeeldzorg.nl"' in captured.out
