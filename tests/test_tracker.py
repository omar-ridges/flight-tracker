"""Unit tests for flight_tracker.tracker."""

import pytest

from flight_tracker.errors import (
    DuplicateFlightError,
    InvalidTransitionError,
    UnknownFlightError,
)
from flight_tracker.models import Flight, FlightStatus, Position
from flight_tracker.tracker import FlightTracker


def _flight(callsign="BA123"):
    flight = Flight(callsign, "JFK", "LHR")
    flight.update_position(0.0, (0.0, 0.0))
    return flight


class TestRegistration:
    def test_create_flight_registers_and_normalises(self):
        tracker = FlightTracker()
        flight = tracker.create_flight("ba123", "JFK", "LHR")
        assert flight.callsign == "BA123"
        assert tracker.get_flight("BA123") is flight
        assert len(tracker) == 1

    def test_constructor_accepts_flight_iterable(self):
        tracker = FlightTracker([_flight("AA1"), _flight("ZZ9")])
        assert len(tracker) == 2

    def test_add_rejects_non_flight(self):
        with pytest.raises(TypeError):
            FlightTracker().add("BA123")

    def test_duplicate_registration_raises(self):
        tracker = FlightTracker([_flight("BA123")])
        with pytest.raises(DuplicateFlightError):
            tracker.add(_flight("ba123"))
        with pytest.raises(DuplicateFlightError):
            tracker.create_flight("BA123", "JFK", "LHR")


class TestLookup:
    def test_get_unknown_flight_raises(self):
        with pytest.raises(UnknownFlightError):
            FlightTracker().get_flight("BA999")

    def test_contains_is_case_insensitive(self):
        tracker = FlightTracker([_flight("AA1"), _flight("ZZ9")])
        assert "AA1" in tracker
        assert "zz9" in tracker
        assert "QQ1" not in tracker

    def test_iteration_is_sorted_by_callsign(self):
        tracker = FlightTracker([_flight("ZZ9"), _flight("AA1")])
        assert [f.callsign for f in tracker] == ["AA1", "ZZ9"]

    def test_list_flights_sorted_and_empty(self):
        tracker = FlightTracker()
        assert tracker.list_flights() == []
        tracker.create_flight("ZZ9", "A", "B")
        tracker.create_flight("AA1", "A", "B")
        assert [f.callsign for f in tracker.list_flights()] == ["AA1", "ZZ9"]

    def test_invalid_callsign_lookup_raises_value_error(self):
        with pytest.raises(ValueError):
            FlightTracker().get_flight("")


class TestRemoval:
    def test_remove_flight(self):
        tracker = FlightTracker([_flight("BA123")])
        tracker.remove_flight("ba123")
        assert "BA123" not in tracker
        assert len(tracker) == 0

    def test_remove_unknown_flight_raises(self):
        with pytest.raises(UnknownFlightError):
            FlightTracker().remove_flight("BA999")


class TestDelegation:
    def test_update_position_delegates_to_flight(self):
        tracker = FlightTracker([_flight("BA123")])
        tracker.update_position("BA123", 5.0, (10.0, 10.0))
        assert tracker.get_flight("BA123").current_position == Position(10, 10)

    def test_update_position_unknown_flight_raises(self):
        with pytest.raises(UnknownFlightError):
            FlightTracker().update_position("NOPE", 0.0, (0, 0))

    def test_set_status_delegates_to_flight(self):
        tracker = FlightTracker([_flight("BA123")])
        tracker.set_status("ba123", FlightStatus.EN_ROUTE)
        assert tracker.get_flight("BA123").status is FlightStatus.EN_ROUTE

    def test_set_status_unknown_flight_raises(self):
        with pytest.raises(UnknownFlightError):
            FlightTracker().set_status("NOPE", FlightStatus.EN_ROUTE)

    def test_set_status_propagates_invalid_transitions(self):
        tracker = FlightTracker([_flight("BA123")])
        tracker.set_status("BA123", FlightStatus.EN_ROUTE)
        with pytest.raises(InvalidTransitionError):
            tracker.set_status("BA123", FlightStatus.SCHEDULED)
