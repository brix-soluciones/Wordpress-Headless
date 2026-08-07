---

description: "Task list template for feature implementation"
---

# Tasks: WordPress MCP Tools Server

**Input**: Design documents from `/specs/002-wp-mcp-tools/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Requested by design — `plan.md`'s Testing section and
`research.md` #9 commit to `pytest` + `pytest-asyncio` + `respx` unit
tests per tool, in addition to the manual `quickstart.md` real-instance
validation. Both are included below.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, per `plan.md`'s Project Structure — all paths are under
`mcp/` at the repository root (`mcp/pyproject.toml`,
`mcp/src/wp_mcp_server/`, `mcp/tests/`). `mcp/.venv` and `mcp/README.md`
already exist in the repo and are reused, not recreated.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeleton — files and dependency metadata exist, nothing wired yet

- [X] T001 Create `mcp/pyproject.toml` (PEP 621): package `wp_mcp_server`,
      runtime dependencies `mcp`, `httpx`, `beautifulsoup4`, `playwright`;
      `[project.optional-dependencies] dev = ["pytest", "pytest-asyncio",
      "respx"]`; console-script entry point `wp-mcp-server =
      "wp_mcp_server.server:main"` (research.md #10). The existing
      `mcp/.venv` is reconciled against this file via `pip install -e
      ".[dev]"`, not recreated. **Result**: installs cleanly; `mcp` 2.0.0
      renamed `FastMCP` to `MCPServer` (importable from `mcp.server`) —
      verified directly against the installed package before writing
      `server.py`, `research.md` #1 updated accordingly.
- [X] T002 [P] Create package skeleton: `mcp/src/wp_mcp_server/__init__.py`
      and `mcp/src/wp_mcp_server/tools/__init__.py` (empty files
      establishing the layout from `plan.md`'s Project Structure)
- [X] T003 [P] Create `mcp/tests/__init__.py` (empty, establishes the test package)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared config, HTTP client, and server wiring that every tool depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `mcp/src/wp_mcp_server/config.py`: a `load_config()`
      that reads `WP_MCP_BASE_URL` from the environment and returns a
      `ServerConfig` (per `data-model.md`); raises a clear, descriptive
      error immediately if the variable is unset or not a well-formed URL
      (FR-007). **Result**: verified both failure paths raise `RuntimeError`
      with the expected message (unset var, malformed URL).
- [X] T005 Implement `mcp/src/wp_mcp_server/wp_client.py`: a factory that
      builds one shared `httpx.AsyncClient` bound to `ServerConfig.base_url`
      (research.md #2), plus a thin `get_json(path, params=None)` helper
      that issues the request and raises on non-2xx — the single chokepoint
      every tool module calls through, per `plan.md`'s Structure Decision
- [X] T006 Implement `mcp/src/wp_mcp_server/server.py`: construct the
      `MCPServer` instance (research.md #1 — SDK's actual class name,
      confirmed against the installed package), a `main()` stdio
      entrypoint that calls `load_config()` and builds the shared client
      from `wp_client.py` before entering the stdio run loop; tool
      registrations added incrementally per user story phase below
- [X] T007 [P] Implement `mcp/tests/conftest.py`: `respx`-based fixtures
      that fake the WordPress REST API (`/wp-json/migracion/v1/site-map`,
      `/wp-json/wp/v2/posts`, `/wp-json/wp/v2/pages`,
      `/wp-json/wp/v2/media`) against a fixed test `base_url`, reusable
      across all `test_*.py` files (research.md #9)

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Discover everything on the site worth migrating (Priority: P1) 🎯 MVP

**Goal**: `get_site_map` returns every publicly published item's URL,
type, and last-modified date via the companion plugin's discovery
endpoint (FR-001, FR-010, FR-011; contract: `contracts/get_site_map.md`)

**Independent Test**: Point the server at a WordPress site with the
companion plugin installed, call `get_site_map` with no arguments, and
confirm the response matches `quickstart.md` scenario 1.

### Tests for User Story 1

- [X] T008 [P] [US1] Write `mcp/tests/test_site_map.py`: success case
      (`items` array passed through as `SiteMapEntry` list), discovery
      endpoint missing/non-2xx → raised error (not a silent empty list),
      target site unreachable → raised error — per
      `contracts/get_site_map.md`. **Result**: 4/4 passing (also added an
      explicit empty-site-map case beyond the 3 originally scoped).

### Implementation for User Story 1

- [X] T009 [US1] Implement `mcp/src/wp_mcp_server/tools/site_map.py`:
      `get_site_map()` calls `wp_client.get_json` against
      `/wp-json/migracion/v1/site-map`, returns the `items` array
      unmodified, and raises per the error conditions in
      `contracts/get_site_map.md` (depends on T004, T005)
- [X] T010 [US1] Register `get_site_map` as a tool on the `MCPServer`
      instance in `mcp/src/wp_mcp_server/server.py` (depends on T006, T009)
- [ ] T011 [US1] Run `quickstart.md` scenario 1 against a real WordPress
      instance with the companion plugin active and confirm the expected
      outcomes. **Not run**: no live WordPress instance available in this
      environment — pending manual verification (see completion report).
- [X] T011a [US1] **Post-ship doc fix** (found via `specs/003-astro-migration-skill`'s
      T012 dry-run): the plugin's discovery endpoint now includes `id`
      per post/page (`specs/001-wp-rest-normalizer`'s T010b) — this
      server needed no code change since `get_site_map` already passes
      the response through unmodified (T009), but `data-model.md`,
      `contracts/get_site_map.md`, and `tests/test_site_map.py`'s
      fixtures were updated to reflect the new field. Full suite
      re-run: 21/21 passing.

**Checkpoint**: User Story 1 is fully functional and testable independently (MVP)

---

## Phase 4: User Story 2 - Read the plain content of a specific page or post (Priority: P1)

**Goal**: `get_page_content(id)` returns an item's plain title/content
plus any exposed ACF fields, via native `/wp/v2/posts`/`/wp/v2/pages`
(FR-002, FR-010, FR-011; contract: `contracts/get_page_content.md`)

**Independent Test**: Call `get_page_content` with the id of a known
post/page (with an ACF field attached), and confirm the response matches
`quickstart.md` scenario 2, including the not-found case.

### Tests for User Story 2

- [X] T012 [P] [US2] Write `mcp/tests/test_page_content.py`: id resolves
      via `/wp/v2/posts`, id resolves via `/wp/v2/pages` fallback after a
      posts-404, `custom_fields` present when `acf` key exists,
      `custom_fields` absent (not `null`) when it doesn't, unknown/
      non-public id → raised "not found" — per
      `contracts/get_page_content.md` and research.md #5. **Result**: 5/5
      passing.

### Implementation for User Story 2

- [X] T013 [US2] Implement `mcp/src/wp_mcp_server/tools/page_content.py`:
      `get_page_content(id)` tries `/wp/v2/posts/{id}`, falls back to
      `/wp/v2/pages/{id}` on 404, maps the result to `PageContent`
      (`title`, `content`, optional `custom_fields` from the response's
      `acf` key), and raises "not found" when neither lookup matches
      (depends on T004, T005)
- [X] T014 [US2] Register `get_page_content` as a tool in
      `mcp/src/wp_mcp_server/server.py` (depends on T006, T013)
- [ ] T015 [US2] Run `quickstart.md` scenario 2 against a real WordPress
      instance, including the ACF field case and the not-found case, and
      confirm the expected outcomes. **Not run**: no live WordPress
      instance available in this environment — pending manual
      verification (see completion report).

**Checkpoint**: User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Relevar la estructura visual de una página pública (Priority: P2)

**Goal**: `get_rendered_structure(url)` returns a simplified layout
outline of a public page, resolved via plain fetch with a headless-render
fallback, and never contains Elementor-internal data (FR-003, FR-004,
FR-005, FR-010, FR-011; contract: `contracts/get_rendered_structure.md`)

**Independent Test**: Call `get_rendered_structure` with a live page URL
on the configured site, and confirm the response matches `quickstart.md`
scenario 3, including the cross-host rejection case.

### Tests for User Story 3

- [X] T016 [P] [US3] Write `mcp/tests/test_rendered_structure.py`:
      hostname not matching the configured base URL → raised error before
      any fetch; plain-fetch success builds an outline with no
      `<script>`/`<style>`/comment nodes; the fallback rule fires on a
      fixture body with fewer than 10 element descendants AND fewer than
      200 chars of visible text; the fallback rule also fires on a fixture
      containing `<div id="root"></div>` (zero element children) even
      when surrounding text is long; the fallback rule does NOT fire on a
      normal WordPress page fixture with substantial body content — per
      `contracts/get_rendered_structure.md`. **Result**: 5/5 passing. The
      headless-render fallback's actual Playwright invocation is not unit
      tested (would require a browser binary + network in CI); the
      decision function that triggers it is tested directly, and the real
      fallback path is exercised in `quickstart.md`.

### Implementation for User Story 3

- [X] T017 [P] [US3] Implement `mcp/src/wp_mcp_server/html_outline.py`:
      parse HTML with `BeautifulSoup` (`html.parser`), strip `<script>`,
      `<style>`, and comment nodes, and build the nested `OutlineNode`
      structure (`tag`, `id`, `class`, `text`, `children`) per
      `data-model.md` (research.md #4)
- [X] T018 [US3] Implement
      `mcp/src/wp_mcp_server/tools/rendered_structure.py`:
      `get_rendered_structure(url)` validates the URL's hostname against
      `ServerConfig.base_url`, performs the plain `GET`, then decides
      whether to fall back to headless rendering using this exact rule on
      the stripped `<body>`: fallback iff **(A: fewer than 10 element
      descendants AND B: visible text under 200 chars, whitespace
      collapsed) OR (C: an element matching `#root`, `#app`, `#__next`,
      `#___gatsby`, or `[data-reactroot]` exists with zero direct element
      children)** (research.md #3). Only when the rule fires, lazily
      launch Playwright, re-fetch `url` there, and re-parse from that DOM
      instead. Builds the `RenderedStructure` (including
      `rendering_method`, `"fetch"` or `"headless_render"`) via
      `html_outline.py` (depends on T004, T005, T017)
- [X] T019 [US3] Register `get_rendered_structure` as a tool in
      `mcp/src/wp_mcp_server/server.py` (depends on T006, T018)
- [ ] T020 [US3] Run `quickstart.md` scenario 3 against a real WordPress
      instance, including the cross-host rejection case, and confirm no
      field resembling `_elementor_data` appears in the outline at any
      depth (FR-005, SC-003). **Not run**: no live WordPress instance
      available in this environment — pending manual verification (see
      completion report).
- [X] T020a [US3] **Post-ship enhancement** (found via real-usage
      validation of T020, not automatable in this environment): the
      outline repeated identical header/nav/footer/comment-form chrome on
      every call, and `<body>` carried Elementor's site-wide kit classes
      (`elementor-default`, `elementor-kit-14`) even on non-Elementor
      content — both pure noise for layout-pattern matching. Added
      `html_outline.resolve_outline_root()` (default: scope to `<main>`,
      fallback to `<body>`) and an optional `selector` param on
      `get_rendered_structure`/the MCP tool, plus a `scope` field in the
      response (FR-012, research.md #11). Scoping to `<main>` by default
      also resolves the kit-class noise structurally, without a
      `elementor-`-prefix filter (deliberately rejected — see research.md
      #11, it would strip real layout signal from genuinely Elementor-built
      pages). Updated `spec.md` (US3 scenarios, Edge Cases, FR-012,
      SC-007), `data-model.md` (RenderedStructure's `scope` field),
      `contracts/get_rendered_structure.md`. Added `soupsieve` as an
      explicit dependency (used directly to match `selector` against the
      root element itself, since `select_one` only searches descendants).
      6 new/updated tests in `test_rendered_structure.py`; full suite
      21/21 passing.

**Checkpoint**: User Stories 1, 2, AND 3 all work independently

---

## Phase 6: User Story 4 - Resolve the original file behind a referenced image (Priority: P3)

**Goal**: `get_media_original(slug)` resolves a media slug to its
full-resolution `source_url`, never a resized/cropped variant (FR-006,
FR-010, FR-011; contract: `contracts/get_media_original.md`)

**Independent Test**: Call `get_media_original` with a known media slug,
and confirm the response matches `quickstart.md` scenario 4, including
the not-found case.

### Tests for User Story 4

- [X] T021 [P] [US4] Write `mcp/tests/test_media_original.py`: slug match
      returns `source_url`/`mime_type` from the first result (never a
      `media_details.sizes.*` value), empty result array → raised "not
      found" — per `contracts/get_media_original.md` and research.md #6.
      **Result**: 2/2 passing.

### Implementation for User Story 4

- [X] T022 [US4] Implement
      `mcp/src/wp_mcp_server/tools/media_original.py`:
      `get_media_original(slug)` queries `/wp/v2/media?slug={slug}`,
      returns `source_url` + `mime_type` from the first array element, and
      raises "not found" on an empty result (depends on T004, T005)
- [X] T023 [US4] Register `get_media_original` as a tool in
      `mcp/src/wp_mcp_server/server.py` (depends on T006, T022)
- [ ] T024 [US4] Run `quickstart.md` scenario 4 against a real WordPress
      instance, including the not-found case, and confirm the expected
      outcomes. **Not run**: no live WordPress instance available in this
      environment — pending manual verification (see completion report).

**Checkpoint**: All four tools work independently

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verification that spans all four tools

- [X] T025 [P] Verify FR-005 / Constitution Article I across the whole
      server: search `mcp/src` for `_elementor_data` and confirm zero
      matches outside of comments/docs that state it's excluded.
      **Result**: one match, in `rendered_structure.py`'s module
      docstring stating it's never exposed — zero matches in actual code.
- [X] T026 [P] Verify FR-011: confirm none of
      `tools/site_map.py`, `tools/page_content.py`,
      `tools/rendered_structure.py`, `tools/media_original.py` imports
      another tool module — each must be callable with only
      `config.py`/`wp_client.py` (and, for US3, `html_outline.py`).
      **Result**: confirmed — only imports are `wp_client` (all four) and
      `html_outline` (rendered_structure only).
- [X] T027 [P] Verify FR-009: review each tool's return shape against
      `data-model.md` and confirm none emits Astro or any other
      target-framework code — only the documented data fields.
      **Result**: confirmed by code review and a live `list_tools()`
      smoke test — each tool's schema exposes exactly the documented
      input (`id`, `url`, `slug`, or no args), and every return statement
      in `tools/*.py` builds only the fields specified in `data-model.md`.
- [ ] T028 [P] Run `quickstart.md` scenario 5 (point `WP_MCP_BASE_URL` at
      a second WordPress site and re-run `get_site_map` with no code
      change) and confirm SC-005. **Not run**: no live WordPress instance
      available in this environment — pending manual verification (see
      completion report). Config-level support for this is verified: T004
      confirms `WP_MCP_BASE_URL` is the sole source of the target site
      with no hardcoded fallback.
- [X] T029 [P] Run the full automated suite (`mcp/.venv/Scripts/pytest`)
      and confirm all tests from Phases 3–6 pass together. **Result**:
      16/16 passing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - Each story touches its own tool module (`tools/site_map.py`,
    `tools/page_content.py`, `tools/rendered_structure.py`,
    `tools/media_original.py`) plus its own test file, so they can proceed
    in parallel once Foundational is done, or sequentially in priority
    order (P1 → P1 → P2 → P3). All four register into the same
    `server.py`, so those specific registration tasks (T010, T014, T019,
    T023) serialize against each other even though the rest of each story
    doesn't.
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on US2/US3/US4 — independently shippable as the MVP
- **User Story 2 (P1)**: No dependencies on US1/US3/US4 — shares only the Foundational config/client
- **User Story 3 (P2)**: No dependencies on US1/US2/US4 — shares only the Foundational config/client
- **User Story 4 (P3)**: No dependencies on US1/US2/US3 — shares only the Foundational config/client

### Within Each User Story

- Tests (T008, T012, T016, T021) are written before their story's
  implementation tasks, and should fail until that story's tool module
  exists
- Within US3: T017 (`html_outline.py`) has no dependency on T018 and can
  run in parallel with it being started, but T018 imports T017's output,
  so T018 cannot be marked complete until T017 is
- Each story's tool-implementation task precedes its own server
  registration task, which precedes its own `quickstart.md` validation task

### Parallel Opportunities

- T002, T003 (Setup skeleton files) — different files, run in parallel
- T007 (test fixtures) can be built in parallel with T004–T006 (different files)
- Once Foundational (Phase 2) completes, Phases 3–6 can be worked in
  parallel by different people — different tool/test files, no shared
  state beyond the Phase 2 config/client
- T025–T029 (Polish) — independent checks, run in parallel

---

## Parallel Example: Setup

```bash
Task: "Create mcp/src/wp_mcp_server/__init__.py and mcp/src/wp_mcp_server/tools/__init__.py"
Task: "Create mcp/tests/__init__.py"
```

## Parallel Example: User Stories (after Foundational)

```bash
Task: "Implement User Story 1 (T008-T011) in mcp/src/wp_mcp_server/tools/site_map.py"
Task: "Implement User Story 2 (T012-T015) in mcp/src/wp_mcp_server/tools/page_content.py"
Task: "Implement User Story 3 (T016-T020) in mcp/src/wp_mcp_server/tools/rendered_structure.py"
Task: "Implement User Story 4 (T021-T024) in mcp/src/wp_mcp_server/tools/media_original.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (`get_site_map`)
4. **STOP and VALIDATE**: Run `quickstart.md` scenario 1
5. Deploy/demo if ready — discovery alone already lets an agent see what a
   site has, even before content/layout/media resolution exist

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. Add User Story 1 → validate independently → MVP
3. Add User Story 2 → validate independently
4. Add User Story 3 → validate independently
5. Add User Story 4 → validate independently
6. Polish: run the full `quickstart.md` (all 5 scenarios) end-to-end plus the automated suite

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Once Foundational is done: Developer A takes US1, Developer B takes
   US2, Developer C takes US3, Developer D takes US4 — each owns a
   distinct tool/test file pair
3. Stories complete and validate independently, then Polish runs against
   the combined result

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests are included per `plan.md`'s Testing decision (pytest +
  pytest-asyncio + respx) — write them first per story, confirm they fail
  before implementing
- `quickstart.md`'s real-instance scenarios remain the Article VIII-spirit
  verification on top of the automated suite, not a replacement for it
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
