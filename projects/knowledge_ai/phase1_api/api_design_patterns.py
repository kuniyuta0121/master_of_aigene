"""
phase1_api/api_design_patterns.py
==================================
API 設計パターン - Google/Tesla/IBM レベルのエンジニアが知るべき設計原則

なぜ API 設計が重要か:
  FAANG の System Design Interview では
  「月間10億リクエストを捌く API を設計せよ」
  「決済 API の冪等性をどう保証するか？」
  という問題が頻出する。
  美しく、スケーラブルで、安全な API を設計する力は
  シニアエンジニアの必須スキル。

このフェーズで学ぶこと:
  1. RESTful API 設計原則（Richardson Maturity Model）
  2. ページネーション戦略（Offset vs Cursor）
  3. レート制限アルゴリズム（Token Bucket / Sliding Window）
  4. 冪等性（Idempotency Key パターン）
  5. API バージョニング戦略
  6. CQRS パターン
  7. GraphQL vs REST vs gRPC 比較
  8. 認証パターン比較
  9. エラーハンドリング（RFC 7807）
  10. API Gateway パターン

実行方法:
  python api_design_patterns.py  (標準ライブラリのみ)

考えてほしい疑問:
  Q1. なぜ Offset ページネーションは大規模データで破綻するのか？
  Q2. Token Bucket と Sliding Window のトレードオフは？
  Q3. POST が冪等でないと決済で何が起きるか？
  Q4. gRPC が社内通信で REST より優れる理由は？
  Q5. API Gateway を入れることで何が解決されるか？
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. RESTful API 設計原則 - Richardson Maturity Model
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def restful_design_principles() -> None:
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Phase 1 API: API 設計パターン (FAANG Level)             ║")
    print("╚════════════════════════════════════════════════════════════╝")

    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Richardson Maturity Model (REST の成熟度)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Level 0: The Swamp of POX
  ─────────────────────────────────────────────────────
    POST /api  (全操作を1つのエンドポイントで)
    Body: {"action": "getUser", "id": 123}
    → SOAP / XML-RPC 時代。REST ではない。

  Level 1: Resources（リソース指向）
  ─────────────────────────────────────────────────────
    POST /users/123  (リソースを URL で表現)
    POST /users/123/orders
    → リソースは分離されたが HTTP メソッドは未活用

  Level 2: HTTP Verbs（HTTP メソッドの適切な使用）
  ─────────────────────────────────────────────────────
    GET    /users/123          → 取得（安全・冪等）
    POST   /users              → 作成
    PUT    /users/123          → 全体更新（冪等）
    PATCH  /users/123          → 部分更新
    DELETE /users/123          → 削除（冪等）
    → ほとんどの "RESTful" API はここ

  Level 3: HATEOAS（Hypermedia as the Engine of Application State）
  ─────────────────────────────────────────────────────
    レスポンスに「次に何ができるか」のリンクを含める:
    {
      "id": 123,
      "name": "田中太郎",
      "links": [
        {"rel": "self",    "href": "/users/123"},
        {"rel": "orders",  "href": "/users/123/orders"},
        {"rel": "update",  "href": "/users/123", "method": "PUT"},
        {"rel": "delete",  "href": "/users/123", "method": "DELETE"}
      ]
    }
    → クライアントが URL をハードコードしなくてよい
    → API の進化に強い（URL 変更がリンクで伝播する）

  考えてみよう:
    なぜ Level 3 (HATEOAS) は理想的だが実務で採用が少ないのか？
    → クライアント側の実装コストが高く、
      多くのチームは OpenAPI/Swagger でドキュメント化する方が実用的と判断する。
      ただし GitHub API は HATEOAS を部分的に採用している。
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. ページネーション戦略
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class Item:
    id: int
    name: str
    created_at: float


def demo_offset_pagination(items: list[Item], page: int, size: int) -> dict:
    """Offset ベースのページネーション（素朴な実装）"""
    start = page * size
    end = start + size
    page_items = items[start:end]
    return {
        "data": [{"id": i.id, "name": i.name} for i in page_items],
        "page": page,
        "size": size,
        "total": len(items),
        "total_pages": (len(items) + size - 1) // size,
    }


def demo_cursor_pagination(
    items: list[Item], cursor: int | None, size: int
) -> dict:
    """Cursor ベースのページネーション（スケーラブル）"""
    # cursor は最後に返した item の id
    if cursor is None:
        start_idx = 0
    else:
        start_idx = next(
            (i for i, item in enumerate(items) if item.id > cursor), len(items)
        )
    page_items = items[start_idx : start_idx + size]
    next_cursor = page_items[-1].id if page_items else None
    return {
        "data": [{"id": i.id, "name": i.name} for i in page_items],
        "next_cursor": next_cursor,
        "has_more": start_idx + size < len(items),
    }


def pagination_strategies() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  2. ページネーション戦略
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────┬────────────────────┬────────────────────┐
  │                 │ Offset-based       │ Cursor-based       │
  ├─────────────────┼────────────────────┼────────────────────┤
  │ リクエスト例    │ ?page=5&size=20    │ ?cursor=abc&size=20│
  │ SQL             │ OFFSET 100 LIMIT 20│ WHERE id > abc     │
  │                 │                    │ LIMIT 20           │
  │ 計算量          │ O(offset + limit)  │ O(limit)           │
  │ 100万件目       │ OFFSET 1000000 遅い│ インデックスで高速 │
  │ データ挿入時    │ ページずれ発生     │ 一貫性保持         │
  │ ランダムアクセス│ 可能（page=N）     │ 不可（順次のみ）   │
  │ 総件数          │ 返せる             │ 返しにくい         │
  │ 適用例          │ 管理画面           │ 無限スクロール     │
  │                 │ 少量データ         │ Twitter/Instagram  │
  └─────────────────┴────────────────────┴────────────────────┘
""")

    # 実際に動かしてみる
    items = [Item(id=i, name=f"item_{i}", created_at=time.time()) for i in range(1, 51)]

    print("  [Offset ページネーション - page=2, size=5]")
    result = demo_offset_pagination(items, page=2, size=5)
    print(f"    data: {result['data']}")
    print(f"    page: {result['page']}, total_pages: {result['total_pages']}")

    print()
    print("  [Cursor ページネーション - cursor=10, size=5]")
    result = demo_cursor_pagination(items, cursor=10, size=5)
    print(f"    data: {result['data']}")
    print(f"    next_cursor: {result['next_cursor']}, has_more: {result['has_more']}")

    print("""
  なぜ Cursor-based がスケールするか:
  ─────────────────────────────────────────────────────
    Offset: SELECT * FROM items ORDER BY id OFFSET 1000000 LIMIT 20
    → DB は 1,000,000 行をスキャンしてから 20 行返す

    Cursor: SELECT * FROM items WHERE id > 1000000 ORDER BY id LIMIT 20
    → B-Tree インデックスで id > 1000000 の位置に直接ジャンプ
    → データ量に関係なく O(limit) で完了

  考えてみよう:
    cursor に id ではなく created_at を使うとどんな問題が起きるか？
    → 同一時刻のレコードがある場合、ページ境界で重複/欠落が発生する
    → 解決策: (created_at, id) の複合カーソルを使う
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. レート制限アルゴリズム
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TokenBucket:
    """Token Bucket アルゴリズム - スクラッチ実装

    仕組み:
      - バケットに一定速度でトークンが追加される
      - リクエスト時にトークンを1つ消費
      - トークンがなければリクエスト拒否（429 Too Many Requests）
      - バースト（瞬間的な大量リクエスト）を許容できる
    """

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity          # バケットの最大トークン数
        self.refill_rate = refill_rate    # 1秒あたりの補充トークン数
        self.tokens = float(capacity)     # 現在のトークン数
        self.last_refill = time.time()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def allow_request(self) -> bool:
        self._refill()
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class SlidingWindowCounter:
    """Sliding Window Counter アルゴリズム - スクラッチ実装

    仕組み:
      - 固定ウィンドウの境界問題を解決
      - 前のウィンドウのカウントを重み付けで考慮
      - メモリ効率が良い（2ウィンドウ分のカウンタのみ）

    例: ウィンドウ60秒、制限100リクエスト
      前のウィンドウ: 80リクエスト
      現在のウィンドウ: 30リクエスト（開始から40秒経過）
      推定カウント = 80 * (20/60) + 30 = 56.7 → 許可
    """

    def __init__(self, window_seconds: int, max_requests: int) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.current_window_start = 0.0
        self.current_count = 0
        self.previous_count = 0

    def allow_request(self) -> bool:
        now = time.time()
        window_start = now - (now % self.window_seconds)

        if window_start != self.current_window_start:
            self.previous_count = self.current_count
            self.current_count = 0
            self.current_window_start = window_start

        elapsed_ratio = (now - window_start) / self.window_seconds
        previous_weight = 1 - elapsed_ratio
        estimated = self.previous_count * previous_weight + self.current_count

        if estimated < self.max_requests:
            self.current_count += 1
            return True
        return False


def rate_limiting() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  3. レート制限アルゴリズム
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────────┬──────────────────┬──────────────────────┐
  │ アルゴリズム     │ メリット         │ デメリット           │
  ├──────────────────┼──────────────────┼──────────────────────┤
  │ Token Bucket     │ バースト許容     │ 分散環境で同期コスト │
  │                  │ 実装シンプル     │                      │
  │ Sliding Window   │ 境界問題なし     │ 推定値（近似）       │
  │ Counter          │ メモリ効率良     │                      │
  │ Sliding Window   │ 正確             │ メモリ使用量大       │
  │ Log              │ 境界問題なし     │ （全タイムスタンプ保持)│
  │ Fixed Window     │ 最もシンプル     │ 境界で2倍通過問題    │
  │ Leaky Bucket     │ 出力レート一定   │ バースト非許容       │
  └──────────────────┴──────────────────┴──────────────────────┘

  Token Bucket の動作イメージ:
  ─────────────────────────────────────────────────────

    capacity=5, refill_rate=1/sec

    [●●●●●]  ← 満タン（5トークン）
       ↓  リクエスト3回
    [●●○○○]  ← 残り2トークン
       ↓  2秒後（2トークン補充）
    [●●●●○]  ← 4トークン
       ↓  リクエスト5回
    [●●●●○]  → 4回成功、1回拒否 (429)
""")

    # Token Bucket のデモ
    bucket = TokenBucket(capacity=5, refill_rate=2.0)
    results = []
    for i in range(8):
        allowed = bucket.allow_request()
        results.append("OK" if allowed else "DENIED")
    print(f"  [Token Bucket デモ] capacity=5, 8連続リクエスト:")
    print(f"    結果: {results}")
    print(f"    → 最初の5回は許可、残り3回は拒否（トークン枯渇）")

    print("""
  レスポンスヘッダー（業界標準）:
  ─────────────────────────────────────────────────────
    X-RateLimit-Limit: 100        ← ウィンドウ内の上限
    X-RateLimit-Remaining: 42     ← 残りリクエスト数
    X-RateLimit-Reset: 1640000000 ← リセット時刻 (Unix)
    Retry-After: 30               ← 429 応答時、何秒後に再試行

  考えてみよう:
    分散システム（サーバー10台）でレート制限を実装するには？
    → Redis を使った中央集権型カウンター
    → Lua スクリプトでアトミック操作
    → ただしネットワーク遅延分の不正確さは許容する設計が必要
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 冪等性 (Idempotency)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IdempotentPaymentService:
    """冪等性を保証する決済サービスの実装例

    冪等性: 同じリクエストを何度実行しても結果が同じになる性質
      GET    → 元々冪等（何度取得しても同じ）
      PUT    → 冪等（同じ状態に上書き）
      DELETE → 冪等（削除済みなら何もしない）
      POST   → 本来は非冪等！→ Idempotency Key で冪等にする
    """

    def __init__(self) -> None:
        self.processed_keys: dict[str, dict] = {}  # idempotency_key -> response
        self.balances: dict[str, float] = {"user_001": 10000.0}

    def charge(self, idempotency_key: str, user_id: str, amount: float) -> dict:
        """Idempotency Key パターンによる冪等な課金"""

        # 1. 既に処理済みならキャッシュされたレスポンスを返す
        if idempotency_key in self.processed_keys:
            cached = self.processed_keys[idempotency_key]
            return {**cached, "idempotent_replay": True}

        # 2. 初回: 実際の処理を実行
        if self.balances.get(user_id, 0) < amount:
            response = {"status": "error", "message": "insufficient_balance"}
        else:
            self.balances[user_id] -= amount
            response = {
                "status": "success",
                "transaction_id": str(uuid.uuid4())[:8],
                "charged": amount,
                "remaining": self.balances[user_id],
            }

        # 3. レスポンスをキャッシュ（TTL 付きで保存すべき。ここでは簡略化）
        self.processed_keys[idempotency_key] = response
        return response


def idempotency_patterns() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4. 冪等性 (Idempotency) - 決済で二重課金を防ぐ
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  なぜ POST の冪等性が重要か:
  ─────────────────────────────────────────────────────
    Client → POST /payments (1000円) → Server
    Client ← (ネットワークタイムアウト)   ← Server（処理は成功）
    Client → POST /payments (1000円) → Server（リトライ）
    → 冪等性がないと 2000円 課金されてしまう！

  Stripe / PayPal の解決策: Idempotency Key
  ─────────────────────────────────────────────────────
    POST /v1/charges
    Idempotency-Key: "key_abc123"  ← クライアントが生成する一意キー
    Body: {"amount": 1000, "currency": "jpy"}

    → サーバーは key_abc123 に対する結果をキャッシュ
    → 同じキーで再リクエストが来たらキャッシュを返す
    → 課金は1回しか実行されない
""")

    # 実際にデモ
    service = IdempotentPaymentService()
    key = "payment_key_001"

    print("  [冪等性デモ] 同じキーで3回課金リクエスト:")
    for attempt in range(1, 4):
        result = service.charge(key, "user_001", 1000.0)
        replay = result.get("idempotent_replay", False)
        print(f"    試行{attempt}: status={result['status']}, "
              f"replay={replay}, remaining={result.get('remaining', 'N/A')}")

    print("""
    → 残高は 9000 のまま。2回目以降はキャッシュ応答。
    → 二重課金は発生しない！

  実装の注意点:
    ・Idempotency Key の TTL: Stripe は24時間
    ・キーの保存先: Redis or DB（サーバー再起動に耐える）
    ・レースコンディション: DB の UNIQUE 制約 + SELECT FOR UPDATE
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. API バージョニング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def api_versioning() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  5. API バージョニング戦略
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────┬──────────────────────┬──────────────────────┐
  │ 方式         │ 例                   │ 採用企業             │
  ├──────────────┼──────────────────────┼──────────────────────┤
  │ URL Path     │ /v1/users            │ Stripe, Twitter/X    │
  │ Header       │ Accept: v=2          │ GitHub               │
  │ Query Param  │ /users?version=2     │ Google Maps          │
  │ Content-Type │ Accept:              │ GitHub (実際)        │
  │ (Media Type) │  application/        │                      │
  │              │  vnd.github.v3+json  │                      │
  └──────────────┴──────────────────────┴──────────────────────┘

  比較:
  ─────────────────────────────────────────────────────
  URL Path (/v1/users):
    [+] 明確で分かりやすい。ブラウザで直接テスト可能
    [+] キャッシュフレンドリー（URL ベースのキャッシュが効く）
    [-] URL がリソースではなくバージョンを含む（REST 原則違反）
    [-] バージョンごとにルーティング設定が必要

  Header (Accept / Custom Header):
    [+] URL がクリーン（リソースのみ）
    [+] REST 原則に忠実
    [-] ブラウザや curl でテストが面倒
    [-] API Gateway でのルーティングが複雑

  Query Param (?version=2):
    [+] 実装が簡単
    [-] キャッシュキーが複雑化
    [-] デフォルトバージョンの扱いが曖昧

  結論:
    迷ったら URL Path (/v1/) を選べ。
    理論的純粋さより、開発者体験（DX）を優先する。
    Stripe が URL Path を採用しているのは、DX 重視の結果。
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. CQRS パターン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class Command:
    """書き込み操作を表す"""
    type: str
    payload: dict = field(default_factory=dict)


@dataclass
class Event:
    """発生した事象を表す（イベントソーシング用）"""
    type: str
    payload: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class WriteModel:
    """コマンド側: 書き込みに最適化されたモデル"""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, command: Command) -> Event:
        if command.type == "CreateOrder":
            event = Event(
                type="OrderCreated",
                payload=command.payload,
            )
        elif command.type == "CancelOrder":
            event = Event(
                type="OrderCancelled",
                payload=command.payload,
            )
        else:
            raise ValueError(f"Unknown command: {command.type}")
        self.events.append(event)
        return event


class ReadModel:
    """クエリ側: 読み取りに最適化されたモデル（非正規化ビュー）"""

    def __init__(self) -> None:
        self.orders: dict[str, dict] = {}

    def apply_event(self, event: Event) -> None:
        """イベントを受けて読み取りモデルを更新"""
        if event.type == "OrderCreated":
            order_id = event.payload["order_id"]
            self.orders[order_id] = {
                **event.payload,
                "status": "active",
            }
        elif event.type == "OrderCancelled":
            order_id = event.payload["order_id"]
            if order_id in self.orders:
                self.orders[order_id]["status"] = "cancelled"

    def get_active_orders(self) -> list[dict]:
        return [o for o in self.orders.values() if o["status"] == "active"]


def cqrs_pattern() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  6. CQRS (Command Query Responsibility Segregation)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  従来の CRUD:
    [Client] → [同じモデル] → [同じDB]
    読み書きが同じテーブル構造を共有 → スケールしない

  CQRS:
    [Client] → Command → [Write Model] → [Write DB (正規化)]
                              ↓ Event
    [Client] ← Query  ← [Read Model]  ← [Read DB (非正規化)]

    書き込みと読み取りを分離する:
    ・Write DB: 正規化された RDB（整合性重視）
    ・Read DB: 非正規化されたビュー（パフォーマンス重視）
    ・Event で Write → Read を同期（結果整合性）
""")

    # CQRS デモ
    write_model = WriteModel()
    read_model = ReadModel()

    commands = [
        Command("CreateOrder", {"order_id": "ORD-001", "item": "MacBook Pro", "amount": 298000}),
        Command("CreateOrder", {"order_id": "ORD-002", "item": "iPad Air", "amount": 92800}),
        Command("CancelOrder", {"order_id": "ORD-001"}),
    ]

    print("  [CQRS デモ]")
    for cmd in commands:
        event = write_model.handle(cmd)
        read_model.apply_event(event)
        print(f"    Command: {cmd.type} → Event: {event.type}")

    active = read_model.get_active_orders()
    print(f"    アクティブ注文: {json.dumps(active, ensure_ascii=False)}")

    print("""
  いつ CQRS を使うか:
    ・読み取りが書き込みの10倍以上（ECサイト、SNS）
    ・読み取りと書き込みで異なるスケーリングが必要
    ・複雑な集計クエリが必要（ダッシュボード）
    ・イベントソーシングと組み合わせたい

  使わない方がいい場合:
    ・シンプルな CRUD アプリ（管理画面など）
    ・強い整合性が必須（結果整合性を許容できない）
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. GraphQL vs REST vs gRPC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def api_paradigm_comparison() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  7. GraphQL vs REST vs gRPC - いつ何を使うか
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌────────────┬───────────────┬───────────────┬──────────────┐
  │            │ REST          │ GraphQL       │ gRPC         │
  ├────────────┼───────────────┼───────────────┼──────────────┤
  │ プロトコル │ HTTP/1.1      │ HTTP/1.1      │ HTTP/2       │
  │ データ形式 │ JSON          │ JSON          │ Protocol Buf │
  │ スキーマ   │ OpenAPI(任意) │ SDL (必須)    │ .proto (必須)│
  │ Over-fetch │ 発生しがち    │ クライアント  │ 型で制御     │
  │            │               │ が選択        │              │
  │ N+1 問題   │ 発生する      │ DataLoader    │ 発生しない   │
  │ ストリーム │ SSE/WebSocket │ Subscription  │ 双方向       │
  │ ブラウザ   │ ネイティブ    │ ライブラリ要  │ gRPC-Web要   │
  │ 学習コスト │ 低            │ 中            │ 高           │
  │ レイテンシ │ 中            │ 中            │ 低           │
  │ 型安全性   │ 低            │ 中            │ 高           │
  └────────────┴───────────────┴───────────────┴──────────────┘

  使い分けガイド:
  ─────────────────────────────────────────────────────

    REST を選ぶ場面:
      ・公開 API（サードパーティ開発者向け）
      ・シンプルな CRUD 操作
      ・キャッシュが重要（HTTP キャッシュが自然に効く）
      例: Stripe API, Twitter API

    GraphQL を選ぶ場面:
      ・フロントエンドが多様（Web, iOS, Android で異なるデータ要求）
      ・ネストの深いデータ取得（1リクエストで完結したい）
      ・高速イテレーション（バックエンド変更なしでフロント開発）
      例: GitHub API v4, Shopify

    gRPC を選ぶ場面:
      ・マイクロサービス間通信（社内バックエンド同士）
      ・低レイテンシが必須（リアルタイムシステム）
      ・双方向ストリーミング（チャット、IoTデータ）
      例: Google 社内, Netflix 社内通信

  考えてみよう:
    Google が社内で gRPC を使い、外部 API は REST を提供する
    のはなぜか？
    → 社内: 型安全性・高速性・コード生成の恩恵を最大化
    → 外部: 開発者がブラウザと curl で簡単にテストできる DX を重視
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 認証パターン比較
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def auth_patterns() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  8. API 認証パターン比較
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────┬─────────────┬──────────────┬─────────────────┐
  │ 方式     │ セキュリティ│ 実装難易度   │ ユースケース    │
  ├──────────┼─────────────┼──────────────┼─────────────────┤
  │ API Key  │ 低          │ 非常に簡単   │ 公開API、開発時 │
  │ OAuth2   │ 高          │ 複雑         │ サードパーティ  │
  │          │             │              │ 連携            │
  │ JWT      │ 中-高       │ 中           │ マイクロサービス│
  │          │             │              │ ステートレス    │
  │ mTLS     │ 非常に高    │ 高           │ サービス間通信  │
  │          │             │              │ Zero Trust      │
  └──────────┴─────────────┴──────────────┴─────────────────┘

  各方式の詳細:
  ─────────────────────────────────────────────────────

  API Key:
    Authorization: Bearer sk_live_abc123
    ・最もシンプル。Stripe, OpenAI が採用
    ・漏洩時の影響大（ローテーション必須）
    ・ユーザー認証には不向き（誰がリクエストしたか分からない）

  OAuth 2.0:
    ・認可コードフロー: Server-side アプリ向け
    ・PKCE: SPA / モバイル向け（コードインターセプト対策）
    ・クライアントクレデンシャル: M2M 通信向け
    ・Google / GitHub ログインの裏側はこれ

  JWT (JSON Web Token):
    Header.Payload.Signature (Base64)
    ・ステートレス: DB 問い合わせ不要で検証可能
    ・失効が難しい（ブラックリストが必要）
    ・短い有効期限 + リフレッシュトークンが定石

  mTLS (Mutual TLS):
    ・クライアントとサーバーが相互に証明書を検証
    ・サービスメッシュ (Istio) で自動化
    ・Zero Trust Architecture の基盤

    Client ──[Client証明書]──→ Server
    Client ←──[Server証明書]── Server
    双方向で身元確認 → 最も安全

  考えてみよう:
    JWT の有効期限を24時間にしたら何が問題か？
    → ユーザーが退職しても24時間アクセスし続けられる
    → 解決策: アクセストークン15分 + リフレッシュトークン7日
    → リフレッシュ時にユーザー状態を再検証
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. エラーハンドリング (RFC 7807)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def error_handling_design() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  9. エラーハンドリング - RFC 7807 Problem Details
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  悪い例（よく見るが、情報不足）:
  ─────────────────────────────────────────────────────
    HTTP 400 Bad Request
    {"error": "invalid request"}
    → 何が invalid なのか分からない。デバッグ不能。

  良い例（RFC 7807 準拠）:
  ─────────────────────────────────────────────────────
    HTTP 422 Unprocessable Entity
    Content-Type: application/problem+json
""")

    error_example = {
        "type": "https://api.example.com/errors/validation",
        "title": "Validation Error",
        "status": 422,
        "detail": "リクエストに2つのバリデーションエラーがあります",
        "instance": "/users/123/orders",
        "errors": [
            {
                "field": "amount",
                "code": "INVALID_RANGE",
                "message": "amount は 1 以上 1000000 以下にしてください",
                "rejected_value": -500,
            },
            {
                "field": "currency",
                "code": "UNSUPPORTED_VALUE",
                "message": "対応通貨: JPY, USD, EUR",
                "rejected_value": "BTC",
            },
        ],
    }
    print(f"    {json.dumps(error_example, ensure_ascii=False, indent=4)}")

    print("""
  エラーコード設計の原則:
  ─────────────────────────────────────────────────────
    1. HTTP ステータスコードを正しく使う
       ・400: クライアントの構文エラー
       ・401: 認証が必要
       ・403: 認証済みだが権限なし
       ・404: リソースが存在しない
       ・409: 競合（楽観ロック失敗など）
       ・422: バリデーションエラー
       ・429: レート制限超過
       ・500: サーバー内部エラー（クライアントに詳細を見せない）
       ・503: サービス一時停止

    2. アプリケーション固有のエラーコードを付与
       ・PAYMENT_INSUFFICIENT_BALANCE
       ・USER_EMAIL_ALREADY_EXISTS
       ・ORDER_ALREADY_CANCELLED
       → クライアントがプログラムで分岐できる

    3. エラーメッセージは人間が読める形式で
       ・開発者がログで見て理解できること
       ・エンドユーザーに見せてはいけない情報を含めない
         （SQLエラー、スタックトレースなど）

  考えてみよう:
    500 エラーでスタックトレースを返すとどんなリスクがあるか？
    → 攻撃者にフレームワーク、ライブラリのバージョン、
      DB テーブル構造などの情報を与えてしまう
    → 本番環境では generic なメッセージ + リクエストIDのみ返す
    → 詳細はサーバーサイドログで確認する
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. API Gateway パターン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CircuitBreaker:
    """Circuit Breaker パターンの実装

    状態遷移:
      CLOSED → (失敗が閾値超過) → OPEN
      OPEN → (タイムアウト経過) → HALF_OPEN
      HALF_OPEN → (成功) → CLOSED
      HALF_OPEN → (失敗) → OPEN
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 5.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0

    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                return {"error": "Circuit OPEN - service unavailable", "state": self.state}

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return {"result": result, "state": self.state}
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            return {"error": str(e), "state": self.state}


def api_gateway_patterns() -> None:
    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  10. API Gateway パターン
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  API Gateway のアーキテクチャ:
  ─────────────────────────────────────────────────────

    Mobile App ─────┐
                    ├──→ [API Gateway] ──→ User Service
    Web App ────────┤      │ │ │         → Order Service
                    │      │ │ │         → Payment Service
    3rd Party ──────┘      │ │ │         → Notification Svc
                           │ │ │
                    Rate   │ │ Auth   Circuit
                    Limit  │        Breaker
                           │
                         Routing

  API Gateway の責務:
  ─────────────────────────────────────────────────────
    1. ルーティング: /users/* → User Service
    2. 認証・認可: JWT 検証、API Key 確認
    3. レート制限: ユーザーごと、IPごとの制限
    4. Circuit Breaker: 障害サービスへのリクエスト遮断
    5. リクエスト/レスポンス変換
    6. ログ・メトリクス収集
    7. SSL 終端

  BFF (Backend for Frontend) パターン:
  ─────────────────────────────────────────────────────

    Mobile App ──→ [Mobile BFF] ──┐
                                  ├──→ Microservices
    Web App ─────→ [Web BFF] ────┘

    ・各クライアントに最適化されたエンドポイント
    ・モバイル: 帯域節約のため最小限のフィールド
    ・Web: リッチなデータを1回のリクエストで取得
    ・各 BFF はクライアントチームが所有 → 自律性が高い
""")

    # Circuit Breaker デモ
    print("  [Circuit Breaker デモ]")
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)
    call_count = 0

    def unreliable_service():
        nonlocal call_count
        call_count += 1
        if call_count <= 4:
            raise ConnectionError("Service Down")
        return "OK"

    for i in range(1, 7):
        result = cb.call(unreliable_service)
        state = result.get("state", "?")
        outcome = result.get("result", result.get("error", "?"))
        print(f"    呼出{i}: state={state}, result={outcome}")

    print("""
    → 3回失敗で OPEN 状態に遷移
    → OPEN 中はサービスを呼ばずに即座にエラー返却
    → 下流サービスを過負荷から保護する

  考えてみよう:
    Circuit Breaker がないとどうなるか？
    → 障害サービスへのリクエストがタイムアウトまで待つ
    → スレッドプールが枯渇 → 全サービスに障害伝播
    → これを Cascading Failure（障害の連鎖）と呼ぶ

  主要な API Gateway 製品:
    ・AWS API Gateway: サーバーレスとの親和性
    ・Kong: オープンソース、プラグイン豊富
    ・Envoy: サービスメッシュ (Istio) の Data Plane
    ・NGINX: 高パフォーマンス、設定ベース
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    restful_design_principles()
    pagination_strategies()
    rate_limiting()
    idempotency_patterns()
    api_versioning()
    cqrs_pattern()
    api_paradigm_comparison()
    auth_patterns()
    error_handling_design()
    api_gateway_patterns()

    print("\n" + "━" * 60)
    print("完了！")
    print("""
  [実装してみよう]
  1. FastAPI で Cursor ページネーション付き API を構築
     → created_at + id の複合カーソルを実装
  2. Redis で分散 Token Bucket を実装
     → Lua スクリプトでアトミックなトークン消費を実現
  3. Stripe の Idempotency Key パターンを自分の決済 API に実装
     → PostgreSQL の UNIQUE 制約 + SELECT FOR UPDATE
  4. Circuit Breaker を非同期 (asyncio) で実装
     → HALF_OPEN 状態でのプローブリクエスト制御

  [読むべきドキュメント]
  ・Stripe API Design: https://stripe.com/docs/api
  ・Google API Design Guide: https://cloud.google.com/apis/design
  ・Microsoft REST API Guidelines
  ・RFC 7807 - Problem Details for HTTP APIs
  ・gRPC Official Documentation

  [面接で問われる設計問題]
  ・「月間10億リクエストの URL 短縮サービスを設計せよ」
  ・「Stripe のような決済 API を設計せよ」
  ・「リアルタイムチャットの API を設計せよ」
  ・「Rate Limiter を設計せよ」
""")

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - REST基礎(HTTPメソッド/ステータスコード)
    - ページネーション
    - エラーハンドリング

  【Tier 2: 重要 — 実務で頻出】
    - レート制限
    - 冪等性(Idempotency Key)
    - API バージョニング
    - OpenAPI/Swagger

  【Tier 3: 上級 — シニア以上で差がつく】
    - CQRS
    - API Gateway パターン
    - Circuit Breaker
    - GraphQL基礎

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - gRPC
    - AsyncAPI
    - HATEOAS
    - Richardson Maturity Model Level 3
""")


if __name__ == "__main__":
    main()
