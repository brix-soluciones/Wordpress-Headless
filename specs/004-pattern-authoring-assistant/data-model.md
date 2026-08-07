# Phase 1 Data Model: Pattern Authoring Assistant Skill

No entity here is persisted by this tool in any project-tracked
location — everything lives under the gitignored staging directory
(research.md #1) until a human promotes it, at which point it becomes an
ordinary, human-owned Astro file this feature no longer has any claim
over.

## PageReference

The human-supplied input identifying which page to draft from (spec:
"Page reference"; FR-001).

| Field | Type | Notes |
|-------|------|-------|
| `input` | string | URL or slug, as given by the human — typically copied from a recent migration-skill flag report. |
| `resolved_id` | integer | WordPress numeric id, resolved via `get_site_map()` the same way `specs/003-astro-migration-skill`'s Preámbulo does (research.md #4). Required before `get_page_content` can be called. |
| `resolved_url` | string | The matching `get_site_map()` entry's absolute URL. |

Not found on the source site → the tool stops and reports this (spec
edge case; FR-008), no `DraftPatternComponent`/`DraftPageFile` produced.

## DraftPatternComponent

The first-draft Astro pattern component (spec: "Draft pattern component";
FR-002).

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | `astro-site/.pattern-drafts/<slug>/component.astro` (research.md #1). |
| `source_outline` | RenderedStructure | The `get_rendered_structure` outline (`specs/002-wp-mcp-tools/data-model.md`) this draft was built from — informs the draft, not persisted separately from the file itself. |

Not trusted/approved until a human says so (FR-004) — promoting it means
a human copies/moves it into `src/components/` themselves; this tool
never does that.

## DraftPageFile

The first-draft page file wiring a `DraftPatternComponent` to one page's
real content (spec: "Draft page file"; FR-003).

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | `astro-site/.pattern-drafts/<slug>/page.astro` (research.md #1). |
| `props` | object | This page's `get_page_content` title/content/custom_fields, plus any `get_media_original`-resolved image URLs (research.md #6), passed to the imported component via `{...props}` (research.md #5 — the shape 003 expects). |

## Relationships

- A `DraftPatternComponent` and its paired `DraftPageFile` are always
  produced together, from the same `PageReference` — User Story 2 never
  runs without User Story 1 having just produced the component it wires
  up.
- Neither entity has any relationship to
  `specs/003-astro-migration-skill`'s `ManifestEntry` — that link is only
  created when a human explicitly adds one, an action this feature never
  performs (FR-006). Until then, these drafts are invisible to the
  migration skill entirely (it only ever reads `astro-site/manifest.json`
  and `src/`, never `.pattern-drafts/`).
