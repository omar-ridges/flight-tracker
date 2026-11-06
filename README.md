# flight-tracker

A lightweight flight tracker with a live web UI, built entirely with the
Python standard library — no third-party dependencies required.

## Features

- **Live dashboard** — the flight table auto-refreshes every 5 seconds with
current status, progress, and approximate aircraft position.
- **Search** — filter by flight number, airline, aircraft, airport code, or
city (e.g. `JFK`, `Emirates`, `London`).
- **Flight details** — click any row for a modal with the full route,
schedule vs. estimated times, delays, progress, and position.
- **Simulated tracking** — positions and statuses are derived from each
flight's schedule, so the dashboard always shows a realistic live mix of
en-route, landed, scheduled, delayed, and cancelled flights.
- **JSON API** — the same data is available programmatically.

## Quick start

```bash
python app.py                 # or: python -m flight_tracker
# then open http://127.0.0.1:8000
```

Options: `--host` (default `127.0.0.1`) and `--port` (default `8000`).

## API

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/` | Web UI |
| GET | `/api/flights?q=<query>` | Flight list (optional search) |
| GET | `/api/flights/{flight_number}` | Single flight detail |

## Project layout

```
app.py                    # entry point (python app.py)
flight_tracker/
  models.py               # Airport / Flight domain models
  store.py                # in-memory store + seeded sample schedule
  server.py               # stdlib HTTP server (UI, static, JSON API)
  app.py                  # CLI argument parsing / main()
templates/index.html      # web UI markup
static/style.css          # styles
static/app.js             # rendering, search, auto-refresh, modal
tests/test_flight_tracker.py
```

## Testing

```bash
python -m unittest discover -s tests -v
```