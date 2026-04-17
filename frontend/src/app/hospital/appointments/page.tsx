// donorpulse-frontend\src\app\hospital\appointments\page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  CheckCircle, 
  Clock, 
  User, 
  Activity, 
  XCircle, 
  Play, 
  Check,
  Calendar,
  AlertCircle
} from 'lucide-react'
import apiClient from '@/lib/api-client'

interface Appointment {
  id: string
  donor_name: string
  donor_phone: string
  donor_id: string
  machine_name: string
  appointment_date: string
  appointment_time: string
  donation_type: string
  status: string
  checked_in_at?: string
  started_at?: string
  completed_at?: string
}

export default function HospitalAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [hospital, setHospital] = useState<any>(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    const hospitalData = localStorage.getItem('hospital')
    if (hospitalData) {
      setHospital(JSON.parse(hospitalData))
    }
    // Set default date to today
    setSelectedDate(new Date().toISOString().split('T')[0])
  }, [])

  useEffect(() => {
    if (hospital && selectedDate) {
      fetchAppointments()
    }
  }, [hospital, selectedDate, filterStatus])

  const fetchAppointments = async () => {
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.get(`/appointments/hospital/${hospital.id}`, {
        params: { date: selectedDate }
      })
      let appointmentsData = response.data.appointments || []
      
      // Apply status filter
      if (filterStatus !== 'all') {
        appointmentsData = appointmentsData.filter((apt: Appointment) => apt.status === filterStatus)
      }
      
      setAppointments(appointmentsData)
    } catch (error) {
      console.error('Failed to fetch appointments', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (appointmentId: string, action: string) => {
    setActionLoading(appointmentId)
    try {
      let endpoint = ''
      let successMessage = ''
      
      switch(action) {
        case 'checkin':
          endpoint = `/appointments/${appointmentId}/checkin`
          successMessage = 'Donor checked in successfully!'
          break
        case 'start':
          endpoint = `/appointments/${appointmentId}/start`
          successMessage = 'Donation started successfully!'
          break
        case 'complete':
          endpoint = `/appointments/${appointmentId}/complete`
          successMessage = 'Donation completed successfully!'
          break
        case 'cancel':
          endpoint = `/appointments/${appointmentId}/cancel`
          successMessage = 'Appointment cancelled successfully!'
          break
        case 'noshow':
          endpoint = `/appointments/${appointmentId}/noshow`
          successMessage = 'Appointment marked as no-show!'
          break
      }
      
      // Use apiClient instead of hardcoded URL
      await apiClient.patch(endpoint, {})
      
      alert(successMessage)
      fetchAppointments() // Refresh the list
    } catch (error: any) {
      alert(error.response?.data?.detail || `Failed to ${action} appointment`)
    } finally {
      setActionLoading(null)
    }
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { color: string, icon: JSX.Element, text: string }> = {
      booked: { 
        color: 'bg-blue-100 text-blue-800', 
        icon: <Calendar className="h-3 w-3" />,
        text: 'Booked'
      },
      checked_in: { 
        color: 'bg-yellow-100 text-yellow-800', 
        icon: <CheckCircle className="h-3 w-3" />,
        text: 'Checked In'
      },
      in_progress: { 
        color: 'bg-purple-100 text-purple-800', 
        icon: <Activity className="h-3 w-3" />,
        text: 'In Progress'
      },
      completed: { 
        color: 'bg-green-100 text-green-800', 
        icon: <Check className="h-3 w-3" />,
        text: 'Completed'
      },
      cancelled: { 
        color: 'bg-red-100 text-red-800', 
        icon: <XCircle className="h-3 w-3" />,
        text: 'Cancelled'
      },
      no_show: { 
        color: 'bg-gray-100 text-gray-800', 
        icon: <AlertCircle className="h-3 w-3" />,
        text: 'No Show'
      }
    }
    
    const badge = badges[status] || badges.booked
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 ${badge.color}`}>
        {badge.icon}
        {badge.text}
      </span>
    )
  }

  const getActions = (appointment: Appointment) => {
    const isLoading = actionLoading === appointment.id
    
    switch(appointment.status) {
      case 'booked':
        return (
          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant="success" 
              onClick={() => updateStatus(appointment.id, 'checkin')}
              loading={isLoading}
            >
              <CheckCircle className="h-4 w-4 mr-1" />
              Check In
            </Button>
            <Button 
              size="sm" 
              variant="danger" 
              onClick={() => updateStatus(appointment.id, 'cancel')}
              loading={isLoading}
            >
              <XCircle className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button 
              size="sm" 
              variant="secondary" 
              onClick={() => updateStatus(appointment.id, 'noshow')}
              loading={isLoading}
            >
              No Show
            </Button>
          </div>
        )
      case 'checked_in':
        return (
          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant="primary" 
              onClick={() => updateStatus(appointment.id, 'start')}
              loading={isLoading}
            >
              <Play className="h-4 w-4 mr-1" />
              Start Donation
            </Button>
            <Button 
              size="sm" 
              variant="danger" 
              onClick={() => updateStatus(appointment.id, 'cancel')}
              loading={isLoading}
            >
              Cancel
            </Button>
          </div>
        )
      case 'in_progress':
        return (
          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant="success" 
              onClick={() => updateStatus(appointment.id, 'complete')}
              loading={isLoading}
            >
              <Check className="h-4 w-4 mr-1" />
              Complete Donation
            </Button>
          </div>
        )
      case 'completed':
        return (
          <div className="text-green-600 text-sm flex items-center gap-1">
            <Check className="h-4 w-4" />
            Completed
          </div>
        )
      case 'cancelled':
        return (
          <div className="text-red-600 text-sm flex items-center gap-1">
            <XCircle className="h-4 w-4" />
            Cancelled
          </div>
        )
      case 'no_show':
        return (
          <div className="text-gray-600 text-sm flex items-center gap-1">
            <XCircle className="h-4 w-4" />
            No Show
          </div>
        )
      default:
        return null
    }
  }

  const getStatusCounts = () => {
    const counts = {
      all: appointments.length,
      booked: appointments.filter(a => a.status === 'booked').length,
      checked_in: appointments.filter(a => a.status === 'checked_in').length,
      in_progress: appointments.filter(a => a.status === 'in_progress').length,
      completed: appointments.filter(a => a.status === 'completed').length,
      cancelled: appointments.filter(a => a.status === 'cancelled').length,
      no_show: appointments.filter(a => a.status === 'no_show').length
    }
    return counts
  }

  const statusCounts = getStatusCounts()

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Appointment Management</h1>
        <div className="flex gap-2">
          <input
            type="date"
            className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
          <Button variant="secondary" onClick={fetchAppointments}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Filter Tabs */}
      <div className="mb-6 overflow-x-auto">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-4">
            <button
              onClick={() => setFilterStatus('all')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'all'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All ({statusCounts.all})
            </button>
            <button
              onClick={() => setFilterStatus('booked')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'booked'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📅 Booked ({statusCounts.booked})
            </button>
            <button
              onClick={() => setFilterStatus('checked_in')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'checked_in'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ✅ Checked In ({statusCounts.checked_in})
            </button>
            <button
              onClick={() => setFilterStatus('in_progress')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'in_progress'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🩸 In Progress ({statusCounts.in_progress})
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'completed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🏆 Completed ({statusCounts.completed})
            </button>
            <button
              onClick={() => setFilterStatus('cancelled')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'cancelled'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ❌ Cancelled ({statusCounts.cancelled})
            </button>
            <button
              onClick={() => setFilterStatus('no_show')}
              className={`py-2 px-3 border-b-2 font-medium text-sm whitespace-nowrap ${
                filterStatus === 'no_show'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ⏰ No Show ({statusCounts.no_show})
            </button>
          </nav>
        </div>
      </div>

      {/* Appointments List */}
      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-500">Loading appointments...</p>
        </div>
      ) : appointments.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500">No appointments for {selectedDate}</p>
            <p className="text-sm text-gray-400 mt-1">Try selecting a different date</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {appointments.map((apt) => (
            <Card key={apt.id} className="hover:shadow-md transition-shadow">
              <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                {/* Left side - Donor Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2 flex-wrap gap-2">
                    <h3 className="text-lg font-semibold">{apt.donor_name}</h3>
                    {getStatusBadge(apt.status)}
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500 text-xs">Phone</p>
                      <p className="font-medium">{apt.donor_phone}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 text-xs">Time</p>
                      <p className="font-medium">{apt.appointment_time}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 text-xs">Station</p>
                      <p className="font-medium">{apt.machine_name}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 text-xs">Donation Type</p>
                      <p className="font-medium">{apt.donation_type.replace('_', ' ').toUpperCase()}</p>
                    </div>
                  </div>
                  
                  {/* Timestamps */}
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-400">
                    {apt.checked_in_at && (
                      <span>✅ Checked in: {new Date(apt.checked_in_at).toLocaleTimeString()}</span>
                    )}
                    {apt.started_at && (
                      <span>🩸 Started: {new Date(apt.started_at).toLocaleTimeString()}</span>
                    )}
                    {apt.completed_at && (
                      <span>🏆 Completed: {new Date(apt.completed_at).toLocaleTimeString()}</span>
                    )}
                  </div>
                </div>
                
                {/* Right side - Actions */}
                <div className="flex-shrink-0">
                  {getActions(apt)}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}