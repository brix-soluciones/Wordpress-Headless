# Contract: `astro-site/manifest.json`

Covers FR-002, FR-009, FR-010, FR-011, FR-012.

## Location

`astro-site/manifest.json` — at the target Astro project's root, never
under `skill/` (explicit user constraint).

## Shape

```json
{
  "pages": [
    {
      "wp_slug": "branding",
      "pattern": "portfolio",
      "astro_file": "src/pages/branding.astro",
      "last_synced_modified": "2026-07-30T14:22:05+00:00"
    },
    {
      "wp_slug": "about-us",
      "pattern": "simple-text-page",
      "astro_file": "src/pages/about-us.astro",
      "last_synced_modified": null
    }
  ]
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `pages` | array | Yes | One entry per page that has a human-assigned component pattern. Empty array (or a missing file) means no page has been migrated yet — not an error. |
| `pages[].wp_slug` | string | Yes | Identifies the source WordPress page/post. |
| `pages[].pattern` | string | Yes | Project-specific pattern name; this feature never invents values for this field (FR-012). |
| `pages[].astro_file` | string | Yes | Path, relative to `astro-site/`, of the corresponding Astro file. |
| `pages[].last_synced_modified` | string (ISO 8601) \| `null` | Yes (may be `null`) | The source page's `modified` date as of the last successful sync; `null` before the first sync. |

## Guarantees

- If `astro-site/manifest.json` doesn't exist, the skill treats it as
  `{ "pages": [] }` — every page is then unmatched/flagged — rather than
  raising an error (spec edge case: "no manifest yet").
- The skill only ever **reads** `pattern`/`astro_file` values and
  **writes** `last_synced_modified` for existing entries plus (after an
  explicit human decision) new entries' initial values — it never
  invents or changes a `pattern` value on its own initiative (FR-012).
- A `wp_slug` appears at most once in `pages` — it is the join key
  against `get_site_map`'s entries for both classification (is this page
  already migrated?) and sync (has it changed since `last_synced_modified`?).

## Error conditions

| Condition | Behavior |
|-----------|----------|
| File exists but isn't valid JSON, or `pages` isn't an array | The skill stops and reports the malformed manifest rather than guessing at its contents or overwriting it. |
| An entry is missing a required field | That entry is reported as invalid; it is not treated as a valid match for its `wp_slug`. |
