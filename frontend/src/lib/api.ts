import { Flight, ApiError } from '@/types/flight';

const API_BASE = '/api';

export async function fetchFlight(flightNumber: string): Promise<Flight> {
  const response = await fetch(
    `${API_BASE}/flight?flight_number=${encodeURIComponent(flightNumber)}`
  );

  const data = await response.json();

  if (!response.ok) {
    const errorData = data as ApiError;
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }

  return data as Flight;
}
