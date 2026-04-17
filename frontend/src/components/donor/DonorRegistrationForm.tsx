// donorpulse-frontend\src\components\donor\DonorRegistrationForm.tsx
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
    illnesses: z.string().optional(),
    medications: z.string().optional(),
    last_donation_date: z.string().optional(),
  }),
  
  location: z.object({
    phone: z.string().min(10, 'Phone number must be at least 10 characters'),
    email: z.string().email().optional().or(z.literal('')),
    address: z.string().min(5, 'Address is required'),
    city: z.string().min(2, 'City is required'),
    pin_code: z.string().min(3, 'Pin code is required'),
  }),
  
  preferences: z.object({
    availability: z.array(z.string()),
    transport_available: z.boolean(),
  }),
})

type FormData = z.infer<typeof donorRegistrationSchema>

const bloodTypes = ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'] as const
const donationTypes = ['whole_blood', 'platelets', 'plasma', 'double_rbc']
const availabilityOptions = ['Morning', 'Afternoon', 'Evening', 'Night'] as const

export const DonorRegistrationForm: React.FC = () => {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  const { register, handleSubmit, formState: { errors }, setValue, watch, trigger } = useForm<FormData>({
    resolver: zodResolver(donorRegistrationSchema),
    defaultValues: {
      medical: {
        donation_types: ['whole_blood'],
      },
      preferences: {
        availability: [],
        transport_available: false
      }
    },
    mode: 'onChange' // Validate on change
  })
  
  // Watch values for debugging
  const watchedValues = watch()
  
  const handleNextStep = async () => {
    // Validate current step fields
    let fieldsToValidate: (keyof FormData)[] = []
    
    if (step === 1) {
      fieldsToValidate = ['name', 'age', 'gender']
    } else if (step === 2) {
      fieldsToValidate = ['medical']
    } else if (step === 3) {
      fieldsToValidate = ['location']
    } else if (step === 4) {
      fieldsToValidate = ['preferences']
    }
    
    const isValid = await trigger(fieldsToValidate)
    
    if (isValid) {
      setStep(step + 1)
      setError(null)
    } else {
      setError('Please fill all required fields correctly')
    }
  }
  
  const onSubmit = async (data: FormData) => {
    console.log('Form submitted with data:', data)
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
          illnesses: data.medical.illnesses ? data.medical.illnesses.split(',').map(s => s.trim()).filter(s => s) : [],
          medications: data.medical.medications ? data.medical.medications.split(',').map(s => s.trim()).filter(s => s) : [],
          last_donation_date: data.medical.last_donation_date || null
        },
        location: {
          phone: data.location.phone,
          email: data.location.email || "",
          address: data.location.address,
          city: data.location.city,
          pin_code: data.location.pin_code,
        },
        preferences: {
          contact_method: "sms",
          availability: data.preferences.availability,
          language: "en",
          notify_types: ["Routine", "Urgent", "Critical", "SOS"],
          transport_available: data.preferences.transport_available
        }
      }
      
      console.log('Sending registration data:', JSON.stringify(formattedData, null, 2))
      
      const response = await donorAPI.register(formattedData)
      
      console.log('Registration response:', response)
      
      setSuccess(`✅ Donor registered successfully! A welcome SMS has been sent.`)
      
      // Redirect after 3 seconds
      setTimeout(() => {
        window.location.href = '/'
      }, 3000)
      
    } catch (error: any) {
      console.error('Registration error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Registration failed'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }
  
  const prevStep = () => {
    setStep(step - 1)
    setError(null)
  }
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card title="Donor Registration">
        {/* Success Message */}
        {success && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            {success}
            <div className="text-sm mt-1">Redirecting to home page...</div>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex justify-between">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className="flex-1 text-center">
                <div 
                  className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center cursor-pointer ${
                    step >= s ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
                  }`}
                  onClick={() => {
                    if (s < step) setStep(s)
                  }}
                >
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
        
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-4">
              <Input 
                label="Full Name" 
                {...register('name')} 
                error={errors.name?.message}
                required
              />
              <Input 
                label="Age" 
                type="number" 
                {...register('age', { valueAsNumber: true })} 
                error={errors.age?.message}
                required
              />
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                <select 
                  {...register('gender')} 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
                {errors.gender && <p className="mt-1 text-sm text-red-600">{errors.gender.message}</p>}
              </div>
              <Input 
                label="Photo URL (Optional)" 
                {...register('photo_url')} 
                placeholder="https://..." 
              />
            </div>
          )}
          
          {/* Step 2: Medical Info */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Blood Type *</label>
                <select 
                  {...register('medical.blood_type')} 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select Blood Type</option>
                  {bloodTypes.map((bt) => (<option key={bt} value={bt}>{bt}</option>))}
                </select>
                {errors.medical?.blood_type && <p className="mt-1 text-sm text-red-600">{errors.medical.blood_type.message}</p>}
              </div>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Donation Types *</label>
                <div className="space-y-2">
                  {donationTypes.map((dt) => (
                    <label key={dt} className="flex items-center">
                      <input 
                        type="checkbox" 
                        value={dt} 
                        {...register('medical.donation_types')} 
                        className="mr-2" 
                      />
                      {dt.replace('_', ' ').toUpperCase()}
                    </label>
                  ))}
                </div>
                {errors.medical?.donation_types && <p className="mt-1 text-sm text-red-600">{errors.medical.donation_types.message}</p>}
              </div>
              
              <Input 
                label="Weight (kg) *" 
                type="number" 
                step="0.1" 
                {...register('medical.weight_kg', { valueAsNumber: true })} 
                error={errors.medical?.weight_kg?.message}
                required
              />
              
              <Input 
                label="Illnesses (comma separated)" 
                {...register('medical.illnesses')} 
                placeholder="e.g., Diabetes, Hypertension" 
              />
              
              <Input 
                label="Medications (comma separated)" 
                {...register('medical.medications')} 
                placeholder="e.g., Insulin, Aspirin" 
              />
              
              <Input 
                label="Last Donation Date (Optional)" 
                type="date" 
                {...register('medical.last_donation_date')} 
              />
            </div>
          )}
          
          {/* Step 3: Location */}
          {step === 3 && (
            <div className="space-y-4">
              <Input 
                label="Phone Number *" 
                type="tel" 
                {...register('location.phone')} 
                placeholder="1234567890" 
                error={errors.location?.phone?.message}
                required
              />
              <Input 
                label="Email (Optional)" 
                type="email" 
                {...register('location.email')} 
              />
              <Input 
                label="Address *" 
                {...register('location.address')} 
                error={errors.location?.address?.message}
                required
              />
              <Input 
                label="City *" 
                {...register('location.city')} 
                error={errors.location?.city?.message}
                required
              />
              <Input 
                label="Pin Code *" 
                {...register('location.pin_code')} 
                error={errors.location?.pin_code?.message}
                required
              />
            </div>
          )}
          
          {/* Step 4: Preferences */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Availability</label>
                <div className="space-y-2">
                  {availabilityOptions.map((avail) => (
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
              
              <div className="mb-4">
                <label className="flex items-center">
                  <input 
                    type="checkbox" 
                    {...register('preferences.transport_available')} 
                    className="mr-2" 
                  />
                  I have my own transport
                </label>
              </div>
            </div>
          )}
          
          {/* Navigation Buttons */}
          <div className="flex justify-between mt-6">
            {step > 1 && (
              <Button variant="secondary" onClick={prevStep} type="button">
                Previous
              </Button>
            )}
            {step < 4 ? (
              <Button onClick={handleNextStep} type="button" className={step === 1 ? 'ml-auto' : ''}>
                Next
              </Button>
            ) : (
              <Button 
                loading={loading} 
                type="submit"
                disabled={loading}
              >
                {loading ? 'Registering...' : 'Register Donor'}
              </Button>
            )}
          </div>
        </form>
      </Card>
    </div>
  )
}