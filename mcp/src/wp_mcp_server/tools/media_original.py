"""get_media_original — full-resolution media file by slug (FR-006, FR-010).

Contract: specs/002-wp-mcp-tools/contracts/get_media_original.md
"""

from __future__ import annotations

from typing import Any

import httpx

from wp_mcp_server.wp_client import WPClient

MEDIA_PATH = "/wp-json/wp/v2/media"


async def get_media_original(client: WPClient, slug: str) -> dict[str, Any]:
    """Resolve slug to its original, full-resolution source_url.

    Raises RuntimeError if no media item matches (FR-010). Multiple
    matches (a WordPress edge case unreachable in normal operation, since
    WP auto-suffixes duplicate slugs) resolve to the first result
    (research.md #6) — a documented limitation, not an error.
    """
    try:
        data = await client.get_json(MEDIA_PATH, params={"slug": slug})
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Could not reach the WordPress site's media endpoint: {exc}"
        ) from exc

    if not data:
        raise RuntimeError(f"No media item found with slug={slug!r}")

    item = data[0]
    return {
        "slug": slug,
        "source_url": item["source_url"],
        "mime_type": item["mime_type"],
    }
