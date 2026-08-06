# Contract: `get_site_map`

Covers FR-001, FR-010, FR-011.

## Input

No parameters. Operates against the site configured via `WP_MCP_BASE_URL`
(`ServerConfig.base_url`).

## Output — success

```json
{
  "items": [
    { "url": "https://origin-site.example/blog/hello-world/", "type": "post", "modified": "2026-07-30T14:22:05+00:00" },
    { "url": "https://origin-site.example/services/consulting/", "type": "page", "modified": "2026-06-11T09:03:44+00:00" }
  ]
}
```

`items` is an array of `SiteMapEntry` (see `data-model.md`), passed
through from the companion plugin's discovery endpoint response
(`GET {base_url}/wp-json/migracion/v1/site-map`, feature 001's contract)
without modification. Empty array is a valid, successful response (a site
with no public content) — not an error.

## Error conditions (raise, per research.md #7)

| Condition | Behavior |
|-----------|----------|
| Discovery endpoint returns non-2xx (e.g. plugin not installed → `404`) | Raise with a message identifying that the discovery endpoint is missing/unreachable — never returned as a silent empty list (spec edge case). |
| Target site unreachable (DNS/connection/timeout) | Raise with a message identifying the connectivity failure. |

## Guarantees

- Never includes non-public content — inherited from the plugin's own
  contract (feature 001), not re-filtered here.
- Never contains `_elementor_data` — the response shape has no field
  capable of carrying it.
