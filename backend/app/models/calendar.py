# FILE: backend/app/models/calendar.py
# PHOENIX PROTOCOL - CALENDAR MODEL V9.1 (ACCOUNTING ENUMS)
# 1. REFACTOR: EventType Enum updated to Accounting standards (TAX_DEADLINE, PAYMENT_DUE, etc.).
# 2. CLEANUP: Removed Legal Enums (HEARING, COURT_DATE, FILING).
# 3. STATUS: Backend Validation synchronized with Frontend Types.

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId 

class EventType(str, Enum):
    # Accounting / Fiscal Types
    TAX_DEADLINE = "TAX_DEADLINE"   # Critical: VAT (TVSH), Corporate Tax (TAK), Declarations
    PAYMENT_DUE = "PAYMENT_DUE"     # Important: Invoices, Salaries, Utilities, Accounts Payable
    APPOINTMENT = "APPOINTMENT"     # Standard: Client meetings
    TASK = "TASK"                   # Routine: Internal bookkeeping, Reconciliations
    OTHER = "OTHER"                 # Fallback

class EventCategory(str, Enum):
    # PHOENIX: Separates Actionable Items from Metadata
    AGENDA = "AGENDA"  # Appears in Calendar (Deadlines, Payments)
    FACT = "FACT"      # Metadata only (Invoice dates, Transaction logs)

class EventPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EventStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class CalendarEventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    start_date: datetime
    end_date: Optional[datetime] = None
    is_all_day: bool = False
    event_type: EventType = EventType.TASK # Default changed to Accounting Task
    category: EventCategory = EventCategory.AGENDA 
    priority: EventPriority = EventPriority.MEDIUM
    location: Optional[str] = Field(None, max_length=100)
    attendees: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)

class CalendarEventCreate(CalendarEventBase):
    case_id: PyObjectId

    @field_validator('case_id', mode='before')
    @classmethod
    def validate_case_id(cls, v):
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception:
                raise ValueError(f"Invalid ObjectId string: {v}")
        elif isinstance(v, ObjectId):
            return v
        else:
            raise ValueError(f"Expected string or ObjectId, got {type(v)}")

class CalendarEventInDB(CalendarEventBase):
    id: PyObjectId = Field(alias="_id")
    owner_id: PyObjectId 
    case_id: str 
    document_id: Optional[str] = None 
    status: EventStatus = EventStatus.PENDING
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(populate_by_name=True)

class CalendarEventOut(CalendarEventInDB):
    working_days_remaining: Optional[int] = None
    severity: Optional[str] = None
    effective_deadline: Optional[datetime] = None
    is_extended: bool = False
    risk_level: Optional[str] = None