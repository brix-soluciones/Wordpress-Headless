<?php
/**
 * Configurable CORS for the WordPress REST API.
 *
 * Implements FR-006, FR-007 (see specs/001-wp-rest-normalizer/spec.md),
 * the "Allowed origin" entity in specs/001-wp-rest-normalizer/data-model.md,
 * and the contract in specs/001-wp-rest-normalizer/contracts/cors.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class Migration_Toolkit_Cors {

	const OPTION_NAME = 'migration_toolkit_allowed_origins';

	public function __construct() {
		add_action( 'admin_init', array( $this, 'register_settings' ) );
		add_action( 'rest_api_init', array( $this, 'add_cors_support' ) );
	}

	public function register_settings() {
		register_setting(
			'general',
			self::OPTION_NAME,
			array(
				'type'              => 'array',
				'default'           => array(),
				'sanitize_callback' => array( $this, 'sanitize_origins' ),
			)
		);

		add_settings_field(
			self::OPTION_NAME,
			__( 'Migration Toolkit: Allowed CORS Origins', 'migration-toolkit' ),
			array( $this, 'render_field' ),
			'general'
		);
	}

	/**
	 * Rejects malformed entries instead of silently accepting them
	 * (data-model.md's validation rule for the Allowed origin entity).
	 *
	 * @param mixed $value Raw submitted value (string from the textarea, or array).
	 * @return string[] Only well-formed scheme+host origins.
	 */
	public function sanitize_origins( $value ) {
		$lines = is_array( $value ) ? $value : preg_split( '/[\r\n,]+/', (string) $value );

		$origins  = array();
		$rejected = array();

		foreach ( $lines as $line ) {
			$line = trim( (string) $line );

			if ( '' === $line ) {
				continue;
			}

			$parts    = wp_parse_url( $line );
			$is_valid = ! empty( $parts['scheme'] )
				&& ! empty( $parts['host'] )
				&& empty( $parts['path'] )
				&& empty( $parts['query'] );

			if ( $is_valid ) {
				$origins[] = untrailingslashit( $line );
			} else {
				$rejected[] = $line;
			}
		}

		if ( ! empty( $rejected ) ) {
			add_settings_error(
				self::OPTION_NAME,
				'migration_toolkit_invalid_origin',
				sprintf(
					/* translators: %s: comma-separated list of rejected origin values */
					__( 'Migration Toolkit: ignored invalid origin(s): %s. Use scheme + host only, e.g. https://example.com', 'migration-toolkit' ),
					esc_html( implode( ', ', $rejected ) )
				)
			);
		}

		return array_values( array_unique( $origins ) );
	}

	public function render_field() {
		$origins = get_option( self::OPTION_NAME, array() );

		printf(
			'<textarea name="%1$s" rows="4" cols="50" placeholder="https://example.com">%2$s</textarea><p class="description">%3$s</p>',
			esc_attr( self::OPTION_NAME ),
			esc_textarea( implode( "\n", (array) $origins ) ),
			esc_html__( 'One origin per line (scheme + host, e.g. https://astro-site.example). No origins are allowed by default.', 'migration-toolkit' )
		);
	}

	public function add_cors_support() {
		// Priority 20: run after WordPress core's own default CORS handling
		// (rest_send_cors_headers, added at the default priority) so a
		// configured origin's header is never silently overwritten.
		add_filter( 'rest_pre_serve_request', array( $this, 'send_cors_headers' ), 20 );
	}

	/**
	 * @param bool $served
	 * @return bool
	 */
	public function send_cors_headers( $served ) {
		$origin = get_http_origin();

		if ( $origin && in_array( untrailingslashit( $origin ), $this->get_allowed_origins(), true ) ) {
			header( 'Access-Control-Allow-Origin: ' . esc_url_raw( $origin ) );
			header( 'Vary: Origin' );
		}

		return $served;
	}

	private function get_allowed_origins() {
		return (array) get_option( self::OPTION_NAME, array() );
	}
}
