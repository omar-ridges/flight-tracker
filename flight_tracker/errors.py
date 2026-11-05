"""Exception hierarchy for the flight tracker."""


class FlightTrackerError(Exception):
    """Base class for all flight tracker errors."""


class UnknownFlightError(FlightTrackerError):
    """Raised when a lookup finds no flight with the given callsign."""


class DuplicateFlightError(FlightTrackerError):
    """Raised when registering a flight whose callsign already exists."""


class InvalidTransitionError(FlightTrackerError):
    """Raised for illegal flight state or position updates."""


class StorageError(FlightTrackerError):
    """Raised when the flight store cannot be read or written."""
