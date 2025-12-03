from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TagEnum(str, Enum):
    EMOTIONAL = "감성길"
    CITY_VIEW = "씨티뷰길"
    NATURE = "자연길"
    NIGHT_VIEW = "야경길"
    SAFE = "안전길"
    SPRING = "봄"
    SUMMER = "여름"
    FALL = "가을"
    WINTER = "겨울"


class FilterEnum(str, Enum):
    ALL = "전체"
    EMOTIONAL = "감성길"
    CITY_VIEW = "씨티뷰길"
    NATURE = "자연길"
    NIGHT_VIEW = "야경길"


class SortEnum(str, Enum):
    LATEST = "최신순"
    RECOMMENDED = "추천순"
    LIKES = "좋아요순"
    DISTANCE = "거리순"
    # 인기순은 시간 관계상 미구현

class PathImageCreate(BaseModel):
    image_url: str
    is_representative: bool = False


class PathImageResponse(BaseModel):
    id: int
    image_url: str
    is_representative: bool

    class Config:
        from_attributes = True


class PathCreate(BaseModel):
    name: str
    start_location: str
    end_location: str
    introduction: Optional[str] = None
    tags: List[TagEnum]


class PathResponse(BaseModel):
    id: int
    name: str
    start_location: str
    end_location: str
    introduction: Optional[str]
    estimated_time: int
    distance: float
    likes_count: int
    created_at: datetime
    images: List[PathImageResponse]
    tags: List[str]

    class Config:
        from_attributes = True


class PathListResponse(BaseModel):
    id: int
    name: str
    representative_image: Optional[str]
    estimated_time: int
    distance: float
    likes_count: int
    tags: List[str]

    class Config:
        from_attributes = True


class PathDetailResponse(BaseModel):
    id: int
    name: str
    start_location: str
    end_location: str
    introduction: Optional[str]
    estimated_time: int
    distance: float
    likes_count: int
    created_at: str  # yyyy.mm.dd 형식
    images: List[PathImageResponse]
    tags: List[str]
    is_liked: bool

    class Config:
        from_attributes = True
