from pydantic import BaseModel, Field, EmailStr
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

class AdminInDB(AdminBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: AdminRole
    is_active: bool