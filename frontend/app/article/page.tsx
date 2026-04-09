"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { api, ArticleAnalysis, ArticleGenerateResponse } from "@/lib/api";

const STYLES = [
  { value: "교육", label: "교육" },
  { value: "글로벌 정세", label: "글로벌 정세" },
  { value: "트렌드", label: "트렌드" },
  { value: "문화", label: "문화" },
  { value: "AI·기술", label: "AI·기술" },
  { value: "과학", label: "과학" },
  { value: "비즈니스", label: "비즈니스" },
  { value: "엔터테인먼트", label: "엔터테인먼트" },
  { value: "스포츠", label: "스포츠" },
  { value: "튜토리얼", label: "튜토리얼" },
];

const VOICES = [
  { value: "changsu", label: "창수 (남성)" },
  { value: "dabin", label: "다빈 (여성)" },
  { value: "inhwa", label: "인화 (여성)" },
  { value: "hana", label: "하나 (여성)" },
];

const IMAGE_STYLES = [
  { value: "realistic", label: "실사" },
  { value: "anime", label: "애니메이션" },
  { value: "pixar3d", label: "픽사 3D" },
];

export default function ArticlePage() {
  const [articleTitle, setArticleTitle] = useState("");
  const [articleBody, setArticleBody] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<ArticleAnalysis | null>(null);
  const [analyzeError, setAnalyzeError] = useState("");

  const [selectedTopic, setSelectedTopic] = useState("");
  const [customTopic, setCustomTopic] = useState("");
  const [style, setStyle] = useState("트렌드");
  const [duration, setDuration] = useState("30");
  const [voice, setVoice] = useState("changsu");
  const [imageStyle, setImageStyle] = useState("pixar3d");
  const [animate, setAnimate] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<ArticleGenerateResponse | null>(null);
  const [generateError, setGenerateError] = useState("");

  const finalTopic = customTopic || selectedTopic;

  async function handleAnalyze() {
    if (articleBody.trim().length < 10) return;
    setAnalyzing(true);
    setAnalysis(null);
    setAnalyzeError("");
    setResult(null);
    setSelectedTopic("");
    setCustomTopic("");

    try {
      const res = await api.analyzeArticle(articleTitle.trim(), articleBody.trim());
      setAnalysis(res);
      if (res.suggested_topics.length > 0) {
        setSelectedTopic(res.suggested_topics[0]);
      }
    } catch (e: unknown) {
      setAnalyzeError(e instanceof Error ? e.message : "분석 실패");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleGenerate() {
    if (!finalTopic) return;
    setGenerating(true);
    setResult(null);
    setGenerateError("");

    try {
      const res = await api.generateFromArticle(
        finalTopic,
        style,
        Number(duration),
        voice,
        imageStyle,
        analysis?.summary || "",
        animate
      );
      setResult(res);
    } catch (e: unknown) {
      setGenerateError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">기사 분석</h2>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>기사 텍스트 입력</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="article-title">기사 제목 (선택)</Label>
            <Input
              id="article-title"
              placeholder="기사 제목을 입력하세요 (없어도 됩니다)"
              value={articleTitle}
              onChange={(e) => setArticleTitle(e.target.value)}
              disabled={analyzing}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="article-body">기사 본문</Label>
            <textarea
              id="article-body"
              className="w-full min-h-[200px] p-3 rounded-md border border-input bg-background text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="기사 본문을 복사해서 붙여넣으세요..."
              value={articleBody}
              onChange={(e) => setArticleBody(e.target.value)}
              disabled={analyzing}
            />
            <p className="text-xs text-muted-foreground">
              {articleBody.length}자 입력됨 {articleBody.length > 0 && articleBody.length < 10 && "· 최소 10자 이상 입력해주세요"}
            </p>
          </div>
          <Button onClick={handleAnalyze} disabled={analyzing || articleBody.trim().length < 10} className="w-full">
            {analyzing ? "분석 중..." : "기사 분석하기"}
          </Button>
          {analyzeError && <p className="text-sm text-destructive">{analyzeError}</p>}
        </CardContent>
      </Card>

      {analysis && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">분석 결과</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-1">기사 제목</h4>
              <p className="text-sm text-muted-foreground">{analysis.title}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">요약</h4>
              <p className="text-sm">{analysis.summary}</p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">핵심 포인트</h4>
              <div className="flex flex-wrap gap-2">
                {analysis.key_points.map((point, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {point}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-2">추천 쇼츠 주제 (클릭하여 선택)</h4>
              <div className="space-y-2">
                {analysis.suggested_topics.map((topic, i) => (
                  <button
                    key={i}
                    onClick={() => { setSelectedTopic(topic); setCustomTopic(""); }}
                    className={`w-full text-left p-3 rounded-lg border text-sm transition-colors ${
                      selectedTopic === topic && !customTopic
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="custom-topic">또는 직접 입력</Label>
              <Input
                id="custom-topic"
                placeholder="원하는 주제를 직접 입력..."
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {analysis && finalTopic && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">쇼츠 생성 설정</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 rounded-lg bg-muted">
              <p className="text-sm"><strong>선택된 주제:</strong> {finalTopic}</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>스타일</Label>
                <Select value={style} onValueChange={(v) => v && setStyle(v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {STYLES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>영상 길이</Label>
                <Select value={duration} onValueChange={(v) => v && setDuration(v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30초</SelectItem>
                    <SelectItem value="60">60초</SelectItem>
                    <SelectItem value="90">90초</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>음성</Label>
                <Select value={voice} onValueChange={(v) => v && setVoice(v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {VOICES.map((v) => (
                      <SelectItem key={v.value} value={v.value}>{v.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>이미지 스타일</Label>
                <Select value={imageStyle} onValueChange={(v) => v && setImageStyle(v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {IMAGE_STYLES.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="animate-check"
                checked={animate}
                onChange={(e) => setAnimate(e.target.checked)}
                className="w-4 h-4 rounded border-input"
              />
              <label htmlFor="animate-check" className="text-sm">
                이미지 애니메이션 적용 (MiniMax Hailuo — 시간이 오래 걸릴 수 있음)
              </label>
            </div>
            <Button onClick={handleGenerate} disabled={generating} className="w-full">
              {generating ? "쇼츠 생성 중... (최대 수 분 소요)" : "쇼츠 생성하기"}
            </Button>
            {generateError && <p className="text-sm text-destructive">{generateError}</p>}
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              생성 완료
              <Badge variant="outline">{result.duration.toFixed(1)}초</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <video
              controls
              className="w-full rounded-md"
              src={`data:video/mp4;base64,${result.video}`}
            />
            <div className="flex gap-2">
              <a href={`data:video/mp4;base64,${result.video}`} download="article_shorts.mp4">
                <Button variant="outline" size="sm">영상 다운로드</Button>
              </a>
            </div>
            <div>
              <h4 className="font-semibold mb-1">자막 미리보기</h4>
              <div className="text-sm text-muted-foreground space-y-1">
                {result.subtitles.map((sub, i) => (
                  <p key={i}>{i + 1}. {sub}</p>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
