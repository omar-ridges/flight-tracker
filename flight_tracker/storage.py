"""JSON persistence for flight data with atomic writes."""

from __future__ import annotations

import json
import os
import tempfile

from .errors import FlightTrackerError, StorageError
from .models import Flight


def save_flights(flights, path):
    """Write ``flights`` to ``path`` atomically, creating parent directories."""
    path = os.fspath(path)
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    payload = [flight.to_dict() for flight in flights]
    fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise StorageError(f"failed to write flight store {path!r}: {exc}") from exc


def load_flights(path):
    """Read a JSON flight store and return the list of flights.

    Any unreadable, malformed, or inconsistent store raises
    :class:`StorageError`.
    """
    path = os.fspath(path)
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise StorageError(f"flight store {path!r} does not exist") from exc
    except json.JSONDecodeError as exc:
        raise StorageError(f"flight store {path!r} is not valid JSON: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"cannot read flight store {path!r}: {exc}") from exc

    if not isinstance(payload, list):
        raise StorageError("flight store must contain a JSON list of flights")

    flights = []
    for index, entry in enumerate(payload):
        try:
            flights.append(Flight.from_dict(entry))
        except (TypeError, KeyError, ValueError, FlightTrackerError) as exc:
            raise StorageError(
                f"invalid flight entry at index {index}: {exc}"
            ) from exc
    return flights
