"""Core flight tracker with admin-restricted stop functionality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


class AdminPermissionError(PermissionError):
    """Raised when a non-admin user attempts an admin-only action."""


@dataclass(frozen=True)
class User:
    """A tracker user identity.

    Carries only an identity name. Admin status is resolved by matching
    ``name`` against a trusted :class:`AdminRegistry`. Only the application's
    authentication boundary may construct a ``User`` from a verified identity.
    """

    name: str


class AdminRegistry:
    """Trusted registry of admin identities.

    Only code holding the registry itself may grant or revoke admin status.
    :meth:`FlightTracker.admin_stop` trusts the :class:`User` it receives.
    A caller that constructs ``User(name=...)`` with a registered admin name
    gains admin authority, so the application must construct ``User`` objects
    only from authenticated identities.
    """

    def __init__(self) -> None:
        """Create an empty registry; nobody is an admin by default."""
        self._admins: set[str] = set()

    def register_admin(self, name: str) -> None:
        """Grant admin status to ``name`` (trusted operation only)."""
        self._admins.add(name)

    def revoke_admin(self, name: str) -> None:
        """Revoke admin status from ``name``."""
        self._admins.discard(name)

    def is_admin(self, user: User) -> bool:
        """Whether ``user`` is a registered admin."""
        return user.name in self._admins


class FlightTracker:
    """Tracks flights in-process.

    Starting is open to any caller, but stopping the tracker is an
    admin-only action (see :meth:`admin_stop`).
    """

    def __init__(self, admin_registry: AdminRegistry | None = None) -> None:
        self._running = False
        self._tracked_flights: List[str] = []
        # Deny-by-default: with no registry supplied, nobody can stop the
        # tracker until the application provides its trusted registry.
        self._admin_registry = admin_registry if admin_registry is not None else AdminRegistry()

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
        if not self._admin_registry.is_admin(user):
            raise AdminPermissionError(
                f"user {user.name!r} is not allowed to stop the tracker"
            )
        if not self._running:
            return "already-stopped"
        self._running = False
        self._tracked_flights.clear()
        return "stopped"
