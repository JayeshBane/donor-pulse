// donorpulse-frontend\src\types\donor.ts 
export type BloodType = 'O-' | 'O+' | 'A-' | 'A+' | 'B-' | 'B+' | 'AB-' | 'AB+'
export type DonationType = 'whole_blood' | 'platelets' | 'plasma' | 'double_rbc'
export type Availability = 'Morning' | 'Afternoon' | 'Evening' | 'Night'
export type NotifyType = 'Routine' | 'Urgent' | 'Critical' | 'SOS'

export interface DonorMedical {
  blood_type: BloodType
  donation_types: DonationType[]
  weight_kg: number
  illnesses: string[]
  medications: string[]
  last_donation_date?: string
}

export interface DonorLocation {
  phone: string
  email?: string
  address: string
  city: string
  pin_code: string
  lat?: number
  lng?: number
}

export interface DonorPreferences {
  contact_method: string
  availability: Availability[]
  language: string
  notify_types: NotifyType[]
  transport_available: boolean
}

export interface Donor {
  id?: string
  name: string
  age: number
  gender: string
  photo_url?: string
  medical: DonorMedical
  location: DonorLocation
  preferences: DonorPreferences
  is_active: boolean
  is_paused: boolean
  reliability_score: number
  created_at?: string
}

export interface DonorStatus {
  eligibility: boolean
  cooldown_days_remaining: number
  last_donation_date: string
  reliability_score: number
  is_active: boolean
  is_paused: boolean
}

export interface DonationHistory {
  date: string
  blood_type: string
  hospital: string
  status: string
}