/**
 * NoteList.tsx - Server Component でノート一覧を取得・表示
 * ==========================================================
 * Server Component の強み:
 *   - APIキーをクライアントに渡さずサーバー側で fetch できる
 *   - JavaScriptバンドルに含まれない（クライアントに送られない）
 *   - データ取得がサーバーで完結するため初期表示が速い
 *
 * 考えてほしい疑問:
 *   Q1. このコンポーネントで useState/useEffect が使えない理由は？
 *   Q2. エラーはどこでハンドリングすべきか？（error.tsx）
 *   Q3. 無限スクロールを実装するとしたら Server Component か Client Component か？
 */

import Link from "next/link";

interface Tag {
  id: number;
  name: string;
}

interface Note {
  id: number;
  title: string;
  content: string;
  tags: Tag[];
  created_at: string;
}

interface NoteListResponse {
  items: Note[];
  total: number;
  page: number;
  per_page: number;
}

async function fetchNotes(params: {
  q?: string;
  tag?: string;
  page: number;
}): Promise<NoteListResponse> {
  const url = new URL(`${process.env.API_URL}/api/v1/notes`);
  if (params.q) url.searchParams.set("q", params.q);
  if (params.tag) url.searchParams.set("tag", params.tag);
  url.searchParams.set("page", String(params.page));

  const res = await fetch(url.toString(), {
    // 30秒間キャッシュ（頻繁に更新されるので長くしない）
    next: { revalidate: 30 },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function NoteList({
  query,
  tag,
  page,
}: {
  query?: string;
  tag?: string;
  page: number;
}) {
  const data = await fetchNotes({ q: query, tag, page });

  if (data.items.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {query ? `"${query}" に一致するノートがありません` : "まだノートがありません"}
      </div>
    );
  }

  return (
    <div className="mt-6 space-y-4">
      <p className="text-sm text-gray-500">{data.total} 件のノート</p>

      {data.items.map((note) => (
        <NoteCard key={note.id} note={note} />
      ))}

      <Pagination total={data.total} page={page} perPage={data.per_page} />
    </div>
  );
}

function NoteCard({ note }: { note: Note }) {
  return (
    <Link href={`/notes/${note.id}`} className="block">
      <article className="p-5 border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">{note.title}</h2>
        <p className="text-gray-600 text-sm line-clamp-2 mb-3">
          {note.content}
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          {note.tags.map((tag) => (
            <span
              key={tag.id}
              className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full"
            >
              {tag.name}
            </span>
          ))}
          <span className="ml-auto text-xs text-gray-400">
            {new Date(note.created_at).toLocaleDateString("ja-JP")}
          </span>
        </div>
      </article>
    </Link>
  );
}

function Pagination({
  total,
  page,
  perPage,
}: {
  total: number;
  page: number;
  perPage: number;
}) {
  const totalPages = Math.ceil(total / perPage);
  if (totalPages <= 1) return null;

  return (
    <div className="flex justify-center gap-2 pt-4">
      {page > 1 && (
        <Link href={`?page=${page - 1}`} className="px-4 py-2 border rounded-lg hover:bg-gray-50">
          前へ
        </Link>
      )}
      <span className="px-4 py-2 text-gray-600">
        {page} / {totalPages}
      </span>
      {page < totalPages && (
        <Link href={`?page=${page + 1}`} className="px-4 py-2 border rounded-lg hover:bg-gray-50">
          次へ
        </Link>
      )}
    </div>
  );
}
