# backend\test_whats.py
import requests
from config import settings

def test_whatsapp():
    print("Testing WhatsApp message sending...")
    print(f"API URL: {settings.vonage_whatsapp_api_url}")
    print(f"API Key: {settings.vonage_api_key[:5]}...")
    print(f"Phone Number: {settings.vonage_whatsapp_number}")
    
    if not settings.vonage_api_key or not settings.vonage_api_secret:
        print("❌ Vonage credentials not configured in .env")
        return
    
    # Test phone number (your donor's number)
    test_phone = "12153916267"  # Local Donor's phone
    
    auth = (settings.vonage_api_key, settings.vonage_api_secret)
    
    payload = {
        "from": settings.vonage_whatsapp_number,
        "to": test_phone,
        "message_type": "text",
        "text": "🧪 Test message from DonorPulse! Your blood request system is working.",
        "channel": "whatsapp"
    }
    
    try:
        response = requests.post(
            settings.vonage_whatsapp_api_url,
            json=payload,
            auth=auth,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 202:
            print("\n✅ WhatsApp message sent successfully!")
        else:
            print("\n❌ Failed to send WhatsApp message")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_whatsapp()