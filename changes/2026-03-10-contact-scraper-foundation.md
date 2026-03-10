## What changed

- Added a Python CLI project for scraping Dutch healthcare provider websites.
- Implemented focused page discovery for contact-oriented pages on the same domain.
- Added extraction and normalization for address, central phone number, and central email address.
- Added fixture-based unit tests for extraction and scrape orchestration.

## How to test locally

- Create and activate a virtual environment.
- Run `python -m pip install -e .[dev]`.
- Run `python -m pytest`.
- Try `python -m vangrondwelle.cli --pretty voorbeeldzorg.nl`.

## Risks/rollback

- Extraction is heuristic-based and may miss sites with highly custom markup.
- Crawling is intentionally shallow and may not reach deeply nested contact pages.
- Roll back by reverting this branch if the initial project layout is not desired.

## Docs touched

- `README.md`
