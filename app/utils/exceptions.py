from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from jose.exceptions import JWTError, ExpiredSignatureError
from app.schemas.common import error_response
from datetime import datetime


async def custom_http_exception_handler(request: Request, exc: Exception):
    """HTTPException 핸들러"""
    if hasattr(exc, 'status_code'):
        status_code = exc.status_code
        detail = exc.detail if hasattr(exc, 'detail') else str(exc)
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = "Internal server error"

    # 에러 코드 매핑
    error_code_mapping = {
        400: "BAD_REQUEST_400",
        401: "UNAUTHORIZED_401",
        403: "FORBIDDEN_403",
        404: "NOT_FOUND_404",
        422: "VALIDATION_ERROR_422",
        500: "INTERNAL_SERVER_ERROR_500"
    }

    error_code = error_code_mapping.get(status_code, f"ERROR_{status_code}")

    response = error_response(
        message=detail,
        code=error_code,
        http_status=status_code
    )

    return JSONResponse(
        status_code=status_code,
        content=response.dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation 에러 핸들러"""
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error['loc'])
        msg = error['msg']
        error_messages.append(f"{field}: {msg}")

    response = error_response(
        message="; ".join(error_messages),
        code="VALIDATION_ERROR_422",
        http_status=422
    )

    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def jwt_exception_handler(request: Request, exc: Exception):
    """JWT 에러 핸들러"""
    if isinstance(exc, ExpiredSignatureError):
        response = error_response(
            message="만료된 JWT 토큰입니다.",
            code="JWT_401_EXPIRED",
            http_status=401
        )
    else:
        response = error_response(
            message="유효하지 않은 JWT 토큰입니다.",
            code="JWT_401_INVALID",
            http_status=401
        )

    return JSONResponse(
        status_code=401,
        content=response.dict()
    )
