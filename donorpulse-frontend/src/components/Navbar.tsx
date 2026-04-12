// donorpulse-frontend\src\components\Navbar.tsx
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { Droplet, LogOut, Home, User, Building2, Shield, Menu, X, Heart, Calendar, Activity } from 'lucide-react'

export default function Navbar() {
  const router = useRouter()
  const pathname = usePathname()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [user, setUser] = useState<{
    type: 'hospital' | 'admin' | null
    name?: string
  }>({ type: null })

  useEffect(() => {
    checkAuth()
  }, [pathname])

  const checkAuth = () => {
    // Check for hospital login
    const hospitalToken = localStorage.getItem('access_token')
    const hospitalData = localStorage.getItem('hospital')
    
    // Check for admin login
    const adminToken = localStorage.getItem('admin_token')
    const adminData = localStorage.getItem('admin')
    
    if (adminToken && adminData) {
      try {
        const admin = JSON.parse(adminData)
        setUser({ type: 'admin', name: admin.full_name || admin.username })
        return
      } catch (e) {}
    }
    
    if (hospitalToken && hospitalData) {
      try {
        const hospital = JSON.parse(hospitalData)
        setUser({ type: 'hospital', name: hospital.name })
        return
      } catch (e) {}
    }
    
    setUser({ type: null })
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('hospital')
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin')
    setUser({ type: null })
    setIsMenuOpen(false)
    router.push('/')
  }

  // Navigation links based on user type
  const getNavLinks = () => {
    const links = []
    
    // Home - always visible
    links.push({ href: '/', label: 'Home', icon: <Home className="h-4 w-4" /> })
    
    if (user.type === 'admin') {
      links.push({ href: '/admin/dashboard', label: 'Dashboard', icon: <Shield className="h-4 w-4" /> })
      links.push({ href: '/admin/donors', label: 'Donors', icon: <User className="h-4 w-4" /> })
    } 
    else if (user.type === 'hospital') {
      links.push({ href: '/hospital/dashboard', label: 'Dashboard', icon: <Activity className="h-4 w-4" /> })
      links.push({ href: '/hospital/machines', label: 'Machines', icon: <Building2 className="h-4 w-4" /> })
      links.push({ href: '/hospital/appointments', label: 'Appointments', icon: <Calendar className="h-4 w-4" /> })
      links.push({ href: '/hospital/requests/new', label: 'Blood Request', icon: <Heart className="h-4 w-4" /> })
    } 
    else {
      // Not logged in - show registration/login links
      links.push({ href: '/donor/register', label: 'Donor Register', icon: <User className="h-4 w-4" /> })
      links.push({ href: '/hospital/register', label: 'Hospital Register', icon: <Building2 className="h-4 w-4" /> })
      links.push({ href: '/hospital/login', label: 'Hospital Login', icon: <Building2 className="h-4 w-4" /> })
      links.push({ href: '/admin/login', label: 'Admin Login', icon: <Shield className="h-4 w-4" /> })
    }
    
    return links
  }

  return (
    <nav className="bg-blue-600 text-white shadow-lg sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 hover:opacity-90 transition-opacity">
            <Droplet className="h-6 w-6" />
            <span className="text-xl font-bold">DonorPulse</span>
          </Link>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            {getNavLinks().map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center space-x-1 hover:bg-blue-700 px-3 py-2 rounded transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                {link.icon}
                <span>{link.label}</span>
              </Link>
            ))}
            
            {/* Show user info and logout when logged in */}
            {user.type && (
              <>
                <span className="border-l border-blue-400 h-6 mx-2"></span>
                <div className="flex items-center space-x-3">
                  <span className="text-sm">
                    👋 {user.name}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="flex items-center space-x-1 bg-red-600 hover:bg-red-700 px-3 py-2 rounded transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </>
            )}
          </div>
          
          {/* Mobile menu button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded hover:bg-blue-700 transition-colors"
          >
            {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
        
        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden pb-4 space-y-2">
            {getNavLinks().map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center space-x-2 hover:bg-blue-700 px-3 py-2 rounded transition-colors"
                onClick={() => setIsMenuOpen(false)}
              >
                {link.icon}
                <span>{link.label}</span>
              </Link>
            ))}
            
            {user.type && (
              <div className="border-t border-blue-400 pt-2 mt-2">
                <div className="px-3 py-2 text-sm">
                  👋 Logged in as <strong>{user.name}</strong>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 w-full bg-red-600 hover:bg-red-700 px-3 py-2 rounded transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}