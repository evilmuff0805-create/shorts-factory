"""
MiniMax Hailuo Image-to-Video 서비스
이미지를 받아 5~6초 동영상 클립으로 변환
"""

import asyncio
import os
import httpx

MINIMAX_API_BASE = "https://api.minimax.io/v1"
HAILUO_MODEL = "MiniMax-Hailuo-2.3-Fast"


def _to_data_url(image_b64: str) -> str:
    """base64 이미지를 data URL 형태로 변환"""
    raw = image_b64.split(",", 1)[-1] if "," in image_b64 else image_b64
    raw = raw.strip().replace("\n", "").replace("\r", "").replace(" ", "")
    raw += "=" * (-len(raw) % 4)
    return f"data:image/png;base64,{raw}"


async def _create_video_task(data_url: str, api_key: str, prompt: str = "") -> str:
    """Hailuo 비디오 생성 태스크 생성, task_id 반환"""
    payload = {
        "model": HAILUO_MODEL,
        "first_frame_image": data_url,
        "prompt": prompt if prompt else "Dynamic camera tracking shot, the subject moves naturally with flowing hair and clothes, environmental elements like clouds and light shift gradually, cinematic motion",
        "prompt_optimizer": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{MINIMAX_API_BASE}/video_generation",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        status_code = data.get("base_resp", {}).get("status_code", 0)
        if status_code != 0:
            raise RuntimeError(f"MiniMax 비디오 태스크 생성 실패: {data.get('base_resp', {}).get('status_msg', data)}")
        return data["task_id"]


async def _poll_video_task(task_id: str, api_key: str, timeout: int = 600) -> str:
    """태스크 완료까지 폴링, file_id 반환"""
    import time
    start = time.time()
    async with httpx.AsyncClient(timeout=30) as client:
        while time.time() - start < timeout:
            resp = await client.get(
                f"{MINIMAX_API_BASE}/query/video_generation",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"task_id": task_id},
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")
            if status == "Success":
                return data["file_id"]
            elif status == "Fail":
                raise RuntimeError(f"MiniMax 비디오 생성 실패: {data}")
            await asyncio.sleep(10)
    raise RuntimeError("MiniMax 비디오 생성 시간 초과 (10분)")


async def _download_video(file_id: str, api_key: str) -> bytes:
    """file_id로 비디오 파일 다운로드, bytes 반환"""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(
            f"{MINIMAX_API_BASE}/files/retrieve",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"file_id": file_id},
        )
        resp.raise_for_status()
        download_url = resp.json()["file"]["download_url"]

        video_resp = await client.get(download_url)
        video_resp.raise_for_status()
        return video_resp.content


async def animate_image(image_b64: str, api_key: str | None = None, prompt: str = "") -> bytes:
    """단일 이미지(base64) → 동영상 클립(bytes) 변환"""
    key = api_key or os.getenv("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY 환경변수가 설정되지 않았습니다.")

    data_url = _to_data_url(image_b64)
    task_id = await _create_video_task(data_url, key, prompt)
    file_id = await _poll_video_task(task_id, key)
    video_bytes = await _download_video(file_id, key)
    return video_bytes


async def animate_images(images_b64: list[str], api_key: str | None = None) -> list[bytes]:
    """여러 이미지를 병렬로 동영상 클립으로 변환"""
    key = api_key or os.getenv("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY 환경변수가 설정되지 않았습니다.")

    tasks = [animate_image(img, key) for img in images_b64]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    videos = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            raise RuntimeError(f"이미지 {i+1}번 비디오 변환 실패: {result}")
        videos.append(result)
    return videos
