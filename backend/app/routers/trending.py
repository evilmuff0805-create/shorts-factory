"""
트렌딩 라우터 — POST /api/trending
YouTube 인기 영상 수집 → Gemini 쇼츠 소재 추천
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import trending_service

router = APIRouter()


class TrendingRequest(BaseModel):
    category: str | None = Field(default=None, description="카테고리 (교육/과학기술/뉴스·정치/엔터테인먼트/스포츠/음악/인물·블로그)")
    count: int = Field(default=10, ge=1, le=50, description="추천 소재 수")


class TrendingResponse(BaseModel):
    trending: list[dict] = Field(..., description="YouTube 인기 영상 원본 목록")
    recommendations: list[dict] = Field(..., description="Gemini 추천 쇼츠 소재 목록")


@router.post("/trending", response_model=TrendingResponse)
async def get_trending(body: TrendingRequest) -> TrendingResponse:
    """
    YouTube 인기 영상 수집 후 Gemini로 쇼츠 소재 추천
    """
    # 카테고리 이름 → ID 변환
    category_id: str | None = None
    if body.category:
        category_id = trending_service.CATEGORY_MAP.get(body.category)
        if category_id is None:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 카테고리입니다. 가능한 값: {list(trending_service.CATEGORY_MAP.keys())}",
            )

    try:
        trending_data = await trending_service.fetch_trending(
            category_id=category_id,
            max_results=20,
        )
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    try:
        recommendations = await trending_service.recommend_topics(
            trending_data=trending_data,
            count=body.count,
        )
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    return TrendingResponse(trending=trending_data, recommendations=recommendations)
