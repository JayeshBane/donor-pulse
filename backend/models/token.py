# backend/models/token.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TokenType(str, Enum):
    MAGIC_LINK = "magic_link"
    PASSWORD_RESET = "password_reset"
    LOCATION = "location"

class UpdateToken(BaseModel):
    """Token for donor profile updates (magic link) - deleted after use"""
    hashed_token: str
    donor_id: str
    token_type: TokenType = TokenType.MAGIC_LINK
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # No is_used field - tokens are deleted instead

class PasswordResetToken(BaseModel):
    """Token for password reset - deleted after use"""
    hashed_token: str
    hospital_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # No is_used field - tokens are deleted instead

class RateLimit(BaseModel):
    """Rate limiting for donor updates"""
    donor_phone: str
    update_count: int = 0
    last_update_date: datetime = Field(default_factory=datetime.utcnow)