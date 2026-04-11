# backend\routers\hospital.py
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from typing import Optional
from database import get_db
from models.hospital import HospitalCreate, HospitalLogin, HospitalResponse
from utils.auth import hash_password, verify_password, create_jwt_token
from middleware.auth import get_admin_hospital, get_current_hospital
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_hospital(hospital: HospitalCreate, db=Depends(get_db)):
    """Register a new hospital"""
    try:
        phone = str(hospital.phone).strip()
        
        # Check for existing records
        existing = await db.hospitals.find_one({"username": hospital.username})
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        email = hospital.email.lower().strip()
        existing_email = await db.hospitals.find_one({"email": email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_phone = await db.hospitals.find_one({"phone": phone})
        if existing_phone:
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Validate license number uniqueness
        existing_license = await db.hospitals.find_one({"license_number": hospital.license_number})
        if existing_license:
            raise HTTPException(status_code=400, detail="License number already registered")
        
        hashed_pwd = hash_password(hospital.password)
        
        hospital_dict = {
            "name": hospital.name,
            "type": hospital.type,
            "license_number": hospital.license_number,
            "email": email,
            "phone": phone,
            "username": hospital.username,
            "hashed_password": hashed_pwd,
            "location": hospital.location.dict(),
            "operational": hospital.operational.dict() if hospital.operational else {},
            "is_verified": False,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.hospitals.insert_one(hospital_dict)
        logger.info(f"Hospital registered: {hospital.username}")
        
        return {
            "message": "Hospital registered successfully. Awaiting admin verification.",
            "hospital_id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering hospital: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login_hospital(login: HospitalLogin, db=Depends(get_db)):
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

@router.get("/", response_model=dict)
async def list_hospitals(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db=Depends(get_db)
):
    """List hospitals with filters (public endpoint)"""
    try:
        # Validate pagination
        if skip < 0:
            raise HTTPException(status_code=400, detail="Skip must be >= 0")
        if limit < 1 or limit > 200:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 200")
        
        query = {}
        if city:
            query["location.city"] = city
        if is_verified is not None:
            query["is_verified"] = is_verified
        
        query["is_active"] = True  # Only show active hospitals to public
        
        total = await db.hospitals.count_documents(query)
        cursor = db.hospitals.find(query).skip(skip).limit(limit)
        hospitals = []
        async for hospital in cursor:
            hospitals.append(HospitalResponse(
                id=str(hospital["_id"]),
                name=hospital["name"],
                type=hospital["type"],
                email=hospital["email"],
                phone=hospital["phone"],
                username=hospital["username"],
                city=hospital["location"]["city"],
                is_verified=hospital.get("is_verified", False),
                is_active=hospital.get("is_active", True)
            ))
        
        return {"total": total, "skip": skip, "limit": limit, "hospitals": hospitals}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing hospitals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str, db=Depends(get_db)):
    """Get hospital by ID (public endpoint)"""
    from bson import ObjectId
    
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID format")
        
        hospital = await db.hospitals.find_one(
            {"_id": ObjectId(hospital_id), "is_active": True}
        )
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        return HospitalResponse(
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hospital: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")