"""
메타데이터 라우터 — POST /api/metadata
쇼츠 스크립트 → 유튜브 업로드용 메타데이터 생성
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import metadata_service

router = APIRouter()


class MetadataRequest(BaseModel):
    script: str = Field(..., description="쇼츠 대본", min_length=1)
    topic: str = Field(..., description="쇼츠 주제", min_length=1)
    genre: str = Field(default="교육", description="장르 (교육/글로벌 정세/트렌드/문화/AI·기술/과학/비즈니스/엔터테인먼트/스포츠/튜토리얼)")


class MetadataResponse(BaseModel):
    title: str = Field(..., description="유튜브 제목 (60자 이내)")
    description: str = Field(..., description="유튜브 설명 (SEO 최적화)")
    hashtags: list[str] = Field(..., description="해시태그 목록 (#포함)")


@router.post("/metadata", response_model=MetadataResponse)
async def create_metadata(body: MetadataRequest) -> MetadataResponse:
    """
    쇼츠 대본 기반 유튜브 업로드용 메타데이터 생성
    """
    try:
        result = await metadata_service.generate_metadata(
            script=body.script,
            topic=body.topic,
            genre=body.genre,
        )
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    return MetadataResponse(
        title=result.get("title", ""),
        description=result.get("description", ""),
        hashtags=result.get("hashtags", []),
    )
