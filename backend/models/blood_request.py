# backend\models\blood_request.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
from bson import ObjectId

class UrgencyLevel(str, Enum):
    ROUTINE = "routine"      # Standard request, 50km radius
    URGENT = "urgent"        # Need within 24 hours, progressive radius
    CRITICAL = "critical"    # Need within 6 hours, wider radius
    SOS = "sos"              # Emergency, city-wide broadcast

class RequestStatus(str, Enum):
    PENDING = "pending"              # Waiting for donors
    MATCHING = "matching"            # Currently finding donors
    BROADCASTING = "broadcasting"    # Sending alerts
    FULFILLED = "fulfilled"          # Enough donors found
    PARTIAL = "partial"              # Some donors found, still need more
    EXPIRED = "expired"              # Request expired
    CANCELLED = "cancelled"          # Cancelled by hospital

class DonorResponseStatus(str, Enum):
    PENDING = "pending"      # Donor hasn't responded
    ACCEPTED = "accepted"    # Donor is coming
    DECLINED = "declined"    # Donor cannot come
    TIMEOUT = "timeout"      # Didn't respond in time
    ARRIVED = "arrived"      # Donor reached hospital
    DONATED = "donated"      # Donation completed

class BloodRequestBase(BaseModel):
    hospital_id: str
    hospital_name: str
    blood_type: str  # O-, O+, A-, A+, B-, B+, AB-, AB+
    quantity_units: int = 1  # Number of units needed
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    reason: Optional[str] = None  # Reason for request
    patient_info: Optional[dict] = None  # Anonymous patient info
    expires_at: datetime

class BloodRequestCreate(BaseModel):
    hospital_id: str
    blood_type: str
    quantity_units: int = 1
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    reason: Optional[str] = None
    patient_info: Optional[dict] = None
    
    @validator('blood_type')
    def validate_blood_type(cls, v):
        valid_types = ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
        if v not in valid_types:
            raise ValueError(f'Invalid blood type. Must be one of {valid_types}')
        return v
    
    @validator('quantity_units')
    def validate_quantity(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Quantity must be between 1 and 50 units')
        return v

class BloodRequestInDB(BloodRequestBase):
    id: str = Field(alias="_id")
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    fulfilled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    
    # Tracking
    donors_contacted: int = 0
    donors_accepted: int = 0
    donors_declined: int = 0
    donors_timeout: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

class MatchedDonor(BaseModel):
    request_id: str
    donor_id: str
    donor_name: str
    donor_phone: str
    donor_blood_type: str
    distance_km: float
    reliability_score: int
    travel_time_minutes: int
    score: float  # Combined score for prioritization
    status: DonorResponseStatus = DonorResponseStatus.PENDING
    contacted_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    eta_minutes: Optional[int] = None
    
class DonorResponse(BaseModel):
    donor_id: str
    request_id: str
    response: DonorResponseStatus
    eta_minutes: Optional[int] = None
    notes: Optional[str] = None