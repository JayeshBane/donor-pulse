from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.auth import decode_jwt_token
from database import get_db
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_hospital(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
):
    """Get current authenticated hospital from JWT token"""
    try:
        token = credentials.credentials
        payload = decode_jwt_token(token)
        hospital_id = payload.get("hospital_id")
        
        from bson import ObjectId
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hospital not found"
            )
        
        return {
            "id": str(hospital["_id"]),
            "username": hospital["username"],
            "is_verified": hospital.get("is_verified", False),
            "is_active": hospital.get("is_active", True)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

async def get_current_admin(
    current_hospital: dict = Depends(get_current_hospital)
):
    """Check if current hospital has admin privileges"""
    if not current_hospital.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_hospital