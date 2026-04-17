// 
'use client'

import { useState, useEffect, useCallback } from 'react'
import { GoogleMap, LoadScript, Marker, DirectionsRenderer, InfoWindow } from '@react-google-maps/api'

const mapContainerStyle = {
  width: '100%',
  height: '500px',
  borderRadius: '0.5rem'
}

interface Donor {
  id: string
  name: string
  lat: number
  lng: number
  distance?: number
  eta?: number
  status: string
}

interface GoogleDonorsMapProps {
  donors: Donor[]
  hospitalLat: number
  hospitalLng: number
  hospitalName: string
  googleMapsApiKey: string
}

export default function GoogleDonorsMap({ 
  donors, 
  hospitalLat, 
  hospitalLng, 
  hospitalName,
  googleMapsApiKey 
}: GoogleDonorsMapProps) {
  const [map, setMap] = useState<google.maps.Map | null>(null)
  const [directions, setDirections] = useState<Record<string, google.maps.DirectionsResult>>({})
  const [selectedDonor, setSelectedDonor] = useState<Donor | null>(null)
  const [travelTimes, setTravelTimes] = useState<Record<string, { distance: string; duration: string }>>({})
  const [isApiLoaded, setIsApiLoaded] = useState(false)

  // Calculate center of map
  const center = {
    lat: donors.length > 0 ? (donors.reduce((sum, d) => sum + d.lat, hospitalLat) / (donors.length + 1)) : hospitalLat,
    lng: donors.length > 0 ? (donors.reduce((sum, d) => sum + d.lng, hospitalLng) / (donors.length + 1)) : hospitalLng
  }

  // Get directions for each donor
  useEffect(() => {
    if (!googleMapsApiKey || !isApiLoaded) return
    
    donors.forEach(donor => {
      if (donor.status === 'accepted') {
        getDirections(donor)
        getDistanceMatrix(donor)
      }
    })
  }, [donors, hospitalLat, hospitalLng, isApiLoaded])

  const getDirections = async (donor: Donor) => {
    if (!window.google) return
    
    const directionsService = new window.google.maps.DirectionsService()
    
    try {
      const result = await directionsService.route({
        origin: { lat: donor.lat, lng: donor.lng },
        destination: { lat: hospitalLat, lng: hospitalLng },
        travelMode: window.google.maps.TravelMode.DRIVING,
        drivingOptions: {
          departureTime: new Date(),
          trafficModel: window.google.maps.TrafficModel.BEST_GUESS
        }
      })
      
      setDirections(prev => ({ ...prev, [donor.id]: result }))
    } catch (error) {
      console.error(`Error getting directions for ${donor.name}:`, error)
    }
  }

  const getDistanceMatrix = async (donor: Donor) => {
    if (!window.google) return
    
    const distanceMatrixService = new window.google.maps.DistanceMatrixService()
    
    try {
      const result = await distanceMatrixService.getDistanceMatrix({
        origins: [{ lat: donor.lat, lng: donor.lng }],
        destinations: [{ lat: hospitalLat, lng: hospitalLng }],
        travelMode: window.google.maps.TravelMode.DRIVING,
        drivingOptions: {
          departureTime: new Date(),
          trafficModel: window.google.maps.TrafficModel.BEST_GUESS
        },
        unitSystem: window.google.maps.UnitSystem.METRIC
      })
      
      if (result.rows[0].elements[0].status === 'OK') {
        setTravelTimes(prev => ({
          ...prev,
          [donor.id]: {
            distance: result.rows[0].elements[0].distance.text,
            duration: result.rows[0].elements[0].duration_in_traffic?.text || result.rows[0].elements[0].duration.text
          }
        }))
      }
    } catch (error) {
      console.error(`Error getting distance for ${donor.name}:`, error)
    }
  }

  const onLoad = useCallback((map: google.maps.Map) => {
    setMap(map)
  }, [])

  const onApiLoad = () => {
    setIsApiLoaded(true)
  }

  // Get marker color based on status (only after API loads)
  const getMarkerIcon = (status: string) => {
    if (!window.google) return undefined
    
    const colors: Record<string, string> = {
      accepted: 'green',
      pending: 'yellow',
      declined: 'red'
    }
    
    const color = colors[status] || 'blue'
    
    return {
      url: `https://maps.google.com/mapfiles/ms/icons/${color}-dot.png`,
      scaledSize: new window.google.maps.Size(32, 32)
    }
  }

  const getHospitalIcon = () => {
    if (!window.google) return undefined
    
    return {
      url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
      scaledSize: new window.google.maps.Size(32, 32)
    }
  }

  if (!googleMapsApiKey) {
    return (
      <div className="flex justify-center items-center h-96 bg-gray-100 rounded-lg">
        <div className="text-center">
          <p className="text-red-500">Google Maps API key not configured</p>
          <p className="text-sm text-gray-500 mt-1">Please add NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to .env.local</p>
        </div>
      </div>
    )
  }

  return (
    <LoadScript 
      googleMapsApiKey={googleMapsApiKey}
      onLoad={onApiLoad}
    >
      {!isApiLoaded ? (
        <div className="flex justify-center items-center h-96 bg-gray-100 rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading Google Maps...</p>
          </div>
        </div>
      ) : (
        <div className="relative">
          {/* Legend */}
          <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg text-xs">
            <p className="font-semibold mb-2">📍 Donor Status</p>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-4 h-4 rounded-full bg-green-500"></div>
              <span>Accepted (with route)</span>
            </div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
              <span>Pending Response</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-4 h-4 rounded-full bg-red-500"></div>
              <span>Declined</span>
            </div>
            <div className="border-t pt-2 mt-1">
              <p className="font-semibold mb-1">🚦 Features</p>
              <p className="text-gray-600">✓ Real-time traffic</p>
              <p className="text-gray-600">✓ Accurate ETA</p>
              <p className="text-gray-600">✓ Turn-by-turn route</p>
            </div>
          </div>

          <GoogleMap
            mapContainerStyle={mapContainerStyle}
            center={center}
            zoom={12}
            onLoad={onLoad}
            options={{
              zoomControl: true,
              streetViewControl: true,
              mapTypeControl: true,
              fullscreenControl: true,
            }}
          >
            {/* Hospital Marker */}
            <Marker
              position={{ lat: hospitalLat, lng: hospitalLng }}
              icon={getHospitalIcon()}
              title={hospitalName}
            />

            {/* Donor Markers and Routes */}
            {donors.map((donor) => (
              <div key={donor.id}>
                <Marker
                  position={{ lat: donor.lat, lng: donor.lng }}
                  icon={getMarkerIcon(donor.status)}
                  onClick={() => setSelectedDonor(donor)}
                  title={donor.name}
                />
                
                {directions[donor.id] && (
                  <DirectionsRenderer
                    directions={directions[donor.id]}
                    options={{
                      suppressMarkers: true,
                      polylineOptions: {
                        strokeColor: donor.status === 'accepted' ? '#10b981' : '#9ca3af',
                        strokeWeight: 4,
                        strokeOpacity: donor.status === 'accepted' ? 0.8 : 0.4
                      }
                    }}
                  />
                )}
              </div>
            ))}

            {/* Info Window for selected donor */}
            {selectedDonor && (
              <InfoWindow
                position={{ lat: selectedDonor.lat, lng: selectedDonor.lng }}
                onCloseClick={() => setSelectedDonor(null)}
              >
                <div className="p-2 min-w-[200px]">
                  <h3 className="font-semibold text-lg">{selectedDonor.name}</h3>
                  <p className="text-sm text-gray-600">
                    Status: {selectedDonor.status === 'accepted' ? '✅ Accepted' : 
                             selectedDonor.status === 'pending' ? '⏳ Pending' : '❌ Declined'}
                  </p>
                  {travelTimes[selectedDonor.id] && (
                    <>
                      <p className="text-sm mt-2">
                        <span className="font-semibold">Distance:</span> {travelTimes[selectedDonor.id].distance}
                      </p>
                      <p className="text-sm">
                        <span className="font-semibold">ETA with traffic:</span> {travelTimes[selectedDonor.id].duration}
                      </p>
                    </>
                  )}
                  {!travelTimes[selectedDonor.id] && selectedDonor.status === 'accepted' && (
                    <p className="text-sm text-gray-500 mt-2">Loading route...</p>
                  )}
                  {selectedDonor.status !== 'accepted' && (
                    <p className="text-sm text-gray-500 mt-2">Awaiting acceptance for ETA</p>
                  )}
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        </div>
      )}
    </LoadScript>
  )
}