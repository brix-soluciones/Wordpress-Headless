# Phase 0 Research: WordPress MCP Tools Server

The user-supplied stack (Python, official `mcp` SDK, stdio-only, `httpx`,
configurable base URL via env var) fixes the major technical decisions.
This document resolves the remaining implementation-level choices needed
before design, each traced back to a spec requirement or edge case.

## 1. MCP server shape

**Decision**: Use the official `mcp` SDK's high-level server class,
registering the four tools as decorated async functions, running over
stdio via its built-in stdio entrypoint. **Verified against the actually
installed `mcp` 2.0.0 package** (not assumed from memory): this class is
`MCPServer`, importable as `from mcp.server import MCPServer` — the
`mcp.server.fastmcp.FastMCP` name from older SDK versions no longer
exists in 2.0.0. Its `.tool()` decorator, `.run(transport="stdio")`
(the default), and exception-to-protocol-error behavior (research.md #7)
were confirmed to work as expected with a throwaway script before writing
`server.py`.

**Rationale**: `MCPServer` is the SDK's batteries-included API for exactly
this shape — a small, fixed set of tools with typed inputs/outputs and no
custom protocol extensions. It removes MCP-protocol boilerplate (message
framing, capability negotiation) that this feature has no need to control
directly.

**Alternatives considered**: The SDK's low-level `Server` class — gives
manual control over the protocol layer, which this feature doesn't need
(FR-011 only requires four independent, typed tools, not custom protocol
behavior). Rejected as unnecessary complexity.

## 2. HTTP client concurrency model

**Decision**: `httpx.AsyncClient`, instantiated once at server startup and
reused across all tool calls (connection pooling), passed into each tool
module rather than constructed per call.

**Rationale**: FastMCP tool handlers run inside the SDK's asyncio event
loop; an async client lets a slow WordPress response yield the loop
instead of blocking it. A single shared client also avoids re-establishing
TCP/TLS per call.

**Alternatives considered**: `httpx.Client` (sync) — simpler code, but
would block the event loop for the duration of every WordPress round trip;
since the user explicitly praised httpx's sync/async support without
mandating one, async was chosen as the better fit for the SDK's runtime
model, not because sync was disqualified.

## 3. `get_rendered_structure` plain-fetch vs. render fallback (FR-003)

**Decision**: Always attempt a plain `GET` first. Parse the response with
`<script>`, `<style>`, `<noscript>`, and comment nodes stripped, then
treat the result as "insufficient" (triggering a headless-render
fallback) iff:

- **(A)** `<body>` has fewer than **10 element descendants**, **AND**
- **(B)** `<body>`'s visible text (all text nodes concatenated, whitespace
  collapsed and trimmed) is shorter than **200 characters**

**OR**

- **(C)** an element matching `#root`, `#app`, `#__next`, `#___gatsby`, or
  `[data-reactroot]` exists and has **zero direct element children**

i.e. fallback fires on `(A AND B) OR C`. Only then, lazily launch a
headless browser (Playwright, per the constitution's own suggestion) to
resolve the final DOM and re-parse from that instead.

A and B are combined (not evaluated alone) so a legitimately short,
server-rendered page (e.g. a minimal "under construction" page) doesn't
false-positive into an unnecessary render. C is evaluated independently
because an empty SPA-root shell can still have some surrounding
server-rendered markup (nav/footer) that would keep it out of A+B while
still being the wrong content to hand the agent.

**Rationale**: WordPress + Elementor pages are server-rendered PHP output
almost universally — the plain fetch is expected to succeed in the
overwhelming majority of calls, so the heuristic keeps the common path
fast and dependency-light, while the fallback exists for the rare
JS-heavy exception FR-003 explicitly calls out.

**Alternatives considered**: Always render with a headless browser —
rejected as unnecessary latency/dependency weight for pages that don't
need it. Plain fetch only, no fallback — rejected, contradicts the
resolved FR-003 (hybrid was the chosen answer during clarification).

## 4. Simplified structural outline shape (FR-004)

**Decision**: Parse the resolved HTML with `BeautifulSoup` (`html.parser`
backend — pure Python, no system dependency), strip `<script>`, `<style>`,
and comment nodes, then emit a nested outline: each node carries tag name,
`id`, `class`, and direct text (recursing into children) as plain
dict/list structures — no raw markup, scripts, or styles included.

**Rationale**: A real parser is more robust than regex-based extraction
against arbitrary real-world HTML, and `html.parser` avoids adding a
compiled dependency (`lxml`) for a single-page-at-a-time operation where
parse speed isn't a bottleneck.

**Alternatives considered**: Returning raw HTML (rejected — the
clarification session explicitly chose the simplified outline to keep
responses token-light for the consuming agent). `lxml` backend — faster,
but adds a C-extension dependency for no measurable benefit at this scale.

## 5. `get_page_content` post/page resolution (FR-002)

**Decision**: Given an identifier, request `/wp/v2/posts/{id}`; on a 404,
fall back to `/wp/v2/pages/{id}`. Surface the `acf` key from the response
body (if present) under a `custom_fields` field in the tool's return
value; omit it entirely when absent (edge case: ACF not installed/exposed).

**Rationale**: WordPress post IDs are unique across all post types in a
single `wp_posts` table, so an ID can only ever resolve against exactly
one of `posts`/`pages` — trying one then the other on 404 is unambiguous,
not a guess. `acf` is the conventional key ACF-to-REST exposure adds to a
post/page response once `show_in_rest` is forced (the companion plugin's
job, not this server's).

**Alternatives considered**: Requiring the caller to specify the content
type — rejected, adds friction the spec doesn't ask for (FR-002 only
requires "by its identifier").

## 6. `get_media_original` resolution (FR-006, edge case: duplicate slugs)

**Decision**: `GET /wp/v2/media?slug={slug}`; return the first item's
`source_url` (the full/original file, never a `media_details.sizes.*`
variant). Empty result array → not-found error (FR-010). Multiple items
(a WordPress edge case only reachable by direct DB manipulation, since WP
itself auto-suffixes duplicate slugs) → return the first item; documented
as a known limitation, not specially handled.

**Rationale**: `source_url` is WordPress's own field for the original
upload; sizes live under a separate, explicitly excluded key. Slug
uniqueness within the `attachment` post type is a WordPress-enforced
invariant in normal operation, so the multiple-match branch is a
documented rather than engineered-around edge case.

## 7. Error surfacing convention

**Decision**: Tool handlers raise ordinary Python exceptions
(`ValueError` for "not found"/"out of scope" cases, e.g. an unknown id or
a `get_rendered_structure` URL outside the configured site's host;
`RuntimeError`/`httpx` exceptions for unreachable-site failures) with a
descriptive message. `MCPServer` converts an unhandled exception into an
MCP-protocol error result for the calling agent — verified directly: the
SDK wraps the raised exception in its own `ToolError` internally, which
the stdio/session layer (not the in-process `call_tool` Python API used
in this verification) turns into the client-facing error result.

**Rationale**: This matches FR-010 (a clear, distinguishable error/"not
found" result) using the protocol's own error channel, rather than
inventing a bespoke "ok but actually an error" payload shape that the
agent would have to know to check for on every call.

**Alternatives considered**: A custom `{"error": ...}` return envelope on
success-shaped responses — rejected, harder for the agent to distinguish
from real data at a glance, and duplicates what MCP's error channel
already provides.

## 8. URL scoping for `get_rendered_structure` (edge case)

**Decision**: Before fetching, compare the requested URL's hostname
against the configured base URL's hostname (from `WP_MCP_BASE_URL`);
reject with a `ValueError` if they differ.

**Rationale**: Directly implements the spec's edge case: "the request
must be rejected rather than silently fetching an arbitrary external
page."

## 9. Testing approach

**Decision**: `pytest` + `pytest-asyncio` for async tool handlers, `respx`
to intercept `httpx.AsyncClient` calls and fake WordPress REST responses
(site-map, posts/pages, media) without a live site. `quickstart.md`
separately covers a real-WordPress-instance smoke test.

**Rationale**: `respx` is built specifically against `httpx`'s client
API (both sync and async), which keeps the fake-response layer aligned
with the actual client library in use rather than a generic HTTP mocking
tool.

**Alternatives considered**: `pytest-httpx` — a comparable option; `respx`
was chosen for its more direct `httpx.AsyncClient`-route-pattern API, not
because the alternative is unsuitable.

## 10. Packaging & entrypoint

**Decision**: `pyproject.toml` (PEP 621) defining the `wp_mcp_server`
package and a console-script entry point (`wp-mcp-server`), so an MCP
client config can launch it directly or via `python -m wp_mcp_server`.
`WP_MCP_BASE_URL` is read at startup; the server fails fast with a clear
message if it's unset or not a well-formed URL (FR-007).

**Rationale**: A console-script entry point is the standard way an
external MCP client process launches a Python stdio server without
needing to know the package's internal module layout.

## 11. Rendered-structure default scope, and why no `elementor-` class filter (FR-012)

**Decision**: By default (`selector=None`), `get_rendered_structure` roots
the outline at the page's `<main>` landmark, falling back to the full
`<body>` when no `<main>` exists. An optional `selector` (CSS selector)
lets the caller scope to anything else instead — including `"body"` for
the whole page, or `"header"`/`"footer"` to inspect chrome deliberately.
`selector` matching nothing raises rather than silently returning
something else. This scoping decision is evaluated **after** the
plain-fetch-vs-headless-render fallback rule (#3 above), which still
always runs against the full `<body>` — the fallback question ("did the
fetch actually work") is independent of which part of the page the
caller ultimately wants.

**Rationale**: Confirmed against a real site: without scoping, every
single-page call repeated identical header/nav/footer/comment-form markup
— pure token cost with zero per-page signal for the layout-pattern
matching this tool exists to support (constitution Article III). `<main>`
is the standard HTML landmark for "the part of the page that isn't
chrome," present on the vast majority of modern WordPress themes
(including Elementor-built pages), so it's a reliable default without
per-site configuration. The `selector` escape hatch keeps the tool able
to answer "what does the header look like" when that's genuinely what's
needed — just not as every call's default.

**Also confirmed against the same real site**: the page's `<body>` (not
`<main>`) carried Elementor's site-wide kit classes (`elementor-default`,
`elementor-kit-14`) even on content unrelated to Elementor. **Decision:
do not add an `elementor-`-prefix class filter to `html_outline.py`.**
Scoping to `<main>` by default already excludes `<body>`'s classes from
the returned tree, which resolves the specific noise observed. A blanket
prefix filter was rejected because Elementor's rendered HTML classes
(`elementor-section`, `elementor-widget-container`, etc.) *are* the real
structural signal for pages actually built with Elementor's page
builder — they are exactly how constitution Article II reads structure
from rendered HTML instead of `_elementor_data`. Stripping anything
`elementor-`-prefixed would remove that signal for the pages where it
matters most. If site-wide kit noise is still observed inside a
`<main>`-scoped (or explicitly `selector`-scoped) outline in the future,
the fix is a narrow, evidence-based exclusion for that specific observed
class/pattern — the same policy already applied to the plugin's
`elementor_library` post-type exclusion (`specs/001-wp-rest-normalizer`)
— not a speculative blanket rule added now.

**Alternatives considered**: Always returning the full `<body>`
(rejected — the token-cost problem this decision solves). A required
(non-optional) `selector` param with no default (rejected — adds friction
to the common case, where `<main>` is almost always the right answer).
Filtering `elementor-*` classes (rejected — see above).

## Note on existing `mcp/` scaffolding

`mcp/README.md` (pre-existing, before this plan) suggested a "Node +
`@modelcontextprotocol/sdk`" stack and additionally listed a
`get_form_structure(form_id)` tool. Both predate this spec/plan cycle:
the stack decision above supersedes the Node suggestion (per the user's
explicit direction for this feature), and `get_form_structure` is out of
scope for this feature per the spec's Input — a candidate for a future
feature, not this plan. The README is updated alongside this plan to
avoid leaving contradictory guidance in the repo.

The pre-existing `mcp/.venv` already has the `mcp` and `httpx`-family
packages installed (plus `uvicorn`/`starlette`, unused by this stdio-only
plan — likely pulled in as optional extras of the `mcp` package). No
action needed; `pyproject.toml` will declare the actual dependency set
this feature needs, and the venv can be reconciled against it during
implementation.
