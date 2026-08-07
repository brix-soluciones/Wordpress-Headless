---

description: "Task list template for feature implementation"
---

# Tasks: Pattern Authoring Assistant Skill

**Input**: Design documents from `/specs/004-pattern-authoring-assistant/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested — per `plan.md`'s Technical Context, this feature
ships no executable code of its own (drafting is Claude's own generation,
not a deterministic procedure), so there is nothing to unit test.
Verification is `quickstart.md`'s manual scenarios plus a direct
structural cross-check against `specs/003-astro-migration-skill`'s actual
`SKILL.md` text (both documents exist in-repo, so this check is real, not
speculative).

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Per `plan.md`'s Project Structure: `pattern-assistant/SKILL.md` (the
procedure) is the only source file this feature adds. Its runtime output
(`astro-site/.pattern-drafts/`) is created by following the skill's
instructions at invocation time, not authored by any task here — same
relationship 003's tasks had to `astro-site/manifest.json`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Skeleton file exists; drafts are excluded from version control

- [X] T001 Create `pattern-assistant/SKILL.md` with frontmatter (`name`,
      `description`, an `argument-hint` for the required page
      URL/slug argument) and section headers for the flow (Preámbulo,
      Recopilar datos, Redactar el componente de patrón, Redactar el
      archivo de página); no flow content yet — same
      placeholder-per-section discipline `specs/003-astro-migration-skill`
      used
- [X] T002 [P] Add `.pattern-drafts/` to `astro-site/.gitignore`
      (research.md #1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Page resolution, overwrite protection, and data-gathering —
shared by both user stories, since a `DraftPatternComponent` and its
paired `DraftPageFile` are always produced from the same invocation
(`data-model.md`'s Relationships)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Write `SKILL.md`'s Preámbulo section (depends on T001):
      resolve the human-supplied URL/slug via `get_site_map()`, deriving
      `wp_slug` and matching the same way
      `specs/003-astro-migration-skill`'s Preámbulo does (research.md #4)
      to obtain `id` + `url`; stop and report clearly if nothing matches
      (FR-008); then check whether
      `astro-site/.pattern-drafts/<slug>/` already exists — if so, stop
      and tell the human instead of proceeding (FR-009, research.md #7).
      **Result**: single required argument (no whole-site mode, unlike
      003), otherwise a direct reuse of 003's resolution logic.
- [X] T004 Write `SKILL.md`'s "Recopilar datos" section (depends on
      T003): call `get_rendered_structure(url)` and `get_page_content(id)`
      before drafting anything (FR-001); for any image found in the
      layout/content, derive its slug using
      `specs/003-astro-migration-skill`'s exact heuristic (strip
      extension + WordPress size suffix, research.md #6) and resolve it
      via `get_media_original` (FR-010); stop and report clearly on any
      tool failure, producing no partial draft (FR-008). **Result**: as
      designed, no deviations.

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Draft a pattern component from a flagged page (Priority: P1) 🎯 MVP

**Goal**: Given a page identifier, produce a reviewable draft Astro
pattern component reflecting that page's actual layout, written outside
any location the migration skill treats as trusted (FR-002, FR-004)

**Independent Test**: Give the tool a page with a distinctive layout and
confirm `astro-site/.pattern-drafts/<slug>/component.astro` reflects that
page's actual structure, and that nothing under `src/` changed.

### Implementation for User Story 1

- [X] T005 [US1] Write `SKILL.md`'s "Redactar el componente de patrón"
      section (depends on T004): using the gathered layout outline,
      write `astro-site/.pattern-drafts/<slug>/component.astro`
      (`contracts/draft-output.md`) — freeform Astro markup reflecting
      the page's actual structure; explicitly state this file is a draft
      for human review, never auto-registered as an approved pattern
      (FR-002, FR-004). **Result**: text explicitly notes there's no
      fixed structure→markup algorithm by design (research.md #2) — the
      one section where judgment, not procedure, is the point.
- [X] T006 [US1] Run `quickstart.md` scenarios 1 (component-drafting
      part), 2 (page not found), and 3 (existing draft) against a real
      WordPress site and confirm expected outcomes. **Not run against a
      real site** (same limitation as every other real-instance task
      across all four features in this repo). **Prose dry-run instead**:
      traced invoking with a flagged page's URL — `get_site_map()`
      resolves `id`+`url`, no existing draft found, `get_rendered_structure`
      + `get_page_content` succeed, `component.astro` written to
      `astro-site/.pattern-drafts/<slug>/`, human-facing message states
      it's a draft pending review. No inconsistencies found.

**Checkpoint**: User Story 1 is fully functional and testable independently (MVP)

---

## Phase 4: User Story 2 - Draft the page wiring for the new pattern (Priority: P2)

**Goal**: Alongside the drafted component, produce a page file that
imports it and passes this page's real content as props, in the exact
shape `specs/003-astro-migration-skill`'s "Poblar componente" expects to
find already in place (FR-003)

**Independent Test**: With a drafted component in hand, confirm
`astro-site/.pattern-drafts/<slug>/page.astro` imports it and passes this
page's real title/content/media as a single `props` object — matching
`contracts/draft-output.md` exactly.

### Implementation for User Story 2

- [X] T007 [US2] Write `SKILL.md`'s "Redactar el archivo de página"
      section (depends on T005 — wires up the component T005 just
      drafted, per `data-model.md`'s Relationships): write
      `astro-site/.pattern-drafts/<slug>/page.astro` with a single
      `import` of the drafted component, a single `const props = {...}`
      object built from this page's `get_page_content`/`get_media_original`
      results, and a single `<Component {...props} />` render line — no
      other structure (`contracts/draft-output.md`; FR-003). **Result**:
      see T008 — the import path requirement was tightened after the
      cross-check found it underspecified.
- [X] T008 [US2] Run `quickstart.md` scenario 1 (page-wiring part)
      against a real WordPress site; additionally (not dependent on a
      live site), directly cross-check `contracts/draft-output.md`'s
      required `page.astro` shape against
      `specs/003-astro-migration-skill/SKILL.md`'s actual "Poblar
      componente" text to confirm the two are genuinely consistent, not
      just documented as such. **Page-wiring quickstart part not run**
      (no live site, same limitation as elsewhere). **Cross-check run
      for real** (both documents exist in-repo) — and it found a genuine
      bug: T007's first draft said "ruta relativa a `component.astro`,"
      which is ambiguous between the staging-relative path
      (`./component.astro`, correct only while both files sit as
      siblings under `.pattern-drafts/<slug>/`) and the path 003 actually
      needs (`../components/ComponentName.astro`, correct only once
      `page.astro`/`component.astro` are promoted to
      `src/pages/`/`src/components/`). Confirmed against 003's own
      worked example (`'../components/PatternMVP.astro'` from
      `src/pages/branding.astro`) that the post-promotion path is the
      one 003 needs verbatim, with no manual fixing after promotion.
      Fixed in both `SKILL.md` and `contracts/draft-output.md`.

**Checkpoint**: Both user stories independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verification and documentation that spans both stories

- [X] T009 [P] Verify constitution Article I: search `pattern-assistant/`
      for `_elementor_data` and confirm zero matches. **Result**: zero
      matches — the file never mentions the field at all, not even in
      passing prose (unlike 001/003, which have one documentary mention
      each).
- [X] T010 [P] Verify FR-004/FR-006: review `SKILL.md` end to end and
      confirm no instruction ever writes into `src/components/`,
      `src/pages/`, or `astro-site/manifest.json` — only under
      `astro-site/.pattern-drafts/`. **Result**: confirmed — every
      mention of those three paths is either an explicit "never write
      here" statement or (for `src/components/`, `src/pages/`) a
      reference to the post-promotion import path text (T008's fix),
      never an actual write target.
- [X] T011 [P] Write `pattern-assistant/README.md` — short pointer doc
      (same role as `skill/README.md`), declaring `SKILL.md` the source
      of truth and summarizing the flow and staging location. **Result**:
      done.
- [X] T012 [P] Update the root `README.md`: "tres componentes" → four,
      add `pattern-assistant/` to the Estructura list, update "Uso con
      spec-kit" to mention it alongside plugin/mcp/skill. **Result**:
      done.

**Checkpoint**: Feature complete — `specs/004-pattern-authoring-assistant`
(12/12 tasks). `pattern-assistant/SKILL.md` is fully assembled: zero
placeholders, a real (not dry-run) structural cross-check against
003's actual text caught and fixed a genuine bug (the import-path
ambiguity) before it could ever produce a broken draft. What remains
unverified is execution against a real WordPress site — same limitation
as specs 001–003.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–4)**: Depend on Foundational phase completion.
  Unlike a fully independent story split, **User Story 2 also depends on
  User Story 1's T005** — a page-wiring draft only makes sense once the
  component it wires up exists (same relationship 003's US1/US2 had
  through their shared classify step).
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational only — independently
  shippable as the MVP (a component draft alone is still useful for
  review, even without the page-wiring draft)
- **User Story 2 (P2)**: Depends on Foundational AND User Story 1's T005

### Parallel Opportunities

- T002 (gitignore) can run in parallel with T001 (different files)
- T009–T012 (Polish) — independent checks/files, run in parallel

---

## Parallel Example: Setup

```bash
Task: "Create pattern-assistant/SKILL.md with frontmatter and section headers"
Task: "Add .pattern-drafts/ to astro-site/.gitignore"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (page resolution + data gathering)
3. Complete Phase 3: User Story 1 (component draft)
4. **STOP and VALIDATE**: Run `quickstart.md` scenarios 1–3
5. A component draft alone is already useful to a human designing a
   pattern by hand — User Story 2's page-wiring draft is a convenience on
   top of it, not a prerequisite for value

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → MVP
3. Add User Story 2 → validate independently (including the structural
   cross-check against 003's actual text)
4. Polish: README updates + constitution/boundary checks

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No automated tests — `quickstart.md` plus the direct structural
  cross-check against 003's `SKILL.md` are the verification method (see
  Tests note above)
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
