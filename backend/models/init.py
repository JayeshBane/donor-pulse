# backend\models\__init__.py
from .donor import DonorCreate, DonorInDB, DonorMedical, DonorLocation, DonorPreferences
from .hospital import HospitalCreate, HospitalInDB, HospitalLogin, HospitalResponse
from .token import UpdateToken, PasswordResetToken, RateLimit, TokenType
from .machine import (
    MachineType, MachineStatus, MachineMaintenanceType,
    MachineBase, MachineCreate, MachineInDB, 
    MachineMaintenanceLog, MachineStatusUpdate, MachineSchedule,
    BulkMachineCreate
)
from .appointment import (
    AppointmentType, AppointmentStatus,
    AppointmentBase, AppointmentCreate, AppointmentInDB,
    TimeSlot, WalkInCreate, AppointmentResponse, WaitlistEntry
)

from .chat_history import ChatMessage, ChatSession, ChatSessionCreate, ChatSessionResponse, MessageRole

__all__ = [
    "DonorCreate",
    "DonorInDB", 
    "DonorMedical",
    "DonorLocation",
    "DonorPreferences",
    "HospitalCreate",
    "HospitalInDB",
    "HospitalLogin",
    "HospitalResponse",
    "UpdateToken",
    "PasswordResetToken",
    "RateLimit",
    "TokenType",
    "MachineType",
    "MachineStatus", 
    "MachineMaintenanceType",
    "MachineBase",
    "MachineCreate",
    "MachineInDB",
    "MachineMaintenanceLog",
    "MachineStatusUpdate",
    "MachineSchedule",
    "BulkMachineCreate",
    "AppointmentType",
    "AppointmentStatus",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentInDB",
    "TimeSlot",
    "WalkInCreate",
    "AppointmentResponse",
    "WaitlistEntry",
    "ChatMessage",
    "ChatSession", 
    "ChatSessionCreate",
    "ChatSessionResponse",
    "MessageRole"
]