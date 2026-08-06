# Quickstart: WordPress-to-Astro Migration Skill

Validates the skill end-to-end against the real `astro-site/` project and
a real, reachable WordPress site. See `contracts/*.md` for exact
file/CLI shapes and `data-model.md` for the entities referenced below.

## Prerequisites

- The MCP server from `specs/002-wp-mcp-tools` configured and reachable
  for the Claude Code session (`WP_MCP_BASE_URL` pointed at a WordPress
  site with the companion plugin from `specs/001-wp-rest-normalizer`
  active).
- `astro-site/` dependencies installed (`npm install` inside `astro-site/`
  — `@playwright/test`'s browser binary may additionally need
  `npx playwright install chromium` the first time).
- At least one source page whose layout is expected to match a pattern
  you're willing to define in `astro-site/manifest.json` for this test,
  and at least one page whose layout you expect **not** to match anything
  yet.

## Setup

Start from an empty or near-empty `astro-site/manifest.json` (or none at
all — the skill treats a missing file as `{ "pages": [] }`, per
`contracts/manifest-schema.md`).

## Validation scenarios

1. **New page, matching pattern (US1)** — Define a manifest entry for a
   known pattern first (simulating a prior human decision), then invoke
   the skill on that page. Expect: `get_rendered_structure` called before
   any classification decision; the matched pattern's component populated
   with that page's content/media; the responsive check run at all five
   viewports against the real build's preview server; a real
   `npm run build` (or equivalent `astro build`) run with the page present
   in `dist/`; the page reported as migrated only if both checks passed.
2. **New page, no matching pattern (US2)** — Invoke the skill on a page
   with no corresponding manifest entry and a layout that doesn't match
   any existing pattern. Expect: the page is reported as flagged, no
   Astro file is created or modified for it, and (if run alongside
   scenario 1's page in the same batch) scenario 1's page still completes
   normally — one flagged page doesn't halt the rest of the run.
3. **Failing verification (US1 edge case)** — Deliberately populate a
   component with content that overflows at one viewport (or break the
   build). Expect: the page is **not** reported as migrated, and the
   report names exactly which viewport(s) failed or that the build
   failed.
4. **Content-only sync (US3)** — Edit the content of the page migrated in
   scenario 1 back on the WordPress site, then run the skill's sync path
   (no specific page argument, or explicitly requesting sync). Expect: no
   `get_rendered_structure` call for that page; `get_site_map` +
   `get_page_content` used to detect the change via `modified` date; only
   that page's content/media updated; its `pattern`/`astro_file` in
   `manifest.json` unchanged; a second sync run immediately after makes
   no further changes (nothing changed since the last sync).
5. **Missing manifest (edge case)** — Temporarily rename/remove
   `astro-site/manifest.json` and invoke the skill. Expect: it behaves as
   if every page is unmatched (flags them) rather than raising an error.

## Automated tests

```sh
cd astro-site
npx playwright test tests/check-responsive.spec.mjs
```

Runs the fixture-based overflow-detection tests (research.md #9) —
independent of the real WordPress site or the real migrated content,
useful for fast iteration on `scripts/check-responsive.mjs` itself.

## Known limitations

- The responsive check and the build check share one `astro build` per
  run (research.md #2) — if you want to verify the check truly runs
  against `dist/` and not a dev server, compare `check-responsive.mjs`'s
  results before and after a `dist/`-only change (e.g. editing built CSS
  directly) as a one-off sanity check; this isn't part of routine
  validation.
- This quickstart assumes `astro-site/`'s existing scaffold (from
  `npm create astro@latest`) as the starting point — a project with a
  substantially different structure isn't covered here.
