"""In-memory flight store with seeded sample data."""

from __future__ import annotations

import threading
from datetime import timedelta
from typing import Iterable, List, Optional

from .models import Airport, Flight, utcnow

AIRPORTS = {
    "JFK": Airport("JFK", "John F. Kennedy International", "New York", 40.6413, -73.7781),
    "LAX": Airport("LAX", "Los Angeles International", "Los Angeles", 33.9416, -118.4085),
    "SFO": Airport("SFO", "San Francisco International", "San Francisco", 37.6213, -122.3790),
    "ORD": Airport("ORD", "O'Hare International", "Chicago", 41.9742, -87.9073),
    "LHR": Airport("LHR", "Heathrow", "London", 51.4700, -0.4543),
    "CDG": Airport("CDG", "Charles de Gaulle", "Paris", 49.0097, 2.5479),
    "DXB": Airport("DXB", "Dubai International", "Dubai", 25.2532, 55.3657),
    "HND": Airport("HND", "Haneda", "Tokyo", 35.5494, 139.7798),
}


def _seed_flights() -> List[Flight]:
    """Build a schedule relative to *now* so the dashboard always has a
    realistic live mix of landed / en-route / scheduled / delayed flights."""
    now = utcnow()
    a = AIRPORTS
    return [
        Flight("UA101", "United", "Boeing 787-9", a["SFO"], a["JFK"],
               now - timedelta(hours=7), now - timedelta(hours=1), "A11"),
        Flight("BA112", "British Airways", "Boeing 777-300", a["JFK"], a["LHR"],
               now - timedelta(hours=2, minutes=10), now + timedelta(hours=4, minutes=50), "B7"),
        Flight("EK204", "Emirates", "Airbus A380", a["JFK"], a["DXB"],
               now - timedelta(minutes=35), now + timedelta(hours=10, minutes=25), "C2"),
        Flight("AF7", "Air France", "Boeing 787-9", a["JFK"], a["CDG"],
               now + timedelta(minutes=40), now + timedelta(hours=6, minutes=55), "D4"),
        Flight("DL419", "Delta", "Airbus A321neo", a["JFK"], a["ORD"],
               now + timedelta(minutes=95), now + timedelta(hours=2, minutes=55), "E1",
               delay_minutes=30),
        Flight("NH9", "ANA", "Boeing 777-300ER", a["ORD"], a["HND"],
               now + timedelta(hours=3), now + timedelta(hours=18), "F3"),
        Flight("AA240", "American", "Airbus A321", a["LAX"], a["JFK"],
               now + timedelta(hours=5), now + timedelta(hours=9, minutes=30), "G6"),
        Flight("UA840", "United", "Boeing 767-300", a["LHR"], a["SFO"],
               now + timedelta(hours=1, minutes=15), now + timedelta(hours=12), "H2",
               forced_status="Cancelled"),
    ]


class FlightStore:
    """Thread-safe in-memory store of flights with snapshot/search/get."""

    def __init__(self, flights: Optional[Iterable[Flight]] = None):
        self._lock = threading.Lock()
        self._flights: List[Flight] = list(flights) if flights is not None else _seed_flights()

    def all_flights(self) -> List[Flight]:
        with self._lock:
            return list(self._flights)

    def snapshot(self, now=None) -> List[dict]:
        now = now or utcnow()
        flights = sorted(self.all_flights(), key=lambda f: f.departure)
        return [f.to_dict(now) for f in flights]

    def search(self, query: str, now=None) -> List[dict]:
        """Case-insensitive search over flight number, airline, aircraft,
        airport codes/cities, and current status."""
        q = (query or "").strip().lower()
        if not q:
            return self.snapshot(now)
        results = [
            f for f in self.all_flights()
            if q in f.flight_number.lower()
            or q in f.airline.lower()
            or q in f.aircraft.lower()
            or q in f.origin.code.lower()
            or q in f.origin.city.lower()
            or q in f.destination.code.lower()
            or q in f.destination.city.lower()
            or q in f.status(now).lower()
        ]
        results.sort(key=lambda f: f.departure)
        return [f.to_dict(now) for f in results]

    def get(self, flight_number: str, now=None) -> Optional[dict]:
        target = (flight_number or "").strip().lower()
        for f in self.all_flights():
            if f.flight_number.lower() == target:
                return f.to_dict(now)
        return None


flight_store = FlightStore()
