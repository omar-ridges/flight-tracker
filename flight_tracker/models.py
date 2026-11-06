"""Domain models for the flight tracker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    lat: float
    lon: float

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "city": self.city,
            "lat": self.lat,
            "lon": self.lon,
        }


@dataclass
class Flight:
    flight_number: str
    airline: str
    aircraft: str
    origin: Airport
    destination: Airport
    departure: datetime
    arrival: datetime
    gate: Optional[str] = None
    delay_minutes: int = 0
    forced_status: Optional[str] = None

    def status(self, now: Optional[datetime] = None) -> str:
        if self.forced_status:
            return self.forced_status
        now = now or utcnow()
        if now >= self.arrival:
            return "Landed"
        if now >= self.departure:
            return "En Route"
        if self.delay_minutes:
            return "Delayed"
        return "Scheduled"

    def progress(self, now: Optional[datetime] = None) -> float:
        """Fraction of the journey completed, clamped to [0, 1]."""
        now = now or utcnow()
        total = (self.arrival - self.departure).total_seconds()
        done = (now - self.departure).total_seconds()
        return max(0.0, min(1.0, done / total))

    def position(self, now: Optional[datetime] = None) -> dict:
        """Approximate aircraft position interpolated along the route."""
        p = self.progress(now)
        return {
            "lat": round(self.origin.lat + (self.destination.lat - self.origin.lat) * p, 4),
            "lon": round(self.origin.lon + (self.destination.lon - self.origin.lon) * p, 4),
        }

    def to_dict(self, now: Optional[datetime] = None) -> dict:
        return {
            "flight_number": self.flight_number,
            "airline": self.airline,
            "aircraft": self.aircraft,
            "origin": self.origin.as_dict(),
            "destination": self.destination.as_dict(),
            "departure": self.departure.isoformat(),
            "arrival": self.arrival.isoformat(),
            "gate": self.gate,
            "delay_minutes": self.delay_minutes,
            "status": self.status(now),
            "progress": round(self.progress(now), 4),
            "position": self.position(now),
        }
