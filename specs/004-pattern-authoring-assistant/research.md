# Phase 0 Research: Pattern Authoring Assistant Skill

The user-supplied constraints (separate skill, human-invoked only, never
part of 003's loop, never touches `manifest.json`, drafts from
`get_rendered_structure` + `get_page_content`) fix the major decisions.
This document resolves the remaining implementation-level choices, each
traced back to a spec requirement or a design consistency point with
`specs/003-astro-migration-skill`.

## 1. Staging location for drafts

**Decision**: `astro-site/.pattern-drafts/<slug>/`, containing
`component.astro` (the pattern component draft) and `page.astro` (the
page-wiring draft). Added to `astro-site/.gitignore`.

**Rationale**: Living outside `src/` entirely (not e.g.
`src/components/.drafts/`) guarantees zero chance of an unreviewed draft
ever being swept into an Astro build by accident — `astro build` only
ever looks under `src/`. The dot-prefix follows this project's own
convention (`.astro/` is already a git-ignored, tooling-owned directory
at the same level). Gitignoring matches how this project already treats
generated/disposable output (`dist/`, `.astro/`, `node_modules/` — see
root `.gitignore`) — a draft is provisional by definition (FR-004, FR-009);
promoting it into `src/` is the explicit human action that makes it a
real, trusted project artifact, and only from that point does it deserve
version history.

**Alternatives considered**: A location under `src/` with a naming
convention (e.g. `src/components/_drafts/`) — rejected, relies on every
tool in the build chain correctly ignoring an underscore/dot prefix
inside `src/`, a weaker guarantee than being outside `src/` altogether.
Keeping drafts tracked in git — rejected; nothing distinguishes an
abandoned draft from a promoted one in history until the human acts, so
gitignoring matches the "not yet real" status more honestly.

## 2. No supporting code

**Decision**: This feature ships zero executable code — no script
analogous to 003's `check-responsive.mjs`. Drafting a component is
Claude's own generation task (informed by the fetched layout/content),
directed by `SKILL.md`'s process constraints, not a deterministic
algorithm this plan needs to specify.

**Rationale**: 003's one piece of code exists because "detect horizontal
overflow" is a well-defined, deterministic check with one right answer —
worth writing once, testing, and reusing. "Draft a plausible Astro
component from a page's layout" has no such single correct algorithm;
that's precisely why the constitution keeps it a human (now
human+AI-assisted) judgment call rather than something 003's automated
loop attempts (Article III's own rationale — "la generación genérica de
layout es un problema abierto y no confiable").

## 3. New skill's own top-level directory

**Decision**: `pattern-assistant/` at the repo root, holding `SKILL.md`
and a short `README.md` — not a file or subdirectory inside `skill/`
(003's directory).

**Rationale**: The user explicitly asked for "skill nueva y separada."
Beyond just a distinct command, giving it its own top-level directory
matches this repo's existing one-directory-per-component convention
(`plugin/`, `mcp/`, `skill/`) and keeps 003's directory exclusively about
the unattended migration/sync procedure — no risk of a future reader
mistaking this tool's files for part of that loop.

## 4. Id/slug resolution reuses 003's exact approach

**Decision**: Given a human-supplied URL or slug, call `get_site_map()`
and resolve it the same way `specs/003-astro-migration-skill`'s
Preámbulo already does (derive `wp_slug` from each entry's `url`, match
against the input) to obtain the `id` `get_page_content` requires.

**Rationale**: This is the same problem 003 already solved (and the same
gap that `specs/001-wp-rest-normalizer`'s T010b fixed by adding `id` to
`SiteMapEntry`) — reusing the identical approach means no new resolution
logic to design, test, or keep consistent with 003's, and this tool
benefits from that earlier fix for free.

## 5. Draft page file's prop-passing shape must match 003's expectations

**Decision**: `page.astro`'s draft MUST import the drafted pattern
component and pass this page's content via a single spread `props`
object (`<Component {...props} />`), the same shape
`specs/003-astro-migration-skill`'s "Poblar componente" section
documents as what it expects to already find in place before it can
populate a page.

**Rationale**: This is the actual interface contract between the two
features (see `contracts/draft-output.md`) — 003 never touches a page
file's import/render structure, only rewrites its `props` object. If a
promoted draft didn't already match that shape, 003 would have nothing
correct to rewrite the first time it processes that page after a human
adds its manifest entry.

## 6. Image handling reuses 003's slug-derivation heuristic

**Decision**: When the draft references an image found in the page's
content or layout, derive its `get_media_original` slug the same way
003's "Poblar componente" already does — strip the file extension and
any WordPress size suffix (`-{width}x{height}`) from the filename.

**Rationale**: Same problem, same correct answer, already worked out and
documented in 003 (`specs/003-astro-migration-skill/research.md`
equivalent reasoning, captured directly in its `SKILL.md`) — no reason to
re-derive or risk drifting from it.

## 7. Overwrite protection

**Decision**: Before writing anything, check whether
`astro-site/.pattern-drafts/<slug>/` already exists. If it does, stop and
tell the human rather than overwriting (FR-009) — let them decide whether
to look at the existing draft, delete it themselves, or pick a different
slug/location.

**Rationale**: Directly implements FR-009's edge case; matches this
project's consistent stance (001, 002, 003 all took the same position at
their own layer) of never silently guessing or clobbering when something
unexpected is already present.
