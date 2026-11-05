"""flight-tracker: a small library for tracking flights between airports."""

from .errors import (
    DuplicateFlightError,
    FlightTrackerError,
    InvalidTransitionError,
    StorageError,
    UnknownFlightError,
)
from .models import Flight, FlightStatus, Position
from .storage import load_flights, save_flights
from .tracker import FlightTracker

__all__ = [
    "DuplicateFlightError",
    "Flight",
    "FlightStatus",
    "FlightTracker",
    "FlightTrackerError",
    "InvalidTransitionError",
    "Position",
    "StorageError",
    "UnknownFlightError",
    "load_flights",
    "save_flights",
]

__version__ = "0.1.0"
