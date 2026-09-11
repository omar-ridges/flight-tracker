# flight-tracker

A standard-library Python command-line tool for looking up publicly available
flight details by flight number. The default provider is the AviationStack
flights API, which supports IATA flight-number queries.

## Requirements

- Python 3.9 or newer
- A free AviationStack access key for the default API

Set the key in the environment so it is not exposed in shell history:

```sh
export AVIATIONSTACK_API_KEY=your_access_key
```

## Usage

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
