# backend\models\chat_history.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModel):
    session_id: str
    phone: str
    donor_id: str
    donor_name: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    context: Optional[dict] = None

class ChatSessionCreate(BaseModel):
    phone: str
    donor_id: str
    donor_name: str
    session_id: str

class ChatSessionResponse(BaseModel):
    session_id: str
    donor_name: str
    messages: List[ChatMessage]
    expires_in_minutes: int
    is_active: bool