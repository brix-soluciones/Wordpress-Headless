"""get_site_map — the companion plugin's discovery endpoint (FR-001, FR-010).

Contract: specs/002-wp-mcp-tools/contracts/get_site_map.md
"""

from __future__ import annotations

from typing import Any

import httpx

from wp_mcp_server.wp_client import WPClient

SITE_MAP_PATH = "/wp-json/migracion/v1/site-map"


async def get_site_map(client: WPClient) -> list[dict[str, Any]]:
    """Return every publicly published item's url, type, and modified date.

    Raises RuntimeError if the discovery endpoint is missing/unreachable —
    never returns a silent empty list standing in for that failure.
    """
    try:
        data = await client.get_json(SITE_MAP_PATH)
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"WordPress discovery endpoint {SITE_MAP_PATH} returned "
            f"{exc.response.status_code} — is the companion normalizer "
            "plugin installed and active?"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Could not reach the WordPress site at {SITE_MAP_PATH}: {exc}"
        ) from exc

    items = data.get("items")
    if items is None:
        raise RuntimeError(
            f"Unexpected response shape from {SITE_MAP_PATH}: missing 'items'"
        )
    return items
