"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, type Recommendation } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const CATEGORIES = [
  { value: "all", label: "전체" },
  { value: "27", label: "교육" },
  { value: "28", label: "과학기술" },
  { value: "25", label: "뉴스/정치" },
  { value: "24", label: "엔터테인먼트" },
  { value: "17", label: "스포츠" },
];

export default function HomePage() {
  const router = useRouter();
  const [category, setCategory] = useState("all");
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadTrending(cat: string) {
    setLoading(true);
    setError("");
    try {
      const res = await api.fetchTrending(cat === "all" ? undefined : cat);
      setRecommendations(res.recommendations);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "트렌드를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTrending(category);
  }, []);

  function handleCategoryChange(val: string | null) {
    if (val) { setCategory(val); loadTrending(val); }
  }

  function handleCreate(item: Recommendation) {
    router.push(`/create?topic=${encodeURIComponent(item.title)}&genre=${encodeURIComponent(item.genre)}`);
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-2xl font-bold">오늘의 트렌드 소재</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => loadTrending(category)}
          disabled={loading}
        >
          새로고침
        </Button>
      </div>

      <div className="mb-6 w-48">
        <Select value={category} onValueChange={handleCategoryChange}>
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

      {loading && (
        <p className="text-muted-foreground">트렌드 분석 중...</p>
      )}

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {!loading && !error && (
        <div className="grid gap-4">
          {recommendations.map((item, idx) => (
            <Card key={idx}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base font-bold">{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">{item.summary}</p>
                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <Badge variant="secondary">{item.genre}</Badge>
                    <Badge variant="outline">인기도 {item.score}</Badge>
                  </div>
                  <Button size="sm" onClick={() => handleCreate(item)}>
                    이 소재로 생성 →
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
