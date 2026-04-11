// donorpulse-frontend\src\app\admin\dashboard\page.tsx
'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  Shield, 
  Users, 
  CheckCircle, 
  XCircle, 
  LogOut,
  Eye,
  Check,
  Ban
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import axios from 'axios'

interface Hospital {
  id: string
  name: string
  type: string
  email: string
  phone: string
  username: string
  city: string
  license_number: string
  created_at: string
  is_active?: boolean
}

export default function AdminDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [admin, setAdmin] = useState<any>(null)
  const [pendingHospitals, setPendingHospitals] = useState<Hospital[]>([])
  const [verifiedHospitals, setVerifiedHospitals] = useState<Hospital[]>([])
  const [stats, setStats] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<'pending' | 'verified'>('pending')
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    const adminData = localStorage.getItem('admin')
    
    if (!token) {
      router.push('/admin/login')
    } else {
      setAdmin(JSON.parse(adminData || '{}'))
      fetchData()
    }
  }, [router])

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('admin_token')
      const headers = { Authorization: `Bearer ${token}` }
      
      const [pendingRes, verifiedRes, statsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/v1/admin/hospitals/pending', { headers }),
        axios.get('http://localhost:8000/api/v1/admin/hospitals/verified', { headers }),
        axios.get('http://localhost:8000/api/v1/admin/stats', { headers })
      ])
      
      setPendingHospitals(pendingRes.data.hospitals)
      setVerifiedHospitals(verifiedRes.data.hospitals)
      setStats(statsRes.data)
    } catch (error) {
      console.error('Failed to fetch data', error)
    } finally {
      setLoading(false)
    }
  }

  const verifyHospital = async (hospitalId: string) => {
    try {
      const token = localStorage.getItem('admin_token')
      await axios.patch(
        `http://localhost:8000/api/v1/admin/hospitals/${hospitalId}/verify`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert('Hospital verified successfully!')
      fetchData()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to verify hospital')
    }
  }

  const rejectHospital = async (hospitalId: string) => {
    if (!confirm('Are you sure you want to reject this hospital registration?')) return
    
    try {
      const token = localStorage.getItem('admin_token')
      await axios.patch(
        `http://localhost:8000/api/v1/admin/hospitals/${hospitalId}/reject`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert('Hospital registration rejected')
      fetchData()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to reject hospital')
    }
  }

  const toggleHospitalActive = async (hospitalId: string, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('admin_token')
      await axios.patch(
        `http://localhost:8000/api/v1/admin/hospitals/${hospitalId}/toggle-active`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert(`Hospital ${currentStatus ? 'deactivated' : 'activated'} successfully`)
      fetchData()
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to toggle status')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin')
    router.push('/admin/login')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-sm text-gray-500">
                  Welcome, <strong>{admin?.full_name || admin?.username}</strong> ({admin?.role})
                </p>
              </div>
            </div>
            <Button variant="secondary" onClick={handleLogout} className="flex items-center space-x-2">
              <LogOut className="h-4 w-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Total Hospitals</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.hospitals.total}</p>
                </div>
              </div>
            </Card>
            
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Pending Verification</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats.hospitals.pending}</p>
                </div>
                <Clock className="h-10 w-10 text-yellow-200" />
              </div>
            </Card>
            
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Verified Hospitals</p>
                  <p className="text-3xl font-bold text-green-600">{stats.hospitals.verified}</p>
                </div>
                <CheckCircle className="h-10 w-10 text-green-200" />
              </div>
            </Card>
            
            <Card>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Total Donors</p>
                  <p className="text-3xl font-bold text-purple-600">{stats.donors.total}</p>
                </div>
                <Users className="h-10 w-10 text-purple-200" />
              </div>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('pending')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Pending Verification ({pendingHospitals.length})
            </button>
            <button
              onClick={() => setActiveTab('verified')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'verified'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Verified Hospitals ({verifiedHospitals.length})
            </button>
          </nav>
        </div>

        {/* Pending Hospitals List */}
        {activeTab === 'pending' && (
          <Card title="Pending Hospital Verifications">
            {pendingHospitals.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No pending verifications
              </div>
            ) : (
              <div className="space-y-4">
                {pendingHospitals.map((hospital) => (
                  <div key={hospital.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="text-lg font-semibold">{hospital.name}</h3>
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">
                            Pending
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <p><span className="font-medium">Type:</span> {hospital.type.toUpperCase()}</p>
                          <p><span className="font-medium">License:</span> {hospital.license_number}</p>
                          <p><span className="font-medium">Email:</span> {hospital.email}</p>
                          <p><span className="font-medium">Phone:</span> {hospital.phone}</p>
                          <p><span className="font-medium">Username:</span> {hospital.username}</p>
                          <p><span className="font-medium">City:</span> {hospital.city}</p>
                          <p className="col-span-2"><span className="font-medium">Registered:</span> {new Date(hospital.created_at).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="success"
                          onClick={() => verifyHospital(hospital.id)}
                          className="flex items-center gap-1"
                        >
                          <Check className="h-4 w-4" />
                          Verify
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => rejectHospital(hospital.id)}
                          className="flex items-center gap-1"
                        >
                          <Ban className="h-4 w-4" />
                          Reject
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Verified Hospitals List */}
        {activeTab === 'verified' && (
          <Card title="Verified Hospitals">
            {verifiedHospitals.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No verified hospitals yet
              </div>
            ) : (
              <div className="space-y-4">
                {verifiedHospitals.map((hospital) => (
                  <div key={hospital.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="text-lg font-semibold">{hospital.name}</h3>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            hospital.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {hospital.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <p><span className="font-medium">Type:</span> {hospital.type.toUpperCase()}</p>
                          <p><span className="font-medium">Email:</span> {hospital.email}</p>
                          <p><span className="font-medium">Phone:</span> {hospital.phone}</p>
                          <p><span className="font-medium">City:</span> {hospital.city}</p>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button
                          size="sm"
                          variant={hospital.is_active ? 'danger' : 'success'}
                          onClick={() => toggleHospitalActive(hospital.id, hospital.is_active || false)}
                        >
                          {hospital.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}

// Add Clock icon import
import { Clock } from 'lucide-react'