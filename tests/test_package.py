"""Tests for the public package API and error hierarchy."""

import flight_tracker


def test_public_api_exports():
    for name in flight_tracker.__all__:
        assert hasattr(flight_tracker, name), name
    assert isinstance(flight_tracker.__version__, str)


def test_error_hierarchy():
    base = flight_tracker.FlightTrackerError
    for exc in (
        flight_tracker.UnknownFlightError,
        flight_tracker.DuplicateFlightError,
        flight_tracker.InvalidTransitionError,
        flight_tracker.StorageError,
    ):
        assert issubclass(exc, base)
    assert issubclass(base, Exception)
