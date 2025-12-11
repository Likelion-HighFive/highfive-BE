from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import decode_access_token

security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    JWT 토큰에서 현재 사용자 정보를 가져옴
    """
    token = credentials.credentials
    token_data = decode_access_token(token)

    if token_data is None or token_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 정보가 유효하지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db),
):
    if not authorization:
        return None

    try:
        token = authorization.replace("Bearer ", "")
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == payload["user_id"]).first()
        return user
    except Exception:
        return None  # 토큰이 잘못되었어도 그냥 '비로그인'으로 처리