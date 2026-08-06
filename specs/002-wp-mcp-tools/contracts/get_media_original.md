# Contract: `get_media_original`

Covers FR-006, FR-010, FR-011.

## Input

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `slug` | string | Yes | Media item's identifying slug. |

## Output — success

```json
{
  "slug": "team-photo-2026",
  "source_url": "https://origin-site.example/wp-content/uploads/2026/07/team-photo-2026.jpg",
  "mime_type": "image/jpeg"
}
```

See `data-model.md`'s `MediaOriginal`. `source_url` is always the
original/full-resolution file — never a `media_details.sizes.*` cropped
or resized variant (FR-006, SC-004).

## Resolution

`GET {base_url}/wp-json/wp/v2/media?slug={slug}` → take the first array
element (research.md #6). Multiple matches (only reachable by direct
database manipulation under normal WordPress operation) resolve to the
first element — a documented limitation, not an error.

## Error conditions

| Condition | Behavior |
|-----------|----------|
| Result array is empty (no media item matches `slug`) | Raise "not found" — never returns an unrelated image (spec edge case, FR-010). |
| Target site unreachable | Raise with a connectivity-failure message. |
