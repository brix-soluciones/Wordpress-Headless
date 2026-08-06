"""Shared fixtures: a WPClient bound to a fixed test base_url, plus respx
faking the WordPress REST API (research.md #9). The `respx_mock` fixture
used across test_*.py files is provided automatically by the `respx`
package's own pytest plugin.
"""

from __future__ import annotations

import pytest

from wp_mcp_server.wp_client import WPClient

TEST_BASE_URL = "https://origin-site.example"


@pytest.fixture
def base_url() -> str:
    return TEST_BASE_URL


@pytest.fixture
async def client(base_url: str):
    wp_client = WPClient(base_url)
    yield wp_client
    await wp_client.aclose()
