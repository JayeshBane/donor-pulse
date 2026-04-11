# backend\models\appointment.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time, timedelta
from enum import Enum
import secrets

class AppointmentType(str, Enum):
    SCHEDULED = "scheduled"
    WALK_IN = "walk_in"
    EMERGENCY = "emergency"

class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentBase(BaseModel):
    donor_id: str
    donor_name: str
    donor_phone: str
    hospital_id: str
    hospital_name: str
    machine_id: str
    machine_name: str
    appointment_type: AppointmentType = AppointmentType.SCHEDULED
    appointment_date: datetime
    appointment_time: str  # HH:MM format
    donation_type: str
    status: AppointmentStatus = AppointmentStatus.BOOKED
    notes: Optional[str] = None

class AppointmentCreate(BaseModel):
    donor_id: str
    hospital_id: str
    machine_id: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    donation_type: str
    notes: Optional[str] = None
    
    @validator('appointment_date')
    def validate_date(cls, v):
        try:
            # Validate date format
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    @validator('appointment_time')
    def validate_time(cls, v):
        try:
            # Validate time format
            datetime.strptime(v, "%H:%M")
            return v
        except:
            raise ValueError("Invalid time format. Use HH:MM")
    
    @validator('donor_id', 'hospital_id', 'machine_id')
    def validate_object_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError(f"Invalid ID: {v}")
        return v

class AppointmentInDB(AppointmentBase):
    id: str = Field(alias="_id")
    booking_token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    checked_in_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None

class TimeSlot(BaseModel):
    date: str
    time: str
    machine_id: str
    machine_name: str
    available: bool
    donor_name: Optional[str] = None

class WalkInCreate(BaseModel):
    donor_name: str
    donor_phone: str
    hospital_id: str
    donation_type: str
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: str
    donor_name: str
    donor_phone: str
    hospital_name: str
    machine_name: str
    appointment_date: str
    appointment_time: str
    donation_type: str
    status: str
    booking_token: str
    created_at: str

class WaitlistEntry(BaseModel):
    donor_id: str
    donor_name: str
    donor_phone: str
    hospital_id: str
    donation_type: str
    requested_time: datetime
    status: str = "waiting"
    notified_at: Optional[datetime] = None
    expires_at: datetime