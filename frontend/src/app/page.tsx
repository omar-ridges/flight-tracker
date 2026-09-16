'use client';

import { useState } from 'react';
import Link from 'next/link';
import FlightSearch from '@/components/FlightSearch';
import FlightDetails from '@/components/FlightDetails';
import { fetchFlight } from '@/lib/api';
import { Flight } from '@/types/flight';

export default function Home() {
  const [flight, setFlight] = useState<Flight | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (flightNumber: string) => {
    setIsLoading(true);
    setError(null);
    setFlight(null);

    try {
      const data = await fetchFlight(flightNumber);
      setFlight(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-sky-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Flight Tracker</h1>
              <p className="text-sm text-gray-500">Track flights in real-time</p>
            </div>
          </div>
        </div>
      </header>

      {/* Search Section */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Track Your Flight
          </h2>
          <p className="text-gray-600">
            Enter a flight number to get real-time status and details
          </p>
        </div>

        <FlightSearch onSearch={handleSearch} isLoading={isLoading} />

        {/* Error Message */}
        {error && (
          <div className="mt-6 max-w-md mx-auto p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Flight Details */}
        {flight && !isLoading && (
          <div className="mt-10">
            <FlightDetails flight={flight} />
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white mt-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
            <p className="text-sm text-gray-500">
              Flight Tracker - Powered by AviationStack
            </p>
            <Link
              href="/legal"
              className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
            >
              Legal
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
