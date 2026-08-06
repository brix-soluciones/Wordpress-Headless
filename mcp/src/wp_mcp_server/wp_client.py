"""Shared HTTP client bound to the configured WordPress site (research.md #2)."""

from __future__ import annotations

from typing import Any

import httpx


class WPClient:
    """Thin wrapper around one shared httpx.AsyncClient for a single site.

    Every tool module calls through this instead of using httpx directly
    (plan.md's Structure Decision), so the request/error-handling shape
    stays in one place.
    """

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET path (relative to base_url) and return the parsed JSON body.

        Raises httpx.HTTPStatusError on a non-2xx response and
        httpx.HTTPError (or a subclass) on a connection/timeout failure —
        callers translate these into the RuntimeError shape their
        contract documents.
        """
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def get_text(self, url: str) -> str:
        """GET an absolute url (used for get_rendered_structure, which
        fetches a public page URL rather than a REST API path) and return
        the response body as text."""
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text

    async def aclose(self) -> None:
        await self._client.aclose()


def create_client(base_url: str) -> WPClient:
    return WPClient(base_url)
