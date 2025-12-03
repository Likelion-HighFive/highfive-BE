from pydantic import BaseModel
from typing import Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    isSuccess: bool
    code: str
    httpStatus: int
    message: str
    data: Optional[T] = None
    timeStamp: str

    class Config:
        from_attributes = True


def success_response(data: T, message: str = "요청이 성공적으로 처리되었습니다.", code: str = "SUCCESS_200") -> ApiResponse[T]:
    """성공 응답 생성"""
    return ApiResponse(
        isSuccess=True,
        code=code,
        httpStatus=200,
        message=message,
        data=data,
        timeStamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def created_response(data: T, message: str = "리소스가 성공적으로 생성되었습니다.", code: str = "CREATED_201") -> ApiResponse[T]:
    """생성 성공 응답"""
    return ApiResponse(
        isSuccess=True,
        code=code,
        httpStatus=201,
        message=message,
        data=data,
        timeStamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def error_response(message: str, code: str, http_status: int = 400) -> ApiResponse:
    """에러 응답 생성"""
    return ApiResponse(
        isSuccess=False,
        code=code,
        httpStatus=http_status,
        message=message,
        data=None,
        timeStamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
