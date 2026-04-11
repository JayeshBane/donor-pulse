from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from datetime import datetime, timedelta
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sms", tags=["sms"])

@router.post("/webhook")
async def sms_webhook(phone: str, command: str, db=Depends(get_db)):
    """Handle incoming SMS commands"""
    donor = await db.donors.find_one({"location.phone": phone})
    if not donor:
        return {"message": "Donor not found. Please register first."}
    
    command = command.upper().strip()
    
    if command == "STATUS":
        return await handle_status(donor)
    elif command == "HELP":
        return await handle_help()
    elif command == "AVAILABLE":
        return await handle_available(donor, db)
    elif command == "UNAVAILABLE":
        return await handle_unavailable(donor, db)
    else:
        return {"message": f"Unknown command. Reply HELP for available commands."}

async def handle_status(donor: dict):
    message = f"""📊 Donor Status:
✅ Active: {donor.get('is_active', True)}
🎯 Reliability: {donor.get('reliability_score', 100)}/100
🩸 Blood Type: {donor.get('medical', {}).get('blood_type')}
📍 City: {donor.get('location', {}).get('city')}"""
    return {"message": message}

async def handle_help():
    message = """📱 DonorPulse Commands:
STATUS - Check eligibility & score
AVAILABLE - Turn on alerts
UNAVAILABLE - Turn off alerts
HELP - Show this message"""
    return {"message": message}

async def handle_available(donor: dict, db):
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
    )
    return {"message": "✅ You are now AVAILABLE to receive blood requests."}

async def handle_unavailable(donor: dict, db):
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return {"message": "❌ You are now UNAVAILABLE."}