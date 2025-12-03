from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.models import *
from app.api import auth, paths

import logging

# 로깅
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="Area API", version="1.0.0")

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
    return {"message": "Area API Server"}
