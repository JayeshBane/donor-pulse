// frontend\src\app\hospital\dashboard\page.tsx
'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  Activity, 
  LogOut, 
  Thermometer,
  Settings,
  PlusCircle,
  CheckCircle,
  AlertCircle,
  Clock,
  Calendar,
  Droplet,
  Users,
  Target,
  Bell,
  Shield
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import apiClient from '@/lib/api-client'

interface Machine {
  _id: string
  machine_id: string
  name: string
  machine_type: string
  status: string
  donation_types: string[]
  floor?: string
  room?: string
  is_active: boolean
}

interface BloodRequest {
  id: string
  blood_type: string
  quantity_units: number
  urgency: string
  status: string
  created_at: string
  expires_at: string
  donors_contacted: number
  donors_accepted: number
}

export default function HospitalDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [hospital, setHospital] = useState<any>(null)
  const [machines, setMachines] = useState<Machine[]>([])
  const [bloodRequests, setBloodRequests] = useState<BloodRequest[]>([])
  const [stats, setStats] = useState({
    total: 0,
    available: 0,
    in_use: 0,
    maintenance: 0
  })
  const [requestStats, setRequestStats] = useState({
    active: 0,
    pending: 0,
    fulfilled: 0
  })
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const hospitalData = localStorage.getItem('hospital')
    
    if (!token) {
      router.push('/hospital/login')
    } else {
      const parsedHospital = JSON.parse(hospitalData || '{}')
      setHospital(parsedHospital)
      
      // Check if hospital is verified
      if (!parsedHospital.is_verified) {
        setLoading(false)
        return
      }
      
      fetchMachines(parsedHospital.id)
      fetchBloodRequests(parsedHospital.id)
    }
  }, [router])

  const fetchMachines = async (hospitalId: string) => {
    try {
      // Use apiClient instead of hardcoded localhost URL
      const response = await apiClient.get(`/machines/hospital/${hospitalId}`)
      
      const machinesData = response.data
      setMachines(machinesData)
      
      const available = machinesData.filter((m: Machine) => m.status === 'available').length
      const in_use = machinesData.filter((m: Machine) => m.status === 'in_use').length
      const maintenance = machinesData.filter((m: Machine) => m.status === 'maintenance').length
      
      setStats({
        total: machinesData.length,
        available: available,
        in_use: in_use,
        maintenance: maintenance
      })
    } catch (error) {
      console.error('Failed to fetch machines', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchBloodRequests = async (hospitalId: string) => {
    try {
      // Use apiClient instead of hardcoded localhost URL
      const response = await apiClient.get(`/requests/hospital/${hospitalId}`)
      
      const requests = response.data.requests || []
      setBloodRequests(requests.slice(0, 5))
      
      const active = requests.filter((r: BloodRequest) => 
        ['pending', 'matching', 'broadcasting'].includes(r.status)
      ).length
      const pending = requests.filter((r: BloodRequest) => r.status === 'pending').length
      const fulfilled = requests.filter((r: BloodRequest) => r.status === 'fulfilled').length
      
      setRequestStats({
        active,
        pending,
        fulfilled
      })
    } catch (error: any) {
      // If 403, just show empty state - hospital not verified yet
      if (error.response?.status !== 403) {
        console.error('Failed to fetch blood requests', error)
      }
    }
  }

  const updateMachineStatus = async (machineId: string, status: string) => {
    try {
      // Use apiClient instead of hardcoded localhost URL
      await apiClient.patch(`/machines/${machineId}/status`, { status })
      if (hospital) {
        fetchMachines(hospital.id)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update status')
    }
  }

  const getUrgencyColor = (urgency: string) => {
    switch(urgency) {
      case 'sos': return 'bg-red-100 text-red-800 border-red-200'
      case 'critical': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'urgent': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default: return 'bg-blue-100 text-blue-800 border-blue-200'
    }
  }

  const getUrgencyIcon = (urgency: string) => {
    switch(urgency) {
      case 'sos': return <AlertCircle className="h-4 w-4" />
      case 'critical': return <Target className="h-4 w-4" />
      case 'urgent': return <Bell className="h-4 w-4" />
      default: return <Droplet className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'available': return 'bg-green-100 text-green-800 border-green-200'
      case 'in_use': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'maintenance': return 'bg-red-100 text-red-800 border-red-200'
      case 'cleaning': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'available': return <CheckCircle className="h-4 w-4" />
      case 'in_use': return <Activity className="h-4 w-4" />
      case 'maintenance': return <AlertCircle className="h-4 w-4" />
      case 'cleaning': return <Clock className="h-4 w-4" />
      default: return <Settings className="h-4 w-4" />
    }
  }

  // Show pending verification message
  if (hospital && !hospital.is_verified) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto p-6">
          <Card>
            <div className="text-center py-8">
              <Shield className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Pending Verification</h2>
              <p className="text-gray-600 mb-4">
                Your hospital account is awaiting admin verification.
              </p>
              <p className="text-sm text-gray-500 mb-6">
                You will be able to access all features once your account is verified.
                Please check back later or contact support.
              </p>
              <Button 
                variant="secondary" 
                onClick={() => {
                  localStorage.removeItem('access_token')
                  localStorage.removeItem('hospital')
                  router.push('/')
                }}
              >
                Return to Home
              </Button>
            </div>
          </Card>
        </div>
      </div>
    )
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Machine Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Total Machines</p>
                <p className="text-3xl font-bold text-blue-600">{stats.total}</p>
              </div>
              <Thermometer className="h-10 w-10 text-blue-200" />
            </div>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Available</p>
                <p className="text-3xl font-bold text-green-600">{stats.available}</p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-200" />
            </div>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">In Use</p>
                <p className="text-3xl font-bold text-blue-600">{stats.in_use}</p>
              </div>
              <Activity className="h-10 w-10 text-blue-200" />
            </div>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">Maintenance</p>
                <p className="text-3xl font-bold text-red-600">{stats.maintenance}</p>
              </div>
              <AlertCircle className="h-10 w-10 text-red-200" />
            </div>
          </Card>
        </div>

        {/* Blood Request Stats Cards - Only show if hospital is verified */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="hover:shadow-lg transition-shadow bg-gradient-to-r from-red-50 to-red-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Active Blood Requests</p>
                <p className="text-3xl font-bold text-red-600">{requestStats.active}</p>
              </div>
              <Droplet className="h-10 w-10 text-red-400" />
            </div>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow bg-gradient-to-r from-yellow-50 to-yellow-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Pending Responses</p>
                <p className="text-3xl font-bold text-yellow-600">{requestStats.pending}</p>
              </div>
              <Clock className="h-10 w-10 text-yellow-400" />
            </div>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow bg-gradient-to-r from-green-50 to-green-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Fulfilled Requests</p>
                <p className="text-3xl font-bold text-green-600">{requestStats.fulfilled}</p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-400" />
            </div>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link href="/hospital/requests/new">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-gradient-to-r from-red-600 to-red-700 text-white">
              <div className="text-center">
                <Droplet className="h-12 w-12 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Create Blood Request</h3>
                <p className="text-red-100 text-sm">Request blood from donors</p>
              </div>
            </Card>
          </Link>
          
          <Link href="/hospital/machines">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-center">
                <Settings className="h-12 w-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Manage Machines</h3>
                <p className="text-gray-600 text-sm">Add, edit, and monitor donation machines</p>
              </div>
            </Card>
          </Link>
          
          <Link href="/hospital/appointments">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-center">
                <Calendar className="h-12 w-12 text-purple-600 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Manage Appointments</h3>
                <p className="text-gray-600 text-sm">View and manage donor appointments</p>
              </div>
            </Card>
          </Link>
        </div>

        {/* Recent Blood Requests */}
        <Card title="Recent Blood Requests" className="mb-8">
          {bloodRequests.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No blood requests yet</p>
              <Link href="/hospital/requests/new">
                <Button>Create Your First Blood Request</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {bloodRequests.map((request) => (
                <div 
                  key={request.id} 
                  className={`border rounded-lg p-4 ${getUrgencyColor(request.urgency)}`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      {getUrgencyIcon(request.urgency)}
                      <h3 className="text-lg font-semibold capitalize">{request.urgency} Request</h3>
                      <span className="px-2 py-1 rounded-full text-xs bg-white bg-opacity-50">
                        {request.status}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">{request.blood_type}</p>
                      <p className="text-xs">{request.quantity_units} unit(s)</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                    <div>
                      <p className="opacity-75">Donors Contacted</p>
                      <p className="font-semibold">{request.donors_contacted}</p>
                    </div>
                    <div>
                      <p className="opacity-75">Accepted</p>
                      <p className="font-semibold text-green-600">{request.donors_accepted}</p>
                    </div>
                    <div>
                      <p className="opacity-75">Created</p>
                      <p className="font-semibold">{new Date(request.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  
                  <Link href={`/hospital/requests/${request.id}`}>
                    <Button size="sm" variant="secondary" className="w-full">
                      View Details
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Machines List */}
        <Card title="Your Machines">
          {machines.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No machines added yet</p>
              <Link href="/hospital/machines/add">
                <Button>Add Your First Machine</Button>
              </Link>
            </div>
          ) : (
            <>
            <div className="space-y-4">
              {machines.slice(0, 3).map((machine) => (
                <div 
                  key={machine._id} 
                  className={`border rounded-lg p-4 ${getStatusColor(machine.status)}`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-lg font-semibold">{machine.name}</h3>
                      <p className="text-sm opacity-75">ID: {machine.machine_id}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 ${getStatusColor(machine.status)}`}>
                      {getStatusIcon(machine.status)}
                      {machine.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                    <div>
                      <span className="font-medium">Type:</span>{' '}
                      {machine.machine_type.replace('_', ' ').toUpperCase()}
                    </div>
                    <div>
                      <span className="font-medium">Donation Types:</span>{' '}
                      {machine.donation_types.map(t => t.replace('_', ' ').toUpperCase()).join(', ')}
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-3">
                    {machine.status !== 'available' && (
                      <Button 
                        size="sm" 
                        variant="success"
                        onClick={() => updateMachineStatus(machine._id, 'available')}
                      >
                        Mark Available
                      </Button>
                    )}
                    {machine.status !== 'in_use' && (
                      <Button 
                        size="sm" 
                        variant="primary"
                        onClick={() => updateMachineStatus(machine._id, 'in_use')}
                      >
                        Start Donation
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              {machines.length > 3 && (
                <Link href="/hospital/machines">
                  <Button variant="secondary" className="w-full">
                    View All {machines.length} Machines
                  </Button>
                </Link>
              )}
            </div>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}