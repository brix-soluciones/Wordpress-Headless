<?php
/**
 * Plugin Name: Migration Toolkit
 * Description: Normalizes WordPress REST exposure for a headless migration toolkit — forces REST exposure for public custom post types and their ACF fields, lets an administrator configure allowed CORS origins, and exposes a single site-map discovery endpoint. Reads and normalizes only: never reads Elementor's internal layout data, never creates, modifies, or deletes content.
 * Version: 0.1.0
 * Requires at least: 5.8
 * Requires PHP: 7.4
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: migration-toolkit
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'MIGRATION_TOOLKIT_DIR', plugin_dir_path( __FILE__ ) );

require_once MIGRATION_TOOLKIT_DIR . 'includes/functions.php';
require_once MIGRATION_TOOLKIT_DIR . 'includes/class-sitemap-endpoint.php';
require_once MIGRATION_TOOLKIT_DIR . 'includes/class-rest-normalizer.php';
require_once MIGRATION_TOOLKIT_DIR . 'includes/class-cors.php';

add_action( 'plugins_loaded', 'migration_toolkit_init' );

/**
 * Wires up all three capabilities. Each class self-registers its own
 * hooks in its constructor, so activation requires no further setup.
 */
function migration_toolkit_init() {
	new Migration_Toolkit_Sitemap_Endpoint();
	new Migration_Toolkit_Rest_Normalizer();
	new Migration_Toolkit_Cors();
}
