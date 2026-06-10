from sqlalchemy import Column, Integer, String, DateTime, JSON, func
from app.database import Base


class WebIntelligenceCache(Base):
    __tablename__ = "web_intelligence_cache"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, nullable=True)          # e.g. "offline_mock_reputation_intelligence"
    target_entity = Column(String, index=True, nullable=False)  # e.g. "retail-co.com"
    scraped_data = Column(JSON, nullable=True)           # Full mock/scraped payload
    scraped_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
