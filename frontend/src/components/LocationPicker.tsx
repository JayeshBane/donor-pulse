// frontend\src\components\LocationPicker.tsx
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { MapPin, Loader2 } from 'lucide-react'

interface LocationPickerProps {
  onLocationSelect: (lat: number, lng: number) => void
  label?: string
}

export const LocationPicker: React.FC<LocationPickerProps> = ({ 
  onLocationSelect, 
  label = "Use My Current Location" 
}) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getCurrentLocation = () => {
    setLoading(true)
    setError(null)
    
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser')
      setLoading(false)
      return
    }
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        onLocationSelect(position.coords.latitude, position.coords.longitude)
        setLoading(false)
      },
      (err) => {
        setError(err.message)
        setLoading(false)
      }
    )
  }
  
  return (
    <div>
      <Button 
        type="button" 
        variant="secondary" 
        onClick={getCurrentLocation}
        disabled={loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Getting Location...
          </>
        ) : (
          <>
            <MapPin className="h-4 w-4 mr-2" />
            {label}
          </>
        )}
      </Button>
      {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
    </div>
  )
}