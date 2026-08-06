<?php
/**
 * Forces REST exposure for public CPTs and their ACF fields.
 *
 * Implements FR-003, FR-004, FR-005 (see specs/001-wp-rest-normalizer/spec.md)
 * and the contract in specs/001-wp-rest-normalizer/contracts/rest-exposure.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class Migration_Toolkit_Rest_Normalizer {

	public function __construct() {
		add_filter( 'register_post_type_args', array( $this, 'force_show_in_rest' ), 10, 2 );

		// ACF is optional — this plugin has no hard dependency on it (research.md).
		if ( class_exists( 'ACF' ) ) {
			add_filter( 'acf/rest_api/field_settings/show_in_rest', '__return_true' );
		}
	}

	/**
	 * @param array  $args      Post type registration args.
	 * @param string $post_type Post type slug.
	 * @return array
	 */
	public function force_show_in_rest( $args, $post_type ) {
		// Never widen exposure for non-public content types (FR-004).
		if ( empty( $args['public'] ) ) {
			return $args;
		}

		// Never touch a post type that already has an explicit REST setting.
		if ( ! empty( $args['show_in_rest'] ) ) {
			return $args;
		}

		$args['show_in_rest'] = true;

		if ( empty( $args['rest_base'] ) ) {
			$args['rest_base'] = $post_type;
		}

		return $args;
	}
}
