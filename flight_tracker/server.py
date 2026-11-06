"""HTTP server exposing the flight tracker web UI and JSON API."""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

from .store import FlightStore, flight_store

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


class FlightTrackerHandler(BaseHTTPRequestHandler):
    server_version = "FlightTracker/1.0"

    @property
    def store(self) -> FlightStore:
        return self.server.store  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ I/O
    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _send_file(self, file_path: Path, default_type: Optional[str] = None) -> None:
        if not file_path.is_file():
            return self._send_json({"error": "not found"}, status=404)
        ctype = default_type or mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if ctype.startswith("text/") and "charset=" not in ctype:
            ctype += "; charset=utf-8"
        self._send_bytes(200, file_path.read_bytes(), ctype)

    # -------------------------------------------------------------- routing
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path in ("/", "/index.html"):
            return self._send_file(TEMPLATE_DIR / "index.html", "text/html; charset=utf-8")
        if path.startswith("/static/"):
            return self._serve_static(path)
        if path == "/api/flights":
            params = parse_qs(parsed.query)
            query = (params.get("q") or [""])[0]
            return self._send_json(self.store.search(query))
        if path.startswith("/api/flights/"):
            number = path[len("/api/flights/"):].strip("/")
            flight = self.store.get(number) if number else None
            if flight is None:
                return self._send_json({"error": f"flight {number!r} not found"}, status=404)
            return self._send_json(flight)
        return self._send_json({"error": "not found"}, status=404)

    def _serve_static(self, path: str) -> None:
        # basename() strips any directory components, which blocks path
        # traversal (e.g. /static/../flight_tracker/models.py).
        name = os.path.basename(path[len("/static/"):])
        if not name:
            return self._send_json({"error": "not found"}, status=404)
        return self._send_file(STATIC_DIR / name)

    def log_message(self, format, *args) -> None:  # noqa: A002 - stdlib API
        pass  # keep test/daemon output quiet


class FlightTrackerServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, store: Optional[FlightStore] = None):
        self.store = store or flight_store
        super().__init__(address, FlightTrackerHandler)
