// donorpulse-frontend\src\app\donor\update\[token]\page.tsx  
'use client'

import { useParams } from 'next/navigation'
import { DonorProfileUpdateForm } from '@/components/donor/DonorProfileUpdateForm'

export default function UpdatePage() {
  const params = useParams()
  const token = params.token as string
  
  return <DonorProfileUpdateForm token={token} />
}