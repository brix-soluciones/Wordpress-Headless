# Contract: Draft output shape

Covers FR-002, FR-003, FR-004, FR-009. This is the boundary between this
tool and two different consumers: the human reviewing the draft, and (only
after promotion) `specs/003-astro-migration-skill`'s migration skill.

## Location

```text
astro-site/.pattern-drafts/<slug>/
├── component.astro
└── page.astro
```

`<slug>` is the `PageReference`'s resolved slug (`data-model.md`). Never
written directly into `src/components/` or `src/pages/` (FR-004).

## `component.astro`

A freeform Astro component draft — no fixed schema, since a pattern's
props/structure are inherently page-type-specific (this is exactly what
the constitution keeps a human (now human+AI-assisted) design decision,
not a generated-to-spec artifact). Reviewed and edited by the human
before it means anything.

## `page.astro`

**Not freeform** — this file's shape is the actual interface contract
with `specs/003-astro-migration-skill` (research.md #5), and MUST follow
it exactly so a promoted draft is immediately usable by the migration
skill with no manual restructuring:

```astro
---
import ComponentName from '../components/ComponentName.astro';
const props = {
  title: '...',
  content: '...',
  // ...whatever fields this page's content/media resolved to
};
---
<ComponentName {...props} />
```

**The import path is written for the post-promotion location, not the
staging location.** While staged, `page.astro` and `component.astro` sit
as siblings under `astro-site/.pattern-drafts/<slug>/` — a literal
sibling-relative path (`./component.astro`) would be correct *there* but
break the moment a human promotes the files to their real destination
(`src/pages/` and `src/components/`, no longer siblings). The import
path MUST instead already be `../components/ComponentName.astro`, as if
both files were already at that destination — matching what
`specs/003-astro-migration-skill`'s own example shows a real,
already-placed page file looks like — even though that path only
resolves correctly *after* promotion, not while staged. Confirmed
against `skill/SKILL.md`'s actual "Poblar componente" text
(`specs/003-astro-migration-skill`'s own worked example uses exactly
this `'../components/PatternMVP.astro'` shape from `src/pages/branding.astro`).

| Requirement | Why |
|-------------|-----|
| A single `import` of the drafted component, at its **post-promotion** relative path | `specs/003-astro-migration-skill`'s "Poblar componente" never touches this line — it must already be correct, with no manual fixing, when 003 first processes this page after promotion. |
| A single `const props = {...}` object | Same reason — 003 only ever rewrites this object's contents, never the surrounding structure. |
| `<ComponentName {...props} />` | Same reason. |

## Guarantees

- Nothing is written if `astro-site/.pattern-drafts/<slug>/` already
  exists — the tool stops and tells the human instead (FR-009).
- Nothing is written if `PageReference` resolution or any MCP tool call
  fails partway through (FR-008) — no partial draft.
- Every image the draft references resolves to `get_media_original`'s
  `source_url` (original, full-resolution) — never a cropped/resized
  variant (FR-010).
- This tool never writes to `astro-site/manifest.json` and never writes
  into `src/` — both remain explicit, separate human actions (FR-004,
  FR-006).
