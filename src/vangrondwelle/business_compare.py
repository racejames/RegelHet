from __future__ import annotations

from dataclasses import dataclass, field

from .normalize import normalize_text

MISSING_VALUE = "missing"


@dataclass(slots=True)
class BusinessComparisonRow:
    scenario: str
    source: str
    business_name: str | None
    street_address: str | None
    postcode: str | None
    city: str | None
    business_type: str | None
    confidence: str
    notes: list[str] = field(default_factory=list)

    def display_value(self, value: str | None) -> str:
        return normalize_text(value) or MISSING_VALUE


def render_comparison_table(rows: list[BusinessComparisonRow]) -> str:
    scenario_headers = [row.scenario for row in rows]
    lines = [
        _render_markdown_row("Field", scenario_headers),
        _render_markdown_row("---", ["---"] * len(rows)),
        _render_markdown_row("Bron", [row.source for row in rows]),
        _render_markdown_row("Bedrijfsnaam", [row.display_value(row.business_name) for row in rows]),
        _render_markdown_row("Adres", [row.display_value(row.street_address) for row in rows]),
        _render_markdown_row("Postcode", [row.display_value(row.postcode) for row in rows]),
        _render_markdown_row("Plaatsnaam", [row.display_value(row.city) for row in rows]),
        _render_markdown_row("Bedrijfsoort", [row.display_value(row.business_type) for row in rows]),
        _render_markdown_row("Confidence", [row.display_value(row.confidence) for row in rows]),
        _render_markdown_row(
            "Notes",
            [", ".join(row.notes) if row.notes else MISSING_VALUE for row in rows],
        ),
    ]
    return "\n".join(lines)


def _render_markdown_row(label: str, values: list[str]) -> str:
    cells = [label, *values]
    return f"| {' | '.join(cells)} |"
