/**
 * AskAI.tsx - Client Component でAIへの質問フォームを実装
 * ==========================================================
 * "use client" が必要な理由:
 *   - useState / useEffect を使う
 *   - ユーザーのインタラクション（onClick, onChange）を扱う
 *   - ストリーミングレスポンスをリアルタイム表示する
 *
 * 考えてほしい疑問:
 *   Q1. なぜ fetch ではなく EventSource（SSE）でストリーミングを受け取るのか？
 *   Q2. AbortController は何のために使うのか？（ユーザーがキャンセルした場合）
 *   Q3. エラー状態・ローディング状態・成功状態の管理が複雑になってきた。
 *       TanStack Query の useMutation を使うとどう改善できるか？
 *
 * [実装してみよう]
 *   - ストリーミングレスポンス（stream=true）でリアルタイムに文字が表示されるようにする
 *   - 回答の出典ノートをクリックすると詳細ページに飛べるようにする
 */

"use client";

import { useState, useRef } from "react";

interface Source {
  title: string;
  score: number;
  note_id: number;
}

interface AIResponse {
  answer: string;
  sources: Source[];
}

export function AskAI() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AIResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    // 前のリクエストをキャンセル
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch("/api/v1/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(`APIエラー: ${res.status}`);
      }

      const data: AIResponse = await res.json();
      setResponse(data);
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setQuestion(e.target.value)
          }
          placeholder="ナレッジベースに質問する... 例: 「Dockerとは何ですか？」"
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !question.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? "考え中..." : "質問"}
        </button>
      </form>

      {error && <p className="mt-3 text-red-600 text-sm">{error}</p>}

      {response && (
        <div className="mt-4 space-y-3">
          <div className="p-4 bg-white rounded-lg border border-blue-200">
            <p className="text-gray-800 whitespace-pre-wrap">
              {response.answer}
            </p>
          </div>

          {response.sources.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">参照したナレッジ:</p>
              <div className="flex gap-2 flex-wrap">
                {response.sources.map((src) => (
                  <a
                    key={src.note_id}
                    href={`/notes/${src.note_id}`}
                    className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700"
                  >
                    {src.title} ({Math.round(src.score * 100)}%)
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
