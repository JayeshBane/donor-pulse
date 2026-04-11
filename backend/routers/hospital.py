from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional, List
import bcrypt
from database import get_db
from models.hospital import HospitalCreate, HospitalLogin, HospitalResponse
from config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals"])

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_hospital(hospital: HospitalCreate, db=Depends(get_db)):
    """Register a new hospital"""
    try:
        phone = str(hospital.phone).strip()
        
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
        raise HTTPException(status_code=500, detail=str(e))

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
            "is_verified": hospital.get("is_verified", False)
        }
        token = create_jwt_token(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
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

@router.get("/", response_model=dict)
async def list_hospitals(
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db=Depends(get_db)
):
    """List hospitals with filters"""
    try:
        query = {}
        if city:
            query["location.city"] = city
        if is_verified is not None:
            query["is_verified"] = is_verified
        
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
    except Exception as e:
        logger.error(f"Error listing hospitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(hospital_id: str, db=Depends(get_db)):
    """Get hospital by ID"""
    from bson import ObjectId
    
    try:
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
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
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))