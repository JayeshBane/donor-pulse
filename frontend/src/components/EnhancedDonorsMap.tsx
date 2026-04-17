// frontend\src\components\EnhancedDonorsMap.tsx
'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

// Dynamically import Leaflet components
const MapContainer = dynamic(() => import('react-leaflet').then((mod) => mod.MapContainer), { ssr: false })
const TileLayer = dynamic(() => import('react-leaflet').then((mod) => mod.TileLayer), { ssr: false })
const Marker = dynamic(() => import('react-leaflet').then((mod) => mod.Marker), { ssr: false })
const Popup = dynamic(() => import('react-leaflet').then((mod) => mod.Popup), { ssr: false })
const Polyline = dynamic(() => import('react-leaflet').then((mod) => mod.Polyline), { ssr: false })

interface Donor {
  id: string
  name: string
  lat: number
  lng: number
  distance?: number
  eta?: number
  status: string
}

interface EnhancedDonorsMapProps {
  donors: Donor[]
  hospitalLat: number
  hospitalLng: number
  hospitalName: string
  orsApiKey: string
  weatherApiKey: string
}

// Custom icons based on donor status
const getDonorIcon = (status: string) => {
  let iconUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png' // default blue
  
  if (status === 'accepted') {
    iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png'
  } else if (status === 'pending') {
    iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png'
  } else if (status === 'declined') {
    iconUrl = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png'
  }
  
  return new L.Icon({
    iconUrl: iconUrl,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  })
}

const hospitalIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function EnhancedDonorsMap({ 
  donors, 
  hospitalLat, 
  hospitalLng, 
  hospitalName,
  orsApiKey,
  weatherApiKey 
}: EnhancedDonorsMapProps) {
  const [center, setCenter] = useState<[number, number]>([hospitalLat, hospitalLng])
  const [routeData, setRouteData] = useState<Record<string, any>>({})
  const [weatherData, setWeatherData] = useState<Record<string, any>>({})

  useEffect(() => {
    // Calculate center point to show all donors
    if (donors.length > 0) {
      const allLats = [hospitalLat, ...donors.map(d => d.lat)]
      const allLngs = [hospitalLng, ...donors.map(d => d.lng)]
      const centerLat = (Math.min(...allLats) + Math.max(...allLats)) / 2
      const centerLng = (Math.min(...allLngs) + Math.max(...allLngs)) / 2
      setCenter([centerLat, centerLng])
    }
    
    // Fetch routes and weather for each donor (only for accepted ones)
    donors.forEach(donor => {
      if (donor.status === 'accepted') {
        fetchRealRoute(donor)
        fetchWeather(donor)
      } else {
        // For non-accepted donors, just use straight line
        setRouteData(prev => ({
          ...prev,
          [donor.id]: {
            route: [[donor.lat, donor.lng], [hospitalLat, hospitalLng]],
            distance: donor.distance,
            eta: donor.eta,
            traffic_delay: 0
          }
        }))
      }
    })
  }, [donors, hospitalLat, hospitalLng])

  const fetchRealRoute = async (donor: Donor) => {
    if (!orsApiKey) {
      console.warn('OpenRouteService API key not configured')
      return
    }
    
    try {
      const response = await fetch('https://api.openrouteservice.org/v2/directions/driving-car/geojson', {
        method: 'POST',
        headers: {
          'Authorization': orsApiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          coordinates: [
            [donor.lng, donor.lat],
            [hospitalLng, hospitalLat]
          ],
          options: {
            profile: 'driving-car',
            preference: 'fastest',
            units: 'km'
          }
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        const coordinates = data.features[0].geometry.coordinates
        const routePoints = coordinates.map((coord: [number, number]) => [coord[1], coord[0]])
        
        const distance = data.features[0].properties.segments[0].distance / 1000
        let duration = data.features[0].properties.segments[0].duration / 60
        
        // Apply weather factor to ETA
        if (weatherData[donor.id]) {
          const weather = weatherData[donor.id]
          let weatherFactor = 1.0
          if (weather.rain > 0) weatherFactor += 0.2
          if (weather.wind_speed > 20) weatherFactor += 0.1
          duration = duration * weatherFactor
        }
        
        setRouteData(prev => ({
          ...prev,
          [donor.id]: {
            route: routePoints,
            distance: Math.round(distance * 10) / 10,
            eta: Math.round(duration),
            traffic_delay: Math.round(duration - (data.features[0].properties.segments[0].duration / 60))
          }
        }))
      }
    } catch (error) {
      console.error(`Error fetching route for ${donor.name}:`, error)
      setRouteData(prev => ({
        ...prev,
        [donor.id]: {
          route: [[donor.lat, donor.lng], [hospitalLat, hospitalLng]],
          distance: donor.distance,
          eta: donor.eta,
          traffic_delay: 0
        }
      }))
    }
  }

  const fetchWeather = async (donor: Donor) => {
    if (!weatherApiKey) {
      console.warn('Weather API key not configured')
      return
    }
    
    try {
      const response = await fetch(
        `https://api.openweathermap.org/data/2.5/weather?lat=${donor.lat}&lon=${donor.lng}&appid=${weatherApiKey}&units=metric`
      )
      
      if (response.ok) {
        const data = await response.json()
        setWeatherData(prev => ({
          ...prev,
          [donor.id]: {
            condition: data.weather[0].main,
            description: data.weather[0].description,
            temp: Math.round(data.main.temp),
            wind_speed: data.wind.speed,
            rain: data.rain?.['1h'] || 0,
            icon: `https://openweathermap.org/img/w/${data.weather[0].icon}.png`
          }
        }))
      }
    } catch (error) {
      console.error(`Error fetching weather for ${donor.name}:`, error)
    }
  }

  // Get route color based on traffic/weather (only for accepted donors)
  const getRouteColor = (donorId: string, status: string) => {
    if (status !== 'accepted') return '#9ca3af' // gray for non-accepted
    
    const route = routeData[donorId]
    if (!route) return '#2563eb'
    
    if (route.traffic_delay > 15) return '#dc2626' // red - heavy delay
    if (route.traffic_delay > 5) return '#f59e0b' // orange - moderate delay
    return '#10b981' // green - light traffic
  }

  // Get route style (dashed for non-accepted)
  const getRouteStyle = (status: string) => {
    if (status !== 'accepted') {
      return { dashArray: '5, 5', opacity: 0.4 }
    }
    return { dashArray: undefined, opacity: 0.8 }
  }

  if (donors.length === 0) {
    return (
      <div className="flex justify-center items-center h-96 bg-gray-100 rounded-lg">
        <div className="text-center">
          <p className="text-gray-500">No donors to display on map</p>
          <p className="text-sm text-gray-400 mt-1">Donors will appear here once they are matched</p>
        </div>
      </div>
    )
  }

  return (
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
          <p className="font-semibold mb-1">🚦 Traffic Legend</p>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 bg-green-500 rounded"></div>
            <span>Light Traffic (&lt;5 min delay)</span>
          </div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 bg-orange-500 rounded"></div>
            <span>Moderate Traffic (5-15 min delay)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <span>Heavy Traffic (&gt;15 min delay)</span>
          </div>
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '500px', width: '100%', borderRadius: '0.5rem' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Hospital Marker */}
        <Marker position={[hospitalLat, hospitalLng]} icon={hospitalIcon}>
          <Popup>
            <div className="text-center">
              <p className="font-semibold">🏥 {hospitalName}</p>
              <p className="text-xs text-gray-500">Destination</p>
            </div>
          </Popup>
        </Marker>
        
        {/* Donor Markers and Routes */}
        {donors.map((donor) => {
          const route = routeData[donor.id]
          const weather = weatherData[donor.id]
          const donorIcon = getDonorIcon(donor.status)
          const routeColor = getRouteColor(donor.id, donor.status)
          const routeStyle = getRouteStyle(donor.status)
          
          const getStatusText = () => {
            switch(donor.status) {
              case 'accepted': return '✅ Accepted'
              case 'pending': return '⏳ Pending Response'
              case 'declined': return '❌ Declined'
              default: return donor.status
            }
          }
          
          return (
            <div key={donor.id}>
              <Marker position={[donor.lat, donor.lng]} icon={donorIcon}>
                <Popup>
                  <div className="text-center min-w-[180px]">
                    <p className="font-semibold">🩸 {donor.name}</p>
                    <p className="text-sm text-gray-600">Status: {getStatusText()}</p>
                    
                    {weather && donor.status === 'accepted' && (
                      <div className="mt-2 pt-2 border-t">
                        <p className="text-xs font-semibold">🌤️ Weather</p>
                        <p className="text-xs">{weather.description}, {weather.temp}°C</p>
                        {weather.rain > 0 && (
                          <p className="text-xs text-blue-600">🌧️ Rain: {weather.rain}mm (+20% time)</p>
                        )}
                      </div>
                    )}
                    
                    {route && (
                      <div className="mt-2 pt-2 border-t">
                        <p className="text-xs font-semibold">🚗 Route Info</p>
                        <p className="text-xs">📏 Distance: {route.distance} km</p>
                        {donor.status === 'accepted' && (
                          <>
                            <p className="text-xs">⏱️ ETA: {route.eta} min</p>
                            {route.traffic_delay > 0 && (
                              <p className="text-xs text-orange-600">🚦 Traffic delay: +{route.traffic_delay} min</p>
                            )}
                          </>
                        )}
                        {donor.status !== 'accepted' && (
                          <p className="text-xs text-gray-500">Awaiting acceptance for ETA</p>
                        )}
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
              
              {/* Route Line */}
              {route && route.route && (
                <Polyline
                  positions={route.route}
                  color={routeColor}
                  weight={donor.status === 'accepted' ? 4 : 2}
                  opacity={routeStyle.opacity}
                  dashArray={routeStyle.dashArray}
                />
              )}
            </div>
          )
        })}
      </MapContainer>
    </div>
  )
}