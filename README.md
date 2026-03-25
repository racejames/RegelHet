# vanGrondwelle

CLI scraper for collecting basic contact details from Dutch healthcare provider websites and for comparing business-source quality across Dutch directory providers.

## What it does

The first version crawls a small set of likely contact pages on a provider domain and extracts:

- postal address
- central phone number
- central email address

The scraper returns JSON so the output can be piped into other tools later.

The repository also includes a comparison demo for checking how one target business appears across:

- OpenStreetMap
- Google Places
- Google Places plus KVK enrichment

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m vangrondwelle.cli --pretty ziekenhuis.nl
```

## Business comparison demo

Run the Bunnik comparison dry-run like this:

```powershell
python -m vangrondwelle.cli compare-business --name "Installatieburo Hevi BV" --location Bunnik
```

Environment variables:

- `GOOGLE_PLACES_API_KEY` for the Google Places scenario
- `KVK_API_KEY` for the Google Places plus KVK scenario
- `KVK_SEARCH_URL` only when you want to override the default KVK search endpoint

Without the paid API keys, the command still renders the comparison table and clearly marks the paid-provider rows as unavailable.

## Run tests

```powershell
python -m pytest
```

## Notes

- The crawler stays on the same domain and only follows a small number of contact-oriented pages.
- Extraction uses heuristics, so some sites will need future rule tuning.
- Logs are emitted as JSON on stderr when `--verbose` is enabled.
- The comparison demo uses OpenStreetMap as the open-source source for scenario 1.
