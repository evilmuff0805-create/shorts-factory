# Shorts Factory — 유튜브 쇼츠 자동화 웹앱

## 프로젝트 개요
유튜브 쇼츠를 자동으로 대량 생성하는 웹 애플리케이션.
키워드/주제 입력 → AI 대본 → AI 이미지 → TTS 음성 → 자막 → 최종 영상 합성

## 기술 스택
- Frontend: Next.js 16 + Tailwind CSS + shadcn/ui (Vercel 배포)
- Backend: Python 3.14 / FastAPI 0.135 (Render → Railway 배포)
- 영상 합성: ffmpeg-python (서버에서 FFmpeg CLI 호출)
- 파일 저장: Cloudflare R2 (10GB 무료)

## 외부 API
- LLM 대본: Google Gemini 2.5 Flash (기본) / GPT-4.1 nano (대량 백업)
- 이미지: GPT Image 1.5 Low ($0.009/장)
- TTS: OpenAI TTS-1 ($15/1M chars)
- STT/자막: OpenAI Whisper API ($0.006/min)
- 유튜브 다운로드: yt-dlp + Deno (JS runtime 필수)
- 뉴스 수집: feedparser + Google News RSS

## 파이프라인 (7단계)
1. 사용자 입력 (주제/키워드 또는 유튜브 URL)
2. AI 대본 생성 (Gemini API)
3. AI 이미지 생성 (GPT Image API)
4. TTS 음성 생성 (OpenAI TTS)
5. FFmpeg 영상 합성 (이미지 + 음성 + 자막)
6. [선택] 롱폼→쇼츠 변환 (yt-dlp → Whisper STT → 하이라이트 추출 → FFmpeg)
7. 최종 파일 다운로드 또는 R2 저장

## 코딩 규칙
- 모든 API 키는 환경변수(.env)로 관리
- 에러 처리 필수 (API 실패 시 재시도 로직)
- 한국어 주석 사용
- 타입 힌트 사용 (Python)
- TypeScript 사용 (Frontend)
- 커밋 메시지는 한국어로

## 프로젝트 구조 (중요 - 절대 잊지 말 것)
- 프론트엔드 경로: D:\app\shorts-factory\frontend
- app 디렉토리: frontend\app\ (src\app\ 아님! src 폴더 없음!)
- layout.tsx 위치: frontend\app\layout.tsx
- page.tsx 위치: frontend\app\page.tsx
- 컴포넌트: frontend\components\

## 현재 버전
- Next.js: 15.1.0
- React: 18.3.1
- react-dom: 18.3.1

## 반복된 실수 기록
- src\app\ 경로로 접근하면 안 됨 → app\ 으로 접근해야 함
- Next.js 16은 불안정 → 15.1.0 사용
- Turbopack 대신 기본 webpack 사용
