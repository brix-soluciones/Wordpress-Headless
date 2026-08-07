# Quickstart: Pattern Authoring Assistant Skill

Validates the feature against a real, reachable WordPress site. See
`contracts/draft-output.md` for the exact output shape and
`data-model.md` for the entities referenced below.

## Prerequisites

- The MCP server from `specs/002-wp-mcp-tools` configured and reachable
  for the Claude Code session, pointed at a WordPress site with the
  companion plugin (`specs/001-wp-rest-normalizer`) active.
- A page on that site with a distinctive layout — ideally one the
  migration skill (`specs/003-astro-migration-skill`) would flag (no
  manifest entry for it).

## Setup

None beyond the MCP prerequisite above — this tool has no dependencies
or configuration of its own (Technical Context: no supporting code).

## Validation scenarios

1. **Draft from a real page (US1, US2)** — invoke the tool with that
   page's URL or slug. Expect: `get_site_map()` called to resolve its
   `id` before anything else (research.md #4); `get_rendered_structure`
   and `get_page_content` called before any file is written;
   `astro-site/.pattern-drafts/<slug>/component.astro` and `page.astro`
   both produced; `component.astro` visibly reflects the source page's
   actual layout (sections/structure recognizable when compared side by
   side with the live page); `page.astro` matches
   `contracts/draft-output.md`'s required shape exactly (single import,
   single `props` object, single render line).
2. **Page not found (edge case)** — invoke with a URL/slug not present in
   `get_site_map()`'s results. Expect: a clear error, no files written.
3. **Existing draft (edge case)** — run scenario 1 twice for the same
   page without deleting the output in between. Expect: the second run
   stops and reports that a draft already exists at that path, rather
   than overwriting it.
4. **Promotion is manual (US1 acceptance scenario 3)** — after scenario
   1, confirm neither `src/components/`, `src/pages/`, nor
   `astro-site/manifest.json` changed at all — only files under
   `.pattern-drafts/` exist. Manually copy `component.astro` into
   `src/components/` and adapt `page.astro` into `src/pages/`, add the
   corresponding entry to `astro-site/manifest.json`, then confirm the
   migration skill's next run (per `specs/003-astro-migration-skill/quickstart.md`
   scenario 1) can populate that page normally — proving the promoted
   shape really is what 003 expects, not just documented as such.

## Known limitations

- Not executable in an environment without a reachable WordPress site —
  same limitation every real-instance scenario across specs 001–003 has
  had in this repo so far.
- Draft quality (does the component actually look right) is inherently
  a judgment call for the human reviewing it — there is no automated
  pass/fail check for this beyond the structural shape of `page.astro`
  (contract) and the absence of writes outside `.pattern-drafts/` (FR-004).
