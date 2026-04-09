"""
대본 생성 라우터 — POST /api/script
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import script_service

router = APIRouter()


class ScriptRequest(BaseModel):
    topic: str = Field(..., description="쇼츠 주제 또는 키워드", min_length=1)
    style: str = Field(default="유머", description="대본 스타일 (유머, 정보, 감동 등)")
    duration: Literal[30, 60, 90] = Field(default=60, description="영상 길이(초) — 30, 60 또는 90")


class ScriptResponse(BaseModel):
    script: str = Field(..., description="생성된 대본 (장면은 --- 구분자로 분리)")
    scene_count: int = Field(..., description="총 장면 수")
    subtitles: list[str] = Field(default=[], description="자막 문장 리스트 (||| 구분)")


@router.post("/script", response_model=ScriptResponse)
async def generate_script(body: ScriptRequest) -> ScriptResponse:
    """AI 대본 생성 — Gemini 2.5 Flash"""
    try:
        script_text, scene_count, subtitles = await script_service.generate_script(
            body.topic, body.style, body.duration
        )
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    return ScriptResponse(script=script_text, scene_count=scene_count, subtitles=subtitles)
