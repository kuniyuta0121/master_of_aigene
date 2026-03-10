// =============================================================================
// TypeScript Task Manager - 型システムを学ぶ教育用アプリ
// =============================================================================

// ---------------------------------------------------------------------------
// 1. Branded Types - 構造的に同じ string でも意味的に区別する
//    TaskId と UserId は両方 string だが、混同するとコンパイルエラーになる
// ---------------------------------------------------------------------------
declare const __brand: unique symbol;
type Brand<T, B extends string> = T & { readonly [__brand]: B };

type TaskId = Brand<string, "TaskId">;
type UserId = Brand<string, "UserId">;

// ブランド型を生成するヘルパー
const TaskId = (id: string): TaskId => id as TaskId;
const UserId = (id: string): UserId => id as UserId;

// コンパイル時に以下はエラーになる（デモ用コメント）:
// const tid: TaskId = UserId("u1"); // Type '"UserId"' is not assignable to type '"TaskId"'

// ---------------------------------------------------------------------------
// 2. Template Literal Types - 文字列パターンを型で表現
//    "task-001" のようなフォーマットを型レベルで強制できる
// ---------------------------------------------------------------------------
type Priority = "low" | "medium" | "high" | "critical";
type TaskTag = `tag:${string}`;       // "tag:" で始まる任意の文字列
type PriorityLabel = `priority-${Priority}`; // "priority-low" | "priority-medium" | ...

function formatPriorityLabel(p: Priority): PriorityLabel {
  return `priority-${p}`;  // 戻り値の型が自動推論される
}

// ---------------------------------------------------------------------------
// 3. Discriminated Unions - status フィールドで分岐する union 型
//    各 status ごとに異なるペイロードを持てる
// ---------------------------------------------------------------------------
interface TodoTask {
  status: "todo";               // discriminant (判別子)
  estimatedHours?: number;
}

interface InProgressTask {
  status: "in_progress";
  startedAt: Date;
  assignee: UserId;
}

interface DoneTask {
  status: "done";
  completedAt: Date;
  assignee: UserId;
  actualHours: number;
}

type TaskStatus = TodoTask | InProgressTask | DoneTask;

// タスク本体 - TaskStatus を交差型で合成
interface TaskBase {
  id: TaskId;
  title: string;
  priority: Priority;
  tags: TaskTag[];
  createdAt: Date;
  dueDate?: Date;
}

type Task = TaskBase & TaskStatus;

// ---------------------------------------------------------------------------
// 4. Type Guards - ランタイムで型を絞り込む関数
//    戻り値に `is` を使うことで、if ブロック内の型が自動的に絞られる
// ---------------------------------------------------------------------------
function isCompleted(task: Task): task is Task & DoneTask {
  return task.status === "done";
}

function isOverdue(task: Task): boolean {
  if (task.status === "done") return false;
  if (!task.dueDate) return false;
  return task.dueDate < new Date();
}

// Discriminated Union の網羅チェック (exhaustive check)
function getStatusEmoji(task: Task): string {
  switch (task.status) {
    case "todo":        return "[ ]";
    case "in_progress": return "[~]";
    case "done":        return "[x]";
    // default の never チェックで、新しい status を追加し忘れるとコンパイルエラー
    default: {
      const _exhaustive: never = task;
      return _exhaustive;
    }
  }
}

// ---------------------------------------------------------------------------
// 5. Result<T, E> - Generics で型安全なエラーハンドリング
//    例外を投げずに成功/失敗を型で表現する (Rust の Result 風)
// ---------------------------------------------------------------------------
type Result<T, E = string> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

// ---------------------------------------------------------------------------
// 6. Utility Types - TypeScript 組み込みのユーティリティ型
// ---------------------------------------------------------------------------

// Partial<T>: 全プロパティを optional に
type TaskUpdate = Partial<Pick<TaskBase, "title" | "priority" | "tags" | "dueDate">>;

// Pick<T, K>: 特定のプロパティだけ抽出
type TaskSummary = Pick<TaskBase, "id" | "title" | "priority">;

// Omit<T, K>: 特定のプロパティを除外
type TaskCreationInput = Omit<TaskBase, "id" | "createdAt">;

// Record<K, V>: キーと値の型を指定した辞書型
type PriorityCount = Record<Priority, number>;

// ---------------------------------------------------------------------------
// 7. Mapped Types & Conditional Types
//    型を変換・条件分岐する高度な型操作
// ---------------------------------------------------------------------------

// Mapped Type: 全プロパティを readonly にする（Readonly<T> の自作版）
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// Conditional Type: 配列なら要素型を取り出す
type ElementOf<T> = T extends readonly (infer U)[] ? U : never;

// 使用例: Task["tags"] から TaskTag を取り出す
type TagElement = ElementOf<Task["tags"]>;  // = TaskTag

// Mapped Type: オブジェクトの全 string 値を必須にする
type RequiredStrings<T> = {
  [K in keyof T as T[K] extends string | undefined ? K : never]-?: string;
};

// ---------------------------------------------------------------------------
// 8. Mini Validator (Zod ライクなランタイムバリデーション)
//    型推論と実行時チェックを連動させるパターン
// ---------------------------------------------------------------------------
interface Validator<T> {
  parse(input: unknown): Result<T>;
}

// string バリデーター
function string_(opts?: { minLength?: number; maxLength?: number }): Validator<string> {
  return {
    parse(input: unknown): Result<string> {
      if (typeof input !== "string") return err(`Expected string, got ${typeof input}`);
      if (opts?.minLength && input.length < opts.minLength)
        return err(`String too short (min: ${opts.minLength})`);
      if (opts?.maxLength && input.length > opts.maxLength)
        return err(`String too long (max: ${opts.maxLength})`);
      return ok(input);
    },
  };
}

// number バリデーター
function number_(opts?: { min?: number; max?: number }): Validator<number> {
  return {
    parse(input: unknown): Result<number> {
      if (typeof input !== "number" || Number.isNaN(input))
        return err(`Expected number, got ${typeof input}`);
      if (opts?.min !== undefined && input < opts.min) return err(`Number too small (min: ${opts.min})`);
      if (opts?.max !== undefined && input > opts.max) return err(`Number too large (max: ${opts.max})`);
      return ok(input);
    },
  };
}

// object バリデーター - スキーマから型を推論する
type InferSchema<S> = {
  [K in keyof S]: S[K] extends Validator<infer T> ? T : never;
};

function object_<S extends Record<string, Validator<unknown>>>(
  schema: S
): Validator<InferSchema<S>> {
  return {
    parse(input: unknown): Result<InferSchema<S>> {
      if (typeof input !== "object" || input === null)
        return err("Expected object");
      const result: Record<string, unknown> = {};
      for (const [key, validator] of Object.entries(schema)) {
        const fieldResult = validator.parse((input as Record<string, unknown>)[key]);
        if (!fieldResult.ok) return err(`${key}: ${fieldResult.error}`);
        result[key] = fieldResult.value;
      }
      return ok(result as InferSchema<S>);
    },
  };
}

// ---------------------------------------------------------------------------
// 9. Generic Repository<T> - 汎用的な in-memory リポジトリ
//    型パラメータ T と制約 (extends) でどんなエンティティでも扱える
// ---------------------------------------------------------------------------
interface Entity {
  id: string;
}

class Repository<T extends Entity> {
  private items: Map<string, T> = new Map();

  add(item: T): Result<T> {
    if (this.items.has(item.id)) {
      return err(`Item with id '${item.id}' already exists`);
    }
    this.items.set(item.id, item);
    return ok(item);
  }

  findById(id: string): T | undefined {
    return this.items.get(id);
  }

  findAll(): T[] {
    return [...this.items.values()];
  }

  update(id: string, updater: (item: T) => T): Result<T> {
    const existing = this.items.get(id);
    if (!existing) return err(`Item '${id}' not found`);
    const updated = updater(existing);
    this.items.set(id, updated);
    return ok(updated);
  }

  delete(id: string): Result<T> {
    const item = this.items.get(id);
    if (!item) return err(`Item '${id}' not found`);
    this.items.delete(id);
    return ok(item);
  }

  // メソッドチェーン用: 条件でフィルタ
  filter(predicate: (item: T) => boolean): T[] {
    return this.findAll().filter(predicate);
  }

  count(): number {
    return this.items.size;
  }
}

// ---------------------------------------------------------------------------
// 10. satisfies 演算子 - 型チェックしつつリテラル型を保持する
//     (TypeScript 4.9+)
// ---------------------------------------------------------------------------
type TaskTemplate = {
  title: string;
  priority: Priority;
  tags: TaskTag[];
};

// satisfies を使うと、型チェックされつつもリテラル型が保持される
// 通常の型注釈 (: TaskTemplate) だと priority が Priority に広がるが、
// satisfies なら "high" のまま
const bugFixTemplate = {
  title: "Bug Fix",
  priority: "high",
  tags: ["tag:bug", "tag:urgent"],
} satisfies TaskTemplate;

// bugFixTemplate.priority の型は "high" (Priority ではなく)
type BugFixPriority = typeof bugFixTemplate.priority; // = "high"

const defaultTemplates = {
  feature: { title: "New Feature", priority: "medium", tags: ["tag:feature"] },
  bugfix: bugFixTemplate,
  chore: { title: "Chore", priority: "low", tags: ["tag:chore"] },
} satisfies Record<string, TaskTemplate>;

// ---------------------------------------------------------------------------
// 11. Task Service - 上記の型機能を組み合わせたビジネスロジック
// ---------------------------------------------------------------------------
class TaskService {
  private repo = new Repository<Task>();
  private nextId = 1;

  createTask(input: TaskCreationInput): Result<Task> {
    const task: Task = {
      ...input,
      id: TaskId(`task-${String(this.nextId++).padStart(3, "0")}`),
      createdAt: new Date(),
      status: "todo",
    };
    return this.repo.add(task);
  }

  startTask(id: TaskId, assignee: UserId): Result<Task> {
    return this.repo.update(id, (task) => ({
      ...task,
      status: "in_progress" as const,
      startedAt: new Date(),
      assignee,
    }));
  }

  completeTask(id: TaskId, actualHours: number): Result<Task> {
    const task = this.repo.findById(id);
    if (!task) return err("Task not found");
    if (task.status !== "in_progress") return err("Task must be in_progress to complete");

    return this.repo.update(id, (t) => ({
      ...t,
      status: "done" as const,
      completedAt: new Date(),
      assignee: (t as Task & InProgressTask).assignee,
      actualHours,
    }));
  }

  updateTask(id: TaskId, update: TaskUpdate): Result<Task> {
    return this.repo.update(id, (task) => ({ ...task, ...update }));
  }

  getSummaries(): TaskSummary[] {
    return this.repo.findAll().map(({ id, title, priority }) => ({
      id, title, priority,
    }));
  }

  getOverdueTasks(): Task[] {
    return this.repo.filter(isOverdue);
  }

  getPriorityStats(): PriorityCount {
    const counts: PriorityCount = { low: 0, medium: 0, high: 0, critical: 0 };
    for (const task of this.repo.findAll()) {
      counts[task.priority]++;
    }
    return counts;
  }

  getAllTasks(): Task[] {
    return this.repo.findAll();
  }
}

// ---------------------------------------------------------------------------
// 12. Demo - 全機能のデモンストレーション
// ---------------------------------------------------------------------------
function printSection(title: string): void {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`  ${title}`);
  console.log(`${"=".repeat(60)}`);
}

function printTask(task: Task): void {
  const emoji = getStatusEmoji(task);
  const overdue = isOverdue(task) ? " [OVERDUE!]" : "";
  console.log(`  ${emoji} ${task.id} | ${task.title} (${task.priority})${overdue}`);

  // Discriminated Union の分岐: status によってアクセスできるプロパティが変わる
  switch (task.status) {
    case "todo":
      if (task.estimatedHours) console.log(`       Est: ${task.estimatedHours}h`);
      break;
    case "in_progress":
      console.log(`       Assignee: ${task.assignee}, Started: ${task.startedAt.toLocaleDateString()}`);
      break;
    case "done":
      console.log(`       Done by: ${task.assignee}, Hours: ${task.actualHours}h`);
      break;
  }
}

function main(): void {
  console.log("TypeScript Task Manager - 型システム教育デモ");

  const service = new TaskService();

  // --- タスク作成 ---
  printSection("1. タスク作成 (Branded Types + Discriminated Unions)");

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  service.createTask({
    title: "認証機能の実装",
    priority: "high",
    tags: ["tag:auth", "tag:backend"],
    dueDate: yesterday,  // 期限切れのタスク
  });

  service.createTask({
    title: "ダッシュボードUI",
    priority: "medium",
    tags: ["tag:frontend"],
  });

  service.createTask({
    title: "CI/CDパイプライン構築",
    priority: "critical",
    tags: ["tag:devops", "tag:infrastructure"],
  });

  service.createTask({
    title: "ユニットテスト追加",
    priority: "low",
    tags: ["tag:testing"],
  });

  for (const task of service.getAllTasks()) {
    printTask(task);
  }

  // --- タスクの状態遷移 ---
  printSection("2. 状態遷移 (Discriminated Union の分岐)");

  const alice = UserId("alice");
  const bob = UserId("bob");

  // Branded Types により、TaskId と UserId を間違えるとコンパイルエラー
  // service.startTask(alice, TaskId("task-001")); // <- これはエラーになる

  service.startTask(TaskId("task-001"), alice);
  service.startTask(TaskId("task-003"), bob);
  service.completeTask(TaskId("task-001"), 6.5);

  for (const task of service.getAllTasks()) {
    printTask(task);
  }

  // --- Utility Types ---
  printSection("3. Utility Types (Partial, Pick, Record)");

  // Partial<Pick<...>> でタイトルだけ更新
  const updateResult = service.updateTask(TaskId("task-002"), {
    title: "ダッシュボードUI v2",
    priority: "high",
  });
  if (updateResult.ok) {
    console.log(`  Updated: ${updateResult.value.title} -> ${updateResult.value.priority}`);
  }

  // Pick で必要なフィールドだけ取得
  console.log("\n  Task Summaries (Pick<Task, 'id' | 'title' | 'priority'>):");
  for (const s of service.getSummaries()) {
    console.log(`    ${s.id}: ${s.title} [${s.priority}]`);
  }

  // Record で集計
  console.log("\n  Priority Stats (Record<Priority, number>):");
  const stats = service.getPriorityStats();
  for (const [priority, count] of Object.entries(stats)) {
    console.log(`    ${priority}: ${"#".repeat(count)} (${count})`);
  }

  // --- Type Guards ---
  printSection("4. Type Guards (isCompleted, isOverdue)");

  const tasks = service.getAllTasks();
  const completed = tasks.filter(isCompleted);
  const overdue = service.getOverdueTasks();

  console.log(`  Completed tasks: ${completed.length}`);
  for (const t of completed) {
    // isCompleted のおかげで t.actualHours にアクセス可能
    console.log(`    ${t.title} - ${t.actualHours}h`);
  }

  console.log(`  Overdue tasks: ${overdue.length}`);
  for (const t of overdue) {
    console.log(`    ${t.title} (due: ${t.dueDate?.toLocaleDateString()})`);
  }

  // --- Template Literal Types ---
  printSection("5. Template Literal Types");

  const labels: PriorityLabel[] = (["low", "medium", "high", "critical"] as const).map(formatPriorityLabel);
  console.log(`  Priority labels: ${labels.join(", ")}`);

  const sampleTag: TaskTag = "tag:important";  // OK
  // const badTag: TaskTag = "important";       // コンパイルエラー: "tag:" prefix が必要
  console.log(`  Sample tag: ${sampleTag}`);

  // --- satisfies ---
  printSection("6. satisfies 演算子");

  console.log(`  bugFixTemplate.priority の型は "${bugFixTemplate.priority}" (リテラル型が保持される)`);
  console.log("  テンプレート一覧:");
  for (const [name, tmpl] of Object.entries(defaultTemplates)) {
    console.log(`    ${name}: ${tmpl.title} [${tmpl.priority}]`);
  }

  // --- Mini Validator ---
  printSection("7. Mini Validator (Zod ライクなランタイム検証)");

  const taskInputValidator = object_({
    title: string_({ minLength: 1, maxLength: 100 }),
    hours: number_({ min: 0, max: 1000 }),
  });

  // 型は自動推論される: { title: string; hours: number }
  const validInput = taskInputValidator.parse({ title: "Test Task", hours: 5 });
  const invalidInput = taskInputValidator.parse({ title: "", hours: 5 });
  const wrongType = taskInputValidator.parse({ title: 123, hours: "abc" });

  console.log(`  Valid input:   ${JSON.stringify(validInput)}`);
  console.log(`  Invalid input: ${JSON.stringify(invalidInput)}`);
  console.log(`  Wrong type:    ${JSON.stringify(wrongType)}`);

  // --- Mapped / Conditional Types ---
  printSection("8. Mapped Types & Conditional Types (コンパイル時のみ)");

  console.log("  DeepReadonly<Task> - 全プロパティが再帰的に readonly");
  console.log("  ElementOf<Task['tags']> - 配列の要素型 TaskTag を抽出");
  console.log("  RequiredStrings<TaskBase> - string プロパティだけ必須化");
  console.log("  (これらはコンパイル時に検証され、ランタイムコストなし)");

  // DeepReadonly のデモ
  const frozenTask: DeepReadonly<Task> = service.getAllTasks()[0]!;
  console.log(`\n  frozenTask.title = "${frozenTask.title}" (readonly)`);
  // frozenTask.title = "changed"; // コンパイルエラー: readonly

  // --- Generic Repository ---
  printSection("9. Generic Repository<T>");

  // Task 以外の型でも使える
  interface User extends Entity {
    id: string;
    name: string;
    role: "admin" | "member";
  }

  const userRepo = new Repository<User>();
  userRepo.add({ id: "u1", name: "Alice", role: "admin" });
  userRepo.add({ id: "u2", name: "Bob", role: "member" });

  console.log(`  Users: ${userRepo.count()}`);
  const admins = userRepo.filter((u) => u.role === "admin");
  console.log(`  Admins: ${admins.map((u) => u.name).join(", ")}`);

  // --- Result<T, E> ---
  printSection("10. Result<T, E> でエラーハンドリング");

  const dupResult = userRepo.add({ id: "u1", name: "Duplicate", role: "member" });
  if (!dupResult.ok) {
    console.log(`  Expected error: ${dupResult.error}`);
  }

  const deleteResult = userRepo.delete("u2");
  if (deleteResult.ok) {
    console.log(`  Deleted: ${deleteResult.value.name}`);
  }

  const notFound = userRepo.delete("u999");
  if (!notFound.ok) {
    console.log(`  Expected error: ${notFound.error}`);
  }

  // --- 完了 ---
  printSection("Done!");
  console.log("  TypeScript の型システムにより、以下が実現されています:");
  console.log("  - コンパイル時の型安全性 (Branded Types, Discriminated Unions)");
  console.log("  - 実行時の安全性 (Type Guards, Validator)");
  console.log("  - 柔軟な型変換 (Utility Types, Mapped Types)");
  console.log("  - ゼロコストの型抽象化 (Conditional Types, Template Literal Types)");
  console.log("");
}

main();
