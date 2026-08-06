# Contract: `get_page_content`

Covers FR-002, FR-010, FR-011.

## Input

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | integer | Yes | WordPress post/page identifier. |

## Output — success

```json
{
  "id": 42,
  "type": "page",
  "title": "Consulting Services",
  "content": "We help teams migrate legacy WordPress sites...",
  "custom_fields": { "hero_subtitle": "Ship faster, break less" }
}
```

See `data-model.md`'s `PageContent`. `custom_fields` is **omitted
entirely** (not present as a key) when the site exposes no ACF data for
this item — callers must not treat its absence as an error.

## Resolution order (research.md #5)

1. `GET {base_url}/wp-json/wp/v2/posts/{id}`
2. On `404` from step 1, `GET {base_url}/wp-json/wp/v2/pages/{id}`

## Error conditions

| Condition | Behavior |
|-----------|----------|
| `id` doesn't match any post or page (404 from both lookups) | Raise "not found" — never returns draft/private content, never a silently empty/partial body (spec edge case, FR-010). |
| Matching item exists but isn't publicly published | Raise "not found" — same as above; this tool never surfaces non-public content (FR-008). |
| Target site unreachable | Raise with a connectivity-failure message. |

## Guarantees

- Only reads WordPress's native `/wp/v2/posts` and `/wp/v2/pages`
  collections (Constitution Article IV) — no custom post types through
  this tool (see `spec.md` Assumptions).
- Succeeds normally when ACF isn't installed/exposed — `custom_fields` is
  simply absent, not an error (spec edge case).
