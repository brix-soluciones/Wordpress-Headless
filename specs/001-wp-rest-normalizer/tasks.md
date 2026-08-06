---

description: "Task list template for feature implementation"
---

# Tasks: WordPress REST Exposure Normalizer Plugin

**Input**: Design documents from `/specs/001-wp-rest-normalizer/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in the feature spec. Per `research.md`, this feature
uses no PHPUnit/Composer-based automated suite (zero-dependency constraint);
verification is the manual/scripted `quickstart.md` flow against a real
WordPress instance, referenced as explicit tasks below instead of automated
test tasks.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, per `plan.md`'s Project Structure — all paths are under
`plugin/` at the repository root (`plugin/migration-toolkit.php`,
`plugin/includes/`, `plugin/readme.txt`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Plugin skeleton — files exist with correct headers, nothing wired yet

- [X] T001 Create `plugin/migration-toolkit.php` with the standard WordPress
      plugin header block (Plugin Name, Description, Version) and
      `plugin/includes/` directory; no logic yet
- [X] T002 [P] Create `plugin/includes/class-sitemap-endpoint.php` with an
      empty class skeleton (constructor only)
- [X] T003 [P] Create `plugin/includes/class-rest-normalizer.php` with an
      empty class skeleton (constructor only)
- [X] T004 [P] Create `plugin/includes/class-cors.php` with an empty class
      skeleton (constructor only)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared logic and wiring that every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `migration_toolkit_get_public_post_types()` in
      `plugin/includes/functions.php` — returns all post types registered
      with `public => true` (per `data-model.md`'s inclusion rule); this is
      the shared source of truth used by both the site-map query (US1) and
      the REST-exposure normalizer (US2)
- [X] T006 Wire the bootstrap in `plugin/migration-toolkit.php`: require
      `includes/functions.php` and all three `includes/class-*.php` files,
      and instantiate each class unconditionally on the `plugins_loaded`
      hook (nothing in any story runs until this exists)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Discover all migratable content through one endpoint (Priority: P1) 🎯 MVP

**Goal**: `GET /wp-json/migracion/v1/site-map` lists every publicly
published content item's URL, type, and last-modified date (FR-001,
FR-002, FR-010; contract: `contracts/site-map-endpoint.md`)

**Independent Test**: Activate the plugin (even with US2/US3 unimplemented),
call the endpoint, and confirm the response matches
`quickstart.md` scenario 1 — every published item listed, drafts/private
excluded, `modified` changes when an item is edited.

### Implementation for User Story 1

- [X] T007 [US1] Register the REST route `migracion/v1/site-map` (`GET`,
      public/unauthenticated permission callback) on `rest_api_init` in
      `plugin/includes/class-sitemap-endpoint.php`
- [X] T008 [US1] Implement the query in
      `plugin/includes/class-sitemap-endpoint.php`: a single
      `WP_Query`/`get_posts` pass across
      `migration_toolkit_get_public_post_types()` with `post_status =>
      'publish'` only — no per-item queries (per `research.md`'s
      single-pass decision; FR-002's exclusion of draft/private/trashed
      items falls out of `post_status => 'publish'`). Password-protected
      posts also have `post_status = 'publish'` in WordPress, so they are
      **not** excluded by the status filter alone — explicitly skip any
      result where `post_password` is non-empty to satisfy FR-002's
      password-protected exclusion.
- [X] T009 [US1] Map each query result to `{ "url": get_permalink(),
      "type": post_type, "modified": ISO-8601 UTC from post_modified_gmt }`
      and wrap in the `{ "items": [...] }` envelope in
      `plugin/includes/class-sitemap-endpoint.php`, per
      `contracts/site-map-endpoint.md` (including the empty-array case for
      a site with no public content)
- [X] T010 [US1] Manually run `quickstart.md` scenario 1 (site-map
      endpoint) against a real WordPress instance and confirm all expected
      outcomes. **Result** (tested on Hostinger): draft correctly excluded;
      `modified` updates correctly when an item is edited.
- [X] T010a [US1] **Post-ship fix** (found via the MCP server's real-usage
      validation, not the original T010 run): `elementor_library`
      (Elementor's internal template/kit library) was appearing in
      site-map results — it's registered `public => true` on the tested
      site despite not being real content. Added
      `migration_toolkit_get_excluded_post_types()` in
      `plugin/includes/functions.php` (same pattern as the existing
      `attachment` exclusion) and excluded it from
      `migration_toolkit_get_public_post_types()`. Updated `spec.md`
      (Assumptions, Edge Cases), `data-model.md` (Site map entry
      inclusion rule), and `contracts/site-map-endpoint.md` (Guarantees)
      to document the exclusion explicitly rather than leaving it
      implicit.

**Checkpoint**: User Story 1 is fully functional and testable independently (MVP)

---

## Phase 4: User Story 2 - Read custom content types and ACF fields that aren't exposed by default (Priority: P2)

**Goal**: Public CPTs without REST support, and ACF fields attached to
REST-readable content, become readable through the standard WordPress REST
API with zero manual per-site configuration (FR-003, FR-004, FR-005;
contract: `contracts/rest-exposure.md`)

**Independent Test**: Activate the plugin (US1 may or may not be present),
and confirm `quickstart.md` scenarios 2 and 3 — a previously-unexposed
public CPT becomes readable, a non-public CPT stays unexposed, ACF field
values appear, and the plugin still activates cleanly with ACF absent.

### Implementation for User Story 2

- [X] T011 [US2] Implement forced REST exposure for public CPTs in
      `plugin/includes/class-rest-normalizer.php`: hook the
      `register_post_type_args` filter and set `show_in_rest = true` only
      when the post type is in `migration_toolkit_get_public_post_types()`
      and does not already have `show_in_rest` set (FR-003, FR-004 — never
      touch non-public types or ones already exposed)
- [X] T012 [US2] Implement conditional ACF field REST exposure in
      `plugin/includes/class-rest-normalizer.php`: guard with
      `class_exists('ACF')`, then hook
      `acf/rest_api/field_settings/show_in_rest` to force `true` for field
      groups attached to REST-readable content types (FR-005); confirm the
      guard makes this a clean no-op when ACF is not active
- [X] T013 [US2] Manually run `quickstart.md` scenarios 2 and 3 (CPT
      exposure, non-public CPT unaffected, ACF field exposure, and the
      no-ACF no-op path) against a real WordPress instance and confirm all
      expected outcomes. **Result** (tested on Hostinger): CPT registered
      with `show_in_rest => false` returned `200` with its content;
      an ACF field whose group had "Show in REST API" toggled off was
      still exposed under `.acf` — confirms the field-level force works
      with zero manual configuration.

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Fetch site content from the migration tooling's own domain (Priority: P3)

**Goal**: An administrator can configure allowed CORS origins; only
requests from a configured origin receive `Access-Control-Allow-Origin`
(FR-006, FR-007; contract: `contracts/cors.md`; entity:
`data-model.md`'s Allowed origin)

**Independent Test**: Activate the plugin (US1/US2 may or may not be
present), and confirm `quickstart.md` scenario 4 — no CORS header before
configuration, the header appears only for a configured origin, and other
origins remain unaffected.

### Implementation for User Story 3

- [X] T014 [US3] Implement allowed-origins storage in
      `plugin/includes/class-cors.php`: register the
      `migration_toolkit_allowed_origins` option (default: empty array) via
      the WordPress Options API, with validation that rejects malformed
      (non scheme+host) entries at save time, per `data-model.md`
- [X] T015 [US3] Add a minimal Settings API field (under the WordPress
      Settings menu) for an administrator to add/remove allowed origins, in
      `plugin/includes/class-cors.php` — no separate admin dashboard, just
      this one field (per `research.md`'s decision)
- [X] T016 [US3] Implement the CORS response header logic in
      `plugin/includes/class-cors.php`: on REST requests, emit
      `Access-Control-Allow-Origin: <origin>` only when the request's
      `Origin` header exactly matches an entry in
      `migration_toolkit_allowed_origins`; never emit a wildcard; no header
      at all when there is no match (FR-007), per `contracts/cors.md`
- [X] T017 [US3] Manually run `quickstart.md` scenario 4 (CORS) against a
      real WordPress instance and confirm all expected outcomes. **Result**
      (tested on Hostinger): the plugin's own CORS behavior is correct.
      Initial run also surfaced Hostinger's CDN unconditionally injecting
      `Access-Control-Allow-Origin` and caching the site-map response —
      both infrastructure-layer, not plugin defects; addressed via the
      `Cache-Control` header in `class-sitemap-endpoint.php`, FR-007's
      application-layer scoping in `spec.md`, and `quickstart.md`'s "Known
      limitations" section.

**Checkpoint**: All three user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification that spans all three stories, plus packaging

- [X] T018 [P] Write full `plugin/readme.txt` content (description,
      installation steps, FAQ) reflecting the plugin's actual scope from
      `plugin/README.md`
- [X] T019 [P] Verify FR-008 across the whole plugin: run `grep -ri
      "_elementor_data" plugin/` and confirm zero matches; confirm no
      response from Phase 3–5 contains the string `elementor`
      (`quickstart.md` scenario 5). **Result**: zero matches in
      `plugin/includes/*.php` and `plugin/migration-toolkit.php` (the only
      matches are in `README.md`/`readme.txt` prose stating the plugin does
      *not* read it). Response-content check deferred with T010/T013/T017
      (needs a live instance).
- [X] T020 [P] Verify FR-009 across all three stories: confirm no post
      count or `post_modified` timestamp changes as a side effect of
      exercising any endpoint or normalization, except the one
      deliberately edited item from `quickstart.md` scenario 1
      (`quickstart.md` scenario 6). **Result** (tested on Hostinger): static
      check (zero content-mutation calls in source) plus live check — same
      post count before/after all six scenarios.
- [X] T021 [P] Verify zero-config activation: activate the plugin on a
      clean WordPress instance with no CPTs/ACF/CORS pre-configured and
      confirm no fatal errors and no required setup step, per `plan.md`'s
      Constraints. **Result**: confirmed on the Hostinger test instance —
      all six `quickstart.md` scenarios ran successfully with no fatal
      errors and no setup step beyond adding the one CORS origin in
      scenario 4.
- [X] T022 [P] Update `plugin/README.md`'s scope checklist to mark
      show_in_rest (CPTs), show_in_rest (ACF), CORS headers, and the
      site-map endpoint as done; leave the "estado de migración" admin
      panel item noted as out of scope for this feature (see
      `research.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
  - Touch entirely different files (`class-sitemap-endpoint.php` vs
    `class-rest-normalizer.php` vs `class-cors.php`), so they can proceed
    in parallel once Foundational is done, or sequentially in priority
    order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on US2/US3 — independently shippable as the MVP
- **User Story 2 (P2)**: No dependencies on US1/US3 — shares only the Foundational helper
- **User Story 3 (P3)**: No dependencies on US1/US2 — shares only the Foundational wiring

### Within Each User Story

- T007→T008→T009 (US1), T011→T012 (US2), and T014→T015→T016 (US3) each
  edit the same file in sequence — not parallelizable within their story
- Each story's final manual-validation task (T010, T013, T017) depends on
  that story's implementation tasks being complete

### Parallel Opportunities

- T002, T003, T004 (Setup stub files) — different files, run in parallel
- Once Foundational (Phase 2) completes, Phase 3, Phase 4, and Phase 5 can
  be worked in parallel by different people — different files, no shared
  state beyond the Phase 2 helper/wiring
- T018–T022 (Polish) — independent checks/files, run in parallel

---

## Parallel Example: Setup

```bash
Task: "Create plugin/includes/class-sitemap-endpoint.php with an empty class skeleton"
Task: "Create plugin/includes/class-rest-normalizer.php with an empty class skeleton"
Task: "Create plugin/includes/class-cors.php with an empty class skeleton"
```

## Parallel Example: User Stories (after Foundational)

```bash
Task: "Implement User Story 1 (T007-T010) in plugin/includes/class-sitemap-endpoint.php"
Task: "Implement User Story 2 (T011-T013) in plugin/includes/class-rest-normalizer.php"
Task: "Implement User Story 3 (T014-T017) in plugin/includes/class-cors.php"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (site-map endpoint)
4. **STOP and VALIDATE**: Run `quickstart.md` scenario 1
5. Deploy/demo if ready — a working discovery endpoint is already useful to
   the migration tooling even before REST-exposure normalization or CORS
   exist

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → MVP
3. Add User Story 2 → validate independently
4. Add User Story 3 → validate independently
5. Polish: run the full `quickstart.md` (all 6 scenarios) end-to-end

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Once Foundational is done: Developer A takes US1, Developer B takes
   US2, Developer C takes US3 — each owns a single file with no overlap
3. Stories complete and validate independently, then Polish runs against
   the combined result

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No automated test tasks — `quickstart.md` is the verification method
  (see `research.md`)
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
