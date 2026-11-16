"""Tests for the admin stop functionality of the flight tracker."""

import unittest

from flight_tracker import AdminPermissionError, AdminRegistry, FlightTracker, User


class AdminStopTests(unittest.TestCase):
    def setUp(self):
        self.registry = AdminRegistry()
        self.tracker = FlightTracker(admin_registry=self.registry)
        self.tracker.start()
        self.admin = User(name="omar")
        self.regular = User(name="guest")
        self.registry.register_admin("omar")

    # -- lifecycle errors --------------------------------------------------

    def test_start_twice_raises(self):
        with self.assertRaises(RuntimeError):
            self.tracker.start()
        # Tracker remains running after a rejected second start.
        self.assertTrue(self.tracker.is_running)

    def test_track_when_not_running_raises(self):
        fresh = FlightTracker()
        with self.assertRaises(RuntimeError):
            fresh.track("AA100")
        self.assertEqual(fresh.tracked_flights, ())

    def test_track_records_multiple_flights(self):
        self.tracker.track("AA100")
        self.tracker.track("BA200")
        self.assertEqual(self.tracked_flights_snapshot(), ("AA100", "BA200"))

    def tracked_flights_snapshot(self):
        return self.tracker.tracked_flights

    # -- authorization boundary --------------------------------------------

    def test_unregistered_user_cannot_stop(self):
        # User carries no authority; admin status is matched by name against
        # the registry, so an unregistered user is denied.
        fresh_tracker = FlightTracker(admin_registry=self.registry)
        fresh_tracker.start()
        with self.assertRaises(AdminPermissionError):
            fresh_tracker.admin_stop(User(name="guest"))
        self.assertTrue(fresh_tracker.is_running)

    def test_tracker_without_registry_denies_everyone(self):
        fresh = FlightTracker()
        fresh.start()
        with self.assertRaises(AdminPermissionError):
            fresh.admin_stop(User(name="omar"))
        self.assertTrue(fresh.is_running)

    def test_revoke_admin_denies_stop(self):
        self.registry.revoke_admin("omar")
        with self.assertRaises(AdminPermissionError):
            self.tracker.admin_stop(self.admin)
        self.assertTrue(self.tracker.is_running)

    def test_revoke_non_registered_admin_is_noop(self):
        self.registry.revoke_admin("nobody-here")  # must not raise

    def test_register_admin_grants_stop(self):
        self.registry.register_admin("guest")
        self.assertEqual(self.tracker.admin_stop(self.regular), "stopped")

    def test_registry_is_admin(self):
        self.assertTrue(self.registry.is_admin(self.admin))
        self.assertFalse(self.registry.is_admin(self.regular))

    # -- authorization ----------------------------------------------------

    def test_admin_can_stop_running_tracker(self):
        self.assertEqual(self.tracker.admin_stop(self.admin), "stopped")
        self.assertFalse(self.tracker.is_running)

    def test_non_admin_cannot_stop(self):
        self.tracker.track("AA100")
        with self.assertRaises(AdminPermissionError):
            self.tracker.admin_stop(self.regular)
        # State must be untouched after a denied stop.
        self.assertTrue(self.tracker.is_running)
        self.assertEqual(self.tracker.tracked_flights, ("AA100",))

    def test_denied_stop_is_a_permission_error(self):
        # AdminPermissionError subclasses PermissionError.
        with self.assertRaises(PermissionError):
            self.tracker.admin_stop(self.regular)

    # -- idempotency -------------------------------------------------------

    def test_stop_is_idempotent(self):
        self.assertEqual(self.tracker.admin_stop(self.admin), "stopped")
        self.assertEqual(self.tracker.admin_stop(self.admin), "already-stopped")
        self.assertFalse(self.tracker.is_running)

    def test_stop_when_never_started_is_idempotent(self):
        fresh = FlightTracker(admin_registry=self.registry)
        self.assertEqual(fresh.admin_stop(self.admin), "already-stopped")
        self.assertFalse(fresh.is_running)

    # -- state cleanup -----------------------------------------------------

    def test_stop_clears_tracked_flights(self):
        self.tracker.track("AA100")
        self.tracker.track("BA200")
        self.tracker.admin_stop(self.admin)
        self.assertEqual(self.tracker.tracked_flights, ())

    def test_can_restart_after_stop(self):
        self.tracker.admin_stop(self.admin)
        self.tracker.start()
        self.tracker.track("AA100")
        self.assertTrue(self.tracker.is_running)
        self.assertEqual(self.tracker.tracked_flights, ("AA100",))


if __name__ == "__main__":
    unittest.main()
