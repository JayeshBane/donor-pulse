// donorpulse-frontend\src\components\donor\DonorProfileUpdateForm.tsx
'use client'

import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { authAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'

interface ProfileUpdateData {
  preferences?: {
    availability?: string[]
    notify_types?: string[]
    transport_available?: boolean
  }
  location?: {
    address?: string
    city?: string
    pin_code?: string
    lat?: number
    lng?: number
  }
  medical?: {
    last_donation_date?: string
    medications?: string[] | string
  }
}

interface DonorData {
  _id: string
  name: string
  age: number
  medical: {
    blood_type: string
    last_donation_date?: string
    medications?: string[]
  }
  preferences: {
    availability?: string[]
    notify_types?: string[]
    transport_available?: boolean
  }
  location: {
    address?: string
    city?: string
    pin_code?: string
    lat?: number
    lng?: number
  }
}

export const DonorProfileUpdateForm: React.FC<{ token: string }> = ({ token }) => {
  const [loading, setLoading] = useState(false)
  const [donorData, setDonorData] = useState<DonorData | null>(null)
  
  const { register, handleSubmit, setValue } = useForm<ProfileUpdateData>()
  
  useEffect(() => {
    verifyToken()
  }, [token])
  
  const verifyToken = async () => {
    try {
      const response = await authAPI.verifyMagicLink(token)
      setDonorData(response.donor)
      
      // Pre-fill form with current data
      if (response.donor.preferences) {
        setValue('preferences.availability', response.donor.preferences.availability || [])
        setValue('preferences.notify_types', response.donor.preferences.notify_types || [])
        setValue('preferences.transport_available', response.donor.preferences.transport_available || false)
      }
      
      if (response.donor.location) {
        setValue('location.address', response.donor.location.address || '')
        setValue('location.city', response.donor.location.city || '')
        setValue('location.pin_code', response.donor.location.pin_code || '')
      }
      
      if (response.donor.medical) {
        setValue('medical.last_donation_date', response.donor.medical.last_donation_date?.split('T')[0] || '')
        const medications = response.donor.medical.medications || []
        setValue('medical.medications', medications.join(', '))
      }
    } catch (error) {
      alert('Invalid or expired magic link')
    }
  }
  
  const onSubmit = async (data: ProfileUpdateData) => {
    setLoading(true)
    try {
      // Process medications string to array if needed
      if (data.medical?.medications && typeof data.medical.medications === 'string') {
        data.medical.medications = (data.medical.medications as string).split(',').map((m: string) => m.trim())
      }
      
      await authAPI.updateViaMagicLink(token, data)
      alert('✅ Profile updated successfully!')
      window.location.href = '/'
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }
  
  if (!donorData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying magic link...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="max-w-3xl mx-auto p-6">
      <Card title="Update Your Profile">
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Donor:</strong> {donorData.name} (Age: {donorData.age})<br />
            <strong>Blood Type:</strong> {donorData.medical.blood_type} (Cannot be changed)
          </p>
        </div>
        
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-6">
            {/* Availability Section */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Availability</h3>
              <div className="space-y-2">
                {['Morning', 'Afternoon', 'Evening', 'Night'].map((avail) => (
                  <label key={avail} className="flex items-center">
                    <input
                      type="checkbox"
                      value={avail}
                      {...register('preferences.availability')}
                      className="mr-2"
                    />
                    {avail}
                  </label>
                ))}
              </div>
            </div>
            
            {/* Notification Preferences */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Notification Preferences</h3>
              <div className="space-y-2">
                {['Routine', 'Urgent', 'Critical', 'SOS'].map((notify) => (
                  <label key={notify} className="flex items-center">
                    <input
                      type="checkbox"
                      value={notify}
                      {...register('preferences.notify_types')}
                      className="mr-2"
                    />
                    {notify}
                  </label>
                ))}
              </div>
            </div>
            
            {/* Transport Availability */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  {...register('preferences.transport_available')}
                  className="mr-2"
                />
                I have my own transport
              </label>
            </div>
            
            {/* Location */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Location</h3>
              <Input
                label="Address"
                {...register('location.address')}
              />
              <Input
                label="City"
                {...register('location.city')}
              />
              <Input
                label="Pin Code"
                {...register('location.pin_code')}
              />
            </div>
            
            {/* Medical Updates */}
            <div>
              <h3 className="text-lg font-semibold mb-3">Medical Information</h3>
              <Input
                label="Last Donation Date"
                type="date"
                {...register('medical.last_donation_date')}
              />
              <Input
                label="Current Medications (comma separated)"
                {...register('medical.medications')}
                placeholder="e.g., Aspirin, Vitamins"
              />
            </div>
            
            <Button type="submit" loading={loading} className="w-full">
              Update Profile
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}