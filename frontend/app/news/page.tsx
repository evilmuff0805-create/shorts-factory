"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { api, NewsShort } from "@/lib/api";

const CATEGORIES = [
  { value: "technology", label: "기술" },
  { value: "science", label: "과학" },
  { value: "business", label: "비즈니스" },
  { value: "health", label: "건강" },
  { value: "entertainment", label: "엔터테인먼트" },
  { value: "sports", label: "스포츠" },
];

export default function NewsPage() {
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("technology");
  const [count, setCount] = useState("3");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<NewsShort[]>([]);
  const [skipped, setSkipped] = useState(0);
  const [warning, setWarning] = useState<string | null>(null);
  const [error, setError] = useState("");

  const countNum = Number(count);

  async function handleGenerate() {
    setLoading(true);
    setResults([]);
    setSkipped(0);
    setWarning(null);
    setError("");

    try {
      const res = await api.generateNewsShorts(keyword || category, category, countNum);
      setResults(res.news_shorts);
      setSkipped(res.skipped);
      setWarning(res.warning);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "생성 실패");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">뉴스 숏츠</h2>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>설정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="keyword">키워드 (선택)</Label>
            <Input
              id="keyword"
              placeholder="예: AI, ChatGPT (비우면 카테고리 전체)"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              disabled={loading}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>카테고리</Label>
              <Select value={category} onValueChange={(v) => v && setCategory(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>개수</Label>
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
          </div>
          {countNum >= 5 && (
            <p className="text-sm text-yellow-500">
              ⚠️ {countNum}개 생성 시 API 비용이 높을 수 있습니다.
            </p>
          )}
          <Button onClick={handleGenerate} disabled={loading} className="w-full">
            {loading ? "생성 중..." : "뉴스 쇼츠 생성"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {warning && <p className="text-sm text-yellow-500 mb-4">{warning}</p>}
      {skipped > 0 && (
        <p className="text-sm text-muted-foreground mb-4">{skipped}개 기사 건너뜀</p>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">결과 ({results.length}개)</h3>
          {results.map((item, i) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {item.title}
                  <Badge variant="outline">뉴스</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <video
                  controls
                  className="w-full rounded-md"
                  src={`data:video/mp4;base64,${item.video}`}
                />
                <a href={`data:video/mp4;base64,${item.video}`} download={`news_${i + 1}.mp4`}>
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
