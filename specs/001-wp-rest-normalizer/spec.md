# Feature Specification: WordPress REST Exposure Normalizer Plugin

**Feature Branch**: `001-wp-rest-normalizer`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Plugin de WordPress que normaliza la exposición REST del sitio: fuerza show_in_rest en CPTs y campos ACF, configura CORS, expone /wp-json/migracion/v1/site-map con URL pública + tipo + fecha de modificación de cada contenido para sync incremental. No lee _elementor_data. No genera contenido nuevo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover all migratable content through one endpoint (Priority: P1)

The migration tooling needs a single place to ask a WordPress site "what public
content do you have, and when did each item last change?" so it can plan and
prioritize a migration or incremental re-sync without crawling the entire site
or guessing which content types exist.

**Why this priority**: This is the core value of the plugin — without a
reliable discovery endpoint, the migration process has no authoritative list
of what to fetch, and every other capability (REST exposure, CORS) exists to
make this list complete and reachable.

**Independent Test**: Install the plugin on a WordPress site with a mix of
posts, pages, and at least one custom post type, call the discovery endpoint,
and verify the response lists every published item with its public URL,
content type, and last-modified date.

**Acceptance Scenarios**:

1. **Given** a WordPress site with published posts, pages, and a custom post
   type, **When** the discovery endpoint is requested, **Then** the response
   includes one entry per published item, each with a public URL, a content
   type label, and a last-modified date.
2. **Given** a site with draft, private, or trashed content, **When** the
   discovery endpoint is requested, **Then** none of that non-public content
   appears in the response.
3. **Given** a previous sync recorded item modification dates, **When** the
   discovery endpoint is requested again after some content changes,
   **Then** comparing the two responses is sufficient to identify exactly
   which items changed, without re-fetching unchanged items' full content.

---

### User Story 2 - Read custom content types and ACF fields that aren't exposed by default (Priority: P2)

WordPress does not expose every custom post type or Advanced Custom Fields
(ACF) field through its REST API by default. The migration tooling needs
those made readable so it can retrieve full content structure using only the
standard WordPress REST API, without the site owner manually reconfiguring
every content type by hand.

**Why this priority**: Without this, the discovery endpoint from User Story 1
can list an item's existence, but the migration tooling still could not read
that item's actual content/fields — this is what makes the content readable
end to end.

**Independent Test**: On a site with a custom post type and ACF fields that
are not REST-exposed by default, activate the plugin and verify those post
types and fields now appear in standard WordPress REST API responses,
without any manual per-site configuration.

**Acceptance Scenarios**:

1. **Given** a public custom post type registered without REST support,
   **When** the plugin is active, **Then** that post type's entries are
   readable through the standard WordPress REST API.
2. **Given** an ACF field attached to a public content type, **When** the
   plugin is active, **Then** that field's value appears in the REST
   response for the corresponding content item.
3. **Given** a custom post type that is intentionally not public (e.g. an
   internal/admin-only type), **When** the plugin is active, **Then** that
   post type remains unexposed — the plugin does not force REST exposure on
   non-public content types.

---

### User Story 3 - Fetch site content from the migration tooling's own domain (Priority: P3)

The migration tooling runs on a different domain than the WordPress site
being migrated. Without cross-origin permission, browser-based requests from
the migration tooling to the WordPress REST API are blocked.

**Why this priority**: This unblocks a specific consumption path (in-browser
requests); server-to-server requests from the migration tooling are
unaffected by CORS, so this is valuable but not blocking for the core
discovery/read flow.

**Independent Test**: From a browser context on the migration tooling's
domain, issue a request to the WordPress REST API and verify it succeeds
without a cross-origin error, while a request from an unrecognized origin is
still rejected.

**Acceptance Scenarios**:

1. **Given** the plugin is configured with an allowed origin, **When** a
   browser-based request to the WordPress REST API originates from that
   origin, **Then** the request succeeds.
2. **Given** the plugin is configured with an allowed origin, **When** a
   browser-based request originates from a different, unrecognized origin,
   **Then** the request is not granted cross-origin access.

---

### Edge Cases

- What happens when a content item is permanently deleted between two
  discovery-endpoint calls? (The item simply stops appearing in the
  response; the plugin does not report deletions explicitly — see
  Assumptions.)
- What happens when a custom post type already has REST support enabled
  before the plugin is activated? The plugin must not break or duplicate
  its existing REST registration.
- What happens when an ACF field is attached to a non-public content type?
  It is not force-exposed, consistent with the content type staying
  unexposed.
- What happens when the site has zero allowed CORS origins configured? The
  discovery and content endpoints remain reachable server-to-server; only
  browser-based cross-origin requests are affected.
- What happens if a request is made for `_elementor_data`, directly or
  indirectly, through any endpoint this plugin controls? The plugin never
  reads or exposes that field, regardless of how it's requested.
- What happens when Elementor registers its internal template/kit library
  post type (`elementor_library`) as `public => true`? The discovery
  endpoint excludes it explicitly (it is page-builder plumbing, not site
  content) — confirmed on a real site where this post type was in fact
  public.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST expose a single discovery endpoint that
  returns, for every publicly published content item on the site, its
  numeric identifier, its public URL, its content type, and its
  last-modified date. The identifier exists so callers that also read
  content via WordPress's native REST API (which addresses posts/pages by
  numeric id, not URL) don't need a second lookup to resolve one from
  the other — added after downstream integration work
  (`specs/003-astro-migration-skill`) found no other way to get it.
- **FR-002**: The discovery endpoint MUST include only publicly published
  content — draft, private, trashed, and password-protected items MUST be
  excluded.
- **FR-003**: The plugin MUST force REST exposure for every public custom
  post type that is not already exposed through the standard WordPress
  REST API.
- **FR-004**: The plugin MUST NOT force REST exposure for content types that
  are marked non-public (e.g., internal/admin-only types).
- **FR-005**: The plugin MUST force REST exposure for ACF fields attached to
  content types that are readable through the REST API, so their values
  appear in the standard content responses.
- **FR-006**: The plugin MUST allow a site administrator to configure which
  origin(s) are permitted to make cross-origin (CORS) requests to the
  WordPress REST API.
- **FR-007**: The plugin MUST NOT grant cross-origin access, at the
  WordPress/REST application layer, to origins that have not been
  explicitly configured as allowed. This is an application-layer guarantee,
  not an end-to-end one: a host's CDN or reverse proxy sitting in front of
  WordPress may add or override CORS headers at the edge, outside what the
  plugin can control or observe — see `quickstart.md`'s "Known limitations
  (CDN-fronted hosting)" section for a confirmed real-world case.
- **FR-008**: The plugin MUST NOT read, process, or expose the
  `_elementor_data` field, in the discovery endpoint or anywhere else under
  its control.
- **FR-009**: The plugin MUST NOT create, modify, or delete any WordPress
  content, fields, or taxonomies — its behavior is limited to exposing and
  normalizing access to content that already exists.
- **FR-010**: The discovery endpoint's last-modified date for each item
  MUST reflect that item's true last modification time, so that comparing
  two discovery-endpoint responses over time reliably identifies which
  items changed.

### Key Entities *(include if feature involves data)*

- **Site map entry**: One discoverable content item, as listed by the
  discovery endpoint. Attributes: numeric identifier, public URL, content
  type, last-modified date. Represents a post, page, or custom-post-type
  item that is publicly published on the WordPress site.
- **Exposed content type**: A custom post type or ACF field group that the
  plugin has made readable through the standard WordPress REST API.
  Represents existing WordPress configuration being surfaced, not new data.
- **Allowed origin**: A domain the site administrator has configured as
  permitted to make cross-origin requests to the WordPress REST API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Given any public content item on a site running the plugin,
  the discovery endpoint reports its existence, type, and last-modified
  date without requiring any manual per-item configuration.
- **SC-002**: A migration process can determine which content changed since
  a prior sync using only the discovery endpoint's response, without
  fetching the full content of unchanged items.
- **SC-003**: 100% of public custom post types and their ACF fields become
  readable through the standard WordPress REST API immediately after plugin
  activation, with zero manual per-type configuration by the site
  administrator.
- **SC-004**: No response produced by the plugin, under any configuration,
  ever contains Elementor's internal layout data.
- **SC-005**: No migration or discovery request made through the plugin
  ever results in new, modified, or deleted WordPress content.

## Assumptions

- The discovery endpoint returns the full current list of public content on
  every call; detecting deletions and filtering by "changed since a given
  date" are done by the calling migration tooling comparing successive
  full responses, not by the plugin itself.
- "Public" content type/post status follows WordPress's own conventions
  (post type registered with `public => true`; post status `publish`),
  **except** for a small, explicit denylist of post types that are
  `public => true` but are not real site content — currently `attachment`
  (media, covered separately) and `elementor_library` (Elementor's
  internal template/kit library, confirmed in practice to be registered
  `public => true` on a real site). This list is deliberately narrow and
  grows only when a real, observed case like this one shows up — not
  speculatively.
- The discovery endpoint and REST-exposed content are readable without
  WordPress user authentication, consistent with the fact that they only
  ever surface content that is already publicly viewable on the site.
- CORS allowed origins are configured per-site by whoever installs the
  plugin (no origins are allowed by default).
- This plugin is one component of a larger migration toolkit; it does not
  itself render pages, fetch HTML, or perform the migration — it only
  normalizes what the WordPress REST API exposes.
