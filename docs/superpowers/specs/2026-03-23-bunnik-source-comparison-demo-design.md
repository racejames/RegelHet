# Bunnik Source Comparison Demo Design

## Summary

Build a small comparison-focused demo that shows how one target business in Bunnik appears under three sourcing strategies:

1. Open source only
2. Google Places only
3. Google Places plus KVK enrichment

The first target business is `Installatieburo Hevi BV`. The output is a side-by-side table intended for customer review, not a bulk export pipeline.

## Goal

Help the customer decide which data sourcing strategy gives the best quality for finding likely employer businesses in a target place, starting with a single dry-run example.

## Non-goals

- No full-village crawl yet
- No bulk export yet
- No automatic employee-count filtering across all businesses yet
- No rewrite of the existing healthcare website scraper

## User-facing outcome

The CLI should accept a target business name and location and print a normalized comparison table with these fields:

- `Bedrijfsnaam`
- `Adres`
- `Postcode`
- `Plaatsnaam`
- `Bedrijfsoort`
- `Bron`
- `Confidence / Notes`

Each row group should correspond to one of the three scenarios so the customer can compare completeness, consistency, and confidence.

## Architecture

Add a new comparison-oriented flow alongside the existing healthcare scraper instead of changing the current domain crawler behavior.

The new flow should have four focused responsibilities:

1. Query one provider and capture its raw result
2. Normalize that result into a shared business record model
3. Render a side-by-side table for terminal output
4. Keep live API access optional behind environment variables

## Components

### Shared business comparison model

Create a normalized model for a single business comparison row. This model should hold the shared customer-facing fields plus traceability metadata such as source name and notes.

### Open source provider

Use an open source directory-style source, with OpenStreetMap Overpass as the expected first choice, to find the target business in Bunnik and map tags into the shared model.

This provider should prefer exact or near-exact name matches and keep notes when fields are missing or inferred from tags.

### Google Places provider

Use Google Places to search for the same target business and map returned name, formatted address, address components, and type/category information into the shared model.

This provider should keep notes about which fields came directly from Places and which ones required mapping.

### Google Places plus KVK provider

Start from the Google Places match, then enrich it with KVK data where available. This provider should prefer official Dutch address and business classification data from KVK when a confident match is found.

It should also add an employee-related signal to the notes when KVK returns it, because that matters for the arbodienst use case.

### Table renderer

Render the three normalized results in a single compact table suitable for terminal demos. Missing values should be shown clearly rather than silently omitted.

## Data flow

1. User runs a new comparison CLI command with business name and location.
2. The command requests a record from the open source provider.
3. The command requests a record from the Google Places provider.
4. The command requests a record from the Google Places plus KVK provider.
5. All provider outputs are normalized into the shared model.
6. The table renderer prints a side-by-side comparison for demo review.

## Matching strategy

For this first demo, matching should be conservative:

- exact name match first
- normalized near-exact name match second
- same-place check required for Bunnik
- if matching is ambiguous, keep the record but lower confidence and explain why in notes

This reduces the chance of showing a polished but incorrect demo row.

## Error handling and observability

The new flow should keep the current project's structured logging style:

- request boundaries
- provider calls
- provider failures
- match ambiguity

Errors must be explicit in output notes. If a provider fails or lacks credentials, the demo should still render a row for that provider with missing values and a clear explanation.

## Testing strategy

Add fixture-based tests for:

- provider-to-model normalization
- table rendering
- confidence and notes behavior for missing fields

Live provider tests should not run by default. They should be gated by environment variables so local unit tests stay deterministic.

## Documentation

Update:

- `README.md` with the new comparison demo purpose and usage
- `docs/index.md` if introduced in this repo
- `docs/FEATURES.md` if the demo is treated as a feature entry
- a module-scoped change note for the affected module

## Risks

- Google Places and KVK matching may not resolve to the same legal entity on the first pass
- OpenStreetMap may have sparse or differently categorized data for the target business
- Employee-related signals may be incomplete and should be presented as enrichment, not hard truth

## Rollout path

If the one-record Bunnik demo is successful, the next phase can expand from single-business comparison to a small location-wide candidate list for Bunnik using the same provider abstractions and normalized output model.
