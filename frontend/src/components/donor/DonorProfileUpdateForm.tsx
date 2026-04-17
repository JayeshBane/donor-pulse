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
  }
  medical?: {
    last_donation_date?: string
    medications?: string
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
  }
}

export const DonorProfileUpdateForm: React.FC<{ token: string }> = ({ token }) => {
  const [loading, setLoading] = useState(false)
  const [donorData, setDonorData] = useState<DonorData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  const { register, handleSubmit, setValue, watch } = useForm<ProfileUpdateData>()
  
  // Watch for checkbox changes
  const watchedAvailability = watch('preferences.availability')
  const watchedNotifyTypes = watch('preferences.notify_types')
  const watchedTransport = watch('preferences.transport_available')
  
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
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Invalid or expired magic link')
    }
  }
  
  const onSubmit = async (data: ProfileUpdateData) => {
    setLoading(true)
    setError(null)
    setSuccess(null)
    
    try {
      console.log('Submitting update data:', data)
      
      // Only send fields that have values
      const updateData: any = {}
      
      // Check if preferences have changed
      if (data.preferences) {
        updateData.preferences = {}
        if (data.preferences.availability && data.preferences.availability.length > 0) {
          updateData.preferences.availability = data.preferences.availability
        }
        if (data.preferences.notify_types && data.preferences.notify_types.length > 0) {
          updateData.preferences.notify_types = data.preferences.notify_types
        }
        if (data.preferences.transport_available !== undefined) {
          updateData.preferences.transport_available = data.preferences.transport_available
        }
        // If no preferences to update, remove the key
        if (Object.keys(updateData.preferences).length === 0) {
          delete updateData.preferences
        }
      }
      
      // Check if location has changed
      if (data.location) {
        updateData.location = {}
        if (data.location.address && data.location.address !== donorData?.location?.address) {
          updateData.location.address = data.location.address
        }
        if (data.location.city && data.location.city !== donorData?.location?.city) {
          updateData.location.city = data.location.city
        }
        if (data.location.pin_code && data.location.pin_code !== donorData?.location?.pin_code) {
          updateData.location.pin_code = data.location.pin_code
        }
        // If no location to update, remove the key
        if (Object.keys(updateData.location).length === 0) {
          delete updateData.location
        }
      }
      
      // Check if medical has changed
      if (data.medical) {
        updateData.medical = {}
        if (data.medical.last_donation_date && data.medical.last_donation_date !== donorData?.medical?.last_donation_date?.split('T')[0]) {
          updateData.medical.last_donation_date = data.medical.last_donation_date
        }
        if (data.medical.medications !== undefined) {
          const medsString = (donorData?.medical?.medications || []).join(', ')
          if (data.medical.medications !== medsString) {
            updateData.medical.medications = data.medical.medications
          }
        }
        // If no medical to update, remove the key
        if (Object.keys(updateData.medical).length === 0) {
          delete updateData.medical
        }
      }
      
      if (Object.keys(updateData).length === 0) {
        setError('No changes were made to update')
        setLoading(false)
        return
      }
      
      console.log('Sending update data:', updateData)
      
      const response = await authAPI.updateViaMagicLink(token, updateData)
      setSuccess(response.message || 'Profile updated successfully!')
      
      // Refresh donor data after update
      setTimeout(() => {
        window.location.href = '/'
      }, 2000)
      
    } catch (error: any) {
      console.error('Update error:', error)
      setError(error.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }
  
  const toggleArrayValue = (currentArray: string[] = [], value: string): string[] => {
    if (currentArray.includes(value)) {
      return currentArray.filter(v => v !== value)
    } else {
      return [...currentArray, value]
    }
  }
  
  if (error) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <Card title="Update Profile">
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
          <div className="mt-4 text-center">
            <a href="/" className="text-blue-600 hover:underline">Return to Home</a>
          </div>
        </Card>
      </div>
    )
  }
  
  if (success) {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <Card title="Update Profile">
          <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {success}
          </div>
          <div className="mt-4 text-center">
            <a href="/" className="text-blue-600 hover:underline">Return to Home</a>
          </div>
        </Card>
      </div>
    )
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
                      checked={watchedAvailability?.includes(avail) || false}
                      onChange={(e) => {
                        const current = watchedAvailability || []
                        const newValue = e.target.checked
                          ? [...current, avail]
                          : current.filter(v => v !== avail)
                        setValue('preferences.availability', newValue)
                      }}
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
                      checked={watchedNotifyTypes?.includes(notify) || false}
                      onChange={(e) => {
                        const current = watchedNotifyTypes || []
                        const newValue = e.target.checked
                          ? [...current, notify]
                          : current.filter(v => v !== notify)
                        setValue('preferences.notify_types', newValue)
                      }}
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
                  checked={watchedTransport || false}
                  onChange={(e) => setValue('preferences.transport_available', e.target.checked)}
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
                placeholder={donorData.location?.address || 'Enter address'}
              />
              <Input
                label="City"
                {...register('location.city')}
                placeholder={donorData.location?.city || 'Enter city'}
              />
              <Input
                label="Pin Code"
                {...register('location.pin_code')}
                placeholder={donorData.location?.pin_code || 'Enter pin code'}
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