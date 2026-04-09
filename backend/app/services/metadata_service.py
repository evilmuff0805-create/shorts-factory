"""
메타데이터 생성 서비스 — Gemini로 유튜브 업로드용 메타데이터 생성
"""

import json
import os

from google import genai


async def generate_metadata(script: str, topic: str, genre: str) -> dict:
    """
    쇼츠 스크립트 기반으로 유튜브 업로드용 메타데이터 생성.
    반환: { title, description, hashtags }
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    prompt = f"""아래 YouTube Shorts 스크립트를 바탕으로 유튜브 업로드용 메타데이터를 생성해줘.
title(60자 이내, 호기심 유발), description(500자 이내, SEO 최적화, 핵심 내용 요약, 해시태그나 이모지 절대 포함하지 마), hashtags(관련 해시태그 10개, #포함) 를 JSON 객체로만 응답해.

주제: {topic}
장르: {genre}

스크립트:
{script}"""

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 실패: {e}") from e

    # JSON 코드블록 제거 후 파싱
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini 응답 JSON 파싱 실패: {e}\n응답: {raw[:200]}") from e
