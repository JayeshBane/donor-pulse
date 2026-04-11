# backend\routers\admin.py
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.admin import AdminCreate, AdminLogin, AdminResponse, AdminRole
from models.hospital import HospitalResponse
from utils.auth import hash_password, verify_password, create_jwt_token
from middleware.auth import get_current_hospital
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Simple admin authentication (in production, use proper admin middleware)
async def verify_admin(token: str, db):
    """Verify if user is admin"""
    from utils.auth import decode_jwt_token
    try:
        payload = decode_jwt_token(token)
        # Check if this is an admin (you can have a separate admin collection)
        # For now, we'll use a simple check - first registered admin
        admin = await db.admins.find_one({"username": payload.get("sub")})
        if not admin:
            return None
        return admin
    except:
        return None

@router.post("/setup")
async def setup_first_admin(db=Depends(get_db)):
    """Setup first admin account (only if no admin exists)"""
    try:
        # Check if any admin exists
        admin_count = await db.admins.count_documents({})
        
        if admin_count > 0:
            raise HTTPException(status_code=400, detail="Admin already exists")
        
        # Create default admin
        admin_data = {
            "username": "admin",
            "email": "admin@donorpulse.com",
            "full_name": "Super Admin",
            "role": AdminRole.SUPER_ADMIN,
            "hashed_password": hash_password("Admin@123"),
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        result = await db.admins.insert_one(admin_data)
        
        return {
            "message": "Admin account created successfully",
            "username": "admin",
            "password": "Admin@123",
            "admin_id": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up admin: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup admin")

@router.post("/login")
async def admin_login(login: AdminLogin, db=Depends(get_db)):
    """Admin login"""
    try:
        admin = await db.admins.find_one({"username": login.username})
        
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not admin.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account disabled")
        
        if not verify_password(login.password, admin["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        await db.admins.update_one(
            {"_id": admin["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        token_data = {
            "sub": admin["username"],
            "admin_id": str(admin["_id"]),
            "role": admin["role"],
            "type": "admin"
        }
        token = create_jwt_token(token_data)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 8 * 3600,
            "admin": AdminResponse(
                id=str(admin["_id"]),
                username=admin["username"],
                email=admin["email"],
                full_name=admin["full_name"],
                role=admin["role"],
                is_active=admin["is_active"]
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/hospitals/pending")
async def get_pending_hospitals(db=Depends(get_db)):
    """Get all pending hospital verifications"""
    try:
        pending = await db.hospitals.find({"is_verified": False}).to_list(length=None)
        
        hospitals = []
        for hospital in pending:
            hospitals.append({
                "id": str(hospital["_id"]),
                "name": hospital["name"],
                "type": hospital["type"],
                "email": hospital["email"],
                "phone": hospital["phone"],
                "username": hospital["username"],
                "city": hospital["location"]["city"],
                "license_number": hospital["license_number"],
                "created_at": hospital["created_at"].isoformat() if hospital.get("created_at") else None
            })
        
        return {
            "total": len(hospitals),
            "hospitals": hospitals
        }
        
    except Exception as e:
        logger.error(f"Error getting pending hospitals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending hospitals")

@router.get("/hospitals/verified")
async def get_verified_hospitals(db=Depends(get_db)):
    """Get all verified hospitals"""
    try:
        verified = await db.hospitals.find({"is_verified": True}).to_list(length=None)
        
        hospitals = []
        for hospital in verified:
            hospitals.append({
                "id": str(hospital["_id"]),
                "name": hospital["name"],
                "type": hospital["type"],
                "email": hospital["email"],
                "phone": hospital["phone"],
                "username": hospital["username"],
                "city": hospital["location"]["city"],
                "is_active": hospital.get("is_active", True),
                "created_at": hospital["created_at"].isoformat() if hospital.get("created_at") else None
            })
        
        return {
            "total": len(hospitals),
            "hospitals": hospitals
        }
        
    except Exception as e:
        logger.error(f"Error getting verified hospitals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get verified hospitals")

@router.patch("/hospitals/{hospital_id}/verify")
async def verify_hospital(hospital_id: str, db=Depends(get_db)):
    """Verify a hospital"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        result = await db.hospitals.update_one(
            {"_id": ObjectId(hospital_id)},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        return {"message": "Hospital verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying hospital: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify hospital")

@router.patch("/hospitals/{hospital_id}/reject")
async def reject_hospital(hospital_id: str, reason: str = None, db=Depends(get_db)):
    """Reject a hospital registration"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        # Delete or mark as rejected
        result = await db.hospitals.delete_one({"_id": ObjectId(hospital_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        return {"message": "Hospital registration rejected and removed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting hospital: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject hospital")

@router.patch("/hospitals/{hospital_id}/toggle-active")
async def toggle_hospital_active(hospital_id: str, db=Depends(get_db)):
    """Toggle hospital active status"""
    try:
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        new_status = not hospital.get("is_active", True)
        
        await db.hospitals.update_one(
            {"_id": ObjectId(hospital_id)},
            {"$set": {"is_active": new_status}}
        )
        
        return {
            "message": f"Hospital {'activated' if new_status else 'deactivated'}",
            "is_active": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling hospital: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle hospital status")

@router.get("/stats")
async def get_admin_stats(db=Depends(get_db)):
    """Get overall statistics"""
    try:
        total_hospitals = await db.hospitals.count_documents({})
        pending_hospitals = await db.hospitals.count_documents({"is_verified": False})
        verified_hospitals = await db.hospitals.count_documents({"is_verified": True})
        total_donors = await db.donors.count_documents({})
        active_donors = await db.donors.count_documents({"is_active": True})
        
        return {
            "hospitals": {
                "total": total_hospitals,
                "pending": pending_hospitals,
                "verified": verified_hospitals
            },
            "donors": {
                "total": total_donors,
                "active": active_donors
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")