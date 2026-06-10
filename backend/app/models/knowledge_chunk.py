from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_doc = Column(String, index=True, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_hash = Column(String, unique=True, index=True, nullable=False)
    embedding_model = Column(String, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
