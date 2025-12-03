from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=True)
    profile_image = Column(String(500), default="default_profile.png")
    total_steps = Column(Integer, default=0)
    total_distance = Column(Float, default=0.0)  # km
    carbon_saved = Column(Float, default=0.0)  # kg
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paths = relationship("Path", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    walking_histories = relationship("WalkingHistory", back_populates="user", cascade="all, delete-orphan")
