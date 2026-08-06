# Quickstart: Validating the REST Exposure Normalizer Plugin

This is the plugin's verification path in place of an automated test suite
(see `research.md` — no PHPUnit/Composer, per the zero-dependency
constraint). It proves the feature end-to-end against a real running
WordPress instance, in the spirit of the constitution's Article VIII.

## Prerequisites

- A standard WordPress installation (PHP 7.4+), reachable via WP-CLI and
  over HTTP.
- At least one custom post type registered as `public => true` without
  `show_in_rest` set, for exercising FR-003.
- ACF active, with at least one field group attached to a public content
  type, for exercising FR-005 (optional — skip this step if validating a
  site without ACF, to confirm the no-op path from `research.md`).
- At least one draft or private post, for exercising FR-002.

## Setup

1. Copy `plugin/` into `wp-content/plugins/migration-toolkit/` on the
   target WordPress installation. No `composer install` or build step —
   the plugin is plain PHP.
2. Activate it:
   ```
   wp plugin activate migration-toolkit
   ```
   **Expected**: activates with no fatal errors and no setup wizard/required
   configuration step (Constraints in `plan.md`).

## Validation scenarios

### 1. Site-map discovery endpoint (FR-001, FR-002, FR-010 — see `contracts/site-map-endpoint.md`)

```
curl -s https://<site>/wp-json/migracion/v1/site-map | jq .
```

- **Expected**: `items` array containing every published post/page/CPT
  entry, each with `url`, `type`, `modified`.
- Confirm the draft/private post from Prerequisites does **not** appear.
- Edit one listed item's content, re-run the request, and confirm its
  `modified` value changed while unrelated items' values did not — this is
  the diffing behavior FR-010 exists to guarantee.

### 2. Forced REST exposure for a CPT (FR-003, FR-004 — see `contracts/rest-exposure.md`)

```
curl -s https://<site>/wp-json/wp/v2/<cpt-rest-base>
```

- **Expected**: `200` with that post type's entries, even though it wasn't
  REST-exposed before the plugin was active.
- Repeat against a known non-public/internal post type (if the site has
  one) and confirm it still returns `404 rest_no_route` — the plugin must
  not have widened its exposure.

### 3. ACF field exposure (FR-005 — see `contracts/rest-exposure.md`)

```
curl -s https://<site>/wp-json/wp/v2/<rest-base>/<id> | jq '.acf'
```

- **Expected**: the ACF field group's values are present in the response.
- On a site without ACF active, confirm the plugin still activates and
  passes scenarios 1 and 2 (no-op path).

### 4. CORS (FR-006, FR-007 — see `contracts/cors.md`)

**First**, check whether the target site sits behind a CDN or host-level
edge cache — look for vendor-specific response headers (e.g. Hostinger's
`x-hcdn-*`, Cloudflare's `cf-cache-status`, `Age`, `x-cache`). If present,
read the "Known limitations" section below *before* running this scenario:
some CDNs inject their own `Access-Control-Allow-Origin` for every request,
independent of the plugin, which makes this scenario's checks
inconclusive on that host.

Before configuring any origin:

```
curl -s -H "Origin: https://not-yet-allowed.example" -I https://<site>/wp-json/migracion/v1/site-map
```

- **Expected**: no `Access-Control-Allow-Origin` header in the response.

Configure `https://astro-site.example` as an allowed origin via the
plugin's settings field, then:

```
curl -s -H "Origin: https://astro-site.example" -I https://<site>/wp-json/migracion/v1/site-map
```

- **Expected**: `Access-Control-Allow-Origin: https://astro-site.example`
  present.

```
curl -s -H "Origin: https://still-not-allowed.example" -I https://<site>/wp-json/migracion/v1/site-map
```

- **Expected**: still no `Access-Control-Allow-Origin` header — only the
  configured origin is granted (FR-007).

### 5. No Elementor data, ever (FR-008)

```
grep -ri "_elementor_data" plugin/
```

- **Expected**: zero matches, anywhere in the plugin source.
- Additionally confirm none of the responses in scenarios 1–3 contain the
  string `elementor` in any field.

### 6. No content mutation (FR-009)

- Record the site's total published-content count and every item's
  `post_modified` timestamp before running scenarios 1–4.
- Re-check after: identical counts, and no `post_modified` timestamps
  changed except the one deliberately edited in scenario 1.

## Known limitations (CDN-fronted hosting)

Confirmed against a real WordPress install on Hostinger. Both findings are
edge/CDN behavior in front of WordPress, not plugin behavior — neither is
fixable from plugin code, since the CDN sits outside the PHP request
lifecycle the plugin runs in.

- **CORS is bypassed by the CDN, unconditionally.** Hostinger's CDN (visible
  via `x-hcdn-*` response headers) added `Access-Control-Allow-Origin` for
  *any* origin, even with the plugin deactivated. On a host whose CDN does
  this, FR-007 ("MUST NOT grant cross-origin access to origins that have
  not been explicitly configured") does not actually hold end-to-end — the
  plugin correctly withholds the header at the WordPress/PHP layer, but the
  CDN grants access anyway before/around that layer. **If you operate a
  site behind a CDN, verify its own CORS behavior and configuration
  directly — do not rely on this plugin's CORS setting as the sole
  boundary.**
- **The CDN can cache the site-map endpoint.** Observed `Age` and
  `x-hcdn-cache-status: HIT` on repeated requests to
  `/wp-json/migracion/v1/site-map`. The plugin sends
  `Cache-Control: no-store, no-cache, must-revalidate, max-age=0` on that
  response specifically to prevent this (see
  `contracts/site-map-endpoint.md`), but not every CDN honors origin cache
  headers for every path. A stale cached copy silently breaks the FR-010
  guarantee (`modified` reliably reflecting recent changes) for as long as
  the CDN serves it. **If your host's CDN caches this endpoint regardless
  of the header, add an explicit cache-bypass rule for
  `/wp-json/migracion/v1/*` in the CDN/host configuration** — this plugin
  cannot force that from within WordPress.

## Done when

All six scenarios above match their expected outcomes on a real WordPress
instance with no manual workarounds or additional configuration beyond the
one CORS origin added in scenario 4 — on a site with no CDN in front, or
with the CDN's cache/CORS behavior for `/wp-json/migracion/v1/*` already
accounted for per the "Known limitations" section above.
