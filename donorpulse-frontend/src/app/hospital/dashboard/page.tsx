// donorpulse-frontend\src\app\hospital\dashboard\page.tsx
'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Activity, Users, CheckCircle, LogOut } from 'lucide-react'
import { useRouter } from 'next/navigation'

export default function HospitalDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [hospital, setHospital] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const hospitalData = localStorage.getItem('hospital')
    
    if (!token) {
      router.push('/hospital/login')
    } else {
      setHospital(JSON.parse(hospitalData || '{}'))
      setLoading(false)
    }
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('hospital')
    router.push('/')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Hospital Dashboard</h1>
        <Button variant="secondary" onClick={handleLogout} className="flex items-center space-x-2">
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </Button>
      </div>
      
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-blue-800">
          Welcome, <strong>{hospital?.name || 'Hospital'}</strong>!
          {!hospital?.is_verified && (
            <span className="ml-2 text-yellow-600">(Pending Admin Verification)</span>
          )}
          {hospital?.is_verified && (
            <span className="ml-2 text-green-600">(Verified Account)</span>
          )}
        </p>
      </div>
      
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <Card>
          <div className="text-center">
            <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <div className="text-3xl font-bold text-blue-600">0</div>
            <p className="text-gray-600">Active Requests</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <Users className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <div className="text-3xl font-bold text-green-600">0</div>
            <p className="text-gray-600">Donors Matched</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <CheckCircle className="h-8 w-8 text-purple-600 mx-auto mb-2" />
            <div className="text-3xl font-bold text-purple-600">0</div>
            <p className="text-gray-600">Donations Completed</p>
          </div>
        </Card>
      </div>
      
      <Card title="Blood Request Management">
        <p className="text-gray-600 text-center py-8">
          Blood request feature coming soon. You will be able to create and manage blood requests here.
        </p>
        <Button disabled className="w-full opacity-50 cursor-not-allowed">
          Create Blood Request (Coming Soon)
        </Button>
      </Card>
    </div>
  )
}