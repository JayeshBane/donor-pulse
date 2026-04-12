from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime, timedelta
from bson import ObjectId
from database import get_db
from models.chat_history import ChatSession, ChatMessage, MessageRole, ChatSessionCreate
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
        # Update last activity
        await db.chat_sessions.update_one(
            {"_id": existing_session["_id"]},
            {"$set": {"last_activity": now}}
        )
        return existing_session
    
    # Create new session
    session_id = generate_session_id()
    expires_at = now + timedelta(hours=SESSION_DURATION_HOURS)
    
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
        "context": {}
    }
    
    await db.chat_sessions.insert_one(session_data)
    
    # Add welcome message
    welcome_message = ChatMessage(
        role=MessageRole.ASSISTANT,
        content="👋 Welcome to DonorPulse! I'm your blood donation assistant.\n\nYou can ask me about:\n• Blood donation eligibility\n• Appointment booking\n• Blood requests\n• Your donor status\n• And more!\n\nHow can I help you today?"
    )
    
    await add_message_to_session(session_id, welcome_message, db)
    
    return session_data

async def add_message_to_session(session_id: str, message: ChatMessage, db) -> bool:
    """Add a message to chat session"""
    result = await db.chat_sessions.update_one(
        {"session_id": session_id, "is_active": True},
        {
            "$push": {"messages": message.dict()},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )
    return result.modified_count > 0

async def get_session_messages(session_id: str, db, limit: int = 20) -> list:
    """Get recent messages from session"""
    session = await db.chat_sessions.find_one({"session_id": session_id, "is_active": True})
    if not session:
        return []
    
    messages = session.get("messages", [])
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
        
        # Get donor
        donor = await db.donors.find_one({"location.phone": phone})
        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")
        
        # Get or create session
        session = await get_or_create_session(phone, str(donor["_id"]), donor["name"], db)
        session_id = session["session_id"]
        
        # Save user message
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=user_message
        )
        await add_message_to_session(session_id, user_msg, db)
        
        # Get recent messages for context
        recent_messages = await get_session_messages(session_id, db, limit=10)
        
        # Build context for AI
        context = f"""You are DonorPulse AI Assistant helping a blood donor.
        
Donor Info:
- Name: {donor['name']}
- Blood Type: {donor.get('medical', {}).get('blood_type')}
- City: {donor.get('location', {}).get('city')}
- Active: {donor.get('is_active', True)}

Recent conversation:
{chr(10).join([f"{m['role']}: {m['content']}" for m in recent_messages])}

Please respond helpfully and concisely. If the donor asks about their status, appointments, or blood requests, guide them to use specific commands like STATUS, AVAILABLE, UPDATE, etc.
"""
        
        # Get AI response
        from utils.llm_inference import get_llm_reponse
        ai_response = await get_llm_reponse(context + f"\n\nDonor: {user_message}\n\nAssistant:")
        
        ai_response_text = ai_response.get("result", {}).get("response", "I'm sorry, I couldn't process that. Please try again or contact support.")
        
        # Save assistant message
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=ai_response_text
        )
        await add_message_to_session(session_id, assistant_msg, db)
        
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
        total_messages = await db.chat_sessions.aggregate([
            {"$unwind": "$messages"},
            {"$count": "total"}
        ]).to_list(length=1)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages[0]["total"] if total_messages else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")