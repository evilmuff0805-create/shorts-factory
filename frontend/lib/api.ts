// 백엔드 API 응답 타입

export interface ScriptResponse {
  script: string;
  scene_count: number;
  subtitles: string[];
}

export interface ImageItem {
  scene: number;
  url: string; // base64 문자열 (data: URL 접두사 없음)
}

export interface ImagesResponse {
  images: ImageItem[];
}

export interface TtsResponse {
  audio: string; // base64 mp3
  duration_estimate: number;
}

export interface AnimateResponse {
  clips: string[]; // base64 mp4 clips
}

export interface RenderResponse {
  video: string; // base64 mp4
  duration: number;
}

export interface ConvertShort {
  index: number;
  video: string; // base64 mp4
  highlight_text: string;
}

export interface ConvertResponse {
  shorts: ConvertShort[];
  warning: string | null;
}

export interface NewsShort {
  title: string;
  video: string; // base64 mp4
  script: string;
}

export interface NewsShortsResponse {
  news_shorts: NewsShort[];
  skipped: number;
  warning: string | null;
}

export interface ArticleAnalysis {
  title: string;
  url: string;
  summary: string;
  key_points: string[];
  suggested_topics: string[];
}

export interface ArticleGenerateResponse {
  video: string;
  duration: number;
  script: string;
  subtitles: string[];
}

export interface TrendingItem {
  title: string;
  channel: string;
  view_count: string;
  video_id: string;
  category_id: string;
  published_at: string;
  description: string;
}

export interface Recommendation {
  title: string;
  summary: string;
  genre: string;
  score: number;
}

export interface TrendingResponse {
  trending: TrendingItem[];
  recommendations: Recommendation[];
}

export interface MetadataResponse {
  title: string;
  description: string;
  hashtags: string[];
}

async function requestLong<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10분

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText);
      throw new Error(`[${res.status}] ${text}`);
    }

    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function request<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`[${res.status}] ${text}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  generateScript(topic: string, style: string, duration: number): Promise<ScriptResponse> {
    return request<ScriptResponse>("/api/script", { topic, style, duration });
  },

  generateImages(script: string, image_style = "pixar3d"): Promise<ImagesResponse> {
    return request<ImagesResponse>("/api/images", { script, image_style });
  },

  generateTts(script: string, voice = "TX3LPaxmHKxFdv7VOQHJ"): Promise<TtsResponse> {
    return request<TtsResponse>("/api/tts", { script, voice });
  },

  animateImages(images: string[]): Promise<AnimateResponse> {
    return requestLong<AnimateResponse>("/api/animate", { images });
  },

  renderVideo(images: string[], audio: string, subtitles: string[]): Promise<RenderResponse> {
    return request<RenderResponse>("/api/render", { images, audio, subtitles });
  },

  convertVideo(url: string, count: number, clip_duration: number): Promise<ConvertResponse> {
    return request<ConvertResponse>("/api/long-to-short", { url, count, clip_duration });
  },

  generateNewsShorts(
    keyword: string,
    category: string,
    count: number
  ): Promise<NewsShortsResponse> {
    return request<NewsShortsResponse>("/api/news-shorts", { keyword, category, count });
  },

  fetchTrending(category?: string, count: number = 10): Promise<TrendingResponse> {
    return request<TrendingResponse>("/api/trending", { category: category || null, count });
  },

  generateMetadata(script: string, topic: string, genre: string): Promise<MetadataResponse> {
    return request<MetadataResponse>("/api/metadata", { script, topic, genre });
  },

  analyzeArticle(title: string, body: string): Promise<ArticleAnalysis> {
    return request<ArticleAnalysis>("/api/article/analyze", { title, body });
  },

  generateFromArticle(
    topic: string,
    style: string,
    duration: number,
    voice: string,
    image_style: string,
    article_context: string,
    animate: boolean = false
  ): Promise<ArticleGenerateResponse> {
    return requestLong<ArticleGenerateResponse>("/api/article/generate", {
      topic, style, duration, voice, image_style, article_context, animate
    });
  },
};
