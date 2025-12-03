from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# 길 정보
class Path(Base):
    __tablename__ = "paths"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    start_location = Column(String(500), nullable=False)  
    end_location = Column(String(500), nullable=False)  
    introduction = Column(Text, nullable=True)
    estimated_time = Column(Integer, nullable=False)  # 분 단위
    distance = Column(Float, nullable=False) # km
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="paths")
    images = relationship("PathImage", back_populates="path", cascade="all, delete-orphan")
    tags = relationship("PathTag", back_populates="path", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="path", cascade="all, delete-orphan")
    walking_histories = relationship("WalkingHistory", back_populates="path", cascade="all, delete-orphan")


# 이미지
class PathImage(Base):
    __tablename__ = "path_images"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("paths.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    is_representative = Column(Integer, default=0) # 대표 사진 여부 (0: False, 1: True)

    # Relationships
    path = relationship("Path", back_populates="images")


# 태그
class PathTag(Base):
    __tablename__ = "path_tags"

    id = Column(Integer, primary_key=True, index=True)
    path_id = Column(Integer, ForeignKey("paths.id"), nullable=False)
    tag_name = Column(String(50), nullable=False)  # 감성길, 씨티뷰길, 자연길, 야경길, 안전길, 여름, 겨울, 가을, 봄 등

    # Relationships
    path = relationship("Path", back_populates="tags")
