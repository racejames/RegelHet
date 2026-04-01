## What changed

- Added a comparison-focused business demo flow for one target business and location.
- Added OpenStreetMap, Google Places, and Google Places plus KVK scenario handling.
- Added a side-by-side table renderer and a new `compare-business` CLI command.
- Added documentation for the new demo flow and feature registry entries.
- Updated the visible product branding to `RegelHet` while keeping the internal package name stable as `vangrondwelle`.

## How to test locally

- Run `python -m pip install -e .[dev]`
- Run `python -m pytest`
- Run `python -m vangrondwelle.cli compare-business --name "Installatieburo Hevi BV" --location Bunnik`
- Optionally set `GOOGLE_PLACES_API_KEY` and `KVK_API_KEY` to exercise the paid scenarios

## Risks/rollback

- External provider payloads may differ from the assumptions in the first-pass normalizers.
- KVK and Google Places may not always match to the same entity without tighter matching rules.
- Roll back by reverting this branch if the comparison demo direction is not desired.

## Docs touched

- `README.md`
- `docs/index.md`
- `docs/FEATURES.md`
- `docs/superpowers/specs/2026-03-23-bunnik-source-comparison-demo-design.md`
- `docs/superpowers/plans/2026-03-23-bunnik-source-comparison-demo.md`
