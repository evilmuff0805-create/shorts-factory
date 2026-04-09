"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, ConvertShort } from "@/lib/api";

export default function ConvertPage() {
  const [url, setUrl] = useState("");
  const [count, setCount] = useState("3");
  const [clipDuration, setClipDuration] = useState("60");
  const [loading, setLoading] = useState(false);
  const [shorts, setShorts] = useState<ConvertShort[]>([]);
  const [warning, setWarning] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleConvert() {
    if (!url.trim()) return;
    setLoading(true);
    setShorts([]);
    setWarning(null);
    setError("");

    try {
      const res = await api.convertVideo(url, Number(count), Number(clipDuration));
      setShorts(res.shorts);
      setWarning(res.warning);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "변환 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">롱비디오 숏츠 변환</h2>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>설정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url">유튜브 URL</Label>
            <Input
              id="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>클립 수</Label>
              <Select value={count} onValueChange={(v) => v && setCount(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 5, 10].map((n) => (
                    <SelectItem key={n} value={String(n)}>
                      {n}개
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>클립 길이 (초)</Label>
              <Select value={clipDuration} onValueChange={(v) => v && setClipDuration(v)}>
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
          <Button onClick={handleConvert} disabled={loading || !url.trim()} className="w-full">
            {loading ? "변환 중..." : "변환 시작"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {warning && (
        <p className="text-sm text-yellow-500 mb-4">{warning}</p>
      )}

      {shorts.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">변환 결과 ({shorts.length}개)</h3>
          {shorts.map((s) => (
            <Card key={s.index}>
              <CardHeader>
                <CardTitle className="text-base">클립 #{s.index + 1}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {s.highlight_text && (
                  <p className="text-sm text-muted-foreground italic">"{s.highlight_text}"</p>
                )}
                <video
                  controls
                  className="w-full rounded-md"
                  src={`data:video/mp4;base64,${s.video}`}
                />
                <a href={`data:video/mp4;base64,${s.video}`} download={`clip_${s.index + 1}.mp4`}>
                  <Button variant="outline" size="sm">
                    다운로드
                  </Button>
                </a>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
