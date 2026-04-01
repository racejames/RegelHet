# Bunnik Source Comparison Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-record Bunnik comparison demo that shows OpenStreetMap, Google Places, and Google Places plus KVK results in one normalized side-by-side table.

**Architecture:** Add a separate comparison flow alongside the existing healthcare contact scraper. Keep provider calls and normalization isolated behind a shared business-record model so the demo can grow from one business to broader area searches later without rewriting the CLI output layer.

**Tech Stack:** Python 3.11+, `requests`, `beautifulsoup4`, `pytest`, standard-library dataclasses and argparse

---

## File Structure

- Create: `src/vangrondwelle/business_compare.py`
  Responsibility: shared normalized comparison row model, provider response model, and terminal table rendering.
- Create: `src/vangrondwelle/business_sources.py`
  Responsibility: OSM, Google Places, and KVK client helpers plus orchestration for the three comparison scenarios.
- Modify: `src/vangrondwelle/logging_utils.py`
  Responsibility: extend structured logging fields for provider/source/comparison events.
- Modify: `src/vangrondwelle/cli.py`
  Responsibility: add a new comparison command without breaking the existing domain scraper command.
- Create: `tests/test_business_compare.py`
  Responsibility: normalized row rendering, provider fallback notes, and orchestrated comparison behavior.
- Create: `tests/test_cli.py`
  Responsibility: new CLI command behavior and output shape.
- Modify: `README.md`
  Responsibility: document comparison demo usage, env vars, and dry-run positioning.
- Create: `docs/index.md`
  Responsibility: documentation landing page for the repo.
- Create: `docs/FEATURES.md`
  Responsibility: feature registry entry for the comparison demo.
- Create: `changes/2026-03-23-bunnik-source-comparison-demo.md`
  Responsibility: change note with testing, risks, and docs touched.

### Task 1: Shared Comparison Model And Renderer

**Files:**
- Create: `tests/test_business_compare.py`
- Create: `src/vangrondwelle/business_compare.py`

- [ ] **Step 1: Write the failing rendering tests**

```python
from vangrondwelle.business_compare import BusinessComparisonRow, render_comparison_table


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
```

- [ ] **Step 2: Run the rendering test to verify it fails**

Run: `python -m pytest tests/test_business_compare.py -k render -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbols from `vangrondwelle.business_compare`

- [ ] **Step 3: Write the minimal model and renderer**

```python
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
    notes: list[str]


def render_comparison_table(rows: list[BusinessComparisonRow]) -> str:
    ...
```

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `python -m pytest tests/test_business_compare.py -k render -v`
Expected: PASS

- [ ] **Step 5: Refactor for clear missing-value handling**

Keep the renderer explicit about missing values by displaying `missing` instead of blank strings.

### Task 2: Scenario Normalization And Orchestration

**Files:**
- Modify: `tests/test_business_compare.py`
- Create: `src/vangrondwelle/business_sources.py`
- Modify: `src/vangrondwelle/business_compare.py`
- Modify: `src/vangrondwelle/logging_utils.py`

- [ ] **Step 1: Write failing orchestration tests**

```python
from requests import Session

from vangrondwelle.business_sources import build_business_comparison


def test_build_business_comparison_returns_three_rows_with_provider_notes(monkeypatch) -> None:
    def fake_open_source(*args, **kwargs):
        return {"name": "Installatieburo Hevi BV", "city": "Bunnik"}

    def fake_places(*args, **kwargs):
        return {"displayName": {"text": "Installatieburo Hevi BV"}}

    def fake_kvk(*args, **kwargs):
        return {"sbiActiviteiten": [{"sbiOmschrijving": "Elektrotechnische bouwinstallatie"}]}

    monkeypatch.setattr("vangrondwelle.business_sources.fetch_osm_business", fake_open_source)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_google_places_business", fake_places)
    monkeypatch.setattr("vangrondwelle.business_sources.fetch_kvk_business", fake_kvk)

    rows = build_business_comparison("Installatieburo Hevi BV", "Bunnik", session=Session())

    assert [row.scenario for row in rows] == [
        "Open source",
        "Places",
        "Places + KVK",
    ]
    assert rows[2].business_type is not None
```

- [ ] **Step 2: Run the orchestration test to verify it fails**

Run: `python -m pytest tests/test_business_compare.py -k comparison -v`
Expected: FAIL because `build_business_comparison` does not exist yet

- [ ] **Step 3: Implement minimal provider helpers and orchestration**

```python
def build_business_comparison(
    business_name: str,
    location: str,
    *,
    session: requests.Session | None = None,
) -> list[BusinessComparisonRow]:
    ...
```

Implementation expectations:
- OSM helper uses Overpass API with the business name plus place
- Google Places helper uses API key from environment when available
- KVK helper uses API key from environment when available
- Missing credentials should produce a row with explanatory notes instead of raising
- Structured logs should include provider/source metadata

- [ ] **Step 4: Run the focused orchestration tests**

Run: `python -m pytest tests/test_business_compare.py -k comparison -v`
Expected: PASS

- [ ] **Step 5: Add edge-case tests for missing credentials and ambiguous matches**

Add at least one failing test first for:
- missing Google API key
- missing KVK API key
- provider returns no match

Then implement the minimal note/confidence behavior to satisfy those tests.

### Task 3: CLI Command

**Files:**
- Create: `tests/test_cli.py`
- Modify: `src/vangrondwelle/cli.py`

- [ ] **Step 1: Write a failing CLI test**

```python
from vangrondwelle import cli


def test_main_supports_compare_business_command(monkeypatch, capsys) -> None:
    def fake_build_business_comparison(name: str, location: str):
        return []

    monkeypatch.setattr(cli, "build_business_comparison", fake_build_business_comparison)
    monkeypatch.setattr("sys.argv", ["vangrondwelle", "compare-business", "--name", "Installatieburo Hevi BV", "--location", "Bunnik"])

    exit_code = cli.main()

    assert exit_code == 0
```

- [ ] **Step 2: Run the CLI test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL because the comparison command does not exist yet

- [ ] **Step 3: Implement the minimal CLI command**

Requirements:
- keep existing domain-scrape behavior available
- add a `compare-business` command with `--name` and `--location`
- print the rendered table to stdout
- preserve `--verbose` logging behavior

- [ ] **Step 4: Run CLI tests**

Run: `python -m pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 5: Smoke test the command manually**

Run: `python -m vangrondwelle.cli compare-business --name "Installatieburo Hevi BV" --location Bunnik`
Expected: table output with three scenario sections, even if API credentials are missing

### Task 4: Documentation And Change Note

**Files:**
- Modify: `README.md`
- Create: `docs/index.md`
- Create: `docs/FEATURES.md`
- Create: `changes/2026-03-23-bunnik-source-comparison-demo.md`

- [ ] **Step 1: Write/update docs with failing expectations in mind**

Document:
- the purpose of the comparison demo
- required env vars for Places and KVK
- example command for the Bunnik dry-run
- the fact that OSM is the open-source source for scenario 1

- [ ] **Step 2: Add the feature registry entry**

Use:

```markdown
### F-001: Bunnik Source Comparison Demo
Reference: `bunnik-source-comparison-demo`
```

- [ ] **Step 3: Add the change note**

Include:
- What changed
- How to test locally
- Risks/rollback
- Docs touched

- [ ] **Step 4: Run the full test suite**

Run: `python -m pytest`
Expected: PASS

- [ ] **Step 5: Review git diff before the review gate**

Run:
- `git status --short`
- `git diff --stat`

Expected: only cohesive comparison-demo changes on the feature branch
