import re
import logging
from config import settings

logger = logging.getLogger(__name__)

# Try to import Twilio, but don't fail if not installed
try:
    from vonage import Auth, Vonage
    from vonage_messages import Sms
    VONAGE_AVAILABLE = True
except ImportError:
    VONAGE_AVAILABLE = False
    logger.warning("Vonage not installed. Message will be logged only.")

def send_sms(to_phone: str, message: str):
    """Send Whatsapp message using Vonage (falls back to logging if not configured)"""
    
    # if TWILIO_AVAILABLE and settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_phone_number:
    #     try:
    #         client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    #         sms_message = client.messages.create(
    #             body=message,
    #             from_=settings.twilio_phone_number,
    #             to=to_phone
    #         )
    #         logger.info(f"✅ SMS sent to {to_phone}: {sms_message.sid}")
    #         return sms_message.sid
    #     except Exception as e:
    #         logger.error(f"Failed to send SMS via Twilio: {e}")
    #         logger.info(f"📱 SMS to {to_phone}: {message}")
    #         return None

    if VONAGE_AVAILABLE and settings.vonage_api_key and settings.vonage_whatsapp_number:
        try:
            client = Vonage(
                Auth(
                    api_key=settings.vonage_api_key,
                    api_secret=settings.vonage_api_secret,
                )
            )

            numeric_to_phone = re.sub(r'[^0-9]', '', to_phone)            

            response = client.messages.send(
                Sms(
                    to=numeric_to_phone,
                    from_=settings.vonage_whatsapp_number,
                    text=message,
                )
            )

            return response
        except Exception as e:
            logger.error(f"Failed to send Whatsapp message via Vonage: {e}")
            logger.info(f"📱 SMS to {to_phone}: {message}")
            return None
    
    
    # Development mode - just log
    logger.info(f"📱 SMS to {to_phone}: {message}")
    print(f"\n{'='*50}")
    print(f"📱 SMS WOULD BE SENT TO: {to_phone}")
    print(f"📝 MESSAGE: {message}")
    print(f"{'='*50}\n")
    
    return "mock_sms_id"

def send_welcome_sms(phone: str, name: str):
    """Send welcome SMS with available commands"""
    message = f"""Welcome {name} to DonorPulse! 🩸

You're now registered as a blood donor.

Commands you can send:
STATUS - Check eligibility
UPDATE - Get profile link
AVAILABLE - Toggle on
UNAVAILABLE - Toggle off
HELP - All commands

Reply HELP for more info."""
    
    return send_sms(phone, message)