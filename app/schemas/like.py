from pydantic import BaseModel


class LikeCreate(BaseModel):
    path_id: int


class LikeResponse(BaseModel):
    message: str
    is_liked: bool
