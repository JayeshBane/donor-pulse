# backend\routers\sms.py
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse
from database import get_db
from datetime import datetime, timedelta
from utils.auth import verify_webhook_signature
from config import settings
import logging
import requests
from bson import ObjectId

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
    
    command_upper = command.upper().strip()
    
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
        "command": command_upper,
        "timestamp": datetime.utcnow(),
        "donor_id": str(donor["_id"])
    })
    
    # Check for YES/NO responses to blood requests
    if command_upper == "YES" or command_upper == "Y":
        return await handle_request_response(phone, "YES", donor, db)
    elif command_upper == "NO" or command_upper == "N":
        return await handle_request_response(phone, "NO", donor, db)
    elif command_upper == "STATUS":
        return await handle_status(donor, db)
    elif command_upper == "HELP":
        return await handle_help()
    elif command_upper == "AVAILABLE":
        return await handle_available(donor, db)
    elif command_upper == "UNAVAILABLE":
        return await handle_unavailable(donor, db)
    elif command_upper == "UPDATE":
        return await handle_update_link(phone, db, donor)
    elif command_upper.startswith("ETA"):
        return await handle_eta_response(phone, command_upper, donor, db)
    else:
        return {"message": f"Unknown command: {command}. Reply HELP for available commands."}

async def handle_request_response(phone: str, response: str, donor: dict, db):
    """Handle donor response to blood request (YES/NO)"""
    try:
        # Find pending request for this donor
        pending_response = await db.matched_donors.find_one({
            "donor_id": str(donor["_id"]),
            "status": "pending"
        })
        
        if not pending_response:
            return {"message": "No pending blood requests found. Reply HELP for available commands."}
        
        # Get request details
        blood_request = await db.blood_requests.find_one({"_id": ObjectId(pending_response["request_id"])})
        if not blood_request:
            return {"message": "Request no longer active."}
        
        # Determine response status
        response_status = "accepted" if response == "YES" else "declined"
        
        # Call the response endpoint
        try:
            response_data = {
                "donor_id": str(donor["_id"]),
                "request_id": pending_response["request_id"],
                "response": response_status
            }
            
            # Make internal API call
            api_response = requests.post(
                f"http://localhost:8000/api/v1/requests/{pending_response['request_id']}/respond",
                json=response_data,
                timeout=10
            )
            
            if api_response.status_code != 200:
                logger.error(f"Failed to record response: {api_response.text}")
                return {"message": "Error processing your response. Please try again."}
            
        except Exception as e:
            logger.error(f"Error calling response API: {e}")
            return {"message": "Error processing your response. Please try again."}
        
        if response_status == "accepted":
            # Get hospital details
            hospital = await db.hospitals.find_one({"_id": ObjectId(blood_request["hospital_id"])})
            hospital_name = hospital.get("name", "the hospital") if hospital else "the hospital"
            
            # Send confirmation message
            message = f"""✅ Thank you for accepting the blood request!

Please proceed to {hospital_name} at your earliest convenience.

Urgency: {blood_request['urgency'].upper()}
Blood Type: {blood_request['blood_type']}

Reply with your estimated arrival time (e.g., "ETA 30") if possible.

- DonorPulse"""
            
            send_sms(phone, message)
            return {"message": "Thank you for accepting! Please proceed to the hospital."}
        else:
            message = f"""Thank you for letting us know. You may be contacted for future blood donation requests.

Stay healthy and keep saving lives! 🩸

- DonorPulse"""
            
            send_sms(phone, message)
            return {"message": "Thank you for your response."}
            
    except Exception as e:
        logger.error(f"Error handling request response: {e}")
        return {"message": "Error processing your response. Please try again."}

async def handle_eta_response(phone: str, command: str, donor: dict, db):
    """Handle donor ETA response"""
    try:
        import re
        # Extract minutes (e.g., "ETA 30" or "ETA 45 minutes")
        minutes_match = re.search(r'ETA\s+(\d+)', command)
        if minutes_match:
            eta_minutes = int(minutes_match.group(1))
            
            # Find accepted request for this donor
            accepted_response = await db.matched_donors.find_one({
                "donor_id": str(donor["_id"]),
                "status": "accepted"
            })
            
            if accepted_response:
                # Update ETA
                await db.matched_donors.update_one(
                    {"_id": accepted_response["_id"]},
                    {"$set": {"eta_minutes": eta_minutes}}
                )
                
                return {"message": f"ETA of {eta_minutes} minutes recorded. Thank you!"}
            else:
                return {"message": "No active request found. Reply HELP for available commands."}
        else:
            return {"message": "Please specify minutes. Example: ETA 30"}
            
    except Exception as e:
        logger.error(f"Error processing ETA: {e}")
        return {"message": "Error processing ETA. Please try again."}

async def handle_status(donor: dict, db):
    # Calculate cooldown status
    from models.donor import DonorInDB
    donor_obj = DonorInDB(**donor)
    
    cooldown_status = "❌ On cooldown" if donor_obj.is_on_cooldown else "✅ Eligible to donate"
    
    # Also check for pending requests
    pending_count = await db.matched_donors.count_documents({
        "donor_id": str(donor["_id"]),
        "status": "pending"
    })
    
    pending_message = f"\n📨 Pending requests: {pending_count}" if pending_count > 0 else ""
    
    message = f"""📊 Donor Status:
    
✅ Active: {donor.get('is_active', True)}
{cooldown_status}
🎯 Reliability: {donor.get('reliability_score', 100)}/100
🩸 Blood Type: {donor.get('medical', {}).get('blood_type')}
📍 City: {donor.get('location', {}).get('city')}{pending_message}

Reply UPDATE to get profile edit link."""
    return {"message": message}

async def handle_help():
    message = """📱 DonorPulse Commands:

STATUS - Check eligibility & score
AVAILABLE - Turn on alerts
UNAVAILABLE - Turn off alerts
UPDATE - Get profile update link
YES/NO - Respond to blood requests
ETA 30 - Provide arrival time
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

    is_location = False

    if "location" in payload:
        is_location = True
        location = payload.get("location")

        latitude = location["lat"]
        longitude = location["long"]

        print(f"Location received: {latitude} and {longitude}")

    text = payload.get("text", "")
    sender = payload.get("from")
    profile = payload.get("profile")
    sender_name = profile.get("name")

    if text and text.lower() == "join job cupid":
        return

    if not is_location:
        logging.info(f"From: {sender} ({sender_name}) | Text: {text}")
        llm_response = await get_llm_reponse(text)

        llm_response_text = llm_response.get("result", {"response": "Error"}).get("response")

        response = send_sms(sender, llm_response_text)

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