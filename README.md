# flight-tracker

A lightweight flight tracker with a web UI, built on the Python standard library
(no dependencies required).

## Run

```bash
python app.py
```

Then open http://localhost:8000 in your browser.

## Features

- Web dashboard listing all tracked flights (id, airline, route, status, times)
- Live search across all flight fields
- Positions of en-route flights update automatically every 5 seconds
- Auto-refreshing UI every 10 seconds

## API

- `GET /` — web UI
- `GET /api/flights?q=<term>` — list flights, optionally filtered by search term
- `GET /api/flights/<id>` — a single flight (404 if unknown)
