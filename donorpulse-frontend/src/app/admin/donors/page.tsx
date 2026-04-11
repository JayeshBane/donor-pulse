// donorpulse-frontend\src\app\admin\donors\page.tsx 
'use client'

import { useState, useEffect } from 'react'
import { donorAPI } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

interface Donor {
  _id: string
  name: string
  age: number
  location: { phone: string; city: string }
  medical: { blood_type: string }
  is_active: boolean
  reliability_score: number
}

export default function AdminDonorsPage() {
  const [donors, setDonors] = useState<Donor[]>([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ blood_type: '', city: '', is_active: '' })
  
  useEffect(() => {
    fetchDonors()
  }, [filters])
  
  const fetchDonors = async () => {
    try {
      const params: any = {}
      if (filters.blood_type) params.blood_type = filters.blood_type
      if (filters.city) params.city = filters.city
      if (filters.is_active !== '') params.is_active = filters.is_active === 'true'
      
      const response = await donorAPI.getDonors(params)
      setDonors(response.donors)
    } catch (error) {
      console.error('Failed to fetch donors', error)
    } finally {
      setLoading(false)
    }
  }
  
  const toggleDonorActive = async (id: string) => {
    try {
      await donorAPI.toggleActive(id)
      fetchDonors()
    } catch (error) {
      console.error('Failed to toggle donor', error)
    }
  }
  
  return (
    <div className="max-w-7xl mx-auto p-6">
      <Card title="Donor Management">
        {/* Filters */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Input
            label="Blood Type"
            placeholder="O+, A-, etc."
            onChange={(e) => setFilters({ ...filters, blood_type: e.target.value })}
          />
          <Input
            label="City"
            placeholder="Filter by city"
            onChange={(e) => setFilters({ ...filters, city: e.target.value })}
          />
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              className="w-full px-3 py-2 border rounded-lg"
              onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
            >
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </div>
        
        {/* Donors Table */}
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left">Name</th>
                  <th className="px-4 py-2 text-left">Blood Type</th>
                  <th className="px-4 py-2 text-left">Phone</th>
                  <th className="px-4 py-2 text-left">City</th>
                  <th className="px-4 py-2 text-left">Score</th>
                  <th className="px-4 py-2 text-left">Status</th>
                  <th className="px-4 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {donors.map((donor) => (
                  <tr key={donor._id} className="border-t">
                    <td className="px-4 py-2">{donor.name}</td>
                    <td className="px-4 py-2">{donor.medical.blood_type}</td>
                    <td className="px-4 py-2">{donor.location.phone}</td>
                    <td className="px-4 py-2">{donor.location.city}</td>
                    <td className="px-4 py-2">{donor.reliability_score}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        donor.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {donor.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <Button
                        size="sm"
                        variant={donor.is_active ? 'danger' : 'success'}
                        onClick={() => toggleDonorActive(donor._id)}
                      >
                        {donor.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}