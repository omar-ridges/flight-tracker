export interface Airline {
  name: string;
  iata: string;
  icao: string;
}

export interface AirportInfo {
  airport: string;
  iata: string;
  icao: string;
  terminal: string;
  gate: string;
  delay: number | null;
  scheduled: string;
  estimated: string;
  actual: string;
}

export interface Aircraft {
  registration: string;
  model: string;
  iata: string;
  icao: string;
}

export interface LiveData {
  latitude: number | null;
  longitude: number | null;
  altitude: number | null;
  direction: number | null;
  speed_horizontal: number | null;
  speed_vertical: number | null;
  is_ground: boolean | null;
  updated: string;
}

export interface Flight {
  flight_number: string;
  flight_date: string;
  status: string;
  airline: Airline;
  departure: AirportInfo;
  arrival: AirportInfo;
  aircraft: Aircraft;
  live: LiveData;
}

export interface ApiError {
  error: string;
}
