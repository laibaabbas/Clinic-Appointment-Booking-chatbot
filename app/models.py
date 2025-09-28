from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from langchain.memory import ConversationBufferMemory
class Doctor(BaseModel):
    id: str
    name: str
    specialization: str
    slots: List[str]

class Clinic(BaseModel):
    name: str
    code: str
    address: str
    hours: str
    contact: str

class ClinicData(BaseModel):
    clinic: Clinic
    doctors: List[Doctor]

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Appointment(BaseModel):
    appointment_id: Optional[str] = None
    patient_name: str
    patient_age: int
    doctor_id: str
    doctor_name: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    status: AppointmentStatus = AppointmentStatus.PENDING
    created_at: Optional[str] = None
    
    class Config:
        use_enum_values = True

class ConversationState(BaseModel):
    current_step: str = "greeting"
    collected_data: Dict[str, Any] = {}
    missing_info: List[str] = []
    appointment: Optional[Appointment] = None
    memory: Optional[ConversationBufferMemory] = None
    
    class Config:
        arbitrary_types_allowed = True