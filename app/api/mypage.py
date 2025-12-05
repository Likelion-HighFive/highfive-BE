from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse, success_response
from app.schemas.user import (
    UserProfileResponse,
    UserNicknameUpdate,
)
from app.utils.dependencies import get_current_user
from app.utils.s3 import upload_image_to_s3, delete_image_from_s3

router = APIRouter(prefix="/mypage", tags=["mypage"])


# -----------------------------------
# 1) 프로필 조회 API
# -----------------------------------
@router.get(
    "/profile",
    response_model=ApiResponse[UserProfileResponse],
    summary="마이페이지 프로필 조회",
    description="사용자 정보(닉네임, 프로필 이미지, 걸음수, 거리, 탄소 절감량 등)를 조회합니다."
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    user_profile = UserProfileResponse.from_orm(current_user)
    return success_response(data=user_profile, message="프로필 조회가 완료되었습니다.")


# -----------------------------------
# 2) 닉네임 변경 API
# -----------------------------------
@router.patch(
    "/nickname",
    response_model=ApiResponse[UserProfileResponse],
    summary="닉네임 변경",
    description="사용자의 닉네임을 변경합니다."
)
def update_nickname(
    payload: UserNicknameUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.nickname = payload.nickname
    db.commit()
    db.refresh(current_user)

    return success_response(
        data=UserProfileResponse.from_orm(current_user),
        message="닉네임이 성공적으로 변경되었습니다."
    )


# -----------------------------------
# 3) 프로필 이미지 변경 API
# -----------------------------------
@router.patch(
    "/profile-image",
    response_model=ApiResponse[UserProfileResponse],
    summary="프로필 이미지 변경",
    description="사용자의 프로필 이미지를 변경합니다. 기존 이미지가 있을 경우 S3에서 삭제합니다."
)
async def update_profile_image(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 기존 이미지 삭제 (default 이미지면 삭제 X)
    if current_user.profile_image and current_user.profile_image != "default_profile.png":
        try:
            await delete_image_from_s3(current_user.profile_image)
        except:
            pass

    # 새 이미지 업로드
    new_image_url = await upload_image_to_s3(image, folder=f"profiles/{current_user.id}")

    current_user.profile_image = new_image_url
    db.commit()
    db.refresh(current_user)

    return success_response(
        data=UserProfileResponse.from_orm(current_user),
        message="프로필 이미지가 성공적으로 변경되었습니다."
    )
