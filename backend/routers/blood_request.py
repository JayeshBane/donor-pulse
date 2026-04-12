# backend\routers\blood_request.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from math import radians, sin, cos, sqrt, atan2
from database import get_db
from models.blood_request import (
    BloodRequestCreate, BloodRequestInDB, RequestStatus, UrgencyLevel,
    MatchedDonor, DonorResponse, DonorResponseStatus
)
from utils.blood_compatibility import get_compatible_donors_for_blood_type, SCORING_WEIGHTS
from middleware.auth import get_verified_hospital
from utils.sms import send_sms
import logging
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/requests", tags=["blood-requests"])

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km using Haversine formula"""
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert to float if they are strings
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (TypeError, ValueError) as e:
        print(f"Error converting coordinates: {e}")
        return 999999  # Return large distance if coordinates are invalid
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def calculate_donor_score(donor: dict, distance_km: float, response_time_bonus: int = 0) -> float:
    """Calculate matching score for a donor"""
    score = 0
    
    # Distance score (closer is better, max 100 points for <5km)
    distance_score = max(0, 100 - (distance_km * 2))
    score += distance_score * SCORING_WEIGHTS["distance"]
    
    # Reliability score (0-100)
    reliability = donor.get("reliability_score", 50)
    score += reliability * SCORING_WEIGHTS["reliability"]
    
    # Transport availability
    has_transport = donor.get("preferences", {}).get("transport_available", False)
    transport_score = 100 if has_transport else 0
    score += transport_score * SCORING_WEIGHTS["transport"]
    
    # Response time bonus (for frequent donors)
    response_bonus = min(50, response_time_bonus)
    score += response_bonus * SCORING_WEIGHTS["response_time"]
    
    # Donation frequency
    total_donations = donor.get("total_donations_completed", 0)
    frequency_score = min(100, total_donations * 10)
    score += frequency_score * SCORING_WEIGHTS["donation_frequency"]
    
    return round(score, 2)

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_blood_request(
    request: BloodRequestCreate,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Create a new blood request"""
    try:
        # Verify hospital matches
        if request.hospital_id != hospital["id"]:
            raise HTTPException(status_code=403, detail="Cannot create request for another hospital")
        
        # Set expiration based on urgency
        if request.urgency == UrgencyLevel.ROUTINE:
            expires_at = datetime.utcnow() + timedelta(days=7)
        elif request.urgency == UrgencyLevel.URGENT:
            expires_at = datetime.utcnow() + timedelta(hours=24)
        elif request.urgency == UrgencyLevel.CRITICAL:
            expires_at = datetime.utcnow() + timedelta(hours=6)
        else:  # SOS
            expires_at = datetime.utcnow() + timedelta(hours=2)
        
        request_dict = {
            "hospital_id": request.hospital_id,
            "hospital_name": hospital["name"],
            "blood_type": request.blood_type,
            "quantity_units": request.quantity_units,
            "urgency": request.urgency,
            "reason": request.reason,
            "patient_info": request.patient_info,
            "expires_at": expires_at,
            "status": RequestStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "donors_contacted": 0,
            "donors_accepted": 0,
            "donors_declined": 0,
            "donors_timeout": 0
        }
        
        result = await db.blood_requests.insert_one(request_dict)
        
        logger.info(f"Blood request created: {result.inserted_id} for hospital {hospital['id']}")
        
        # Start matching process asynchronously
        asyncio.create_task(match_donors_for_request(str(result.inserted_id), db))
        
        return {
            "message": "Blood request created successfully",
            "request_id": str(result.inserted_id),
            "expires_at": expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating blood request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create blood request")

async def match_donors_for_request(request_id: str, db):
    """Find matching donors for a blood request"""
    try:
        # Get request details
        request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            logger.error(f"Request {request_id} not found")
            return
        
        # Update status to matching
        await db.blood_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": RequestStatus.MATCHING, "updated_at": datetime.utcnow()}}
        )
        
        # Get hospital location
        hospital = await db.hospitals.find_one({"_id": ObjectId(request["hospital_id"])})
        if not hospital:
            logger.error(f"Hospital not found for request {request_id}")
            return
        
        hospital_lat = hospital["location"].get("lat")
        hospital_lng = hospital["location"].get("lng")
        
        if not hospital_lat or not hospital_lng:
            logger.error(f"Hospital {request['hospital_id']} missing location coordinates")
            return
        
        # Get compatible blood types
        compatible_blood_types = get_compatible_donors_for_blood_type(request["blood_type"])
        logger.info(f"Compatible blood types for {request['blood_type']}: {compatible_blood_types}")
        
        # Find eligible donors
        donor_query = {
            "medical.blood_type": {"$in": compatible_blood_types},
            "is_active": True,
            "is_paused": False
        }
        
        donors = await db.donors.find(donor_query).to_list(length=None)
        logger.info(f"Found {len(donors)} donors with compatible blood type")
        
        # Calculate distances and scores
        matched_donors = []
        for donor in donors:
            donor_lat = donor.get("location", {}).get("lat")
            donor_lng = donor.get("location", {}).get("lng")
            
            # Skip donors without location
            if not donor_lat or not donor_lng:
                logger.info(f"Donor {donor['name']} missing location coordinates - skipping")
                continue
            
            # Check cooldown (56 days)
            last_donation = donor.get("medical", {}).get("last_donation_date")
            if last_donation:
                if isinstance(last_donation, str):
                    last_donation = datetime.fromisoformat(last_donation)
                days_since = (datetime.utcnow() - last_donation).days
                if days_since < 56:
                    logger.info(f"Donor {donor['name']} on cooldown ({days_since} days) - skipping")
                    continue
            
            # Calculate distance
            distance = calculate_distance(donor_lat, donor_lng, hospital_lat, hospital_lng)
            logger.info(f"Donor {donor['name']} distance: {distance:.2f} km")
            
            # Apply radius based on urgency
            radius_limits = {
                "routine": 50,
                "urgent": 100,
                "critical": 200,
                "sos": 999999  # No limit for SOS
            }
            max_distance = radius_limits.get(request["urgency"], 50)
            
            if distance > max_distance:
                logger.info(f"Donor {donor['name']} too far ({distance:.0f} km > {max_distance} km) - skipping")
                continue
            
            # Calculate travel time (rough estimate: 2 min per km)
            travel_time = int(distance * 2)
            
            # Calculate score
            score = calculate_donor_score(donor, distance, 0)
            
            matched_donors.append({
                "donor_id": str(donor["_id"]),
                "donor_name": donor["name"],
                "donor_phone": donor["location"]["phone"],
                "donor_blood_type": donor["medical"]["blood_type"],
                "distance_km": round(distance, 2),
                "reliability_score": donor.get("reliability_score", 50),
                "travel_time_minutes": travel_time,
                "score": score
            })
        
        logger.info(f"Matched {len(matched_donors)} donors after filtering")
        
        # Sort by score (highest first)
        matched_donors.sort(key=lambda x: x["score"], reverse=True)
        
        # Determine how many donors to contact based on urgency
        contact_counts = {
            "routine": 10,
            "urgent": 20,
            "critical": 30,
            "sos": 50
        }
        contact_count = min(contact_counts.get(request["urgency"], 10), len(matched_donors))
        
        # Store matched donors in database
        inserted_count = 0
        for donor in matched_donors[:contact_count]:
            try:
                await db.matched_donors.insert_one({
                    "request_id": request_id,
                    "donor_id": donor["donor_id"],
                    "donor_name": donor["donor_name"],
                    "donor_phone": donor["donor_phone"],
                    "donor_blood_type": donor["donor_blood_type"],
                    "distance_km": donor["distance_km"],
                    "reliability_score": donor["reliability_score"],
                    "travel_time_minutes": donor["travel_time_minutes"],
                    "score": donor["score"],
                    "status": "pending",
                    "contacted_at": datetime.utcnow()
                })
                inserted_count += 1
                logger.info(f"Inserted donor {donor['donor_name']} for request {request_id}")
            except Exception as e:
                logger.error(f"Error inserting donor {donor['donor_name']}: {e}")
        
        logger.info(f"Inserted {inserted_count} matched donors for request {request_id}")
        
        # Update request with donor count
        await db.blood_requests.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$set": {
                    "status": RequestStatus.BROADCASTING,
                    "donors_contacted": inserted_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Send notifications
        if inserted_count > 0:
            await broadcast_request_to_donors(request_id, matched_donors[:contact_count], request, db)
        else:
            logger.warning(f"No donors to notify for request {request_id}")
            
    except Exception as e:
        logger.error(f"Error matching donors for request {request_id}: {e}")
        import traceback
        traceback.print_exc()


async def broadcast_request_to_donors(request_id: str, donors: list, request: dict, db):
    """Send notifications to matched donors"""
    from utils.sms import send_sms, format_phone_number
    
    sent_count = 0
    for donor in donors:
        try:
            # Create SMS/WhatsApp message
            urgency_emoji = {
                "routine": "🩸",
                "urgent": "⚠️",
                "critical": "🔴",
                "sos": "🚨"
            }.get(request["urgency"], "🩸")
            
            message = f"""{urgency_emoji} BLOOD REQUEST - {request['urgency'].upper()}

Hospital: {request['hospital_name']}
Blood Type: {request['blood_type']}
Distance: {donor['distance_km']:.1f} km
Est. Travel: {donor['travel_time_minutes']} min

Reply YES to help save a life!
Reply NO if unable.

- DonorPulse"""
            
            # Format the phone number properly
            donor_phone = donor["donor_phone"]
            formatted_phone = format_phone_number(donor_phone)
            
            logger.info(f"Sending to {donor['donor_name']} at {formatted_phone}")
            
            # Send via SMS/WhatsApp
            result = send_sms(formatted_phone, message)
            
            # Store notification record
            await db.donor_notifications.insert_one({
                "request_id": request_id,
                "donor_id": donor["donor_id"],
                "donor_phone": formatted_phone,
                "donor_name": donor["donor_name"],
                "message": message,
                "sent_at": datetime.utcnow(),
                "status": "sent" if result else "failed"
            })
            
            sent_count += 1
            logger.info(f"✅ Notification sent to {donor['donor_name']}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error sending notification to donor {donor['donor_name']}: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"Sent {sent_count} notifications for request {request_id}")
    return sent_count

@router.post("/{request_id}/respond")
async def respond_to_request(
    request_id: str,
    response: DonorResponse,
    db=Depends(get_db)
):
    """Donor responds to a blood request"""
    try:
        # Update matched donor record
        result = await db.matched_donors.update_one(
            {
                "request_id": request_id,
                "donor_id": response.donor_id
            },
            {
                "$set": {
                    "status": response.response,
                    "responded_at": datetime.utcnow(),
                    "eta_minutes": response.eta_minutes,
                    "notes": response.notes
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Donor not matched to this request")
        
        # Update request counts
        if response.response == DonorResponseStatus.ACCEPTED:
            await db.blood_requests.update_one(
                {"_id": ObjectId(request_id)},
                {"$inc": {"donors_accepted": 1}}
            )
        elif response.response == DonorResponseStatus.DECLINED:
            await db.blood_requests.update_one(
                {"_id": ObjectId(request_id)},
                {"$inc": {"donors_declined": 1}}
            )
        
        # Check if request is fulfilled
        request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
        if request and request["donors_accepted"] >= request["quantity_units"]:
            await db.blood_requests.update_one(
                {"_id": ObjectId(request_id)},
                {
                    "$set": {
                        "status": RequestStatus.FULFILLED,
                        "fulfilled_at": datetime.utcnow()
                    }
                }
            )
            
            # Notify hospital
            hospital = await db.hospitals.find_one({"_id": ObjectId(request["hospital_id"])})
            if hospital:
                send_sms(
                    hospital["phone"],
                    f"✅ Blood request fulfilled! {request['donors_accepted']} donors confirmed."
                )
        
        return {"message": f"Response recorded: {response.response}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing donor response: {e}")
        raise HTTPException(status_code=500, detail="Failed to process response")

@router.get("/hospital/{hospital_id}")
async def get_hospital_requests(
    hospital_id: str,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Get blood requests for a hospital"""
    try:
        if hospital["id"] != hospital_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = {"hospital_id": hospital_id}
        if status:
            query["status"] = status
        
        requests = await db.blood_requests.find(query).sort("created_at", -1).limit(limit).to_list(length=None)
        
        result = []
        for req in requests:
            result.append({
                "id": str(req["_id"]),
                "blood_type": req["blood_type"],
                "quantity_units": req["quantity_units"],
                "urgency": req["urgency"],
                "status": req["status"],
                "created_at": req["created_at"].isoformat(),
                "expires_at": req["expires_at"].isoformat(),
                "donors_contacted": req.get("donors_contacted", 0),
                "donors_accepted": req.get("donors_accepted", 0)
            })
        
        return {
            "total": len(result),
            "requests": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hospital requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to get requests")

@router.get("/{request_id}")
async def get_request_details(
    request_id: str,
    db=Depends(get_db)
):
    """Get detailed information about a blood request"""
    try:
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        
        request = await db.blood_requests.find_one({"_id": ObjectId(request_id)})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Get matched donors
        matched_donors = await db.matched_donors.find(
            {"request_id": request_id}
        ).sort("score", -1).to_list(length=None)
        
        return {
            "id": str(request["_id"]),
            "hospital_id": request["hospital_id"],
            "hospital_name": request["hospital_name"],
            "blood_type": request["blood_type"],
            "quantity_units": request["quantity_units"],
            "urgency": request["urgency"],
            "reason": request.get("reason"),
            "status": request["status"],
            "created_at": request["created_at"].isoformat(),
            "expires_at": request["expires_at"].isoformat(),
            "statistics": {
                "donors_contacted": request.get("donors_contacted", 0),
                "donors_accepted": request.get("donors_accepted", 0),
                "donors_declined": request.get("donors_declined", 0),
                "donors_timeout": request.get("donors_timeout", 0)
            },
            "matched_donors": [
                {
                    "donor_name": d["donor_name"],
                    "donor_blood_type": d["donor_blood_type"],
                    "distance_km": d["distance_km"],
                    "status": d["status"],
                    "eta_minutes": d.get("eta_minutes")
                }
                for d in matched_donors[:10]
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get request details")

@router.patch("/{request_id}/cancel")
async def cancel_request(
    request_id: str,
    reason: Optional[str] = None,
    hospital: dict = Depends(get_verified_hospital),
    db=Depends(get_db)
):
    """Cancel a blood request"""
    try:
        if not ObjectId.is_valid(request_id):
            raise HTTPException(status_code=400, detail="Invalid request ID")
        
        request = await db.blood_requests.find_one({
            "_id": ObjectId(request_id),
            "hospital_id": hospital["id"]
        })
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request["status"] in [RequestStatus.FULFILLED, RequestStatus.CANCELLED, RequestStatus.EXPIRED]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel request with status: {request['status']}")
        
        await db.blood_requests.update_one(
            {"_id": ObjectId(request_id)},
            {
                "$set": {
                    "status": RequestStatus.CANCELLED,
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Request {request_id} cancelled by hospital {hospital['id']}")
        
        return {"message": "Request cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel request")

@router.get("/donor/{donor_id}/nearby")
async def get_nearby_requests(
    donor_id: str,
    lat: float = Query(..., description="Donor latitude"),
    lng: float = Query(..., description="Donor longitude"),
    db=Depends(get_db)
):
    """Get active blood requests near a donor"""
    try:
        # Get donor to verify blood type
        donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        donor_blood_type = donor["medical"]["blood_type"]
        
        # Get active requests
        active_requests = await db.blood_requests.find({
            "status": {"$in": [RequestStatus.PENDING, RequestStatus.MATCHING, RequestStatus.BROADCASTING]},
            "expires_at": {"$gt": datetime.utcnow()}
        }).to_list(length=None)
        
        nearby_requests = []
        for req in active_requests:
            # Check blood type compatibility
            compatible_blood_types = get_compatible_donors_for_blood_type(req["blood_type"])
            if donor_blood_type not in compatible_blood_types:
                continue
            
            # Get hospital location
            hospital = await db.hospitals.find_one({"_id": ObjectId(req["hospital_id"])})
            if hospital and hospital["location"].get("lat"):
                distance = calculate_distance(
                    lat, lng,
                    hospital["location"]["lat"],
                    hospital["location"]["lng"]
                )
                
                # Apply radius filter based on urgency
                max_distance = {
                    "routine": 50,
                    "urgent": 100,
                    "critical": 200,
                    "sos": 500
                }.get(req["urgency"], 50)
                
                if distance <= max_distance:
                    nearby_requests.append({
                        "id": str(req["_id"]),
                        "hospital_name": req["hospital_name"],
                        "blood_type": req["blood_type"],
                        "urgency": req["urgency"],
                        "distance_km": round(distance, 2),
                        "created_at": req["created_at"].isoformat()
                    })
        
        # Sort by urgency and distance
        urgency_order = {"sos": 0, "critical": 1, "urgent": 2, "routine": 3}
        nearby_requests.sort(key=lambda x: (urgency_order[x["urgency"]], x["distance_km"]))
        
        return {
            "total": len(nearby_requests),
            "requests": nearby_requests[:20]
        }
        
    except Exception as e:
        logger.error(f"Error getting nearby requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nearby requests")