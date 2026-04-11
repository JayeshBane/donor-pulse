from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from database import get_db
from models.hospital import HospitalLogin, HospitalResponse
from models.token import TokenType
from utils.auth import verify_password, create_jwt_token, generate_magic_token, hash_password
from middleware.auth import get_current_hospital
import logging
import secrets
import string
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
            "expires_in": 8 * 3600,
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/donor/generate-magic-link")
async def generate_donor_magic_link(phone: str, db=Depends(get_db)):
    """Generate a magic link for donor profile update"""
    try:
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        # Rate limiting
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        rate_limit = await db.rate_limits.find_one({
            "donor_phone": phone,
            "last_update_date": {"$gte": today}
        })
        
        if rate_limit and rate_limit.get("update_count", 0) >= 3:
            raise HTTPException(status_code=429, detail="Maximum 3 update requests per day")
        
        # Generate token
        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        expires_at = datetime.utcnow() + timedelta(minutes=30)
        
        await db.update_tokens.insert_one({
            "token": token,
            "donor_id": str(donor["_id"]),
            "token_type": "magic_link",
            "expires_at": expires_at,
            "is_used": False,
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
        
        magic_link = f"http://localhost:3000/donor/update/{token}"
        logger.info(f"Magic link generated for {phone}")
        
        return {
            "message": "Magic link generated successfully",
            "magic_link": magic_link,
            "expires_in": 30
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating magic link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/donor/verify-magic-link/{token}")
async def verify_magic_link(token: str, db=Depends(get_db)):
    """Verify magic link token and return donor data"""
    try:
        token_doc = await db.update_tokens.find_one({"token": token, "token_type": "magic_link"})
        
        if not token_doc:
            raise HTTPException(status_code=404, detail="Invalid or expired magic link")
        
        if token_doc.get("is_used", False):
            raise HTTPException(status_code=400, detail="Magic link already used")
        
        if token_doc["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Magic link expired")
        
        donor = await db.donors.find_one({"_id": ObjectId(token_doc["donor_id"])})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        await db.update_tokens.update_one(
            {"_id": token_doc["_id"]},
            {"$set": {"is_used": True}}
        )
        
        donor["_id"] = str(donor["_id"])
        
        return {
            "message": "Magic link verified successfully",
            "donor": donor,
            "can_edit_fields": [
                "preferences.availability", "preferences.notify_types",
                "preferences.transport_available", "location.address",
                "location.city", "location.pin_code", "medical.last_donation_date",
                "medical.medications"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying magic link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/donor/update/{token}")
async def update_donor_via_magic_link(token: str, update_data: dict, db=Depends(get_db)):
    """Update donor profile using magic link"""
    try:
        token_doc = await db.update_tokens.find_one({"token": token, "token_type": "magic_link"})
        
        if not token_doc or token_doc.get("is_used", False) or token_doc["expires_at"] < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired magic link")
        
        allowed_fields = [
            "preferences.availability", "preferences.notify_types",
            "preferences.transport_available", "location.address",
            "location.city", "location.pin_code", "medical.last_donation_date",
            "medical.medications"
        ]
        
        update_query = {}
        for field, value in update_data.items():
            if field in allowed_fields:
                update_query[field] = value
        
        if not update_query:
            raise HTTPException(status_code=400, detail="No editable fields provided")
        
        update_query["updated_at"] = datetime.utcnow()
        
        await db.donors.update_one(
            {"_id": ObjectId(token_doc["donor_id"])},
            {"$set": update_query}
        )
        
        await db.update_tokens.update_one(
            {"_id": token_doc["_id"]},
            {"$set": {"is_used": True}}
        )
        
        return {"message": "Donor profile updated successfully", "updated_fields": list(update_query.keys())}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating donor: {e}")
        raise HTTPException(status_code=500, detail=str(e))