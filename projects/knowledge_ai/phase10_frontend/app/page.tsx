/**
 * Phase 10: Next.js フロントエンド - ナレッジ一覧ページ
 * =========================================================
 * 学習目標:
 *   - React Server Components（RSC）と Client Components の使い分け
 *   - TanStack Query によるサーバー状態管理
 *   - TypeScript の型安全なAPIクライアント設計
 *
 * 考えてほしい疑問:
 *   Q1. このページが "use client" を使わない理由は？（Server Component のメリット）
 *   Q2. fetch() に cache: "no-store" を付けるとSSRになり、"force-cache" はSSGになる。
 *       ナレッジ一覧にはどちらが適切か？
 *   Q3. Suspense boundary を使う理由は？（ストリーミングSSR）
 *
 * セットアップ:
 *   npx create-next-app@latest knowledge-ai-frontend --typescript --tailwind --app
 *   npm install @tanstack/react-query axios
 */

import { Suspense } from "react";
import { NoteList } from "./components/NoteList";
import { SearchBar } from "./components/SearchBar";
import { AskAI } from "./components/AskAI";

// Server Component（サーバーで実行される - APIキー不要・SEO最適）
export default async function HomePage({
  searchParams,
}: {
  searchParams: { q?: string; tag?: string; page?: string };
}) {
  return (
    <main className="container mx-auto px-4 py-8 max-w-5xl">
      <h1 className="text-3xl font-bold mb-8 text-gray-900">
        KnowledgeAI
      </h1>

      {/* AIへの質問フォーム */}
      <section className="mb-8 p-6 bg-blue-50 rounded-xl border border-blue-200">
        <h2 className="text-lg font-semibold mb-3">AIに質問する</h2>
        <AskAI />
      </section>

      {/* 検索バー（Client Component） */}
      <SearchBar initialQuery={searchParams.q} initialTag={searchParams.tag} />

      {/* ノート一覧（Suspenseでストリーミング） */}
      <Suspense fallback={<NoteListSkeleton />}>
        <NoteList
          query={searchParams.q}
          tag={searchParams.tag}
          page={Number(searchParams.page) || 1}
        />
      </Suspense>
    </main>
  );
}

function NoteListSkeleton() {
  return (
    <div className="space-y-4 mt-6">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
      ))}
    </div>
  );
}
