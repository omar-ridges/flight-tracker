"""Tests for the flight tracker models, store, and HTTP server."""

import json
import unittest
import urllib.error
import urllib.request
from datetime import timedelta
from threading import Thread

from flight_tracker.models import Airport, Flight, utcnow
from flight_tracker.server import FlightTrackerServer
from flight_tracker.store import AIRPORTS, FlightStore

JFK = Airport("JFK", "JFK Intl", "New York", 40.6413, -73.7781)
LAX = Airport("LAX", "LAX Intl", "Los Angeles", 33.9416, -118.4085)


def make_flight(**overrides):
    now = utcnow()
    defaults = dict(
        flight_number="XX100",
        airline="Test Air",
        aircraft="A320",
        origin=JFK,
        destination=LAX,
        departure=now - timedelta(hours=3),
        arrival=now + timedelta(hours=3),
    )
    defaults.update(overrides)
    return Flight(**defaults)


class TestModels(unittest.TestCase):
    def test_status_scheduled_enroute_landed(self):
        now = utcnow()
        scheduled = make_flight(departure=now + timedelta(hours=1), arrival=now + timedelta(hours=5))
        enroute = make_flight()
        landed = make_flight(departure=now - timedelta(hours=5), arrival=now - timedelta(hours=1))
        self.assertEqual(scheduled.status(now), "Scheduled")
        self.assertEqual(enroute.status(now), "En Route")
        self.assertEqual(landed.status(now), "Landed")

    def test_delayed_status_and_flag(self):
        now = utcnow()
        f = make_flight(departure=now + timedelta(hours=1), arrival=now + timedelta(hours=5), delay_minutes=45)
        self.assertEqual(f.status(now), "Delayed")
        self.assertEqual(f.to_dict(now)["delay_minutes"], 45)

    def test_forced_status(self):
        f = make_flight(forced_status="Cancelled")
        self.assertEqual(f.status(), "Cancelled")

    def test_progress_clamped(self):
        now = utcnow()
        f = make_flight(departure=now - timedelta(hours=2), arrival=now + timedelta(hours=2))
        self.assertAlmostEqual(f.progress(now), 0.5)
        early = make_flight(departure=now + timedelta(hours=1), arrival=now + timedelta(hours=3))
        self.assertEqual(early.progress(now), 0.0)
        late = make_flight(departure=now - timedelta(hours=3), arrival=now - timedelta(hours=1))
        self.assertEqual(late.progress(now), 1.0)

    def test_position_midpoint(self):
        now = utcnow()
        f = make_flight(departure=now - timedelta(hours=3), arrival=now + timedelta(hours=3))
        pos = f.position(now)
        self.assertAlmostEqual(pos["lat"], (JFK.lat + LAX.lat) / 2, places=2)
        self.assertAlmostEqual(pos["lon"], (JFK.lon + LAX.lon) / 2, places=2)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = FlightStore()
        self.now = utcnow()

    def test_seed_has_live_mix(self):
        flights = self.store.snapshot(self.now)
        statuses = {f["status"] for f in flights}
        self.assertIn("En Route", statuses)
        self.assertIn("Landed", statuses)
        self.assertIn("Cancelled", statuses)

    def test_search_by_airport_code(self):
        results = self.store.search("JFK", self.now)
        self.assertTrue(results)
        for f in results:
            self.assertTrue("JFK" in (f["origin"]["code"], f["destination"]["code"]))

    def test_search_by_city_case_insensitive(self):
        self.assertTrue(self.store.search("london", self.now))

    def test_search_no_match(self):
        self.assertEqual(self.store.search("zzzzz", self.now), [])

    def test_get_flight_case_insensitive(self):
        self.assertIsNotNone(self.store.get("ba112", self.now))
        self.assertIsNone(self.store.get("NO999", self.now))


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = FlightTrackerServer(("127.0.0.1", 0), FlightStore())
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as res:
                return res.status, res.headers.get("Content-Type", ""), res.read()
        except urllib.error.HTTPError as err:
            return err.code, err.headers.get("Content-Type", ""), err.read()

    def test_index_serves_html(self):
        status, ctype, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn(b"Flight Tracker", body)

    def test_static_assets(self):
        status, ctype, body = self._get("/static/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"refresh", body)
        status, ctype, _ = self._get("/static/style.css")
        self.assertEqual(status, 200)
        self.assertIn("css", ctype)

    def test_api_flights_list(self):
        status, ctype, body = self._get("/api/flights")
        self.assertEqual(status, 200)
        self.assertIn("application/json", ctype)
        flights = json.loads(body)
        self.assertTrue(flights)
        for key in ("flight_number", "airline", "status", "progress",
                    "origin", "destination", "departure", "arrival"):
            self.assertIn(key, flights[0])

    def test_api_flights_search(self):
        status, _, body = self._get("/api/flights?q=emirates")
        flights = json.loads(body)
        self.assertTrue(flights)
        self.assertTrue(all("Emirates" in f["airline"] for f in flights))

    def test_api_flight_detail(self):
        status, _, body = self._get("/api/flights/BA112")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["flight_number"], "BA112")

    def test_api_flight_missing_404(self):
        status, ctype, body = self._get("/api/flights/NO999")
        self.assertEqual(status, 404)
        self.assertIn("application/json", ctype)
        self.assertIn("error", json.loads(body))

    def test_unknown_path_404(self):
        status, _, _ = self._get("/nope")
        self.assertEqual(status, 404)

    def test_static_traversal_blocked(self):
        status, _, _ = self._get("/static/..%2Fflight_tracker%2Fmodels.py")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
