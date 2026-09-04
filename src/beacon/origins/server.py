"""In-cluster origin: the only web the primary grid may fetch.

Primary trials never hit the public internet. That keeps beacons under experimental
control and blocks live-web contamination.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable
from urllib.parse import urlparse


@dataclass
class OriginState:
    routes: dict[str, tuple[int, bytes, str]] = field(default_factory=dict)
    beacon_paths: set[str] = field(default_factory=set)

    def add(self, path: str, body: bytes, *, status: int = 200, content_type: str = "text/html; charset=utf-8", beacon: bool = False) -> None:
        self.routes[path] = (status, body, content_type)
        if beacon:
            self.beacon_paths.add(path)

    def get(self, path: str) -> tuple[int, bytes, str]:
        if path in self.routes:
            return self.routes[path]
        return (404, b"not found", "text/plain")


def make_handler(state: OriginState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            status, body, content_type = state.get(path)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:
            return

    return Handler


def serve_in_thread(state: OriginState, host: str = "127.0.0.1", port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    bound = httpd.server_address
    return httpd, f"http://{bound[0]}:{bound[1]}"


def fetch_local(state: OriginState, path: str) -> tuple[int, bytes, bool]:
    """Harness-side fetch that does not need a listening socket (dry-run / unit of rollout)."""
    status, body, _ = state.get(path)
    return status, body, path in state.beacon_paths


HTTPStatus  # re-export-friendly
Callable  # keep import used for type hints in callers
