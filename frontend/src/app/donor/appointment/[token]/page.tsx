// donorpulse-frontend\src\app\donor\appointment\[token]\page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { 
  CheckCircle, 
  Calendar, 
  Clock, 
  MapPin, 
  User, 
  Phone, 
  Droplet,
  Download,
  Share2,
  Heart,
  Building2,
  QrCode
} from 'lucide-react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import apiClient from '@/lib/api-client'

interface AppointmentDetails {
  id: string
  donor_name: string
  donor_phone: string
  hospital_name: string
  machine_name: string
  appointment_date: string
  appointment_time: string
  donation_type: string
  status: string
  booking_token: string
  notes?: string
}

export default function AppointmentReceiptPage() {
  const params = useParams()
  const token = params.token as string
  const [appointment, setAppointment] = useState<AppointmentDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAppointment()
  }, [token])

  const fetchAppointment = async () => {
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.get(`/appointments/token/${token}`)
      setAppointment(response.data)
    } catch (error: any) {
      console.error('Failed to fetch appointment', error)
      setError(error.response?.data?.detail || 'Appointment not found')
    } finally {
      setLoading(false)
    }
  }

  const downloadReceipt = () => {
    if (!appointment) return
    
    const receiptHtml = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Donation Appointment Receipt</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
          .header { text-align: center; border-bottom: 2px solid #dc2626; padding-bottom: 20px; margin-bottom: 30px; }
          .logo { font-size: 24px; color: #dc2626; font-weight: bold; }
          .receipt-title { font-size: 28px; margin: 20px 0; }
          .details { background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
          .thankyou { text-align: center; margin-top: 40px; padding: 20px; background: #dcfce7; border-radius: 8px; }
          .footer { text-align: center; margin-top: 40px; color: #6b7280; font-size: 12px; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">🩸 DonorPulse</div>
          <div class="receipt-title">Appointment Confirmation</div>
        </div>
        
        <div class="details">
          <div class="detail-row">
            <strong>Booking ID:</strong> <span>${appointment.booking_token.substring(0, 16)}...</span>
          </div>
          <div class="detail-row">
            <strong>Donor Name:</strong> <span>${appointment.donor_name}</span>
          </div>
          <div class="detail-row">
            <strong>Hospital:</strong> <span>${appointment.hospital_name}</span>
          </div>
          <div class="detail-row">
            <strong>Date:</strong> <span>${new Date(appointment.appointment_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
          <div class="detail-row">
            <strong>Time:</strong> <span>${appointment.appointment_time}</span>
          </div>
          <div class="detail-row">
            <strong>Donation Type:</strong> <span>${appointment.donation_type.replace('_', ' ').toUpperCase()}</span>
          </div>
          <div class="detail-row">
            <strong>Station:</strong> <span>${appointment.machine_name}</span>
          </div>
        </div>
        
        <div class="thankyou">
          <h2>Thank You for Saving Lives! 🩸</h2>
          <p>Your decision to donate blood can save up to 3 lives.</p>
          <p>Please arrive 15 minutes before your appointment time.</p>
        </div>
        
        <div class="footer">
          <p>DonorPulse - Connecting Donors with Hospitals</p>
          <p>For any changes, please contact the hospital directly.</p>
        </div>
      </body>
      </html>
    `
    
    const blob = new Blob([receiptHtml], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `donation_receipt_${appointment.booking_token.substring(0, 8)}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const shareReceipt = () => {
    if (!appointment) return
    
    const shareText = `I've scheduled a blood donation appointment at ${appointment.hospital_name} on ${new Date(appointment.appointment_date).toLocaleDateString()} at ${appointment.appointment_time}. Every drop counts! 🩸`
    
    if (navigator.share) {
      navigator.share({
        title: 'My Donation Appointment',
        text: shareText,
        url: window.location.href
      })
    } else {
      navigator.clipboard.writeText(shareText)
      alert('Appointment details copied to clipboard!')
    }
  }

  const addToCalendar = () => {
    if (!appointment) return
    
    const startDateTime = new Date(`${appointment.appointment_date}T${appointment.appointment_time}:00`)
    const endDateTime = new Date(startDateTime.getTime() + 60 * 60 * 1000) // 1 hour duration
    
    const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=Blood%20Donation%20Appointment&dates=${startDateTime.toISOString().replace(/-|:|\./g, '')}/${endDateTime.toISOString().replace(/-|:|\./g, '')}&details=Donation%20type%3A%20${appointment.donation_type}%0AStation%3A%20${appointment.machine_name}&location=${encodeURIComponent(appointment.hospital_name)}`
    
    window.open(googleCalendarUrl, '_blank')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading appointment details...</p>
        </div>
      </div>
    )
  }

  if (error || !appointment) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <Card>
          <div className="text-center py-12">
            <div className="text-red-600 text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold mb-2">Appointment Not Found</h2>
            <p className="text-gray-600 mb-6">{error || 'Invalid appointment token'}</p>
            <Link href="/">
              <Button>Return to Home</Button>
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Success Animation */}
      <div className="text-center mb-8 animate-bounce">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full">
          <CheckCircle className="h-12 w-12 text-green-600" />
        </div>
      </div>

      {/* Main Receipt Card */}
      <Card className="overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-red-600 to-red-700 text-white p-6 text-center">
          <Droplet className="h-12 w-12 mx-auto mb-3" />
          <h1 className="text-2xl font-bold">Appointment Confirmed!</h1>
          <p className="text-red-100 mt-2">Thank you for your generosity</p>
        </div>

        {/* Booking ID */}
        <div className="bg-gray-50 p-4 text-center border-b">
          <p className="text-sm text-gray-500">Booking Reference</p>
          <p className="font-mono font-bold text-lg">{appointment.booking_token.substring(0, 16)}...</p>
          <p className="text-xs text-gray-400 mt-1">Please save this for future reference</p>
        </div>

        {/* Appointment Details */}
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-red-600" />
            Appointment Details
          </h2>
          
          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="flex items-start space-x-3">
                <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Date</p>
                  <p className="font-medium">
                    {new Date(appointment.appointment_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm text-gray-500">Time</p>
                  <p className="font-medium">{appointment.appointment_time}</p>
                </div>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Building2 className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Hospital</p>
                <p className="font-medium">{appointment.hospital_name}</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <User className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Donor</p>
                <p className="font-medium">{appointment.donor_name}</p>
                <p className="text-sm text-gray-600">{appointment.donor_phone}</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Droplet className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Donation Type & Station</p>
                <p className="font-medium">
                  {appointment.donation_type.replace('_', ' ').toUpperCase()} at {appointment.machine_name}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Important Information */}
        <div className="bg-yellow-50 p-6 border-t border-yellow-200">
          <h3 className="font-semibold text-yellow-800 mb-2">📋 Important Information</h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            <li>• Please arrive 15 minutes before your appointment time</li>
            <li>• Bring a valid ID proof</li>
            <li>• Eat a light meal before donation</li>
            <li>• Stay hydrated</li>
            <li>• Get a good night's sleep</li>
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="p-6 border-t bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <Button 
              variant="secondary" 
              onClick={downloadReceipt}
              className="flex items-center justify-center gap-2"
            >
              <Download className="h-4 w-4" />
              Download Receipt
            </Button>
            
            <Button 
              variant="secondary" 
              onClick={shareReceipt}
              className="flex items-center justify-center gap-2"
            >
              <Share2 className="h-4 w-4" />
              Share
            </Button>
            
            <Button 
              variant="secondary" 
              onClick={addToCalendar}
              className="flex items-center justify-center gap-2 md:col-span-1 col-span-2"
            >
              <Calendar className="h-4 w-4" />
              Add to Calendar
            </Button>
          </div>
        </div>
      </Card>

      {/* Thank You Message */}
      <div className="mt-8 text-center">
        <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-lg p-8">
          <Heart className="h-16 w-16 text-red-500 mx-auto mb-4 animate-pulse" />
          <h2 className="text-2xl font-bold text-red-800 mb-2">You're a Hero! 🦸</h2>
          <p className="text-gray-700 mb-4">
            Your single donation can save up to 3 lives. Thank you for making a difference!
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/">
              <Button variant="secondary">Return to Home</Button>
            </Link>
            <Link href={`/donor/update/${appointment.booking_token}`}>
              <Button>Update Profile</Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Share Quote */}
      <div className="mt-6 text-center text-gray-500 text-sm">
        <p>"The gift of blood is the gift of life"</p>
        <p className="mt-2">Share your commitment to saving lives using #DonorPulse</p>
      </div>
    </div>
  )
}