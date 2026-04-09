"""
트렌딩 서비스 — YouTube Data API v3 인기 영상 수집 + Gemini 소재 추천
"""

import json
import os

from google import genai
from googleapiclient.discovery import build


# 카테고리 ID 매핑
CATEGORY_MAP = {
    "교육": "27",
    "과학기술": "28",
    "뉴스/정치": "25",
    "엔터테인먼트": "24",
    "스포츠": "17",
    "음악": "10",
    "인물/블로그": "22",
}


async def fetch_trending(
    category_id: str | None,
    max_results: int = 20,
) -> list[dict]:
    """
    YouTube Data API v3로 한국 인기 영상 수집.
    반환: [{ title, channel, view_count, video_id, category_id, published_at, description }]
    """
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY 환경변수가 설정되지 않았습니다.")

    try:
        youtube = build("youtube", "v3", developerKey=key)

        # videos.list 파라미터 구성
        params: dict = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": "KR",
            "maxResults": max_results,
        }
        if category_id:
            params["videoCategoryId"] = category_id

        response = youtube.videos().list(**params).execute()
    except Exception as e:
        raise RuntimeError(f"YouTube API 호출 실패: {e}") from e

    items = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        items.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "view_count": int(stats.get("viewCount", 0)),
            "video_id": item.get("id", ""),
            "category_id": snippet.get("categoryId", ""),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", "")[:200],
        })

    return items


async def recommend_topics(
    trending_data: list[dict],
    count: int = 10,
) -> list[dict]:
    """
    인기 영상 목록을 Gemini에게 전달해 YouTube Shorts 소재 추천.
    반환: [{ title, summary, genre, score }]
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    # 영상 목록을 텍스트로 변환
    videos_text = json.dumps(trending_data, ensure_ascii=False, indent=2)

    prompt = f"""아래 유튜브 인기 영상 목록을 분석해서 YouTube Shorts로 만들기 좋은 소재 {count}개를 추천해줘.
각 소재마다 title(소재 제목), summary(한 줄 요약), genre(교육/글로벌 정세/트렌드/문화/AI·기술/과학/비즈니스/엔터테인먼트/스포츠/튜토리얼 중 하나), score(1~100 인기도 점수)를 JSON 배열로만 응답해.

{videos_text}"""

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
