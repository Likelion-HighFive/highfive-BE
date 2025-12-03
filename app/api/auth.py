from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserSignup, UserLogin, Token, UserResponse
from app.schemas.common import ApiResponse, created_response, success_response
from app.utils.auth import (
    verify_password,
    get_password_hash,
    validate_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    회원가입
    - 이메일 중복 검사
    - 비밀번호 유효성 검사 (영문, 숫자 포함 8자리 이상)
    """
    # 이메일 중복 검사
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )

    # 비밀번호 유효성 검사
    if not validate_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 영문, 숫자 포함 8자리 이상이어야 합니다"
        )

    # 사용자 생성
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password=hashed_password,
        profile_image="default_profile.png"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_response = UserResponse.from_orm(new_user)
    return created_response(data=user_response, message="회원가입이 완료되었습니다.")


@router.post("/login", response_model=ApiResponse[Token])
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    로그인
    - 이메일과 비밀번호로 인증
    - JWT 액세스 토큰 반환
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다"
        )

    # 비밀번호 확인
    if not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다"
        )

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.email})
    token_response = Token(access_token=access_token, token_type="bearer")

    return success_response(data=token_response, message="로그인이 완료되었습니다.")
