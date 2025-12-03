import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException
from app.config import get_settings
import uuid
from datetime import datetime

settings = get_settings()


def get_s3_client():
    """S3 클라이언트 생성"""
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )


async def upload_image_to_s3(file: UploadFile, folder: str = "paths") -> str:
    """
    이미지를 S3에 업로드하고 URL 반환

    Args:
        file: 업로드할 파일
        folder: S3 내 폴더 경로

    Returns:
        S3 URL
    """
    # 파일 크기 검증
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다")

    # 파일 확장자 검증
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
        )

    # 고유한 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{folder}/{timestamp}_{uuid.uuid4().hex[:8]}.{file_extension}"

    try:
        # S3 업로드
        s3_client = get_s3_client()
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=unique_filename,
            Body=contents,
            ContentType=file.content_type
        )

        # S3 URL 반환
        s3_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
        return s3_url

    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")
    finally:
        await file.seek(0)


async def delete_image_from_s3(image_url: str) -> bool:
    """
    S3에서 이미지 삭제

    Args:
        image_url: 삭제할 이미지 URL

    Returns:
        삭제 성공 여부
    """
    try:
        # URL에서 키 추출
        key = image_url.split('.amazonaws.com/')[-1]

        s3_client = get_s3_client()
        s3_client.delete_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key
        )
        return True

    except ClientError as e:
        print(f"S3 삭제 실패: {str(e)}")
        return False
