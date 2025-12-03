from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from jose.exceptions import JWTError, ExpiredSignatureError
from app.database import Base, engine
from app.models import *
from app.api import auth, paths
from app.utils.exceptions import (
    custom_http_exception_handler,
    validation_exception_handler,
    jwt_exception_handler
)
from app.schemas.common import success_response

import logging

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Area API",
    version="1.0.0",
    description="산책 코스 추천 및 기록 관리 서비스"
)

# 예외 핸들러 등록
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(JWTError, jwt_exception_handler)
app.add_exception_handler(ExpiredSignatureError, jwt_exception_handler)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(paths.router)


# 앱 시작 시
@app.on_event("startup")
def startup_event():
    # 서버 시작 시 DB 연결 확인 및 테이블 생성 로그 출력
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connected & tables created successfully.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

@app.get("/")
def root():
    return success_response(data={"message": "Area API Server"}, message="서버가 정상 작동 중입니다.")
