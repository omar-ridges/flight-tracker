import { Flight } from '@/types/flight';

interface FlightDetailsProps {
  flight: Flight;
}

function StatusBadge({ status }: { status: string }) {
  const statusColors: Record<string, string> = {
    scheduled: 'bg-blue-100 text-blue-800',
    active: 'bg-green-100 text-green-800',
    landed: 'bg-gray-100 text-gray-800',
    cancelled: 'bg-red-100 text-red-800',
    diverted: 'bg-yellow-100 text-yellow-800',
    delayed: 'bg-orange-100 text-orange-800',
  };

  const colorClass = statusColors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${colorClass}`}>
      {status}
    </span>
  );
}

function InfoCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function AirportDisplay({ label, info }: { label: string; info: Flight['departure'] }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold text-gray-900">
          {info.iata || info.icao || 'Unknown'}
        </span>
        {info.airport && (
          <span className="text-sm text-gray-600">{info.airport}</span>
        )}
      </div>
      {info.terminal && (
        <p className="text-sm text-gray-600">Terminal {info.terminal}</p>
      )}
      {info.gate && (
        <p className="text-sm text-gray-600">Gate {info.gate}</p>
      )}
      {info.delay && info.delay > 0 && (
        <p className="text-sm text-red-600 font-medium">Delay: {info.delay} min</p>
      )}
      <div className="text-sm text-gray-600 mt-2">
        {info.scheduled && (
          <p>Scheduled: {info.scheduled}</p>
        )}
        {info.estimated && info.estimated !== info.scheduled && (
          <p>Estimated: {info.estimated}</p>
        )}
        {info.actual && (
          <p>Actual: {info.actual}</p>
        )}
      </div>
    </div>
  );
}

export default function FlightDetails({ flight }: FlightDetailsProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{flight.flight_number}</h2>
            {flight.flight_date && (
              <p className="text-sm text-gray-500 mt-1">{flight.flight_date}</p>
            )}
          </div>
          <StatusBadge status={flight.status} />
        </div>
        {flight.airline.name && (
          <p className="text-gray-600 mt-3">
            {flight.airline.name}
            {flight.airline.iata && ` (${flight.airline.iata})`}
          </p>
        )}
      </div>

      {/* Departure & Arrival */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InfoCard title="Departure">
          <AirportDisplay label="Departure" info={flight.departure} />
        </InfoCard>
        <InfoCard title="Arrival">
          <AirportDisplay label="Arrival" info={flight.arrival} />
        </InfoCard>
      </div>

      {/* Aircraft */}
      {(flight.aircraft.model || flight.aircraft.registration) && (
        <InfoCard title="Aircraft">
          <div className="space-y-1">
            {flight.aircraft.model && (
              <p className="text-gray-900 font-medium">{flight.aircraft.model}</p>
            )}
            <div className="flex flex-wrap gap-2 text-sm text-gray-600">
              {flight.aircraft.registration && (
                <span>Reg: {flight.aircraft.registration}</span>
              )}
              {flight.aircraft.iata && (
                <span>IATA: {flight.aircraft.iata}</span>
              )}
              {flight.aircraft.icao && (
                <span>ICAO: {flight.aircraft.icao}</span>
              )}
            </div>
          </div>
        </InfoCard>
      )}

      {/* Live Tracking */}
      {(flight.live.latitude !== null || flight.live.longitude !== null) && (
        <InfoCard title="Live Position">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
            {flight.live.latitude !== null && (
              <div>
                <p className="text-gray-500">Latitude</p>
                <p className="font-medium text-gray-900">{flight.live.latitude}</p>
              </div>
            )}
            {flight.live.longitude !== null && (
              <div>
                <p className="text-gray-500">Longitude</p>
                <p className="font-medium text-gray-900">{flight.live.longitude}</p>
              </div>
            )}
            {flight.live.altitude !== null && (
              <div>
                <p className="text-gray-500">Altitude</p>
                <p className="font-medium text-gray-900">{flight.live.altitude}</p>
              </div>
            )}
            {flight.live.direction !== null && (
              <div>
                <p className="text-gray-500">Direction</p>
                <p className="font-medium text-gray-900">{flight.live.direction}&deg;</p>
              </div>
            )}
            {flight.live.speed_horizontal !== null && (
              <div>
                <p className="text-gray-500">Speed</p>
                <p className="font-medium text-gray-900">{flight.live.speed_horizontal}</p>
              </div>
            )}
            {flight.live.is_ground !== null && (
              <div>
                <p className="text-gray-500">On Ground</p>
                <p className="font-medium text-gray-900">{flight.live.is_ground ? 'Yes' : 'No'}</p>
              </div>
            )}
          </div>
          {flight.live.updated && (
            <p className="text-xs text-gray-400 mt-3">Updated: {flight.live.updated}</p>
          )}
        </InfoCard>
      )}
    </div>
  );
}
