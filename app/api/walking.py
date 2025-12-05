from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.walking_history import WalkingHistory
from app.schemas.walking import WalkingStatsResponse
from app.schemas.common import ApiResponse, success_response
from app.utils.dependencies import get_current_user
from app.utils.distance import calculate_carbon_saved

router = APIRouter(prefix="/walking", tags=["walking"])

#현재 user_id 기준으로 WalkingHistory를 조회해서 COOUT 및 SUM을 수행
@router.get(
    "/summary",
    response_model=ApiResponse[WalkingStatsResponse],
    summary="누적 산책 통계 조회",
    description="사용자의 전체 산책 기록을 집계하여 총 산책 횟수, 완료 횟수, 누적 걸음 수, 누적 거리(km), 탄소 절감량(kg)을 반환합니다."
)
def get_walking_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    누적 산책 통계 조회
    - 집계 방식: 매 요청 시 WalkingHistory 테이블에서 SUM/COUNT 수행
    """

    # 1) 총 산책 횟수
    total_walks = (
        db.query(func.count(WalkingHistory.id))
        .filter(WalkingHistory.user_id == current_user.id)
        .scalar()
        or 0
    )

    # 2) 완료된 산책 횟수
    completed_walks = (
        db.query(func.count(WalkingHistory.id))
        .filter(
            WalkingHistory.user_id == current_user.id,
            WalkingHistory.is_completed.is_(True),
        )
        .scalar()
        or 0
    )

    # 3) 누적 걸음 수, 누적 거리(m)
    total_steps, total_distance_m = (
        db.query(
            func.coalesce(func.sum(WalkingHistory.steps), 0),
            func.coalesce(func.sum(WalkingHistory.distance), 0),
        )
        .filter(WalkingHistory.user_id == current_user.id)
        .one()
    )

    # distance는 m 단위이므로 km로 변환
    total_distance_km = round(total_distance_m / 1000.0, 2) if total_distance_m else 0.0

    # km -> 탄소 절감량(kg)
    total_carbon_saved_kg = calculate_carbon_saved(total_distance_km)

    stats_response = WalkingStatsResponse(
        total_walks=total_walks,
        completed_walks=completed_walks,
        total_steps=total_steps,
        total_distance_km=total_distance_km,
        total_carbon_saved_kg=total_carbon_saved_kg,
    )

    return success_response(
        data=stats_response,
        message="누적 산책 통계 조회가 완료되었습니다.",
    )