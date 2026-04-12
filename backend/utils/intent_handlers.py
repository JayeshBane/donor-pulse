import logging
from datetime import datetime
from bson import ObjectId
from utils.sms import send_sms
from utils.auth import generate_magic_token
from config import settings

logger = logging.getLogger(__name__)

async def handle_status_intent(donor: dict, db, entities: dict) -> str:
    """Handle STATUS intent"""
    from models.donor import DonorInDB
    
    donor_obj = DonorInDB(**donor)
    
    cooldown_status = "❌ On cooldown" if donor_obj.is_on_cooldown else "✅ Eligible to donate"
    
    message = f"""📊 Donor Status:
    
✅ Active: {donor.get('is_active', True)}
{cooldown_status}
🎯 Reliability: {donor.get('reliability_score', 100)}/100
🩸 Blood Type: {donor.get('medical', {}).get('blood_type')}
📍 City: {donor.get('location', {}).get('city')}
📅 Last Donation: {donor.get('medical', {}).get('last_donation_date', 'Never')}

Reply UPDATE to get profile edit link."""
    
    return message

async def handle_available_intent(donor: dict, db, entities: dict) -> str:
    """Handle AVAILABLE intent"""
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
    )
    return "✅ You are now AVAILABLE to receive blood requests."

async def handle_unavailable_intent(donor: dict, db, entities: dict) -> str:
    """Handle UNAVAILABLE intent"""
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return "❌ You are now UNAVAILABLE for blood requests."

async def handle_update_intent(donor: dict, db, entities: dict) -> str:
    """Handle UPDATE intent"""
    from routers.auth import generate_donor_magic_link
    phone = donor.get("location", {}).get("phone")
    
    if phone:
        result = await generate_donor_magic_link(phone, db)
        return f"Update link sent to your registered phone. Link expires in 30 minutes."
    return "Unable to generate update link. Please contact support."

async def handle_book_appointment_intent(donor: dict, db, entities: dict) -> str:
    """Handle BOOK APPOINTMENT intent"""
    donor_id = str(donor["_id"])
    blood_type = entities.get("blood_type", donor.get("medical", {}).get("blood_type"))
    
    # Get hospitals with available slots
    hospitals = await db.hospitals.find({"is_verified": True, "is_active": True}).limit(5).to_list(length=None)
    
    if not hospitals:
        return "No hospitals available for booking at the moment. Please try again later."
    
    # Create booking link
    booking_link = f"{settings.frontend_url}/donor/book?donor_id={donor_id}"
    
    message = f"""📅 Book a Donation Appointment

Click the link below to book your appointment:
{booking_link}

Available hospitals near you:
"""
    for hospital in hospitals[:3]:
        message += f"\n🏥 {hospital.get('name')} - {hospital.get('location', {}).get('city')}"
    
    message += f"\n\nBlood Type: {blood_type}"
    
    return message

async def handle_nearby_requests_intent(donor: dict, db, entities: dict) -> str:
    """Handle NEARBY REQUESTS intent"""
    donor_lat = donor.get("location", {}).get("lat")
    donor_lng = donor.get("location", {}).get("lng")
    radius = entities.get("radius", 50)
    
    if not donor_lat or not donor_lng:
        return "Please update your profile with your location to see nearby blood requests."
    
    # Find nearby requests
    requests = await db.blood_requests.find({
        "status": {"$in": ["pending", "broadcasting"]},
        "expires_at": {"$gt": datetime.utcnow()}
    }).limit(5).to_list(length=None)
    
    if not requests:
        return "No active blood requests in your area at the moment."
    
    message = f"📍 Nearby Blood Requests (within {radius}km):\n\n"
    for req in requests:
        message += f"🩸 {req.get('blood_type')} - {req.get('urgency').upper()}\n"
        message += f"🏥 {req.get('hospital_name')}\n"
        message += f"📅 Expires: {req.get('expires_at').strftime('%Y-%m-%d %H:%M')}\n\n"
    
    message += "Reply YES to any request you receive to help save lives!"
    
    return message

async def handle_donation_history_intent(donor: dict, db, entities: dict) -> str:
    """Handle DONATION HISTORY intent"""
    total_donations = donor.get('total_donations_completed', 0)
    reliability_score = donor.get('reliability_score', 100)
    
    # Get recent appointments
    appointments = await db.appointments.find({
        "donor_id": str(donor["_id"]),
        "status": "completed"
    }).sort("appointment_date", -1).limit(5).to_list(length=None)
    
    message = f"📊 Your Donation History:\n\n"
    message += f"🎯 Total Donations: {total_donations}\n"
    message += f"⭐ Reliability Score: {reliability_score}/100\n\n"
    
    if appointments:
        message += "📅 Recent Donations:\n"
        for apt in appointments:
            date = apt.get("appointment_date")
            date_str = date.strftime("%Y-%m-%d") if date else "Unknown"
            message += f"  • {date_str} - {apt.get('hospital_name')}\n"
    else:
        message += "No donation history yet. Be the first to donate!"
    
    return message

async def handle_blood_type_info_intent(donor: dict, db, entities: dict) -> str:
    """Handle BLOOD TYPE INFO intent"""
    blood_type = donor.get("medical", {}).get("blood_type")
    
    # Blood type compatibility info
    compatibility = {
        "O-": {"donate_to": "All blood types", "receive_from": "O- only"},
        "O+": {"donate_to": "O+, A+, B+, AB+", "receive_from": "O-, O+"},
        "A-": {"donate_to": "A-, A+, AB-, AB+", "receive_from": "O-, A-"},
        "A+": {"donate_to": "A+, AB+", "receive_from": "O-, O+, A-, A+"},
        "B-": {"donate_to": "B-, B+, AB-, AB+", "receive_from": "O-, B-"},
        "B+": {"donate_to": "B+, AB+", "receive_from": "O-, O+, B-, B+"},
        "AB-": {"donate_to": "AB-, AB+", "receive_from": "All negative types"},
        "AB+": {"donate_to": "AB+ only", "receive_from": "All blood types"}
    }
    
    info = compatibility.get(blood_type, {})
    
    message = f"🩸 Your Blood Type: {blood_type}\n\n"
    message += f"📤 You can donate to: {info.get('donate_to', 'Unknown')}\n"
    message += f"📥 You can receive from: {info.get('receive_from', 'Unknown')}\n\n"
    message += f"{'⭐ You are a Universal Donor!' if blood_type == 'O-' else '💪 Every donation saves lives!'}"
    
    return message

async def handle_hospital_info_intent(donor: dict, db, entities: dict) -> str:
    """Handle HOSPITAL INFO intent"""
    donor_city = donor.get("location", {}).get("city")
    
    query = {"is_verified": True, "is_active": True}
    if donor_city:
        query["location.city"] = donor_city
    
    hospitals = await db.hospitals.find(query).limit(5).to_list(length=None)
    
    if not hospitals:
        return "No verified hospitals found in your area."
    
    message = f"🏥 Nearby Hospitals:\n\n"
    for hospital in hospitals:
        message += f"• {hospital.get('name')}\n"
        message += f"  📍 {hospital.get('location', {}).get('city')}\n"
        message += f"  📞 {hospital.get('phone')}\n\n"
    
    return message

async def handle_help_intent(donor: dict, db, entities: dict) -> str:
    """Handle HELP intent"""
    message = """📱 DonorPulse Commands:

🔹 STATUS - Check eligibility & score
🔹 AVAILABLE - Turn on alerts
🔹 UNAVAILABLE - Turn off alerts  
🔹 UPDATE - Get profile update link
🔹 BOOK - Schedule an appointment
🔹 REQUESTS - See nearby blood requests
🔹 HISTORY - View donation history
🔹 BLOOD TYPE - Get compatibility info
🔹 HOSPITALS - Find nearby hospitals
🔹 HELP - Show this message

💬 You can also chat naturally. I'll understand your intent!

Need help? Contact support@donorpulse.com"""
    
    return message

# Map intents to handler functions
INTENT_HANDLERS = {
    "status": handle_status_intent,
    "available": handle_available_intent,
    "unavailable": handle_unavailable_intent,
    "update": handle_update_intent,
    "book_appointment": handle_book_appointment_intent,
    "nearby_requests": handle_nearby_requests_intent,
    "donation_history": handle_donation_history_intent,
    "blood_type_info": handle_blood_type_info_intent,
    "hospital_info": handle_hospital_info_intent,
    "help": handle_help_intent,
}