# Feature Specification: WordPress MCP Tools Server

**Feature Branch**: `002-wp-mcp-tools`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Servidor MCP en Python que expone el sitio WordPress como tools para un agente. Tools: get_site_map (consulta /wp-json/migracion/v1/site-map del plugin), get_page_content(id) (contenido plano vía REST nativo /wp/v2/posts y /wp/v2/pages, incluye ACF si está expuesto), get_rendered_structure(url) (HTML/DOM resuelto de una página pública, para relevamiento de layout — nunca lee _elementor_data), get_media_original(slug) (resolución original de una imagen vía /wp/v2/media?slug=). La URL base del WordPress es configurable, no hardcodeada. No genera código Astro directamente, solo da datos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover everything on the site worth migrating (Priority: P1)

Before an agent can plan or drive a migration, it needs one reliable way to
ask "what does this WordPress site have, and what changed since I last
looked?" — without crawling the site by hand or guessing which content
types exist.

**Why this priority**: This is the entry point for every other capability.
Without a trustworthy list of what exists, the agent has nothing to point
the other tools at.

**Independent Test**: Point the tools at a WordPress site that has the
companion discovery endpoint installed, request the site map, and verify
the agent receives every publicly published item with its URL, content
type, and last-modified date.

**Acceptance Scenarios**:

1. **Given** a configured WordPress site with published posts, pages, and a
   custom post type, **When** the agent requests the site map, **Then** it
   receives one entry per published item with a URL, content type, and
   last-modified date.
2. **Given** the site map was already fetched once, **When** the agent
   requests it again after some content changed, **Then** comparing the two
   results is enough to tell which items changed, without re-fetching every
   item's full content.

---

### User Story 2 - Read the plain content of a specific page or post (Priority: P1)

Once the agent knows an item exists, it needs its actual content — title,
body text, and any custom fields — to understand what to migrate, without
needing to understand WordPress's internal data model.

**Why this priority**: This is the core value exchange of the whole
server: turning "an item exists" into "here is what it actually says."
Most migration decisions depend on this content being available.

**Independent Test**: Given the identifier of a known post or page (with at
least one custom field attached), request its content and verify the
response contains its plain text content and that custom field's value,
using only WordPress's standard content API.

**Acceptance Scenarios**:

1. **Given** the identifier of a published post or page, **When** the agent
   requests its content, **Then** it receives that item's plain text
   content.
2. **Given** a post or page with a custom field exposed by the site,
   **When** the agent requests its content, **Then** the custom field's
   value is included in the response.
3. **Given** a post or page with no custom fields exposed, **When** the
   agent requests its content, **Then** the response still succeeds and
   simply omits custom field data.

---

### User Story 3 - Relevar la estructura visual de una página pública (Priority: P2)

Some pages need their actual rendered layout examined — not just their
text — so the agent can match them against a known set of layout patterns.
The agent needs the page as a visitor's browser would actually see it, not
whatever internal format the page builder used to construct it.

**Why this priority**: Layout relevamiento only matters for pages where
visual structure drives the migration decision; it builds on the content
already retrieved via User Story 2, so it is valuable but not the first
thing every migration needs.

**Independent Test**: Given the public URL of a live page, request its
resolved structure and verify the response reflects the page's actual
rendered layout, and never contains the page builder's internal layout
data.

**Acceptance Scenarios**:

1. **Given** the public URL of a live page on the configured site,
   **When** the agent requests its rendered structure, **Then** it
   receives that page's resolved HTML/DOM structure.
2. **Given** any page on the configured site, **When** the agent requests
   its rendered structure, **Then** the response never contains the page
   builder's internal layout data, under any circumstance.
3. **Given** a page whose header, navigation, footer, and comment form are
   identical across every page of the site, **When** the agent requests
   its rendered structure without specifying which part of the page it
   wants, **Then** the response reflects only that page's main content
   area, without repeating that site-wide chrome.
4. **Given** the agent does need to inspect a different part of a page
   (e.g. the site-wide header, or the full page), **When** it requests the
   rendered structure with that part specified, **Then** the response
   reflects that requested part instead of the default main content area.

---

### User Story 4 - Resolve the original file behind a referenced image (Priority: P3)

Content and layout often reference images only by a short identifying
name. The agent needs to resolve that reference to the actual
full-resolution source file, not a resized or cropped variant, so the
migrated asset matches the original quality.

**Why this priority**: This supports the other three capabilities (content
and layout both reference media) rather than standing on its own as a
migration starting point, so it's valuable but comes last.

**Independent Test**: Given the identifying slug of a known media item,
request its original file and verify the response resolves to the
full-resolution source, not a thumbnail or cropped size.

**Acceptance Scenarios**:

1. **Given** the slug of a known image on the configured site, **When**
   the agent requests its original, **Then** it receives that image's
   full-resolution source location.
2. **Given** a slug that matches no media item on the configured site,
   **When** the agent requests its original, **Then** the response clearly
   indicates nothing was found, rather than returning an unrelated image.

---

### Edge Cases

- What happens when `get_page_content` is called with an identifier that
  doesn't exist, or that belongs to non-public content? The response must
  clearly indicate "not found," never return draft/private content.
- What happens when `get_rendered_structure` is called with a URL that
  isn't on the configured WordPress site? The request must be rejected
  rather than silently fetching an arbitrary external page.
- What happens when the discovery endpoint the plugin provides (per the
  companion normalizer plugin) is missing or unreachable on the target
  site? `get_site_map` must fail clearly, rather than silently returning
  an empty or partial list indistinguishable from "no content."
- What happens when ACF (or any custom-field system) isn't installed or
  exposed on the target site? `get_page_content` must still succeed and
  simply return no custom field data.
- What happens when the configured base URL is unreachable or doesn't
  point to a WordPress site at all? Every tool must fail with a clear,
  distinguishable error rather than an unhandled failure.
- What happens when two media items on the site coincidentally share the
  same slug? The tool's behavior in that case must be predictable and
  documented, not arbitrary.
- What happens when a page has no distinguishable "main content" region
  (e.g. the site's theme doesn't mark one)? `get_rendered_structure`'s
  default MUST still return something usable — the page as a whole —
  rather than an empty or missing result.
- What happens when the agent explicitly asks for a part of the page that
  doesn't exist on it? The response must clearly indicate that, rather
  than silently returning an unrelated part of the page or the whole page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let an agent retrieve the full list of
  publicly published content on the configured WordPress site — URL,
  content type, and last-modified date per item — via the site's
  discovery endpoint.
- **FR-002**: The system MUST let an agent retrieve the plain content of a
  specific post or page by its identifier, using WordPress's native
  content API, including any custom fields already exposed by the site.
- **FR-003**: The system MUST let an agent retrieve the resolved
  HTML/DOM structure of a public page given its URL, reflecting the page
  as actually rendered for a visitor. Resolution MUST first attempt a
  plain HTTP fetch of the server-delivered HTML, and fall back to
  executing client-side rendering only when that plain fetch is
  insufficient to reach the page's final layout (e.g. content that
  depends on JavaScript to appear).
- **FR-004**: The rendered structure returned by the system MUST be a
  simplified structural outline — tag hierarchy with key attributes
  (e.g. `class`, `id`) and text content — rather than the full raw HTML
  document, so the agent can compare it against known layout patterns
  without unrelated markup, scripts, or styles.
- **FR-005**: The system MUST NOT read, request, process, or expose
  Elementor's internal layout data (`_elementor_data`), through any tool,
  under any circumstance.
- **FR-006**: The system MUST let an agent resolve the original,
  full-resolution file behind a media item given its identifying slug —
  never a resized or cropped variant.
- **FR-007**: The WordPress site the tools operate against MUST be
  configurable by whoever operates the server, and MUST NOT be fixed to
  any specific site in the system itself.
- **FR-008**: The system MUST restrict every tool to content that is
  already publicly visible on the configured WordPress site, and MUST NOT
  require or accept WordPress user credentials to reach draft, private,
  or otherwise non-public content — consistent with the companion
  plugin's public-only discovery endpoint.
- **FR-009**: The system MUST NOT generate, return, or otherwise produce
  target-framework code (e.g., page or component code) — its
  responsibility ends at providing data about the source site.
- **FR-010**: When a requested item does not exist, isn't publicly
  available, or the configured site can't be reached, the system MUST
  return a clear, distinguishable "not found" or error result rather than
  partial, incorrect, or silently empty data.
- **FR-011**: Each of the four capabilities (site map, page content,
  rendered structure, media original) MUST be independently usable by an
  agent — none requires another to have been called first.
- **FR-012**: By default, the rendered structure MUST be limited to a
  page's main content area, excluding site-wide chrome (header,
  navigation, footer, comment form, and similar elements repeated
  identically across pages) — confirmed in practice to otherwise dominate
  every response with no per-page signal. The agent MUST be able to
  request a different part of the page (including the whole page)
  instead of that default when it needs to.

### Key Entities *(include if feature involves data)*

- **Site map entry**: One discoverable content item on the configured
  WordPress site, as returned by the discovery endpoint — URL, content
  type, and last-modified date.
- **Page content**: The plain text content of a specific post or page,
  plus any custom field values already exposed by the site, keyed by that
  item's identifier.
- **Rendered structure**: The resolved HTML/DOM representation of a
  specific public page URL, used for layout relevamiento — never contains
  page-builder-internal layout data. Scoped by default to the page's main
  content area (FR-012); the agent may request a different scope.
- **Media original**: The full-resolution source file behind a media
  item, resolved by its identifying slug.
- **Site configuration**: The base URL of the WordPress site the tools
  currently operate against; not fixed within the system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An agent can obtain the complete list of migratable content
  on a configured site in a single request, with no manual crawling.
- **SC-002**: An agent can retrieve the plain content and any exposed
  custom fields of any public post or page using only its identifier, with
  no per-item manual configuration.
- **SC-003**: An agent can obtain a resolved layout structure for any
  publicly reachable page URL on the configured site, and that structure
  never contains page-builder-internal layout data, in 100% of requests.
- **SC-004**: An agent can resolve the original full-resolution file for
  any media item using only its slug, with no manual lookup step.
- **SC-005**: Pointing the tools at a different WordPress site requires
  changing only its base URL configuration — no other change is needed.
- **SC-006**: 100% of data returned by the tools contains no
  target-framework (e.g., Astro) code — only source-site data.
- **SC-007**: Surveying multiple pages of the same site does not repeat
  identical site-wide chrome (header, navigation, footer, comment form)
  in every rendered-structure response, unless the agent specifically
  asked for that part of the page.

## Assumptions

- The configured WordPress site has the companion REST normalizer plugin
  installed for `get_site_map` (its discovery endpoint) and for any
  custom-post-type/ACF exposure beyond WordPress's own defaults;
  `get_page_content` against native `post`/`page` items works even
  without it.
- `get_page_content` is scoped to WordPress's native `post` and `page`
  content types, per the feature description; other custom post types may
  still appear in `get_site_map` but aren't fetched through this tool.
- The tools require no WordPress user authentication, consistent with all
  data involved already being publicly viewable on the source site.
- A single configured site is operated against at a time; multi-site or
  multi-tenant operation in one server instance is out of scope.
- "Insufficient" for the plain-fetch step in FR-003 (triggering the
  client-side-rendering fallback) is judged by whether the fetched HTML
  is missing content expected to be on the page (e.g. an emptied-out
  container that JavaScript would normally fill) — the exact detection
  rule is a planning-time decision, not a spec-level one.
