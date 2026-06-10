from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    agent_reasoning_log = Column(JSON, nullable=True)  # maps to reasoning_trace
    action_type = Column(String, nullable=False)        # decision / action type
    proposed_content = Column(Text, nullable=True)      # draft_reply
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Extended triage fields
    recommended_action = Column(Text, nullable=True)
    auto_reply_allowed = Column(Boolean, default=False, nullable=False)
    requires_human_approval = Column(Boolean, default=True, nullable=False)
    escalation_team = Column(String, nullable=True)
    safety_level = Column(String, nullable=True)
    policy_sources = Column(JSON, nullable=True)
    status = Column(String, default="pending", nullable=False)

    # Relationships
    email = relationship("Email", backref="actions")

