from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TokenType(str, Enum):
    MAGIC_LINK = "magic_link"
    PASSWORD_RESET = "password_reset"
    LOCATION = "location"

class UpdateToken(BaseModel):
    """Token for donor profile updates (magic link)"""
    token: str
    donor_id: str
    token_type: TokenType = TokenType.MAGIC_LINK
    expires_at: datetime
    is_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PasswordResetToken(BaseModel):
    """Token for password reset"""
    token: str
    hospital_id: str
    expires_at: datetime
    is_used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RateLimit(BaseModel):
    """Rate limiting for donor updates"""
    donor_phone: str
    update_count: int = 0
    last_update_date: datetime = Field(default_factory=datetime.utcnow)