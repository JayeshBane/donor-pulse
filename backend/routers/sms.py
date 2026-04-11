# backend\routers\sms.py
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse
from database import get_db
from datetime import datetime, timedelta
from utils.auth import verify_webhook_signature
from config import settings
import logging

from utils.sms import send_sms
from utils.llm_inference import get_llm_reponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sms", tags=["sms"])

@router.post("/webhook")
async def sms_webhook(
    request: Request,
    db=Depends(get_db),
    x_twilio_signature: str = Header(None)
):
    """Handle incoming SMS commands with signature verification"""
    
    # Verify webhook signature in production
    if settings.environment == "production" and settings.twilio_auth_token:
        body = await request.body()
        body_str = body.decode()
        
        if not verify_webhook_signature(x_twilio_signature, body_str, settings.twilio_auth_token):
            logger.warning(f"Invalid webhook signature from {request.client.host}")
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse form data
    form_data = await request.form()
    phone = form_data.get("From", "").strip()
    command = form_data.get("Body", "").strip()
    
    if not phone or not command:
        return {"message": "Invalid request"}
    
    # Remove '+' prefix if present
    phone = phone.lstrip('+')
    
    donor = await db.donors.find_one({"location.phone": phone})
    if not donor:
        return {"message": "Donor not found. Please register at our website first."}
    
    command = command.upper().strip()
    
    # Rate limit SMS commands (max 10 per hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_commands = await db.sms_logs.count_documents({
        "phone": phone,
        "timestamp": {"$gte": one_hour_ago}
    })
    
    if recent_commands >= 10:
        return {"message": "Rate limit exceeded. Please try again later."}
    
    # Log the command
    await db.sms_logs.insert_one({
        "phone": phone,
        "command": command,
        "timestamp": datetime.utcnow(),
        "donor_id": str(donor["_id"])
    })
    
    if command == "STATUS":
        return await handle_status(donor)
    elif command == "HELP":
        return await handle_help()
    elif command == "AVAILABLE":
        return await handle_available(donor, db)
    elif command == "UNAVAILABLE":
        return await handle_unavailable(donor, db)
    elif command == "UPDATE":
        return await handle_update_link(phone, db, donor)
    else:
        return {"message": f"Unknown command: {command}. Reply HELP for available commands."}

async def handle_status(donor: dict):
    # Calculate cooldown status
    from models.donor import DonorInDB
    donor_obj = DonorInDB(**donor)
    
    cooldown_status = "❌ On cooldown" if donor_obj.is_on_cooldown else "✅ Eligible to donate"
    
    message = f"""📊 Donor Status:
    
✅ Active: {donor.get('is_active', True)}
{cooldown_status}
🎯 Reliability: {donor.get('reliability_score', 100)}/100
🩸 Blood Type: {donor.get('medical', {}).get('blood_type')}
📍 City: {donor.get('location', {}).get('city')}

Reply UPDATE to get profile edit link."""
    return {"message": message}

async def handle_help():
    message = """📱 DonorPulse Commands:

STATUS - Check eligibility & score
AVAILABLE - Turn on alerts
UNAVAILABLE - Turn off alerts
UPDATE - Get profile update link
HELP - Show this message

Need help? Contact support@donorpulse.com"""
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
    return {"message": "❌ You are now UNAVAILABLE for blood requests."}

async def handle_update_link(phone: str, db, donor: dict):
    """Generate magic link for donor update"""
    from routers.auth import generate_donor_magic_link
    
    try:
        result = await generate_donor_magic_link(phone, db)
        return {"message": f"Update link sent to your registered phone. Link expires in 30 minutes."}
    except Exception as e:
        logger.error(f"Error generating update link: {e}")
        return {"message": "Unable to generate update link. Please contact support."}
    

@router.post("/webhooks/inbound")
async def inbound_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📩 Inbound: {payload}")

    text = payload.get("text")
    sender = payload.get("from")
    profile = payload.get("profile")
    sender_name = profile.get("name")

    if text.lower() == "join job cupid":
        return

    logging.info(f"From: {sender} ({sender_name}) | Text: {text}")

    llm_response = await get_llm_reponse(text)

    llm_response_text = llm_response.get("result", {"response": "Error"}).get("response")

    response = send_sms(sender, llm_response_text)

    print(f"LLM Response: {llm_response}")

    return JSONResponse(content={"status": "received"})


# -------------------------
# Status webhook
# -------------------------
@router.post("/webhooks/status")
async def status_webhook(request: Request):
    payload = await request.json()
    logging.info(f"📊 Status: {payload}")

    status = payload.get("status")
    message_uuid = payload.get("message_uuid")

    logging.info(f"Message {message_uuid} status: {status}")

    return JSONResponse(content={"status": "ok"})