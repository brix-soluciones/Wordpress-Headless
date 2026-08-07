# Contract: Site Map Discovery Endpoint

Covers FR-001, FR-002, FR-010.

## `GET /wp-json/migracion/v1/site-map`

Read-only discovery endpoint. No authentication required (spec Assumptions:
it only ever surfaces content that is already publicly viewable on the
site).

### Request

No parameters in this version (see `research.md` — filtering by
`modified_after` is explicitly out of scope; the caller fetches the full
list and diffs it against a previously stored response).

### Response — `200 OK`

```json
{
  "items": [
    {
      "id": 101,
      "url": "https://origin-site.example/blog/hello-world/",
      "type": "post",
      "modified": "2026-07-30T14:22:05+00:00"
    },
    {
      "id": 42,
      "url": "https://origin-site.example/services/consulting/",
      "type": "page",
      "modified": "2026-06-11T09:03:44+00:00"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|--------------|
| `items` | array | One entry per publicly published content item on the site. Empty array (not an error) if the site has no public content. |
| `items[].id` | integer | WordPress's numeric post identifier. Added post-ship (`specs/003-astro-migration-skill`'s integration work found no other way to resolve the `id` that reading a post's content via native REST requires). |
| `items[].url` | string | Absolute public URL of the item. |
| `items[].type` | string | Post type slug (`post`, `page`, or a custom post type slug). |
| `items[].modified` | string | ISO 8601 datetime (UTC) of the item's last modification. |

### Guarantees

- Only items with post status `publish` and post type `public => true`
  appear (FR-002). Draft, private, trashed, and password-protected content
  is never included, under any request.
- Post types that are `public => true` but are not real site content are
  excluded regardless: `attachment` (media, covered separately via
  `/wp/v2/media`) and `elementor_library` (Elementor's internal
  template/kit library — page-builder plumbing, not content, though
  WordPress/Elementor can register it as `public => true`). See
  `migration_toolkit_get_excluded_post_types()` in
  `plugin/includes/functions.php`.
- `modified` always reflects the item's true last-modified time (FR-010) —
  comparing two responses over time is sufficient to detect changed items.
- The response never includes `_elementor_data` or any Elementor-internal
  field, in this or any other form (FR-008) — this endpoint's shape has no
  field capable of carrying it.
- Calling this endpoint never creates, modifies, or deletes any WordPress
  content (FR-009) — it is read-only.
- The response is sent with `Cache-Control: no-store, no-cache,
  must-revalidate, max-age=0`, in support of the FR-010 guarantee above —
  the plugin itself never intends this response to be cached. Whether a
  host-level page cache or CDN in front of WordPress honors that header is
  outside the plugin's control — see `quickstart.md`'s known-limitations
  section for a confirmed real-world exception.

### Error responses

| Status | Condition |
|--------|-----------|
| `500` | Unexpected server-side failure (e.g. database error). Standard WordPress REST API error envelope (`code`, `message`, `data.status`). |

No `4xx` auth-related errors are defined for this version — the endpoint is
public/unauthenticated per the spec's Assumptions.
