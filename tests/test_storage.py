"""Unit tests for flight_tracker.storage."""

import json
import os

import pytest

from flight_tracker.errors import StorageError
from flight_tracker.models import Flight, FlightStatus, Position
from flight_tracker.storage import load_flights, save_flights
from flight_tracker.tracker import FlightTracker


def _tracker():
    tracker = FlightTracker()
    alpha = tracker.create_flight("AA1", "JFK", "LHR")
    alpha.update_position(0.0, (40.64, -73.78))
    alpha.update_position(1.0, (45.0, -60.0))
    beta = tracker.create_flight("BA2", "SFO", "NRT")
    beta.update_position(0.0, (37.61, -122.37))
    beta.set_status(FlightStatus.EN_ROUTE)
    beta.set_status(FlightStatus.LANDED)
    return tracker


class TestSaveFlights:
    def test_creates_parent_directories(self, tmp_path):
        target = tmp_path / "nested" / "dir" / "flights.json"
        save_flights([], target)
        assert target.exists()

    def test_overwrites_existing_file(self, tmp_path):
        target = tmp_path / "flights.json"
        save_flights([], target)
        save_flights([Flight("AA1", "A", "B")], target)
        assert len(load_flights(target)) == 1


class TestLoadFlights:
    def test_round_trip_preserves_state(self, tmp_path):
        target = tmp_path / "flights.json"
        _tracker().save(target)
        loaded = FlightTracker.load(target)
        assert [f.callsign for f in loaded] == ["AA1", "BA2"]
        alpha, beta = loaded.list_flights()
        assert alpha.current_position == Position(45.0, -60.0)
        assert alpha.distance_flown == pytest.approx(
            Position(40.64, -73.78).distance_to(Position(45.0, -60.0))
        )
        assert beta.status is FlightStatus.LANDED

    def test_module_level_functions_round_trip(self, tmp_path):
        target = tmp_path / "flights.json"
        save_flights(list(_tracker()), target)
        loaded = load_flights(target)
        assert [f.callsign for f in loaded] == ["AA1", "BA2"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(StorageError):
            load_flights(tmp_path / "missing.json")

    def test_directory_path_raises(self, tmp_path):
        with pytest.raises(StorageError):
            load_flights(tmp_path)

    def test_corrupt_json_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text("{not json", encoding="utf-8")
        with pytest.raises(StorageError):
            load_flights(target)

    def test_non_list_payload_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(json.dumps({"callsign": "AA1"}), encoding="utf-8")
        with pytest.raises(StorageError):
            load_flights(target)

    def test_entry_missing_keys_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(json.dumps([{"callsign": "AA1"}]), encoding="utf-8")
        with pytest.raises(StorageError):
            load_flights(target)

    def test_unknown_status_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(
            json.dumps(
                [
                    {
                        "callsign": "AA1",
                        "origin": "A",
                        "destination": "B",
                        "status": "teleporting",
                        "track": [],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(StorageError):
            load_flights(target)

    def test_track_entry_missing_fields_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(
            json.dumps(
                [
                    {
                        "callsign": "AA1",
                        "origin": "A",
                        "destination": "B",
                        "status": "scheduled",
                        "track": [{"timestamp": 0.0}],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(StorageError):
            load_flights(target)

    def test_landed_flight_with_track_loads(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(
            json.dumps(
                [
                    {
                        "callsign": "AA1",
                        "origin": "A",
                        "destination": "B",
                        "status": "landed",
                        "track": [
                            {"timestamp": 0.0, "latitude": 0.0, "longitude": 0.0}
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        loaded = load_flights(target)
        assert len(loaded) == 1
        assert loaded[0].status is FlightStatus.LANDED
        assert loaded[0].current_position == Position(0, 0)

    def test_non_monotonic_track_raises(self, tmp_path):
        target = tmp_path / "flights.json"
        target.write_text(
            json.dumps(
                [
                    {
                        "callsign": "AA1",
                        "origin": "A",
                        "destination": "B",
                        "status": "en_route",
                        "track": [
                            {"timestamp": 5.0, "latitude": 0.0, "longitude": 0.0},
                            {"timestamp": 1.0, "latitude": 1.0, "longitude": 1.0},
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        with pytest.raises(StorageError):
            load_flights(target)


class TestSaveFailures:
    def test_save_onto_directory_raises(self, tmp_path):
        with pytest.raises(StorageError):
            save_flights([], tmp_path)

    def test_cleanup_failure_still_raises_storage_error(
        self, tmp_path, monkeypatch
    ):
        target = tmp_path / "flights.json"

        def _fail(*_args, **_kwargs):
            raise OSError("injected failure")

        monkeypatch.setattr(os, "replace", _fail)
        monkeypatch.setattr(os, "unlink", _fail)
        with pytest.raises(StorageError):
            save_flights([], target)
