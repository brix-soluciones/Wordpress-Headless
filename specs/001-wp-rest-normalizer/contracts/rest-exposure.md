# Contract: Forced REST Exposure (CPTs and ACF fields)

Covers FR-003, FR-004, FR-005. This is not a new endpoint — it's an
observable effect on WordPress's existing `/wp-json/wp/v2/*` REST API.

## Effect on custom post type routes

For every registered post type with `public => true` that does not already
have `show_in_rest => true`:

- **Before** activation: `GET /wp-json/wp/v2/<type-rest-base>` → `404 rest_no_route`.
- **After** activation (no configuration needed): the same request returns
  `200` with the standard WP REST post-type collection/item shape,
  including that post type's entries.

For any post type with `public => false` (internal/admin-only types): no
change. It remains unexposed (FR-004) — this plugin never widens access to
non-public content types.

For any post type that already had `show_in_rest => true` before
activation: no change in behavior — the plugin does not duplicate or
conflict with existing REST registration.

## Effect on ACF field values

For an ACF field group attached to a REST-readable content type, when the
ACF plugin is active on the site:

- **Before** activation: the field either does not appear in the REST
  response for that content item, or requires "ACF to REST API" or manual
  `show_in_rest` configuration per field group.
- **After** activation: the field's value appears in the REST response for
  the corresponding content item, without any manual per-site
  configuration.

If ACF is not active on the site: no-op. This plugin does not require ACF
and does not fail or warn in its absence — see `research.md`.

## Guarantees

- No content type or field that was previously private/unexposed becomes
  exposed if it is not `public => true` on the post type (FR-004).
- This normalization never touches `_elementor_data` (Article I) — it
  operates on post-type and ACF-field registration, not on individual meta
  keys' content.
- Applying this normalization does not create, modify, or delete any post,
  field value, or taxonomy term (FR-009) — only the REST *visibility* of
  already-existing registrations changes.
