'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { User, Lock } from 'lucide-react'
import axios from 'axios'

interface LoginFormData {
  username: string
  password: string
}

export default function HospitalLoginPage() {
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>()

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await axios.post(`${API_URL}/auth/hospital/login`, data)
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('hospital', JSON.stringify(response.data.hospital))
      alert('Login successful!')
      window.location.href = '/hospital/dashboard'
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <Card title="Hospital Login">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="relative">
            <User className="absolute left-3 top-9 h-4 w-4 text-gray-400" />
            <Input
              label="Username"
              className="pl-9"
              {...register('username', { required: 'Username is required' })}
              error={errors.username?.message}
            />
          </div>
          
          <div className="relative">
            <Lock className="absolute left-3 top-9 h-4 w-4 text-gray-400" />
            <Input
              label="Password"
              type="password"
              className="pl-9"
              {...register('password', { required: 'Password is required' })}
              error={errors.password?.message}
            />
          </div>
          
          <Button type="submit" loading={loading} className="w-full">
            Login
          </Button>
        </form>
        
        <div className="mt-4 text-center">
          <a href="/hospital/register" className="text-blue-600 hover:underline text-sm">
            Don't have an account? Register here
          </a>
        </div>
      </Card>
    </div>
  )
}