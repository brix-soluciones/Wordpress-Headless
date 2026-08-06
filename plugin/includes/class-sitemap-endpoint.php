<?php
/**
 * Registers and serves GET /wp-json/migracion/v1/site-map.
 *
 * Implements FR-001, FR-002, FR-010 (see specs/001-wp-rest-normalizer/spec.md)
 * and the contract in specs/001-wp-rest-normalizer/contracts/site-map-endpoint.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class Migration_Toolkit_Sitemap_Endpoint {

	public function __construct() {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
	}

	public function register_routes() {
		register_rest_route(
			'migracion/v1',
			'/site-map',
			array(
				'methods'             => 'GET',
				'callback'            => array( $this, 'get_site_map' ),
				'permission_callback' => '__return_true',
			)
		);
	}

	/**
	 * @param WP_REST_Request $request
	 * @return WP_REST_Response
	 */
	public function get_site_map( $request ) {
		$response = rest_ensure_response( array( 'items' => $this->query_items() ) );

		// This is a live discovery endpoint (FR-010) — a cached copy served by a
		// host-level page cache or CDN would silently break incremental sync
		// (callers would keep seeing stale `modified` dates). Not all CDNs honor
		// origin cache headers (see quickstart.md's known-limitations section),
		// but sending this is still the correct origin-side signal.
		$response->header( 'Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0' );

		return $response;
	}

	private function query_items() {
		$post_types = migration_toolkit_get_public_post_types();

		if ( empty( $post_types ) ) {
			return array();
		}

		$query = new WP_Query(
			array(
				'post_type'              => $post_types,
				'post_status'            => 'publish',
				'posts_per_page'         => -1,
				'orderby'                => 'ID',
				'order'                  => 'ASC',
				'no_found_rows'          => true,
				'ignore_sticky_posts'    => true,
				'update_post_meta_cache' => false,
				'update_post_term_cache' => false,
			)
		);

		$items = array();

		foreach ( $query->posts as $post ) {
			// Password-protected posts keep post_status = 'publish' in WordPress;
			// the status filter above does not exclude them on its own (FR-002).
			if ( '' !== $post->post_password ) {
				continue;
			}

			$items[] = array(
				'url'      => get_permalink( $post ),
				'type'     => $post->post_type,
				'modified' => $this->to_iso8601_utc( $post->post_modified_gmt ),
			);
		}

		return $items;
	}

	private function to_iso8601_utc( $mysql_datetime_gmt ) {
		$date = new DateTime( $mysql_datetime_gmt, new DateTimeZone( 'UTC' ) );

		return $date->format( 'c' );
	}
}
