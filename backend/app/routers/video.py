"""
이미지 애니메이션 라우터 — POST /api/animate
"""

import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import video_service

router = APIRouter()


class AnimateRequest(BaseModel):
    images: list[str] = Field(..., description="이미지 base64 목록", min_length=1)


class AnimateResponse(BaseModel):
    clips: list[str] = Field(..., description="동영상 클립 base64 목록 (MP4)")


@router.post("/animate", response_model=AnimateResponse)
async def animate_images(body: AnimateRequest) -> AnimateResponse:
    """이미지들을 MiniMax Hailuo로 동영상 클립으로 변환"""
    try:
        video_bytes_list = await video_service.animate_images(body.images)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    clips_b64 = [base64.b64encode(vb).decode("utf-8") for vb in video_bytes_list]
    return AnimateResponse(clips=clips_b64)
