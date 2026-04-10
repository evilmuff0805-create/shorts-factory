"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { api, type MetadataResponse } from "@/lib/api";

type Stage = "idle" | "script" | "images" | "tts" | "animate" | "render" | "done" | "error";

const STAGES: Stage[] = ["script", "images", "tts", "animate", "render"];
const STAGE_LABELS: Record<string, string> = {
  script: "1. 스크립트 생성",
  images: "2. 이미지 생성",
  tts: "3. 음성 합성",
  animate: "4. 이미지 애니메이션",
  render: "5. 영상 렌더링",
};

function CreatePageInner() {
  const searchParams = useSearchParams();

  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("교육");
  const [duration, setDuration] = useState("60");
  const [voice, setVoice] = useState("changsu");
  const [stage, setStage] = useState<Stage>("idle");
  const [progress, setProgress] = useState(0);
  const [videoB64, setVideoB64] = useState<string | null>(null);
  const [useAnimate, setUseAnimate] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [scriptText, setScriptText] = useState("");
  const [imageStyle, setImageStyle] = useState("pixar3d");

  const [metadata, setMetadata] = useState<MetadataResponse | null>(null);
  const [metaLoading, setMetaLoading] = useState(false);

  const [copiedField, setCopiedField] = useState<string | null>(null);

  // URL 파라미터로 주제/장르 자동입력
  useEffect(() => {
    const topicParam = searchParams.get("topic");
    const genreParam = searchParams.get("genre");
    if (topicParam) setTopic(topicParam);
    if (genreParam) setStyle(genreParam);
  }, [searchParams]);

  const handleRegenerate = () => {
    setStage("idle");
    setVideoB64(null);
    setProgress(0);
    setErrorMsg("");
  };

  async function handleGenerate() {
    if (!topic.trim()) return;
    setStage("script");
    setProgress(10);
    setVideoB64(null);
    setErrorMsg("");
    setMetadata(null);

    try {
      const scriptRes = await api.generateScript(topic, style, Number(duration));
      setScriptText(scriptRes.subtitles.join(". "));
      setStage("images");
      setProgress(30);

      const imagesRes = await api.generateImages(scriptRes.script, imageStyle);
      setStage("tts");
      setProgress(55);

      const ttsRes = await api.generateTts(scriptRes.subtitles.join(". "), voice);

      // animate 단계 (선택)
      let finalImages = imagesRes.images.map((i) => i.url);
      if (useAnimate) {
        setStage("animate");
        setProgress(65);
        const animateRes = await api.animateImages(finalImages);
        finalImages = animateRes.clips;
      }

      setStage("render");
      setProgress(useAnimate ? 80 : 75);
      const renderRes = await api.renderVideo(
        finalImages,
        ttsRes.audio,
        scriptRes.subtitles
      );
      setProgress(100);
      setStage("done");
      setVideoB64(renderRes.video);

      // 메타데이터 자동 생성
      setMetaLoading(true);
      try {
        const metaRes = await api.generateMetadata(scriptRes.script, topic, style);
        setMetadata(metaRes);
      } catch {
        // 메타데이터 실패는 무시 (영상은 이미 완성)
      } finally {
        setMetaLoading(false);
      }
    } catch (e: unknown) {
      setStage("error");
      setErrorMsg(e instanceof Error ? e.message : "알 수 없는 오류");
    }
  }

  async function copyToClipboard(text: string, field: string) {
    await navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  }

  const currentStageIdx = STAGES.indexOf(stage as (typeof STAGES)[number]);

  return (
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">영상 생성</h2>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>설정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">주제</Label>
            <Input
              id="topic"
              placeholder="예: 인공지능의 미래"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={stage !== "idle" && stage !== "done" && stage !== "error"}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>스타일</Label>
              <Select value={style} onValueChange={(v) => v && setStyle(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="교육">교육</SelectItem>
                  <SelectItem value="글로벌 정세">글로벌 정세</SelectItem>
                  <SelectItem value="트렌드">트렌드</SelectItem>
                  <SelectItem value="문화">문화</SelectItem>
                  <SelectItem value="AI·기술">AI·기술</SelectItem>
                  <SelectItem value="과학">과학</SelectItem>
                  <SelectItem value="비즈니스">비즈니스</SelectItem>
                  <SelectItem value="엔터테인먼트">엔터테인먼트</SelectItem>
                  <SelectItem value="스포츠">스포츠</SelectItem>
                  <SelectItem value="튜토리얼">튜토리얼</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>길이 (초)</Label>
              <Select value={duration} onValueChange={(v) => v && setDuration(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30초</SelectItem>
                  <SelectItem value="60">60초</SelectItem>
                  <SelectItem value="90">90초</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>음성 선택</Label>
            <Select value={voice} onValueChange={(v) => v && setVoice(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="changsu">박창수 (남성 스토리텔링)</SelectItem>
                <SelectItem value="dabin">다빈 (남성 다큐멘터리)</SelectItem>
                <SelectItem value="inhwa">인화 (여성 다큐멘터리)</SelectItem>
                <SelectItem value="hana">하나 (여성 스토리텔링)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>그림체 선택</Label>
            <Select value={imageStyle} onValueChange={(v) => v && setImageStyle(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="realistic">실사 (Photorealistic)</SelectItem>
                <SelectItem value="anime">애니메이션 (Anime)</SelectItem>
                <SelectItem value="pixar3d">픽사 3D (Pixar 3D)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-300 mt-2">
              <input
                type="checkbox"
                checked={useAnimate}
                onChange={(e) => setUseAnimate(e.target.checked)}
                className="rounded"
              />
              이미지 애니메이션 (AI 동영상 변환 · 클립당 ~$0.19)
            </label>
          <Button
            onClick={handleGenerate}
            disabled={!topic.trim() || (stage !== "idle" && stage !== "done" && stage !== "error")}
            className="w-full"
          >
            생성 시작
          </Button>
        </CardContent>
      </Card>

      {stage !== "idle" && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>진행 상황</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Progress value={progress} />
            <div className="flex gap-2 flex-wrap">
              {STAGES.map((s, idx) => (
                <span
                  key={s}
                  className={
                    idx < currentStageIdx
                      ? "text-sm text-muted-foreground line-through"
                      : idx === currentStageIdx && stage !== "done" && stage !== "error"
                      ? "text-sm font-semibold text-primary"
                      : "text-sm text-muted-foreground"
                  }
                >
                  {STAGE_LABELS[s]}
                </span>
              ))}
            </div>
            {stage === "error" && (
              <p className="text-sm text-destructive">{errorMsg}</p>
            )}
          </CardContent>
        </Card>
      )}

      {stage === "done" && videoB64 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>완성된 영상</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <video
              controls
              className="w-full rounded-md"
              src={`data:video/mp4;base64,${videoB64}`}
            />
            <div className="flex gap-3">
              <a
                href={`data:video/mp4;base64,${videoB64}`}
                download="shorts.mp4"
                className="block flex-1"
              >
                <Button variant="outline" className="w-full">
                  다운로드
                </Button>
              </a>
              <button
                onClick={handleRegenerate}
                className="flex-1 bg-gray-600 text-white py-3 rounded-lg font-semibold hover:bg-gray-700"
              >
                다시 생성
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {stage === "done" && (
        <Card>
          <CardHeader>
            <CardTitle>유튜브 업로드용</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {metaLoading && (
              <p className="text-sm text-muted-foreground">메타데이터 생성 중...</p>
            )}
            {metadata && (
              <>
                <div className="space-y-2">
                  <Label>제목</Label>
                  <div className="flex gap-2">
                    <Input readOnly value={metadata.title} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(metadata.title, "title")}
                    >
                      {copiedField === "title" ? "복사됨!" : "복사"}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>상세설명</Label>
                  <div className="flex gap-2 items-start">
                    <Textarea readOnly value={metadata.description} rows={6} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(metadata.description, "description")}
                    >
                      {copiedField === "description" ? "복사됨!" : "복사"}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>해시태그</Label>
                  <div className="flex gap-2">
                    <Input readOnly value={metadata.hashtags.join(" ")} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(metadata.hashtags.join(" "), "hashtags")}
                    >
                      {copiedField === "hashtags" ? "복사됨!" : "복사"}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">로딩 중...</div>}>
      <CreatePageInner />
    </Suspense>
  );
}
