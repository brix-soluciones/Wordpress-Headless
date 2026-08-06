# Implementation Plan: WordPress REST Exposure Normalizer Plugin

**Branch**: `001-wp-rest-normalizer` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-wp-rest-normalizer/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A zero-dependency WordPress plugin that normalizes what the site's REST API
exposes: it forces `show_in_rest` for public custom post types and their ACF
fields that aren't already REST-readable, lets an administrator configure
which origins may make CORS requests, and adds one discovery endpoint
(`/wp-json/migracion/v1/site-map`) listing every publicly published item's
URL, type, and last-modified date. It never reads `_elementor_data` and
never creates, modifies, or deletes content — it only exposes what already
exists, using WordPress core APIs only.

## Technical Context

**Language/Version**: PHP 7.4+ (matches current WordPress minimum-supported
baseline; avoids syntax newer than what typical shared-hosting WP installs
run)

**Primary Dependencies**: None. WordPress core APIs only (hooks/filters,
REST API, Settings API, Options API). No Composer, no `vendor/`, no bundled
libraries — per explicit stack constraint. ACF field exposure integrates
conditionally (hooks into ACF's own filter only `if` ACF is active); ACF is
not a hard dependency.

**Storage**: WordPress `wp_options` table only, via the core Options API —
a single option stores the configured list of allowed CORS origins. No
custom database tables, no external storage.

**Testing**: Manual/scripted verification against a real WordPress
instance (WP-CLI + direct REST calls), documented in `quickstart.md`. No
PHPUnit/Composer-based automated suite, consistent with the zero-dependency
constraint — mirrors the constitution's Article VIII philosophy of
verifying against a real running artifact rather than an abstract test
harness.

**Target Platform**: Any standard self-hosted WordPress installation
(single site or per-site on multisite), PHP 7.4+, no assumptions about
active theme or hosting provider.

**Project Type**: Single project — one self-contained WordPress plugin.

**Performance Goals**: No hard SLA specified in the spec. Discovery
endpoint should return promptly for typical content volumes (up to a few
thousand published items) using a single native `WP_Query`/`get_posts`
pass — no N+1 per-item queries.

**Constraints**: Zero external runtime dependencies (no Composer, no
bundled libraries). Plugin MUST activate cleanly with no fatal errors and
no required setup step — CORS defaults to no allowed origins until an
administrator configures one, and REST-exposure normalization runs
automatically on activation with no configuration needed.

**Scale/Scope**: One plugin covering three capabilities (forced REST
exposure, configurable CORS, site-map discovery endpoint), applied
independently per WordPress installation it's activated on.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Applies? | Assessment |
|---------|----------|------------|
| I. No se lee `_elementor_data` | Yes | PASS — no code path in this plan reads or exposes `_elementor_data`; FR-008 makes this an explicit requirement, verified in `quickstart.md`. |
| II. HTML renderizado, no JSON interno | N/A | This article governs the layout-survey process (Astro/MCP side); this plugin does no layout survey. |
| III. Patrón finito de componentes | N/A | Governs Astro component generation; not applicable to a WordPress REST-exposure plugin. |
| IV. REST nativo sin plugin cuando se pueda | Yes | PASS — this plugin complements `/wp-json/wp/v2/*`, it never duplicates or replaces native REST output; it only fills gaps (CPTs/ACF without REST) and adds one new discovery endpoint. |
| V. El plugin normaliza, no genera | Yes | PASS — this feature *is* Article V's scope verbatim. FR-009 forbids creating/modifying/deleting content; the plugin's three capabilities are all exposure/normalization, not generation. |
| VI. Responsive verificable | N/A | Frontend/Astro concern; this plugin has no rendered UI in scope. |
| VII. Formularios | N/A | This plugin doesn't handle form submission runtime. |
| VIII. Verificación con build real | Adapted | The literal gate (`npm run build` + `dist/`) is Astro-specific. Equivalent discipline applied here: `quickstart.md` requires activating the plugin on a real WordPress instance and confirming actual REST responses, not just code review. |

No violations requiring justification — Complexity Tracking is empty.

**Post-Phase 1 re-check**: `data-model.md`, `contracts/*`, and
`quickstart.md` introduce one persisted value (allowed-origins option) and
three read-only/normalization contracts — nothing that reads
`_elementor_data`, generates content, or duplicates native REST output. All
rows above still hold; no new violations introduced by the design.

## Project Structure

### Documentation (this feature)

```text
specs/001-wp-rest-normalizer/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
plugin/
├── migration-toolkit.php           # Plugin bootstrap: header, activation checks, hooks includes/*
├── includes/
│   ├── functions.php               # Shared helper migration_toolkit_get_public_post_types(),
│   │                                #   used by both class-sitemap-endpoint.php and class-rest-normalizer.php
│   ├── class-rest-normalizer.php   # FR-003, FR-004, FR-005: forces show_in_rest for public
│   │                                #   CPTs and their ACF fields (conditional on ACF being active)
│   ├── class-cors.php              # FR-006, FR-007: reads allowed-origins option, sends
│   │                                #   Access-Control-Allow-Origin only for configured origins
│   └── class-sitemap-endpoint.php  # FR-001, FR-002, FR-010: registers and serves
│                                    #   GET /wp-json/migracion/v1/site-map
└── readme.txt                      # Standard WordPress plugin readme (installation, description)
```

**Structure Decision**: Single WordPress plugin, all within `plugin/`
(already the reserved location for this component per the repo's top-level
`README.md`). One bootstrap file plus one class per capability, matching
the plugin's three functional areas 1:1 so each can be understood, tested,
and — per Article IV/V — reasoned about independently. No `tests/` directory:
per the zero-Composer constraint, verification is the manual/scripted flow
in `quickstart.md` against a real WordPress instance, not a PHPUnit suite.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A — no Constitution Check violations were identified for this feature. | — | — |
