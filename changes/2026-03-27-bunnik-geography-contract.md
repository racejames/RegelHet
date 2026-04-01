## What changed

- Added a shared Bunnik geography contract in the business source selectors.
- Added provider-specific Bunnik resolution for OSM, Google Places, and KVK.
- Added rollout tests that cover Bunnik acceptance, rejection, and fallback behavior.

## How to test locally

- Set `PYTHONPATH` to `D:\Repos\vanGrondwelle.worktrees\9-bunnik-geography-contract\src`
- Run `python -m pytest tests/test_bunnik_rollout.py -k bunnik_filter -v`
- Run `python -m pytest`

## Risks/rollback

- Risk: Bunnik filtering could become too strict or too loose for provider payloads with partial address data.
- Rollback: revert the business source changes and remove the Bunnik rollout test file.

## Docs touched

- `changes/2026-03-27-bunnik-geography-contract.md`
