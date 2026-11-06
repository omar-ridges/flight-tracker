"""Command-line entry point for the flight tracker web app."""

from __future__ import annotations

import argparse

from .server import FlightTrackerServer
from .store import FlightStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the flight tracker web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    server = FlightTrackerServer((args.host, args.port), FlightStore())
    host, port = server.server_address[:2]
    print(f"Flight tracker running at http://{host}:{port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
