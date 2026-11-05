"""Unit tests for flight_tracker.models."""

import math

import pytest

from flight_tracker.errors import InvalidTransitionError
from flight_tracker.models import EARTH_RADIUS_KM, Flight, FlightStatus, Position


class TestPosition:
    def test_valid_position_coerces_to_float(self):
        pos = Position("10", "-20")
        assert pos.latitude == 10.0
        assert pos.longitude == -20.0

    @pytest.mark.parametrize(
        "lat,lon",
        [(0, 0), (90, 0), (-90, 0), (0, 180), (0, -180)],
    )
    def test_boundary_coordinates_are_valid(self, lat, lon):
        pos = Position(lat, lon)
        assert pos.latitude == lat
        assert pos.longitude == lon

    @pytest.mark.parametrize(
        "lat,lon",
        [(90.0001, 0), (-90.0001, 0), (0, 180.0001), (0, -180.0001)],
    )
    def test_out_of_range_coordinates_raise(self, lat, lon):
        with pytest.raises(ValueError):
            Position(lat, lon)

    def test_non_numeric_coordinates_raise(self):
        with pytest.raises(ValueError):
            Position("north", 0)

    def test_distance_to_self_is_zero(self):
        pos = Position(52.31, 13.02)
        assert pos.distance_to(Position(52.31, 13.02)) == pytest.approx(0.0)

    def test_one_degree_at_equator(self):
        assert Position(0, 0).distance_to(Position(0, 1)) == pytest.approx(
            111.195, abs=0.5
        )

    def test_pole_to_pole_distance(self):
        dist = Position(90, 0).distance_to(Position(-90, 0))
        assert dist == pytest.approx(math.pi * EARTH_RADIUS_KM, rel=1e-9)

    def test_distance_across_antimeridian(self):
        dist = Position(0, 179.5).distance_to(Position(0, -179.5))
        assert dist == pytest.approx(111.195, abs=0.5)

    def test_equality(self):
        assert Position(1, 2) == Position(1.0, 2.0)
        assert Position(1, 2) != Position(1, 2.5)
        assert Position(1, 2) != "not a position"

    def test_repr(self):
        assert repr(Position(1, 2)) == "Position(latitude=1.0, longitude=2.0)"


class TestFlightCreation:
    def test_callsign_is_normalised(self):
        assert Flight(" ba123 ", "JFK", "LHR").callsign == "BA123"

    @pytest.mark.parametrize("bad", ["", "   ", "AB-12", "FL 7"])
    def test_invalid_callsign_raises(self, bad):
        with pytest.raises(ValueError):
            Flight(bad, "JFK", "LHR")

    def test_new_flight_starts_scheduled_with_empty_track(self):
        flight = Flight("BA123", "JFK", "LHR")
        assert flight.origin == "JFK"
        assert flight.destination == "LHR"
        assert flight.status is FlightStatus.SCHEDULED
        assert flight.current_position is None
        assert flight.distance_flown == 0.0


class TestPositionUpdates:
    def test_update_position_appends_track(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.update_position(1.0, Position(1, 1))
        flight.update_position(2.0, Position(2, 2))
        assert flight.current_position == Position(2, 2)
        assert flight.distance_flown > 0.0

    def test_update_position_accepts_tuple(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.update_position(0.0, (5.0, 6.0))
        assert flight.current_position == Position(5, 6)

    def test_equal_timestamp_raises(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.update_position(10.0, (0, 0))
        with pytest.raises(ValueError):
            flight.update_position(10.0, (1, 1))

    def test_decreasing_timestamp_raises(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.update_position(10.0, (0, 0))
        with pytest.raises(ValueError):
            flight.update_position(5.0, (1, 1))

    def test_invalid_timestamp_type_raises(self):
        flight = Flight("BA123", "JFK", "LHR")
        with pytest.raises(ValueError):
            flight.update_position("soon", (0, 0))

    def test_invalid_position_payload_raises(self):
        flight = Flight("BA123", "JFK", "LHR")
        with pytest.raises(ValueError):
            flight.update_position(0.0, "nowhere")

    def test_cannot_update_position_after_landing(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.update_position(0.0, (0, 0))
        flight.set_status(FlightStatus.EN_ROUTE)
        flight.set_status(FlightStatus.LANDED)
        with pytest.raises(InvalidTransitionError):
            flight.update_position(1.0, (1, 1))

    def test_cannot_update_position_after_cancellation(self):
        flight = Flight("BA123", "JFK", "LHR")
        flight.set_status(FlightStatus.CANCELLED)
        with pytest.raises(InvalidTransitionError):
            flight.update_position(0.0, (0, 0))


class TestStatusTransitions:
    def test_scheduled_to_en_route(self):
        flight = Flight("BA1", "JFK", "LHR")
        flight.set_status(FlightStatus.EN_ROUTE)
        assert flight.status is FlightStatus.EN_ROUTE

    def test_status_accepts_string_value(self):
        flight = Flight("BA1", "JFK", "LHR")
        flight.set_status("en_route")
        assert flight.status is FlightStatus.EN_ROUTE

    def test_unknown_status_string_raises(self):
        flight = Flight("BA1", "JFK", "LHR")
        with pytest.raises(ValueError):
            flight.set_status("teleporting")

    def test_setting_same_status_is_a_noop(self):
        flight = Flight("BA1", "JFK", "LHR")
        flight.set_status(FlightStatus.SCHEDULED)
        assert flight.status is FlightStatus.SCHEDULED

    def test_full_lifecycle_to_landed(self):
        flight = Flight("BA1", "JFK", "LHR")
        flight.set_status(FlightStatus.EN_ROUTE)
        flight.set_status(FlightStatus.LANDED)
        assert flight.status is FlightStatus.LANDED

    @staticmethod
    def _advance_to(flight, status):
        legal_paths = {
            FlightStatus.SCHEDULED: [],
            FlightStatus.EN_ROUTE: [FlightStatus.EN_ROUTE],
            FlightStatus.LANDED: [FlightStatus.EN_ROUTE, FlightStatus.LANDED],
            FlightStatus.CANCELLED: [FlightStatus.CANCELLED],
        }
        for step in legal_paths[status]:
            flight.set_status(step)

    @pytest.mark.parametrize(
        "current,target",
        [
            (FlightStatus.LANDED, FlightStatus.SCHEDULED),
            (FlightStatus.LANDED, FlightStatus.EN_ROUTE),
            (FlightStatus.LANDED, FlightStatus.CANCELLED),
            (FlightStatus.CANCELLED, FlightStatus.SCHEDULED),
            (FlightStatus.CANCELLED, FlightStatus.EN_ROUTE),
            (FlightStatus.CANCELLED, FlightStatus.LANDED),
            (FlightStatus.SCHEDULED, FlightStatus.LANDED),
            (FlightStatus.EN_ROUTE, FlightStatus.SCHEDULED),
        ],
    )
    def test_disallowed_transitions_raise(self, current, target):
        flight = Flight("BA1", "JFK", "LHR")
        self._advance_to(flight, current)
        with pytest.raises(InvalidTransitionError):
            flight.set_status(target)
