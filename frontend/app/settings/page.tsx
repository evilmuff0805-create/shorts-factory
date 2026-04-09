"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const KEYS = [
  { id: "openai_api_key", label: "OpenAI API Key", placeholder: "sk-..." },
  { id: "gemini_api_key", label: "Gemini API Key", placeholder: "AIza..." },
];

export default function SettingsPage() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const loaded: Record<string, string> = {};
    for (const { id } of KEYS) {
      loaded[id] = localStorage.getItem(id) ?? "";
    }
    setValues(loaded);
  }, []);

  function handleSave() {
    for (const { id } of KEYS) {
      localStorage.setItem(id, values[id] ?? "");
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="p-8 max-w-xl">
      <h2 className="text-2xl font-bold mb-6">설정</h2>

      <Card>
        <CardHeader>
          <CardTitle>API 키 (메모용)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            실제 API 키는 백엔드 .env 파일에서 관리됩니다. 여기에 입력한 값은
            브라우저 localStorage에만 저장됩니다.
          </p>
          {KEYS.map(({ id, label, placeholder }) => (
            <div key={id} className="space-y-2">
              <Label htmlFor={id}>{label}</Label>
              <Input
                id={id}
                type="password"
                placeholder={placeholder}
                value={values[id] ?? ""}
                onChange={(e) =>
                  setValues((prev) => ({ ...prev, [id]: e.target.value }))
                }
              />
            </div>
          ))}
          <Button onClick={handleSave} className="w-full">
            {saved ? "저장됨!" : "저장"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
