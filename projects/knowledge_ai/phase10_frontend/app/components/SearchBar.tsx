/**
 * SearchBar.tsx - 検索バー（Client Component）
 * URL パラメータを操作してServer Componentの再レンダリングをトリガーする。
 */
"use client";

import { useRouter, usePathname } from "next/navigation";
import { useCallback, useState, useTransition } from "react";

export function SearchBar({
  initialQuery,
  initialTag,
}: {
  initialQuery?: string;
  initialTag?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [query, setQuery] = useState(initialQuery ?? "");
  const [isPending, startTransition] = useTransition();

  const handleSearch = useCallback(
    (q: string) => {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (initialTag) params.set("tag", initialTag);

      // useTransition: ナビゲーション中もUIをレスポンシブに保つ
      startTransition(() => {
        router.push(`${pathname}?${params.toString()}`);
      });
    },
    [router, pathname, initialTag]
  );

  return (
    <div className="flex gap-2">
      <input
        type="search"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          // 入力から500ms後に自動検索（Debounce）
          // [実装してみよう] useDebounce フックを作って実装する
        }}
        onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
        placeholder="ノートを検索..."
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
      />
      <button
        onClick={() => handleSearch(query)}
        disabled={isPending}
        className="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700"
      >
        {isPending ? "..." : "検索"}
      </button>
    </div>
  );
}
