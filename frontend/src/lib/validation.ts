// donorpulse-frontend\src\lib\validation.ts 
import { z } from 'zod'

export const donorRegistrationSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.number().min(18, 'Age must be 18 or older').max(65, 'Age must be 65 or younger'),
  gender: z.string().min(1, 'Gender is required'),
  photo_url: z.string().optional(),
  
  medical: z.object({
    blood_type: z.enum(['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']),
    donation_types: z.array(z.string()).min(1, 'Select at least one donation type'),
    weight_kg: z.number().min(50, 'Weight must be at least 50kg'),
    illnesses: z.array(z.string()),
    medications: z.array(z.string()),
    last_donation_date: z.string().optional(),
  }),
  
  location: z.object({
    phone: z.string().regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number'),
    email: z.string().email().optional(),
    address: z.string().min(5, 'Address is required'),
    city: z.string().min(2, 'City is required'),
    pin_code: z.string().min(3, 'Pin code is required'),
    lat: z.number().optional(),
    lng: z.number().optional(),
  }),
  
  preferences: z.object({
    contact_method: z.string(),
    availability: z.array(z.enum(['Morning', 'Afternoon', 'Evening', 'Night'])),
    language: z.string(),
    notify_types: z.array(z.enum(['Routine', 'Urgent', 'Critical', 'SOS'])),
    transport_available: z.boolean(),
  }),
})

export type DonorFormData = z.infer<typeof donorRegistrationSchema>