"""
영상 합성 서비스 — FFmpeg 파이프라인 로직
라우터와 news.py에서 재사용
"""

import asyncio
import base64
import os
import shutil
import tempfile
from pathlib import Path

import ffmpeg

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920


def _find_font() -> str | None:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _escape_drawtext(text: str) -> str:
    text = ''.join(c for c in text if c.isprintable() and ord(c) < 65536)
    return (
        text.replace("\\", "\\\\")
            .replace("'", "\u2019")
            .replace(":", "\\:")
            .replace("%", "\\%")
    )


def _wrap_text(text: str, max_chars: int = 13) -> str:
    """긴 텍스트를 max_chars 글자마다 줄바꿈 삽입"""
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 > max_chars and current_line:
            lines.append(current_line)
            current_line = word
        else:
            current_line = f"{current_line} {word}".strip() if current_line else word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)


def _get_audio_duration(audio_path: str) -> float:
    probe = ffmpeg.probe(audio_path)
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return float(stream["duration"])
    return float(probe["format"]["duration"])


def _run_ffmpeg(
    media_paths: list[str],
    audio_path: str,
    subtitles: list[str],
    fps: int,
    output_path: str,
    is_video_clips: bool = False,
) -> float:
    total_duration = _get_audio_duration(audio_path)

    if is_video_clips:
        # MP4 클립들을 이어붙이기
        inputs = [ffmpeg.input(p) for p in media_paths]
        video = ffmpeg.concat(*[i.video for i in inputs], v=1, a=0)
    else:
        # 정적 이미지 모드 (기존 로직)
        n = len(media_paths)
        scene_duration = total_duration / n
        img_inputs = [
            ffmpeg.input(p, loop=1, t=scene_duration, framerate=fps)
            for p in media_paths
        ]
        scaled = [
            inp.video
            .filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT,
                    force_original_aspect_ratio="decrease")
            .filter("pad", VIDEO_WIDTH, VIDEO_HEIGHT,
                    "(ow-iw)/2", "(oh-ih)/2", color="black")
            .filter("setsar", "1")
            for inp in img_inputs
        ]
        video = ffmpeg.concat(*scaled, v=1, a=0)

    # 비디오 클립인 경우에도 스케일 및 SAR 보정
    if is_video_clips:
        video = video.filter("scale", VIDEO_WIDTH, VIDEO_HEIGHT,
                             force_original_aspect_ratio="decrease")
        video = video.filter("pad", VIDEO_WIDTH, VIDEO_HEIGHT,
                             "(ow-iw)/2", "(oh-ih)/2", color="black")
        video = video.filter("setsar", "1")

    audio_input = ffmpeg.input(audio_path)

    font_path = _find_font()
    if subtitles:
        total_chars = sum(len(s.replace(" ", "")) for s in subtitles) or 1
        current_time = 0.0
        for i, subtitle_text in enumerate(subtitles):
            if not subtitle_text.strip():
                continue
            char_len = len(subtitle_text.replace(" ", "")) or 1
            sub_duration = total_duration * (char_len / total_chars)
            start_t = current_time
            end_t = current_time + sub_duration - 0.05
            current_time = current_time + sub_duration
            clean_text = ''.join(c for c in subtitle_text if c.isprintable() and ord(c) < 65536)
            kwargs: dict = {
                "text": _escape_drawtext(clean_text),
                "fontsize": 70,
                "fontcolor": "white",
                "borderw": 5,
                "bordercolor": "black",
                "x": "(w-text_w)/2",
                "y": "(h-th)/2",
                "enable": f"between(t,{start_t:.3f},{end_t:.3f})",
            }
            if font_path:
                kwargs["fontfile"] = font_path
            video = video.filter("drawtext", **kwargs)

    out = ffmpeg.output(
        video, audio_input.audio, output_path,
        vcodec="libx264", acodec="aac",
        pix_fmt="yuv420p", r=fps,
        movflags="+faststart", shortest=None,
    )
    ffmpeg.run(out, overwrite_output=True, quiet=True)
    return total_duration


async def render_video(
    images_b64: list[str],
    audio_b64: str,
    subtitles: list[str],
    fps: int = 30,
) -> tuple[str, float]:
    """
    이미지 또는 비디오 클립(base64) + 음성(base64 MP3) + 자막 → base64 MP4.
    반환: (base64_mp4, duration_sec)
    """
    tmp_dir = tempfile.mkdtemp(prefix="shorts_render_")
    try:
        # base64 데이터가 MP4인지 감지
        first_raw = images_b64[0].split(",", 1)[-1] if "," in images_b64[0] else images_b64[0]
        first_raw_clean = first_raw.strip().replace("\n", "").replace("\r", "").replace(" ", "")
        first_raw_clean += "=" * (-len(first_raw_clean) % 4)
        first_bytes = base64.b64decode(first_raw_clean[:20])
        is_video = first_bytes[:4] != b'\x89PNG' and first_bytes[:8] != b'\xff\xd8\xff\xe0\x00\x10JFIF'[:len(first_bytes)]

        media_paths: list[str] = []
        for i, item_b64 in enumerate(images_b64):
            ext = ".mp4" if is_video else ".png"
            media_path = os.path.join(tmp_dir, f"scene_{i:03d}{ext}")
            raw = item_b64.split(",", 1)[-1] if "," in item_b64 else item_b64
            raw = raw.strip().replace("\n", "").replace("\r", "").replace(" ", "")
            raw += "=" * (-len(raw) % 4)
            Path(media_path).write_bytes(base64.b64decode(raw))
            media_paths.append(media_path)

        audio_path = os.path.join(tmp_dir, "audio.mp3")
        raw_audio = audio_b64.split(",", 1)[-1] if "," in audio_b64 else audio_b64
        raw_audio = raw_audio.strip().replace("\n", "").replace("\r", "").replace(" ", "")
        raw_audio += "=" * (-len(raw_audio) % 4)
        Path(audio_path).write_bytes(base64.b64decode(raw_audio))

        output_path = os.path.join(tmp_dir, "output.mp4")

        try:
            duration = await asyncio.to_thread(
                _run_ffmpeg, media_paths, audio_path, subtitles, fps, output_path, is_video
            )
        except ffmpeg.Error as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            raise RuntimeError(f"FFmpeg 실패: {stderr[-500:]}")
        except Exception as e:
            raise RuntimeError(f"영상 생성 실패: {e}") from e

        video_b64 = base64.b64encode(Path(output_path).read_bytes()).decode("utf-8")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return video_b64, round(duration, 2)
