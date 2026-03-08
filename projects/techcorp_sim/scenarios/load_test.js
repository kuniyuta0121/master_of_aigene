/**
 * load_test.js - k6 負荷テストスクリプト
 * ==========================================
 * シナリオ4: トラフィックスパイク対応で使用
 *
 * 実行方法:
 *   docker compose --profile load-test up load_generator
 *
 * または直接:
 *   k6 run --env API_URL=http://localhost:8000 scenarios/load_test.js
 *
 * 学習ポイント:
 *   - VUsers (仮想ユーザー数) とスループットの関係
 *   - P95レイテンシが閾値を超えたときの対処法
 *   - rate limiting の効果をメトリクスで確認する
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend, Counter } from "k6/metrics";

// カスタムメトリクス
const errorRate = new Rate("error_rate");
const notesCreated = new Counter("notes_created");
const searchLatency = new Trend("search_latency_ms");

// ─── 負荷プロファイル設定 ────────────────────────────────
export const options = {
  // 段階的に負荷を上げる（実際の本番スパイクを模倣）
  stages: [
    { duration: "30s", target: 10 },   // ウォームアップ: 10 VU
    { duration: "1m",  target: 50 },   // 通常トラフィック: 50 VU
    { duration: "30s", target: 200 },  // スパイク開始: 200 VU
    { duration: "2m",  target: 200 },  // スパイク持続
    { duration: "30s", target: 50 },   // 回復: 50 VU に戻す
    { duration: "30s", target: 0 },    // クールダウン
  ],

  // SLO閾値 - これを超えるとテスト失敗
  thresholds: {
    // 95% of requests must complete below 2s
    "http_req_duration": ["p(95)<2000"],
    // エラーレートは1%未満
    "error_rate": ["rate<0.01"],
    // 検索レイテンシのP99は3s未満
    "search_latency_ms": ["p(99)<3000"],
  },
};

const BASE_URL = __ENV.API_URL || "http://api_gateway:8000";

// テスト用ユーザートークン（本番ではOAuthフローが必要）
const TEST_TOKENS = [
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.test1",
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMiJ9.test2",
];

// サンプル検索クエリ（実ユーザー行動を模倣）
const SEARCH_QUERIES = [
  "Python",
  "機械学習",
  "Docker",
  "FastAPI",
  "PostgreSQL",
  "Kubernetes",
  "TypeScript",
  "セキュリティ",
  "マイクロサービス",
  "CI/CD",
];

// ─── メインテスト関数 ────────────────────────────────────
export default function () {
  const token = TEST_TOKENS[Math.floor(Math.random() * TEST_TOKENS.length)];
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // ユーザー行動パターンをランダムに選択
  const action = Math.random();

  if (action < 0.4) {
    // 40%: ノート一覧取得（最も多いアクション）
    listNotes(headers);
  } else if (action < 0.7) {
    // 30%: 検索
    searchNotes(headers);
  } else if (action < 0.85) {
    // 15%: ノート作成
    createNote(headers);
  } else {
    // 15%: ヘルスチェック（監視ツールを模倣）
    healthCheck();
  }

  // ユーザーの思考時間 (0.5〜2秒)
  sleep(0.5 + Math.random() * 1.5);
}

// ─── 個別アクション関数 ──────────────────────────────────

function listNotes(headers) {
  const page = Math.floor(Math.random() * 5) + 1;
  const res = http.get(`${BASE_URL}/notes?page=${page}&per_page=20`, {
    headers,
    tags: { endpoint: "list_notes" },
  });

  const ok = check(res, {
    "list notes: status 200": (r) => r.status === 200,
    "list notes: has items": (r) => {
      try {
        return JSON.parse(r.body).items !== undefined;
      } catch {
        return false;
      }
    },
  });

  errorRate.add(!ok);
}

function searchNotes(headers) {
  const q = SEARCH_QUERIES[Math.floor(Math.random() * SEARCH_QUERIES.length)];
  const start = Date.now();

  // [BUG-02観察点] /search は認証なし → レート制限もなし → 攻撃し放題
  const res = http.get(`${BASE_URL}/search?q=${encodeURIComponent(q)}`, {
    headers,
    tags: { endpoint: "search" },
  });

  const latency = Date.now() - start;
  searchLatency.add(latency);

  const ok = check(res, {
    "search: status 200 or 429": (r) =>
      r.status === 200 || r.status === 429, // 429 = rate limited (修正後)
    "search: response time < 3s": (r) => r.timings.duration < 3000,
  });

  errorRate.add(!ok);
}

function createNote(headers) {
  const payload = JSON.stringify({
    title: `負荷テストノート ${Date.now()}`,
    content: `このノートは負荷テスト中に作成されました。\n時刻: ${new Date().toISOString()}`,
    tags: ["load-test", "k6"],
  });

  const res = http.post(`${BASE_URL}/notes`, payload, {
    headers,
    tags: { endpoint: "create_note" },
  });

  const ok = check(res, {
    "create note: status 200 or 201": (r) =>
      r.status === 200 || r.status === 201,
  });

  if (ok) {
    notesCreated.add(1);
  }
  errorRate.add(!ok);
}

function healthCheck() {
  const res = http.get(`${BASE_URL}/health`, {
    tags: { endpoint: "health" },
  });

  check(res, {
    "health: status 200": (r) => r.status === 200,
    "health: fast response": (r) => r.timings.duration < 100,
  });
}

// ─── テスト開始時のセットアップ ───────────────────────────
export function setup() {
  console.log(`🚀 負荷テスト開始: ${BASE_URL}`);
  console.log("📊 Grafana ダッシュボードで確認: http://localhost:3001");
  console.log("📈 Prometheus メトリクス: http://localhost:9090");

  // 事前ヘルスチェック
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`API Gateway が応答していません: ${res.status}`);
  }

  return { startTime: Date.now() };
}

// ─── テスト終了時のサマリー ───────────────────────────────
export function teardown(data) {
  const duration = ((Date.now() - data.startTime) / 1000).toFixed(1);
  console.log(`\n✅ 負荷テスト完了 (${duration}秒)`);
  console.log("📝 結果確認のポイント:");
  console.log("   1. P95レイテンシが2秒未満か？");
  console.log("   2. エラーレートが1%未満か？");
  console.log("   3. Grafanaダッシュボードでスパイク時のDBコネクション数を確認");
  console.log("   4. /search エンドポイントへの集中攻撃を確認（BUG-02）");
}

// ─── カスタムサマリー ────────────────────────────────────
export function handleSummary(data) {
  const p95 = data.metrics.http_req_duration?.values?.["p(95)"] || 0;
  const errRate = data.metrics.error_rate?.values?.rate || 0;
  const totalReqs = data.metrics.http_reqs?.values?.count || 0;

  const summary = {
    total_requests: totalReqs,
    p95_latency_ms: p95.toFixed(0),
    error_rate_pct: (errRate * 100).toFixed(2),
    notes_created: data.metrics.notes_created?.values?.count || 0,
    slo_passed: p95 < 2000 && errRate < 0.01,
  };

  console.log("\n" + "=".repeat(50));
  console.log("📊 負荷テスト サマリー");
  console.log("=".repeat(50));
  console.log(`総リクエスト数: ${summary.total_requests}`);
  console.log(`P95レイテンシ:  ${summary.p95_latency_ms}ms (SLO: <2000ms)`);
  console.log(`エラーレート:   ${summary.error_rate_pct}% (SLO: <1%)`);
  console.log(`作成ノート数:   ${summary.notes_created}`);
  console.log(`SLO達成:        ${summary.slo_passed ? "✅ PASS" : "❌ FAIL"}`);
  console.log("=".repeat(50));

  return {
    stdout: JSON.stringify(summary, null, 2),
    "summary.json": JSON.stringify(data, null, 2),
  };
}
