from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends, Request
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.admin import AdminCreate, AdminLogin, AdminResponse, AdminRole
from models.hospital import HospitalResponse
from utils.auth import hash_password, verify_password, create_jwt_token, decode_jwt_token
from middleware.auth import get_current_hospital
import logging
from utils.sms import send_sms
from models.donor import DonorInDB
from models.hospital import HospitalInDB
from pydantic import BaseModel

class BroadcastRequest(BaseModel):
    message: str

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Audit log helper function
async def log_admin_action(db, admin_id: str, admin_name: str, action: str, details: dict, ip: str = None):
    """Log admin action for audit trail"""
    await db.audit_logs.insert_one({
        "admin_id": admin_id,
        "admin_name": admin_name,
        "action": action,
        "details": details,
        "ip_address": ip,
        "timestamp": datetime.utcnow()
    })

# Get current admin from token
async def get_current_admin(request: Request, db):
    """Get current admin from JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        token = auth_header.replace("Bearer ", "")
        payload = decode_jwt_token(token)
        
        if payload.get("type") != "admin":
            return None
        
        admin = await db.admins.find_one({"username": payload.get("sub")})
        return admin
    except:
        return None

# Simple admin authentication (in production, use proper admin middleware)
async def verify_admin(token: str, db):
    """Verify if user is admin"""
    try:
        payload = decode_jwt_token(token)
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
async def verify_hospital(
    hospital_id: str, 
    request: Request,
    db=Depends(get_db)
):
    """Verify a hospital with audit log"""
    try:
        # Get admin info
        admin = await get_current_admin(request, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin authentication required")
        
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        old_status = hospital.get("is_verified", False)
        
        result = await db.hospitals.update_one(
            {"_id": ObjectId(hospital_id)},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Log the action
        await log_admin_action(
            db, 
            str(admin["_id"]), 
            admin.get("username", "admin"),
            "VERIFY_HOSPITAL", 
            {
                "hospital_id": hospital_id,
                "hospital_name": hospital.get("name"),
                "hospital_email": hospital.get("email"),
                "old_status": old_status,
                "new_status": True
            },
            request.client.host
        )
        
        return {"message": "Hospital verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying hospital: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify hospital")

@router.patch("/hospitals/{hospital_id}/reject")
async def reject_hospital(
    hospital_id: str, 
    reason: str = None,
    request: Request = None,
    db=Depends(get_db)
):
    """Reject a hospital registration with audit log"""
    try:
        # Get admin info
        admin = await get_current_admin(request, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin authentication required")
        
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Log the action before deleting
        await log_admin_action(
            db, 
            str(admin["_id"]), 
            admin.get("username", "admin"),
            "REJECT_HOSPITAL", 
            {
                "hospital_id": hospital_id,
                "hospital_name": hospital.get("name"),
                "hospital_email": hospital.get("email"),
                "reason": reason
            },
            request.client.host
        )
        
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
async def toggle_hospital_active(
    hospital_id: str,
    request: Request,
    db=Depends(get_db)
):
    """Toggle hospital active status with audit log"""
    try:
        # Get admin info
        admin = await get_current_admin(request, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin authentication required")
        
        if not ObjectId.is_valid(hospital_id):
            raise HTTPException(status_code=400, detail="Invalid hospital ID")
        
        hospital = await db.hospitals.find_one({"_id": ObjectId(hospital_id)})
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        old_status = hospital.get("is_active", True)
        new_status = not old_status
        
        await db.hospitals.update_one(
            {"_id": ObjectId(hospital_id)},
            {"$set": {"is_active": new_status}}
        )
        
        # Log the action
        await log_admin_action(
            db, 
            str(admin["_id"]), 
            admin.get("username", "admin"),
            "TOGGLE_HOSPITAL_STATUS", 
            {
                "hospital_id": hospital_id,
                "hospital_name": hospital.get("name"),
                "old_status": old_status,
                "new_status": new_status
            },
            request.client.host
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

@router.post("/broadcast/donors")
async def broadcast_to_donors(
    broadcast: BroadcastRequest,
    request: Request,
    db=Depends(get_db)
):
    """Send broadcast message to all donors with audit log"""
    try:
        # Get admin info
        admin = await get_current_admin(request, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin authentication required")
        
        message = broadcast.message
        # Get all active donors
        donors = await db.donors.find({"is_active": True}).to_list(length=None)
        
        sent_count = 0
        failed_count = 0
        failed_phones = []
        
        for donor in donors:
            try:
                phone = donor.get("location", {}).get("phone")
                if phone:
                    broadcast_message = f"""📢 DonorPulse Broadcast

{message}

Thank you for being a life saver! 🩸

- DonorPulse Team"""
                    
                    result = send_sms(phone, broadcast_message)
                    if result:
                        sent_count += 1
                    else:
                        failed_count += 1
                        failed_phones.append(phone)
            except Exception as e:
                logger.error(f"Failed to send broadcast to donor {donor.get('_id')}: {e}")
                failed_count += 1
        
        # Log the broadcast
        await db.broadcast_logs.insert_one({
            "type": "donors",
            "message": message,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "failed_phones": failed_phones[:10],  # Store first 10 failures
            "sent_at": datetime.utcnow(),
            "sent_by": admin.get("username", "admin"),
            "admin_id": str(admin["_id"])
        })
        
        # Audit log for broadcast
        await log_admin_action(
            db, 
            str(admin["_id"]), 
            admin.get("username", "admin"),
            "BROADCAST_DONORS", 
            {
                "message_preview": message[:100],
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_donors": len(donors)
            },
            request.client.host
        )
        
        return {
            "message": f"Broadcast sent to {sent_count} donors",
            "sent": sent_count,
            "failed": failed_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting to donors: {e}")
        raise HTTPException(status_code=500, detail="Failed to send broadcast")

@router.post("/broadcast/hospitals")
async def broadcast_to_hospitals(
    broadcast: BroadcastRequest,
    request: Request,
    db=Depends(get_db)
):
    """Send broadcast message to all hospitals with audit log"""
    try:
        # Get admin info
        admin = await get_current_admin(request, db)
        if not admin:
            raise HTTPException(status_code=401, detail="Admin authentication required")
        
        message = broadcast.message
        # Get all active hospitals
        hospitals = await db.hospitals.find({"is_active": True}).to_list(length=None)
        
        sent_count = 0
        failed_count = 0
        failed_phones = []
        
        for hospital in hospitals:
            try:
                phone = hospital.get("phone")
                if phone:
                    broadcast_message = f"""📢 DonorPulse Broadcast - Hospital Update

{message}

For assistance, contact DonorPulse support.

- DonorPulse Team"""
                    
                    result = send_sms(phone, broadcast_message)
                    if result:
                        sent_count += 1
                    else:
                        failed_count += 1
                        failed_phones.append(phone)
            except Exception as e:
                logger.error(f"Failed to send broadcast to hospital {hospital.get('_id')}: {e}")
                failed_count += 1
        
        # Log the broadcast
        await db.broadcast_logs.insert_one({
            "type": "hospitals",
            "message": message,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "failed_phones": failed_phones[:10],
            "sent_at": datetime.utcnow(),
            "sent_by": admin.get("username", "admin"),
            "admin_id": str(admin["_id"])
        })
        
        # Audit log for broadcast
        await log_admin_action(
            db, 
            str(admin["_id"]), 
            admin.get("username", "admin"),
            "BROADCAST_HOSPITALS", 
            {
                "message_preview": message[:100],
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_hospitals": len(hospitals)
            },
            request.client.host
        )
        
        return {
            "message": f"Broadcast sent to {sent_count} hospitals",
            "sent": sent_count,
            "failed": failed_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error broadcasting to hospitals: {e}")
        raise HTTPException(status_code=500, detail="Failed to send broadcast")

@router.get("/broadcast/logs")
async def get_broadcast_logs(
    limit: int = Query(50, ge=1, le=200),
    db=Depends(get_db)
):
    """Get broadcast history"""
    try:
        logs = await db.broadcast_logs.find().sort("sent_at", -1).limit(limit).to_list(length=None)
        
        result = []
        for log in logs:
            result.append({
                "id": str(log["_id"]),
                "type": log["type"],
                "message": log["message"][:100] + "..." if len(log["message"]) > 100 else log["message"],
                "sent_count": log["sent_count"],
                "failed_count": log["failed_count"],
                "sent_at": log["sent_at"].isoformat(),
                "sent_by": log.get("sent_by", "admin")
            })
        
        return {
            "total": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting broadcast logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get broadcast logs")

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    db=Depends(get_db)
):
    """Get audit logs for admin actions"""
    try:
        query = {}
        if action:
            query["action"] = action
        
        logs = await db.audit_logs.find(query).sort("timestamp", -1).limit(limit).to_list(length=None)
        
        result = []
        for log in logs:
            result.append({
                "id": str(log["_id"]),
                "admin_name": log.get("admin_name", "Unknown"),
                "admin_id": log["admin_id"],
                "action": log["action"],
                "details": log["details"],
                "ip_address": log.get("ip_address"),
                "timestamp": log["timestamp"].isoformat()
            })
        
        return {
            "total": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@router.get("/logs/audit")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    db=Depends(get_db)
):
    """Get audit logs for admin actions"""
    try:
        query = {}
        if action:
            query["action"] = action
        
        logs = await db.audit_logs.find(query).sort("timestamp", -1).limit(limit).to_list(length=None)
        
        result = []
        for log in logs:
            result.append({
                "id": str(log["_id"]),
                "admin_name": log.get("admin_name", "Unknown"),
                "admin_id": log["admin_id"],
                "action": log["action"],
                "details": log["details"],
                "ip_address": log.get("ip_address"),
                "timestamp": log["timestamp"].isoformat()
            })
        
        return {
            "total": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit logs")

@router.get("/logs/hospitals")
async def get_hospital_logs(
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db)
):
    """Get hospital registration and activity logs"""
    try:
        # Get hospital registration logs
        hospitals = await db.hospitals.find().sort("created_at", -1).limit(limit).to_list(length=None)
        
        result = []
        for hospital in hospitals:
            result.append({
                "type": "hospital",
                "id": str(hospital["_id"]),
                "name": hospital["name"],
                "action": "registered",
                "details": {
                    "email": hospital.get("email"),
                    "phone": hospital.get("phone"),
                    "city": hospital.get("location", {}).get("city"),
                    "type": hospital.get("type")
                },
                "timestamp": hospital.get("created_at").isoformat() if hospital.get("created_at") else None,
                "status": "verified" if hospital.get("is_verified") else "pending"
            })
        
        return {
            "total": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting hospital logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get hospital logs")

@router.get("/logs/donors")
async def get_donor_logs(
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db)
):
    """Get donor registration and activity logs"""
    try:
        # Get donor registration logs
        donors = await db.donors.find().sort("created_at", -1).limit(limit).to_list(length=None)
        
        result = []
        for donor in donors:
            result.append({
                "type": "donor",
                "id": str(donor["_id"]),
                "name": donor["name"],
                "action": "registered",
                "details": {
                    "blood_type": donor.get("medical", {}).get("blood_type"),
                    "phone": donor.get("location", {}).get("phone"),
                    "city": donor.get("location", {}).get("city")
                },
                "timestamp": donor.get("created_at").isoformat() if donor.get("created_at") else None,
                "status": "active" if donor.get("is_active") else "inactive"
            })
        
        return {
            "total": len(result),
            "logs": result
        }
        
    except Exception as e:
        logger.error(f"Error getting donor logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get donor logs")