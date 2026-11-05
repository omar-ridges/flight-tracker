"""Registry that manages the set of tracked flights."""

from __future__ import annotations

from .errors import DuplicateFlightError, UnknownFlightError
from .models import Flight
from .storage import load_flights, save_flights


class FlightTracker:
    """A collection of :class:`~flight_tracker.models.Flight` objects
    keyed by normalised callsign."""

    def __init__(self, flights=None):
        self._flights = {}
        for flight in flights or ():
            self.add(flight)

    def add(self, flight):
        """Register an existing :class:`Flight` instance."""
        if not isinstance(flight, Flight):
            raise TypeError(f"expected a Flight, got {type(flight).__name__}")
        if flight.callsign in self._flights:
            raise DuplicateFlightError(
                f"a flight with callsign {flight.callsign!r} already exists"
            )
        self._flights[flight.callsign] = flight
        return flight

    def create_flight(self, callsign, origin, destination):
        """Create and register a new flight."""
        return self.add(Flight(callsign, origin, destination))

    def get_flight(self, callsign):
        try:
            return self._flights[Flight.normalize_callsign(callsign)]
        except KeyError as exc:
            raise UnknownFlightError(
                f"no flight with callsign {callsign!r}"
            ) from exc

    def list_flights(self):
        """All tracked flights, ordered by callsign."""
        return [self._flights[key] for key in sorted(self._flights)]

    def remove_flight(self, callsign):
        flight = self.get_flight(callsign)
        del self._flights[flight.callsign]

    def update_position(self, callsign, timestamp, position):
        self.get_flight(callsign).update_position(timestamp, position)

    def set_status(self, callsign, status):
        self.get_flight(callsign).set_status(status)

    def save(self, path):
        """Persist every tracked flight to ``path`` as JSON."""
        save_flights(list(self), path)

    @classmethod
    def load(cls, path):
        """Build a tracker from a JSON file written by :meth:`save`."""
        tracker = cls()
        for flight in load_flights(path):
            tracker.add(flight)
        return tracker

    def __len__(self):
        return len(self._flights)

    def __contains__(self, callsign):
        return Flight.normalize_callsign(callsign) in self._flights

    def __iter__(self):
        return iter(self.list_flights())
