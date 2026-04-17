// donorpulse-frontend\src\app\hospital\requests\new\page.tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useRouter } from 'next/navigation'
import apiClient from '@/lib/api-client'

export default function CreateBloodRequestPage() {
  const [loading, setLoading] = useState(false)
  const [hospital, setHospital] = useState<any>(null)
  const router = useRouter()
  
  const [formData, setFormData] = useState({
    blood_type: '',
    quantity_units: 1,
    urgency: 'routine',
    reason: ''
  })

  useEffect(() => {
    const hospitalData = localStorage.getItem('hospital')
    if (hospitalData) {
      setHospital(JSON.parse(hospitalData))
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      // Use apiClient instead of hardcoded URL with axios
      const response = await apiClient.post('/requests/create', {
        hospital_id: hospital?.id,
        ...formData
      })
      
      console.log('Response:', response.data)
      
      const requestId = response.data.request_id
      alert('Blood request created successfully! Donors will be notified.')
      
      // Redirect to the request details page
      router.push(`/hospital/requests/${requestId}`)
      
    } catch (error: any) {
      console.error('Error:', error)
      alert(error.response?.data?.detail || 'Failed to create request')
    } finally {
      setLoading(false)
    }
  }

  const urgencyInfo = {
    routine: { color: 'blue', description: 'Standard request, donors within 50km' },
    urgent: { color: 'yellow', description: 'Need within 24 hours, progressive radius' },
    critical: { color: 'orange', description: 'Need within 6 hours, wider radius' },
    sos: { color: 'red', description: 'Emergency, city-wide broadcast' }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card title="Create Blood Request">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Blood Type Required</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={formData.blood_type}
              onChange={(e) => setFormData({...formData, blood_type: e.target.value})}
              required
            >
              <option value="">Select Blood Type</option>
              <option value="O-">O- (Universal Donor)</option>
              <option value="O+">O+</option>
              <option value="A-">A-</option>
              <option value="A+">A+</option>
              <option value="B-">B-</option>
              <option value="B+">B+</option>
              <option value="AB-">AB-</option>
              <option value="AB+">AB+ (Universal Recipient)</option>
            </select>
          </div>

          <Input
            label="Quantity (Units)"
            type="number"
            min="1"
            max="50"
            value={formData.quantity_units}
            onChange={(e) => setFormData({...formData, quantity_units: parseInt(e.target.value)})}
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Urgency Level</label>
            <div className="space-y-2">
              {['routine', 'urgent', 'critical', 'sos'].map((level) => (
                <label key={level} className="flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                  <input
                    type="radio"
                    name="urgency"
                    value={level}
                    checked={formData.urgency === level}
                    onChange={(e) => setFormData({...formData, urgency: e.target.value})}
                    className="mt-1 mr-3"
                  />
                  <div>
                    <div className="font-medium capitalize">{level}</div>
                    <div className="text-sm text-gray-500">{urgencyInfo[level as keyof typeof urgencyInfo].description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reason (Optional)</label>
            <textarea
              className="w-full px-3 py-2 border rounded-lg"
              rows={3}
              value={formData.reason}
              onChange={(e) => setFormData({...formData, reason: e.target.value})}
              placeholder="e.g., Emergency surgery, Accident victim, etc."
            />
          </div>

          <Button type="submit" loading={loading} className="w-full">
            Create Blood Request
          </Button>
        </form>
      </Card>
    </div>
  )
}