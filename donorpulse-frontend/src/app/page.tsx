// donorpulse-frontend\src\app\page.tsx
'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="flex justify-center mb-4">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
            <span className="text-3xl">🩸</span>
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Save Lives Through Blood Donation
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Join our network of donors and help hospitals save lives when every second counts.
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-8 mb-12">
        {/* Donor Card */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden text-center hover:shadow-lg transition-shadow">
          <div className="p-6">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-3xl">🩸</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold mb-2">Register as Donor</h3>
            <p className="text-gray-600 mb-4">
              Sign up to become a blood donor and help save lives in your community.
            </p>
            <Link href="/donor/register">
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                Register Now
              </button>
            </Link>
          </div>
        </div>

        {/* Hospital Card */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden text-center hover:shadow-lg transition-shadow">
          <div className="p-6">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-3xl">🏥</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold mb-2">Register Hospital</h3>
            <p className="text-gray-600 mb-4">
              Hospitals can register to request blood and manage donors.
            </p>
            <Link href="/hospital/register">
              <button className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
                Register Hospital
              </button>
            </Link>
          </div>
        </div>

        {/* SMS Commands Card */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden text-center hover:shadow-lg transition-shadow">
          <div className="p-6">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-3xl">📱</span>
              </div>
            </div>
            <h3 className="text-xl font-semibold mb-2">SMS Commands</h3>
            <p className="text-gray-600 mb-4">
              After registration, use SMS commands to manage your donor profile.
            </p>
            <div className="text-left bg-gray-50 p-3 rounded-lg">
              <p className="text-sm font-mono">STATUS - Check eligibility</p>
              <p className="text-sm font-mono">UPDATE - Get update link</p>
              <p className="text-sm font-mono">AVAILABLE - Turn on alerts</p>
              <p className="text-sm font-mono">HELP - All commands</p>
            </div>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-blue-800 mb-6">How It Works</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">1</span>
                </div>
                <div className="font-bold text-blue-700 mb-2">Register</div>
                <p className="text-gray-700">Create your donor profile with medical info and location.</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">2</span>
                </div>
                <div className="font-bold text-blue-700 mb-2">Get SMS</div>
                <p className="text-gray-700">Receive welcome SMS with available commands.</p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-white font-bold">3</span>
                </div>
                <div className="font-bold text-blue-700 mb-2">Respond</div>
                <p className="text-gray-700">Reply to alerts when hospitals need your blood type.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}