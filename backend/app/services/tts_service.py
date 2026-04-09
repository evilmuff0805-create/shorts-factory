import httpx
import base64
import os
import subprocess
import tempfile

TYPECAST_MODEL = "ssfm-v21"
_KO_CHARS_PER_SEC = 5.5

VOICE_MAP = {
    "changsu": "tc_6059dad0b83880769a50502f",
    "dabin": "tc_67ad583c7848a19031f798f7",
    "inhwa": "tc_6296a815b958a8ed9610b189",
    "hana": "tc_61659cc118732016a95fe7c6",
}

def _get_audio_duration(path: str) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0

async def generate_tts(script: str, voice: str = "changsu", api_key: str = None) -> tuple[str, float]:
    key = api_key or os.getenv("TYPECAST_API_KEY", "")
    if not key:
        raise RuntimeError("TYPECAST_API_KEY가 설정되지 않았습니다.")

    voice_id = VOICE_MAP.get(voice, VOICE_MAP["changsu"])

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.typecast.ai/v1/text-to-speech",
            headers={"Content-Type": "application/json", "X-API-KEY": key},
            json={
                "voice_id": voice_id,
                "text": script,
                "model": TYPECAST_MODEL,
                "language": "kor",
                "output": {"audio_format": "mp3", "audio_tempo": 1.4}
            }
        )

        if resp.status_code == 401:
            raise RuntimeError("Typecast API 키가 유효하지 않습니다.")
        if resp.status_code == 429:
            raise RuntimeError("Typecast API 요청 한도 초과. 잠시 후 다시 시도하세요.")
        if resp.status_code != 200:
            raise RuntimeError(f"Typecast TTS 오류: {resp.status_code} - {resp.text[:200]}")

        audio_bytes = resp.content
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        duration = _get_audio_duration(tmp_path)
        if duration == 0.0:
            duration = len(script.replace(" ", "")) / _KO_CHARS_PER_SEC

        os.unlink(tmp_path)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return audio_b64, duration
