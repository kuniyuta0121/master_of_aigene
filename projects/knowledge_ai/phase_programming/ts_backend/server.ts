/**
 * ====================================================================
 * TypeScript バックエンド学習用ミニアプリ - Hono REST API
 * ====================================================================
 *
 * Pythonとの比較を通じて、TypeScriptの型システムの強みを体感する。
 *
 * 起動方法:
 *   npm install
 *   npm run dev
 *
 * テスト:
 *   curl http://localhost:3000/notes
 *   curl -X POST http://localhost:3000/notes -H "Content-Type: application/json" -d '{"title":"Test","body":"Hello"}'
 */

import { Hono } from "hono";
import { serve } from "@hono/node-server";

// ====================================================================
// 1. TypeScriptの型システム - Pythonのtype hintsとの根本的な違い
// ====================================================================
//
// Pythonのtype hints:
//   def greet(name: str) -> str:
//       return name + 123  # 実行時まで型エラーに気づかない!
//
// TypeScriptの型注釈:
//   function greet(name: string): string {
//       return name + 123; // コンパイル時にエラー! TSが未然に防ぐ
//   }
//
// 核心的な違い:
//   - Python: type hintsは「ドキュメント」。実行時に無視される (mypyは別ツール)
//   - TypeScript: 型は「契約」。コンパイルが通らなければ実行すらできない
//   - TypeScriptは「型が正しいコードしか存在を許さない」世界観

// ====================================================================
// 2. interface vs type - いつどちらを使う?
// ====================================================================
//
// interface: オブジェクトの「形」を定義。拡張(extends)可能。宣言マージ可能。
// type: あらゆる型に別名を付ける。union/intersectionに使う。
//
// 実務上の使い分け:
//   - APIのリクエスト/レスポンスの形 -> interface (拡張しやすい)
//   - union型や computed type    -> type (interfaceでは書けない)
//   - 迷ったら interface を使え (公式推奨)

/** ノートの基本構造 - interfaceで定義 */
interface Note {
  id: number;
  title: string;
  body: string;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

/** 作成時はid/日付が不要 - Omitユーティリティ型で「引き算」 */
// Python equivalent: TypedDictで似たことはできるが、こんな型演算はできない
type CreateNoteInput = Omit<Note, "id" | "createdAt" | "updatedAt">;

/** 更新時はすべてのフィールドがオプション - Partialユーティリティ型 */
type UpdateNoteInput = Partial<CreateNoteInput>;

// ====================================================================
// 3. Genericsの威力 - Pythonにはない「型の変数」
// ====================================================================
//
// Pythonで書くと:
//   def first(items: list) -> Any:  # Any...型情報が消える
//       return items[0]
//
// TypeScriptなら:
//   function first<T>(items: T[]): T { return items[0]; }
//   // first([1,2,3]) は number と推論される
//   // first(["a"]) は string と推論される

/** APIレスポンスの共通ラッパー - Genericsで中身の型を保持 */
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string; // ?はundefined許容。後述のnull安全に関連
}

interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  perPage: number;
}

/** 型安全なレスポンスビルダー */
function ok<T>(data: T, message?: string): ApiResponse<T> {
  return { success: true, data, message };
}

function fail<T = null>(message: string): ApiResponse<T> {
  return { success: false, data: null as T, message };
}

// ====================================================================
// 4. Union Types / Discriminated Unions
//    - Pythonでは絶対にできない、TypeScript最強の機能の一つ
// ====================================================================
//
// 「この変数は A か B か C のどれか」を型で表現する。
// さらにdiscriminated unionなら、共通フィールドで分岐できる。

/** ログレベル - リテラル型のunion */
type LogLevel = "info" | "warn" | "error";
// Pythonだと Literal["info", "warn", "error"] が近いが、
// TypeScriptほど自然に使えない

/** Discriminated Union の例: アプリ内イベント */
type AppEvent =
  | { kind: "note_created"; note: Note }
  | { kind: "note_updated"; noteId: number; changes: UpdateNoteInput }
  | { kind: "note_deleted"; noteId: number }
  | { kind: "server_error"; error: Error };

/** exhaustive check - すべてのケースを網羅しないとコンパイルエラー */
function describeEvent(event: AppEvent): string {
  switch (event.kind) {
    case "note_created":
      return `Note "${event.note.title}" created`;
    case "note_updated":
      return `Note #${event.noteId} updated`;
    case "note_deleted":
      return `Note #${event.noteId} deleted`;
    case "server_error":
      return `Error: ${event.error.message}`;
    // もしここに新しいkindを追加して、caseを書き忘れると...
    // 下のdefaultでコンパイルエラーになる! (never型に代入できない)
    default: {
      const _exhaustive: never = event;
      return _exhaustive;
    }
  }
}
// Pythonでこれをやろうとすると... match文はあるが、
// 「全ケース網羅していなくてもエラーにならない」。
// バグの温床を型レベルで防げるのがTypeScriptの真骨頂。

// ====================================================================
// 5. null - "The Billion Dollar Mistake" とTypeScriptの解決策
// ====================================================================
//
// C.A.R. Hoare (null参照の発明者) が自ら認めた「10億ドルの過ち」:
//   - nullは「値がない」を表すが、型システムの穴になる
//   - Java: String s = null; s.length() -> NullPointerException (実行時)
//   - Python: x = None; x.upper() -> AttributeError (実行時)
//
// TypeScriptの解決策 (strictNullChecks: true):
//   - null/undefinedは明示的にunion型で宣言しないと使えない
//   - string型の変数にnullは代入できない
//   - string | null 型なら、nullチェックしないとstringのメソッドを呼べない
//
// つまり「nullかもしれない」をコンパイラが追跡してくれる!

/** ノートをIDで検索 - 見つからない可能性をundefinedで型に表現 */
function findNoteById(notes: Note[], id: number): Note | undefined {
  return notes.find((n) => n.id === id);
}
// この関数の戻り値に対して note.title とアクセスしようとすると...
// TypeScriptは「undefinedかもしれないぞ」とコンパイルエラーを出す!
// if (note) { note.title } のようにnarrowingが必要。
//
// Pythonでは Optional[Note] と書けるが、チェックしなくてもエラーにならない。
// 「忘れる」ことが許されるのがPython、「忘れられない」のがTypeScript。

// ====================================================================
// 6. アプリケーション実装
// ====================================================================

/** インメモリDB */
let notes: Note[] = [];
let nextId = 1;

/** イベントログ (Discriminated Unionの活用) */
const eventLog: AppEvent[] = [];

function emitEvent(event: AppEvent): void {
  eventLog.push(event);
  const level: LogLevel = event.kind === "server_error" ? "error" : "info";
  logMessage(level, describeEvent(event));
}

function logMessage(level: LogLevel, msg: string): void {
  const timestamp = new Date().toISOString();
  const prefix = { info: "[INFO]", warn: "[WARN]", error: "[ERROR]" }[level];
  console.log(`${timestamp} ${prefix} ${msg}`);
}

// ====================================================================
// Honoアプリケーション
// ====================================================================
const app = new Hono();

// --- ミドルウェア: リクエストログ ---
app.use("*", async (c, next) => {
  const start = Date.now();
  logMessage("info", `-> ${c.req.method} ${c.req.path}`);
  await next();
  const ms = Date.now() - start;
  logMessage("info", `<- ${c.req.method} ${c.req.path} ${c.res.status} (${ms}ms)`);
});

// --- ミドルウェア: エラーハンドリング ---
app.onError((err, c) => {
  emitEvent({ kind: "server_error", error: err });
  return c.json(fail("Internal Server Error"), 500);
});

// --- GET /notes - 一覧取得 ---
app.get("/notes", (c) => {
  // クエリパラメータでフィルタリング (型安全)
  const tag = c.req.query("tag");
  let result = notes;
  if (tag) {
    result = notes.filter((n) => n.tags.includes(tag));
  }
  return c.json(ok(result));
});

// --- GET /notes/:id - 個別取得 ---
app.get("/notes/:id", (c) => {
  const id = parseInt(c.req.param("id"), 10);
  if (isNaN(id)) {
    return c.json(fail("Invalid ID"), 400);
  }

  // findNoteByIdの戻り値は Note | undefined
  // TypeScriptがnullチェックを強制する!
  const note = findNoteById(notes, id);
  if (!note) {
    return c.json(fail("Note not found"), 404);
  }
  // ここではnoteはNote型に narrowing されている (undefinedが除外)
  return c.json(ok(note));
});

// --- POST /notes - 新規作成 ---
app.post("/notes", async (c) => {
  const input = await c.req.json<CreateNoteInput>();

  // バリデーション - TypeScriptの型はランタイムには消える!
  // だから実行時バリデーションは別途必要 (zodなどのライブラリが人気)
  if (!input.title || typeof input.title !== "string") {
    return c.json(fail("title is required"), 400);
  }

  const now = new Date();
  const note: Note = {
    id: nextId++,
    title: input.title,
    body: input.body ?? "", // ?? はnullish coalescing (null/undefinedの時だけ右辺)
    tags: input.tags ?? [],
    createdAt: now,
    updatedAt: now,
  };

  notes.push(note);
  emitEvent({ kind: "note_created", note });
  return c.json(ok(note), 201);
});

// --- PUT /notes/:id - 更新 ---
app.put("/notes/:id", async (c) => {
  const id = parseInt(c.req.param("id"), 10);
  if (isNaN(id)) return c.json(fail("Invalid ID"), 400);

  const index = notes.findIndex((n) => n.id === id);
  if (index === -1) return c.json(fail("Note not found"), 404);

  const input = await c.req.json<UpdateNoteInput>();
  // Partial<CreateNoteInput> なので、すべてのフィールドが string | undefined
  // スプレッド演算子で既存値とマージ
  const existing = notes[index]!; // ! は「undefinedでないことを保証」(noUncheckedIndexedAccess対策)
  const updated: Note = {
    ...existing,
    ...input,
    id: existing.id, // idは変更不可
    createdAt: existing.createdAt,
    updatedAt: new Date(),
  };

  notes[index] = updated;
  emitEvent({ kind: "note_updated", noteId: id, changes: input });
  return c.json(ok(updated));
});

// --- DELETE /notes/:id - 削除 ---
app.delete("/notes/:id", (c) => {
  const id = parseInt(c.req.param("id"), 10);
  if (isNaN(id)) return c.json(fail("Invalid ID"), 400);

  const index = notes.findIndex((n) => n.id === id);
  if (index === -1) return c.json(fail("Note not found"), 404);

  notes.splice(index, 1);
  emitEvent({ kind: "note_deleted", noteId: id });
  return c.json(ok(null, "Deleted"));
});

// --- GET /events - イベントログ取得 (Discriminated Unionの実用例) ---
app.get("/events", (c) => {
  return c.json(ok(eventLog.map(describeEvent)));
});

// ====================================================================
// サーバー起動
// ====================================================================
const PORT = 3000;

serve({ fetch: app.fetch, port: PORT }, () => {
  logMessage("info", `Server running at http://localhost:${PORT}`);
  logMessage("info", "Endpoints: GET/POST /notes, GET/PUT/DELETE /notes/:id, GET /events");
});

// ====================================================================
// 考えてほしい疑問
// ====================================================================
//
// Q1: CreateNoteInput を Omit<Note, ...> で定義した。
//     もしNoteにフィールドを追加したら、CreateNoteInputはどうなる?
//     -> 自動的に追加される! Pythonでは手動で2箇所を修正する必要がある。
//
// Q2: describeEvent の switch文から case "note_deleted" を削除すると
//     どうなる? 実際にやってみよう。never型の威力を体感できる。
//
// Q3: strictNullChecks を tsconfig で false にするとどうなる?
//     findNoteById の戻り値チェックを省略してもエラーにならなくなる。
//     ...つまりnullバグが混入しうる。だからstrictは必須。
//
// Q4: c.req.json<CreateNoteInput>() の<>は何をしている?
//     ジェネリクスでjson()の戻り値型をCreateNoteInputに指定している。
//     しかし実行時にはこの型情報は消える! なぜランタイムバリデーションも必要か?
//
// Q5: Pythonの def greet(name: str = None) は型的に正しい?
//     TypeScriptなら (name: string = null) はコンパイルエラー。
//     (name: string | null = null) と明示する必要がある。どちらが安全?

// ====================================================================
// [実装してみよう] 課題
// ====================================================================
//
// Task 1: タグでの検索を強化
//   GET /notes?tag=typescript は実装済み。複数タグのAND検索
//   (?tags=ts,hono) を追加してみよう。
//   ヒント: c.req.query("tags")?.split(",") で配列に。
//
// Task 2: zodによるランタイムバリデーション
//   npm install zod して、CreateNoteInputのバリデーションを
//   zodスキーマで書き直してみよう。型定義を二重管理しない方法:
//     const createNoteSchema = z.object({ title: z.string().min(1), ... });
//     type CreateNoteInput = z.infer<typeof createNoteSchema>;
//
// Task 3: Discriminated Unionの拡張
//   AppEventに { kind: "note_searched"; query: string; resultCount: number }
//   を追加してみよう。describeEventを修正しないとコンパイルエラーに
//   なることを確認しよう (exhaustive checkの威力)。
//
// Task 4: Genericsの練習
//   PaginatedResponse<T> を使って GET /notes にページネーションを
//   実装してみよう。?page=1&perPage=10 のクエリパラメータを受け取り、
//   total, page, perPage をレスポンスに含める。
//
// Task 5: Middleware パターン
//   認証ミドルウェアを追加してみよう。
//   Authorizationヘッダーに "Bearer secret123" があれば通す。
//   なければ401を返す。HonoのMiddlewareHandlerの型を調べてみよう。
