'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { donorAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card } from '@/components/ui/Card'

const donorRegistrationSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.number().min(18, 'Age must be 18 or older').max(65, 'Age must be 65 or younger'),
  gender: z.string().min(1, 'Gender is required'),
  photo_url: z.string().optional(),
  
  medical: z.object({
    blood_type: z.enum(['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']),
    donation_types: z.array(z.string()).min(1, 'Select at least one donation type'),
    weight_kg: z.number().min(50, 'Weight must be at least 50kg'),
    illnesses: z.array(z.string()),
    medications: z.array(z.string()),
    last_donation_date: z.string().optional(),
  }),
  
  location: z.object({
    phone: z.string().min(10, 'Phone number must be at least 10 characters'),
    email: z.string().email().optional().or(z.literal('')),
    address: z.string().min(5, 'Address is required'),
    city: z.string().min(2, 'City is required'),
    pin_code: z.string().min(3, 'Pin code is required'),
    lat: z.number().optional(),
    lng: z.number().optional(),
  }),
  
  preferences: z.object({
    contact_method: z.string(),
    availability: z.array(z.enum(['Morning', 'Afternoon', 'Evening', 'Night'])),
    language: z.string(),
    notify_types: z.array(z.enum(['Routine', 'Urgent', 'Critical', 'SOS'])),
    transport_available: z.boolean(),
  }),
})

type FormData = z.infer<typeof donorRegistrationSchema>

const bloodTypes = ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'] as const
const donationTypes = ['whole_blood', 'platelets', 'plasma', 'double_rbc']
const availabilityOptions = ['Morning', 'Afternoon', 'Evening', 'Night'] as const
const notifyOptions = ['Routine', 'Urgent', 'Critical', 'SOS'] as const

export const DonorRegistrationForm: React.FC = () => {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { register, handleSubmit, formState: { errors }, setValue } = useForm<FormData>({
    resolver: zodResolver(donorRegistrationSchema),
    defaultValues: {
      medical: {
        donation_types: ['whole_blood'],
        illnesses: [],
        medications: []
      },
      preferences: {
        contact_method: 'sms',
        availability: [],
        language: 'en',
        notify_types: ['Routine', 'Urgent', 'Critical', 'SOS'],
        transport_available: false
      }
    }
  })
  
  const onSubmit = async (data: FormData) => {
    setLoading(true)
    setError(null)
    
    try {
      const formattedData = {
        name: data.name,
        age: data.age,
        gender: data.gender,
        photo_url: data.photo_url || "",
        medical: {
          blood_type: data.medical.blood_type,
          donation_types: data.medical.donation_types,
          weight_kg: data.medical.weight_kg,
          illnesses: data.medical.illnesses || [],
          medications: data.medical.medications || [],
          last_donation_date: data.medical.last_donation_date || null
        },
        location: {
          phone: data.location.phone,
          email: data.location.email || "",
          address: data.location.address,
          city: data.location.city,
          pin_code: data.location.pin_code,
          lat: data.location.lat || null,
          lng: data.location.lng || null
        },
        preferences: {
          contact_method: data.preferences.contact_method,
          availability: data.preferences.availability,
          language: data.preferences.language,
          notify_types: data.preferences.notify_types,
          transport_available: data.preferences.transport_available
        }
      }
      
      const response = await donorAPI.register(formattedData)
      
      alert(`✅ Donor registered successfully!\n\nA welcome SMS has been sent to ${data.location.phone}\n\nUse SMS commands to manage your profile:\n• Send STATUS to check eligibility\n• Send UPDATE to get profile update link\n• Send HELP for all commands`)
      
      window.location.href = '/'
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed'
      setError(errorMessage)
      alert(`❌ Registration failed: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }
  
  const nextStep = () => {
    setError(null)
    setStep(step + 1)
  }
  
  const prevStep = () => {
    setError(null)
    setStep(step - 1)
  }
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card title="Donor Registration">
        <div className="mb-8">
          <div className="flex justify-between">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className="flex-1 text-center">
                <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center ${
                  step >= s ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  {s}
                </div>
                <p className="text-sm mt-2">
                  {s === 1 && 'Basic Info'}
                  {s === 2 && 'Medical Info'}
                  {s === 3 && 'Location'}
                  {s === 4 && 'Preferences'}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)}>
          {step === 1 && (
            <div className="space-y-4">
              <Input label="Full Name" {...register('name')} error={errors.name?.message} />
              <Input label="Age" type="number" {...register('age', { valueAsNumber: true })} error={errors.age?.message} />
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select {...register('gender')} className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
                {errors.gender && <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>}
              </div>
              <Input label="Photo URL (Optional)" {...register('photo_url')} placeholder="https://..." />
            </div>
          )}
          
          {step === 2 && (
            <div className="space-y-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Blood Type</label>
                <select {...register('medical.blood_type')} className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="">Select Blood Type</option>
                  {bloodTypes.map((bt) => (<option key={bt} value={bt}>{bt}</option>))}
                </select>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Donation Types</label>
                <div className="space-y-2">
                  {donationTypes.map((dt) => (
                    <label key={dt} className="flex items-center">
                      <input type="checkbox" value={dt} {...register('medical.donation_types')} className="mr-2" />
                      {dt.replace('_', ' ').toUpperCase()}
                    </label>
                  ))}
                </div>
              </div>
              
              <Input label="Weight (kg)" type="number" step="0.1" {...register('medical.weight_kg', { valueAsNumber: true })} />
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Illnesses (comma separated)</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg" onChange={(e) => setValue('medical.illnesses', e.target.value ? e.target.value.split(',').map(s => s.trim()) : [])} placeholder="e.g., Diabetes, Hypertension" />
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Medications (comma separated)</label>
                <input type="text" className="w-full px-3 py-2 border border-gray-300 rounded-lg" onChange={(e) => setValue('medical.medications', e.target.value ? e.target.value.split(',').map(s => s.trim()) : [])} placeholder="e.g., Insulin, Aspirin" />
              </div>
              
              <Input label="Last Donation Date (Optional)" type="date" {...register('medical.last_donation_date')} />
            </div>
          )}
          
          {step === 3 && (
            <div className="space-y-4">
              <Input label="Phone Number" type="tel" {...register('location.phone')} placeholder="+1234567890" />
              <Input label="Email (Optional)" type="email" {...register('location.email')} />
              <Input label="Address" {...register('location.address')} />
              <Input label="City" {...register('location.city')} />
              <Input label="Pin Code" {...register('location.pin_code')} />
            </div>
          )}
          
          {step === 4 && (
            <div className="space-y-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Availability</label>
                <div className="space-y-2">
                  {availabilityOptions.map((avail) => (
                    <label key={avail} className="flex items-center">
                      <input type="checkbox" value={avail} {...register('preferences.availability')} className="mr-2" />
                      {avail}
                    </label>
                  ))}
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notification Types</label>
                <div className="space-y-2">
                  {notifyOptions.map((notify) => (
                    <label key={notify} className="flex items-center">
                      <input type="checkbox" value={notify} {...register('preferences.notify_types')} className="mr-2" />
                      {notify}
                    </label>
                  ))}
                </div>
              </div>
              
              <div className="mb-4">
                <label className="flex items-center">
                  <input type="checkbox" {...register('preferences.transport_available')} className="mr-2" />
                  I have my own transport
                </label>
              </div>
            </div>
          )}
          
          <div className="flex justify-between mt-6">
            {step > 1 && (<Button variant="secondary" onClick={prevStep} type="button">Previous</Button>)}
            {step < 4 ? (<Button onClick={nextStep} type="button">Next</Button>) : (<Button loading={loading} type="submit">Register</Button>)}
          </div>
        </form>
      </Card>
    </div>
  )
}