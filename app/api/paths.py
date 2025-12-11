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
    PathLikeStatusResponse,
)
from app.schemas.common import ApiResponse, created_response, success_response
from app.utils.dependencies import get_current_user, get_optional_user
from app.utils.distance import calculate_distance, calculate_estimated_time
from app.utils.s3 import upload_image_to_s3
import json

router = APIRouter(prefix="/paths", tags=["paths"])


@router.post(
    "",
    response_model=ApiResponse[PathResponse],
    status_code=status.HTTP_201_CREATED,
    summary="산책 코스 등록",
    description="거리/시간 자동 계산, S3 이미지 업로드, 태그 JSON 배열"
)
async def create_path(
    name: str = Form(...),
    start_location: str = Form(...),
    end_location: str = Form(...),
    introduction: Optional[str] = Form(None),
    tags: str = Form(...),
    representative_image_index: int = Form(0),
    images: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    path_response = PathResponse(
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

    return created_response(data=path_response, message="산책 코스가 등록되었습니다.")


@router.get(
    "",
    response_model=ApiResponse[List[PathListResponse]],
    summary="산책 코스 목록 조회",
    description="필터링 · 정렬 · 검색 지원"
)
def get_paths(
        filter: Optional[FilterEnum] = FilterEnum.ALL,
        sort: Optional[SortEnum] = SortEnum.LATEST,
        search: Optional[str] = None,   # 검색 추가
        user_location: Optional[str] = None,
        current_user: Optional[User] = Depends(get_optional_user),
        db: Session = Depends(get_db)
):
    # 필터 매핑
    filter_mapping = {
        FilterEnum.EMOTIONAL: "감성길",
        FilterEnum.CITY_VIEW: "씨티뷰길",
        FilterEnum.NATURE: "자연길",
        FilterEnum.NIGHT_VIEW: "야경길",
        FilterEnum.SAFE: "안전길"
    }

    query = db.query(Path)

    # 검색 기능
    if search:
        query = query.filter(Path.name.ilike(f"%{search}%"))

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
        query = query.order_by(Path.likes_count.desc(), Path.created_at.desc())
    elif sort == SortEnum.DISTANCE:
        query = query.order_by(Path.distance.asc())

    paths = query.all()

    # 응답 구성
    result = []
    for path in paths:
        representative_image = db.query(PathImage).filter(
            PathImage.path_id == path.id,
            PathImage.is_representative == 1
        ).first()

        tags = [tag.tag_name for tag in path.tags]

        is_liked = False
        if current_user:
            like = db.query(Like).filter(
                Like.user_id == current_user.id,
                Like.path_id == path.id
            ).first()
            is_liked = like is not None

        result.append(PathListResponse(
            id=path.id,
            name=path.name,
            representative_image=representative_image.image_url if representative_image else None,
            estimated_time=path.estimated_time,
            distance=path.distance,
            likes_count=path.likes_count,
            tags=tags,
            is_liked=is_liked
        ))

    return success_response(data=result, message="산책 코스 목록 조회가 완료되었습니다.")

@router.post(
    "/{path_id}/like-toggle",
    response_model=ApiResponse[PathLikeStatusResponse],
    summary="산책 코스 좋아요 토글",
    description="이미 좋아요한 코스면 좋아요를 취소하고, 아니라면 좋아요를 등록합니다."
)

def toggle_path_like(
    path_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 코스 존재 여부 확인
    path = db.query(Path).filter(Path.id == path_id).first()
    if not path:
        raise HTTPException(status_code=404, detail="코스를 찾을 수 없습니다")

    # 기존 좋아요 있는지 확인
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.path_id == path_id
    ).first()

    # 좋아요가 이미 있으면 → 취소
    if existing_like:
        db.delete(existing_like)
        # likes_count 감소 (0 아래로 내려가지 않게 보호)
        path.likes_count = max(0, (path.likes_count or 0) - 1)
        is_liked = False
        message = "좋아요가 취소되었습니다."
    else:
        # 없으면 → 새로 등록
        new_like = Like(user_id=current_user.id, path_id=path_id)
        db.add(new_like)
        path.likes_count = (path.likes_count or 0) + 1
        is_liked = True
        message = "좋아요가 등록되었습니다."

    db.commit()
    db.refresh(path)

    like_status = PathLikeStatusResponse(
        path_id=path.id,
        is_liked=is_liked,
        likes_count=path.likes_count or 0
    )

    return success_response(
        data=like_status,
        message=message
    )
    
@router.get(
    "/likes",
    response_model=ApiResponse[List[PathListResponse]],
    summary="좋아요한 산책 코스 목록 조회(기존)",
    description="사용자가 좋아요한 산책 코스만 모아 조회합니다."
)
def get_liked_paths(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자가 좋아요한 산책 코스 목록을 반환
    - PathListResponse 포맷을 재사용
    - is_liked는 항상 True
    """

    # 좋아요한 path_id 목록
    liked_path_ids_subquery = (
        db.query(Like.path_id)
        .filter(Like.user_id == current_user.id)
        .subquery()
    )

    # 해당 path들만 조회
    paths = (
        db.query(Path)
        .filter(Path.id.in_(liked_path_ids_subquery))
        .order_by(Path.created_at.desc())
        .all()
    )

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
            tags=tags,
            is_liked=True  # ✅ 좋아요 목록이므로 항상 True
        ))

    return success_response(
        data=result,
        message="좋아요한 산책 코스 목록 조회가 완료되었습니다."
    )

@router.get(
    "/liked",
    response_model=ApiResponse[List[PathListResponse]],
    summary="좋아요한 산책 코스 목록 조회 (검색/필터/정렬 지원 - 추가된 api!!)",
    description="JWT 인증된 사용자가 좋아요한 코스만 전체 조회 방식으로 필터링/검색/정렬하여 반환합니다."
)
def get_liked_paths_advanced(
        filter: Optional[FilterEnum] = FilterEnum.ALL,
        sort: Optional[SortEnum] = SortEnum.LATEST,
        search: Optional[str] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 좋아요 기반 목록 조회
    liked_path_ids = (
        db.query(Like.path_id)
        .filter(Like.user_id == current_user.id)
        .subquery()
    )

    query = db.query(Path).filter(Path.id.in_(liked_path_ids))

    # 검색
    if search:
        query = query.filter(Path.name.ilike(f"%{search}%"))

    # 필터(태그)
    filter_mapping = {
        FilterEnum.EMOTIONAL: "감성길",
        FilterEnum.CITY_VIEW: "씨티뷰길",
        FilterEnum.NATURE: "자연길",
        FilterEnum.NIGHT_VIEW: "야경길",
        FilterEnum.SAFE: "안전길"
    }

    if filter != FilterEnum.ALL:
        tag = filter_mapping.get(filter)
        if tag:
            query = query.join(PathTag).filter(PathTag.tag_name == tag)

    # 정렬
    if sort == SortEnum.LATEST:
        query = query.order_by(Path.created_at.desc())
    elif sort == SortEnum.LIKES:
        query = query.order_by(Path.likes_count.desc())
    elif sort == SortEnum.RECOMMENDED:
        query = query.order_by(Path.likes_count.desc(), Path.created_at.desc())
    elif sort == SortEnum.DISTANCE:
        query = query.order_by(Path.distance.asc())

    paths = query.all()

    result = []
    for path in paths:
        rep = db.query(PathImage).filter(
            PathImage.path_id == path.id,
            PathImage.is_representative == 1
        ).first()

        tags = [tag.tag_name for tag in path.tags]

        result.append(PathListResponse(
            id=path.id,
            name=path.name,
            representative_image=rep.image_url if rep else None,
            estimated_time=path.estimated_time,
            distance=path.distance,
            likes_count=path.likes_count,
            tags=tags,
            is_liked=True
        ))

    return success_response(
        data=result,
        message="좋아요한 산책 코스 목록 조회가 완료되었습니다."
    )



@router.get(
    "/{path_id}",
    response_model=ApiResponse[PathDetailResponse],
    summary="산책 코스 상세 조회",
    description="전체 이미지, 코스 타입, 좋아요 여부 포함"
)
def get_path_detail(
    path_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

    # 종류 (감성길, 씨티뷰길, 자연길, 야경길, 안전길만 필터링)
    path_type_list = ["감성길", "씨티뷰길", "자연길", "야경길", "안전길"]
    path_types = [tag.tag_name for tag in path.tags if tag.tag_name in path_type_list]

    # 날짜 포맷 변환 (yyyy.mm.dd)
    created_at_str = path.created_at.strftime("%Y.%m.%d")

    path_detail = PathDetailResponse(
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
        path_types=path_types,
        is_liked=is_liked
    )

    return success_response(data=path_detail, message="산책 코스 상세 조회가 완료되었습니다.")
