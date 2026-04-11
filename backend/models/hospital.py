from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class HospitalType(str, Enum):
    GOVERNMENT = "government"
    PRIVATE = "private"
    TRUST = "trust"
    MILITARY = "military"

class HospitalLocation(BaseModel):
    address: str
    city: str
    pin_code: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class HospitalOperational(BaseModel):
    departments: Optional[List[str]] = []
    monthly_blood_units: Optional[int] = 0
    blood_bank_available: Optional[bool] = False
    operating_hours: Optional[str] = "24/7"

class HospitalBase(BaseModel):
    name: str
    type: HospitalType
    license_number: str
    email: EmailStr
    phone: str
    username: str
    location: HospitalLocation
    operational: Optional[HospitalOperational] = None
    is_verified: Optional[bool] = False
    is_active: Optional[bool] = True

class HospitalCreate(HospitalBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class HospitalInDB(HospitalBase):
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class HospitalLogin(BaseModel):
    username: str
    password: str

class HospitalResponse(BaseModel):
    id: str
    name: str
    type: HospitalType
    email: EmailStr
    phone: str
    username: str
    city: str
    is_verified: bool
    is_active: bool