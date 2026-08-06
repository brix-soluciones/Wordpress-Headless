=== Migration Toolkit ===
Tags: rest-api, headless, migration, cors
Requires at least: 5.8
Tested up to: 6.6
Requires PHP: 7.4
Stable tag: 0.1.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Normalizes what a WordPress site's REST API exposes, for headless migration tooling.

== Description ==

Migration Toolkit is a zero-dependency WordPress plugin with three capabilities:

1. **Site-map discovery endpoint** — `GET /wp-json/migracion/v1/site-map` lists every publicly published post, page, and custom-post-type item with its public URL, content type, and last-modified date, so external tooling can plan and incrementally re-sync a migration without crawling the site.
2. **Forced REST exposure** — public custom post types and their Advanced Custom Fields (ACF) fields that aren't exposed through the REST API by default become readable through the standard WordPress REST API, with zero manual per-site configuration. Non-public content types are never affected.
3. **Configurable CORS** — an administrator can allow specific origins to make cross-origin requests to the REST API. No origin is allowed by default.

The plugin never reads or exposes Elementor's internal `_elementor_data` field, and it never creates, modifies, or deletes any WordPress content — it only exposes and normalizes access to content that already exists.

== Installation ==

1. Upload the `migration-toolkit` folder to `/wp-content/plugins/`.
2. Activate the plugin through the "Plugins" screen in WordPress.
3. No further configuration is required — REST exposure normalization and the site-map endpoint work immediately. To allow cross-origin requests from your migration tooling's domain, add its origin under Settings → General → "Migration Toolkit: Allowed CORS Origins".

== Frequently Asked Questions ==

= Does this plugin create or modify any content? =

No. It only changes what is *visible* through the REST API (post-type/field REST registration and CORS headers). It never writes posts, fields, or taxonomy terms.

= Does it require Advanced Custom Fields (ACF)? =

No. ACF field exposure is applied only when ACF is active; the plugin works fully without it.

= Does it read Elementor's internal layout data? =

No, never — not in the site-map endpoint, nor anywhere else the plugin controls.

== Changelog ==

= 0.1.0 =
* Initial release: forced REST exposure for public CPTs and ACF fields, configurable CORS, and the site-map discovery endpoint.
