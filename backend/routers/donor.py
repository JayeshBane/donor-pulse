# backend\routers\donor.py
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from database import get_db
from models.donor import DonorCreate
from utils.sms import send_welcome_sms
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/donors", tags=["donors"])

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_donor(donor: DonorCreate, db=Depends(get_db)):
    """Register a new donor"""
    try:
        phone = str(donor.location.phone).strip()
        
        # Check for duplicate phone
        existing = await db.donors.find_one({"location.phone": phone})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Donor with phone number {phone} already exists"
            )
        
        # Check for duplicate email if provided
        if donor.location.email:
            email = donor.location.email.lower().strip()
            existing_email = await db.donors.find_one({"location.email": email})
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Donor with email {email} already exists"
                )
        
        # Validate age and weight
        if donor.age < 18 or donor.age > 65:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Age must be between 18 and 65"
            )
        
        if donor.medical.weight_kg < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be at least 50kg"
            )
        
        # Create donor document
        donor_dict = donor.dict()
        donor_dict["location"]["phone"] = phone
        if donor_dict["location"].get("email"):
            donor_dict["location"]["email"] = donor_dict["location"]["email"].lower().strip()
        
        donor_dict["created_at"] = datetime.utcnow()
        donor_dict["updated_at"] = datetime.utcnow()
        
        # Handle last_donation_date
        if donor_dict["medical"].get("last_donation_date"):
            if isinstance(donor_dict["medical"]["last_donation_date"], str):
                try:
                    donor_dict["medical"]["last_donation_date"] = datetime.fromisoformat(
                        donor_dict["medical"]["last_donation_date"].replace('Z', '+00:00')
                    )
                except:
                    donor_dict["medical"]["last_donation_date"] = None
        
        result = await db.donors.insert_one(donor_dict)
        
        logger.info(f"Donor registered successfully: {phone}")
        
        # Send welcome SMS
        try:
            send_welcome_sms(phone, donor.name)
        except Exception as sms_error:
            logger.error(f"Failed to send welcome SMS: {sms_error}")
        
        return {
            "message": "Donor registered successfully",
            "donor_id": str(result.inserted_id),
            "phone": phone
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering donor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register donor"
        )

@router.get("/by-phone/", response_model=dict)
async def get_donor_by_phone(
    phone: str = Query(..., description="Donor phone number"),
    db=Depends(get_db)
):
    """Get donor by phone number"""
    try:
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found"
            )
        
        donor["_id"] = str(donor["_id"])
        if donor.get("created_at"):
            donor["created_at"] = donor["created_at"].isoformat()
        if donor.get("updated_at"):
            donor["updated_at"] = donor["updated_at"].isoformat()
        if donor.get("medical") and donor["medical"].get("last_donation_date"):
            if isinstance(donor["medical"]["last_donation_date"], datetime):
                donor["medical"]["last_donation_date"] = donor["medical"]["last_donation_date"].isoformat()
        
        return donor
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting donor by phone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get donor"
        )

@router.get("/", response_model=dict)
async def list_donors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    blood_type: Optional[str] = None,
    city: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db=Depends(get_db)
):
    """List donors with pagination and filters"""
    try:
        query = {}
        if blood_type:
            query["medical.blood_type"] = blood_type
        if city:
            query["location.city"] = city
        if is_active is not None:
            query["is_active"] = is_active
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"location.phone": {"$regex": search, "$options": "i"}}
            ]
        
        total = await db.donors.count_documents(query)
        cursor = db.donors.find(query).skip(skip).limit(limit).sort("created_at", -1)
        donors = []
        async for donor in cursor:
            donor["_id"] = str(donor["_id"])
            if donor.get("created_at"):
                donor["created_at"] = donor["created_at"].isoformat()
            if donor.get("updated_at"):
                donor["updated_at"] = donor["updated_at"].isoformat()
            donors.append(donor)
        
        return {"total": total, "skip": skip, "limit": limit, "donors": donors}
        
    except Exception as e:
        logger.error(f"Error listing donors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{donor_id}", response_model=dict)
async def get_donor(donor_id: str, db=Depends(get_db)):
    """Get donor by ID"""
    try:
        if not ObjectId.is_valid(donor_id):
            raise HTTPException(status_code=400, detail="Invalid donor ID format")
        
        donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        donor["_id"] = str(donor["_id"])
        return donor
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting donor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/{donor_id}/toggle-active", response_model=dict)
async def toggle_donor_active(donor_id: str, db=Depends(get_db)):
    """Toggle donor active status"""
    try:
        if not ObjectId.is_valid(donor_id):
            raise HTTPException(status_code=400, detail="Invalid donor ID format")
        
        donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        new_status = not donor.get("is_active", True)
        await db.donors.update_one(
            {"_id": ObjectId(donor_id)},
            {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "message": f"Donor {'activated' if new_status else 'deactivated'} successfully",
            "is_active": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling donor: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")