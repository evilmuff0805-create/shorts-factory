# Shorts Factory

유튜브 쇼츠를 자동으로 대량 생성하는 웹 애플리케이션.

**파이프라인**: 키워드/주제 입력 → AI 대본 → AI 이미지 → TTS 음성 → 자막 → 최종 영상

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Next.js 16 + Tailwind CSS + shadcn/ui |
| Backend | Python 3.14 + FastAPI 0.135 |
| 영상 합성 | FFmpeg |
| 파일 저장 | Cloudflare R2 |
| LLM | Google Gemini 2.5 Flash |
| 이미지 | GPT Image 1.5 |
| TTS | OpenAI TTS-1 |
| STT | OpenAI Whisper |

## 설치 및 실행

### 사전 요구사항
- Node.js 20+
- Python 3.14+
- FFmpeg (시스템 설치 필요)

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### 3. 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# http://localhost:8000
# API 문서: http://localhost:8000/docs
```

## 프로젝트 구조

```
shorts-factory/
├── frontend/          # Next.js 16 앱
├── backend/           # FastAPI 앱
├── tasks/             # 작업 관리
│   ├── todo.md
│   └── lessons.md
├── .env.example       # 환경변수 템플릿
└── CLAUDE.md          # AI 코딩 규칙
```

## API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /api/script` | AI 대본 생성 |
| `POST /api/images` | AI 이미지 생성 |
| `POST /api/tts` | TTS 음성 생성 |
| `POST /api/render` | FFmpeg 영상 합성 |
| `POST /api/long-to-short` | 롱폼→쇼츠 변환 |
| `POST /api/news-shorts` | 뉴스 쇼츠 자동화 |
