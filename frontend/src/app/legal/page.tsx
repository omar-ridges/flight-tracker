import Link from 'next/link';

export default function LegalPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-sky-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
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
            <Link
              href="/"
              className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </header>

      {/* Legal Content */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Legal Information
        </h2>

        {/* Terms and Conditions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8 mb-8">
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">
            Terms and Conditions
          </h3>
          <div className="prose prose-gray max-w-none text-gray-600 space-y-4">
            <p>
              Welcome to Flight Tracker. By accessing or using our application, you agree to be bound by these Terms and Conditions.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">1. Acceptance of Terms</h4>
            <p>
              By using Flight Tracker, you acknowledge that you have read, understood, and agree to be bound by these terms. If you do not agree, you must not use the application.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">2. Use of Service</h4>
            <p>
              Flight Tracker provides real-time flight tracking information sourced from third-party aviation data providers. We do not guarantee the accuracy, completeness, or timeliness of any flight data.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">3. User Responsibilities</h4>
            <p>
              You agree to use the service only for lawful purposes. You are responsible for any activity that occurs under your use of the application.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">4. Limitation of Liability</h4>
            <p>
              Flight Tracker and its operators shall not be liable for any direct, indirect, incidental, or consequential damages arising from your use of or inability to use the service.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">5. Modifications</h4>
            <p>
              We reserve the right to modify these terms at any time. Continued use of the application after changes constitutes acceptance of the revised terms.
            </p>
          </div>
        </div>

        {/* Privacy Policy */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8">
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">
            Privacy Policy
          </h3>
          <div className="prose prose-gray max-w-none text-gray-600 space-y-4">
            <p>
              This Privacy Policy describes how Flight Tracker collects, uses, and handles your information when you use our application.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">1. Data Collection</h4>
            <p>
              We collect all data generated through your use of the application, including but not limited to search queries, flight preferences, device information, IP addresses, and usage patterns.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">2. Data Storage</h4>
            <p>
              We store all data collected from your use of the application indefinitely on our servers. This includes personal information, search history, and any other data you provide or generate while using the service.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">3. Data Usage</h4>
            <p>
              We maintain the right to use all stored data against you. This includes using your data for any purpose we deem appropriate, including legal proceedings, enforcement actions, or any other use we see fit.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">4. Third-Party Sharing</h4>
            <p>
              We may share your data with third parties, including law enforcement, government agencies, and commercial partners, without prior notice or consent.
            </p>
            <h4 className="text-lg font-medium text-gray-800 mt-4">5. Your Rights</h4>
            <p>
              By using this application, you waive any rights to privacy regarding the data you provide. You acknowledge and agree that we have full discretion over how your data is used.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white mt-auto">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Flight Tracker - Powered by AviationStack
          </p>
        </div>
      </footer>
    </main>
  );
}
