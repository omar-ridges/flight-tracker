"""Core flight tracker with admin-restricted stop functionality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


class AdminPermissionError(PermissionError):
    """Raised when a non-admin user attempts an admin-only action."""


@dataclass(frozen=True)
class User:
    """A tracker user; only admins may stop the tracker."""

    name: str
    is_admin: bool = False


class FlightTracker:
    """Tracks flights in-process.

    Starting is open to any caller, but stopping the tracker is an
    admin-only action (see :meth:`admin_stop`).
    """

    def __init__(self) -> None:
        self._running = False
        self._tracked_flights: List[str] = []

    @property
    def is_running(self) -> bool:
        """Whether the tracker is currently running."""
        return self._running

    @property
    def tracked_flights(self) -> Tuple[str, ...]:
        """Snapshot of the flights tracked since the last (re)start."""
        return tuple(self._tracked_flights)

    def start(self) -> None:
        """Start tracking flights."""
        if self._running:
            raise RuntimeError("tracker is already running")
        self._running = True

    def track(self, flight: str) -> None:
        """Record a flight as being tracked."""
        if not self._running:
            raise RuntimeError("tracker is not running")
        self._tracked_flights.append(flight)

    def admin_stop(self, user: User) -> str:
        """Stop the tracker. Restricted to admins; safe to call repeatedly.

        Returns ``"stopped"`` when a running tracker was stopped and
        ``"already-stopped"`` when the tracker was not running (idempotent
        no-op). Raises :class:`AdminPermissionError` for non-admin users,
        leaving tracker state untouched.
        """
        if not user.is_admin:
            raise AdminPermissionError(
                f"user {user.name!r} is not allowed to stop the tracker"
            )
        if not self._running:
            return "already-stopped"
        self._running = False
        self._tracked_flights.clear()
        return "stopped"
