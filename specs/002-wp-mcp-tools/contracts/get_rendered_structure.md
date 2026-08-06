# Contract: `get_rendered_structure`

Covers FR-003, FR-004, FR-005, FR-010, FR-011, FR-012.

## Input

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `url` | string | Yes | Public URL of a page on the configured site. MUST share a hostname with `WP_MCP_BASE_URL` (research.md #8). |
| `selector` | string | No | CSS selector scoping the outline to a specific part of the page (e.g. `"header"`, `"body"` for the whole page). Omit to use the default: the page's `<main>` landmark, falling back to the whole page when absent (research.md #11; FR-012). |

## Output — success

```json
{
  "url": "https://origin-site.example/services/consulting/",
  "rendering_method": "fetch",
  "scope": "main",
  "outline": {
    "tag": "main",
    "children": [
      {
        "tag": "section",
        "id": "hero",
        "class": ["hero"],
        "children": [
          { "tag": "h1", "text": "Consulting Services", "children": [] }
        ]
      }
    ]
  }
}
```

See `data-model.md`'s `RenderedStructure` / `OutlineNode`.
`rendering_method` is `"fetch"` when the plain HTTP fetch alone was
sufficient, `"headless_render"` when the JS-render fallback fired
(research.md #3). `scope` names which part of the page `outline` is
rooted at — `"main"` by default when the page has that landmark, `"body"`
when it doesn't (default fallback) or when the whole page was explicitly
requested, or the caller's own `selector` string otherwise.

## Resolution steps

1. Validate `url`'s hostname matches the configured base URL's hostname —
   reject before any network call otherwise (spec edge case).
2. `GET url` (plain fetch). Parse the response HTML with `<script>`,
   `<style>`, `<noscript>`, and comments stripped.
3. Evaluate the fallback rule (research.md #3) against the full parsed
   `<body>` — **not** the eventual `selector`-scoped subset — since this
   is a page-level "did the fetch actually work" judgment, independent of
   which part of the page the caller ultimately wants:
   `(body has <10 element descendants AND body visible text is <200
   chars) OR (a #root/#app/#__next/#___gatsby/[data-reactroot] element
   exists with zero direct element children)`. If it fires, re-resolve
   `url` via headless-browser rendering instead and parse that DOM.
4. Resolve the outline's root (research.md #11): if `selector` was given,
   scope to it (raising if nothing matches, including against the body
   itself — e.g. `selector="body"` is a valid way to ask for the whole
   page); otherwise default to the page's `<main>` element, falling back
   to the full `<body>` when no `<main>` exists.
5. Build the simplified outline (`html_outline.py`, research.md #4) from
   that root, stripping `<script>`, `<style>`, and comments (already done
   in step 2/3's parse).

## Error conditions

| Condition | Behavior |
|-----------|----------|
| `url` hostname doesn't match the configured site | Raise — never fetches an arbitrary external URL (spec edge case). |
| `url` returns non-2xx, or is unreachable | Raise with a message identifying the fetch failure. |
| `selector` matches nothing on the page | Raise — never silently returns an unrelated part of the page or the whole page instead (spec edge case). |

## Guarantees

- The `outline` MUST NOT, under any circumstance, contain
  `_elementor_data` or any Elementor-internal field, regardless of
  `rendering_method` or `scope` — the outline is built purely from
  resolved HTML/DOM, which has no path to that data (Constitution
  Article I & II; FR-005; SC-003).
- `outline` is always the simplified structural form (FR-004) — never
  raw HTML, scripts, or styles.
- By default (no `selector`), `outline` never repeats site-wide chrome
  (header/nav/footer/comment form) that is identical across every page —
  it is scoped to `<main>` when present (FR-012; SC-007).
