# backend\models\admin.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VIEWER = "viewer"

class AdminBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: AdminRole = AdminRole.ADMIN
    is_active: bool = True

class AdminCreate(AdminBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer')
        return v

class AdminInDB(AdminBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class AdminLogin(BaseModel):
    username: str
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 72 bytes or fewer')
        return v

class AdminResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: AdminRole
    is_active: bool
