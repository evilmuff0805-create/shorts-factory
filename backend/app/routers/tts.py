"""
TTS 음성 생성 라우터 — POST /api/tts
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import tts_service

router = APIRouter()


class TtsRequest(BaseModel):
    script: str = Field(..., description="음성으로 변환할 대본 텍스트", min_length=1)
    voice: str = Field(
        default="changsu", description="Typecast voice key (changsu, dabin, inhwa, hana)"
    )


class TtsResponse(BaseModel):
    audio: str = Field(..., description="base64 인코딩된 MP3 음성 데이터")
    duration_estimate: float = Field(..., description="예상 재생 시간(초) — 글자수 기반 추정")


@router.post("/tts", response_model=TtsResponse)
async def generate_tts(body: TtsRequest) -> TtsResponse:
    """대본 → TTS 음성 생성 — OpenAI TTS-1"""
    try:
        audio_b64, duration_estimate = await tts_service.generate_tts(body.script, body.voice)
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    return TtsResponse(audio=audio_b64, duration_estimate=duration_estimate)
