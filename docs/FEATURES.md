# Features

### F-001: Bunnik Source Comparison Demo
Reference: `bunnik-source-comparison-demo`

Capabilities:
- Compare one target business across OpenStreetMap, Google Places, and Google Places plus KVK
- Normalize the provider outputs into one shared customer-facing table
- Preserve demo output even when paid-provider credentials are missing

Configuration:
- `GOOGLE_PLACES_API_KEY`
- `KVK_API_KEY`
- `KVK_SEARCH_URL` for custom KVK environments

Related endpoints:
- None. This feature is exposed through the CLI.
