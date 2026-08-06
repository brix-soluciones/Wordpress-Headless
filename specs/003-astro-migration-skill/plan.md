# Implementation Plan: WordPress-to-Astro Migration Skill

**Branch**: `003-astro-migration-skill` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-astro-migration-skill/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A Claude Code skill (`SKILL.md`) that drives WordPress→Astro migration:
relevar a new page's layout via the MCP's `get_rendered_structure`,
classify it against `astro-site/manifest.json`'s known page→pattern
mappings, flag unmatched pages for human decision, or populate a matched
pattern's component with `get_page_content`/`get_media_original` data.
Every migrated or updated page must pass a real, automated 5-viewport
overflow check and a real `npm run build` before being reported done.
Content-only sync for already-migrated pages skips relevamiento and uses
`get_site_map` + `get_page_content` to detect and pull in changes by
comparing `modified` dates. The skill contains no WordPress HTTP client of
its own — every piece of WordPress data comes through the four MCP tools
from `specs/002-wp-mcp-tools`. The one piece of real supporting code is a
Node/Playwright script that performs the overflow check, living inside
`astro-site/` to reuse its already-installed `@playwright/test`.

## Technical Context

**Language/Version**: The skill itself is a Markdown procedure
(`SKILL.md`, Claude Code's skill format) — not a programming language
artifact. Its one supporting script (`astro-site/scripts/check-responsive.mjs`)
is Node.js, matching `astro-site/package.json`'s `engines.node >= 22.12.0`.

**Primary Dependencies**: None added for the skill itself — MCP tool
calls happen natively through Claude Code once the `specs/002-wp-mcp-tools`
server is configured for the session; the skill's instructions invoke
`get_site_map`/`get_page_content`/`get_rendered_structure`/`get_media_original`
by name, with no custom client code to keep in sync with their contracts.
The responsive-check script depends on `@playwright/test`, already present
in `astro-site/package.json`'s `devDependencies` — no new dependency
introduced.

**Storage**: `astro-site/manifest.json` — the one piece of state this
feature owns: page→component-pattern mappings plus, per entry, the
last-synced `modified` date used to detect content changes (spec's "Sync
record"). No other persistence; flagged pages and verification results
are recomputed fresh each run, not stored between runs (research.md #5).

**Testing**: `@playwright/test` (already available in `astro-site/`) for
a small, fixture-based test of the responsive-check script's overflow
logic — independent of the real site's content. `quickstart.md` covers
the three user stories end-to-end against the real `astro-site` project,
matching Article VIII's real-build-artifact verification philosophy for
the skill's procedure itself (which, being a Markdown flow rather than
code, isn't unit-testable the way the script is).

**Target Platform**: Developer machines running Claude Code, with Node.js
available for the responsive-check script and the target Astro project's
own build tooling already installed (`astro-site/node_modules`).

**Project Type**: Claude Code skill (Markdown procedure) + one companion
Node.js verification script — distinct in shape from feature 001 (PHP
plugin) and 002 (Python MCP server), consistent with this repo's
one-component-per-feature pattern (`README.md`).

**Performance Goals**: No hard SLA in the spec. Per-page cost is
dominated by the MCP tool calls (already addressed in 002) and one
headless-browser pass across 5 viewports; per-run cost includes exactly
one real `astro build`, not one per page (research.md #2).

**Constraints**: The skill MUST NOT implement its own HTTP calls to
WordPress — all WordPress data comes through the four existing MCP tools
(explicit user constraint). `astro-site/` is a fixed, hardcoded sibling
path within this repo, not a configurable parameter (explicit user
statement — no evidence a second target project exists or is planned).
`manifest.json` MUST live at `astro-site/` root, never under `skill/`.

**Scale/Scope**: One target Astro project (`astro-site/`) per repo; a run
may cover a single page or the full site (spec Assumptions).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Applies? | Assessment |
|---------|----------|------------|
| I. No se lee `_elementor_data` | Yes | PASS — the skill never touches WordPress data directly; it only ever consumes `get_rendered_structure`'s output, which 002's contract already guarantees is free of that field (FR-013). |
| II. HTML renderizado, no JSON interno | Yes | PASS — this feature *is* Article II's consumer: `get_rendered_structure` (rendered HTML/DOM) is the only layout source ever used for classification (FR-001). |
| III. Patrón finito de componentes | Yes | PASS — this feature *is* Article III's implementation: `manifest.json` is the finite, project-specific catalog; no-match pages are flagged for human decision, never forced (FR-002, FR-003, FR-012). |
| IV. REST nativo sin plugin cuando se pueda | N/A | Governs how WordPress data is fetched (001/002's concern); this skill only consumes already-built MCP tools, never talks to WordPress REST itself. |
| V. El plugin normaliza, no genera | Related | Written about the WordPress plugin specifically, but the same spirit — expose/apply, never invent — is honored here too: FR-012 forbids the skill from adding new manifest patterns on its own initiative; only a human decision does that. |
| VI. Responsive verificable | Yes | PASS — this feature is Article VI's literal implementation: automated `scrollWidth`/`clientWidth` overflow check at exactly the five specified viewports (320/375/768/1024/1920px), a hard gate before "done" (FR-005, FR-006). |
| VII. Formularios | N/A | Form structure/submission is out of scope for this feature (and for 002) — nothing here touches forms. |
| VIII. Verificación con build real | Yes | PASS — this feature is Article VIII's literal implementation: a real `npm run build` with the page present in `dist/` is a hard gate before "done" (FR-007, FR-008), not a proxy/mock check. |

No violations requiring justification — Complexity Tracking is empty.

**Post-Phase 1 re-check**: `data-model.md`, `contracts/*`, and
`quickstart.md` introduce one state file (`manifest.json`, project
config the skill applies but never invents) and no new WordPress access
path — all rows above still hold; no new violations introduced by the
design.

## Project Structure

### Documentation (this feature)

```text
specs/003-astro-migration-skill/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
skill/
├── SKILL.md                       # The procedure: frontmatter + the flow
│                                    #   (relevar → classify → populate/flag →
│                                    #   verify responsive → verify build → report;
│                                    #   plus the content-only sync path)
└── README.md                      # Pre-existing background doc; stays as the
                                     #   human-facing overview SKILL.md links to

astro-site/                        # Pre-existing target Astro project (sibling dir)
├── manifest.json                  # NEW — this feature's only persisted state
│                                    #   (page → pattern mapping + per-entry sync record)
├── scripts/
│   └── check-responsive.mjs       # NEW — Node/Playwright overflow check (FR-005, FR-006),
│                                    #   reuses astro-site's own @playwright/test devDependency
├── tests/
│   └── check-responsive.spec.mjs  # NEW — fixture-based test of the overflow logic
│                                    #   (@playwright/test, already a devDependency)
└── (existing scaffold: package.json, src/pages, src/components, src/layouts — untouched
    by this feature except for the migrated/updated .astro components each run produces)
```

**Structure Decision**: Two directories, per the user's explicit
constraints: `skill/` holds the procedure itself (`SKILL.md`) — no
programmatic source, since the skill's job is to orchestrate already-built
MCP tools, not reimplement anything. `astro-site/` (pre-existing, sibling
to `skill/`) holds both this feature's one piece of state
(`manifest.json`, explicitly required to live there, not under `skill/`)
and its one piece of supporting code (`scripts/check-responsive.mjs`),
placed there specifically to resolve `@playwright/test` from
`astro-site/node_modules` via normal Node module resolution — a script
under `skill/` would need its own separate `node_modules`/install for the
same dependency `astro-site/package.json` already declares
(research.md #1).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A — no Constitution Check violations were identified for this feature. | — | — |
