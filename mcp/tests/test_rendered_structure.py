"""Tests for get_rendered_structure (contracts/get_rendered_structure.md)."""

from __future__ import annotations

import httpx
import pytest

from wp_mcp_server import html_outline
from wp_mcp_server.tools.rendered_structure import get_rendered_structure

BASE_URL = "https://origin-site.example"
PAGE_URL = f"{BASE_URL}/services/consulting/"

_NORMAL_PAGE_HTML = """
<html><body>
  <header>
    <nav>
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/about/">About</a></li>
        <li><a href="/services/">Services</a></li>
        <li><a href="/contact/">Contact</a></li>
      </ul>
    </nav>
  </header>
  <main>
    <h1>Consulting Services</h1>
    <p>We help teams migrate legacy WordPress sites to Astro while
    keeping WordPress as the content backend, with enough real body
    copy here to comfortably clear both the element-count and
    visible-text thresholds used by the fallback rule.</p>
    <p>A second paragraph adds further genuine content so this
    fixture reads like an ordinary, fully server-rendered page.</p>
  </main>
  <footer><p>&copy; 2026</p></footer>
</body></html>
"""

_PAGE_WITHOUT_MAIN_HTML = """
<html><body>
  <div id="content">
    <h1>Consulting Services</h1>
    <p>This theme has no semantic &lt;main&gt; landmark at all, so the
    default scope must fall back to the full body instead of raising or
    returning nothing. This paragraph, together with the next one, is
    deliberately long enough to keep this fixture well clear of the
    render-fallback heuristic's thresholds, since that's not what this
    particular test is checking.</p>
    <p>A second paragraph adds further real content for the same reason
    — this test is about default-scope resolution when no &lt;main&gt;
    exists, not about the plain-fetch-vs-headless-render decision.</p>
  </div>
</body></html>
"""


async def test_rejects_url_on_a_different_host(client):
    with pytest.raises(ValueError, match="does not match"):
        await get_rendered_structure(client, BASE_URL, "https://elsewhere.example/page/")


async def test_default_scope_is_main_and_excludes_repeated_chrome(client, respx_mock):
    respx_mock.get(PAGE_URL).mock(return_value=httpx.Response(200, text=_NORMAL_PAGE_HTML))

    result = await get_rendered_structure(client, BASE_URL, PAGE_URL)

    assert result["scope"] == "main"
    outline_str = str(result["outline"])
    assert "Consulting Services" in outline_str
    assert "Home" not in outline_str  # nav chrome
    assert "2026" not in outline_str  # footer chrome


async def test_falls_back_to_body_when_page_has_no_main(client, respx_mock):
    respx_mock.get(PAGE_URL).mock(
        return_value=httpx.Response(200, text=_PAGE_WITHOUT_MAIN_HTML)
    )

    result = await get_rendered_structure(client, BASE_URL, PAGE_URL)

    assert result["scope"] == "body"
    assert "Consulting Services" in str(result["outline"])


async def test_explicit_selector_scopes_to_the_requested_element(client, respx_mock):
    respx_mock.get(PAGE_URL).mock(return_value=httpx.Response(200, text=_NORMAL_PAGE_HTML))

    result = await get_rendered_structure(client, BASE_URL, PAGE_URL, selector="footer")

    assert result["scope"] == "footer"
    assert result["outline"]["tag"] == "footer"
    assert "Consulting Services" not in str(result["outline"])


async def test_explicit_selector_body_returns_the_whole_page(client, respx_mock):
    respx_mock.get(PAGE_URL).mock(return_value=httpx.Response(200, text=_NORMAL_PAGE_HTML))

    result = await get_rendered_structure(client, BASE_URL, PAGE_URL, selector="body")

    assert result["scope"] == "body"
    outline_str = str(result["outline"])
    assert "Consulting Services" in outline_str
    assert "Home" in outline_str  # chrome is included when explicitly scoped to body


async def test_selector_matching_nothing_raises(client, respx_mock):
    respx_mock.get(PAGE_URL).mock(return_value=httpx.Response(200, text=_NORMAL_PAGE_HTML))

    with pytest.raises(ValueError, match="No element matches selector"):
        await get_rendered_structure(client, BASE_URL, PAGE_URL, selector=".does-not-exist")


async def test_plain_fetch_strips_scripts_styles_and_comments(client, respx_mock):
    html = _NORMAL_PAGE_HTML.replace(
        "</body>",
        "<script>console.log('nope')</script><style>.hero{color:red}</style>"
        "<!-- a comment --></body>",
    )
    respx_mock.get(PAGE_URL).mock(return_value=httpx.Response(200, text=html))

    # Scope explicitly to body so this test's own scope covers the
    # injected script/style/comment (they're siblings of <main>, outside
    # the default main-scoped outline) — this test is about stripping,
    # not scoping.
    result = await get_rendered_structure(client, BASE_URL, PAGE_URL, selector="body")

    assert result["url"] == PAGE_URL
    assert result["rendering_method"] == "fetch"
    outline_str = str(result["outline"])
    assert "script" not in outline_str
    assert "console.log" not in outline_str
    assert "color:red" not in outline_str
    assert "a comment" not in outline_str


def test_fallback_fires_on_sparse_short_body():
    body = html_outline.parse_body("<html><body><div>hi</div></body></html>")
    assert html_outline.needs_render_fallback(body) is True


def test_fallback_fires_on_empty_spa_root_regardless_of_surrounding_text():
    long_text = "Welcome. " * 60  # > 200 chars of real surrounding text
    html = f"<html><body><nav>{long_text}</nav><div id='root'></div></body></html>"
    body = html_outline.parse_body(html)
    assert html_outline.needs_render_fallback(body) is True


def test_fallback_does_not_fire_on_a_normal_wordpress_page():
    body = html_outline.parse_body(_NORMAL_PAGE_HTML)
    assert html_outline.needs_render_fallback(body) is False
