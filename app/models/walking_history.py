from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# 걷기 기록
class WalkingHistory(Base):
    __tablename__ = "walking_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    path_id = Column(Integer, ForeignKey("paths.id"), nullable=False)
    steps = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False) # seconds
    distance = Column(Integer, nullable=False) # meters
    is_completed = Column(Boolean, default=False)
    walked_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="walking_histories")
    path = relationship("Path", back_populates="walking_histories")
