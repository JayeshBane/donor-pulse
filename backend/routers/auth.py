from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from database import get_db
from models.hospital import HospitalLogin, HospitalResponse
from utils.auth import verify_password, create_jwt_token, generate_magic_token, hash_token
from config import settings
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/hospital/login")
async def hospital_login(login: HospitalLogin, db=Depends(get_db)):
    """Login hospital and return JWT token"""
    try:
        hospital = await db.hospitals.find_one({"username": login.username})
        
        if not hospital:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not hospital.get("is_active", True):
            raise HTTPException(status_code=401, detail="Hospital account is deactivated")
        
        if not verify_password(login.password, hospital["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        token_data = {
            "sub": hospital["username"],
            "hospital_id": str(hospital["_id"]),
            "is_verified": hospital.get("is_verified", False),
            "type": "hospital"
        }
        token = create_jwt_token(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expiry_hours * 3600,
            "hospital": HospitalResponse(
                id=str(hospital["_id"]),
                name=hospital["name"],
                type=hospital["type"],
                email=hospital["email"],
                phone=hospital["phone"],
                username=hospital["username"],
                city=hospital["location"]["city"],
                is_verified=hospital.get("is_verified", False),
                is_active=hospital.get("is_active", True)
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/donor/generate-magic-link")
async def generate_donor_magic_link(phone: str, db=Depends(get_db)):
    """Generate a magic link for donor profile update"""
    try:
        logger.info(f"Generating magic link for phone: {phone}")
        
        # Find donor by phone
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        logger.info(f"Found donor: {donor['_id']}")
        
        # Rate limiting - check daily limit
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        rate_limit = await db.rate_limits.find_one({
            "donor_phone": phone,
            "last_update_date": {"$gte": today}
        })
        
        if rate_limit and rate_limit.get("update_count", 0) >= 3:
            raise HTTPException(status_code=429, detail="Maximum 3 update requests per day")
        
        # Generate token and hash it
        token = generate_magic_token()
        hashed_token = hash_token(token)
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        # Store hashed token (don't delete until update)
        await db.update_tokens.insert_one({
            "hashed_token": hashed_token,
            "donor_id": str(donor["_id"]),
            "token_type": "magic_link",
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        })
        
        # Update rate limit
        if rate_limit:
            await db.rate_limits.update_one(
                {"donor_phone": phone, "last_update_date": {"$gte": today}},
                {"$inc": {"update_count": 1}}
            )
        else:
            await db.rate_limits.insert_one({
                "donor_phone": phone,
                "update_count": 1,
                "last_update_date": today
            })
        
        # Create magic link
        magic_link = f"{settings.frontend_url}/donor/update/{token}"
        
        # In development, return the link directly
        if settings.environment == "development":
            return {
                "message": "Magic link generated successfully",
                "magic_link": magic_link,
                "expires_in": 30
            }
        else:
            # In production, send via SMS
            from utils.sms import send_sms
            send_sms(phone, f"Your DonorPulse update link: {magic_link}")
            return {
                "message": "Magic link sent to your phone",
                "expires_in": 30
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating magic link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate magic link")

@router.post("/donor/verify-magic-link/{token}")
async def verify_magic_link(token: str, db=Depends(get_db)):
    """Verify magic link token and return donor data (does NOT delete token)"""
    try:
        logger.info(f"Verifying magic link token: {token[:10]}...")
        
        # Hash the token
        hashed_token = hash_token(token)
        
        # Find token (don't delete yet)
        token_doc = await db.update_tokens.find_one({
            "hashed_token": hashed_token,
            "token_type": "magic_link",
            "expires_at": {"$gt": datetime.utcnow()}  # Not expired
        })
        
        if not token_doc:
            # Check if token exists but expired
            expired_token = await db.update_tokens.find_one({
                "hashed_token": hashed_token,
                "token_type": "magic_link",
                "expires_at": {"$lte": datetime.utcnow()}
            })
            if expired_token:
                # Delete expired token
                await db.update_tokens.delete_one({"_id": expired_token["_id"]})
                raise HTTPException(status_code=400, detail="Magic link expired")
            else:
                raise HTTPException(status_code=404, detail="Invalid magic link")
        
        logger.info(f"Found valid token for donor: {token_doc['donor_id']}")
        
        # Get donor data
        donor = await db.donors.find_one({"_id": ObjectId(token_doc["donor_id"])})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        # Convert ObjectId to string for JSON response
        donor["_id"] = str(donor["_id"])
        
        return {
            "message": "Magic link verified successfully",
            "donor": donor,
            "can_edit_fields": [
                "preferences.availability",
                "preferences.notify_types",
                "preferences.transport_available",
                "location.address",
                "location.city",
                "location.pin_code",
                "medical.last_donation_date",
                "medical.medications"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying magic link: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify magic link")

@router.put("/donor/update/{token}")
async def update_donor_via_magic_link(token: str, update_data: dict, db=Depends(get_db)):
    """Update donor profile using magic link (DELETE token AFTER successful update)"""
    try:
        logger.info(f"Updating donor via magic link: {token[:10]}...")
        logger.info(f"Received update data: {update_data}")
        
        # Hash the token
        hashed_token = hash_token(token)
        
        # Find and DELETE the token in one atomic operation (only on update)
        token_doc = await db.update_tokens.find_one_and_delete({
            "hashed_token": hashed_token,
            "token_type": "magic_link",
            "expires_at": {"$gt": datetime.utcnow()}  # Only if not expired
        })
        
        if not token_doc:
            # Check if token exists but expired
            expired_token = await db.update_tokens.find_one({
                "hashed_token": hashed_token,
                "token_type": "magic_link",
                "expires_at": {"$lte": datetime.utcnow()}
            })
            if expired_token:
                await db.update_tokens.delete_one({"_id": expired_token["_id"]})
                raise HTTPException(status_code=400, detail="Magic link expired")
            else:
                raise HTTPException(status_code=404, detail="Invalid magic link")
        
        logger.info(f"Found and deleted token for donor: {token_doc['donor_id']}")
        
        # Build update query by flattening nested objects
        update_query = {}
        
        # Handle preferences
        if "preferences" in update_data:
            prefs = update_data["preferences"]
            if "availability" in prefs and prefs["availability"]:
                update_query["preferences.availability"] = prefs["availability"]
            if "notify_types" in prefs and prefs["notify_types"]:
                update_query["preferences.notify_types"] = prefs["notify_types"]
            if "transport_available" in prefs:
                update_query["preferences.transport_available"] = prefs["transport_available"]
        
        # Handle location
        if "location" in update_data:
            loc = update_data["location"]
            if "address" in loc and loc["address"]:
                update_query["location.address"] = loc["address"]
            if "city" in loc and loc["city"]:
                update_query["location.city"] = loc["city"]
            if "pin_code" in loc and loc["pin_code"]:
                update_query["location.pin_code"] = loc["pin_code"]
        
        # Handle medical
        if "medical" in update_data:
            med = update_data["medical"]
            if "last_donation_date" in med and med["last_donation_date"]:
                update_query["medical.last_donation_date"] = med["last_donation_date"]
            if "medications" in med:
                medications = med["medications"]
                if isinstance(medications, str):
                    medications = [m.strip() for m in medications.split(',') if m.strip()]
                elif not isinstance(medications, list):
                    medications = []
                update_query["medical.medications"] = medications
        
        # Also handle direct field updates (for backward compatibility)
        allowed_fields = [
            "preferences.availability",
            "preferences.notify_types",
            "preferences.transport_available",
            "location.address",
            "location.city",
            "location.pin_code",
            "medical.last_donation_date",
            "medical.medications"
        ]
        
        for field in allowed_fields:
            if field in update_data:
                value = update_data[field]
                if value is not None and value != "":
                    if field == "medical.medications" and isinstance(value, str):
                        value = [m.strip() for m in value.split(',') if m.strip()]
                    update_query[field] = value
        
        if not update_query:
            logger.warning(f"No valid fields to update. Received data: {update_data}")
            raise HTTPException(status_code=400, detail="No editable fields provided. Please provide valid fields like preferences, location, or medical data.")
        
        logger.info(f"Update query: {update_query}")
        
        update_query["updated_at"] = datetime.utcnow()
        
        # Update donor
        result = await db.donors.update_one(
            {"_id": ObjectId(token_doc["donor_id"])},
            {"$set": update_query}
        )
        
        if result.modified_count == 0:
            logger.warning(f"No changes made for donor: {token_doc['donor_id']}")
            return {
                "message": "No changes were made to the profile",
                "updated_fields": []
            }
        
        logger.info(f"Successfully updated donor: {token_doc['donor_id']}")
        
        return {
            "message": "Donor profile updated successfully",
            "updated_fields": list(update_query.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating donor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update donor: {str(e)}")