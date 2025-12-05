from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.walking_history import WalkingHistory
from app.models.path import Path
from app.schemas.walking import (
    WalkingStart,
    WalkingEnd,
    WalkingSessionStartResponse,
    WalkingHistoryResponse,
    WalkingStatsResponse,
)
from app.schemas.common import ApiResponse, success_response, created_response
from app.utils.dependencies import get_current_user
from app.utils.distance import calculate_carbon_saved

router = APIRouter(prefix="/walking", tags=["walking"])


@router.post(
    "/start",
    response_model=ApiResponse[WalkingSessionStartResponse],
    status_code=status.HTTP_201_CREATED,
    summary="산책 세션 시작",
    description="산책 세션을 시작하고 sessionId를 발급합니다.",
)
def start_walking_session(
    body: WalkingStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    산책 세션 시작
    - WalkingHistory에 빈 세션(steps=0, duration=0, distance=0, is_completed=False) 생성
    - 생성된 id를 session_id로 반환
    """

    # 안정성을 위해서 path 존재 여부 검증
    path = db.query(Path).filter(Path.id == body.path_id).first()
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="산책 코스를 찾을 수 없습니다.",
        )

    new_history = WalkingHistory(
        user_id=current_user.id,
        path_id=body.path_id,
        steps=0,
        duration=0,
        distance=0,
        is_completed=False,
        walked_at=datetime.utcnow(),
    )

    db.add(new_history)
    db.commit()
    db.refresh(new_history)

    response = WalkingSessionStartResponse(
        session_id=new_history.id,
        path_id=new_history.path_id,
    )

    return created_response(
        data=response,
        message="산책 세션이 시작되었습니다.",
    )


@router.post(
    "/{session_id}/end",
    response_model=ApiResponse[WalkingHistoryResponse],
    summary="산책 세션 종료",
    description="걸음 수, 시간, 이동 거리, 완료 여부를 저장하고 사용자 누적 데이터를 업데이트합니다.",
)
def end_walking_session(
    session_id: int,
    body: WalkingEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    산책 세션 종료
    - 해당 세션에 steps, duration, distance, is_completed 업데이트
    - User.total_steps, User.total_distance, User.carbon_saved 누적 업데이트
    """

    # 세션 조회 (본인 것만)
    history = (
        db.query(WalkingHistory)
        .filter(
            WalkingHistory.id == session_id,
            WalkingHistory.user_id == current_user.id,
        )
        .first()
    )

    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="산책 세션을 찾을 수 없습니다.",
        )

    # Path 이름 사용을 위해 관계 접근
    path = history.path
    if not path:
        path = db.query(Path).filter(Path.id == history.path_id).first()

    # WalkingHistory 업데이트
    history.steps = body.steps
    history.duration = body.duration
    history.distance = body.distance  # meters
    history.is_completed = body.is_completed
    history.walked_at = datetime.utcnow()

    # User 누적 값 업데이트
    user = current_user

    # steps 누적
    user.total_steps = (user.total_steps or 0) + body.steps

    # distance 누적 (m -> km)
    delta_distance_km = round(body.distance / 1000.0, 2)
    user.total_distance = round((user.total_distance or 0.0) + delta_distance_km, 2)

    # 탄소 절감량 누적 (거리 기반)
    delta_carbon_kg = calculate_carbon_saved(delta_distance_km)
    user.carbon_saved = round((user.carbon_saved or 0.0) + delta_carbon_kg, 2)

    db.commit()
    db.refresh(history)
    db.refresh(user)

    history_response = WalkingHistoryResponse(
        id=history.id,
        path_id=history.path_id,
        path_name=path.name if path else "",
        steps=history.steps,
        duration=history.duration,
        distance=history.distance,
        is_completed=history.is_completed,
        walked_at=history.walked_at,
    )

    return success_response(
        data=history_response,
        message="산책 세션이 종료되었습니다.",
    )


# 아래부터는 기존 summary API 그대로 유지
@router.get(
    "/summary",
    response_model=ApiResponse[WalkingStatsResponse],
    summary="누적 산책 통계 조회",
    description="사용자의 전체 산책 기록을 집계하여 총 산책 횟수, 완료 횟수, 누적 걸음 수, 누적 거리(km), 탄소 절감량(kg)을 반환합니다.",
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
