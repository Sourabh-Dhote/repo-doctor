import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False)
    severity = Column(String, nullable=False)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    suggestion = Column(Text, nullable=True)

    analysis = relationship("Analysis", back_populates="issues")
