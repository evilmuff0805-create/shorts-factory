"""
뉴스 쇼츠 자동 생성 라우터 — POST /api/news-shorts
Google News RSS 수집 → Gemini 대본 → 이미지 → TTS → FFmpeg 합성
"""

import re

import feedparser
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import image_service, render_service, script_service, tts_service

router = APIRouter()

# Google News RSS URL 템플릿 (한국어)
_GNEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

# count 기준 비용 경고 임계값
_COST_WARNING_THRESHOLD = 5

# 뉴스 쇼츠당 예상 이미지 수 (60초 기준 6~8장면 → 평균 6)
_AVG_SCENES_PER_SHORT = 6
_IMAGE_COST_PER = 0.009  # gpt-image-1 low quality


# ===== 모델 =====

class NewsShortsRequest(BaseModel):
    category: str = Field(default="", description="뉴스 카테고리 (선택)")
    keyword: str = Field(..., description="검색 키워드", min_length=1)
    count: int = Field(default=3, ge=1, le=10, description="생성할 쇼츠 수")


class NewsShortItem(BaseModel):
    title: str = Field(..., description="원본 뉴스 기사 제목")
    video: str = Field(..., description="생성된 쇼츠 base64 MP4")
    script: str = Field(..., description="AI 생성 대본")


class NewsShortsResponse(BaseModel):
    news_shorts: list[NewsShortItem] = Field(..., description="생성된 뉴스 쇼츠 목록")
    skipped: int = Field(default=0, description="처리 실패로 스킵된 항목 수")
    warning: str | None = Field(default=None, description="비용 경고 메시지")


# ===== 헬퍼 =====

def _strip_html(text: str) -> str:
    """feedparser 요약에 포함된 HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", text).strip()


def _fetch_news(keyword: str, category: str, count: int) -> list[dict[str, str]]:
    """
    Google News RSS에서 뉴스 수집.
    반환: [{"title": ..., "summary": ...}, ...]
    """
    query = f"{category} {keyword}".strip() if category else keyword
    url = _GNEWS_RSS.format(query=query.replace(" ", "+"))

    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"RSS 피드 파싱 실패: {url}")

    items = []
    for entry in feed.entries[:count]:
        title = _strip_html(entry.get("title", ""))
        summary = _strip_html(entry.get("summary", ""))
        if title:
            items.append({"title": title, "summary": summary})

    return items


def _estimate_cost(count: int) -> str:
    image_cost = count * _AVG_SCENES_PER_SHORT * _IMAGE_COST_PER
    return (
        f"뉴스 {count}개 처리 예상 비용: 이미지 약 ${image_cost:.2f} USD "
        f"(gpt-image-1 low × {count * _AVG_SCENES_PER_SHORT}장) + TTS/Gemini 소량"
    )


# ===== 파이프라인: 뉴스 1건 → 쇼츠 =====

async def _process_one(title: str, summary: str) -> NewsShortItem:
    """
    뉴스 제목+요약 → 쇼츠 생성 파이프라인.
    실패 시 예외 발생 (호출부에서 스킵 처리).
    """
    # 뉴스 내용을 대본 주제로 구성
    topic = f"[뉴스] {title}\n\n{summary[:300]}" if summary else f"[뉴스] {title}"

    # 1. 대본 생성 (3개 반환: image_section, scene_count, subtitles)
    image_section, scene_count, subtitles = await script_service.generate_script(
        topic=topic,
        style="트렌드",
        duration=60,
    )

    # 2. 이미지 생성
    images_result = await image_service.generate_images(image_section)
    images_b64 = images_result

    # 3. TTS 음성 생성 (Typecast 음성 사용)
    audio_b64, audio_duration = await tts_service.generate_tts(script="\n".join(subtitles), voice="changsu")

    # 4. 영상 합성
    video_b64, video_duration = await render_service.render_video(
        images_b64, audio_b64, subtitles
    )

    return NewsShortItem(title=title, video=video_b64, script=image_section)


# ===== 엔드포인트 =====

@router.post("/news-shorts", response_model=NewsShortsResponse)
async def create_news_shorts(body: NewsShortsRequest) -> NewsShortsResponse:
    """
    뉴스 쇼츠 자동 생성 엔드포인트
    Google News RSS → 대본 → 이미지 → TTS → FFmpeg (뉴스별 순차 처리)
    """
    # 비용 경고 (count 임계값 이상)
    warning: str | None = None
    if body.count >= _COST_WARNING_THRESHOLD:
        warning = _estimate_cost(body.count)

    # RSS 뉴스 수집
    try:
        news_items = _fetch_news(body.keyword, body.category, body.count)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    if not news_items:
        raise HTTPException(
            status_code=404,
            detail=f"'{body.keyword}' 키워드로 뉴스를 찾지 못했습니다.",
        )

    # 뉴스별 쇼츠 생성 (순차 — API rate limit 고려, 개별 실패 스킵)
    results: list[NewsShortItem] = []
    skipped = 0

    for item in news_items:
        try:
            short = await _process_one(item["title"], item["summary"])
            results.append(short)
        except Exception:
            # 개별 뉴스 처리 실패 → 스킵하고 나머지 계속
            skipped += 1

    if not results:
        raise HTTPException(
            status_code=502,
            detail="모든 뉴스 항목 처리에 실패했습니다. API 키와 서버 상태를 확인하세요.",
        )

    return NewsShortsResponse(news_shorts=results, skipped=skipped, warning=warning)
