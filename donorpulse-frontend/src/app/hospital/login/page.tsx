// donorpulse-frontend\src\app\hospital\login\page.tsx 
'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { User, Lock } from 'lucide-react'
import { authAPI } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface LoginFormData {
  username: string
  password: string
}

export default function HospitalLoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>()

  const onSubmit = async (data: LoginFormData) => {
    setLoading(true)
    setError(null)
    try {
      const response = await authAPI.hospitalLogin(data.username, data.password)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('hospital', JSON.stringify(response.hospital))
      router.push('/hospital/dashboard')
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <Card title="Hospital Login">
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Username"
            {...register('username', { required: 'Username is required' })}
            error={errors.username?.message}
          />
          
          <Input
            label="Password"
            type="password"
            {...register('password', { required: 'Password is required' })}
            error={errors.password?.message}
          />
          
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