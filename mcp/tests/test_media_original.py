"""Tests for get_media_original (contracts/get_media_original.md)."""

from __future__ import annotations

import httpx
import pytest

from wp_mcp_server.tools.media_original import get_media_original

MEDIA_URL = "https://origin-site.example/wp-json/wp/v2/media"


async def test_returns_original_source_url_not_a_sized_variant(client, respx_mock):
    respx_mock.get(MEDIA_URL, params={"slug": "team-photo-2026"}).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "source_url": (
                        "https://origin-site.example/wp-content/uploads/"
                        "2026/07/team-photo-2026.jpg"
                    ),
                    "mime_type": "image/jpeg",
                    "media_details": {
                        "sizes": {
                            "thumbnail": {
                                "source_url": (
                                    "https://origin-site.example/wp-content/"
                                    "uploads/2026/07/team-photo-2026-150x150.jpg"
                                )
                            }
                        }
                    },
                }
            ],
        )
    )

    result = await get_media_original(client, "team-photo-2026")

    assert result == {
        "slug": "team-photo-2026",
        "source_url": (
            "https://origin-site.example/wp-content/uploads/2026/07/team-photo-2026.jpg"
        ),
        "mime_type": "image/jpeg",
    }
    assert "150x150" not in result["source_url"]


async def test_raises_not_found_for_unknown_slug(client, respx_mock):
    respx_mock.get(MEDIA_URL, params={"slug": "does-not-exist"}).mock(
        return_value=httpx.Response(200, json=[])
    )

    with pytest.raises(RuntimeError, match="No media item found"):
        await get_media_original(client, "does-not-exist")
