"""
이미지 생성 서비스 — OpenAI gpt-image-1 호출 로직
라우터와 news.py에서 재사용
"""

import asyncio
import os

from openai import AsyncOpenAI


def _build_image_prompt(scene_text: str, image_style: str = "pixar3d") -> str:
    style_prefix = {
        "realistic": "Photorealistic cinematic photography, ultra detailed, natural lighting, ",
        "anime": "Japanese anime style illustration, vibrant colors, detailed cel shading, ",
        "pixar3d": "Pixar-style 3D animation, cute stylized characters, ",
    }
    prefix = style_prefix.get(image_style, style_prefix["pixar3d"])
    return (
        f"{prefix}"
        f"vertical 9:16 aspect ratio, vibrant colors, "
        f"high quality, detailed background. "
        f"Scene: {scene_text}"
    )


async def _generate_one(client: AsyncOpenAI, prompt: str) -> str:
    """장면 하나 → raw base64 문자열 반환"""
    response = await client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1536",
        quality="low",
        n=1,
    )
    return response.data[0].b64_json


async def generate_images(
    script: str,
    api_key: str | None = None,
    image_style: str = "pixar3d",
) -> list[str]:
    """
    대본 → 장면별 이미지 생성 (병렬).
    반환: raw base64 문자열 목록 (data: URL 접두어 없음)
    예외: ValueError (장면 없음), RuntimeError (API 실패)
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

    scenes = [s.strip() for s in script.split("---") if s.strip()]
    if not scenes:
        raise ValueError("대본에서 장면을 파싱할 수 없습니다. --- 구분자를 확인하세요.")

    try:
        client = AsyncOpenAI(api_key=key)
        tasks = [_generate_one(client, _build_image_prompt(scene, image_style)) for scene in scenes]
        return list(await asyncio.gather(*tasks))
    except Exception as e:
        error_msg = str(e)
        if "content_policy" in error_msg or "safety" in error_msg or "moderation" in error_msg:
            raise RuntimeError("이미지 생성이 콘텐츠 정책에 의해 차단되었습니다. 다른 주제로 시도해주세요.") from e
        elif "billing" in error_msg or "quota" in error_msg or "insufficient" in error_msg:
            raise RuntimeError("OpenAI API 잔액이 부족합니다. 결제 정보를 확인해주세요.") from e
        else:
            raise RuntimeError(f"OpenAI 이미지 생성 실패: {e}") from e
