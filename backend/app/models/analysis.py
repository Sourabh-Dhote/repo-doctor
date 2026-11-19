import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="pending")
    health_score = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    started_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    repository = relationship("Repository", back_populates="analyses")
    issues = relationship("Issue", back_populates="analysis", cascade="all, delete-orphan")
