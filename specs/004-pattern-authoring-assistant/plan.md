# Implementation Plan: Pattern Authoring Assistant Skill

**Branch**: `004-pattern-authoring-assistant` | **Date**: 2026-08-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-pattern-authoring-assistant/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A second, separate Claude Code skill — never auto-triggered, never part of
`specs/003-astro-migration-skill`'s loop — that a human invokes by hand
with a page identifier (typically one just flagged by the migration
skill) to get a reviewable first draft: a pattern component plus the page
file that wires it to that page's real content, both written to a
staging location outside the project's trusted `src/`. It reuses
`specs/002-wp-mcp-tools`'s tools (including `get_site_map` for id
resolution, the same approach 003 already uses) and needs no code of its
own — the "drafting" itself is Claude's own generation, guided by the
skill's process constraints, not a deterministic algorithm the way 003's
classify/verify logic is. Promoting a draft into `src/` and registering
it in `astro-site/manifest.json` stay explicit, separate human actions
this tool never performs.

## Technical Context

**Language/Version**: N/A — a Markdown Claude Code skill (`SKILL.md`),
same artifact type as `specs/003-astro-migration-skill`. Unlike 003, this
feature introduces **no supporting code** (no script analogous to
`check-responsive.mjs`) — drafting a component is Claude's own generation
task using its native file-writing ability, not a deterministic procedure
to implement.

**Primary Dependencies**: None new. Reuses the MCP tools from
`specs/002-wp-mcp-tools` (`get_site_map` for id resolution — same
approach as 003's Preámbulo — `get_page_content`, `get_rendered_structure`,
`get_media_original`), invoked natively through Claude Code once that
server is configured for the session, exactly as 003 does.

**Storage**: One new on-disk convention this tool owns: draft output at
`astro-site/.pattern-drafts/<slug>/` (`component.astro` + `page.astro`).
Not part of the Astro build (lives outside `src/`), and gitignored
(research.md #1) — drafts are provisional by definition, promoting one
into `src/` is the explicit human action that makes it permanent.
Nothing else is persisted; this tool never writes to
`astro-site/manifest.json` (FR-006).

**Testing**: No automated test suite — this feature has no executable
code of its own to test. Verified via `quickstart.md`'s manual scenarios
plus structural review confirming the drafted `page.astro`'s prop-passing
shape matches what `specs/003-astro-migration-skill`'s "Poblar componente"
section expects to find already in place (research.md #6) — that
structural match is the real correctness bar for this feature, more than
any single draft's content quality.

**Target Platform**: Developer machines running Claude Code, with the
`specs/002-wp-mcp-tools` MCP server configured for the session — same
platform as 003.

**Project Type**: Claude Code skill (pure Markdown procedure, no
supporting code) — simpler in shape than 003 (skill + one script).

**Performance Goals**: No hard SLA. Bounded by the same MCP tool call
latency as any 002 consumer, plus Claude's own generation time for the
draft — not a concern this plan needs to engineer for.

**Constraints**: MUST NOT run automatically or be invoked as part of
003's flow (FR-005). MUST NOT write to `astro-site/manifest.json`
(FR-006). MUST NOT write directly into `src/components/` or `src/pages/`
(FR-004) — staging location only. MUST NOT run responsive or build
verification (FR-007) — that stays 003's job, applied once a draft is
promoted and its manifest entry exists.

**Scale/Scope**: One page's draft per invocation, human-paced — this
tool has no whole-site batch mode (unlike 003's Preámbulo); drafting
many patterns unsupervised would undermine the human-review point of the
whole feature.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Applies? | Assessment |
|---------|----------|------------|
| I. No se lee `_elementor_data` | Yes | PASS — this tool only ever consumes `get_rendered_structure`'s output (already guaranteed free of that field by 002's contract); it never touches WordPress directly. |
| II. HTML renderizado, no JSON interno | Yes | PASS — the draft is built from `get_rendered_structure`'s rendered-DOM outline, the same source 003 uses; Article II's philosophy applies equally to this human-assisted step. |
| III. Patrón finito de componentes | Yes | PASS, and this feature exists specifically in service of this article: it drafts, a human decides, nothing joins the trusted catalog without that explicit, separate action (FR-004, FR-006, FR-009) — the "never forced" guarantee is about the *unattended* pipeline (003), which this tool is deliberately not part of. |
| IV. REST nativo sin plugin cuando se pueda | N/A | Governs how WordPress data is fetched (001/002's concern); this tool only consumes already-built MCP tools. |
| V. El plugin normaliza, no genera | Related | Written about the WordPress plugin specifically; this tool's own, tighter version of that discipline is FR-004/FR-006/FR-009 — draft output is never trusted or registered without an explicit human action, however generative the drafting step itself is. |
| VI. Responsive verificable | N/A (by design) | This tool explicitly does not run the responsive check (FR-007) — it stays 003's gate, applied once a promoted draft has a manifest entry. Not a gap: the system-level guarantee still holds, just not from this tool. |
| VII. Formularios | N/A | Out of scope, same as 002/003. |
| VIII. Verificación con build real | N/A (by design) | Same reasoning as Article VI — this tool never runs a build check (FR-007); 003 still does, downstream, once a draft is promoted. |

No violations requiring justification — Complexity Tracking is empty.

**Post-Phase 1 re-check**: `data-model.md`, `contracts/*`, and
`quickstart.md` introduce one new on-disk convention (the gitignored
`.pattern-drafts/` staging location) and no new WordPress access path,
no manifest writes, and no verification logic — all rows above still
hold; no new violations introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/004-pattern-authoring-assistant/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pattern-assistant/                 # NEW — own top-level directory, matching the
│                                    #   one-directory-per-component pattern
│                                    #   plugin/, mcp/, skill/ already follow
├── SKILL.md                       # The procedure: frontmatter + drafting flow
└── README.md                      # Short pointer doc (same role as skill/README.md)

astro-site/                        # Pre-existing target Astro project
├── .gitignore                     # UPDATED — add .pattern-drafts/
└── .pattern-drafts/                # Runtime output, not a repo deliverable —
    └── <slug>/                    #   created per-invocation by the skill itself,
        ├── component.astro        #   not authored as part of this feature's tasks
        └── page.astro

README.md                          # UPDATED — "tres componentes" → four,
                                     #   add pattern-assistant/ to the structure list
```

**Structure Decision**: A fourth top-level directory, `pattern-assistant/`,
kept separate from `skill/` (003) per the user's explicit "skill nueva y
separada" — a distinct SKILL.md/command, not a mode within 003's. No
`src/`/`tests/` split: there's no code to organize this way (Technical
Context — no supporting script, unlike 003's `check-responsive.mjs`).
The one runtime artifact this tool produces (`.pattern-drafts/`) lives
under `astro-site/`, next to the other runtime state 003 already owns
there (`manifest.json`), but is gitignored since drafts are provisional
by definition — promoting one into `src/` is what makes it permanent.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A — no Constitution Check violations were identified for this feature. | — | — |
