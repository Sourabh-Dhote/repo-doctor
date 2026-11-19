import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    cloned_at = Column(DateTime, default=get_utc_now)
    total_files = Column(Integer, default=0)
    languages = Column(JSON, default=dict)
    
    analyses = relationship("Analysis", back_populates="repository")
