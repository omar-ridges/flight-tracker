"""Core domain models for the flight tracker."""

from __future__ import annotations

import math
from enum import Enum

from .errors import InvalidTransitionError

EARTH_RADIUS_KM = 6371.0


class FlightStatus(Enum):
    """Lifecycle states of a flight."""

    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    LANDED = "landed"
    CANCELLED = "cancelled"


class Position:
    """A geographic coordinate validated against WGS 84 bounds.

    Latitudes must be within ``[-90, 90]`` and longitudes within
    ``[-180, 180]``; values are coerced to ``float``.
    """

    __slots__ = ("latitude", "longitude")

    def __init__(self, latitude, longitude):
        lat = float(latitude)
        lon = float(longitude)
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"latitude out of range: {latitude!r}")
        if not -180.0 <= lon <= 180.0:
            raise ValueError(f"longitude out of range: {longitude!r}")
        self.latitude = lat
        self.longitude = lon

    def distance_to(self, other):
        """Return the great-circle distance to ``other`` in kilometres."""
        phi1 = math.radians(self.latitude)
        phi2 = math.radians(other.latitude)
        d_phi = math.radians(other.latitude - self.latitude)
        d_lambda = math.radians(other.longitude - self.longitude)
        a = (
            math.sin(d_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2
        )
        return 2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))

    def __eq__(self, other):
        if not isinstance(other, Position):
            return NotImplemented
        return (self.latitude, self.longitude) == (other.latitude, other.longitude)

    def __repr__(self):
        return f"Position(latitude={self.latitude}, longitude={self.longitude})"


class Flight:
    """A flight identified by a unique callsign, with a position track.

    Position updates must carry strictly increasing timestamps, and the
    status may only move along the lifecycle
    ``SCHEDULED -> EN_ROUTE -> LANDED`` (or ``CANCELLED`` from either of
    the first two states). Terminal states are immutable.
    """

    TERMINAL_STATES = frozenset({FlightStatus.LANDED, FlightStatus.CANCELLED})
    ALLOWED_TRANSITIONS = {
        FlightStatus.SCHEDULED: frozenset(
            {FlightStatus.EN_ROUTE, FlightStatus.CANCELLED}
        ),
        FlightStatus.EN_ROUTE: frozenset(
            {FlightStatus.LANDED, FlightStatus.CANCELLED}
        ),
    }

    def __init__(self, callsign, origin, destination):
        self.callsign = self.normalize_callsign(callsign)
        self.origin = origin
        self.destination = destination
        self.status = FlightStatus.SCHEDULED
        self._track = []

    @staticmethod
    def normalize_callsign(callsign):
        normalized = str(callsign).strip().upper()
        if not normalized or not normalized.isalnum():
            raise ValueError(
                f"callsign must be non-empty and alphanumeric: {callsign!r}"
            )
        return normalized

    def update_position(self, timestamp, position):
        """Append a ``(timestamp, position)`` sample to the flight track."""
        if self.status in self.TERMINAL_STATES:
            raise InvalidTransitionError(
                f"cannot update position of flight {self.callsign} in "
                f"terminal state {self.status.value!r}"
            )
        ts = float(timestamp)
        if self._track and ts <= self._track[-1][0]:
            raise ValueError("position timestamps must be strictly increasing")
        if not isinstance(position, Position):
            position = Position(position[0], position[1])
        self._track.append((ts, position))

    @property
    def current_position(self):
        """The most recent :class:`Position`, or ``None`` before any update."""
        return self._track[-1][1] if self._track else None

    @property
    def distance_flown(self):
        """Total great-circle distance covered so far, in kilometres."""
        total = 0.0
        for (_, start), (_, end) in zip(self._track, self._track[1:]):
            total += start.distance_to(end)
        return total

    def set_status(self, new_status):
        """Move the flight to ``new_status`` if the transition is allowed."""
        if not isinstance(new_status, FlightStatus):
            new_status = FlightStatus(new_status)
        if new_status is self.status:
            return
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, frozenset())
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"cannot transition flight {self.callsign} from "
                f"{self.status.value!r} to {new_status.value!r}"
            )
        self.status = new_status

    def to_dict(self):
        """Return a JSON-serialisable representation of the flight."""
        return {
            "callsign": self.callsign,
            "origin": self.origin,
            "destination": self.destination,
            "status": self.status.value,
            "track": [
                {"timestamp": ts, "latitude": pos.latitude, "longitude": pos.longitude}
                for ts, pos in self._track
            ],
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a :class:`Flight` from :meth:`to_dict` output."""
        flight = cls(data["callsign"], data["origin"], data["destination"])
        for item in data["track"]:
            flight.update_position(
                item["timestamp"], Position(item["latitude"], item["longitude"])
            )
        flight.status = FlightStatus(data["status"])
        return flight
