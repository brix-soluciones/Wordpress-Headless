<?php
/**
 * Shared helpers used by more than one class in this plugin.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Post types excluded from migratable content even though WordPress (or
 * a plugin) registers them with `public => true`.
 *
 * - `attachment`: media is already covered natively via
 *   `/wp-json/wp/v2/media` (constitution Article IV), and standalone
 *   attachments are the one `public => true` type that can carry a
 *   `publish` status without being a content item.
 * - `elementor_library`: Elementor's internal template/kit library.
 *   Observed in practice registered with `public => true` on a real
 *   site, but it is page-builder plumbing, not site content — exactly
 *   the kind of Elementor-internal data this plugin (Article I) and the
 *   migration tooling downstream must never treat as migratable.
 *
 * @return string[] Post type slugs.
 */
function migration_toolkit_get_excluded_post_types() {
	return array( 'attachment', 'elementor_library' );
}

/**
 * Post types this plugin treats as migratable content.
 *
 * @return string[] Post type slugs.
 */
function migration_toolkit_get_public_post_types() {
	$post_types = get_post_types( array( 'public' => true ), 'names' );

	foreach ( migration_toolkit_get_excluded_post_types() as $excluded ) {
		unset( $post_types[ $excluded ] );
	}

	return array_values( $post_types );
}
