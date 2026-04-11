// donorpulse-frontend\src\lib\api.ts
import axios from 'axios'

// Use relative URL for production, fallback to localhost for development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL

// For production, use relative path (will proxy through Next.js)
const isProduction = process.env.NODE_ENV === 'production'

const api = axios.create({
  baseURL: isProduction ? '/api/v1' : API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000,
  withCredentials: false, // Set to true if using cookies
})

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log(`📤 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data)
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`📥 ${response.status} ${response.config.url}`, response.data)
    return response
  },
  (error) => {
    console.error('Response error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Donor API
export const donorAPI = {
  register: async (data: any) => {
    const response = await api.post('/donors/register', data)
    return response.data
  },
  
  getDonor: async (id: string) => {
    const response = await api.get(`/donors/${id}`)
    return response.data
  },
  
  getDonors: async (params?: any) => {
    const response = await api.get('/donors/', { params })
    return response.data
  },
  
  getDonorByPhone: async (phone: string) => {
    const response = await api.get('/donors/by-phone/', { params: { phone } })
    return response.data
  },
  
  updateDonor: async (id: string, data: any) => {
    const response = await api.patch(`/donors/${id}`, data)
    return response.data
  },
  
  toggleActive: async (id: string) => {
    const response = await api.patch(`/donors/${id}/toggle-active`)
    return response.data
  },
  
  getStatus: async (phone: string) => {
    try {
      const donor = await donorAPI.getDonorByPhone(phone)
      
      // Calculate cooldown
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
  
  getHistory: async (phone: string) => {
    // Mock data for now
    return {
      donations: [
        { date: "2024-12-15", blood_type: "O+", hospital: "City Hospital", status: "Completed" },
        { date: "2024-10-20", blood_type: "O+", hospital: "General Hospital", status: "Completed" }
      ]
    }
  },
}

// Auth API
export const authAPI = {
  generateMagicLink: async (phone: string) => {
    const response = await api.post('/auth/donor/generate-magic-link', null, {
      params: { phone }
    })
    return response.data
  },
  
  verifyMagicLink: async (token: string) => {
    const response = await api.post(`/auth/donor/verify-magic-link/${token}`)
    return response.data
  },
  
  updateViaMagicLink: async (token: string, data: any) => {
    const response = await api.put(`/auth/donor/update/${token}`, data)
    return response.data
  },
}

export default api