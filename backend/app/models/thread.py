from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)
    subject = Column(String, nullable=False)
    sender_email = Column(String, nullable=False)
    first_seen_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    status = Column(String, default="Open")  # Open, Resolved, Escalated, Ignored
    assigned_to = Column(String, nullable=True)
