"""
기사 분석 서비스 — URL 크롤링 + Gemini 분석
"""

import os
import re
import httpx
from bs4 import BeautifulSoup
from google import genai


async def fetch_article(url: str) -> dict:
    """
    기사 URL → 제목 + 본문 텍스트 크롤링.
    반환: {"title": str, "body": str, "url": str}
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 제목 추출: og:title → <title> → 빈 문자열
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()
    else:
        title = ""

    # 본문 추출: <article> 태그 우선, 없으면 <p> 태그 전체
    article_tag = soup.find("article")
    if article_tag:
        paragraphs = article_tag.find_all("p")
    else:
        paragraphs = soup.find_all("p")

    body = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # 본문이 너무 짧으면 크롤링 실패로 판단
    if len(body) < 50:
        raise RuntimeError(
            "기사 본문을 충분히 가져오지 못했습니다. "
            "해당 사이트가 크롤링을 차단하고 있을 수 있습니다."
        )

    # 너무 긴 본문은 앞부분만 사용 (Gemini 토큰 절약)
    if len(body) > 3000:
        body = body[:3000] + "..."

    return {"title": title, "body": body, "url": url}


async def analyze_article(title: str, body: str) -> dict:
    """
    Gemini로 기사 내용 분석.
    반환: {"summary": str, "key_points": list[str], "suggested_topics": list[str]}
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    prompt = f"""너는 뉴스 기사 분석 전문가야. 아래 기사를 분석해줘.

[기사 제목]
{title}

[기사 본문]
{body}

[분석 규칙]
1. 반드시 아래 형식대로만 출력해. 다른 말 붙이지 마.
2. 한국어로 작성해.

[요약]
기사 핵심 내용을 3~5문장으로 요약해줘.

[핵심 포인트]
가장 중요한 포인트 3~5개를 ||| 로 구분해서 작성해.

[추천 쇼츠 주제]
이 기사를 기반으로 유튜브 쇼츠로 만들기 좋은 주제 3개를 ||| 로 구분해서 작성해. 각 주제는 호기심을 자극하는 한 문장으로."""

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        result_text = response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 실패: {e}") from e

    # 파싱
    summary = ""
    key_points = []
    suggested_topics = []

    # [요약] 섹션 추출
    summary_match = re.search(r"\[요약\]\s*\n(.*?)(?=\[핵심 포인트\])", result_text, re.DOTALL)
    if summary_match:
        summary = summary_match.group(1).strip()

    # [핵심 포인트] 섹션 추출
    points_match = re.search(r"\[핵심 포인트\]\s*\n(.*?)(?=\[추천 쇼츠 주제\])", result_text, re.DOTALL)
    if points_match:
        key_points = [p.strip() for p in points_match.group(1).split("|||") if p.strip()]

    # [추천 쇼츠 주제] 섹션 추출
    topics_match = re.search(r"\[추천 쇼츠 주제\]\s*\n(.*)", result_text, re.DOTALL)
    if topics_match:
        suggested_topics = [t.strip() for t in topics_match.group(1).split("|||") if t.strip()]

    return {
        "summary": summary or "분석 결과를 파싱하지 못했습니다.",
        "key_points": key_points or ["핵심 포인트를 추출하지 못했습니다."],
        "suggested_topics": suggested_topics or ["추천 주제를 생성하지 못했습니다."],
    }
