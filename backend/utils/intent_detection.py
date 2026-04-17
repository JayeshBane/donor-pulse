# backend\utils\intent_detection.py
import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# Define intents and their keywords
INTENTS = {
    "status": {
        "keywords": ["status", "check status", "my status", "eligibility", "am i eligible", "can i donate", "when can i donate"],
        "description": "Check donor eligibility and status"
    },
    "available": {
        "keywords": ["available", "turn on", "activate", "start alerts", "i can donate", "ready to donate"],
        "description": "Turn on donation alerts"
    },
    "unavailable": {
        "keywords": ["unavailable", "turn off", "deactivate", "stop alerts", "cannot donate", "not available", "busy"],
        "description": "Turn off donation alerts"
    },
    "update": {
        "keywords": ["update", "edit profile", "change profile", "update profile", "modify profile", "change details"],
        "description": "Get profile update link"
    },
    "book_appointment": {
        "keywords": [
            "book appointment", "schedule appointment", "make appointment", 
            "want to donate", "i want to donate", "donation appointment",
            "book donation", "schedule donation", "make a donation",
            "i want to give blood", "need to donate", "donate blood",
            "booking", "appointment"
        ],
        "description": "Book a donation appointment"
    },
    "nearby_requests": {
        "keywords": ["nearby requests", "active requests", "blood requests near me", "any requests", "need blood"],
        "description": "Find nearby blood requests"
    },
    "donation_history": {
        "keywords": ["history", "past donations", "donation history", "my donations", "how many times"],
        "description": "View donation history"
    },
    "blood_type_info": {
        "keywords": ["blood type", "my blood type", "what is my blood type", "blood group"],
        "description": "Get blood type information"
    },
    "hospital_info": {
        "keywords": ["hospital near me", "nearby hospital", "closest hospital", "where to donate"],
        "description": "Find nearby hospitals"
    },
    "help": {
        "keywords": ["help", "commands", "what can you do", "how to use", "menu"],
        "description": "Show help menu"
    }
}

def detect_intent(message: str) -> Tuple[str, float]:
    """
    Detect intent from user message
    Returns: (intent_name, confidence_score)
    """
    message_lower = message.lower().strip()
    best_intent = "chat"
    best_score = 0.0
    
    for intent, config in INTENTS.items():
        score = 0
        for keyword in config["keywords"]:
            if keyword in message_lower:
                # Exact match gets higher score
                if keyword == message_lower:
                    score += 1.0
                # Word boundary match
                elif re.search(rf'\b{re.escape(keyword)}\b', message_lower):
                    score += 0.9
                # Partial match
                else:
                    score += 0.6
        
        if score > best_score:
            best_score = score
            best_intent = intent
    
    # Lower threshold for book_appointment to catch more variations
    if best_intent == "book_appointment" and best_score >= 0.4:
        return best_intent, best_score
    
    # Only return intent if confidence is high enough
    if best_score >= 0.5:
        return best_intent, best_score
    return "chat", best_score

def extract_entities(message: str, intent: str) -> Dict[str, Any]:
    """
    Extract entities from message based on intent
    """
    entities = {}
    message_lower = message.lower()
    
    if intent == "book_appointment":
        # Extract blood type
        blood_types = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
        for bt in blood_types:
            if bt.lower() in message_lower or bt in message:
                entities["blood_type"] = bt
                break
        
        # Extract date
        date_patterns = [
            (r'\btomorrow\b', 'tomorrow'),
            (r'\btoday\b', 'today'),
            (r'next (\w+)', None),
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', None)
        ]
        for pattern, _ in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["date"] = match.group(0)
                break
        
        # Extract time
        time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        match = re.search(time_pattern, message_lower)
        if match:
            entities["time"] = match.group(0)
    
    elif intent == "nearby_requests":
        # Extract radius
        radius_match = re.search(r'within (\d+) km', message_lower)
        if radius_match:
            entities["radius"] = int(radius_match.group(1))
        else:
            entities["radius"] = 50
    
    elif intent == "status":
        if "blood type" in message_lower:
            entities["detail"] = "blood_type"
        elif "score" in message_lower or "reliability" in message_lower:
            entities["detail"] = "reliability"
        elif "city" in message_lower or "location" in message_lower:
            entities["detail"] = "location"
    
    return entities