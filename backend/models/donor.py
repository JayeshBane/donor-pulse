from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class BloodType(str, Enum):
    O_NEGATIVE = "O-"
    O_POSITIVE = "O+"
    A_NEGATIVE = "A-"
    A_POSITIVE = "A+"
    B_NEGATIVE = "B-"
    B_POSITIVE = "B+"
    AB_NEGATIVE = "AB-"
    AB_POSITIVE = "AB+"

class DonationType(str, Enum):
    WHOLE_BLOOD = "whole_blood"
    PLATELETS = "platelets"
    PLASMA = "plasma"
    DOUBLE_RBC = "double_rbc"

class Availability(str, Enum):
    MORNING = "Morning"
    AFTERNOON = "Afternoon"
    EVENING = "Evening"
    NIGHT = "Night"

class NotifyType(str, Enum):
    ROUTINE = "Routine"
    URGENT = "Urgent"
    CRITICAL = "Critical"
    SOS = "SOS"

class DonorPreferences(BaseModel):
    contact_method: str = "sms"
    availability: List[Availability] = []
    language: str = "en"
    notify_types: List[NotifyType] = [NotifyType.ROUTINE, NotifyType.URGENT, NotifyType.CRITICAL, NotifyType.SOS]
    transport_available: bool = False

class DonorMedical(BaseModel):
    blood_type: BloodType
    donation_types: List[DonationType] = [DonationType.WHOLE_BLOOD]
    weight_kg: float
    illnesses: List[str] = []
    medications: List[str] = []
    last_donation_date: Optional[datetime] = None

class DonorLocation(BaseModel):
    phone: str
    email: Optional[EmailStr] = None
    address: str
    city: str
    pin_code: str
    lat: Optional[float] = None
    lng: Optional[float] = None

class DonorBase(BaseModel):
    name: str
    age: int
    gender: str
    photo_url: Optional[str] = None
    is_active: bool = True
    is_paused: bool = False
    pause_expiry: Optional[datetime] = None
    reliability_score: int = 100
    total_alerts_sent: int = 0
    total_alerts_responded: int = 0
    total_donations_confirmed: int = 0
    total_donations_completed: int = 0
    
    @validator('age')
    def validate_age(cls, v):
        if v < 18 or v > 65:
            raise ValueError('Age must be between 18 and 65')
        return v

class DonorCreate(DonorBase):
    medical: DonorMedical
    location: DonorLocation
    preferences: DonorPreferences = DonorPreferences()

class DonorInDB(DonorCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def is_on_cooldown(self) -> bool:
        if not self.medical.last_donation_date:
            return False
        cooldown_days = 56
        return datetime.utcnow() < self.medical.last_donation_date + timedelta(days=cooldown_days)
    
    @property
    def can_receive_alerts(self) -> bool:
        return (self.is_active and 
                not self.is_paused and 
                not self.is_on_cooldown)