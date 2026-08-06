# Feature Specification: WordPress-to-Astro Migration Skill

**Feature Branch**: `003-astro-migration-skill`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Skill de Claude Code para migrar contenido de WordPress a componentes Astro. Usa las 4 tools del MCP (feature 002): get_site_map y get_page_content para sync de contenido, get_rendered_structure para relevar layout de páginas nuevas, get_media_original para imágenes. Flujo: relevar página con get_rendered_structure, clasificar contra manifest.json del proyecto (mapeo página→patrón de componente conocido), si no hay patrón flaggear para decisión humana, si hay patrón poblar el componente con contenido de get_page_content, verificar responsive (chequeo automatizado de overflow en 5 viewports: 320/375/768/1024/1920px), verificar con npm run build real antes de dar por terminado. Para actualizaciones de contenido ya migrado, saltar el relevamiento de layout y usar get_site_map + get_page_content para sync incremental comparando modified date."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Migrate a new page that matches a known layout pattern (Priority: P1) 🎯 MVP

Someone running a WordPress-to-Astro migration wants a specific source
page turned into a working, populated Astro component — without hand
writing markup for a layout the project has already solved before.

**Why this priority**: This is the core value of the whole skill —
turning a source page into a verified, shippable Astro component with no
manual coding. Every other capability exists to make this safe (the
no-match branch) or efficient (content-only sync).

**Independent Test**: Point the skill at a source page whose layout
matches an existing entry in the project's manifest, run it, and confirm
the resulting component contains that page's content, passes the
responsive check at all five viewports, and the project builds
successfully with that page present in the output.

**Acceptance Scenarios**:

1. **Given** a source page not yet migrated, **When** the skill runs on
   it, **Then** it first retrieves that page's actual rendered layout
   before making any decision about which component pattern applies.
2. **Given** a relevaded page whose layout matches an existing pattern in
   the project's manifest, **When** the skill classifies it, **Then** it
   populates that pattern's component with the page's text, custom
   fields, and images sourced from the site.
3. **Given** a populated component, **When** the skill verifies it,
   **Then** it checks for horizontal overflow at each of five specified
   viewport widths and runs a real project build, and only reports the
   page as migrated if both checks pass.
4. **Given** either the responsive check or the build fails, **When** the
   skill finishes verifying, **Then** it does not report that page as
   migrated, and reports exactly what failed.

---

### User Story 2 - Flag a new page with no matching layout pattern (Priority: P1)

Someone running a migration needs to know when a source page's layout
doesn't match anything the project has solved before, so a human can
decide how to handle it — instead of the skill silently forcing an
incorrect layout or getting stuck.

**Why this priority**: This is the other half of every classification
decision in User Story 1 — without it, the skill has no safe behavior for
the pages that don't fit a known pattern, which is a normal and expected
outcome, not an edge case.

**Independent Test**: Point the skill at a source page whose relevaded
layout does not match any entry in the project's manifest, run it, and
confirm it is reported as flagged for human decision, with no Astro
component created or forced for it.

**Acceptance Scenarios**:

1. **Given** a relevaded page whose layout matches no entry in the
   project's manifest, **When** the skill classifies it, **Then** it
   flags that page for human decision and does not create or force any
   component for it.
2. **Given** a page has been flagged, **When** the skill is processing
   other pages in the same run, **Then** it continues processing them —
   one flagged page does not halt the rest of the run.
3. **Given** the skill's run has finished, **When** its report is
   reviewed, **Then** every flagged page is listed clearly, distinct from
   pages that were successfully migrated.

---

### User Story 3 - Sync content for an already-migrated page (Priority: P2)

Someone maintaining a site that's already been migrated wants to pull in
content edits made back on the WordPress site — without repeating the
layout work that's already done and verified.

**Why this priority**: This is an ongoing-maintenance capability that
only matters once at least one page has already been migrated via User
Story 1; it's valuable but not needed for a project's first migration run.

**Independent Test**: Edit the content of an already-migrated source page,
run the skill's sync, and confirm only that page's component content is
updated — its assigned layout pattern is untouched, and no layout
relevamiento occurs.

**Acceptance Scenarios**:

1. **Given** a page already has an assigned pattern in the project's
   manifest, **When** the skill syncs it, **Then** it does not perform
   layout relevamiento for that page.
2. **Given** the full list of site content and each item's last-modified
   date, **When** the skill syncs, **Then** it updates only the
   already-migrated pages whose last-modified date changed since their
   last sync.
3. **Given** an already-migrated page whose content has not changed since
   its last sync, **When** the skill syncs, **Then** that page is left
   untouched.
4. **Given** a page's content is updated via sync, **When** the update
   completes, **Then** that page's assigned component pattern is
   unchanged — only its content and media were updated.

---

### Edge Cases

- What happens when the project has no manifest yet (first migration run
  on a new project)? Every page is treated as unmatched and flagged for
  human decision — the skill never invents an initial set of patterns on
  its own.
- What happens when a human resolves a flagged page by defining a new
  pattern for it? A subsequent run picks it up like any other matched
  page — the skill does not need a separate "retry" mechanism.
- What happens when retrieving a page's layout, content, or media fails
  (e.g. the source site is unreachable)? The skill stops processing that
  page, reports the failure clearly, and continues with any other pages
  in the run rather than guessing at missing data.
- What happens when a page matches a pattern but references an image that
  can't be resolved to an original file? The skill reports that
  specifically rather than silently omitting the image or migrating with
  a broken reference.
- What happens when the responsive check passes at four of five viewports
  but fails at one? The page is still not reported as migrated — any
  single failing viewport blocks completion.
- What happens when a content-only sync is run on a page that was never
  migrated (no assigned pattern)? It is treated as a new page (User Story
  1/2's flow), not a sync target.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: For any source page not yet migrated, the skill MUST
  retrieve that page's actual rendered layout before deciding how to
  handle it.
- **FR-002**: The skill MUST classify a relevaded page against the
  project's manifest of known page→component-pattern mappings to
  determine whether an existing pattern applies.
- **FR-003**: When no known pattern matches a page, the skill MUST flag
  that page for human decision and MUST NOT create, generate, or force a
  component for it.
- **FR-004**: When a known pattern matches a page, the skill MUST
  populate that pattern's component with the page's content (text and
  any exposed custom fields) and media (original-resolution images)
  sourced from the site.
- **FR-005**: Before considering any page's migration or content update
  complete, the skill MUST verify the resulting component has no
  horizontal overflow at each of five specified viewport widths: 320,
  375, 768, 1024, and 1920 pixels.
- **FR-006**: If the responsive check fails at any of the five viewports,
  the skill MUST NOT report that page as migrated/updated, and MUST
  report which viewport(s) failed.
- **FR-007**: Before considering any page's migration or content update
  complete, the skill MUST verify a real, successful build of the target
  project with that page's component included in the build output.
- **FR-008**: If the build fails, the skill MUST NOT report that page as
  migrated/updated, and MUST report the build failure.
- **FR-009**: For a page that already has an assigned pattern in the
  manifest, the skill MUST support updating its content without
  performing layout relevamiento again.
- **FR-010**: The content-only sync path MUST determine which
  already-migrated pages changed by comparing each page's current
  last-modified date against the date recorded at its last sync, and
  MUST leave unchanged pages untouched.
- **FR-011**: The content-only sync path MUST NOT alter a page's assigned
  component pattern — it updates only that pattern's content and media.
- **FR-012**: The skill MUST NOT add a new pattern to the project's
  manifest on its own initiative — new pattern assignments require
  explicit human decision.
- **FR-013**: The skill MUST NOT read, request, or rely on Elementor's
  internal layout data at any point — all layout information MUST come
  only from a page's rendered structure.
- **FR-014**: A page being flagged for human decision MUST NOT halt
  processing of other pages in the same run.
- **FR-015**: At the end of any run, the skill MUST report, per page it
  processed: what changed, whether the responsive check passed, whether
  the build check passed, and whether it was flagged for human decision.

### Key Entities *(include if feature involves data)*

- **Manifest entry**: A project-specific mapping from a source page to a
  known component pattern (and the Astro file it corresponds to).
  Project-specific configuration, never generated by the skill itself.
- **Layout relevamiento**: The rendered-structure snapshot retrieved for
  a page not yet classified against the manifest.
- **Flagged page**: A page whose layout matched no manifest entry,
  awaiting an explicit human decision before any component is created for
  it.
- **Sync record**: The last-synced last-modified date for an
  already-migrated page, used to detect which pages changed since the
  previous sync.
- **Verification result**: The pass/fail outcome of the responsive check
  (per viewport) and the build check for a migrated or updated page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A page whose layout matches an existing pattern can be
  migrated — content populated, responsive-verified, and build-verified —
  in a single run, with no manual code edits.
- **SC-002**: 100% of pages whose layout matches no known pattern are
  flagged for human review rather than migrated with an incorrect or
  forced layout.
- **SC-003**: No page is ever reported as migration/update complete while
  failing the responsive check at any of the five specified viewports.
- **SC-004**: No page is ever reported as migration/update complete while
  the project fails to build.
- **SC-005**: A content-only sync run touches only the already-migrated
  pages whose content changed since their last sync — unchanged pages
  produce no modifications.
- **SC-006**: From a single run's report alone, a human can identify
  exactly which pages changed, which passed verification, and which need
  a decision, without inspecting any code.

## Assumptions

- The companion WordPress plugin (`specs/001-wp-rest-normalizer`) and MCP
  tools server (`specs/002-wp-mcp-tools`) are already available and
  configured against the source site; this skill is their consumer, not a
  replacement for either.
- The target Astro project already has a working build command that
  produces a build output directory; the skill runs and inspects the
  result of that existing command rather than defining a new build
  process.
- The skill is responsible for performing the automated responsive
  overflow check itself (there is no other existing capability in this
  project that provides it); the build check, by contrast, is delegated
  to the target project's own existing build command.
- A run may target a single specified page or the full set of pages
  discoverable on the site; per-page flagging, verification, and
  reporting behave the same either way.
- "Human decision" on a flagged page happens through normal conversation
  with whoever is operating the skill — no separate ticketing or approval
  system is assumed.
- Automatic remediation of a failed responsive or build check is out of
  scope — a failure is reported, not auto-fixed, consistent with the
  skill's role as a mechanical migration procedure, not a general-purpose
  code-fixing agent.
