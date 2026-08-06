# Quickstart: WordPress MCP Tools Server

Validates the feature end-to-end against a real, reachable WordPress site.
See `contracts/*.md` for exact tool input/output shapes and
`data-model.md` for the entities referenced below.

## Prerequisites

- Python 3.11+.
- A WordPress site reachable over HTTP(S), with the companion normalizer
  plugin (`specs/001-wp-rest-normalizer`) installed and active — required
  for `get_site_map` and for reading any custom-post-type/ACF data beyond
  WordPress's own defaults.
- At least one published post or page with an ACF field attached, to
  exercise `get_page_content`'s `custom_fields` path.
- At least one media item with a known slug, to exercise
  `get_media_original`.

## Setup

```sh
cd mcp
python -m venv .venv          # if not already present
.venv/Scripts/pip install -e ".[dev]"
```

Configure the target site (never hardcoded, per FR-007):

```sh
set WP_MCP_BASE_URL=https://origin-site.example
```

## Run

Start the server directly over stdio via the installed console script
(verified: `pip install -e ".[dev]"` registers `wp-mcp-server` on `PATH`
inside the venv):

```sh
.venv/Scripts/wp-mcp-server
```

Or `python -m wp_mcp_server.server`. (The SDK's `mcp dev` inspector CLI
needs the extra `mcp[cli]` — `pip install "mcp[cli]"` — not declared as a
dependency here since this server only needs the stdio runtime.)

Or point an MCP client (Claude Desktop/Code config) at the console-script
entry point:

```json
{
  "mcpServers": {
    "wp-migration": {
      "command": "wp-mcp-server",
      "env": { "WP_MCP_BASE_URL": "https://origin-site.example" }
    }
  }
}
```

## Validation scenarios

1. **`get_site_map`** — call with no arguments. Expect an `items` array
   covering every known published post/page/CPT on the site, each with
   `url`, `type`, `modified` (contract: `get_site_map.md`; US1).
2. **`get_page_content`** — call with the numeric id of the known
   post/page from Prerequisites. Expect `title`, `content`, and a
   `custom_fields` object containing the known ACF field (US2, scenario
   2). Then call with an id belonging to a draft or a nonexistent id;
   expect a raised "not found" error, not a partial response (US2
   edge case).
3. **`get_rendered_structure`** — call with that same item's public URL.
   Expect a `rendering_method` of `"fetch"` for a normal WordPress page,
   and an `outline` tree with no field resembling `_elementor_data` at
   any depth (US3). Then call with a URL on a different host; expect a
   raised error, not a fetched response (US3 edge case).
4. **`get_media_original`** — call with the known media slug from
   Prerequisites. Expect `source_url` to point at the original uploaded
   file (compare against the Media Library's "Full Size" URL, not a
   thumbnail) (US4). Then call with a slug that matches nothing; expect a
   raised "not found" error (US4 edge case).
5. **Reconfigure to a second site** — change only `WP_MCP_BASE_URL` and
   repeat scenario 1; expect it to work with no code change (SC-005).

## Automated tests

```sh
.venv/Scripts/pytest
```

Runs the `respx`-backed unit tests (`tests/test_*.py`) that fake the
WordPress REST API for each tool, independent of a live site — useful for
fast iteration between real-instance smoke tests.

## Known limitations

- `get_rendered_structure`'s headless-render fallback (research.md #3)
  requires a Playwright browser binary to be installed
  (`playwright install chromium`) the first time it's actually exercised;
  the plain-fetch path has no such requirement and is expected to cover
  the large majority of WordPress/Elementor pages.
- This server assumes a single configured site per process — running
  against multiple sites concurrently means running multiple server
  processes with different `WP_MCP_BASE_URL` values, not a runtime switch
  (spec Assumptions).
