"""
Shorts Factory — FastAPI 백엔드 엔트리포인트
실행: uvicorn app.main:app --reload
API 문서: http://localhost:8000/docs
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import script, images, tts, render, convert, news, trending, metadata, article
from app.routers import video as video_router

load_dotenv()

app = FastAPI(
    title="Shorts Factory API",
    description="유튜브 쇼츠 자동 생성 파이프라인",
    version="0.1.0",
)

# CORS 설정 — 프론트엔드 허용
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(script.router, prefix="/api", tags=["대본 생성"])
app.include_router(images.router, prefix="/api", tags=["이미지 생성"])
app.include_router(tts.router, prefix="/api", tags=["TTS 음성"])
app.include_router(render.router, prefix="/api", tags=["영상 합성"])
app.include_router(convert.router, prefix="/api", tags=["롱폼→쇼츠"])
app.include_router(news.router, prefix="/api", tags=["뉴스 쇼츠"])
app.include_router(trending.router, prefix="/api", tags=["트렌드"])
app.include_router(metadata.router, prefix="/api", tags=["메타데이터"])
app.include_router(video_router.router, prefix="/api", tags=["video"])
app.include_router(article.router, prefix="/api", tags=["기사 분석"])


@app.get("/health")
async def health_check() -> dict:
    """헬스 체크 엔드포인트"""
    return {"status": "ok", "version": "0.1.0"}
