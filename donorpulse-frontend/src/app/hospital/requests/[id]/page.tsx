'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useParams, useRouter } from 'next/navigation'
import axios from 'axios'
import { 
  Droplet, 
  Clock, 
  Users, 
  CheckCircle, 
  XCircle,
  ArrowLeft,
  RefreshCw
} from 'lucide-react'

interface MatchedDonor {
  donor_name: string
  donor_blood_type: string
  distance_km?: number
  status: string
  eta_minutes?: number
}

interface RequestDetails {
  id: string
  blood_type: string
  quantity_units: number
  urgency: string
  status: string
  created_at: string
  expires_at: string
  statistics?: {
    donors_contacted: number
    donors_accepted: number
    donors_declined: number
    donors_timeout: number
  }
  matched_donors?: MatchedDonor[]
}

type UrgencyColorKey = 'routine' | 'urgent' | 'critical' | 'sos'

export default function RequestDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const requestId = params.id as string
  const [request, setRequest] = useState<RequestDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (requestId) {
      fetchRequest()
    }
  }, [requestId])

  const fetchRequest = async () => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(
        `http://localhost:8000/api/v1/requests/${requestId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setRequest(response.data)
    } catch (error: any) {
      console.error('Failed to fetch request', error)
      if (error.response?.status === 404) {
        setError('Request not found. It may have been deleted or expired.')
      } else {
        setError(error.response?.data?.detail || 'Failed to load request details')
      }
    } finally {
      setLoading(false)
    }
  }

  const cancelRequest = async () => {
    if (!confirm('Are you sure you want to cancel this request?')) return
    
    try {
      const token = localStorage.getItem('access_token')
      await axios.patch(
        `http://localhost:8000/api/v1/requests/${requestId}/cancel`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      )
      alert('Request cancelled')
      router.push('/hospital/dashboard')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to cancel request')
    }
  }

  const getUrgencyColor = (urgency: string): string => {
    const colors: Record<UrgencyColorKey, string> = {
      routine: 'bg-blue-100 text-blue-800',
      urgent: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-orange-100 text-orange-800',
      sos: 'bg-red-100 text-red-800'
    }
    return colors[urgency as UrgencyColorKey] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading request details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <div className="text-center py-12">
            <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Unable to Load Request</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <div className="flex gap-3 justify-center">
              <Button onClick={() => router.push('/hospital/dashboard')}>
                Go to Dashboard
              </Button>
              <Button variant="secondary" onClick={fetchRequest}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  if (!request) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">Request not found</p>
            <Button onClick={() => router.push('/hospital/dashboard')}>Go to Dashboard</Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <button 
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <Card>
        <div className="mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold">Blood Request Details</h1>
              <p className="text-gray-500 mt-1">ID: {request.id}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${getUrgencyColor(request.urgency)}`}>
              {request.urgency}
            </span>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Droplet className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-gray-500">Blood Type Needed</p>
                <p className="text-2xl font-bold">{request.blood_type}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">Quantity Needed</p>
                <p className="text-2xl font-bold">{request.quantity_units} unit(s)</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p>{new Date(request.created_at).toLocaleString()}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-gray-500">Expires</p>
                <p>{new Date(request.expires_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t pt-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Statistics</h2>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-blue-600">{request.statistics?.donors_contacted || 0}</p>
              <p className="text-sm text-gray-500">Contacted</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-green-600">{request.statistics?.donors_accepted || 0}</p>
              <p className="text-sm text-gray-500">Accepted</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-red-600">{request.statistics?.donors_declined || 0}</p>
              <p className="text-sm text-gray-500">Declined</p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-600">{request.statistics?.donors_timeout || 0}</p>
              <p className="text-sm text-gray-500">Timeout</p>
            </div>
          </div>
        </div>

        {request.matched_donors && request.matched_donors.length > 0 && (
          <div className="border-t pt-6">
            <h2 className="text-lg font-semibold mb-4">Responding Donors ({request.matched_donors.length})</h2>
            <div className="space-y-3">
              {request.matched_donors.map((donor, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{donor.donor_name}</p>
                    <p className="text-sm text-gray-500">Blood Type: {donor.donor_blood_type}</p>
                    {donor.distance_km && (
                      <p className="text-xs text-gray-400">{donor.distance_km} km away</p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      donor.status === 'accepted' ? 'bg-green-100 text-green-800' :
                      donor.status === 'declined' ? 'bg-red-100 text-red-800' :
                      donor.status === 'arrived' ? 'bg-purple-100 text-purple-800' :
                      donor.status === 'donated' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {donor.status}
                    </span>
                    {donor.eta_minutes && (
                      <p className="text-xs text-gray-500 mt-1">ETA: {donor.eta_minutes} min</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {request.status !== 'fulfilled' && request.status !== 'cancelled' && request.status !== 'expired' && (
          <div className="border-t pt-6 mt-6">
            <Button variant="danger" onClick={cancelRequest} className="w-full">
              Cancel Request
            </Button>
          </div>
        )}

        {request.status === 'fulfilled' && (
          <div className="mt-6 p-4 bg-green-50 rounded-lg text-center">
            <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <p className="text-green-800 font-semibold">Request Fulfilled!</p>
            <p className="text-green-600 text-sm">All required donors have been confirmed.</p>
          </div>
        )}

        {request.status === 'expired' && (
          <div className="mt-6 p-4 bg-red-50 rounded-lg text-center">
            <XCircle className="h-8 w-8 text-red-600 mx-auto mb-2" />
            <p className="text-red-800 font-semibold">Request Expired</p>
            <p className="text-red-600 text-sm">This request has expired.</p>
          </div>
        )}
      </Card>
    </div>
  )
}