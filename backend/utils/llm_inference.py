# backend\utils\llm_inference.py
import requests
from config import settings
import logging

logger = logging.getLogger(__name__)

# Define the system prompt that limits AI to blood donation context
SYSTEM_PROMPT = """You are DonorPulse AI Assistant, a specialized assistant for blood donation management.

YOUR ROLE:
- Help donors with blood donation-related queries only
- Provide information about donor status, appointments, blood requests, and hospital locations
- Guide users through DonorPulse platform features

YOUR LIMITATIONS:
- ONLY answer questions related to blood donation, blood types, donor eligibility, appointments, and the DonorPulse platform
- For ANY question NOT related to blood donation, respond with: "I'm specialized in blood donation assistance. Please ask me about donor status, appointments, blood requests, or blood donation information."
- Do NOT answer questions about politics, sports, entertainment, general knowledge, or any topic outside blood donation
- Do NOT provide medical advice beyond basic blood donation eligibility
- Keep responses concise and WhatsApp-friendly (short sentences)

AVAILABLE COMMANDS YOU CAN SUGGEST:
- STATUS - Check donor eligibility and score
- AVAILABLE - Turn on donation alerts
- UNAVAILABLE - Turn off donation alerts
- UPDATE - Get profile update link
- BOOK - Schedule an appointment
- REQUESTS - See nearby blood requests
- HISTORY - View donation history
- BLOOD TYPE - Get compatibility info
- HOSPITALS - Find nearby hospitals

DONOR INFORMATION YOU HAVE ACCESS TO (when provided):
- Donor name, blood type, city, active status, reliability score

RESPONSE GUIDELINES:
- Be helpful but concise
- If you don't know something about blood donation, say so
- Always prioritize directing users to the appropriate commands
- Never invent information about blood donation that you're not sure about"""

async def get_llm_reponse(prompt: str, include_system_prompt: bool = True):
    """
    Get LLM response with optional system prompt to constrain the AI
    
    Args:
        prompt: The user prompt
        include_system_prompt: Whether to include the constrained system prompt
    """
    ACCOUNT_ID = settings.cloudflare_account_id
    AUTH_TOKEN = settings.cloudflare_auth_token
    
    if not ACCOUNT_ID or not AUTH_TOKEN:
        logger.warning("Cloudflare credentials not configured")
        return {"result": {"response": "AI service not configured. Please contact support."}}
    
    try:
        messages = []
        
        if include_system_prompt:
            messages.append({"role": "system", "content": SYSTEM_PROMPT})
        
        messages.append({"role": "user", "content": prompt})
        
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/meta/llama-3.2-3b-instruct",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"messages": messages},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            logger.error(f"Cloudflare API error: {response.status_code} - {response.text}")
            return {"result": {"response": "Sorry, I'm having trouble connecting. Please try again later."}}
            
    except requests.exceptions.Timeout:
        logger.error("Cloudflare API timeout")
        return {"result": {"response": "The request timed out. Please try again."}}
    except Exception as e:
        logger.error(f"Error calling Cloudflare API: {e}")
        return {"result": {"response": "An error occurred. Please try again later."}}

async def get_constrained_response(user_message: str, donor_context: dict = None) -> str:
    """
    Get a constrained response that only answers blood donation related questions
    
    Args:
        user_message: The user's message
        donor_context: Optional donor information dict
    """
    # Build context if donor info is available
    context = ""
    if donor_context:
        context = f"""
Donor Context:
- Name: {donor_context.get('name', 'Unknown')}
- Blood Type: {donor_context.get('blood_type', 'Unknown')}
- City: {donor_context.get('city', 'Unknown')}
- Active: {donor_context.get('is_active', True)}
- Reliability Score: {donor_context.get('reliability_score', 100)}/100
"""
    
    full_prompt = f"""{context}

User Question: {user_message}

Remember: Only answer blood donation related questions. If the question is not about blood donation, politely decline and redirect to blood donation topics."""
    
    result = await get_llm_reponse(full_prompt, include_system_prompt=True)
    return result.get("result", {}).get("response", "I'm here to help with blood donation questions!")

async def is_blood_donation_related(message: str) -> bool:
    """
    Quick check if message is related to blood donation
    """
    blood_keywords = [
        'blood', 'donate', 'donation', 'blood type', 'plasma', 'platelet',
        'hemoglobin', 'red blood', 'white blood', 'transfusion', 'donor',
        'recipient', 'blood bank', 'blood drive', 'blood request', 'blood camp',
        'status', 'appointment', 'hospital', 'eligibility', 'cooldown'
    ]
    
    message_lower = message.lower()
    for keyword in blood_keywords:
        if keyword in message_lower:
            return True
    return False