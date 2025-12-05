from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="영문, 숫자 포함 8자리 이상")
    nickname: Optional[str] = Field(None, min_length=1, max_length=50)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    nickname: Optional[str] = None  # 로그인 시에도 nickname을 받을 수 있게 대응 (실제 사용 X)

class UserResponse(BaseModel):
    id: int
    email: str
    nickname: Optional[str]
    profile_image: str
    total_steps: int
    total_distance: float
    carbon_saved: float
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    profile_image: Optional[str] = None


class CarbonInfo(BaseModel):
    total_steps: int
    total_distance: float  # km
    carbon_saved: float  # kg

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserProfileResponse(BaseModel):
    id: int
    email: EmailStr
    nickname: Optional[str]
    profile_image: str
    total_steps: int
    total_distance: float
    carbon_saved: float
    created_at: datetime

    class Config:
        from_attributes = True


class UserNicknameUpdate(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=50)


class UserProfileImageUpdate(BaseModel):
    profile_image: str