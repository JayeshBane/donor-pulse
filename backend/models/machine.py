# backend\models\machine.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, time
from enum import Enum
from bson import ObjectId

class MachineType(str, Enum):
    WHOLE_BLOOD = "whole_blood"
    PLATELET = "platelet"
    PLASMA = "plasma"
    DOUBLE_RBC = "double_rbc"
    MULTI_PURPOSE = "multi_purpose"

class MachineStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    OFFLINE = "offline"

class MachineMaintenanceType(str, Enum):
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    EMERGENCY = "emergency"
    CLEANING = "cleaning"
    CALIBRATION = "calibration"

class MachineBase(BaseModel):
    machine_id: str
    machine_type: MachineType
    name: str
    description: Optional[str] = None
    donation_types: List[str]
    max_daily_donations: int = 10
    slot_duration_minutes: int = 30
    buffer_minutes: int = 15
    status: MachineStatus = MachineStatus.AVAILABLE
    current_donor_id: Optional[str] = None
    current_appointment_id: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    operating_start: str = "09:00"
    operating_end: str = "17:00"
    is_active: bool = True  # Default to True, but hospital can change
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MachineCreate(BaseModel):
    machine_id: str
    machine_type: MachineType
    name: str
    description: Optional[str] = None
    donation_types: List[str]
    max_daily_donations: Optional[int] = 10
    slot_duration_minutes: Optional[int] = 30
    buffer_minutes: Optional[int] = 15
    floor: Optional[str] = None
    room: Optional[str] = None
    operating_start: Optional[str] = "09:00"
    operating_end: Optional[str] = "17:00"
    
    @validator('donation_types')
    def validate_donation_types(cls, v):
        valid_types = ['whole_blood', 'platelets', 'plasma', 'double_rbc']
        for dt in v:
            if dt not in valid_types:
                raise ValueError(f'Invalid donation type: {dt}')
        return v

class MachineInDB(MachineBase):
    id: str = Field(alias="_id")
    hospital_id: str
    hospital_name: Optional[str] = None

class MachineMaintenanceLog(BaseModel):
    machine_id: str
    hospital_id: str
    maintenance_type: MachineMaintenanceType
    description: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    performed_by: str  # staff name or ID
    cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MachineStatusUpdate(BaseModel):
    status: MachineStatus
    reason: Optional[str] = None

class MachineSchedule(BaseModel):
    machine_id: str
    date: str  # YYYY-MM-DD
    slots: List[dict]  # List of time slots with availability
    total_slots: int
    booked_slots: int
    available_slots: int

class BulkMachineCreate(BaseModel):
    machines: List[MachineCreate]
    hospital_id: str