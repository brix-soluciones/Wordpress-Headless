# Phase 1 Data Model: WordPress REST Exposure Normalizer Plugin

This plugin does not introduce new persistent data beyond one settings
value. The entities below are the shapes it reads from or exposes about
WordPress's existing data, as identified in `spec.md`'s Key Entities.

## Site map entry

Represents one discoverable, publicly published content item, as returned
by the discovery endpoint (FR-001, FR-002, FR-010).

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `url` | string (absolute URL) | `get_permalink()` | Public URL; never a preview/draft URL. |
| `type` | string | post type slug (e.g. `post`, `page`, a CPT slug) | Identifies which content type this item belongs to. |
| `modified` | string (ISO 8601 datetime, UTC) | `post_modified_gmt` | MUST reflect true last modification time (FR-010); used by callers to diff against a prior sync. |

**Inclusion rule** (FR-002): only items with post status `publish`, from
post types with `public => true`, are included — **except** the post
types listed in `migration_toolkit_get_excluded_post_types()`
(`attachment`, `elementor_library`), which are excluded even though they
may be registered `public => true`: they are not real site content
(media is covered separately via `/wp/v2/media`; `elementor_library` is
Elementor's internal template/kit library, observed in practice
registered as public on a real site). Draft, private, trashed, and
password-protected items are excluded regardless of post type.

**Not persisted by the plugin** — computed fresh on each request from
WordPress's own post table via `WP_Query`.

## Exposed content type

Represents a custom post type or ACF field group that the plugin has made
readable through the standard WordPress REST API (FR-003, FR-004, FR-005).
This is existing WordPress configuration being surfaced/forced, not a new
entity the plugin owns or stores — there is no plugin-side record; whether
a type is "exposed" is fully derived at runtime from `show_in_rest` on the
post-type/field registration, which the plugin sets via filters.

| Concept | Type | Rule |
|---------|------|------|
| Post type REST exposure | derived (filter-applied) | Only touched when `public => true` on the post type (FR-004: non-public types are never forced). |
| ACF field REST exposure | derived (filter-applied) | Only touched for field groups attached to a REST-readable content type; no-op if ACF is not active. |

## Allowed origin

Represents a domain the site administrator has configured as permitted to
make cross-origin (CORS) requests to the WordPress REST API (FR-006,
FR-007). This is the plugin's one piece of actual persisted state.

| Field | Type | Storage | Notes |
|-------|------|---------|-------|
| Allowed origins list | array of origin strings (scheme + host, e.g. `https://example-astro-site.com`) | single `wp_options` entry (option name: `migration_toolkit_allowed_origins`) | Defaults to an empty array (no origins allowed) until an administrator configures at least one — CORS fails closed by default (spec Assumptions). |

**Validation rule**: each entry MUST be a well-formed absolute origin
(scheme + host, no path); malformed entries are rejected at save time
rather than silently accepted and later failing to match at request time.

## Relationships

- A **site map entry** always corresponds to exactly one WordPress post (of
  some public, published post type); it has no direct relationship to
  **exposed content type** or **allowed origin** — those affect *how* the
  underlying content is reachable, not what the site-map lists.
- **Exposed content type** and **allowed origin** are independent,
  orthogonal settings; a content type can be REST-exposed regardless of
  CORS configuration, and vice versa.

## State transitions

None of these entities have a lifecycle beyond WordPress's own (a post
moves through draft → publish → trash, entirely managed by WordPress core;
the plugin only reads the current state at request time). The allowed
origins list changes only through explicit administrator action (add/remove
an origin); there is no automatic expiry or transition.
