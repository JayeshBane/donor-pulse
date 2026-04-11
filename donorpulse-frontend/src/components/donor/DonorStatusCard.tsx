// donorpulse-frontend\src\components\donor\DonorStatusCard.tsx 
'use client'

import React, { useState, useEffect } from 'react'
import { donorAPI } from '@/lib/api'
import { Card } from '@/components/ui/Card'

interface DonorStatusCardProps {
  phone: string
}

export const DonorStatusCard: React.FC<DonorStatusCardProps> = ({ phone }) => {
  const [status, setStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await donorAPI.getStatus(phone)
        setStatus(data)
      } catch (error) {
        console.error('Failed to fetch status', error)
      } finally {
        setLoading(false)
      }
    }
    
    if (phone) {
      fetchStatus()
    }
  }, [phone])
  
  if (loading) {
    return <div className="text-center">Loading status...</div>
  }
  
  if (!status) {
    return <div className="text-center text-red-600">Donor not found</div>
  }
  
  return (
    <Card title="Donor Status">
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="font-medium">Eligibility:</span>
          <span className={status.eligibility ? 'text-green-600' : 'text-red-600'}>
            {status.eligibility ? 'Eligible' : 'Not Eligible'}
          </span>
        </div>
        
        {status.cooldown_days_remaining > 0 && (
          <div className="flex justify-between">
            <span className="font-medium">Cooldown Remaining:</span>
            <span>{status.cooldown_days_remaining} days</span>
          </div>
        )}
        
        <div className="flex justify-between">
          <span className="font-medium">Last Donation:</span>
          <span>{status.last_donation_date ? new Date(status.last_donation_date).toLocaleDateString() : 'Never'}</span>
        </div>
        
        <div className="flex justify-between">
          <span className="font-medium">Reliability Score:</span>
          <span>
            <span className="font-bold">{status.reliability_score}</span>/100
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div 
                className="bg-blue-600 rounded-full h-2 transition-all"
                style={{ width: `${status.reliability_score}%` }}
              />
            </div>
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="font-medium">Status:</span>
          <span className={status.is_active && !status.is_paused ? 'text-green-600' : 'text-red-600'}>
            {!status.is_active ? 'Deactivated' : status.is_paused ? 'Paused' : 'Active'}
          </span>
        </div>
      </div>
    </Card>
  )
}