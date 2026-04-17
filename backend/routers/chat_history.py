# backend\routers\chat_history.py
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.chat_history import ChatMessage, MessageRole
import secrets
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

SESSION_DURATION_HOURS = 2

def generate_session_id() -> str:
    """Generate a unique session ID"""
    return secrets.token_urlsafe(32)

async def get_or_create_session(phone: str, donor_id: str, donor_name: str, db) -> dict:
    """Get existing active session or create new one"""
    now = datetime.utcnow()
    
    # Check for existing active session
    existing_session = await db.chat_sessions.find_one({
        "phone": phone,
        "is_active": True,
        "expires_at": {"$gt": now}
    })
    
    if existing_session:
        logger.info(f"Found existing session for {phone}: {existing_session['session_id']}")
        # Update last activity
        await db.chat_sessions.update_one(
            {"_id": existing_session["_id"]},
            {"$set": {"last_activity": now}}
        )
        return existing_session
    
    # Create new session
    session_id = generate_session_id()
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)
    
    # Get donor info
    donor = await db.donors.find_one({"_id": ObjectId(donor_id)})
    
    session_data = {
        "session_id": session_id,
        "phone": phone,
        "donor_id": donor_id,
        "donor_name": donor_name,
        "messages": [],
        "created_at": now,
        "expires_at": expires_at,
        "last_activity": now,
        "is_active": True,
        "context": {
            "donor_blood_type": donor.get("medical", {}).get("blood_type") if donor else None,
            "donor_city": donor.get("location", {}).get("city") if donor else None,
            "donor_active": donor.get("is_active", True) if donor else True
        }
    }
    
    result = await db.chat_sessions.insert_one(session_data)
    logger.info(f"Created new session for {phone}: {session_id}")
    
    # Add welcome message
    welcome_message = {
        "role": MessageRole.ASSISTANT.value,
        "content": "👋 Welcome to DonorPulse! I'm your blood donation assistant.\n\nYou can ask me about:\n• Blood donation eligibility\n• Appointment booking\n• Blood requests\n• Your donor status\n• And more!\n\nHow can I help you today?",
        "timestamp": now.isoformat()
    }
    
    await add_message_to_session(session_id, welcome_message, db)
    
    # Return the updated session
    return await db.chat_sessions.find_one({"session_id": session_id})

async def add_message_to_session(session_id: str, message: dict, db) -> bool:
    """Add a message to chat session"""
    try:
        result = await db.chat_sessions.update_one(
            {"session_id": session_id, "is_active": True},
            {
                "$push": {"messages": message},
                "$set": {"last_activity": datetime.utcnow()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Added message to session {session_id}: {message.get('role')}")
            return True
        else:
            logger.warning(f"Failed to add message to session {session_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding message to session: {e}")
        return False

async def get_session_messages(session_id: str, db, limit: int = 20) -> list:
    """Get recent messages from session"""
    session = await db.chat_sessions.find_one({"session_id": session_id, "is_active": True})
    if not session:
        logger.warning(f"Session not found: {session_id}")
        return []
    
    messages = session.get("messages", [])
    logger.info(f"Retrieved {len(messages)} messages from session {session_id}")
    return messages[-limit:]

async def update_session_context(session_id: str, context: dict, db):
    """Update session context"""
    await db.chat_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"context": context}}
    )

async def cleanup_expired_sessions(db):
    """Mark expired sessions as inactive"""
    result = await db.chat_sessions.update_many(
        {"expires_at": {"$lt": datetime.utcnow()}, "is_active": True},
        {"$set": {"is_active": False}}
    )
    return result.modified_count

@router.get("/session/{phone}")
async def get_chat_session(
    phone: str,
    db=Depends(get_db)
):
    """Get or create chat session for a donor"""
    try:
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        session = await get_or_create_session(phone, str(donor["_id"]), donor["name"], db)
        
        # Calculate expires in minutes
        expires_in = int((session["expires_at"] - datetime.utcnow()).total_seconds() / 60)
        
        return {
            "session_id": session["session_id"],
            "donor_name": donor["name"],
            "messages": session.get("messages", []),
            "expires_in_minutes": expires_in,
            "is_active": session["is_active"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat session")

@router.post("/message")
async def send_message(
    request: Request,
    db=Depends(get_db)
):
    """Send a message and get AI response with context"""
    try:
        data = await request.json()
        phone = data.get("phone")
        user_message = data.get("message", "").strip()
        
        if not phone or not user_message:
            raise HTTPException(status_code=400, detail="Phone and message are required")
        
        logger.info(f"Received message from {phone}: {user_message[:50]}...")
        
        # Get donor
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        # Get or create session
        session = await get_or_create_session(phone, str(donor["_id"]), donor["name"], db)
        session_id = session["session_id"]
        
        # Save user message
        user_msg = {
            "role": MessageRole.USER.value,
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        await add_message_to_session(session_id, user_msg, db)
        
        # Get ALL messages for full context
        all_messages = await get_session_messages(session_id, db, limit=50)
        
        # Build conversation history for AI
        conversation_history = []
        for msg in all_messages:
            conversation_history.append(f"{msg['role']}: {msg['content']}")
        
        conversation_text = "\n".join(conversation_history)
        
        # Get donor context
        donor_context = session.get("context", {})
        
        # Build prompt for AI
        prompt = f"""You are DonorPulse AI Assistant helping a blood donor.

Donor Information:
- Name: {donor['name']}
- Blood Type: {donor.get('medical', {}).get('blood_type')}
- City: {donor.get('location', {}).get('city')}
- Active Status: {'Active' if donor.get('is_active', True) else 'Inactive'}
- Reliability Score: {donor.get('reliability_score', 100)}/100

Previous Conversation:
{conversation_text}

Please provide a helpful, friendly response. Keep it concise. If the donor asks about commands, guide them to use STATUS, AVAILABLE, UPDATE, etc.

Donor: {user_message}

Assistant:"""
        
        # Get AI response
        from utils.llm_inference import get_llm_reponse
        ai_response = await get_llm_reponse(prompt)
        
        ai_response_text = ai_response.get("result", {}).get("response", "I'm sorry, I couldn't process that. Please try again or contact support.")
        
        # Save assistant message
        assistant_msg = {
            "role": MessageRole.ASSISTANT.value,
            "content": ai_response_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        await add_message_to_session(session_id, assistant_msg, db)
        
        logger.info(f"Sent response to {phone}: {ai_response_text[:50]}...")
        
        return {
            "message": ai_response_text,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/session/{session_id}")
async def clear_chat_session(
    session_id: str,
    db=Depends(get_db)
):
    """Clear chat session messages"""
    try:
        result = await db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"messages": [], "last_activity": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Add fresh welcome message
        welcome_message = {
            "role": MessageRole.ASSISTANT.value,
            "content": "Chat history cleared. How can I help you today?",
            "timestamp": datetime.utcnow().isoformat()
        }
        await add_message_to_session(session_id, welcome_message, db)
        
        return {"message": "Chat session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat session")

@router.get("/stats")
async def get_chat_stats(
    db=Depends(get_db)
):
    """Get chat system statistics"""
    try:
        total_sessions = await db.chat_sessions.count_documents({})
        active_sessions = await db.chat_sessions.count_documents({"is_active": True})
        
        # Count total messages across all sessions
        pipeline = [
            {"$unwind": "$messages"},
            {"$count": "total"}
        ]
        result = await db.chat_sessions.aggregate(pipeline).to_list(length=1)
        total_messages = result[0]["total"] if result else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages
        }
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")

@router.get("/messages/{session_id}")
async def get_session_messages_endpoint(
    session_id: str,
    limit: int = 20,
    db=Depends(get_db)
):
    """Get messages from a specific session"""
    try:
        session = await db.chat_sessions.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = session.get("messages", [])[-limit:]
        
        return {
            "session_id": session_id,
            "donor_name": session.get("donor_name"),
            "messages": messages,
            "total_messages": len(session.get("messages", [])),
            "expires_at": session.get("expires_at").isoformat() if session.get("expires_at") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")