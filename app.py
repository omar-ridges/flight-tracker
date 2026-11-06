"""Flight Tracker web UI.

Serves a single-page web interface and a JSON API for tracking flights.
Uses only the Python standard library, so no dependencies are required.

Run:  python app.py   (then open http://localhost:8000)
"""

import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOST = "0.0.0.0"
PORT = 8000
STATIC_DIR = Path(__file__).parent / "static"

# Seed data: flights with status and position information.
FLIGHTS = [
    {"id": "UA101", "airline": "United", "origin": "SFO", "destination": "JFK",
     "departure": "08:30", "arrival": "17:05", "status": "En Route",
     "lat": 39.5, "lon": -100.0, "altitude_ft": 35000, "speed_kts": 480},
    {"id": "DL456", "airline": "Delta", "origin": "ATL", "destination": "LAX",
     "departure": "09:15", "arrival": "11:40", "status": "En Route",
     "lat": 33.9, "lon": -105.0, "altitude_ft": 38000, "speed_kts": 500},
    {"id": "AA789", "airline": "American", "origin": "ORD", "destination": "MIA",
     "departure": "10:00", "arrival": "13:50", "status": "Scheduled",
     "lat": 41.9, "lon": -87.6, "altitude_ft": 0, "speed_kts": 0},
    {"id": "BA112", "airline": "British Airways", "origin": "LHR", "destination": "JFK",
     "departure": "11:20", "arrival": "14:35", "status": "En Route",
     "lat": 50.0, "lon": -40.0, "altitude_ft": 36000, "speed_kts": 520},
    {"id": "LH401", "airline": "Lufthansa", "origin": "FRA", "destination": "ORD",
     "departure": "13:05", "arrival": "15:30", "status": "Delayed",
     "lat": 50.1, "lon": 8.6, "altitude_ft": 0, "speed_kts": 0},
]

_lock = threading.Lock()


def simulate_position_updates():
    """Nudge positions of en-route flights so the UI shows live-ish data."""
    while True:
        with _lock:
            for f in FLIGHTS:
                if f["status"] == "En Route":
                    f["lat"] = round(f["lat"] + random.uniform(-0.5, 0.5), 2)
                    f["lon"] = round(f["lon"] + random.uniform(-0.5, 0.5), 2)
                    f["speed_kts"] = max(300, f["speed_kts"] + random.randint(-15, 15))
        time.sleep(5)


def all_flights():
    with _lock:
        return [dict(f) for f in FLIGHTS]


def find_flight(flight_id):
    with _lock:
        for f in FLIGHTS:
            if f["id"].lower() == flight_id.lower():
                return dict(f)
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode(), "application/json")

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        if route in ("/", "/index.html"):
            page = (STATIC_DIR / "index.html").read_bytes()
            self._send(200, page, "text/html; charset=utf-8")
        elif route == "/api/flights":
            query = parse_qs(parsed.query)
            flights = all_flights()
            term = (query.get("q", [""])[0] or "").lower()
            if term:
                flights = [f for f in flights if term in json.dumps(f).lower()]
            self._json(200, {"flights": flights})
        elif route.startswith("/api/flights/"):
            flight_id = route.rsplit("/", 1)[-1]
            flight = find_flight(flight_id)
            if flight:
                self._json(200, flight)
            else:
                self._json(404, {"error": f"flight {flight_id!r} not found"})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # quieter console
        pass


def main():
    threading.Thread(target=simulate_position_updates, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Flight Tracker running at http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
