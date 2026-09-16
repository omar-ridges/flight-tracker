#!/usr/bin/env python3
'''Flask API server that wraps flight lookup for the Next.js frontend.'''

from __future__ import annotations

import os
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS

from flight_cli import (
    ConfigurationError,
    FlightLookupError,
    FlightNotFoundError,
    fetch_flight_details,
    normalize_flight_number,
)

app = Flask(__name__)
CORS(app)

API_KEY_ENV = 'AVIATIONSTACK_API_KEY'


def _flight_to_dict(flight: Any) -> dict[str, Any]:
    '''Convert a raw API flight record into a structured dict for the frontend.'''
    from flight_cli import _as_mapping, _string

    flight_info = _as_mapping(flight.get('flight'))
    airline_info = _as_mapping(flight.get('airline'))
    departure = _as_mapping(flight.get('departure'))
    arrival = _as_mapping(flight.get('arrival'))
    aircraft_info = _as_mapping(flight.get('aircraft'))
    live = _as_mapping(flight.get('live'))

    def _airport(section: Any) -> dict[str, Any]:
        return {
            'airport': _string(section.get('airport')),
            'iata': _string(section.get('iata')),
            'icao': _string(section.get('icao')),
            'terminal': _string(section.get('terminal')),
            'gate': _string(section.get('gate')),
            'delay': section.get('delay'),
            'scheduled': _string(section.get('scheduled')),
            'estimated': _string(section.get('estimated')),
            'actual': _string(section.get('actual')),
        }

    def _aircraft(info: Any) -> dict[str, Any]:
        return {
            'registration': _string(info.get('registration')),
            'model': _string(info.get('model')),
            'iata': _string(info.get('iata')),
            'icao': _string(info.get('icao')),
        }

    def _live_data(live_section: Any) -> dict[str, Any]:
        return {
            'latitude': live_section.get('latitude'),
            'longitude': live_section.get('longitude'),
            'altitude': live_section.get('altitude'),
            'direction': live_section.get('direction'),
            'speed_horizontal': live_section.get('speed_horizontal'),
            'speed_vertical': live_section.get('speed_vertical'),
            'is_ground': live_section.get('is_ground'),
            'updated': _string(live_section.get('updated')),
        }

    return {
        'flight_number': (
            _string(flight_info.get('iata'))
            or _string(flight_info.get('icao'))
            or _string(flight.get('flight_iata'))
            or 'Unknown'
        ),
        'flight_date': _string(flight.get('flight_date')),
        'status': _string(flight.get('flight_status')),
        'airline': {
            'name': _string(airline_info.get('name')),
            'iata': _string(airline_info.get('iata')),
            'icao': _string(airline_info.get('icao')),
        },
        'departure': _airport(departure),
        'arrival': _airport(arrival),
        'aircraft': _aircraft(aircraft_info),
        'live': _live_data(live),
    }


@app.route('/api/flight', methods=['GET'])
def get_flight() -> Any:
    '''Fetch flight details by flight number.'''
    flight_number = request.args.get('flight_number', '').strip()
    if not flight_number:
        return jsonify({'error': 'flight_number query parameter is required'}), 400

    try:
        normalized = normalize_flight_number(flight_number)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400

    api_key = os.getenv(API_KEY_ENV, '').strip()
    if not api_key:
        return jsonify({'error': f'Set {API_KEY_ENV} environment variable.'}), 500

    try:
        record = fetch_flight_details(normalized, api_key=api_key)
        return jsonify(_flight_to_dict(record))
    except FlightNotFoundError as error:
        return jsonify({'error': str(error)}), 404
    except ConfigurationError as error:
        return jsonify({'error': str(error)}), 500
    except FlightLookupError as error:
        return jsonify({'error': str(error)}), 502
    except Exception as error:
        return jsonify({'error': f'Unexpected error: {error}'}), 500


@app.route('/api/health', methods=['GET'])
def health() -> Any:
    '''Health check endpoint.'''
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
