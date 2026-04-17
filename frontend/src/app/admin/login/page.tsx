// donorpulse-frontend\src\app\admin\login\page.tsx
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { User, Lock, Shield } from 'lucide-react'
import { useRouter } from 'next/navigation'
import apiClient from '@/lib/api-client'

interface LoginFormData {
  username: string
  password: string
}

export default function AdminLoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>()

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    setError(null)
    try {
      // Use apiClient instead of hardcoded URL
      const response = await apiClient.post('/admin/login', data)
      localStorage.setItem('admin_token', response.data.access_token)
      localStorage.setItem('admin', JSON.stringify(response.data.admin))
      router.push('/admin/dashboard')
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full mx-auto p-6">
        <Card title="Admin Login">
          <div className="text-center mb-6">
            <Shield className="h-12 w-12 text-blue-600 mx-auto mb-2" />
            <p className="text-gray-600">Administrator Access Only</p>
          </div>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Username"
              icon={<User className="h-4 w-4" />}
              {...register('username', { required: 'Username is required' })}
              error={errors.username?.message}
            />
            
            <Input
              label="Password"
              type="password"
              icon={<Lock className="h-4 w-4" />}
              {...register('password', { required: 'Password is required' })}
              error={errors.password?.message}
            />
            
            <Button type="submit" loading={loading} className="w-full">
              Login as Admin
            </Button>
          </form>
          
          <div className="mt-4 text-center text-sm text-gray-500">
            <p>Default Admin: admin / Admin@123</p>
            <p className="text-xs mt-2">Run setup first if no admin exists</p>
          </div>
        </Card>
      </div>
    </div>
  )
}