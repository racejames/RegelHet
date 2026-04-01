## What changed

- Added CSV output support to the CLI.
- Added a discovery flow that reads public ZorgkaartNederland Den Haag organization listings and extracts provider website seeds.
- Generated an initial Den Haag provider CSV dataset at `output/den-haag-zorgbedrijven.csv`.
- Added tests for CSV serialization and directory discovery parsing.
- Documented how to generate a Den Haag CSV dataset locally.

## How to test locally

- Run `python -m pip install -e .[dev]`.
- Run `python -m pytest`.
- Run `python -m vangrondwelle.cli --format csv ziekenhuis.nl`.
- Run `python -m vangrondwelle.cli --discover-den-haag --format csv --output output\den-haag-zorgbedrijven.csv --max-providers 5`.

## Risks/rollback

- The Den Haag seed flow depends on the current ZorgkaartNederland markup and may need updating if their page structure changes.
- Some organization entries do not expose a provider website and will be skipped.
- Roll back by reverting this branch if the discovery/export workflow is not wanted.

## Docs touched

- `README.md`
