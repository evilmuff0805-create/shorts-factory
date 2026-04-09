"""
영상 합성 라우터 — POST /api/render
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import render_service

router = APIRouter()


class RenderRequest(BaseModel):
    images: list[str] = Field(..., description="장면별 이미지 base64 목록", min_length=1)
    audio: str = Field(..., description="음성 파일 base64 (MP3)")
    subtitles: list[str] = Field(default=[], description="장면별 자막 텍스트 목록")
    fps: int = Field(default=30, ge=24, le=60, description="프레임레이트")


class RenderResponse(BaseModel):
    video: str = Field(..., description="합성된 영상 base64 (MP4)")
    duration: float = Field(..., description="영상 재생 시간(초)")


@router.post("/render", response_model=RenderResponse)
async def render_video(body: RenderRequest) -> RenderResponse:
    """이미지 + 음성 + 자막 → 1080×1920 MP4 합성 — FFmpeg"""
    try:
        video_b64, duration = await render_service.render_video(
            body.images, body.audio, body.subtitles, body.fps
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return RenderResponse(video=video_b64, duration=duration)
