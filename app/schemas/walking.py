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

class WalkingSessionStartResponse(BaseModel):
    """
    걷기 세션 시작 시 내려줄 응답
    - session_id: WalkingHistory.id
    - path_id: 어떤 코스를 걷는지
    """
    session_id: int
    path_id: int

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
    total_steps: int = 0
    total_distance_km: float = 0.0
    total_carbon_saved_kg: float = 0.0
#기존 DTO 충돌 방지를 위해 total_walks, completed_walks 만 세팅해도 검증 에러 발생 X