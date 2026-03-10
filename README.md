# vanGrondwelle

CLI scraper for collecting basic contact details from Dutch healthcare provider websites.

## What it does

The first version crawls a small set of likely contact pages on a provider domain and extracts:

- postal address
- central phone number
- central email address

The scraper returns JSON so the output can be piped into other tools later.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m vangrondwelle.cli --pretty ziekenhuis.nl
```

## Run tests

```powershell
python -m pytest
```

## Notes

- The crawler stays on the same domain and only follows a small number of contact-oriented pages.
- Extraction uses heuristics, so some sites will need future rule tuning.
- Logs are emitted as JSON on stderr when `--verbose` is enabled.
