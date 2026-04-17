// lib/api.ts
import apiClient from './api-client';

// Re-export the client as default
export default apiClient;

// Donor API
export const donorAPI = {
  register: async (data: any) => {
    const response = await apiClient.post('/donors/register', data)
    return response.data
  },
  
  getDonor: async (id: string) => {
    const response = await apiClient.get(`/donors/${id}`)
    return response.data
  },
  
  getDonors: async (params?: any) => {
    const response = await apiClient.get('/donors/', { params })
    return response.data
  },
  
  getDonorByPhone: async (phone: string) => {
    const response = await apiClient.get('/donors/by-phone/', { params: { phone } })
    return response.data
  },
  
  toggleActive: async (id: string) => {
    const response = await apiClient.patch(`/donors/${id}/toggle-active`)
    return response.data
  },

  getStatus: async (phone: string) => {
    try {
      const donor = await donorAPI.getDonorByPhone(phone)
      
      let cooldownDays = 0
      let isEligible = donor.is_active && !donor.is_paused
      
      if (donor.medical?.last_donation_date) {
        const lastDonation = new Date(donor.medical.last_donation_date)
        const daysSince = Math.floor((Date.now() - lastDonation.getTime()) / (1000 * 60 * 60 * 24))
        if (daysSince < 56) {
          cooldownDays = 56 - daysSince
          isEligible = false
        }
      }
      
      return {
        eligibility: isEligible,
        cooldown_days_remaining: cooldownDays,
        last_donation_date: donor.medical?.last_donation_date,
        reliability_score: donor.reliability_score || 100,
        is_active: donor.is_active,
        is_paused: donor.is_paused,
        blood_type: donor.medical?.blood_type,
        city: donor.location?.city
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error('Donor not found. Please register first.')
      }
      throw error
    }
  },
}

// Auth API
export const authAPI = {
  hospitalLogin: async (username: string, password: string) => {
    const response = await apiClient.post('/auth/hospital/login', { username, password })
    return response.data
  },
  
  generateMagicLink: async (phone: string) => {
    const response = await apiClient.post('/auth/donor/generate-magic-link', null, {
      params: { phone }
    })
    return response.data
  },
  
  verifyMagicLink: async (token: string) => {
    const response = await apiClient.post(`/auth/donor/verify-magic-link/${token}`)
    return response.data
  },
  
  updateViaMagicLink: async (token: string, data: any) => {
    const response = await apiClient.put(`/auth/donor/update/${token}`, data)
    return response.data
  },
}

// Hospital API
export const hospitalAPI = {
  register: async (data: any) => {
    const response = await apiClient.post('/hospitals/register', data)
    return response.data
  },
  
  getHospitals: async (params?: any) => {
    const response = await apiClient.get('/hospitals/', { params })
    return response.data
  },
  
  getHospital: async (id: string) => {
    const response = await apiClient.get(`/hospitals/${id}`)
    return response.data
  },
}