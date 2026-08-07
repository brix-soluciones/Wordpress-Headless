# Feature Specification: Pattern Authoring Assistant Skill

**Feature Branch**: `004-pattern-authoring-assistant`

**Created**: 2026-08-07

**Status**: Draft

**Input**: User description: "Skill de Claude Code separada del skill de migración (specs/003-astro-migration-skill), invocada solo a mano por un humano cuando una página quedó flaggeada sin patrón conocido. Ayuda a redactar un primer borrador del componente de patrón Astro (ej. src/components/NuevoPatron.astro) usando como referencia el layout ya relevado de esa página (el outline de get_rendered_structure que el skill de migración adjunta al reporte de flaggeo) y su contenido (get_page_content). El humano revisa/ajusta el borrador antes de darlo por bueno. Una vez aprobado, el humano (no esta skill) agrega la entrada correspondiente a astro-site/manifest.json para que el skill de migración lo aplique en la próxima corrida. Esta skill nunca se dispara automáticamente ni es parte del loop de migración/sync — es una herramienta de apoyo al paso humano de diseño de patrones (Artículo III de la constitution), nunca reemplaza esa decisión ni la fuerza."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Draft a pattern component from a flagged page (Priority: P1) 🎯 MVP

Someone doing a migration has a page the migration skill flagged — its layout
doesn't match any pattern built so far. Rather than hand-writing an Astro
component from scratch by eyeballing the source page, they want a
reviewable first draft built from that page's actual layout and content.

**Why this priority**: This is the entire value of the tool — turning "a
human has to design a component from scratch" into "a human reviews and
adjusts a draft." Without it, there's nothing to build on.

**Independent Test**: Give the tool the identifier of a page with a
distinctive layout, and confirm it produces a draft Astro component file
reflecting that page's actual structure, without touching any file the
migration skill treats as an already-approved pattern.

**Acceptance Scenarios**:

1. **Given** the URL or slug of a specific page, **When** the human
   invokes the tool with it, **Then** it retrieves that page's current
   rendered layout and content from the source site before drafting
   anything.
2. **Given** that retrieved layout and content, **When** the tool drafts
   a component, **Then** the draft reflects the page's actual structure
   and is written somewhere clearly separate from the project's trusted,
   already-approved pattern components.
3. **Given** a draft has been produced, **When** the human reviews it,
   **Then** they can freely edit it before deciding whether to adopt it —
   the tool does not register it as an approved pattern on its own.

---

### User Story 2 - Draft the page wiring for the new pattern (Priority: P2)

Once there's a draft pattern component, someone still needs a page file
that imports it and passes this specific page's content as props — the
exact shape the migration skill expects to find already in place before
it can populate a page (per `specs/003-astro-migration-skill`).

**Why this priority**: This unblocks the migration skill's own
precondition for a newly-approved pattern, but only matters once User
Story 1 has already produced a draft component to wire up.

**Independent Test**: With a drafted pattern component in hand, confirm
the tool also produces a draft page file that imports it and passes this
page's real retrieved content as props, in the same staging location as
the component draft.

**Acceptance Scenarios**:

1. **Given** a drafted pattern component for a page, **When** the tool
   finishes, **Then** it also produces a draft page file that imports
   that component and passes this page's title/content/media as props.
2. **Given** the drafted page file, **When** a human later approves the
   pattern and the migration skill runs, **Then** the migration skill's
   own content-population step can correctly find and update that page's
   props without any special-casing for it having come from this tool.

---

### Edge Cases

- What happens when the given page identifier doesn't resolve on the
  source site? The tool stops and reports that clearly — no draft is
  attempted from guessed or partial data.
- What happens when retrieving the page's layout, content, or an image it
  references fails partway through? The tool stops and reports the
  failure — it never produces a partial or silently-incomplete draft.
- What happens when a draft already exists at the staging location for
  the same page? The tool does not silently overwrite it — it surfaces
  that to the human before doing anything further.
- What happens if the human runs this tool for a page that already has an
  approved pattern in the manifest? Nothing prevents it (the tool has no
  dependency on flag state, which the migration skill doesn't persist
  anyway — see Assumptions), but it's an unusual use; the tool behaves
  the same as for any other page identifier.
- What happens if the human never acts on a draft? It simply sits in the
  staging location — the tool has no cleanup or expiry behavior, and
  produces no effect anywhere else in the project.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Given a page identifier (URL or slug) supplied by a human,
  the system MUST retrieve that page's current rendered layout and
  content from the source WordPress site before drafting anything.
- **FR-002**: The system MUST produce a first-draft Astro pattern
  component reflecting the retrieved page's actual layout structure.
- **FR-003**: The system MUST also produce a first-draft page file that
  imports the drafted pattern component and passes this page's retrieved
  content as props, matching the shape the migration skill expects to
  already exist before it populates a page.
- **FR-004**: All drafted output MUST be written to a location clearly
  separate from the project's trusted, already-approved pattern
  components and pages — never directly into those locations.
- **FR-005**: The system MUST NOT run automatically and MUST NOT be
  invoked as part of the migration or sync flow
  (`specs/003-astro-migration-skill`) — it starts only from an explicit,
  separate human action.
- **FR-006**: The system MUST NOT modify `astro-site/manifest.json` —
  registering an approved pattern remains a separate, explicit human
  action, never performed by this tool.
- **FR-007**: The system MUST NOT perform responsive or build
  verification on its drafted output — that remains the migration
  skill's responsibility once a human has approved the pattern.
- **FR-008**: If the given page identifier can't be resolved on the
  source site, or retrieving its layout/content/media fails, the system
  MUST stop and report the failure rather than drafting from incomplete
  or guessed data.
- **FR-009**: If a draft already exists at the staging location for the
  same page, the system MUST NOT silently overwrite it — it MUST surface
  this to the human before proceeding.
- **FR-010**: For any image the draft references, the system MUST
  resolve it to its original, full-resolution file — never a cropped or
  resized variant.

### Key Entities *(include if feature involves data)*

- **Draft pattern component**: A first-version Astro component file,
  written to a staging location, reflecting one page's relevaded layout.
  Not trusted/approved until a human says so.
- **Draft page file**: A first-version page file wiring a draft pattern
  component to one specific page's real, retrieved content.
- **Page reference**: The human-supplied identifier (URL or slug) that
  tells the tool which page to draft from.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A human can go from "a page has no matching pattern" to "a
  reviewable draft Astro component built from that page's real layout
  and content" without hand-writing any markup themselves.
- **SC-002**: No drafted output ever appears in the project's trusted
  pattern location, or in `astro-site/manifest.json`, without a separate,
  explicit human action.
- **SC-003**: 100% of failures to retrieve source data are reported
  clearly, with zero partial or guessed drafts produced as a result.
- **SC-004**: Using this tool, or not, has zero effect on any unattended
  migration or sync run — its presence changes nothing about
  `specs/003-astro-migration-skill`'s automated behavior.

## Assumptions

- This tool has no dependency on the migration skill's flag output being
  persisted anywhere — it isn't (see `specs/003-astro-migration-skill`'s
  research.md #5, flags are recomputed fresh each run and never written
  to a file). A human invokes this tool with a page identifier they
  already have in hand (typically copied from a recent flag report), not
  by reading some stored list of flagged pages.
- The tool reuses the same MCP tools the migration skill uses
  (`specs/002-wp-mcp-tools`) — no separate WordPress access path.
- Iterating on a draft (asking for changes, trying a different layout
  reading) happens through normal conversation in the same session — no
  separate "revision" mechanism is assumed.
- Editing or improving an already-approved pattern is out of scope — this
  tool is only for drafting a starting point for a page that doesn't
  match anything yet.
- The staging location for drafts is project configuration this tool
  owns (distinct from `astro-site/manifest.json`, which it never
  touches) — its exact path is a planning-time decision, not a
  spec-level one.
