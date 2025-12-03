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
    ALL = "ALL"
    EMOTIONAL = "EMOTIONAL"
    CITY_VIEW = "CITY_VIEW"
    NATURE = "NATURE"
    NIGHT_VIEW = "NIGHT_VIEW"
    SAFE = "SAFE"


class SortEnum(str, Enum):
    LATEST = "LATEST"
    RECOMMENDED = "RECOMMENDED"
    LIKES = "LIKES"
    DISTANCE = "DISTANCE"

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
