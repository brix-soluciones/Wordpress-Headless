# Phase 0 Research: WordPress-to-Astro Migration Skill

The user-supplied constraints (SKILL.md format, Node/Playwright
responsive-check script, `astro-site/` as the fixed target project,
`manifest.json` at its root, MCP-only WordPress access) fix the major
decisions. This document resolves the remaining implementation-level
choices, each traced back to a spec requirement, edge case, or a concrete
signal already present in the repository.

## 1. Where the responsive-check script lives, and its dependency

**Decision**: `astro-site/scripts/check-responsive.mjs`, using the
`@playwright/test` package already declared in
`astro-site/package.json`'s `devDependencies` — not a new dependency
under `skill/`.

**Rationale**: Confirmed by inspecting the repo before deciding:
`astro-site/node_modules/@playwright/test` and `playwright-core` are
already installed, and nothing else in the repo references them yet —
strong evidence this was provisioned specifically for this checker.
Node's module resolution walks *up* from a script's own directory
looking for `node_modules`, never *sideways* into a sibling directory —
so a script under `skill/scripts/` could not resolve
`astro-site/node_modules/@playwright/test` without a second install
(duplicating a dependency the target project already has) or an
`NODE_PATH` workaround. Placing the script inside `astro-site/` avoids
both.

**Alternatives considered**: A script under `skill/scripts/` with its own
`package.json` + `node_modules` — rejected, duplicates a dependency
already present one directory away for no benefit. `NODE_PATH`-based
cross-directory resolution — rejected, fragile and non-obvious compared
to just placing the file where its dependency already resolves normally.

## 2. Responsive check runs against the real build, not a dev server

**Decision**: The verification sequence for a page's "done" state is:
`npm run build` (already required by FR-007) → serve the resulting
`dist/` via `astro preview` → run the 5-viewport overflow check
(`check-responsive.mjs`) against that preview server's URL for the page.
The build that satisfies FR-007/FR-008 and the build the responsive check
(FR-005/FR-006) runs against are **the same build**, not two independent
passes.

**Rationale**: The spec requires both a passing responsive check and a
passing build before a page counts as done, but doesn't mandate which
artifact the responsive check inspects. Checking against `astro dev`'s
dev server risks the dev server's output diverging from what actually
ships (different bundling/CSS injection timing) — checking the real
`dist/` output is strictly more faithful to what Article VIII's "real
build" gate is trying to guarantee, and avoids paying for two separate
Astro builds (dev-server startup + a production build) when one already
suffices for both gates.

**Alternatives considered**: Checking against `astro dev` — rejected,
weaker guarantee and doesn't reduce work (still needs the production
build for FR-007 regardless). Running two independent builds (one
implicit via dev server, one explicit for FR-007) — rejected as wasted
work once the shared-artifact approach was identified.

## 3. Overflow-detection metric

**Decision**: For each of the five viewport widths (320, 375, 768, 1024,
1920px; height fixed at a generous constant, e.g. 1000px, since only
horizontal overflow is in scope), set the Playwright page's viewport,
navigate to the target URL, and evaluate
`document.documentElement.scrollWidth > document.documentElement.clientWidth`
in-page. A page fails the check if this is true at any of the five
widths.

**Rationale**: This is the standard, well-established technique for
detecting horizontal overflow — `scrollWidth` reflects the content's
actual rendered width including anything that overflows, `clientWidth`
reflects the visible viewport width; a mismatch means something doesn't
fit. It requires no additional tooling beyond what Playwright already
provides (`page.evaluate`).

## 4. `manifest.json` schema and where the sync record lives

**Decision**: A single JSON file at `astro-site/manifest.json`, an array
of entries each carrying `wp_slug` (or full URL), `pattern`, `astro_file`,
and `last_synced_modified` (nullable — absent/`null` until the page's
first successful sync) — one file, not a separate sync-record store. If
the file doesn't exist yet, the skill treats it as an empty entry list
(spec edge case: "no manifest yet") rather than erroring.

**Rationale**: The spec's "Sync record" (FR-010) always applies to an
already-migrated page — i.e. one that already has a manifest entry — so
storing the sync timestamp on that same entry avoids introducing a
second file that could drift out of sync with the manifest itself. See
`contracts/manifest-schema.md`.

**Alternatives considered**: A separate `sync-state.json` — rejected,
no benefit identified over co-locating the field, and a second file adds
a second thing that can go stale/inconsistent with the first.

## 5. Flagged pages and verification results are not persisted

**Decision**: Which pages are flagged (no matching pattern) and each
page's latest verification result (responsive/build pass-fail) are
computed fresh every run and only ever surface in that run's report —
neither is written to a file.

**Rationale**: A page is "flagged" purely as a function of "does it have
a manifest entry" (FR-002/FR-003) — this is fully derivable from
`manifest.json` plus the current site-map on every run, so a separate
persisted flag list would be redundant, and could go stale (e.g. still
listing a page a human already resolved by hand outside a skill run).
Matches spec Assumptions: human decisions happen through conversation,
not a separate ticketing system this feature would need to maintain.

## 6. The skill has no MCP client code

**Decision**: `SKILL.md` contains no code that speaks the MCP protocol
or makes HTTP calls to WordPress. It instructs Claude Code to invoke
`get_site_map`, `get_page_content`, `get_rendered_structure`, and
`get_media_original` as already-available tools (from the
`specs/002-wp-mcp-tools` server, assumed configured for the session) —
the same way any Claude Code skill instructs use of any tool already in
its toolset.

**Rationale**: This is the strongest possible reading of the user's
"la skill no reimplementa llamadas HTTP a WordPress, siempre pasa por el
MCP" constraint — there is no custom client code to keep in sync with
002's contracts, and no second code path that could diverge from what
002 already guarantees (e.g. never reading `_elementor_data`).

## 7. `astro-site/` path is fixed, not configurable

**Decision**: `SKILL.md`'s instructions reference `astro-site/` as a
literal, hardcoded sibling path within this repository. No
environment-variable or config-file indirection is introduced for it.

**Rationale**: The user stated this directly and unconditionally ("vive
en `astro-site/`, mismo repo, carpeta hermana"), and nothing in the repo
suggests more than one target project exists or is planned. Adding
configurability here would be speculative scope beyond what's asked or
evidenced — if a second target project ever becomes real, that's a
future amendment made against that concrete need, not now.

## 8. Single-page vs whole-site invocation

**Decision**: `SKILL.md` accepts an optional argument identifying a
single page (URL or slug). When given, only that page is processed. When
omitted, the skill processes the full site: `get_site_map` for
discovery, comparing every item against `manifest.json` to decide,
per item, whether it's a new page (User Story 1/2's flow) or an
already-migrated page eligible for content sync (User Story 3's flow).

**Rationale**: Directly implements the spec's Assumption that a run may
target a single page or the full site, and matches Claude Code's own
skill-invocation convention (an optional free-text argument after the
skill name) rather than inventing a separate flag/parameter scheme.

## 9. Testing the responsive-check script

**Decision**: A small `@playwright/test` suite
(`astro-site/tests/check-responsive.spec.mjs`) against local static
fixture HTML — one page with a deliberately overflowing element at a
specific viewport, one clean page — verifying the pass/fail decision
directly, independent of `astro-site`'s real content. `quickstart.md`
separately runs the script against the real `astro-site` project as part
of validating the full skill flow end-to-end.

**Rationale**: `@playwright/test` is already available as a real test
framework (not something this feature needs to add), so a fast,
deterministic fixture-based test of the core overflow-detection logic is
low-cost and catches regressions in that logic specifically, complementing
(not replacing) the real-project `quickstart.md` validation — consistent
with how 001 and 002 each paired a small amount of automated verification
with a real-artifact validation guide, proportional to what each
feature's project type actually supports.
