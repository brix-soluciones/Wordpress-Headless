"""Stdio MCP server exposing WordPress migration-survey tools (research.md #1)."""

from __future__ import annotations

from mcp.server import MCPServer

from wp_mcp_server.config import load_config
from wp_mcp_server.tools import media_original, page_content, rendered_structure, site_map
from wp_mcp_server.wp_client import WPClient, create_client


def build_server(client: WPClient, base_url: str) -> MCPServer:
    mcp = MCPServer("wp-migration")

    @mcp.tool()
    async def get_site_map() -> list[dict]:
        """List every publicly published item on the configured WordPress
        site: its url, content type, and last-modified date."""
        return await site_map.get_site_map(client)

    @mcp.tool()
    async def get_page_content(id: int) -> dict:
        """Return the plain title/content and any exposed custom fields
        for the post or page with this id."""
        return await page_content.get_page_content(client, id)

    @mcp.tool()
    async def get_rendered_structure(url: str, selector: str | None = None) -> dict:
        """Return a simplified layout outline of a public page on the
        configured site, resolved from its actual rendered HTML. Never
        contains Elementor's internal layout data. By default scopes to
        the page's <main> landmark (falling back to the full page when
        absent) to avoid repeating site-wide header/nav/footer chrome on
        every call; pass selector (a CSS selector, e.g. "body" or
        "header") to scope to something else instead."""
        return await rendered_structure.get_rendered_structure(client, base_url, url, selector)

    @mcp.tool()
    async def get_media_original(slug: str) -> dict:
        """Resolve a media item's slug to its original, full-resolution
        source file — never a resized or cropped variant."""
        return await media_original.get_media_original(client, slug)

    return mcp


def main() -> None:
    config = load_config()
    client = create_client(config.base_url)
    mcp = build_server(client, config.base_url)
    mcp.run()


if __name__ == "__main__":
    main()
