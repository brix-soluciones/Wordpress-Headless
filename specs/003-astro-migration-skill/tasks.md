---

description: "Task list template for feature implementation"
---

# Tasks: WordPress-to-Astro Migration Skill

**Input**: Design documents from `/specs/003-astro-migration-skill/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Requested by design — `research.md` #9 commits to a small
`@playwright/test` fixture suite for `check-responsive.mjs` (the one
piece of real code this feature adds), in addition to the manual
`quickstart.md` validation against the real `astro-site` project and
WordPress site (the `SKILL.md` procedure itself isn't unit-testable the
way code is).

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Per `plan.md`'s Project Structure: `skill/SKILL.md` (the procedure) and,
under the pre-existing `astro-site/` project,
`astro-site/scripts/check-responsive.mjs` (new code) and
`astro-site/tests/check-responsive.spec.mjs` (new tests).
`astro-site/manifest.json` is created/updated at runtime by following
`SKILL.md`'s instructions — it is not a file this feature's tasks write
directly, except as example fixtures during manual validation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Skeleton files exist; nothing wired yet

- [X] T001 Create `skill/SKILL.md` with frontmatter (`name`, `description`,
      an `argument-hint` covering the optional single-page argument —
      research.md #8) and top-level section headers for the flow
      (preamble, classify, populate, verify, report, sync path); no flow
      content yet. **Result**: frontmatter shape follows this repo's own
      `.claude/skills/*/SKILL.md` examples (`name`, `description`,
      `argument-hint`, `user-invocable`, `disable-model-invocation`) —
      the only real precedent available in-repo; each section is an HTML
      comment + `_Placeholder — T0NN._` marker naming exactly which task
      fills it in, so later tasks can target one section without
      touching the others.
- [X] T002 [P] Create `astro-site/scripts/check-responsive.mjs` as an
      empty file (no logic yet). **Result**: header comment only (usage +
      contract reference), no logic — matches 001's "skeleton, no logic"
      precedent.
- [X] T003 [P] Create `astro-site/tests/check-responsive.spec.mjs` as an
      empty file (no logic yet). **Result**: header comment only.
- [X] T004 [P] Confirm `@playwright/test`'s browser binary is installed
      for `astro-site/` (`npx playwright install chromium` from within
      `astro-site/`, if not already present) — one-time environment
      setup, not code. **Result**: `chromium-1234` already present under
      `%LOCALAPPDATA%\ms-playwright`; verified beyond just "installed" by
      actually launching it and rendering a page from within
      `astro-site/` (`chromium.launch()` → `setContent` → `textContent`
      round-trip succeeded).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared script, its tests, and the shared `SKILL.md`
sections every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `astro-site/scripts/check-responsive.mjs` per
      `contracts/check-responsive-cli.md`: parse `<preview-base-url>` and
      one-or-more `<path>` args, launch Playwright, for each path set the
      viewport to each of the five widths (320/375/768/1024/1920, fixed
      height) and evaluate `document.documentElement.scrollWidth >
      document.documentElement.clientWidth` (research.md #3), print the
      `{ "results": { "<path>": { "<width>": bool, ... } } }` JSON to
      stdout, exit non-zero with a stderr message only on a genuine
      script failure (unreachable preview server, non-2xx path) — never
      on an individual page failing its own overflow check (depends on T002).
      **Result**: core logic split into two exported functions
      (`measureOverflowAcrossViewports`, `checkPath`) plus a guarded
      `main()` CLI entrypoint, so T006 can test the logic directly without
      spawning a subprocess. **Bug found and fixed during smoke-testing**:
      the initial `import.meta.url === file://${process.argv[1]}`
      direct-execution check silently failed on Windows (real
      `file://` URLs have three slashes before the drive letter,
      `file:///C:/...`, not two) — `main()` never ran, exit 0, no output,
      no error. Fixed with Node's `pathToFileURL()` instead of hand-built
      string comparison. Verified via a local static HTTP server (success
      case → correct JSON + exit 0; missing args → usage + exit 1; 404
      path → error message + exit 1) — **run via PowerShell**, not Git
      Bash: Git Bash's MSYS path-conversion rewrites arguments starting
      with `/` (e.g. `/wide/`) into Windows paths before they reach node,
      breaking navigation. Documented in `SKILL.md`'s Verificar section.
- [X] T006 [P] Write `astro-site/tests/check-responsive.spec.mjs`
      (research.md #9): a local static fixture page with an element
      deliberately wider than its container at one viewport width
      (expect that width's result `false`), and a clean fixture page
      (expect all five widths `true`) (depends on T003, T005). **Result**:
      5/5 passing (`npx playwright test tests/check-responsive.spec.mjs`)
      — the two fixture cases above, an "always exactly five keys"
      shape check, and two `checkPath`-level cases (success via
      `page.route` fulfill, non-2xx throws) using Playwright's route
      interception instead of a real server.
- [X] T007 Write `SKILL.md`'s shared preamble (depends on T001): the
      constraint that all WordPress data comes only through
      `get_site_map`/`get_page_content`/`get_rendered_structure`/
      `get_media_original` — never a direct HTTP call (research.md #6);
      how the optional single-page argument selects single-page vs
      whole-site-via-`get_site_map` mode (research.md #8); and the
      `astro-site/manifest.json` read/parse instructions per
      `contracts/manifest-schema.md` — treat a missing file as
      `{ "pages": [] }`, stop and report on malformed JSON, never guess.
      **Result**: replaces the `## Preámbulo` placeholder only; all other
      sections untouched.
- [X] T008 Write `SKILL.md`'s shared verification sub-procedure (depends
      on T001, T005): run the project's build, start `astro preview`
      against that build's output, invoke `check-responsive.mjs`
      (`contracts/check-responsive-cli.md`) against the preview server
      for the page(s) being verified, and combine its per-viewport result
      with the build's pass/fail into one `VerificationResult`
      (`data-model.md`) per page — referenced (not repeated) by both the
      new-page flow (US1) and the sync flow (US3), since FR-005 applies
      to content updates too, not just new migrations. **Result**:
      replaces the `## Verificar (responsive + build)` placeholder only;
      includes the PowerShell-not-Git-Bash invocation note from T005's
      finding. `## Reportar` and the other remaining placeholders are
      untouched — filling them is US1/US2/US3 work (T011, T014, T016–T018),
      not Foundational.

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Migrate a new page that matches a known layout pattern (Priority: P1) 🎯 MVP

**Goal**: A page whose relevaded layout matches an existing manifest
pattern gets its component populated with real content/media, and is
only reported migrated once it passes both the responsive check and a
real build (FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-008)

**Independent Test**: Point the skill at a source page whose layout
matches an existing manifest entry, run it, and confirm `quickstart.md`
scenario 1 — and scenario 3's failure path — both hold.

### Implementation for User Story 1

- [X] T009 [US1] Write `SKILL.md`'s relevar-and-classify(match) section
      (depends on T007): for a page with no manifest entry, call
      `get_rendered_structure` before any classification decision
      (FR-001), and check its layout against the manifest's known
      `pattern` values (FR-002). **Result**: split into "Relevar y buscar
      en el manifest" (this task) and "Página sin patrón conocido"
      (placeholder, T013). **Design clarification made explicit in the
      text**: matching in this MVP is a pure manifest lookup by
      `wp_slug` — the relevaded structure is evidence for the report/human
      decision, not input to an auto-classifier (nothing in spec.md/
      data-model.md describes a layout-signature-matching algorithm;
      manifest entries are already per-specific-page per their documented
      shape). Flagged this reading to the user for confirmation.
- [X] T010 [US1] Write `SKILL.md`'s populate section (depends on T009):
      when a pattern matches, populate that pattern's component with the
      page's content and custom fields via `get_page_content` and its
      images via `get_media_original` (FR-004). **Result**: worked
      example using an illustrative `PatternMVP` component (named per
      user request), with an explicit "touches only `astro_file`'s
      props, never the pattern component file itself" boundary
      (Article III/V). Includes an image-slug-derivation heuristic
      (strip extension + WordPress's `-{width}x{height}` size suffix)
      added after the T012 dry-run surfaced it as underspecified.
- [X] T011 [US1] Write `SKILL.md`'s completion-gating section for this
      flow (depends on T008, T010): invoke the shared verification
      sub-procedure and report the page as migrated only when both the
      responsive check (all five viewports) and the build pass (FR-006,
      FR-008); on failure, report exactly what failed instead. **Result**:
      added as `### Páginas migradas o actualizadas` under `## Reportar`,
      explicitly invoking the Verificar sub-procedure per the user's
      request; `### Páginas flaggeadas` left as a T014 placeholder
      alongside it.
- [ ] T012 [US1] Run `quickstart.md` scenarios 1 and 3 (matching pattern;
      deliberately failing verification) against the real `astro-site`
      project and a real WordPress site, and confirm all expected
      outcomes. **Partially done, real WordPress site not available in
      this environment** (same limitation as 001/002's real-instance
      tasks). What was actually verified for real: the entire "Verificar"
      sub-procedure (`npm run build` → `astro preview` →
      `check-responsive.mjs`) run against the real, unmodified
      `astro-site` project end-to-end — build succeeded, preview served
      `dist/`, script reported `{"/":{"320":true,...,"1920":true}}`,
      exit 0. What was validated by manual prose trace instead of
      execution (no live WP): Preámbulo → Clasificar(match) → Poblar →
      Verificar → Reportar(success) chain for a hypothetical already-
      matched page. **The trace surfaced a blocking cross-feature gap,
      reported to the user, not yet resolved**: `get_page_content`
      requires a numeric `id` (`specs/002-wp-mcp-tools/contracts/
      get_page_content.md`), but nothing in the pipeline currently
      supplies one — `get_site_map`'s `SiteMapEntry` has only
      `url`/`type`/`modified` (no `id`), and `get_page_content` has no
      slug-based lookup alternative. As drafted, US1's Poblar componente
      step 1 cannot actually execute. Proposed fix (not applied,
      pending confirmation): add `id` to `SiteMapEntry` in
      `specs/001-wp-rest-normalizer` (trivial — `WP_Query` already has
      `$post->ID`), and route single-page-argument mode through
      `get_site_map` too (filtering to the one matching entry) so both
      invocation modes get `id` the same way — requires also amending
      `SKILL.md`'s Preámbulo (outside this task's file-section scope) and
      touching an already-completed prior feature, so this is
      deliberately left for the user to decide before proceeding, not
      silently patched.

**Checkpoint**: User Story 1 is fully functional and testable independently (MVP)

---

## Phase 4: User Story 2 - Flag a new page with no matching layout pattern (Priority: P1)

**Goal**: A page whose relevaded layout matches nothing in the manifest
is flagged for human decision, with no component created or forced, and
without blocking the rest of a batch run (FR-003, FR-012, FR-014, FR-015)

**Independent Test**: Point the skill at a source page whose layout
matches no manifest entry, run it, and confirm `quickstart.md` scenario
2 — including that another page in the same run still completes normally.

### Implementation for User Story 2

- [X] T013 [US2] Write `SKILL.md`'s classify(no-match) section (depends
      on T009): when no manifest pattern matches, flag the page for human
      decision and explicitly do not create, generate, or force any
      component for it (FR-003, FR-012). **Result**: replaces
      `### Página sin patrón conocido`'s placeholder. Registers
      `wp_slug`/`url`/the already-fetched relevamiento outline/a reason
      (`"no manifest entry"` vs `"invalid manifest entry"`) for the
      report, never invents a `pattern`/`astro_file`, and explicitly
      continues the run instead of halting (FR-014) — actually reporting
      is deferred to `### Páginas flaggeadas` (T014), not done inline here.
- [X] T014 [US2] Write `SKILL.md`'s batch-continuation-and-reporting
      section (depends on T013): flagging a page does not halt processing
      of other pages in the same run (FR-014); the end-of-run report
      lists flagged pages distinctly from migrated/updated ones (FR-015).
      **Result**: replaces `### Páginas flaggeadas`'s placeholder under
      `## Reportar`. Always a separate list from
      `### Páginas migradas o actualizadas`; per-page reason + outline
      summary; explicit "no pages flagged" happy-path note.
- [X] T015 [US2] Run `quickstart.md` scenario 2 against the real
      `astro-site` project and a real WordPress site, and confirm all
      expected outcomes. **Not run against a real site** (same
      environment limitation as T012/T011/etc. across all three
      features). **Prose dry-run instead**: traced a 3-page batch (no
      argument, whole-site mode) — one page ("branding") with a manifest
      entry (`last_synced_modified: null`), two ("old-services", "about")
      with none. Preámbulo routes all three to *Clasificar página
      nueva* (none have `last_synced_modified` set, so none go to
      *Sync de contenido*); "branding" matches → *Poblar componente*;
      the other two don't match → *Página sin patrón conocido*, both
      flagged with reason `"no manifest entry"`, and — critically —
      "old-services" being flagged does not stop "about" from also being
      evaluated (FR-014 confirmed by the trace, not just asserted).
      Also traced the "invalid manifest entry" path (entry present but
      missing `astro_file`) → correctly still routes through Clasificar
      to the flag branch. Report ends with "branding" under *Páginas
      migradas* and the other two under *Páginas flaggeadas*, never
      mixed (FR-015). **No inconsistencies found** — unlike T012's
      dry-run, which surfaced the `id`-resolution gap (see T010b in
      `specs/001-wp-rest-normalizer/tasks.md`, now fixed), this trace
      composed cleanly end to end.

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Sync content for an already-migrated page (Priority: P2)

**Goal**: A page that already has a manifest entry gets its content
synced from WordPress edits without repeating layout relevamiento,
touching only pages whose `modified` date changed, and never altering
its assigned pattern (FR-009, FR-010, FR-011, FR-005 applied to updates)

**Independent Test**: Edit an already-migrated source page's content, run
the skill's sync path, and confirm `quickstart.md` scenario 4 — only that
page's content changes, its pattern is untouched, and a second immediate
sync run makes no further changes.

### Implementation for User Story 3

- [X] T016 [US3] Write `SKILL.md`'s sync-detection section (depends on
      T007): for pages that already have a manifest entry, call
      `get_site_map` and compare each entry's current `modified` date
      against that manifest entry's `last_synced_modified`, skipping
      layout relevamiction entirely for this flow (FR-009, FR-010);
      pages whose date hasn't changed are left untouched. **Result**:
      replaces `## Sync de contenido`'s placeholder (`### Detectar
      cambios` subsection). Comparison is exact-string equality, not
      datetime parsing — justified inline: `last_synced_modified` is
      always stored as a literal copy of the `modified` string that
      motivated the sync (never reformatted), so equality is sufficient
      and avoids a datetime-parsing dependency. Unchanged pages are
      fully skipped (no `get_page_content`, no `Verificar`, absent from
      both `Reportar` lists) — noted that the run's summary can still
      report a plain count of unchanged pages without needing a new
      `Reportar` subsection.
- [X] T017 [US3] Write `SKILL.md`'s sync-update section (depends on T008,
      T016): for each changed page, update its component's content/media
      via `get_page_content`/`get_media_original` without altering its
      `pattern` or `astro_file` (FR-011), then invoke the shared
      verification sub-procedure (T008) — FR-005's responsive/build gate
      applies to content updates, not only new migrations. **Result**:
      `### Actualizar contenido` subsection — explicitly invokes *Poblar
      componente* rather than duplicating its steps (same DRY pattern as
      *Verificar*), then adds sync's own extra restriction (never
      reassign `pattern`/`astro_file` in the manifest entry — a
      superset of Poblar componente's existing "never touch the pattern
      component file" rule), then invokes *Verificar*.
- [X] T018 [US3] Write `SKILL.md`'s sync-completion section (depends on
      T017): on a successful update, write that entry's new
      `last_synced_modified` to `astro-site/manifest.json`
      (`contracts/manifest-schema.md`). **Result**: `### Persistir el
      sync` subsection — only updates `last_synced_modified` (copied
      verbatim from the `modified` that triggered the sync) when
      `complete` is `true`; on failure, explicitly leaves it stale so
      the next run retries automatically, and reports via the existing
      *Reportar → Páginas migradas o actualizadas* (already generic
      enough from T011 to cover "actualizada" — confirmed no `Reportar`
      edit was actually needed here, correcting the user's premise that
      one remained).
- [X] T019 [US3] Run `quickstart.md` scenario 4 against the real
      `astro-site` project and a real WordPress site, including
      confirming a second immediate sync run makes no further changes,
      and confirm all expected outcomes. **Not run against a real site**
      (same limitation as every other real-instance task across all
      three features). **Prose dry-run instead**: traced a 2-page batch
      — "branding" (`modified` changed since its `last_synced_modified`)
      and "about" (`modified` identical to its `last_synced_modified`).
      "branding": Preámbulo routes to Sync (id resolved there) →
      Detectar cambios (strings differ) → Actualizar contenido (Poblar
      componente with that id, pattern/astro_file untouched) → Verificar
      → Persistir (`last_synced_modified` overwritten with the new
      `modified`, verbatim) → reported as actualizada. "about": Detectar
      cambios (strings equal) → skipped entirely, no tool calls, no
      report entry either way. Also traced the edge case of an
      *invalid* manifest entry that happens to have
      `last_synced_modified` set — correctly still routes through
      Preámbulo to *Clasificar página nueva*, not *Sync de contenido*
      (Sync requires a *valid* entry). **No inconsistencies found.**

**Checkpoint**: All three user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification that spans all three stories

- [X] T020 [P] Run `quickstart.md` scenario 5 (missing
      `astro-site/manifest.json`) and confirm the skill treats it as
      `{ "pages": [] }` rather than raising an error
      (contracts/manifest-schema.md). **Result**: confirmed
      `astro-site/manifest.json` does not currently exist in the repo —
      the real starting state already matches this edge case, and
      Preámbulo point 2 states the required behavior unambiguously
      (treat as `{ "pages": [] }`, not an error).
- [X] T021 [P] Verify constitution Article I across the whole feature:
      search `skill/` and `astro-site/scripts/`, `astro-site/tests/` for
      `_elementor_data` and confirm zero matches. **Result**: one match,
      in `SKILL.md`'s own prose stating the field is never read — zero
      matches in any instruction/logic.
- [X] T022 [P] Verify FR-012: review `SKILL.md` end to end and confirm no
      instruction ever assigns/fabricates a `pattern` value that isn't
      already present in `astro-site/manifest.json` from a prior human
      decision. **Result**: every `pattern` reference in the document is
      either reading it from an existing entry, reporting it, or
      explicitly forbidding the skill from writing/reassigning it — none
      assign a new value.
- [X] T023 [P] Update `skill/README.md` to reflect the as-built flow —
      cross-reference `SKILL.md`, and note that `manifest.json` now lives
      under `astro-site/`, not `skill/` (plan.md's Structure Decision).
      **Result**: rewritten as a short pointer doc (`SKILL.md` is now the
      declared source of truth), flow summary updated to match the
      as-built 3-way Preámbulo routing, `manifest.json` example updated
      with `last_synced_modified` and its `astro-site/` location.
- [X] T024 [P] Run the full `astro-site` test suite
      (`cd astro-site && npx playwright test`) and confirm
      `check-responsive.spec.mjs` passes alongside anything else already
      there. **Result**: 5/5 passing — no other test files exist in
      `astro-site/` yet, so this suite is currently the whole thing.
      Re-run after the terminology/formatting polish pass (below) to
      confirm it touched no logic: still 5/5.

**Polish pass (style/terminology, logic unchanged)**: standardized
cross-section references in `SKILL.md` to a single consistent style
(italic short name, e.g. `*Verificar*`, `*Poblar componente*` — three
spots previously used bold with an inconsistent long/short mix) and
fixed one hyphenation inconsistency (`"modo sitio-completo"` → `"modo
sitio completo"`, matching the first/defining usage). No procedural,
verification, or routing text changed — confirmed via the T024 re-run
above (5/5 unchanged) and a full manual re-read of the document.
Also updated the file's own header comment (previously said "each
section is a placeholder" — no longer true) to point future editors at
this tasks.md and note that `Verificar`/`Poblar componente` are
intentionally shared sub-procedures invoked from multiple places, not
duplicated — don't fork them when editing later.

**Checkpoint**: Feature complete — `specs/003-astro-migration-skill` (24/24
tasks). `skill/SKILL.md` is fully assembled: zero placeholders, three
prose dry-runs (T012, T015, T019) traced every routing path with no
inconsistencies found (after fixing the `id`-resolution gap via
`specs/001-wp-rest-normalizer`'s T010b and a `last_synced_modified`
routing bug caught before it shipped), and the one real piece of code
(`astro-site/scripts/check-responsive.mjs`) is implemented, tested
(5/5), and was exercised end-to-end for real against the live
`astro-site` project (T012). What remains unverified is execution
against a real WordPress site — consistent with every other
real-instance task across all three features in this repo, none of
which had one available in this environment.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
  - US1 and US2 both build on the same `SKILL.md` classify section
    (T009), so US2's first task (T013) depends on T009 completing —
    these two stories are not fully independent of each other the way
    001/002's stories were, since "match" and "no-match" are the two
    branches of one classification step. US3 is independent of both
    (different section of `SKILL.md`, only sharing Foundational's T007/T008).
  - Both US1 (T011) and US3 (T017) depend on Foundational's shared
    verification sub-procedure (T008) — implemented once, invoked twice.
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational only — independently
  shippable as the MVP
- **User Story 2 (P1)**: Its first task (T013) depends on US1's T009
  (the shared classify step); otherwise independent of US1's populate/
  verify tasks (T010, T011)
- **User Story 3 (P2)**: Depends on Foundational only (T007, T008) — no
  dependency on US1/US2's tasks, though it reuses the same shared
  verification sub-procedure US1 also invokes

### Within Each User Story

- Tests (T006) precede the code they verify only in the Foundational
  phase, where the one piece of real code (`check-responsive.mjs`) lives
  — the user-story phases themselves are all `SKILL.md` sections (no
  additional automated tests requested for those; `quickstart.md` is
  their verification, per the Tests note above)
- Within each story, section-writing tasks precede that story's
  `quickstart.md` validation task

### Parallel Opportunities

- T002, T003, T004 (Setup) — different files/one-time setup, run in parallel
- T006 can be written in parallel with T007/T008 once T005 exists
  (different files: test file vs `SKILL.md`)
- T020–T024 (Polish) — independent checks, run in parallel

---

## Parallel Example: Setup

```bash
Task: "Create astro-site/scripts/check-responsive.mjs as an empty file"
Task: "Create astro-site/tests/check-responsive.spec.mjs as an empty file"
Task: "Confirm @playwright/test's browser binary is installed for astro-site/"
```

## Parallel Example: User Stories (after Foundational)

```bash
Task: "Implement User Story 1 (T009-T012) in skill/SKILL.md"
Task: "Implement User Story 3 (T016-T019) in skill/SKILL.md"
# User Story 2 (T013-T015) starts once US1's T009 (shared classify step) lands
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (script + shared `SKILL.md` sections)
3. Complete Phase 3: User Story 1 (matching-pattern migration)
4. **STOP and VALIDATE**: Run `quickstart.md` scenarios 1 and 3
5. Deploy/demo if ready — note User Story 2's classify(no-match) branch
   (T013) technically depends on T009 from this phase, so in practice
   User Story 2 tends to land alongside User Story 1, not strictly after

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → MVP
3. Add User Story 2 (shares US1's classify step) → validate independently
4. Add User Story 3 → validate independently
5. Polish: run `quickstart.md` scenario 5 plus the full `astro-site` test suite

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Once Foundational is done: Developer A takes US1 (which also unblocks
   US2's flag branch), Developer B takes US3 — both edit `SKILL.md`, so
   coordinate on section boundaries rather than working fully in parallel
   on the same file
3. Stories complete and validate independently, then Polish runs against
   the combined result

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Unlike 001/002, most of this feature's "implementation" is `SKILL.md`
  prose (a single shared file), so story independence is weaker than
  usual — dependencies above call out exactly where stories share that
  file's sections
- Automated tests cover only `check-responsive.mjs` (the one piece of
  real code); `quickstart.md` is the verification method for the skill's
  procedure itself
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
