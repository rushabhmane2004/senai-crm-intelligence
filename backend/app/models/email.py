from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False)
    message_id = Column(String, unique=True, index=True, nullable=False)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    priority_score = Column(Integer, default=0, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    category = Column(String, nullable=True)
    urgency = Column(String, nullable=True)
    requires_human = Column(Boolean, nullable=True)
    confidence = Column(Float, nullable=True)
    raw_entities = Column(JSON, nullable=True)
    status = Column(String, default="Received")  # Received, Processing, Replied, Escalated, Ignored, Spam
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    thread = relationship("Thread", backref="emails")
