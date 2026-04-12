# # backend\utils\sms.py
# import re
# import logging
# from urllib import response
# from config import settings
# import requests

# logger = logging.getLogger(__name__)

# # Try to import Twilio, but don't fail if not installed
# # try:
# #     from vonage import Auth, Vonage
# #     from vonage_messages import Sms
# #     VONAGE_AVAILABLE = True
# # except ImportError:
# #     VONAGE_AVAILABLE = False
# #     logger.warning("Vonage not installed. Message will be logged only.")

# def send_sms(to_phone: str, message: str):
#     """Send Whatsapp message using Vonage (falls back to logging if not configured)"""
    
#     # if TWILIO_AVAILABLE and settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number:
#     #     try:
#     #         client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
#     #         sms_message = client.messages.create(
#     #             body=message,
#     #             from_=settings.twilio_phone_number,
#     #             to=to_phone
#     #         )
#     #         logger.info(f"✅ SMS sent to {to_phone}: {sms_message.sid}")
#     #         return sms_message.sid
#     #     except Exception as e:
#     #         logger.error(f"Failed to send SMS via Twilio: {e}")
#     #         logger.info(f"📱 SMS to {to_phone}: {message}")
#     #         return None

#     if settings.vonage_api_key and settings.vonage_whatsapp_number:
#         try:
#             auth = (settings.vonage_api_key, settings.vonage_api_secret)  # (API key, API secret)

#             headers = {
#                 "Content-Type": "application/json",
#                 "Accept": "application/json"
#             }

#             numeric_to_phone = re.sub(r'^[0-9]$','', to_phone)

#             payload = {
#                 "from": settings.vonage_whatsapp_number,   # e.g. "14157386102" or WhatsApp-enabled number
#                 "to": numeric_to_phone,     # e.g. "919XXXXXXXXX"
#                 "message_type": "text",
#                 "text": message,
#                 "channel": "whatsapp"
#             }

#             response = requests.post(settings.vonage_whatsapp_api_url, json=payload, headers=headers, auth=auth)

#             # logger.info("Status Code:", response.status_code)
#             # logger.info("Response:", response.text)

#             return response
#         except Exception as e:
#             logger.error(f"Failed to send Whatsapp message via Vonage: {e}")
#             logger.info(f"📱 SMS to {to_phone}: {message}")
#             return None
    
    
#     # Development mode - just log
#     logger.info(f"📱 SMS to {to_phone}: {message}")
#     print(f"\n{'='*50}")
#     print(f"📱 SMS WOULD BE SENT TO: {to_phone}")
#     print(f"📝 MESSAGE: {message}")
#     print(f"{'='*50}\n")
    
#     return "mock_sms_id"

# def send_welcome_sms(phone: str, name: str):
#     """Send welcome SMS with available commands"""
#     message = f"""Welcome {name} to DonorPulse! 🩸

# You're now registered as a blood donor.

# Commands you can send:
# STATUS - Check eligibility
# UPDATE - Get profile link
# AVAILABLE - Toggle on
# UNAVAILABLE - Toggle off
# HELP - All commands

# Reply HELP for more info."""
    
#     return send_sms(phone, message)

import re
import logging
from config import settings
import requests

logger = logging.getLogger(__name__)

def format_phone_number(phone: str) -> str:
    """Format phone number for Vonage WhatsApp sandbox - must match exactly how it's whitelisted"""
    # Remove any whitespace
    phone = phone.strip()
    
    # Remove leading '+' if present
    phone = phone.lstrip('+')
    
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # For US/Canada numbers (10 digits), add 1
    if len(phone) == 10:
        return '1' + phone
    
    # For numbers with 11 digits starting with 1
    if len(phone) == 11 and phone.startswith('1'):
        return phone
    
    # For numbers with country code (e.g., 91 for India)
    if len(phone) > 10:
        return phone
    
    # Default
    return '1' + phone

def send_sms(to_phone: str, message: str):
    """Send Whatsapp message using Vonage"""
    
    # Format phone number
    formatted_phone = format_phone_number(to_phone)
    logger.info(f"Original phone: {to_phone} -> Formatted: {formatted_phone}")
    
    # Always try to send via Vonage if configured
    if settings.vonage_api_key and settings.vonage_whatsapp_number:
        try:
            auth = (settings.vonage_api_key, settings.vonage_api_secret)

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "from": settings.vonage_whatsapp_number,
                "to": formatted_phone,
                "message_type": "text",
                "text": message,
                "channel": "whatsapp"
            }

            logger.info(f"Sending WhatsApp to {formatted_phone}")
            response = requests.post(
                settings.vonage_whatsapp_api_url, 
                json=payload, 
                headers=headers, 
                auth=auth,
                timeout=30
            )

            logger.info(f"WhatsApp Response Status: {response.status_code}")
            
            if response.status_code == 202:
                logger.info(f"✅ WhatsApp message sent to {formatted_phone}")
                return response
            else:
                logger.error(f"WhatsApp failed with status {response.status_code}: {response.text}")
                # Don't fall through - just log the error
                return None
                
        except Exception as e:
            logger.error(f"Failed to send Whatsapp message via Vonage: {e}")
            return None
    
    # If Vonage not configured, just log
    logger.info(f"📱 Message to {formatted_phone}: {message}")
    print(f"\n{'='*50}")
    print(f"📱 WHATSAPP MESSAGE (DEVELOPMENT MODE)")
    print(f"📱 TO: {formatted_phone}")
    print(f"📝 MESSAGE: {message}")
    print(f"{'='*50}\n")
    
    return "mock_message_id"

def send_welcome_sms(phone: str, name: str):
    """Send welcome SMS with available commands"""
    formatted_phone = format_phone_number(phone)
    
    message = f"""Welcome {name} to DonorPulse! 🩸

You're now registered as a blood donor.

Commands you can send:
STATUS - Check eligibility
UPDATE - Get profile link
AVAILABLE - Toggle on
UNAVAILABLE - Toggle off
HELP - All commands

Reply HELP for more info."""
    
    return send_sms(formatted_phone, message)