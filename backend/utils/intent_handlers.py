import logging
from datetime import datetime
from bson import ObjectId
from utils.sms import send_sms
from utils.auth import generate_magic_token
from config import settings

logger = logging.getLogger(__name__)

def calculate_cooldown(donor: dict) -> tuple:
    """Calculate if donor is on cooldown"""
    last_donation = donor.get("medical", {}).get("last_donation_date")
    if not last_donation:
        return False, 0
    
    from datetime import datetime, timedelta
    if isinstance(last_donation, str):
        last_donation = datetime.fromisoformat(last_donation.replace('Z', '+00:00'))
    
    days_since = (datetime.utcnow() - last_donation).days
    cooldown_days = 56
    if days_since < cooldown_days:
        return True, cooldown_days - days_since
    return False, 0

async def handle_status_intent(donor: dict, db, entities: dict) -> str:
    """Handle STATUS intent"""
    donor_name = donor.get('name', 'Donor')
    is_active = donor.get('is_active', True)
    is_paused = donor.get('is_paused', False)
    reliability_score = donor.get('reliability_score', 100)
    blood_type = donor.get('medical', {}).get('blood_type', 'Unknown')
    city = donor.get('location', {}).get('city', 'Unknown')
    
    # Check cooldown
    on_cooldown, days_remaining = calculate_cooldown(donor)
    
    # Calculate eligibility
    is_eligible = is_active and not is_paused and not on_cooldown
    
    cooldown_status = "❌ On cooldown" if on_cooldown else "✅ Eligible to donate"
    if on_cooldown and days_remaining > 0:
        cooldown_status += f" ({days_remaining} days remaining)"
    
    # Get last donation date
    last_donation = donor.get('medical', {}).get('last_donation_date')
    last_donation_str = "Never"
    if last_donation:
        if isinstance(last_donation, datetime):
            last_donation_str = last_donation.strftime("%Y-%m-%d")
        else:
            last_donation_str = str(last_donation)[:10]
    
    # Get pending requests count
    pending_count = await db.matched_donors.count_documents({
        "donor_id": str(donor["_id"]),
        "status": "pending"
    })
    
    message = f"""📊 Donor Status - {donor_name}

✅ Active: {'Yes' if is_active else 'No'}
{cooldown_status}
🎯 Reliability: {reliability_score}/100
🩸 Blood Type: {blood_type}
📍 City: {city}
📅 Last Donation: {last_donation_str}"""

    if pending_count > 0:
        message += f"\n📨 Pending requests: {pending_count}"
    
    message += "\n\nReply UPDATE to get profile edit link."
    
    return message

async def handle_available_intent(donor: dict, db, entities: dict) -> str:
    """Handle AVAILABLE intent"""
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": True, "is_paused": False, "updated_at": datetime.utcnow()}}
    )
    return "✅ You are now AVAILABLE to receive blood requests. You will be notified when your blood type is needed."

async def handle_unavailable_intent(donor: dict, db, entities: dict) -> str:
    """Handle UNAVAILABLE intent"""
    await db.donors.update_one(
        {"_id": donor["_id"]},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    return "❌ You are now UNAVAILABLE for blood requests. You can turn back on anytime by replying AVAILABLE."

async def handle_update_intent(donor: dict, db, entities: dict) -> str:
    """Handle UPDATE intent"""
    from routers.auth import generate_donor_magic_link
    phone = donor.get("location", {}).get("phone")
    
    if phone:
        try:
            result = await generate_donor_magic_link(phone, db)
            if isinstance(result, dict) and "magic_link" in result:
                return f"🔗 Update link sent to your phone. Link expires in 30 minutes.\n\nYou can also update via web: {result['magic_link']}"
            return f"Update link sent to your registered phone. Link expires in 30 minutes."
        except Exception as e:
            logger.error(f"Error generating magic link: {e}")
            return "Unable to generate update link. Please contact support."
    
    return "Unable to generate update link. No phone number found in your profile."

# Replace the handle_book_appointment_intent function

async def handle_book_appointment_intent(donor: dict, db, entities: dict) -> str:
    """Handle BOOK APPOINTMENT intent"""
    donor_id = str(donor["_id"])
    donor_name = donor.get('name', 'Donor')
    blood_type = entities.get("blood_type", donor.get("medical", {}).get("blood_type", "Unknown"))
    
    # Create booking link
    booking_link = f"{settings.frontend_url}/donor/book?donor_id={donor_id}"
    
    # Get hospitals with available slots
    hospitals = await db.hospitals.find({
        "is_verified": True, 
        "is_active": True
    }).limit(3).to_list(length=None)
    
    message = f"📅 Book a Donation Appointment, {donor_name}!\n\n"
    message += f"🔗 Click this link to book your appointment:\n{booking_link}\n\n"
    message += f"🩸 Your Blood Type: {blood_type}\n\n"
    
    if hospitals:
        message += "🏥 Available Hospitals:\n"
        for hospital in hospitals:
            hospital_name = hospital.get('name', 'Unknown')
            hospital_city = hospital.get('location', {}).get('city', 'Unknown')
            message += f"   • {hospital_name} - {hospital_city}\n"
        message += "\n"
    
    message += "💡 Tip: Book in advance to secure your preferred time slot!\n"
    message += "📞 Need help? Contact support@donorpulse.com"
    
    return message

async def handle_nearby_requests_intent(donor: dict, db, entities: dict) -> str:
    """Handle NEARBY REQUESTS intent"""
    donor_lat = donor.get("location", {}).get("lat")
    donor_lng = donor.get("location", {}).get("lng")
    donor_city = donor.get("location", {}).get("city", "your area")
    radius = entities.get("radius", 50)
    
    if not donor_lat or not donor_lng:
        return "📍 Please update your profile with your location to see nearby blood requests.\n\nReply UPDATE to get a profile update link."
    
    # Find active requests
    from datetime import datetime, timedelta
    active_requests = await db.blood_requests.find({
        "status": {"$in": ["pending", "broadcasting"]},
        "expires_at": {"$gt": datetime.utcnow()}
    }).limit(5).to_list(length=None)
    
    if not active_requests:
        return f"📍 No active blood requests in {donor_city} at the moment.\n\nYou will be notified when your blood type is needed."
    
    message = f"📍 Blood Requests Near {donor_city}:\n\n"
    
    urgency_emoji = {
        "routine": "🩸",
        "urgent": "⚠️",
        "critical": "🔴",
        "sos": "🚨"
    }
    
    for req in active_requests[:5]:
        urgency = req.get('urgency', 'routine')
        emoji = urgency_emoji.get(urgency, "🩸")
        message += f"{emoji} {req.get('blood_type', 'Unknown')} - {urgency.upper()}\n"
        message += f"🏥 {req.get('hospital_name', 'Unknown Hospital')}\n"
        
        expires_at = req.get('expires_at')
        if expires_at:
            if isinstance(expires_at, datetime):
                expires_str = expires_at.strftime("%Y-%m-%d %H:%M")
            else:
                expires_str = str(expires_at)[:16]
            message += f"⏰ Expires: {expires_str}\n"
        message += "\n"
    
    message += "Reply YES to any request you receive to help save lives!"
    
    return message

async def handle_donation_history_intent(donor: dict, db, entities: dict) -> str:
    """Handle DONATION HISTORY intent"""
    total_donations = donor.get('total_donations_completed', 0)
    total_confirmed = donor.get('total_donations_confirmed', 0)
    reliability_score = donor.get('reliability_score', 100)
    alerts_sent = donor.get('total_alerts_sent', 0)
    alerts_responded = donor.get('total_alerts_responded', 0)
    
    response_rate = 0
    if alerts_sent > 0:
        response_rate = int((alerts_responded / alerts_sent) * 100)
    
    message = f"📊 Your Donation History\n\n"
    message += f"🏆 Completed Donations: {total_donations}\n"
    message += f"✅ Confirmed Donations: {total_confirmed}\n"
    message += f"⭐ Reliability Score: {reliability_score}/100\n"
    message += f"📱 Response Rate: {response_rate}%\n\n"
    
    # Get recent appointments
    appointments = await db.appointments.find({
        "donor_id": str(donor["_id"]),
        "status": "completed"
    }).sort("appointment_date", -1).limit(5).to_list(length=None)
    
    if appointments:
        message += "📅 Recent Donations:\n"
        for apt in appointments:
            apt_date = apt.get("appointment_date")
            date_str = apt_date.strftime("%Y-%m-%d") if apt_date else "Unknown"
            hospital_name = apt.get("hospital_name", "Unknown Hospital")
            message += f"  • {date_str} - {hospital_name}\n"
    else:
        message += "📅 No donation history yet.\n"
        message += "💪 Be the first to donate and save lives!"
    
    return message

async def handle_blood_type_info_intent(donor: dict, db, entities: dict) -> str:
    """Handle BLOOD TYPE INFO intent"""
    blood_type = donor.get("medical", {}).get("blood_type")
    
    if not blood_type:
        return "🩸 Blood type not found in your profile. Please update your profile with your blood type.\n\nReply UPDATE to get a profile update link."
    
    # Blood type compatibility info
    compatibility = {
        "O-": {"donate_to": "All blood types (Universal Donor)", "receive_from": "O- only", "fact": "You are a universal donor! Your blood can save anyone."},
        "O+": {"donate_to": "O+, A+, B+, AB+", "receive_from": "O-, O+", "fact": "You are the most common blood type."},
        "A-": {"donate_to": "A-, A+, AB-, AB+", "receive_from": "O-, A-", "fact": "Your blood is rare and valuable."},
        "A+": {"donate_to": "A+, AB+", "receive_from": "O-, O+, A-, A+", "fact": "You are a common blood type."},
        "B-": {"donate_to": "B-, B+, AB-, AB+", "receive_from": "O-, B-", "fact": "Your blood is rare."},
        "B+": {"donate_to": "B+, AB+", "receive_from": "O-, O+, B-, B+", "fact": "You are a valuable donor."},
        "AB-": {"donate_to": "AB-, AB+", "receive_from": "All negative types", "fact": "You are a universal plasma donor!"},
        "AB+": {"donate_to": "AB+ only", "receive_from": "All blood types (Universal Recipient)", "fact": "You can receive from anyone!"}
    }
    
    info = compatibility.get(blood_type, {})
    
    message = f"🩸 Your Blood Type: {blood_type}\n\n"
    message += f"📤 You can donate to: {info.get('donate_to', 'Unknown')}\n"
    message += f"📥 You can receive from: {info.get('receive_from', 'Unknown')}\n\n"
    message += f"💡 Did you know? {info.get('fact', 'Every donation saves up to 3 lives!')}\n\n"
    message += f"⭐ { 'You are a Universal Donor!' if blood_type == 'O-' else 'Your donation matters!' }"
    
    return message

async def handle_hospital_info_intent(donor: dict, db, entities: dict) -> str:
    """Handle HOSPITAL INFO intent"""
    donor_city = donor.get("location", {}).get("city")
    
    query = {"is_verified": True, "is_active": True}
    if donor_city:
        query["location.city"] = donor_city
    
    hospitals = await db.hospitals.find(query).limit(5).to_list(length=None)
    
    if not hospitals:
        if donor_city:
            return f"🏥 No verified hospitals found in {donor_city}. Please check other cities or contact support."
        return "🏥 No verified hospitals found. Please check back later."
    
    message = f"🏥 Hospitals in {donor_city if donor_city else 'Your Area'}:\n\n"
    
    for hospital in hospitals:
        name = hospital.get('name', 'Unknown')
        city = hospital.get('location', {}).get('city', 'Unknown')
        phone = hospital.get('phone', 'N/A')
        address = hospital.get('location', {}).get('address', 'Address not available')
        
        message += f"🏥 {name}\n"
        message += f"📍 {address}, {city}\n"
        message += f"📞 {phone}\n\n"
    
    message += "💡 You can also book appointments at these hospitals through our website."
    
    return message

async def handle_help_intent(donor: dict, db, entities: dict) -> str:
    """Handle HELP intent"""
    donor_name = donor.get('name', 'Donor')
    
    message = f"📱 DonorPulse Help - Welcome {donor_name}!\n\n"
    message += "🔹 COMMANDS:\n"
    message += "   STATUS - Check eligibility & score\n"
    message += "   AVAILABLE - Turn on alerts\n"
    message += "   UNAVAILABLE - Turn off alerts\n"
    message += "   UPDATE - Get profile update link\n"
    message += "   BOOK - Schedule an appointment\n"
    message += "   REQUESTS - See nearby blood requests\n"
    message += "   HISTORY - View donation history\n"
    message += "   BLOOD TYPE - Get compatibility info\n"
    message += "   HOSPITALS - Find nearby hospitals\n"
    message += "   HELP - Show this message\n\n"
    message += "🔹 NATURAL LANGUAGE:\n"
    message += "   You can also ask naturally like:\n"
    message += "   • 'What is my status?'\n"
    message += "   • 'I want to donate blood'\n"
    message += "   • 'Find hospitals near me'\n\n"
    message += "💬 Need more help? Contact support@donorpulse.com"
    
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