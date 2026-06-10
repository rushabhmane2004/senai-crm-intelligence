from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    agent_reasoning_log = Column(JSON, nullable=True)
    action_type = Column(String, nullable=False)
    proposed_content = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    email = relationship("Email", backref="actions")
