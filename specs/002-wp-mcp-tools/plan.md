# Implementation Plan: WordPress MCP Tools Server

**Branch**: `002-wp-mcp-tools` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-wp-mcp-tools/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A standalone Python MCP server, invoked over stdio, that exposes four
read-only tools an agent uses to survey a WordPress site during migration:
`get_site_map` (the companion plugin's discovery endpoint), `get_page_content`
(plain content + ACF via native `/wp/v2/posts`/`/wp/v2/pages`),
`get_rendered_structure` (a simplified layout outline of a public URL,
plain-fetch first with a headless-render fallback, never `_elementor_data`),
and `get_media_original` (full-resolution media by slug via
`/wp/v2/media?slug=`). The target site's base URL is read from an
environment variable, never hardcoded. The server holds no state beyond one
shared HTTP client and produces no target-framework code — only data.

## Technical Context

**Language/Version**: Python 3.11+ (matches the official MCP SDK's async
patterns; local dev environment already has 3.14 installed, which is
forward-compatible)

**Primary Dependencies**: `mcp` (official Python MCP SDK — stdio server +
tool registration), `httpx` (async HTTP client against the WordPress REST
API), `beautifulsoup4` (HTML parsing for `get_rendered_structure`'s
simplified outline), `playwright` (lazy, fallback-only headless rendering
for JS-dependent pages). No additional web framework — the server speaks
MCP over stdio only, per explicit stack constraint.

**Storage**: N/A — the server is stateless beyond one shared, reused
`httpx.AsyncClient` for connection pooling; nothing is persisted between
tool calls or process restarts.

**Testing**: `pytest` + `pytest-asyncio` for tool-handler logic, `respx` to
fake WordPress REST responses (posts/pages/media/site-map) without a real
WP instance. `quickstart.md` additionally covers a real-instance smoke test
against a live WordPress site, matching Article VIII's build-verification
spirit for this project type.

**Target Platform**: Any host able to run Python 3.11+ and spawn a
subprocess communicating over stdio — this server is launched by an MCP
client (e.g. Claude Desktop/Code configuration), not deployed as a network
service.

**Project Type**: Single project — a standalone Python MCP server (`mcp/`
in this repo).

**Performance Goals**: No hard SLA in the spec. Each tool call is bound by
one (or, for the rendering fallback, at most two) round-trip(s) to the
target WordPress site; the server itself adds negligible overhead beyond
that network wait.

**Constraints**: stdio transport only, no bundled web framework; the
target site's base URL MUST come from an environment variable and MUST
NOT be hardcoded (FR-007); MUST NOT read or expose `_elementor_data`
(FR-005); MUST NOT require or accept WordPress credentials (FR-008); MUST
NOT emit target-framework code (FR-009).

**Scale/Scope**: One configured WordPress site per running server process;
four tools, each independently callable (FR-011).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Applies? | Assessment |
|---------|----------|------------|
| I. No se lee `_elementor_data` | Yes | PASS — no tool, including `get_rendered_structure`, ever reads or forwards that field (FR-005); enforced by construction (the outline is built from resolved HTML/DOM, which has no path to that internal field). |
| II. HTML renderizado, no JSON interno | Yes | PASS — `get_rendered_structure` is this article's implementation: it resolves the public page's actual rendered HTML (plain fetch, headless-render fallback only when needed per FR-003) rather than any page-builder-internal representation. |
| III. Patrón finito de componentes | N/A | Matching pages to component patterns is the consuming skill's job (future feature); this server only supplies the structural outline data it needs to do that. |
| IV. REST nativo sin plugin cuando se pueda | Yes | PASS — `get_page_content` reads `/wp/v2/posts` and `/wp/v2/pages` directly; the companion plugin (001) is only required for `get_site_map`'s discovery endpoint and for CPT/ACF exposure beyond WordPress defaults, not for reading native post/page content. |
| V. El plugin normaliza, no genera | Related | This article is written about the WordPress plugin specifically, but its spirit — expose/normalize, never generate — is honored here too: FR-009 forbids this server from producing any target-framework code; it only returns source-site data. |
| VI. Responsive verificable | N/A | Frontend/Astro-build concern; this server does no rendering of output components. |
| VII. Formularios | N/A | `get_form_structure` (form structure discovery) is explicitly out of scope for this feature per the spec's Input — a candidate for a future feature, not this plan. |
| VIII. Verificación con build real | Adapted | The literal gate (`npm run build` + `dist/`) is Astro-specific. Equivalent discipline here: `quickstart.md` requires running the server and calling all four tools against a real, reachable WordPress site (with the companion plugin installed), not just passing mocked unit tests. |

No violations requiring justification — Complexity Tracking is empty.

**Post-Phase 1 re-check**: `data-model.md`, `contracts/*`, and
`quickstart.md` introduce no new state, no `_elementor_data` access path,
and no code-generation responsibility — all four tool contracts are
read-only data retrieval. All rows above still hold; no new violations
introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/002-wp-mcp-tools/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
mcp/
├── README.md
├── pyproject.toml                  # Package metadata + console-script entry point
├── src/
│   └── wp_mcp_server/
│       ├── __init__.py
│       ├── server.py                # FastMCP instance, tool registration, stdio entrypoint (main())
│       ├── config.py                # Reads WP_MCP_BASE_URL env var; fails fast if unset (FR-007)
│       ├── wp_client.py             # Shared httpx.AsyncClient; thin wrappers over WP REST calls
│       ├── tools/
│       │   ├── site_map.py          # get_site_map — FR-001
│       │   ├── page_content.py      # get_page_content — FR-002, FR-010
│       │   ├── rendered_structure.py# get_rendered_structure — FR-003, FR-004, FR-005, FR-010
│       │   └── media_original.py    # get_media_original — FR-006, FR-010
│       └── html_outline.py          # HTML → simplified structural outline (used by rendered_structure)
└── tests/
    ├── conftest.py                  # respx fixtures faking the WP REST API
    ├── test_site_map.py
    ├── test_page_content.py
    ├── test_rendered_structure.py
    └── test_media_original.py
```

**Structure Decision**: Single Python project under the repo's existing
`mcp/` directory (already reserved for this component per the top-level
`README.md`; its `.venv` and `README.md` predate this plan and are
retained). One module per tool under `tools/`, matching the four
capabilities 1:1 so each can be read, tested, and reasoned about
independently — mirroring the plugin's (001) one-class-per-capability
structure. `wp_client.py` centralizes the single shared `httpx.AsyncClient`
and the two native-REST call patterns (`/wp/v2/posts|pages`,
`/wp/v2/media`) so no tool module talks to `httpx` directly.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A — no Constitution Check violations were identified for this feature. | — | — |
