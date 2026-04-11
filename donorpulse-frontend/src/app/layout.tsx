import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Droplet } from 'lucide-react'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DonorPulse - Blood Donation Management',
  description: 'Connecting blood donors with hospitals in real-time',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <nav className="bg-blue-600 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-2">
                <Droplet className="h-6 w-6" />
                <h1 className="text-xl font-bold">DonorPulse</h1>
              </div>
              <div className="hidden md:flex space-x-4">
                <a href="/" className="hover:bg-blue-700 px-3 py-2 rounded transition-colors">Home</a>
                <a href="/donor/register" className="hover:bg-blue-700 px-3 py-2 rounded transition-colors">Donor Register</a>
                <a href="/hospital/register" className="hover:bg-blue-700 px-3 py-2 rounded transition-colors">Hospital Register</a>
                <a href="/hospital/login" className="hover:bg-blue-700 px-3 py-2 rounded transition-colors">Hospital Login</a>
              </div>
            </div>
          </div>
        </nav>
        <main className="min-h-screen bg-gray-50">
          {children}
        </main>
        <footer className="bg-gray-800 text-white py-6">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p>&copy; 2024 DonorPulse - Saving Lives Through Blood Donation</p>
          </div>
        </footer>
      </body>
    </html>
  )
}