#!/usr/bin/env python3
'''Command-line lookup for public flight details.'''

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE_URL = 'https://api.aviationstack.com/v1/flights'
API_KEY_ENV = 'AVIATIONSTACK_API_KEY'
USER_AGENT = 'flight-tracker-cli/1.0'
FLIGHT_NUMBER_PATTERN = re.compile(
    r'^(?=[A-Z0-9]{2,3}[0-9])(?:[A-Z0-9]{2}|[A-Z]{3})[0-9]{1,4}[A-Z]?$'
)


class FlightLookupError(Exception):
    '''Base class for errors that should be shown to CLI users.'''


class ConfigurationError(FlightLookupError):
    '''Raised when the flight API is not configured correctly.'''


class FlightNotFoundError(FlightLookupError):
    '''Raised when the API has no matching flight record.'''


class ApiError(FlightLookupError):
    '''Raised when the flight API returns an unusable response.'''


def _string(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def normalize_flight_number(value: str) -> str:
    '''Normalize common user input while rejecting ambiguous values.'''
    if not isinstance(value, str):
        raise ValueError('Flight number must be text.')

    candidate = value.strip().upper().replace(' ', '').replace('-', '')
    if (
        not FLIGHT_NUMBER_PATTERN.fullmatch(candidate)
        or not any(character.isalpha() for character in candidate)
        or not any(character.isdigit() for character in candidate)
    ):
        raise ValueError(
            'Flight number must look like AA123, BA 123, BAW116, or U2123.'
        )
    return candidate


def _message_from_payload(payload: Any, fallback: str) -> str:
    if isinstance(payload, Mapping):
        error = payload.get('error')
        if isinstance(error, Mapping):
            return (
                _string(error.get('message'))
                or _string(error.get('code'))
                or fallback
            )
        message = _string(payload.get('message'))
        if message:
            return message
    return fallback


def _read_json_response(response: Any) -> Any:
    raw = response.read()
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    if not raw:
        return {}
    return json.loads(raw)


def _http_error_message(error: HTTPError) -> str:
    try:
        return _message_from_payload(_read_json_response(error), f'HTTP {error.code}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return f'HTTP {error.code}'


def fetch_flight_details(
    flight_number: str,
    api_key: Optional[str] = None,
    base_url: str = API_BASE_URL,
    timeout: float = 10.0,
    opener: Optional[Callable[..., Any]] = None,
) -> Mapping[str, Any]:
    '''Fetch one flight record from the configured public flight API.'''
    normalized = normalize_flight_number(flight_number)
    key = (api_key or os.getenv(API_KEY_ENV) or '').strip()
    if not key:
        raise ConfigurationError(
            f'Set {API_KEY_ENV} or pass --api-key before looking up a flight.'
        )

    query = urlencode(
        {
            'access_key': key,
            'flight_iata': normalized,
            'limit': '1',
        }
    )
    separator = '&' if '?' in base_url else '?'
    request = Request(
        f'{base_url}{separator}{query}',
        headers={'User-Agent': USER_AGENT},
    )
    open_url = urlopen if opener is None else opener
    response: Any = None

    try:
        response = open_url(request, timeout=timeout)
        status = int(getattr(response, 'status', 200))
        payload = _read_json_response(response)

        if status >= 400:
            message = _message_from_payload(payload, f'HTTP {status}')
            if status == 401:
                raise ConfigurationError(
                    'The flight API key is missing or invalid.'
                )
            if status == 404:
                raise FlightNotFoundError(
                    f'No flight details were found for {normalized}.'
                )
            raise ApiError(f'Flight API returned HTTP {status}: {message}')

        if (
            isinstance(payload, Mapping)
            and 'error' in payload
            and not payload.get('data')
        ):
            raise ApiError(
                _message_from_payload(payload, 'The flight API returned an error.')
            )

        records = payload.get('data') if isinstance(payload, Mapping) else None
        if not isinstance(records, list) or not records:
            raise FlightNotFoundError(
                f'No flight details were found for {normalized}.'
            )
        record = records[0]
        if not isinstance(record, Mapping):
            raise ApiError('The flight API returned an invalid flight record.')
        return record
    except HTTPError as error:
        message = _http_error_message(error)
        if error.code == 401:
            raise ConfigurationError(
                'The flight API key is missing or invalid.'
            ) from error
        if error.code == 404:
            raise FlightNotFoundError(
                f'No flight details were found for {normalized}.'
            ) from error
        raise ApiError(f'Flight API returned HTTP {error.code}: {message}') from error
    except URLError as error:
        reason = getattr(error, 'reason', error)
        raise ApiError(f'Network error while contacting the flight API: {reason}') from error
    except TimeoutError as error:
        raise ApiError('The flight API request timed out.') from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ApiError('The flight API returned invalid JSON.') from error
    finally:
        if response is not None:
            close = getattr(response, 'close', None)
            if callable(close):
                close()


def _airport_label(section: Mapping[str, Any]) -> str:
    airport = _string(section.get('airport'))
    iata = _string(section.get('iata'))
    icao = _string(section.get('icao'))
    if airport and iata:
        return f'{airport} ({iata})'
    return airport or iata or icao or 'Unknown'


def _schedule_label(section: Mapping[str, Any]) -> str:
    scheduled = _string(section.get('scheduled'))
    estimated = _string(section.get('estimated'))
    actual = _string(section.get('actual'))
    parts: list[str] = []
    if scheduled:
        parts.append(f'scheduled {scheduled}')
    if estimated and estimated != scheduled:
        parts.append(f'estimated {estimated}')
    if actual:
        parts.append(f'actual {actual}')
    return '; '.join(parts) if parts else 'N/A'


def _airport_details(section: Mapping[str, Any]) -> list[str]:
    details: list[str] = []
    terminal = _string(section.get('terminal'))
    gate = _string(section.get('gate'))
    delay = section.get('delay')
    if terminal:
        details.append(f'terminal {terminal}')
    if gate:
        details.append(f'gate {gate}')
    if delay not in (None, '', 0, '0'):
        details.append(f'delay {delay} min')
    return details


def format_flight_details(flight: Mapping[str, Any]) -> str:
    '''Render an API flight record as a compact human-readable report.'''
    flight_info = _as_mapping(flight.get('flight'))
    flight_number = (
        _string(flight_info.get('iata'))
        or _string(flight_info.get('icao'))
        or _string(flight.get('flight_iata'))
        or 'Unknown'
    )
    lines = [f'Flight: {flight_number}']

    flight_date = _string(flight.get('flight_date'))
    if flight_date:
        lines.append(f'Date: {flight_date}')
    status = _string(flight.get('flight_status'))
    lines.append(f'Status: {status or "N/A"}')

    airline_info = _as_mapping(flight.get('airline'))
    airline_parts = [
        _string(airline_info.get('name')),
        _string(airline_info.get('iata')),
        _string(airline_info.get('icao')),
    ]
    airline_parts = [part for part in airline_parts if part]
    lines.append(
        'Airline: '
        + (' / '.join(airline_parts) if airline_parts else 'N/A')
    )

    departure = _as_mapping(flight.get('departure'))
    arrival = _as_mapping(flight.get('arrival'))
    lines.append(f'Departure: {_airport_label(departure)}')
    departure_schedule = _schedule_label(departure)
    if departure_schedule != 'N/A':
        lines.append(f'  Times: {departure_schedule}')
    departure_details = _airport_details(departure)
    if departure_details:
        lines.append('  ' + ', '.join(departure_details))

    lines.append(f'Arrival: {_airport_label(arrival)}')
    arrival_schedule = _schedule_label(arrival)
    if arrival_schedule != 'N/A':
        lines.append(f'  Times: {arrival_schedule}')
    arrival_details = _airport_details(arrival)
    if arrival_details:
        lines.append('  ' + ', '.join(arrival_details))

    aircraft_info = _as_mapping(flight.get('aircraft'))
    aircraft_parts = [
        _string(aircraft_info.get('registration')),
        _string(aircraft_info.get('model')),
        _string(aircraft_info.get('iata')),
        _string(aircraft_info.get('icao')),
    ]
    aircraft_parts = [part for part in aircraft_parts if part]
    lines.append(
        'Aircraft: '
        + (' / '.join(aircraft_parts) if aircraft_parts else 'N/A')
    )

    live = _as_mapping(flight.get('live'))
    live_parts: list[str] = []
    latitude = live.get('latitude')
    longitude = live.get('longitude')
    if latitude not in (None, '') and longitude not in (None, ''):
        live_parts.append(f'position {latitude}, {longitude}')
    elif latitude not in (None, ''):
        live_parts.append(f'latitude {latitude}')
    elif longitude not in (None, ''):
        live_parts.append(f'longitude {longitude}')
    for label, key in (
        ('altitude', 'altitude'),
        ('direction', 'direction'),
        ('horizontal speed', 'speed_horizontal'),
        ('vertical speed', 'speed_vertical'),
    ):
        value = live.get(key)
        if value not in (None, ''):
            live_parts.append(f'{label} {value}')
    if live.get('is_ground') is not None:
        live_parts.append(f'on ground {str(live.get("is_ground")).lower()}')
    updated = _string(live.get('updated'))
    if updated:
        live_parts.append(f'updated {updated}')
    if live_parts:
        lines.append('Live: ' + ', '.join(live_parts))

    return '\n'.join(lines)


def display_flight_details(flight_data: Mapping[str, Any]) -> None:
    '''Print a human-readable flight report.'''
    print(format_flight_details(flight_data))


def _positive_timeout(value: str) -> float:
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('timeout must be a number') from error
    if timeout <= 0:
        raise argparse.ArgumentTypeError('timeout must be greater than zero')
    return timeout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Display publicly available flight details for one or more '
            'flight numbers.'
        )
    )
    parser.add_argument(
        'flight_numbers',
        nargs='+',
        metavar='FLIGHT_NUMBER',
        help='flight number such as AA123, BA 123, BAW116, or U2123',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        dest='json_output',
        help='print the raw API record(s) as JSON instead of a readable report',
    )
    parser.add_argument(
        '--api-key',
        help=(
            'AviationStack access key; AVIATIONSTACK_API_KEY is preferred '
            'over putting a key in the command line'
        ),
    )
    parser.add_argument(
        '--api-base-url',
        default=API_BASE_URL,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        '--timeout',
        type=_positive_timeout,
        default=10.0,
        help='HTTP timeout in seconds (default: 10)',
    )
    parser.add_argument(
        '--version',
        action='version',
        version='flight-tracker 1.0.0',
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        flight_numbers = [normalize_flight_number(value) for value in args.flight_numbers]
        api_key = (args.api_key or os.getenv(API_KEY_ENV) or '').strip()
        if not api_key:
            raise ConfigurationError(
                f'Set {API_KEY_ENV} or pass --api-key before looking up a flight.'
            )
        flights = [
            fetch_flight_details(
                flight_number,
                api_key=api_key,
                base_url=args.api_base_url,
                timeout=args.timeout,
            )
            for flight_number in flight_numbers
        ]
    except FlightLookupError as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    except (TypeError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1

    if args.json_output:
        output = flights[0] if len(flights) == 1 else flights
        json.dump(output, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write('\n')
        return 0

    for index, flight in enumerate(flights, start=1):
        if len(flights) > 1:
            if index > 1:
                sys.stdout.write('\n')
            print(f'Flight {index} of {len(flights)}')
        display_flight_details(flight)
    return 0


if __name__ == '__main__':
    sys.exit(main())
