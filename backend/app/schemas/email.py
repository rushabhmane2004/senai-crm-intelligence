from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, EmailStr

class EmailIngestPayload(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    sender: EmailStr = Field(..., description="Valid email address of the sender")
    subject: Optional[str] = Field(None, description="Email subject")
    body: Optional[str] = Field(None, description="Email body content")
    timestamp: datetime = Field(..., description="Timestamp of when the email was sent")
    thread_id: str = Field(..., description="External thread identifier")

class EmailIngestResponse(BaseModel):
    email_id: Optional[int] = Field(None, description="Database ID of the email")
    message_id: str = Field(..., description="Unique message identifier")
    thread_id: str = Field(..., description="External thread identifier")
    status: str = Field(..., description="Ingestion status (e.g. Received, duplicate_ignored)")
    priority_score: int = Field(..., description="Priority score calculated (0 to 3)")

class EmailStatusResponse(BaseModel):
    message_id: str
    status: str
    category: Optional[str] = None
    urgency: Optional[str] = None
    priority_score: Optional[int] = None
    requires_human: Optional[bool] = None
    confidence: Optional[float] = None
    raw_entities: Optional[Dict[str, Any]] = None
    sender: Optional[str] = None
    body: Optional[str] = None
    subject: Optional[str] = None

    # Compact agent fields
    agent_decision: Optional[str] = None
    auto_reply_allowed: Optional[bool] = None
    requires_human_approval: Optional[bool] = None
    escalation_team: Optional[str] = None
    safety_level: Optional[str] = None




# Schema definitions for GET /threads/{contact_email}
class ActionSchema(BaseModel):
    id: int
    email_id: int
    agent_reasoning_log: Optional[Any] = None
    action_type: str
    proposed_content: Optional[str] = None
    is_approved: bool
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EmailSchema(BaseModel):
    id: int
    thread_id: int
    message_id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime
    priority_score: int
    sentiment_score: Optional[float] = None
    category: Optional[str] = None
    urgency: Optional[str] = None
    requires_human: Optional[bool] = None
    confidence: Optional[float] = None
    raw_entities: Optional[Any] = None
    status: str
    created_at: datetime
    actions: List[ActionSchema] = []

    class Config:
        from_attributes = True

class ThreadSchema(BaseModel):
    id: int
    thread_id: str
    subject: str
    sender_email: str
    first_seen_at: datetime
    last_updated_at: datetime
    status: str
    assigned_to: Optional[str] = None
    emails: List[EmailSchema] = []

    class Config:
        from_attributes = True

class ContactProfile(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    status: str
    account_value: float
    churn_risk_score: float
    created_at: datetime
    last_contact_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContactHistoryResponse(BaseModel):
    contact: ContactProfile
    threads: List[ThreadSchema]

# Dashboard stats response
class DashboardStatsResponse(BaseModel):
    total_emails: int
    pending_emails: int
    spam_emails: int
    escalated_emails: int
    critical_emails: int
    total_contacts: int
    total_threads: int
