// donorpulse-frontend\src\app\donor\book\page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Calendar, Clock, User, Phone, CheckCircle, Building2 } from 'lucide-react'
import { useSearchParams, useRouter } from 'next/navigation'
import apiClient from '@/lib/api-client'

interface TimeSlot {
  machine_id: string
  machine_name: string
  machine_type: string
  time: string
  donation_types: string[]
  floor?: string
  room?: string
}

export default function BookAppointmentPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const donorId = searchParams.get('donor_id')
  const [loading, setLoading] = useState(false)
  const [slots, setSlots] = useState<TimeSlot[]>([])
  const [selectedSlot, setSelectedSlot] = useState<TimeSlot | null>(null)
  const [donor, setDonor] = useState<any>(null)
  const [hospitals, setHospitals] = useState<any[]>([])
  const [selectedHospital, setSelectedHospital] = useState('')
  const [selectedDate, setSelectedDate] = useState('')
  const [donationType, setDonationType] = useState('whole_blood')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    fetchDonor()
    fetchHospitals()
    // Set default date to tomorrow
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    setSelectedDate(tomorrow.toISOString().split('T')[0])
  }, [])

  const fetchDonor = async () => {
    if (!donorId) {
      setError('No donor ID provided. Please register first.')
      return
    }
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.get(`/donors/${donorId}`)
      setDonor(response.data)
    } catch (error) {
      console.error('Failed to fetch donor', error)
      setError('Donor not found. Please register first.')
    }
  }

  const fetchHospitals = async () => {
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.get('/hospitals/')
      setHospitals(response.data.hospitals || [])
    } catch (error) {
      console.error('Failed to fetch hospitals', error)
    }
  }

  const fetchSlots = async () => {
    if (!selectedHospital) {
      alert('Please select a hospital')
      return
    }
    
    setLoading(true)
    setError(null)
    setSelectedSlot(null)
    
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.get('/appointments/slots/available', {
        params: {
          hospital_id: selectedHospital,
          date: selectedDate,
          donation_type: donationType
        }
      })
      
      console.log('Slots response:', response.data)
      
      if (response.data.slots && response.data.slots.length > 0) {
        setSlots(response.data.slots)
      } else {
        setSlots([])
        setError(response.data.message || 'No available slots for this date')
      }
    } catch (error: any) {
      console.error('Failed to fetch slots', error)
      setError(error.response?.data?.detail || 'Failed to load available slots')
      setSlots([])
    } finally {
      setLoading(false)
    }
  }

  const handleSlotSelect = (slot: TimeSlot) => {
    console.log('Selected slot:', slot)
    setSelectedSlot(slot)
  }

  const bookAppointment = async () => {
    console.log('Booking appointment with selectedSlot:', selectedSlot)
    
    if (!selectedSlot) {
      alert('Please select a time slot first')
      return
    }
    
    if (!donor) {
      alert('Donor information not found')
      return
    }
    
    if (!selectedHospital) {
      alert('Please select a hospital')
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      const appointmentData = {
        donor_id: donor._id,
        hospital_id: selectedHospital,
        machine_id: selectedSlot.machine_id,
        appointment_date: selectedDate,
        appointment_time: selectedSlot.time,
        donation_type: donationType
      }

      console.log('Sending booking data:', JSON.stringify(appointmentData, null, 2))

      // Use apiClient instead of hardcoded URL
      const response = await apiClient.post('/appointments/book', appointmentData)

      console.log('Booking response:', response.data)
      
      setSuccess(`Appointment booked successfully! Redirecting to receipt...`)
      
      // Redirect to receipt page after 2 seconds
      setTimeout(() => {
        router.push(`/donor/appointment/${response.data.booking_token}`)
      }, 2000)
      
    } catch (error: any) {
      console.error('Booking error:', error)
      console.error('Error response:', error.response?.data)
      
      let errorMessage = 'Failed to book appointment'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.message) {
        errorMessage = error.message
      }
      
      setError(errorMessage)
      alert(`Booking failed: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const getSelectedSlotClass = (slot: TimeSlot) => {
    if (selectedSlot?.time === slot.time && selectedSlot?.machine_id === slot.machine_id) {
      return 'bg-blue-600 text-white border-blue-600'
    }
    return 'hover:bg-gray-50'
  }

  if (error && !donor) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <a href="/donor/register">
              <Button>Register as Donor</Button>
            </a>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Book a Donation Appointment</h1>
      
      {success && (
        <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
          {success}
        </div>
      )}
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Donor Info */}
        {donor && (
          <Card title="Donor Information">
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-500" />
                <span className="font-medium">{donor.name}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-gray-500" />
                <span>{donor.location.phone}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-medium">Blood Type:</span>
                <span className="text-red-600 font-bold">{donor.medical.blood_type}</span>
              </div>
            </div>
          </Card>
        )}

        {/* Booking Form */}
        <Card title="Appointment Details">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Hospital</label>
              <select
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                value={selectedHospital}
                onChange={(e) => {
                  setSelectedHospital(e.target.value)
                  setSlots([])
                  setSelectedSlot(null)
                }}
              >
                <option value="">Choose a hospital</option>
                {hospitals.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} - {h.city}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Donation Type</label>
              <select
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                value={donationType}
                onChange={(e) => {
                  setDonationType(e.target.value)
                  setSlots([])
                  setSelectedSlot(null)
                }}
              >
                <option value="whole_blood">Whole Blood</option>
                <option value="platelets">Platelets</option>
                <option value="plasma">Plasma</option>
                <option value="double_rbc">Double RBC</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Select Date</label>
              <input
                type="date"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                value={selectedDate}
                min={new Date().toISOString().split('T')[0]}
                onChange={(e) => {
                  setSelectedDate(e.target.value)
                  setSlots([])
                  setSelectedSlot(null)
                }}
              />
            </div>

            <Button 
              onClick={fetchSlots} 
              disabled={!selectedHospital || loading}
              className="w-full"
            >
              {loading ? 'Loading...' : 'Check Available Slots'}
            </Button>
          </div>
        </Card>
      </div>

      {/* Available Slots */}
      {slots.length > 0 && (
        <div className="mt-8">
          <Card title={`Available Time Slots for ${selectedDate}`}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {slots.map((slot, index) => (
                <button
                  key={`${slot.time}-${slot.machine_id}-${index}`}
                  onClick={() => handleSlotSelect(slot)}
                  className={`time-slot-button p-3 border rounded-lg text-center transition-all hover:shadow-md ${getSelectedSlotClass(slot)}`}
                >
                  <Clock className="h-5 w-5 mx-auto mb-2" />
                  <div className="font-medium text-lg">{slot.time}</div>
                  <div className="text-xs mt-1">{slot.machine_name}</div>
                  {slot.floor && (
                    <div className="text-xs opacity-75 mt-1">{slot.floor}</div>
                  )}
                </button>
              ))}
            </div>
            
            {selectedSlot && (
              <div className="mt-6 pt-4 border-t">
                <div className="bg-green-50 p-4 rounded-lg mb-4">
                  <h3 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Selected Appointment:
                  </h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="font-medium">Date:</span> {selectedDate}</div>
                    <div><span className="font-medium">Time:</span> {selectedSlot.time}</div>
                    <div><span className="font-medium">Machine:</span> {selectedSlot.machine_name}</div>
                    <div><span className="font-medium">Type:</span> {donationType.replace('_', ' ').toUpperCase()}</div>
                  </div>
                </div>
                <Button 
                  onClick={bookAppointment} 
                  loading={loading}
                  className="w-full"
                  disabled={!selectedSlot}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirm Appointment
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {slots.length === 0 && selectedHospital && selectedDate && !loading && !error && (
        <div className="mt-8 text-center text-gray-500">
          No available slots for this date. Please try another date.
        </div>
      )}
      
      {error && slots.length === 0 && (
        <div className="mt-8 p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg">
          {error}
        </div>
      )}
    </div>
  )
}