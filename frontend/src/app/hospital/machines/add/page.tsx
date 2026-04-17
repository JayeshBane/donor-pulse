// donorpulse-frontend\src\app\hospital\machines\add\page.tsx
'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useRouter } from 'next/navigation'
import apiClient from '@/lib/api-client'

export default function AddMachinePage() {
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  
  const [formData, setFormData] = useState({
    machine_id: '',
    name: '',
    machine_type: 'whole_blood',
    donation_types: ['whole_blood'],
    floor: '',
    room: '',
    operating_start: '09:00',
    operating_end: '17:00',
    max_daily_donations: 15,
    slot_duration_minutes: 30,
    buffer_minutes: 15
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      // Use apiClient instead of hardcoded URL
      await apiClient.post('/machines/add', formData)
      alert('Machine added successfully!')
      router.push('/hospital/dashboard')
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to add machine')
    } finally {
      setLoading(false)
    }
  }

  const toggleDonationType = (type: string) => {
    if (formData.donation_types.includes(type)) {
      setFormData({
        ...formData,
        donation_types: formData.donation_types.filter(t => t !== type)
      })
    } else {
      setFormData({
        ...formData,
        donation_types: [...formData.donation_types, type]
      })
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Card title="Add New Donation Machine">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Machine ID"
              placeholder="e.g., M-001"
              value={formData.machine_id}
              onChange={(e) => setFormData({...formData, machine_id: e.target.value})}
              required
            />
            <Input
              label="Machine Name"
              placeholder="e.g., Donation Station A"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Machine Type</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              value={formData.machine_type}
              onChange={(e) => setFormData({...formData, machine_type: e.target.value})}
              required
            >
              <option value="whole_blood">Whole Blood</option>
              <option value="platelet">Platelet</option>
              <option value="plasma">Plasma</option>
              <option value="double_rbc">Double RBC</option>
              <option value="multi_purpose">Multi Purpose</option>
            </select>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Donation Types Supported</label>
            <div className="space-y-2">
              {['whole_blood', 'platelets', 'plasma', 'double_rbc'].map((type) => (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.donation_types.includes(type)}
                    onChange={() => toggleDonationType(type)}
                    className="mr-2"
                  />
                  {type.replace('_', ' ').toUpperCase()}
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Floor"
              placeholder="e.g., Ground Floor"
              value={formData.floor}
              onChange={(e) => setFormData({...formData, floor: e.target.value})}
            />
            <Input
              label="Room"
              placeholder="e.g., Room 101"
              value={formData.room}
              onChange={(e) => setFormData({...formData, room: e.target.value})}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Operating Start"
              type="time"
              value={formData.operating_start}
              onChange={(e) => setFormData({...formData, operating_start: e.target.value})}
            />
            <Input
              label="Operating End"
              type="time"
              value={formData.operating_end}
              onChange={(e) => setFormData({...formData, operating_end: e.target.value})}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <Input
              label="Max Daily Donations"
              type="number"
              value={formData.max_daily_donations}
              onChange={(e) => setFormData({...formData, max_daily_donations: parseInt(e.target.value)})}
            />
            <Input
              label="Slot Duration (min)"
              type="number"
              value={formData.slot_duration_minutes}
              onChange={(e) => setFormData({...formData, slot_duration_minutes: parseInt(e.target.value)})}
            />
            <Input
              label="Buffer Time (min)"
              type="number"
              value={formData.buffer_minutes}
              onChange={(e) => setFormData({...formData, buffer_minutes: parseInt(e.target.value)})}
            />
          </div>

          <div className="flex gap-2 pt-4">
            <Button type="submit" loading={loading}>
              Add Machine
            </Button>
            <Button type="button" variant="secondary" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}