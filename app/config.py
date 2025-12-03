from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # MySQL Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "area"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10485760

    # Server
    DEBUG: bool = True

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
