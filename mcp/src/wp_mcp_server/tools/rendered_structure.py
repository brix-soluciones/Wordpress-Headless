"""get_rendered_structure — simplified layout outline of a public page.

Plain fetch first, headless-render fallback only when needed (FR-003);
never exposes _elementor_data (FR-005); output is a simplified outline,
not raw HTML (FR-004); scoped to <main> by default, or an explicit
selector, so repeated site-wide chrome isn't duplicated per call (FR-012).

Contract: specs/002-wp-mcp-tools/contracts/get_rendered_structure.md
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from wp_mcp_server import html_outline
from wp_mcp_server.wp_client import WPClient


async def _render_with_playwright(url: str) -> str:
    """Lazily resolve url's final DOM with a headless browser.

    Only imported/launched when the plain-fetch heuristic actually fires
    (research.md #3) — most calls never pay this cost.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            return await page.content()
        finally:
            await browser.close()


async def get_rendered_structure(
    client: WPClient, base_url: str, url: str, selector: str | None = None
) -> dict[str, Any]:
    """Resolve url's simplified layout outline.

    Rejects url outright if its hostname doesn't match the configured
    site's (spec edge case) before making any request. Raises
    RuntimeError if the fetch fails.

    By default (selector=None) the outline is scoped to the page's <main>
    landmark when present, falling back to the full body otherwise — this
    avoids repeating identical site-wide chrome (header/nav/footer/
    comment form) on every call. Pass selector to scope to something else
    instead (e.g. "body" for the whole page, "header" to inspect chrome
    once); raises ValueError if selector matches nothing on the page.
    """
    configured_host = urlparse(base_url).hostname
    requested_host = urlparse(url).hostname
    if not requested_host or requested_host != configured_host:
        raise ValueError(
            f"url host {requested_host!r} does not match the configured "
            f"site {configured_host!r}"
        )

    try:
        html = await client.get_text(url)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Could not fetch {url}: {exc}") from exc

    body = html_outline.parse_body(html)
    rendering_method = "fetch"

    if html_outline.needs_render_fallback(body):
        html = await _render_with_playwright(url)
        body = html_outline.parse_body(html)
        rendering_method = "headless_render"

    root, scope = html_outline.resolve_outline_root(body, selector)

    return {
        "url": url,
        "rendering_method": rendering_method,
        "scope": scope,
        "outline": html_outline.build_outline(root),
    }
