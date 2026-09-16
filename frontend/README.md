# Flight Tracker Frontend

A modern Next.js frontend for tracking flights, built with React, TypeScript, and Tailwind CSS.

## Features

- **Flight Search**: Enter a flight number (e.g. `BA123`) to look up real-time flight details
- **Flight Details Display**: View comprehensive flight information including:
  - Flight status with color-coded badges
  - Airline information
  - Departure and arrival airport details (terminal, gate, delays)
  - Aircraft information
  - Live position tracking (when available)
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Error Handling**: Clear error messages for invalid flight numbers, missing flights, or API issues
- **Loading States**: Visual feedback during API requests

## Tech Stack

- [Next.js 14](https://nextjs.org/) — React framework with App Router
- [React 18](https://react.dev/) — UI library
- [TypeScript](https://www.typescriptlang.org/) — Type-safe JavaScript
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css          # Global styles with Tailwind directives
│   │   ├── layout.tsx           # Root layout component
│   │   └── page.tsx             # Main page with flight search
│   ├── components/
│   │   ├── FlightSearch.tsx     # Search form component
│   │   └── FlightDetails.tsx    # Flight details display component
│   ├── lib/
│   │   └── api.ts               # API client for backend communication
│   └── types/
│       └── flight.ts            # TypeScript interfaces for flight data
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
└── postcss.config.js
```

## Getting Started

### Prerequisites

- Node.js 18 or newer
- The Python backend API server running (see `../api_server.py`)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

The Next.js dev server automatically proxies `/api/*` requests to the Python backend at `http://localhost:5000`.

### Production Build

```bash
npm run build
npm start
```

## Backend Integration

The frontend communicates with the Python backend via the following API endpoints:

- `GET /api/health` — Health check
- `GET /api/flight?flight_number=BA123` — Fetch flight details

The `next.config.js` includes a rewrite rule to proxy API requests to the backend during development.
