# Phase 1 Data Model: WordPress MCP Tools Server

All entities below are transient — read from the target WordPress site on
each call and returned to the calling agent. Nothing is persisted by this
server (see `plan.md` Technical Context: Storage — N/A).

## SiteMapEntry

One discoverable content item, as returned by `get_site_map` (spec: "Site
map entry"; FR-001).

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | WordPress's numeric post identifier — the same `id` `get_page_content` requires. Added to the plugin's response post-ship (`specs/001-wp-rest-normalizer`'s T010b, prompted by `specs/003-astro-migration-skill` finding no other way to resolve it); this server needed no code change since `get_site_map` already passes the plugin's response through as-is. |
| `url` | string | Absolute public URL, as returned by the plugin's discovery endpoint. |
| `type` | string | Post type slug (`post`, `page`, or a custom post type slug). |
| `modified` | string (ISO 8601) | Last-modified datetime, used by the caller to diff successive site maps. |

Source: `GET /wp-json/migracion/v1/site-map` (feature 001's contract) —
this server passes the `items` array through as-is, one `SiteMapEntry` per
element.

## PageContent

The plain content of a specific post or page (spec: "Page content";
FR-002).

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | The requested identifier, echoed back. |
| `type` | string | `"post"` or `"page"` — which native REST collection resolved the id (research.md #5). |
| `title` | string | Plain text, rendered title. |
| `content` | string | Plain text content (rendered field's text, not raw block/shortcode markup). |
| `custom_fields` | object \| absent | The `acf` object from the REST response, passed through as-is when present; the key is omitted entirely (not `null`) when the site exposes no ACF data for this item. |

Not found (no matching id in either `posts` or `pages`, or the matching
item isn't publicly published) → tool raises rather than returning a
partial `PageContent` (research.md #7; FR-010).

## RenderedStructure

The simplified layout outline of a public page URL (spec: "Rendered
structure"; FR-003, FR-004, FR-012).

| Field | Type | Notes |
|-------|------|-------|
| `url` | string | The requested URL, echoed back. |
| `rendering_method` | `"fetch"` \| `"headless_render"` | Which resolution path produced this outline (research.md #3) — lets the agent/caller know whether the fallback fired. |
| `scope` | string | Which part of the page `outline` is rooted at: `"main"` (default, when the page has a `<main>` landmark), `"body"` (default's fallback when no `<main>` exists, or an explicit request for the whole page), or the caller's own selector string when one was passed (research.md #11; FR-012). |
| `outline` | OutlineNode | Root of the simplified structure tree, rooted at whatever `scope` names — not necessarily the page's `<body>`. |

### OutlineNode

| Field | Type | Notes |
|-------|------|-------|
| `tag` | string | HTML tag name, e.g. `"div"`, `"section"`. |
| `id` | string \| absent | The element's `id` attribute, when present. |
| `class` | array of string \| absent | The element's class list, when present. |
| `text` | string \| absent | Direct text content of this node (not descendants'), when non-empty. |
| `children` | array of OutlineNode | Nested child elements, in document order; empty array for leaf nodes. |

Guarantee: no `OutlineNode`, at any depth, can carry `_elementor_data` or
any Elementor-internal field — the outline is derived purely from the
resolved DOM, which has no path to that data (Constitution Article I;
FR-005).

## MediaOriginal

The full-resolution source file behind a media item (spec: "Media
original"; FR-006).

| Field | Type | Notes |
|-------|------|-------|
| `slug` | string | The requested slug, echoed back. |
| `source_url` | string | The original, full-resolution file URL (`source_url` from the `/wp/v2/media` response — never a `media_details.sizes.*` variant). |
| `mime_type` | string | The media item's MIME type, as returned by WordPress. |

Not found (empty result for the slug) → tool raises rather than returning
a partial `MediaOriginal` (research.md #6; FR-010).

## ServerConfig

Process-level configuration, read once at startup (spec: "Site
configuration"; FR-007) — not returned by any tool, but shapes every
call.

| Field | Type | Notes |
|-------|------|-------|
| `base_url` | string | The target WordPress site's base URL, from the `WP_MCP_BASE_URL` environment variable. Server fails fast at startup if unset or malformed. |

## Relationships

- `SiteMapEntry.url` values are the expected input shape for
  `get_rendered_structure`'s `url` parameter, and `SiteMapEntry.type` +
  the id embedded in typical WordPress permalinks hint at, but do not
  directly supply, `get_page_content`'s numeric `id` — the two tools are
  independently callable (FR-011), not chained by contract.
- `RenderedStructure.outline` nodes may reference images whose filename
  or slug a caller can pass to `get_media_original` — no direct field
  linkage is enforced by this server; resolving that association is the
  calling agent's responsibility.
- Every URL passed to `get_rendered_structure` MUST share a hostname with
  `ServerConfig.base_url` (research.md #8; spec edge case) — enforced at
  call time, not persisted as a relationship.
