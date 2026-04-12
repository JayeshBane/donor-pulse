// donorpulse-frontend\src\lib\api.ts
import axios from 'axios'

// Use your new IP address
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 30000,
})



// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log(`📤 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// Handle 401 unauthorized responses
api.interceptors.response.use(
  (response) => {
    console.log(`📥 ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('hospital')
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/hospital/login')) {
        window.location.href = '/hospital/login'
      }
    }
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
  
  toggleActive: async (id: string) => {
    const response = await api.patch(`/donors/${id}/toggle-active`)
    return response.data
  },

  // Add to donorAPI object
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
}

// Auth API
export const authAPI = {
  hospitalLogin: async (username: string, password: string) => {
    const response = await api.post('/auth/hospital/login', { username, password })
    return response.data
  },
  
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

// Hospital API
export const hospitalAPI = {
  register: async (data: any) => {
    const response = await api.post('/hospitals/register', data)
    return response.data
  },
  
  getHospitals: async (params?: any) => {
    const response = await api.get('/hospitals/', { params })
    return response.data
  },
  
  getHospital: async (id: string) => {
    const response = await api.get(`/hospitals/${id}`)
    return response.data
  },
}

export default api