# flight-tracker

## Admin stop

Stopping the tracker is restricted to admin users and is idempotent:

```python
from flight_tracker import FlightTracker, User

tracker = FlightTracker()
tracker.start()
tracker.track("AA100")

tracker.admin_stop(User(name="omar", is_admin=True))  # -> "stopped"
tracker.admin_stop(User(name="omar", is_admin=True))  # -> "already-stopped"
```

Non-admin users raise `AdminPermissionError` and the tracker state is left
untouched.

Run the tests with:

```
python -m unittest discover -s tests -t . -v
```
