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
  Clock
} from 'lucide-react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import Link from 'next/link'

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

export default function HospitalDashboardPage() {
  const [loading, setLoading] = useState(true)
  const [hospital, setHospital] = useState<any>(null)
  const [machines, setMachines] = useState<Machine[]>([])
  const [stats, setStats] = useState({
    total: 0,
    available: 0,
    in_use: 0,
    maintenance: 0
  })
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const hospitalData = localStorage.getItem('hospital')
    
    if (!token) {
      router.push('/hospital/login')
    } else {
      const parsedHospital = JSON.parse(hospitalData || '{}')
      setHospital(parsedHospital)
      fetchMachines(parsedHospital.id)
    }
  }, [router])

  const fetchMachines = async (hospitalId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      
      const response = await axios.get(
        `http://localhost:8000/api/v1/machines/hospital/${hospitalId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      const machinesData = response.data
      setMachines(machinesData)
      
      // Calculate stats
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

  const updateMachineStatus = async (machineId: string, status: string) => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.patch(
        `http://localhost:8000/api/v1/machines/${machineId}/status`,
        { status },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      // Refresh machines list
      fetchMachines(hospital.id)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update status')
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Hospital Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Welcome, <strong>{hospital?.name || 'Hospital'}</strong>
                {!hospital?.is_verified && (
                  <span className="ml-2 text-yellow-600">(Pending Verification)</span>
                )}
              </p>
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

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Link href="/hospital/machines">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-center">
                <Settings className="h-12 w-12 text-blue-600 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Manage Machines</h3>
                <p className="text-gray-600 text-sm">Add, edit, and monitor donation machines</p>
              </div>
            </Card>
          </Link>
          
          <Link href="/hospital/machines/add">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <div className="text-center">
                <PlusCircle className="h-12 w-12 text-green-600 mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-2">Add New Machine</h3>
                <p className="text-gray-600 text-sm">Add a new donation machine to your hospital</p>
              </div>
            </Card>
          </Link>
        </div>

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
            <div className="space-y-4">
              {machines.map((machine) => (
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
                    {(machine.floor || machine.room) && (
                      <div className="col-span-2">
                        <span className="font-medium">Location:</span>{' '}
                        {[machine.floor, machine.room].filter(Boolean).join(' - ')}
                      </div>
                    )}
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
                    {machine.status !== 'maintenance' && (
                      <Button 
                        size="sm" 
                        variant="danger"
                        onClick={() => updateMachineStatus(machine._id, 'maintenance')}
                      >
                        Maintenance
                      </Button>
                    )}
                    {machine.status !== 'cleaning' && (
                      <Button 
                        size="sm" 
                        variant="secondary"
                        onClick={() => updateMachineStatus(machine._id, 'cleaning')}
                      >
                        Cleaning
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}