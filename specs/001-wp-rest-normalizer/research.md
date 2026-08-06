# Phase 0 Research: WordPress REST Exposure Normalizer Plugin

No `NEEDS CLARIFICATION` markers remained in the Technical Context — the
user supplied the stack constraint directly (PHP puro, sin dependencias
externas ni Composer, plug-and-play activation). This document records the
implementation-level decisions needed to turn that constraint plus the spec
into a concrete design, each with rationale and rejected alternatives.

## Decision: PHP 7.4+ as minimum target

**Rationale**: WordPress core itself still supports down to PHP 7.2 for
some LTS hosting, but 7.4 is the practical floor for typed properties and
arrow functions while staying compatible with the vast majority of
currently-active WordPress hosting. Avoids the plugin becoming the reason a
site can't activate it.

**Alternatives considered**: PHP 8.0+ only — rejected, would exclude a
meaningful share of real-world shared hosting still on 7.x, and the spec
requires activating on "any" standard WordPress installation.

## Decision: ACF integration is conditional, not a hard dependency

**Rationale**: The spec (FR-005) requires exposing ACF fields when they
exist, but the plugin must work on sites without ACF installed at all (spec
scope is about content types/fields "attached to content types that are
readable through the REST API" — sites without ACF simply have nothing to
normalize there). The plugin checks `class_exists('ACF')` (or hooks into
`acf/rest_api/field_settings/show_in_rest`, a filter that only fires if ACF
itself is active) before doing anything ACF-specific.

**Alternatives considered**: Requiring ACF as a hard dependency — rejected,
directly contradicts "sin dependencias externas" and "cualquier instalación
WordPress sin configuración adicional" (a site without ACF must still
activate cleanly and get full value from the other two capabilities).

## Decision: Allowed CORS origins stored as a single `wp_options` entry, configured via WordPress core Settings API

**Rationale**: FR-006 requires an administrator be able to configure
allowed origins. The Options API is core WordPress, adds no dependency, and
a single settings field (not a full dashboard) is the minimal surface that
satisfies FR-006 without contradicting "sin configuración adicional" for
*activation* — the plugin activates and both other capabilities work with
zero setup; only CORS requires an explicit opt-in per origin, and it fails
closed (no origins allowed) until configured, per the spec's Assumptions.

**Alternatives considered**:
- A PHP-level filter (`apply_filters('migration_toolkit_cors_origins', [])`)
  instead of an admin UI — rejected as the sole mechanism because it would
  require the site administrator to edit code, which is a materially higher
  bar than FR-006 implies; kept internally as an optional escape hatch a
  developer can still use, but not the primary configuration path.
- A full "estado de migración" admin dashboard (as sketched in
  `plugin/README.md`) — out of scope for this feature; nothing in
  `spec.md`'s functional requirements calls for a status dashboard. Noted
  as a candidate for a future feature spec, not built here.

## Decision: No PHPUnit/Composer-based automated test suite

**Rationale**: Standard WordPress plugin testing (`wp-phpunit`,
`yoast/wp-test-utils`) is installed via Composer, which directly conflicts
with the "sin dependencias externas ni Composer" constraint if those
dev-dependencies end up expected as part of the delivered plugin's
workflow. Verification instead follows the constitution's Article VIII
spirit: prove the feature works against a real running WordPress instance.
`quickstart.md` defines this as an explicit, repeatable script (WP-CLI +
`curl` against the REST API).

**Alternatives considered**: Composer-installed PHPUnit as a dev-only
dependency (never shipped) — reasonable in many WP projects, but rejected
here because the user's stated constraint didn't distinguish "shipped" vs
"dev" dependencies, and a zero-Composer repository (no `composer.json` at
all) is simpler to reason about and matches the explicit instruction.

## Decision: Site-map endpoint built on a single `WP_Query`/`get_posts` pass across all public post types

**Rationale**: FR-010 requires last-modified dates to reliably reflect true
modification time, and the endpoint must return promptly (no stated SLA,
but no N+1 query pattern should be introduced for a few thousand items).
Querying all public post types in one pass with `post_status=publish` and
selecting only the fields needed (URL, type, modified date) keeps this to a
single database round-trip class of query, using only `WP_Query` /
`get_post_types( ['public' => true] )` — both core APIs.

**Alternatives considered**: Per-post-type separate REST sub-endpoints —
rejected, spec (FR-001) calls for "a single discovery endpoint," and
splitting it would push the diffing/aggregation work onto the client for no
benefit.
