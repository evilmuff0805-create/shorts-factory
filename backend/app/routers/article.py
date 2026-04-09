"""
기사 분석 라우터 — POST /api/article/analyze, POST /api/article/generate
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import article_service, script_service, image_service, tts_service, render_service, video_service

router = APIRouter(prefix="/article")


# ===== 요청/응답 모델 =====

class AnalyzeRequest(BaseModel):
    title: str = Field(default="", description="기사 제목 (선택)")
    body: str = Field(..., description="기사 본문 텍스트", min_length=10)


class AnalyzeResponse(BaseModel):
    title: str = Field(..., description="기사 제목")
    url: str = Field(..., description="원본 기사 URL")
    summary: str = Field(..., description="기사 요약 (3~5문장)")
    key_points: list[str] = Field(..., description="핵심 포인트 목록")
    suggested_topics: list[str] = Field(..., description="추천 쇼츠 주제 목록")


class GenerateRequest(BaseModel):
    topic: str = Field(..., description="쇼츠 주제 (추천 주제 중 선택 또는 직접 입력)")
    style: str = Field(default="트렌드", description="콘텐츠 스타일")
    duration: int = Field(default=30, description="영상 길이 (30/60/90초)")
    voice: str = Field(default="changsu", description="TTS 음성")
    image_style: str = Field(default="pixar3d", description="이미지 스타일")
    article_context: str = Field(default="", description="기사 요약 (대본 품질 향상용)")
    animate: bool = Field(default=False, description="이미지 애니메이션 적용 여부")


class GenerateResponse(BaseModel):
    video: str = Field(..., description="base64 MP4 영상")
    duration: float = Field(..., description="영상 길이 (초)")
    script: str = Field(..., description="생성된 대본")
    subtitles: list[str] = Field(..., description="자막 목록")


# ===== 엔드포인트 =====

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_article(body: AnalyzeRequest) -> AnalyzeResponse:
    """
    기사 텍스트 → Gemini 분석
    """
    if len(body.body.strip()) < 10:
        raise HTTPException(status_code=400, detail="기사 본문이 너무 짧습니다. 최소 10자 이상 입력해주세요.")

    # Gemini 분석
    try:
        analysis = await article_service.analyze_article(
            title=body.title or "제목 없음",
            body=body.body[:3000],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"기사 분석 실패: {e}")

    return AnalyzeResponse(
        title=body.title or "제목 없음",
        url="",
        summary=analysis["summary"],
        key_points=analysis["key_points"],
        suggested_topics=analysis["suggested_topics"],
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_from_article(body: GenerateRequest) -> GenerateResponse:
    """
    기사 분석 결과 기반 쇼츠 생성 파이프라인
    주제 → 대본 → 이미지 → TTS → 영상 렌더링
    """
    # 기사 맥락이 있으면 주제에 포함
    topic = body.topic
    if body.article_context:
        topic = f"{body.topic}\n\n[참고 기사 요약]\n{body.article_context[:500]}"

    # 1. 대본 생성
    try:
        image_section, scene_count, subtitles = await script_service.generate_script(
            topic=topic,
            style=body.style,
            duration=body.duration,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"대본 생성 실패: {e}")

    # 2. 이미지 생성
    try:
        images_result = await image_service.generate_images(
            image_section,
            image_style=body.image_style,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"이미지 생성 실패: {e}")

    images_b64 = images_result

    # 3. TTS 생성
    try:
        audio_b64, audio_duration = await tts_service.generate_tts(script="\n".join(subtitles), voice=body.voice)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS 생성 실패: {e}")

    # 3.5. 이미지 애니메이션 (선택)
    if body.animate:
        try:
            video_clips = await video_service.animate_images(images_b64)
            import base64 as b64mod
            images_b64 = [b64mod.b64encode(clip).decode("utf-8") for clip in video_clips]
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"이미지 애니메이션 실패: {e}")

    # 4. 영상 렌더링
    try:
        video_b64, video_duration = await render_service.render_video(
            images_b64, audio_b64, subtitles
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"영상 렌더링 실패: {e}")

    return GenerateResponse(
        video=video_b64,
        duration=video_duration,
        script=image_section,
        subtitles=subtitles,
    )
