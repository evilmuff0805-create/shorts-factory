"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface Result {
  topic: string;
  video: string | null;
  error: string | null;
}

export default function BatchPage() {
  const [topicsText, setTopicsText] = useState("");
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<Result[]>([]);
  const [doneCount, setDoneCount] = useState(0);

  async function handleBatch() {
    const topics = topicsText
      .split("\n")
      .map((t) => t.trim())
      .filter(Boolean);
    if (!topics.length) return;

    setRunning(true);
    setResults([]);
    setDoneCount(0);

    for (const topic of topics) {
      try {
        const scriptRes = await api.generateScript(topic, "educational", 60);
        const imagesRes = await api.generateImages(scriptRes.script);
        const ttsRes = await api.generateTts(scriptRes.script);
        const renderRes = await api.renderVideo(
          imagesRes.images.map((i) => i.url),
          ttsRes.audio,
          scriptRes.script
        );
        setResults((prev) => [...prev, { topic, video: renderRes.video, error: null }]);
      } catch (e: unknown) {
        setResults((prev) => [
          ...prev,
          { topic, error: e instanceof Error ? e.message : "오류", video: null },
        ]);
      }
      setDoneCount((n) => n + 1);
    }

    setRunning(false);
  }

  const totalTopics = topicsText.split("\n").filter((t) => t.trim()).length;

  return (
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">일괄 생성</h2>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>주제 목록</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topics">주제 (줄바꿈으로 구분)</Label>
            <Textarea
              id="topics"
              placeholder={"인공지능의 미래\n기후변화와 환경\n우주 역사 최신 지식"}
              value={topicsText}
              onChange={(e) => setTopicsText(e.target.value)}
              rows={6}
              disabled={running}
            />
          </div>
          <Button onClick={handleBatch} disabled={running || !topicsText.trim()} className="w-full">
            {running ? `생성 중... (${doneCount}/${totalTopics})` : "일괄 생성 시작"}
          </Button>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">
            결과 ({doneCount}/{totalTopics})
          </h3>
          {results.map((r, i) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {r.topic}
                  {r.error ? (
                    <Badge variant="destructive">실패</Badge>
                  ) : (
                    <Badge>완료</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {r.error ? (
                  <p className="text-sm text-destructive">{r.error}</p>
                ) : r.video ? (
                  <div className="space-y-2">
                    <video
                      controls
                      className="w-full rounded-md"
                      src={`data:video/mp4;base64,${r.video}`}
                    />
                    <a href={`data:video/mp4;base64,${r.video}`} download={`${r.topic}.mp4`}>
                      <Button variant="outline" size="sm">
                        다운로드
                      </Button>
                    </a>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
