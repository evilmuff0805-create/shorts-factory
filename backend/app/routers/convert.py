"""
롱폼→쇼츠 변환 라우터 — POST /api/long-to-short
yt-dlp 다운로드 → Whisper STT → Gemini 하이라이트 추출 → FFmpeg 클립 합성
"""

import asyncio
import base64
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import ffmpeg
import yt_dlp
from fastapi import APIRouter, HTTPException
from google import genai
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

router = APIRouter()

# 한국어 폰트 (render.py와 동일)
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

_LONG_VIDEO_THRESHOLD_SEC = 1800  # 30분 이상이면 Whisper 비용 경고


# ===== 모델 =====

class ConvertRequest(BaseModel):
    youtube_url: str = Field(..., description="변환할 유튜브 영상 URL")
    shorts_count: int = Field(default=3, ge=1, le=10, description="생성할 쇼츠 수")
    shorts_duration: int = Field(default=60, ge=15, le=90, description="각 쇼츠 목표 길이(초)")


class ShortItem(BaseModel):
    index: int = Field(..., description="쇼츠 번호 (1부터 시작)")
    video: str = Field(..., description="base64 인코딩된 MP4")
    highlight_text: str = Field(..., description="하이라이트 요약 텍스트")


class ConvertResponse(BaseModel):
    shorts: list[ShortItem] = Field(..., description="생성된 쇼츠 목록")
    warning: str | None = Field(default=None, description="주의 메시지 (긴 영상 비용 경고 등)")


# ===== Step 1: yt-dlp 다운로드 (동기 — to_thread 호출) =====

def _download_video(url: str, tmp_dir: str) -> str:
    """유튜브 영상을 720p 이하로 다운로드. 실제 저장 경로 반환."""
    ydl_opts = {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "outtmpl": os.path.join(tmp_dir, "video.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # 실제 저장된 파일 경로 결정
            video_path = os.path.join(tmp_dir, f"video.{info.get('ext', 'mp4')}")
            if not os.path.exists(video_path):
                video_path = os.path.join(tmp_dir, "video.mp4")
            return video_path
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"영상 다운로드 실패: {str(e)}")


# ===== Step 2: 오디오 추출 + 영상 길이 확인 (동기) =====

def _extract_audio_and_probe(video_path: str, tmp_dir: str) -> tuple[str, float]:
    """
    영상에서 오디오 추출 (Whisper용 mp3) + 전체 길이 반환.
    반환: (audio_path, duration_sec)
    """
    audio_path = os.path.join(tmp_dir, "audio.mp3")
    probe = ffmpeg.probe(video_path)
    duration = float(probe["format"]["duration"])

    # 16kHz 모노 mp3로 추출 (Whisper 최적화, 파일 크기 절감)
    (
        ffmpeg
        .input(video_path)
        .audio
        .filter("aresample", 16000)
        .output(audio_path, ac=1, audio_bitrate="64k")
        .run(overwrite_output=True, quiet=True)
    )
    return audio_path, duration


# ===== Step 3: Whisper STT =====

async def _transcribe(audio_path: str, api_key: str) -> list[dict[str, Any]]:
    """
    Whisper API로 STT 수행.
    반환: [{"start": float, "end": float, "text": str}, ...]
    """
    client = AsyncOpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ko",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    return [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in result.segments
    ]


# ===== Step 4: Gemini 하이라이트 추출 =====

def _build_transcript_text(segments: list[dict[str, Any]]) -> str:
    """STT 세그먼트 → 타임스탬프 포함 텍스트"""
    lines = [f"[{s['start']:.1f}s - {s['end']:.1f}s] {s['text']}" for s in segments]
    return "\n".join(lines)


async def _get_highlights(
    segments: list[dict[str, Any]],
    shorts_count: int,
    shorts_duration: int,
    api_key: str,
) -> list[dict[str, Any]]:
    """
    Gemini로 하이라이트 구간 추출.
    반환: [{"start": float, "end": float, "summary": str}, ...]
    """
    transcript_text = _build_transcript_text(segments)
    prompt = f"""다음은 유튜브 영상의 자막입니다 (타임스탬프 포함):

{transcript_text}

이 영상에서 유튜브 쇼츠로 만들기 좋은 하이라이트 {shorts_count}개를 추출해줘.
- 각 하이라이트는 {shorts_duration}초 내외
- 흥미롭고 완결성 있는 구간 선택
- 서로 겹치지 않게

반드시 아래 JSON 형식으로만 응답해줘 (설명 없이):
[
  {{"start": 10.5, "end": 70.5, "summary": "요약 텍스트"}},
  ...
]"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw = response.text.strip()

    # 마크다운 코드블록 제거 후 JSON 파싱
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    try:
        highlights = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini 응답 JSON 파싱 실패: {e}\n원문: {raw[:300]}")

    return highlights[:shorts_count]


# ===== Step 5: FFmpeg 클립 추출 (동기 — to_thread 호출) =====

def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace("'", "\u2019")
            .replace(":", "\\:")
            .replace("%", "\\%")
    )


def _extract_clip(
    video_path: str,
    highlight: dict[str, Any],
    segments: list[dict[str, Any]],
    index: int,
    tmp_dir: str,
) -> str:
    """
    FFmpeg로 하이라이트 구간 추출 + 9:16 크롭 + 자막 burn-in.
    반환: 클립 파일 경로
    """
    start: float = highlight["start"]
    end: float = highlight["end"]
    clip_path = os.path.join(tmp_dir, f"clip_{index:02d}.mp4")

    # 구간 내 자막 세그먼트 필터링 + 타임스탬프 오프셋
    clip_segments = [
        {
            "start": max(0.0, s["start"] - start),
            "end": min(end - start, s["end"] - start),
            "text": s["text"],
        }
        for s in segments
        if s["start"] < end and s["end"] > start and s["text"]
    ]

    # 입력 스트림 (구간 지정)
    inp = ffmpeg.input(video_path, ss=start, to=end)

    # 비디오 필터: 가운데 9:16 크롭 → 1080×1920 스케일
    video = (
        inp.video
        .filter("crop", "ih*9/16", "ih")
        .filter("scale", 1080, 1920)
        .filter("setsar", "1")
    )

    # 자막 drawtext burn-in
    font_path = _find_font()
    for seg in clip_segments:
        if not seg["text"].strip():
            continue
        kwargs: dict = {
            "text": _escape_drawtext(seg["text"]),
            "fontsize": 50,
            "fontcolor": "white",
            "borderw": 3,
            "bordercolor": "black",
            "x": "(w-text_w)/2",
            "y": "h-th-150",
            "enable": f"between(t,{seg['start']:.3f},{seg['end']:.3f})",
        }
        if font_path:
            kwargs["fontfile"] = font_path
        video = video.filter("drawtext", **kwargs)

    # 출력
    out = ffmpeg.output(
        video,
        inp.audio,
        clip_path,
        vcodec="libx264",
        acodec="aac",
        pix_fmt="yuv420p",
        movflags="+faststart",
    )
    ffmpeg.run(out, overwrite_output=True, quiet=True)
    return clip_path


# ===== 엔드포인트 =====

@router.post("/long-to-short", response_model=ConvertResponse)
async def convert_to_shorts(body: ConvertRequest) -> ConvertResponse:
    """
    롱폼 유튜브 영상 → 쇼츠 변환 엔드포인트
    yt-dlp → Whisper STT → Gemini 하이라이트 → FFmpeg 클립
    """
    # API 키 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY 환경변수가 없습니다.")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 환경변수가 없습니다.")

    tmp_dir = tempfile.mkdtemp(prefix="shorts_convert_")
    warning: str | None = None

    try:
        # ── 1. 다운로드 ──────────────────────────────────────────────────
        try:
            video_path = await asyncio.to_thread(_download_video, body.youtube_url, tmp_dir)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # ── 2. 오디오 추출 + 길이 확인 ──────────────────────────────────
        try:
            audio_path, duration = await asyncio.to_thread(
                _extract_audio_and_probe, video_path, tmp_dir
            )
        except ffmpeg.Error as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            raise HTTPException(status_code=502, detail=f"오디오 추출 실패: {stderr[-300:]}")

        if duration > _LONG_VIDEO_THRESHOLD_SEC:
            minutes = int(duration // 60)
            warning = (
                f"영상 길이가 {minutes}분으로 Whisper STT 비용이 높을 수 있습니다. "
                f"(약 ${duration / 60 * 0.006:.2f} USD)"
            )

        # ── 3. Whisper STT ───────────────────────────────────────────────
        try:
            segments = await _transcribe(audio_path, openai_key)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Whisper STT 실패: {str(e)}")

        if not segments:
            raise HTTPException(status_code=422, detail="영상에서 음성을 감지하지 못했습니다.")

        # ── 4. Gemini 하이라이트 추출 ────────────────────────────────────
        try:
            highlights = await _get_highlights(
                segments, body.shorts_count, body.shorts_duration, gemini_key
            )
        except ValueError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Gemini 하이라이트 추출 실패: {str(e)}")

        # ── 5. FFmpeg 클립 추출 ──────────────────────────────────────────
        shorts: list[ShortItem] = []
        for i, hl in enumerate(highlights):
            try:
                clip_path = await asyncio.to_thread(
                    _extract_clip, video_path, hl, segments, i, tmp_dir
                )
            except ffmpeg.Error as e:
                stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
                raise HTTPException(status_code=502, detail=f"클립 {i+1} 추출 실패: {stderr[-300:]}")

            video_b64 = base64.b64encode(Path(clip_path).read_bytes()).decode("utf-8")
            shorts.append(ShortItem(
                index=i + 1,
                video=video_b64,
                highlight_text=hl.get("summary", ""),
            ))

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return ConvertResponse(shorts=shorts, warning=warning)
