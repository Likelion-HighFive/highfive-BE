from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.path import Path, PathImage, PathTag
from app.models.like import Like
from app.schemas.path import (
    PathResponse,
    PathListResponse,
    PathDetailResponse,
    PathImageResponse,
    FilterEnum,
    SortEnum,
)
from app.utils.dependencies import get_current_user
from app.utils.distance import calculate_distance, calculate_estimated_time
from app.utils.s3 import upload_image_to_s3
import json

router = APIRouter(prefix="/paths", tags=["paths"])


@router.post("", response_model=PathResponse, status_code=status.HTTP_201_CREATED)
async def create_path(
    name: str = Form(...),
    start_location: str = Form(...),
    end_location: str = Form(...),
    introduction: Optional[str] = Form(None),
    tags: str = Form(...),  # JSON string: ["감성길", "봄"]
    representative_image_index: int = Form(0),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    산책 코스 등록
    - 시작/끝 위치로 거리 자동 계산
    - 거리로 예상 소요 시간 자동 계산
    - 이미지 여러 개 업로드 (0개 가능)
    - 대표 이미지 선택
    """
    # 태그 파싱
    tags_list = json.loads(tags)

    # 거리 계산
    distance = calculate_distance(start_location, end_location)

    # 예상 소요 시간 계산
    estimated_time = calculate_estimated_time(distance)

    # 경로 생성
    new_path = Path(
        name=name,
        start_location=start_location,
        end_location=end_location,
        introduction=introduction,
        distance=distance,
        estimated_time=estimated_time,
        user_id=current_user.id
    )

    db.add(new_path)
    db.flush()

    # 태그 추가
    for tag in tags_list:
        path_tag = PathTag(path_id=new_path.id, tag_name=tag)
        db.add(path_tag)

    # 이미지 업로드 및 저장
    if images and len(images) > 0:
        for idx, image in enumerate(images):
            # S3 업로드
            image_url = await upload_image_to_s3(image, folder=f"paths/{new_path.id}")

            # DB 저장
            is_representative = 1 if idx == representative_image_index else 0
            path_image = PathImage(
                path_id=new_path.id,
                image_url=image_url,
                is_representative=is_representative
            )
            db.add(path_image)

    db.commit()
    db.refresh(new_path)

    # 응답 데이터 구성
    images_response = [PathImageResponse(
        id=img.id,
        image_url=img.image_url,
        is_representative=bool(img.is_representative)
    ) for img in new_path.images]

    tags_response = [tag.tag_name for tag in new_path.tags]

    return PathResponse(
        id=new_path.id,
        name=new_path.name,
        start_location=new_path.start_location,
        end_location=new_path.end_location,
        introduction=new_path.introduction,
        estimated_time=new_path.estimated_time,
        distance=new_path.distance,
        likes_count=new_path.likes_count,
        created_at=new_path.created_at,
        images=images_response,
        tags=tags_response
    )


@router.get("", response_model=List[PathListResponse])
def get_paths(
    filter: Optional[FilterEnum] = FilterEnum.ALL,
    sort: Optional[SortEnum] = SortEnum.LATEST,
    user_location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    산책 코스 목록 조회
    - 필터링: ALL, EMOTIONAL, CITY_VIEW, NATURE, NIGHT_VIEW, SAFE
    - 정렬: LATEST, RECOMMENDED, LIKES, DISTANCE
    """
    # 필터 매핑 (영어 -> 한글)
    filter_mapping = {
        FilterEnum.EMOTIONAL: "감성길",
        FilterEnum.CITY_VIEW: "씨티뷰길",
        FilterEnum.NATURE: "자연길",
        FilterEnum.NIGHT_VIEW: "야경길",
        FilterEnum.SAFE: "안전길"
    }

    query = db.query(Path)

    # 필터링
    if filter != FilterEnum.ALL:
        tag_name = filter_mapping.get(filter)
        if tag_name:
            query = query.join(PathTag).filter(PathTag.tag_name == tag_name)

    # 정렬
    if sort == SortEnum.LATEST:
        query = query.order_by(Path.created_at.desc())
    elif sort == SortEnum.LIKES:
        query = query.order_by(Path.likes_count.desc())
    elif sort == SortEnum.RECOMMENDED:
        # 추천순: 좋아요 수 + 최신순 조합 -> TODO: 추후 조정 필요
        query = query.order_by(Path.likes_count.desc(), Path.created_at.desc())
    elif sort == SortEnum.DISTANCE:
        # 거리순: 사용자 위치 기반 (user_location 필요)
        query = query.order_by(Path.distance.asc())

    paths = query.all()

    # 응답 데이터 구성
    result = []
    for path in paths:
        # 대표 이미지 찾기
        representative_image = db.query(PathImage).filter(
            PathImage.path_id == path.id,
            PathImage.is_representative == 1
        ).first()

        # 태그 목록
        tags = [tag.tag_name for tag in path.tags]

        result.append(PathListResponse(
            id=path.id,
            name=path.name,
            representative_image=representative_image.image_url if representative_image else None,
            estimated_time=path.estimated_time,
            distance=path.distance,
            likes_count=path.likes_count,
            tags=tags
        ))

    return result


@router.get("/{path_id}", response_model=PathDetailResponse)
def get_path_detail(
    path_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    산책 코스 상세 조회
    - 이미지 목록 (대표 이미지 포함)
    - 태그, 등록일, 소개글, 좋아요 개수
    - 시작/끝 위치
    """
    path = db.query(Path).filter(Path.id == path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다")

    # 좋아요 여부 확인
    is_liked = False
    if current_user:
        like = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.path_id == path_id
        ).first()
        is_liked = like is not None

    # 이미지 목록
    images = [PathImageResponse(
        id=img.id,
        image_url=img.image_url,
        is_representative=bool(img.is_representative)
    ) for img in path.images]

    # 태그 목록
    tags = [tag.tag_name for tag in path.tags]

    # 날짜 포맷 변환 (yyyy.mm.dd)
    created_at_str = path.created_at.strftime("%Y.%m.%d")

    return PathDetailResponse(
        id=path.id,
        name=path.name,
        start_location=path.start_location,
        end_location=path.end_location,
        introduction=path.introduction,
        estimated_time=path.estimated_time,
        distance=path.distance,
        likes_count=path.likes_count,
        created_at=created_at_str,
        images=images,
        tags=tags,
        is_liked=is_liked
    )
