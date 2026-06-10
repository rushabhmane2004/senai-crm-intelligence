from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(String, default="Active")  # VIP, Blocked, Active, Churned
    account_value = Column(Float, default=0.0, nullable=False)
    churn_risk_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_contact_at = Column(DateTime, nullable=True)
