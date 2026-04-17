// donorpulse-frontend\src\app\page.tsx
'use client'

import Link from 'next/link'
import { Droplet, Heart, Building2, MessageCircle, Calendar, Activity, CheckCircle, Zap } from 'lucide-react'

export default function Home() {
  const features = [
    {
      icon: <Zap className="h-6 w-6 text-yellow-500" />,
      title: "Real-time Alerts",
      description: "Instant WhatsApp notifications when hospitals need your blood type"
    },
    {
      icon: <MessageCircle className="h-6 w-6 text-green-500" />,
      title: "SMS Commands",
      description: "Manage your profile with simple text messages"
    },
    {
      icon: <Calendar className="h-6 w-6 text-blue-500" />,
      title: "Easy Booking",
      description: "Schedule appointments at your convenience"
    },
    {
      icon: <Activity className="h-6 w-6 text-red-500" />,
      title: "Smart Matching",
      description: "Automatic donor matching based on blood type and location"
    }
  ]

  const smsCommands = [
    { cmd: "STATUS", desc: "Check eligibility" },
    { cmd: "AVAILABLE", desc: "Turn on alerts" },
    { cmd: "UPDATE", desc: "Get profile link" },
    { cmd: "YES/NO", desc: "Respond to requests" },
    { cmd: "HELP", desc: "All commands" }
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 to-blue-800 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <Droplet className="h-16 w-16 mx-auto mb-4 text-red-300" />
            <h1 className="text-4xl lg:text-5xl font-bold mb-4">
              DonorPulse
            </h1>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Instant blood donation matching. Get notified when hospitals need your blood type.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/donor/register">
                <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition flex items-center justify-center gap-2">
                  <Heart className="h-5 w-5" />
                  Become a Donor
                </button>
              </Link>
              <Link href="/hospital/register">
                <button className="bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-6 rounded-lg transition backdrop-blur-sm flex items-center justify-center gap-2">
                  <Building2 className="h-5 w-5" />
                  Register Hospital
                </button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">Features</h2>
          <p className="text-center text-gray-600 mb-12">Everything you need for blood donation management</p>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <div key={idx} className="text-center p-6 border rounded-lg hover:shadow-lg transition">
                <div className="flex justify-center mb-3">{feature.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SMS Commands */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">SMS Commands</h2>
          <p className="text-center text-gray-600 mb-8">Control your donor profile via text message</p>
          
          <div className="grid sm:grid-cols-2 gap-3">
            {smsCommands.map((cmd, idx) => (
              <div key={idx} className="flex justify-between items-center p-3 bg-white rounded-lg border">
                <code className="font-mono font-bold text-blue-600">{cmd.cmd}</code>
                <span className="text-gray-600 text-sm">{cmd.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-4">How It Works</h2>
          <p className="text-center text-gray-600 mb-12">Simple steps to start saving lives</p>
          
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Register", desc: "Create your donor profile" },
              { step: "2", title: "Get Alerts", desc: "Receive WhatsApp notifications" },
              { step: "3", title: "Respond", desc: "Reply YES to help" },
              { step: "4", title: "Donate", desc: "Save lives at the hospital" }
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-3">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-red-600 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Save Lives?</h2>
          <p className="text-red-100 mb-8">Join our network of blood donors today</p>
          <Link href="/donor/register">
            <button className="bg-white text-red-600 hover:bg-gray-100 font-semibold py-3 px-6 rounded-lg transition inline-flex items-center gap-2">
              <Heart className="h-5 w-5" />
              Register Now
            </button>
          </Link>
        </div>
      </section>
    </div>
  )
}