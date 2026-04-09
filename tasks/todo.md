# Shorts Factory — 작업 체크리스트

## Phase 1: 프로젝트 초기 셋업 ✅
- [x] CLAUDE.md 생성
- [x] 모노레포 폴더 구조 생성 (frontend + backend)
- [x] .gitignore, .env.example, README.md

## Phase 2: 백엔드 핵심 파이프라인
- [ ] AI 대본 생성 (`/api/script`) — Gemini 2.5 Flash 연동
- [ ] AI 이미지 생성 (`/api/images`) — GPT Image API 연동
- [ ] TTS 음성 생성 (`/api/tts`) — OpenAI TTS-1 연동
- [ ] FFmpeg 영상 합성 (`/api/render`) — 이미지 + 음성 + 자막
- [ ] Whisper 자막 생성 — STT → SRT 변환
- [ ] Cloudflare R2 업로드 유틸

## Phase 3: 롱폼→쇼츠 변환
- [ ] yt-dlp 다운로드 서비스
- [ ] Whisper 전체 대본 추출
- [ ] 하이라이트 구간 추출 (Gemini)
- [ ] FFmpeg 클립 추출 + 쇼츠 포맷 변환 (`/api/long-to-short`)

## Phase 4: 뉴스 쇼츠 자동화
- [ ] feedparser Google News RSS 수집 (`/api/news-shorts`)
- [ ] 뉴스 → 대본 자동 변환
- [ ] 대량 생산 큐 시스템

## Phase 5: 프론트엔드 UI
- [ ] 메인 대시보드 — 최근 생성 쇼츠 목록
- [ ] 새 쇼츠 만들기 — 주제 입력 → 파이프라인 실행
- [ ] 대량 생산 — CSV/목록 업로드
- [ ] 롱폼→쇼츠 변환 — URL 입력
- [ ] 설정 페이지 — API 키 관리

## Working Notes
- 백엔드 포트: 8000, 프론트엔드 포트: 3000
- API 프록시: Next.js `/api/*` → `http://localhost:8000`
- 영상 포맷: 9:16 (1080×1920), 최대 60초
- 모든 API 키는 .env로만 관리 (절대 하드코딩 금지)
