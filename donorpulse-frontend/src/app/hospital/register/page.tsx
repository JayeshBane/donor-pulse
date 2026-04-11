'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Building2, Mail, Phone, User, Lock, MapPin } from 'lucide-react'
import axios from 'axios'

interface HospitalFormData {
  name: string
  type: string
  license_number: string
  email: string
  phone: string
  username: string
  password: string
  address: string
  city: string
  pin_code: string
}

export default function HospitalRegisterPage() {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<HospitalFormData>()

  const onSubmit = async (data: HospitalFormData) => {
    setLoading(true)
    try {
      const payload = {
        name: data.name,
        type: data.type,
        license_number: data.license_number,
        email: data.email,
        phone: data.phone,
        username: data.username,
        password: data.password,
        location: {
          address: data.address,
          city: data.city,
          pin_code: data.pin_code
        }
      }
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await axios.post(`${API_URL}/hospitals/register`, payload)
      
      alert(`Hospital registered successfully!\n\nAwaiting admin verification.\nID: ${response.data.hospital_id}`)
      window.location.href = '/hospital/login'
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Card title="Hospital Registration">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="flex items-center space-x-2 mb-2">
            <Building2 className="h-5 w-5 text-gray-500" />
            <h3 className="font-medium">Hospital Information</h3>
          </div>
          
          <Input
            label="Hospital Name"
            {...register('name', { required: 'Name is required' })}
            error={errors.name?.message}
          />
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Hospital Type</label>
            <select
              {...register('type', { required: 'Type is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Type</option>
              <option value="government">Government</option>
              <option value="private">Private</option>
              <option value="trust">Trust</option>
              <option value="military">Military</option>
            </select>
            {errors.type && <p className="mt-1 text-sm text-red-600">{errors.type.message}</p>}
          </div>
          
          <Input
            label="License Number"
            {...register('license_number', { required: 'License number is required' })}
            error={errors.license_number?.message}
          />
          
          <div className="flex items-center space-x-2 mb-2 mt-4">
            <Mail className="h-5 w-5 text-gray-500" />
            <h3 className="font-medium">Contact Information</h3>
          </div>
          
          <Input
            label="Email"
            type="email"
            {...register('email', { required: 'Email is required' })}
            error={errors.email?.message}
          />
          
          <Input
            label="Phone"
            type="tel"
            {...register('phone', { required: 'Phone is required' })}
            error={errors.phone?.message}
          />
          
          <div className="flex items-center space-x-2 mb-2 mt-4">
            <User className="h-5 w-5 text-gray-500" />
            <h3 className="font-medium">Account Information</h3>
          </div>
          
          <Input
            label="Username"
            {...register('username', { required: 'Username is required', minLength: 3 })}
            error={errors.username?.message}
          />
          
          <Input
            label="Password"
            type="password"
            {...register('password', { required: 'Password is required', minLength: 6 })}
            error={errors.password?.message}
          />
          
          <div className="flex items-center space-x-2 mb-2 mt-4">
            <MapPin className="h-5 w-5 text-gray-500" />
            <h3 className="font-medium">Location</h3>
          </div>
          
          <Input
            label="Address"
            {...register('address', { required: 'Address is required' })}
            error={errors.address?.message}
          />
          
          <Input
            label="City"
            {...register('city', { required: 'City is required' })}
            error={errors.city?.message}
          />
          
          <Input
            label="Pin Code"
            {...register('pin_code', { required: 'Pin code is required' })}
            error={errors.pin_code?.message}
          />
          
          <Button type="submit" loading={loading} className="w-full">
            Register Hospital
          </Button>
        </form>
        
        <div className="mt-4 text-center">
          <a href="/hospital/login" className="text-blue-600 hover:underline text-sm">
            Already have an account? Login here
          </a>
        </div>
      </Card>
    </div>
  )
}