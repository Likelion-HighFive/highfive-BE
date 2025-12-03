from pydantic import BaseModel
from datetime import datetime


class WalkingStart(BaseModel):
    path_id: int


class WalkingEnd(BaseModel):
    path_id: int
    steps: int
    duration: int 
    distance: int
    is_completed: bool


class WalkingHistoryResponse(BaseModel):
    id: int
    path_id: int
    path_name: str
    steps: int
    duration: int
    distance: int
    is_completed: bool
    walked_at: datetime

    class Config:
        from_attributes = True


class WalkingStatsResponse(BaseModel):
    total_walks: int
    completed_walks: int
