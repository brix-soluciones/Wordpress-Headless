# Contract: Configurable CORS

Covers FR-006, FR-007.

## Configuration

A site administrator configures zero or more allowed origins (see
`data-model.md` — `Allowed origin`). Default on activation: empty list (no
origins allowed) — activating the plugin never opens CORS access by itself
(spec Assumptions, "no configuración adicional" for activation).

## Effect on REST API responses

For any request to `/wp-json/*` carrying an `Origin` request header:

| Condition | Response header |
|-----------|------------------|
| `Origin` value exactly matches a configured allowed origin | `Access-Control-Allow-Origin: <that origin>` is present in the response. |
| `Origin` value does not match any configured allowed origin (including when the list is empty) | No `Access-Control-Allow-Origin` header is added by this plugin (FR-007 — cross-origin access is never granted to unconfigured origins). |
| No `Origin` header present (server-to-server request) | Unaffected — CORS headers are a browser-enforced concept only; server-to-server requests never depended on them. |

## Guarantees

- No wildcard (`*`) origin is ever emitted — matching is exact, against the
  configured list only.
- Configuring an origin only affects CORS response headers; it grants no
  additional read access beyond what the REST API already exposes publicly
  (this plugin does not gate content behind CORS — CORS only affects
  whether a *browser* permits the calling page's JavaScript to read the
  response).
