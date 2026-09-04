"""Allowlisted fetch. Primary grid never leaves the harness origin."""

from __future__ import annotations

from urllib.parse import urlparse

from beacon.origins.server import OriginState, fetch_local


def fetch(state: OriginState, url: str, *, origin_prefix: str = "") -> tuple[int, bytes, bool]:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if origin_prefix and parsed.netloc and not url.startswith(origin_prefix):
        raise PermissionError(f"fetch blocked (allowlist): {url}")
    return fetch_local(state, path)
