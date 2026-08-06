"""Tests for get_page_content (contracts/get_page_content.md)."""

from __future__ import annotations

import httpx
import pytest

from wp_mcp_server.tools.page_content import get_page_content

POSTS_URL = "https://origin-site.example/wp-json/wp/v2/posts/42"
PAGES_URL = "https://origin-site.example/wp-json/wp/v2/pages/42"


async def test_resolves_via_native_posts_endpoint(client, respx_mock):
    respx_mock.get(POSTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 42,
                "title": {"rendered": "Hello World"},
                "content": {"rendered": "<p>Hi</p>"},
            },
        )
    )

    result = await get_page_content(client, 42)

    assert result == {
        "id": 42,
        "type": "post",
        "title": "Hello World",
        "content": "<p>Hi</p>",
    }


async def test_falls_back_to_pages_on_posts_404(client, respx_mock):
    respx_mock.get(POSTS_URL).mock(return_value=httpx.Response(404))
    respx_mock.get(PAGES_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 42,
                "title": {"rendered": "Consulting Services"},
                "content": {"rendered": "<p>...</p>"},
            },
        )
    )

    result = await get_page_content(client, 42)

    assert result["type"] == "page"
    assert result["title"] == "Consulting Services"


async def test_includes_custom_fields_when_acf_present(client, respx_mock):
    respx_mock.get(POSTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 42,
                "title": {"rendered": "Consulting Services"},
                "content": {"rendered": "<p>...</p>"},
                "acf": {"hero_subtitle": "Ship faster, break less"},
            },
        )
    )

    result = await get_page_content(client, 42)

    assert result["custom_fields"] == {"hero_subtitle": "Ship faster, break less"}


async def test_omits_custom_fields_key_when_acf_absent(client, respx_mock):
    respx_mock.get(POSTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 42,
                "title": {"rendered": "Consulting Services"},
                "content": {"rendered": "<p>...</p>"},
            },
        )
    )

    result = await get_page_content(client, 42)

    assert "custom_fields" not in result


async def test_raises_not_found_when_neither_lookup_matches(client, respx_mock):
    respx_mock.get(POSTS_URL).mock(return_value=httpx.Response(404))
    respx_mock.get(PAGES_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RuntimeError, match="No published post or page"):
        await get_page_content(client, 42)
