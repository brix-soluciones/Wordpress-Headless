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

- [ ] T001 Create `skill/SKILL.md` with frontmatter (`name`, `description`,
      an `argument-hint` covering the optional single-page argument —
      research.md #8) and top-level section headers for the flow
      (preamble, classify, populate, verify, report, sync path); no flow
      content yet
- [ ] T002 [P] Create `astro-site/scripts/check-responsive.mjs` as an
      empty file (no logic yet)
- [ ] T003 [P] Create `astro-site/tests/check-responsive.spec.mjs` as an
      empty file (no logic yet)
- [ ] T004 [P] Confirm `@playwright/test`'s browser binary is installed
      for `astro-site/` (`npx playwright install chromium` from within
      `astro-site/`, if not already present) — one-time environment
      setup, not code

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared script, its tests, and the shared `SKILL.md`
sections every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `astro-site/scripts/check-responsive.mjs` per
      `contracts/check-responsive-cli.md`: parse `<preview-base-url>` and
      one-or-more `<path>` args, launch Playwright, for each path set the
      viewport to each of the five widths (320/375/768/1024/1920, fixed
      height) and evaluate `document.documentElement.scrollWidth >
      document.documentElement.clientWidth` (research.md #3), print the
      `{ "results": { "<path>": { "<width>": bool, ... } } }` JSON to
      stdout, exit non-zero with a stderr message only on a genuine
      script failure (unreachable preview server, non-2xx path) — never
      on an individual page failing its own overflow check (depends on T002)
- [ ] T006 [P] Write `astro-site/tests/check-responsive.spec.mjs`
      (research.md #9): a local static fixture page with an element
      deliberately wider than its container at one viewport width
      (expect that width's result `false`), and a clean fixture page
      (expect all five widths `true`) (depends on T003, T005)
- [ ] T007 Write `SKILL.md`'s shared preamble (depends on T001): the
      constraint that all WordPress data comes only through
      `get_site_map`/`get_page_content`/`get_rendered_structure`/
      `get_media_original` — never a direct HTTP call (research.md #6);
      how the optional single-page argument selects single-page vs
      whole-site-via-`get_site_map` mode (research.md #8); and the
      `astro-site/manifest.json` read/parse instructions per
      `contracts/manifest-schema.md` — treat a missing file as
      `{ "pages": [] }`, stop and report on malformed JSON, never guess
- [ ] T008 Write `SKILL.md`'s shared verification sub-procedure (depends
      on T001, T005): run the project's build, start `astro preview`
      against that build's output, invoke `check-responsive.mjs`
      (`contracts/check-responsive-cli.md`) against the preview server
      for the page(s) being verified, and combine its per-viewport result
      with the build's pass/fail into one `VerificationResult`
      (`data-model.md`) per page — referenced (not repeated) by both the
      new-page flow (US1) and the sync flow (US3), since FR-005 applies
      to content updates too, not just new migrations

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

- [ ] T009 [US1] Write `SKILL.md`'s relevar-and-classify(match) section
      (depends on T007): for a page with no manifest entry, call
      `get_rendered_structure` before any classification decision
      (FR-001), and check its layout against the manifest's known
      `pattern` values (FR-002)
- [ ] T010 [US1] Write `SKILL.md`'s populate section (depends on T009):
      when a pattern matches, populate that pattern's component with the
      page's content and custom fields via `get_page_content` and its
      images via `get_media_original` (FR-004)
- [ ] T011 [US1] Write `SKILL.md`'s completion-gating section for this
      flow (depends on T008, T010): invoke the shared verification
      sub-procedure and report the page as migrated only when both the
      responsive check (all five viewports) and the build pass (FR-006,
      FR-008); on failure, report exactly what failed instead
- [ ] T012 [US1] Run `quickstart.md` scenarios 1 and 3 (matching pattern;
      deliberately failing verification) against the real `astro-site`
      project and a real WordPress site, and confirm all expected
      outcomes

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

- [ ] T013 [US2] Write `SKILL.md`'s classify(no-match) section (depends
      on T009): when no manifest pattern matches, flag the page for human
      decision and explicitly do not create, generate, or force any
      component for it (FR-003, FR-012)
- [ ] T014 [US2] Write `SKILL.md`'s batch-continuation-and-reporting
      section (depends on T013): flagging a page does not halt processing
      of other pages in the same run (FR-014); the end-of-run report
      lists flagged pages distinctly from migrated/updated ones (FR-015)
- [ ] T015 [US2] Run `quickstart.md` scenario 2 against the real
      `astro-site` project and a real WordPress site, and confirm all
      expected outcomes

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

- [ ] T016 [US3] Write `SKILL.md`'s sync-detection section (depends on
      T007): for pages that already have a manifest entry, call
      `get_site_map` and compare each entry's current `modified` date
      against that manifest entry's `last_synced_modified`, skipping
      layout relevamiction entirely for this flow (FR-009, FR-010);
      pages whose date hasn't changed are left untouched
- [ ] T017 [US3] Write `SKILL.md`'s sync-update section (depends on T008,
      T016): for each changed page, update its component's content/media
      via `get_page_content`/`get_media_original` without altering its
      `pattern` or `astro_file` (FR-011), then invoke the shared
      verification sub-procedure (T008) — FR-005's responsive/build gate
      applies to content updates, not only new migrations
- [ ] T018 [US3] Write `SKILL.md`'s sync-completion section (depends on
      T017): on a successful update, write that entry's new
      `last_synced_modified` to `astro-site/manifest.json`
      (`contracts/manifest-schema.md`)
- [ ] T019 [US3] Run `quickstart.md` scenario 4 against the real
      `astro-site` project and a real WordPress site, including
      confirming a second immediate sync run makes no further changes,
      and confirm all expected outcomes

**Checkpoint**: All three user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification that spans all three stories

- [ ] T020 [P] Run `quickstart.md` scenario 5 (missing
      `astro-site/manifest.json`) and confirm the skill treats it as
      `{ "pages": [] }` rather than raising an error (contracts/manifest-schema.md)
- [ ] T021 [P] Verify constitution Article I across the whole feature:
      search `skill/` and `astro-site/scripts/`, `astro-site/tests/` for
      `_elementor_data` and confirm zero matches
- [ ] T022 [P] Verify FR-012: review `SKILL.md` end to end and confirm no
      instruction ever assigns/fabricates a `pattern` value that isn't
      already present in `astro-site/manifest.json` from a prior human
      decision
- [ ] T023 [P] Update `skill/README.md` to reflect the as-built flow —
      cross-reference `SKILL.md`, and note that `manifest.json` now lives
      under `astro-site/`, not `skill/` (plan.md's Structure Decision)
- [ ] T024 [P] Run the full `astro-site` test suite
      (`cd astro-site && npx playwright test`) and confirm
      `check-responsive.spec.mjs` passes alongside anything else already
      there

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
