"""
대본 생성 서비스 — Gemini 2.5 Flash 호출 로직
라우터와 news.py에서 재사용
"""

import os

from google import genai


_STYLE_GUIDE: dict[str, str] = {
    "교육": "지식을 쉽고 재미있게 전달하는 교육 콘텐츠",
    "글로벌 정세": "국제 뉴스와 세계 이슈를 분석하는 콘텐츠",
    "트렌드": "지금 화제인 주제를 다루는 바이럴 콘텐츠",
    "문화": "문화 현상, 예술, 역사를 다루는 콘텐츠",
    "AI·기술": "인공지능과 신기술을 소개하는 콘텐츠",
    "과학": "과학 발견과 자연 현상을 설명하는 콘텐츠",
    "비즈니스": "경제, 투자, 기업 이야기를 다루는 콘텐츠",
    "엔터테인먼트": "재미와 흥미 위주의 가벼운 콘텐츠",
    "스포츠": "스포츠 하이라이트와 분석 콘텐츠",
    "튜토리얼": "방법과 과정을 단계별로 설명하는 가이드 콘텐츠",
}


def _build_prompt(topic: str, style: str, duration: int) -> str:
    if duration == 30:
        image_count = "5개"
        subtitle_count = "10~15개"
    elif duration == 90:
        image_count = "15개"
        subtitle_count = "30~45개"
    else:  # 60초
        image_count = "10개"
        subtitle_count = "20~30개"

    style_description = _STYLE_GUIDE.get(style, style)

    total_chars = int(duration * 5.5)

    return f"""너는 유튜브 쇼츠 대본 작가야. 주제: "{topic}"
스타일: {style_description}
영상 길이: {duration}초

[대본 규칙]
1. 전체 나레이션 글자수(공백 제외)를 반드시 {total_chars}자 내외로 맞춰라.
2. 유튜브 커뮤니티처럼 자연스러운 반말을 써라. (~임, ~거든, ~잖아, ~ㅋㅋ, ~인데)
3. 격식체(~합니다, ~됩니다, ~입니다) 절대 금지.
4. 이모지, 특수문자, 해시태그 금지.
5. 첫 문장은 무조건 궁금증 유발하는 훅으로 시작해.
6. 마지막 문장은 짧고 임팩트 있게 끝내.

[가장 중요한 규칙 - 자막 문장 품질]
- 자막은 절대 단어 나열이나 키워드 조합이 아니다.
- 모든 자막은 주어+서술어가 있는 완전한 문장이어야 한다.
- 누군가에게 이야기를 들려주듯이 자연스럽게 말하는 문장을 써라.
- 나쁜 예: "에티오피아 목동 칼디 춤추는 염소들 발견" (단어 나열)
- 좋은 예: "옛날에 에티오피아 목동이 춤추는 염소를 발견했거든" (완전한 문장)
- 나쁜 예: "놀라운 음료의 기원, 염소 똥에서 시작?" (키워드 조합)
- 좋은 예: "근데 이 커피가 어떻게 시작됐는지 알면 놀랄걸?" (자연스러운 말)

[출력 형식]
[이미지]
영어로 된 이미지 생성 프롬프트 {image_count}개를 --- 로 구분해서 작성해.
각 프롬프트는 장면을 묘사하는 한 문장이어야 해.

[자막]
한국어 자막 {subtitle_count}개를 ||| 로 구분해서 작성해.
각 자막은 7~15글자의 완전한 문장으로, 위의 나레이션 대본을 순서대로 쪼갠 것이어야 해."""


async def generate_script(
    topic: str,
    style: str,
    duration: int,
    api_key: str | None = None,
) -> tuple[str, int, list[str]]:
    """
    Gemini로 쇼츠 대본 생성.
    반환: (image_script, scene_count, subtitles)
    예외: RuntimeError (API 키 없음 또는 Gemini 실패)
    """
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=_build_prompt(topic, style, duration),
        )
        script_text = response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API 호출 실패: {e}") from e

    # [이미지]와 [자막] 섹션 파싱
    image_section = ""
    subtitle_section = ""

    if "[이미지]" in script_text and "[자막]" in script_text:
        parts = script_text.split("[자막]")
        image_section = parts[0].replace("[이미지]", "").strip()
        subtitle_section = parts[1].strip()
    else:
        image_section = script_text
        subtitle_section = ""

    image_prompts = [s.strip() for s in image_section.split("---") if s.strip()]
    subtitles = [s.strip() for s in subtitle_section.split("|||") if s.strip()] if subtitle_section else []

    if not image_prompts:
        raise RuntimeError("스크립트 생성 결과에서 이미지 설명을 찾을 수 없습니다. 다시 시도해주세요.")
    if not subtitles:
        raise RuntimeError("스크립트 생성 결과에서 자막을 찾을 수 없습니다. 다시 시도해주세요.")

    return image_section, len(image_prompts), subtitles
