import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Flight Tracker',
  description: 'Track flights easily through a modern web interface',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  );
}
