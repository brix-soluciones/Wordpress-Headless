"""get_page_content — plain content + ACF via native REST (FR-002, FR-010).

Contract: specs/002-wp-mcp-tools/contracts/get_page_content.md
"""

from __future__ import annotations

from typing import Any

import httpx

from wp_mcp_server.wp_client import WPClient

_LOOKUPS = (
    ("post", "/wp-json/wp/v2/posts/{id}"),
    ("page", "/wp-json/wp/v2/pages/{id}"),
)


async def get_page_content(client: WPClient, id: int) -> dict[str, Any]:
    """Return id's plain title/content, plus any exposed custom fields.

    Tries /wp/v2/posts/{id} first, falling back to /wp/v2/pages/{id} on a
    404 — a WordPress id belongs to exactly one of the two (research.md
    #5). Raises RuntimeError if neither lookup matches, or if the site
    can't be reached.
    """
    last_status: int | None = None

    for post_type, path_template in _LOOKUPS:
        path = path_template.format(id=id)
        try:
            data = await client.get_json(path)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                last_status = 404
                continue
            raise RuntimeError(
                f"WordPress returned {exc.response.status_code} for {path}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Could not reach the WordPress site at {path}: {exc}"
            ) from exc

        result: dict[str, Any] = {
            "id": data["id"],
            "type": post_type,
            "title": data.get("title", {}).get("rendered", ""),
            "content": data.get("content", {}).get("rendered", ""),
        }
        acf = data.get("acf")
        if acf:
            result["custom_fields"] = acf
        return result

    raise RuntimeError(
        f"No published post or page found with id={id} (last status: {last_status})"
    )
