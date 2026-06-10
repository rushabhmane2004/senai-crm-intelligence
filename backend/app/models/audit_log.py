from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    performed_by = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    diff = Column(JSON, nullable=True)
