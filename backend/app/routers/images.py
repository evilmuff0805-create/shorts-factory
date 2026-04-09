"""
이미지 생성 라우터 — POST /api/images
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import image_service

router = APIRouter()


class ImagesRequest(BaseModel):
    script: str = Field(..., description="대본 전문 (장면은 --- 구분자로 분리)", min_length=1)
    image_style: str = Field(default="pixar3d", description="이미지 스타일 (realistic, anime, pixar3d)")


class ImageItem(BaseModel):
    scene: int = Field(..., description="장면 번호 (1부터 시작)")
    url: str = Field(..., description="생성된 이미지 (data:image/png;base64,...)")


class ImagesResponse(BaseModel):
    images: list[ImageItem] = Field(..., description="장면별 이미지 목록")


@router.post("/images", response_model=ImagesResponse)
async def generate_images(body: ImagesRequest) -> ImagesResponse:
    """대본 → 장면별 이미지 생성 — gpt-image-1 (병렬)"""
    try:
        raw_b64_list = await image_service.generate_images(body.script, image_style=body.image_style)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        status = 500 if "환경변수" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    images = [
        ImageItem(scene=i + 1, url=f"data:image/png;base64,{b64}")
        for i, b64 in enumerate(raw_b64_list)
    ]
    return ImagesResponse(images=images)
