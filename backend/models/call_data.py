from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class EmergencyType(str, Enum):
    FIRE = "FIRE"
    MEDICAL = "MEDICAL"
    CRIME = "CRIME"
    ACCIDENT = "ACCIDENT"
    DISASTER = "DISASTER"
    UNKNOWN = "UNKNOWN"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RoutingDecision(BaseModel):
    department: str
    confidence: float


class CallData(BaseModel):
    call_id: str
    timestamp: datetime
    transcript: str
    predicted_class: EmergencyType
    severity: SeverityLevel
    routing_decision: RoutingDecision
    confidence: float
    explanation: str
    location: Optional[str] = None
    emotion_meter: Optional[float] = None
    noise_confidence: Optional[float] = None
    extracted_entities: Optional[Dict[str, Any]] = {}