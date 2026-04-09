"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-8">
      <h2 className="text-xl font-bold mb-2">오류가 발생했습니다</h2>
      <button onClick={reset} className="text-sm underline">
        다시 시도
      </button>
    </div>
  );
}
