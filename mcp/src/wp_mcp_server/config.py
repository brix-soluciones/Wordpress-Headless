"""Server configuration: the target WordPress site's base URL (FR-007)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

ENV_VAR = "WP_MCP_BASE_URL"


@dataclass(frozen=True)
class ServerConfig:
    base_url: str


def load_config() -> ServerConfig:
    """Read the target WordPress site's base URL from the environment.

    Raises RuntimeError immediately if it is unset or not a well-formed
    absolute URL — the base URL must never be hardcoded (FR-007).
    """
    raw = os.environ.get(ENV_VAR)
    if not raw:
        raise RuntimeError(
            f"{ENV_VAR} is not set. Configure it to the target WordPress "
            "site's base URL (e.g. https://origin-site.example) before "
            "starting the server."
        )

    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise RuntimeError(
            f"{ENV_VAR}={raw!r} is not a well-formed absolute URL "
            "(expected e.g. https://origin-site.example)."
        )

    return ServerConfig(base_url=raw.rstrip("/"))
