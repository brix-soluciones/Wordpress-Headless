"""Tests for get_site_map (contracts/get_site_map.md)."""

from __future__ import annotations

import httpx
import pytest

from wp_mcp_server.tools.site_map import get_site_map

SITE_MAP_URL = "https://origin-site.example/wp-json/migracion/v1/site-map"


async def test_returns_items_passthrough(client, respx_mock):
    items = [
        {
            "url": "https://origin-site.example/blog/hello-world/",
            "type": "post",
            "modified": "2026-07-30T14:22:05+00:00",
        },
        {
            "url": "https://origin-site.example/services/consulting/",
            "type": "page",
            "modified": "2026-06-11T09:03:44+00:00",
        },
    ]
    respx_mock.get(SITE_MAP_URL).mock(
        return_value=httpx.Response(200, json={"items": items})
    )

    result = await get_site_map(client)

    assert result == items


async def test_returns_empty_list_for_a_site_with_no_public_content(client, respx_mock):
    respx_mock.get(SITE_MAP_URL).mock(return_value=httpx.Response(200, json={"items": []}))

    result = await get_site_map(client)

    assert result == []


async def test_raises_when_discovery_endpoint_missing(client, respx_mock):
    respx_mock.get(SITE_MAP_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RuntimeError, match="discovery endpoint"):
        await get_site_map(client)


async def test_raises_when_site_unreachable(client, respx_mock):
    respx_mock.get(SITE_MAP_URL).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(RuntimeError, match="Could not reach"):
        await get_site_map(client)
