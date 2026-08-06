# Phase 1 Data Model: WordPress-to-Astro Migration Skill

Only one entity is actually persisted by this feature
(`manifest.json` — see research.md #4, #5). The others are computed fresh
each run and only ever appear in a run's report.

## ManifestEntry (persisted)

One row of `astro-site/manifest.json` (spec: "Manifest entry"; FR-002,
FR-009, FR-010, FR-011, FR-012).

| Field | Type | Notes |
|-------|------|-------|
| `wp_slug` | string | Identifies the source WordPress page/post this entry maps from. |
| `pattern` | string | Name of the known component pattern this page uses (project-specific vocabulary; this feature never invents pattern names, only applies human-assigned ones — FR-012). |
| `astro_file` | string | Path (relative to `astro-site/`) of the Astro component/page file this entry corresponds to. |
| `last_synced_modified` | string (ISO 8601) \| `null` | The source page's `modified` date (from `get_site_map`) as of this entry's last successful sync. `null` until the first sync after this entry is created. |

**Existence rule**: a page has this entry if and only if a human has
decided its component pattern — the skill never creates an entry on its
own initiative (FR-012). Absence of an entry for a given page is exactly
what makes that page a "new page" (User Story 1/2's flow) rather than a
sync target (User Story 3's flow).

## LayoutRelevamiento (ephemeral)

The `RenderedStructure` returned by the MCP's `get_rendered_structure`
(see `specs/002-wp-mcp-tools/data-model.md`) for a page not yet in the
manifest (spec: "Layout relevamiento"; FR-001). Consumed immediately for
classification against the manifest's known `pattern` values; not stored.

## FlaggedPage (ephemeral)

A page whose relevaded layout matched no `pattern` in `manifest.json`
(spec: "Flagged page"; FR-003). Recomputed every run (research.md #5) —
appears only in that run's report, alongside a description of what was
relevaded, so a human has enough context to decide.

| Field | Type | Notes |
|-------|------|-------|
| `wp_slug` | string | The unmatched page's identifier. |
| `url` | string | The unmatched page's public URL. |
| `reason` | string | Human-readable note on why no pattern matched (e.g. "no manifest entry"; future pattern-matching logic may enrich this further — see tasks.md for what's actually implemented in this pass). |

## VerificationResult (ephemeral)

The pass/fail outcome for one page's responsive and build checks (spec:
"Verification result"; FR-005 through FR-008). Recomputed every run
(research.md #5) — appears only in that run's report.

| Field | Type | Notes |
|-------|------|-------|
| `wp_slug` | string | Which manifest entry this result is for. |
| `responsive` | object | `{ "320": bool, "375": bool, "768": bool, "1024": bool, "1920": bool }` — pass/fail per viewport width; a page's overall responsive result is the AND of all five. |
| `build_passed` | bool | Whether the shared build (research.md #2) succeeded with this page's component present in `dist/`. |
| `complete` | bool | `responsive` all-true AND `build_passed` — whether this page counts as migrated/updated (FR-006, FR-008). |

## Relationships

- A `FlaggedPage` and a `ManifestEntry` are mutually exclusive for the
  same `wp_slug` in a given run: a page is either matched (has/gets a
  `ManifestEntry`) or flagged, never both.
- A `VerificationResult` only ever exists for a page that has (or, this
  run, is getting) a `ManifestEntry` — flagged pages are never verified,
  since no component exists yet to check.
- `ManifestEntry.last_synced_modified` is compared against the
  corresponding `get_site_map` entry's `modified` date (see
  `specs/002-wp-mcp-tools/data-model.md`'s `SiteMapEntry`) to decide, per
  User Story 3, whether that entry's page needs a content sync this run.
