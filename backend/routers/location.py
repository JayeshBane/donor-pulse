# backend\routers\location.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from bson import ObjectId
from database import get_db
from middleware.auth import get_verified_hospital
from config import settings
import requests
import logging
from math import radians, sin, cos, sqrt, atan2

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/location", tags=["location"])

async def calculate_road_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> dict:
    """Calculate road distance and ETA using OpenRouteService"""
    try:
        if not settings.ors_api_key:
            logger.warning("ORS_API_KEY not set, using straight-line distance")
            return None
        
        headers = {
            "Authorization": settings.ors_api_key,
            "Content-Type": "application/json"
        }
        
        body = {
            "coordinates": [[lng1, lat1], [lng2, lat2]],
            "format": "json"
        }
        
        response = requests.post(settings.ors_api_url, json=body, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            distance_km = data['features'][0]['properties']['segments'][0]['distance'] / 1000
            duration_min = data['features'][0]['properties']['segments'][0]['duration'] / 60
            
            return {
                "distance_km": round(distance_km, 2),
                "duration_min": round(duration_min, 2),
                "duration_text": f"{int(duration_min)} minutes"
            }
        
        return None
        
    except Exception as e:
        logger.error(f"OpenRouteService error: {e}")
        return None

async def get_weather(lat: float, lng: float) -> dict:
    """Get weather conditions for ETA adjustment"""
    try:
        if not settings.weather_api_key:
            return {"weather": None, "factor": 1.0}
        
        params = {
            "lat": lat,
            "lon": lng,
            "appid": settings.weather_api_key,
            "units": "metric"
        }
        
        response = requests.get(settings.weather_api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            weather = {
                "condition": data['weather'][0]['main'],
                "description": data['weather'][0]['description'],
                "temp": data['main']['temp'],
                "wind_speed": data['wind']['speed'],
                "rain": data.get('rain', {}).get('1h', 0)
            }
            
            # Calculate weather factor (rain = +20% time)
            factor = 1.0
            if weather['rain'] > 0:
                factor += 0.2
            if weather['wind_speed'] > 20:
                factor += 0.1
                
            return {"weather": weather, "factor": factor}
        
        return {"weather": None, "factor": 1.0}
        
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {"weather": None, "factor": 1.0}

def calculate_straight_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> dict:
    """Fallback: Calculate straight-line distance using Haversine formula"""
    R = 6371
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    
    return {
        "distance_km": round(distance, 2),
        "duration_min": round(distance * 2, 2),
        "duration_text": f"{int(distance * 2)} minutes",
        "source": "straight_line"
    }

@router.post("/share/{request_id}")
async def share_location(
    request_id: str,
    lat: float = Query(..., description="Donor latitude"),
    lng: float = Query(..., description="Donor longitude"),
    db=Depends(get_db)
):
    """Donor shares live location for a blood request"""
    try:
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        
        # Find the matched donor record
        matched_donor = await db.matched_donors.find_one({
            "request_id": request_id,
            "status": "accepted"
        })
        
        if not matched_donor:
            raise HTTPException(status_code=404, detail="No active request found")
        
        # Get request and hospital details
        blood_request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
        if not blood_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(blood_request["hospital_id"])})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        hospital_lat = hospital.get("location", {}).get("lat")
        hospital_lng = hospital.get("location", {}).get("lng")
        
        if not hospital_lat or not hospital_lng:
            raise HTTPException(status_code=400, detail="Hospital location not available")
        
        # Calculate road distance and ETA
        route = await calculate_road_distance(lat, lng, hospital_lat, hospital_lng)
        
        if not route:
            route = calculate_straight_distance(lat, lng, hospital_lat, hospital_lng)
            route["source"] = "straight_line"
        else:
            route["source"] = "openrouteservice"
        
        # Get weather for ETA adjustment
        weather_data = await get_weather(lat, lng)
        adjusted_duration = route['duration_min'] * weather_data['factor']
        
        # Update matched donor with location and ETA
        await db.matched_donors.update_one(
            {"_id": matched_donor["_id"]},
            {"$set": {
                "live_lat": lat,
                "live_lng": lng,
                "distance_km": route['distance_km'],
                "eta_minutes": int(adjusted_duration),
                "eta_source": route.get("source", "unknown"),
                "eta_updated_at": datetime.utcnow(),
                "weather_condition": weather_data['weather']['condition'] if weather_data['weather'] else None,
                "route_info": route,
                "location_shared_at": datetime.utcnow()
            }}
        )
        
        # Send confirmation
        from utils.sms import send_sms, format_phone_number
        donor = await db.donors.find_one({"_id": ObjectId(matched_donor["donor_id"])})
        if donor:
            donor_phone = donor.get("location", {}).get("phone")
            if donor_phone:
                formatted_phone = format_phone_number(donor_phone)
                weather_text = f"\n🌤️ Weather: {weather_data['weather']['description']}" if weather_data['weather'] else ""
                message = f"""📍 Location received!

Estimated arrival: {int(adjusted_duration)} minutes
Distance: {route['distance_km']} km{weather_text}

Hospital will track your ETA. Drive safely! 🚗

- DonorPulse"""
                send_sms(formatted_phone, message)
        
        return {
            "message": "Location shared successfully",
            "distance_km": route['distance_km'],
            "eta_minutes": int(adjusted_duration),
            "eta_source": route.get("source", "unknown"),
            "weather": weather_data['weather']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-location/{donor_id}")
async def get_donor_location(
    donor_id: str,
    request_id: str = Query(..., description="Request ID"),
    db=Depends(get_db)
):
    """Get donor's location (live or profile as fallback)"""
    try:
        # Get matched donor record
        matched_donor = await db.matched_donors.find_one({
            "request_id": request_id,
            "donor_id": donor_id
        })
        
        # Get donor profile
        donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        # Use live location if available, otherwise use profile location
        live_lat = matched_donor.get("live_lat") if matched_donor else None
        live_lng = matched_donor.get("live_lng") if matched_donor else None
        eta_minutes = matched_donor.get("eta_minutes") if matched_donor else None
        distance_km = matched_donor.get("distance_km") if matched_donor else None
        
        # Fallback to profile location
        if not live_lat or not live_lng:
            profile_lat = donor.get("location", {}).get("lat")
            profile_lng = donor.get("location", {}).get("lng")
            
            if profile_lat and profile_lng:
                live_lat = profile_lat
                live_lng = profile_lng
                # Calculate ETA from profile location if not already calculated
                if not eta_minutes or not distance_km:
                    # Get hospital location
                    blood_request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
                    if blood_request:
                        hospital = await db.hospitals.find_one({"_id": ObjectId(blood_request["hospital_id"])})
                        if hospital:
                            hospital_lat = hospital.get("location", {}).get("lat")
                            hospital_lng = hospital.get("location", {}).get("lng")
                            
                            if hospital_lat and hospital_lng:
                                # Try road distance first
                                route = await calculate_road_distance(profile_lat, profile_lng, hospital_lat, hospital_lng)
                                if route:
                                    distance_km = route['distance_km']
                                    eta_minutes = route['duration_min']
                                else:
                                    # Fallback to straight line
                                    route = calculate_straight_distance(profile_lat, profile_lng, hospital_lat, hospital_lng)
                                    distance_km = route['distance_km']
                                    eta_minutes = route['duration_min']
                                
                                # Store in matched_donor for future use
                                if matched_donor:
                                    await db.matched_donors.update_one(
                                        {"_id": matched_donor["_id"]},
                                        {"$set": {
                                            "distance_km": distance_km,
                                            "eta_minutes": int(eta_minutes),
                                            "eta_source": "profile_location",
                                            "profile_lat": profile_lat,
                                            "profile_lng": profile_lng
                                        }}
                                    )
        
        return {
            "donor_name": donor.get("name"),
            "donor_id": donor_id,
            "live_lat": live_lat,
            "live_lng": live_lng,
            "distance_km": distance_km,
            "eta_minutes": int(eta_minutes) if eta_minutes else None,
            "eta_source": "live" if (matched_donor and matched_donor.get("live_lat")) else "profile",
            "has_live_location": bool(matched_donor and matched_donor.get("live_lat")),
            "weather_condition": matched_donor.get("weather_condition") if matched_donor else None,
            "location_shared_at": matched_donor.get("location_shared_at").isoformat() if matched_donor and matched_donor.get("location_shared_at") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting donor location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/{lat}/{lng}")
async def get_weather_at_location(
    lat: float,
    lng: float,
    db=Depends(get_db)
):
    """Get weather at donor location"""
    try:
        weather_data = await get_weather(lat, lng)
        return {
            "weather": weather_data['weather'],
            "factor": weather_data['factor']
        }
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/route/{donor_id}/{request_id}")
async def get_donor_route(
    donor_id: str,
    request_id: str,
    db=Depends(get_db)
):
    """Get real road route for donor"""
    try:
        # Get donor location
        donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        donor_lat = donor.get("location", {}).get("lat")
        donor_lng = donor.get("location", {}).get("lng")
        
        if not donor_lat or not donor_lng:
            # Try to get from matched donor
            matched = await db.matched_donors.find_one({"donor_id": donor_id, "request_id": request_id})
            if matched:
                donor_lat = matched.get("live_lat") or matched.get("profile_lat")
                donor_lng = matched.get("live_lng") or matched.get("profile_lng")
        
        # Get hospital location from request
        blood_request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
        if not blood_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(blood_request["hospital_id"])})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        hospital_lat = hospital.get("location", {}).get("lat")
        hospital_lng = hospital.get("location", {}).get("lng")
        
        if not donor_lat or not hospital_lat:
            raise HTTPException(status_code=400, detail="Missing location coordinates")
        
        # Get road route from OpenRouteService
        route = await calculate_road_distance(donor_lat, donor_lng, hospital_lat, hospital_lng)
        
        if not route:
            route = calculate_straight_distance(donor_lat, donor_lng, hospital_lat, hospital_lng)
        
        # Get weather
        weather = await get_weather(donor_lat, donor_lng)
        
        return {
            "distance_km": route['distance_km'],
            "eta_minutes": int(route['duration_min'] * weather['factor']),
            "original_eta_minutes": int(route['duration_min']),
            "weather": weather['weather'],
            "weather_factor": weather['factor'],
            "route_source": route.get("source", "openrouteservice")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-config")
async def test_config():
    """Test if APIs are configured correctly"""
    return {
        "ors_api_configured": bool(settings.ors_api_key),
        "weather_api_configured": bool(settings.weather_api_key),
        "message": "Map features ready for testing!"
    }