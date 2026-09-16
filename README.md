# flight-tracker

A Python command-line tool and web application for looking up publicly available
flight details by flight number. The default provider is the AviationStack
flights API, which supports IATA flight-number queries.

## Requirements

- Python 3.9 or newer
- A free AviationStack access key for the default API
- Node.js 18 or newer (for the frontend)

Set the key in the environment so it is not exposed in shell history:

```sh
export AVIATIONSTACK_API_KEY=your_access_key
```

## CLI Usage

```sh
python3 flight_cli.py BA123
python3 flight_cli.py 'BA 123' --json
python3 flight_cli.py AA123 DL456
```

The default output is a readable report containing the airline, status, date,
origin, destination, scheduled/estimated/actual times, terminal and gate when
available, aircraft information, and live position/speed fields when the API
provides them. `--json` prints the raw API record for one flight, or an array
when multiple flight numbers are supplied.

`--api-key` is available for one-off use, but the environment variable is
recommended. Invalid flight numbers, missing keys, empty API results, network
failures, timeouts, and non-success API responses are reported on stderr with
a nonzero exit status.

## Web Frontend

A modern Next.js frontend is included in the `frontend/` directory, providing a
user-friendly web interface for tracking flights.

### Tech Stack

- **Next.js 14** with App Router
- **React 18** with TypeScript
- **Tailwind CSS** for responsive styling

### Quick Start

1. Start the Python backend API server:
   ```sh
   python api_server.py
   ```

2. In a new terminal, start the frontend dev server:
   ```sh
   cd frontend
   npm install
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Backend API Endpoints

The Python backend exposes a Flask API:

- `GET /api/health` — Health check
- `GET /api/flight?flight_number=BA123` — Fetch flight details by flight number

The frontend proxies API requests to the backend during development via the
rewrite rule in `frontend/next.config.js`.

### Project Structure

```
.
├── flight_cli.py          # Original CLI tool
├── api_server.py          # Flask backend API
└── frontend/              # Next.js frontend
    ├── src/
    │   ├── app/           # Next.js App Router pages
    │   ├── components/    # React components
    │   ├── lib/           # API client utilities
    │   └── types/         # TypeScript type definitions
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.js
    └── next.config.js
```
