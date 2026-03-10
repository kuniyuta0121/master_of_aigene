"""
phase_architecture/system_design_patterns.py
=============================================
システム設計パターン完全ガイド - FAANG Tech Lead / PM 面接対策

なぜシステム設計パターンが必要か:
  FAANG のシニアエンジニア / Tech Lead 面接では
  「数億ユーザーのチャットシステムを設計せよ」
  「マイクロサービス間のデータ整合性をどう保証するか」
  といった設計力が問われる。パターンを知り、
  トレードオフを語れなければ通らない。

このフェーズで学ぶこと:
  1. マイクロサービスパターン (API Gateway, Saga, Circuit Breaker)
  2. イベント駆動アーキテクチャ (Event Sourcing, CQRS, Outbox)
  3. DDD (Aggregate, Entity, Value Object, Bounded Context)
  4. 分散システムパターン (Consistent Hashing, Vector Clock, Gossip)
  5. 汎用システム設計問題 (URL Shortener, Rate Limiter, Chat, Feed)
  6. スケーラビリティパターン (Sharding, Cache, Back-pressure)

実行方法:
  python system_design_patterns.py  (標準ライブラリのみ)

考えてほしい疑問:
  Q1. Saga パターンで Choreography と Orchestration のどちらを選ぶべきか？
  Q2. Circuit Breaker の閾値はどう決める？（SLA, p99 レイテンシ）
  Q3. Event Sourcing でイベントストアが巨大になったらどうする？（スナップショット）
  Q4. CQRS で Read Model が Write Model と一時的に不整合になる問題は許容できるか？
  Q5. Consistent Hashing で仮想ノードの数はどう決める？
  Q6. CAP 定理で「CA」を選べない理由は？（ネットワーク分断は避けられない）
  Q7. Rate Limiter で Token Bucket と Sliding Window Log の使い分けは？
  Q8. Fan-out on Write と Fan-out on Read はどんなユーザー構成で切り替える？
"""

from __future__ import annotations

import hashlib
import heapq
import json
import random
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. マイクロサービスパターン (Microservices Patterns)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 1.1 Service Decomposition (Bounded Context from DDD) ──

@dataclass
class BoundedContext:
    """
    DDD の Bounded Context によるサービス分割

    考えてほしい疑問:
      ・1つのサービスが大きくなりすぎたらどう分割する？
      ・チーム境界とサービス境界を一致させるべき理由は？（Conway の法則）

    [実装してみよう] 自分のプロジェクトを Bounded Context で分割してみる
    """
    name: str
    entities: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    events_published: list[str] = field(default_factory=list)
    events_consumed: list[str] = field(default_factory=list)
    upstream_contexts: list[str] = field(default_factory=list)
    downstream_contexts: list[str] = field(default_factory=list)

    def describe(self) -> str:
        lines = [f"[BoundedContext: {self.name}]"]
        lines.append(f"  Entities: {', '.join(self.entities)}")
        lines.append(f"  Commands: {', '.join(self.commands)}")
        lines.append(f"  Publishes: {', '.join(self.events_published)}")
        lines.append(f"  Consumes: {', '.join(self.events_consumed)}")
        if self.upstream_contexts:
            lines.append(f"  Upstream: {', '.join(self.upstream_contexts)}")
        if self.downstream_contexts:
            lines.append(f"  Downstream: {', '.join(self.downstream_contexts)}")
        return "\n".join(lines)


def demo_service_decomposition() -> None:
    """EC サイトを Bounded Context で分割する例"""
    order_ctx = BoundedContext(
        name="Order",
        entities=["Order", "OrderLine", "OrderStatus"],
        commands=["PlaceOrder", "CancelOrder", "UpdateOrder"],
        events_published=["OrderPlaced", "OrderCancelled"],
        events_consumed=["PaymentCompleted", "InventoryReserved"],
        downstream_contexts=["Payment", "Inventory", "Shipping"],
    )
    payment_ctx = BoundedContext(
        name="Payment",
        entities=["Payment", "PaymentMethod", "Refund"],
        commands=["ProcessPayment", "IssueRefund"],
        events_published=["PaymentCompleted", "PaymentFailed", "RefundIssued"],
        events_consumed=["OrderPlaced"],
        upstream_contexts=["Order"],
    )
    inventory_ctx = BoundedContext(
        name="Inventory",
        entities=["Product", "Stock", "Warehouse"],
        commands=["ReserveStock", "ReleaseStock"],
        events_published=["InventoryReserved", "InventoryInsufficient"],
        events_consumed=["OrderPlaced", "OrderCancelled"],
        upstream_contexts=["Order"],
    )

    print("  ── EC サイトの Bounded Context 分割 ──")
    for ctx in [order_ctx, payment_ctx, inventory_ctx]:
        print(f"  {ctx.describe()}")
        print()


# ── 1.2 API Gateway Pattern ──

class RateLimitRule:
    """Rate limit: Token Bucket per client"""
    def __init__(self, max_tokens: int, refill_per_sec: float):
        self.max_tokens = max_tokens
        self.refill_per_sec = refill_per_sec
        self.buckets: dict[str, float] = {}
        self.last_refill: dict[str, float] = {}

    def allow(self, client_id: str) -> bool:
        now = time.monotonic()
        if client_id not in self.buckets:
            self.buckets[client_id] = self.max_tokens
            self.last_refill[client_id] = now

        elapsed = now - self.last_refill[client_id]
        self.buckets[client_id] = min(
            self.max_tokens,
            self.buckets[client_id] + elapsed * self.refill_per_sec,
        )
        self.last_refill[client_id] = now

        if self.buckets[client_id] >= 1.0:
            self.buckets[client_id] -= 1.0
            return True
        return False


@dataclass
class RouteConfig:
    path_prefix: str
    target_service: str
    requires_auth: bool = True
    rate_limit: Optional[RateLimitRule] = None


class APIGateway:
    """
    API Gateway パターン

    責務: ルーティング、認証、レート制限、レスポンス集約

    考えてほしい疑問:
      ・API Gateway が単一障害点にならないようにするには？
      ・BFF (Backend for Frontend) パターンとの違いは？

    [実装してみよう] Circuit Breaker を Gateway に組み込む
    """
    def __init__(self) -> None:
        self.routes: list[RouteConfig] = []
        self.auth_tokens: set[str] = set()

    def register_route(self, route: RouteConfig) -> None:
        self.routes.append(route)

    def add_auth_token(self, token: str) -> None:
        self.auth_tokens.add(token)

    def handle_request(self, path: str, auth_token: Optional[str] = None,
                       client_id: str = "anonymous") -> dict[str, Any]:
        # Find matching route
        route = None
        for r in self.routes:
            if path.startswith(r.path_prefix):
                route = r
                break
        if route is None:
            return {"status": 404, "body": "Not Found"}

        # Auth check
        if route.requires_auth:
            if auth_token is None or auth_token not in self.auth_tokens:
                return {"status": 401, "body": "Unauthorized"}

        # Rate limiting
        if route.rate_limit and not route.rate_limit.allow(client_id):
            return {"status": 429, "body": "Too Many Requests"}

        return {
            "status": 200,
            "body": f"Routed to {route.target_service}",
            "service": route.target_service,
        }


def demo_api_gateway() -> None:
    gw = APIGateway()
    gw.add_auth_token("valid-token-123")

    rate_limit = RateLimitRule(max_tokens=3, refill_per_sec=1.0)
    gw.register_route(RouteConfig("/api/orders", "order-service", True, rate_limit))
    gw.register_route(RouteConfig("/api/products", "product-service", False))
    gw.register_route(RouteConfig("/api/users", "user-service", True))

    print("  ── API Gateway Pattern ──")
    # No auth on public route
    print(f"  GET /api/products (no auth): {gw.handle_request('/api/products')}")
    # Auth required
    print(f"  GET /api/users (no token):   {gw.handle_request('/api/users')}")
    print(f"  GET /api/users (valid):      {gw.handle_request('/api/users', 'valid-token-123')}")
    # Rate limiting
    for i in range(5):
        res = gw.handle_request("/api/orders", "valid-token-123", "client-A")
        print(f"  GET /api/orders #{i+1}: status={res['status']}")
    print()


# ── 1.3 Service Discovery ──

class ServiceRegistry:
    """
    サービスディスカバリ (Client-side discovery パターン)

    Client-side: クライアントがレジストリに問い合わせ → 直接呼び出し
    Server-side: ロードバランサーがレジストリに問い合わせ → 転送

    考えてほしい疑問:
      ・Kubernetes の kube-dns は Server-side discovery。なぜ？
      ・ヘルスチェックが失敗したインスタンスをどう除外する？
    """
    def __init__(self) -> None:
        self.services: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def register(self, name: str, host: str, port: int, metadata: dict | None = None) -> None:
        instance = {"host": host, "port": port, "healthy": True,
                     "metadata": metadata or {}, "id": f"{host}:{port}"}
        self.services[name].append(instance)

    def deregister(self, name: str, host: str, port: int) -> None:
        inst_id = f"{host}:{port}"
        self.services[name] = [i for i in self.services[name] if i["id"] != inst_id]

    def discover(self, name: str) -> list[dict[str, Any]]:
        return [i for i in self.services[name] if i["healthy"]]

    def mark_unhealthy(self, name: str, host: str, port: int) -> None:
        for inst in self.services[name]:
            if inst["id"] == f"{host}:{port}":
                inst["healthy"] = False

    def get_one(self, name: str) -> Optional[dict[str, Any]]:
        """Round-robin style: pick random healthy instance"""
        healthy = self.discover(name)
        return random.choice(healthy) if healthy else None


def demo_service_discovery() -> None:
    registry = ServiceRegistry()
    registry.register("order-service", "10.0.0.1", 8080)
    registry.register("order-service", "10.0.0.2", 8080)
    registry.register("order-service", "10.0.0.3", 8080)

    print("  ── Service Discovery ──")
    print(f"  Healthy instances: {len(registry.discover('order-service'))}")
    registry.mark_unhealthy("order-service", "10.0.0.2", 8080)
    print(f"  After marking 10.0.0.2 unhealthy: {len(registry.discover('order-service'))}")
    picked = registry.get_one("order-service")
    print(f"  Selected instance: {picked['id'] if picked else 'None'}")
    print()


# ── 1.4 Saga Pattern (Choreography vs Orchestration) ──

class SagaStepStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()
    COMPENSATED = auto()


@dataclass
class SagaStep:
    name: str
    action: Callable[[], bool]
    compensate: Callable[[], None]
    status: SagaStepStatus = SagaStepStatus.PENDING


class SagaOrchestrator:
    """
    Saga パターン - Orchestration (中央調整者)

    分散トランザクションを、一連のローカルトランザクション + 補償で実現。
    Orchestrator が各ステップを順に呼び出し、失敗時は逆順に補償する。

    考えてほしい疑問:
      ・Choreography (イベント連鎖) とどちらが保守しやすいか？
      ・補償アクションが失敗したらどうする？（リトライ + Dead Letter Queue）

    [実装してみよう] Choreography 版を EventBus を使って実装する
    """
    def __init__(self, saga_id: str, steps: list[SagaStep]) -> None:
        self.saga_id = saga_id
        self.steps = steps
        self.log: list[str] = []

    def execute(self) -> bool:
        self.log.append(f"Saga {self.saga_id} started")
        for i, step in enumerate(self.steps):
            self.log.append(f"  Executing: {step.name}")
            success = step.action()
            if success:
                step.status = SagaStepStatus.COMPLETED
                self.log.append(f"  ✓ {step.name} completed")
            else:
                step.status = SagaStepStatus.FAILED
                self.log.append(f"  ✗ {step.name} FAILED → compensating")
                self._compensate(i)
                return False
        self.log.append(f"Saga {self.saga_id} completed successfully")
        return True

    def _compensate(self, failed_index: int) -> None:
        for j in range(failed_index - 1, -1, -1):
            step = self.steps[j]
            if step.status == SagaStepStatus.COMPLETED:
                self.log.append(f"  Compensating: {step.name}")
                step.compensate()
                step.status = SagaStepStatus.COMPENSATED
                self.log.append(f"  ↩ {step.name} compensated")


class SagaChoreography:
    """
    Saga パターン - Choreography (イベント連鎖)

    各サービスがイベントを発行し、次のサービスがそれを購読する。
    中央調整者がない分、シンプルだがフロー全体の可視性が低い。
    """
    def __init__(self) -> None:
        self.event_bus: dict[str, list[Callable]] = defaultdict(list)
        self.log: list[str] = []

    def subscribe(self, event: str, handler: Callable) -> None:
        self.event_bus[event].append(handler)

    def publish(self, event: str, data: dict) -> None:
        self.log.append(f"  Event published: {event}")
        for handler in self.event_bus.get(event, []):
            handler(data)


def demo_saga() -> None:
    print("  ── Saga Pattern: Orchestration ──")
    # Simulate: order → payment → inventory (payment fails)
    steps = [
        SagaStep(
            name="CreateOrder",
            action=lambda: True,
            compensate=lambda: None,
        ),
        SagaStep(
            name="ProcessPayment",
            action=lambda: False,  # Simulate failure
            compensate=lambda: None,
        ),
        SagaStep(
            name="ReserveInventory",
            action=lambda: True,
            compensate=lambda: None,
        ),
    ]
    saga = SagaOrchestrator("order-saga-001", steps)
    result = saga.execute()
    for line in saga.log:
        print(f"    {line}")
    print(f"  Result: {'Success' if result else 'Rolled back'}")

    print("\n  ── Saga Pattern: Choreography ──")
    choreo = SagaChoreography()

    def on_order_created(data: dict) -> None:
        choreo.log.append(f"  PaymentService received OrderCreated for {data['order_id']}")
        choreo.publish("PaymentCompleted", {"order_id": data["order_id"]})

    def on_payment_completed(data: dict) -> None:
        choreo.log.append(f"  InventoryService received PaymentCompleted for {data['order_id']}")
        choreo.publish("InventoryReserved", {"order_id": data["order_id"]})

    def on_inventory_reserved(data: dict) -> None:
        choreo.log.append(f"  ShippingService received InventoryReserved for {data['order_id']}")

    choreo.subscribe("OrderCreated", on_order_created)
    choreo.subscribe("PaymentCompleted", on_payment_completed)
    choreo.subscribe("InventoryReserved", on_inventory_reserved)
    choreo.publish("OrderCreated", {"order_id": "ORD-42"})
    for line in choreo.log:
        print(f"    {line}")
    print()


# ── 1.5 Circuit Breaker (State Machine) ──

class CircuitState(Enum):
    CLOSED = "CLOSED"         # 正常: リクエストを通す
    OPEN = "OPEN"             # 遮断: リクエストを即座に拒否
    HALF_OPEN = "HALF_OPEN"   # 試行: 限定的にリクエストを通す


class CircuitBreaker:
    """
    Circuit Breaker パターン

    状態遷移:
      CLOSED → (failure_threshold 超過) → OPEN
      OPEN → (timeout 経過) → HALF_OPEN
      HALF_OPEN → (成功) → CLOSED
      HALF_OPEN → (失敗) → OPEN

    考えてほしい疑問:
      ・failure_threshold を低くしすぎると何が起こるか？（false positive）
      ・Netflix Hystrix から Resilience4j へ移行した理由は？

    [実装してみよう] メトリクス収集（成功率、レイテンシ）を追加する
    """
    def __init__(self, name: str, failure_threshold: int = 3,
                 recovery_timeout: float = 5.0, half_open_max: int = 1) -> None:
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max = half_open_max
        self.half_open_calls = 0
        self.last_failure_time: Optional[float] = None
        self.log: list[str] = []

    def call(self, func: Callable[[], Any]) -> Any:
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               (time.monotonic() - self.last_failure_time) > self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
            else:
                self.log.append(f"  [{self.name}] OPEN → request rejected")
                raise Exception("Circuit is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max:
                self.log.append(f"  [{self.name}] HALF_OPEN max calls reached → rejecting")
                raise Exception("Circuit is HALF_OPEN, max calls reached")
            self.half_open_calls += 1

        try:
            result = func()
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.CLOSED)
        self.failure_count = 0
        self.success_count += 1

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.state == CircuitState.HALF_OPEN:
            self._transition(CircuitState.OPEN)
        elif self.failure_count >= self.failure_threshold:
            self._transition(CircuitState.OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        old = self.state
        self.state = new_state
        self.log.append(f"  [{self.name}] {old.value} → {new_state.value}")
        if new_state == CircuitState.CLOSED:
            self.failure_count = 0
            self.half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self.half_open_calls = 0


def demo_circuit_breaker() -> None:
    print("  ── Circuit Breaker State Machine ──")
    cb = CircuitBreaker("payment-service", failure_threshold=3, recovery_timeout=0.1)
    call_count = 0

    def unreliable_service() -> str:
        nonlocal call_count
        call_count += 1
        if call_count <= 4:
            raise Exception("Service unavailable")
        return "OK"

    for i in range(6):
        try:
            result = cb.call(unreliable_service)
            print(f"    Call {i+1}: {result} (state={cb.state.value})")
        except Exception as e:
            print(f"    Call {i+1}: FAILED - {e} (state={cb.state.value})")
        if cb.state == CircuitState.OPEN:
            time.sleep(0.15)  # Wait for recovery timeout

    for line in cb.log:
        print(f"    {line}")
    print()


# ── 1.6 Sidecar / Ambassador / Adapter Patterns ──

class Sidecar:
    """
    Sidecar パターン: メインプロセスの隣にデプロイされる補助プロセス
    例: Envoy Proxy, Fluentd ログ収集, Vault Agent

    Ambassador: Sidecar の特殊系。外部サービスへのプロキシ
    Adapter: Sidecar の特殊系。出力フォーマットの変換
    """
    def __init__(self, name: str, main_service: str) -> None:
        self.name = name
        self.main_service = main_service
        self.intercepted: list[str] = []

    def intercept_outbound(self, request: str) -> str:
        """Ambassador: 外部呼び出しにリトライ/TLS/サービスメッシュ機能を付加"""
        self.intercepted.append(f"outbound: {request}")
        return f"[{self.name}] proxied → {request}"

    def intercept_inbound(self, request: str) -> str:
        """Sidecar: インバウンドにメトリクス/ログ/認証を付加"""
        self.intercepted.append(f"inbound: {request}")
        return f"[{self.name}] logged+authed → {request}"

    def adapt_output(self, raw_output: dict) -> str:
        """Adapter: 出力を標準フォーマットに変換"""
        self.intercepted.append(f"adapt: {raw_output}")
        return json.dumps({"timestamp": "2026-03-09T00:00:00Z",
                           "service": self.main_service,
                           "data": raw_output})


def demo_sidecar() -> None:
    print("  ── Sidecar / Ambassador / Adapter ──")
    sidecar = Sidecar("envoy-proxy", "order-service")
    print(f"  Ambassador: {sidecar.intercept_outbound('GET /api/payment')}")
    print(f"  Sidecar:    {sidecar.intercept_inbound('POST /api/orders')}")
    print(f"  Adapter:    {sidecar.adapt_output({'cpu': 45, 'mem': 78})}")
    print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. イベント駆動アーキテクチャ (Event-Driven Architecture)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 2.1 Event Sourcing ──

@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    aggregate_id: str
    event_type: str
    data: dict
    timestamp: float
    version: int


class EventStore:
    """
    Event Sourcing: 状態を直接保存せず、イベントの列で表現

    考えてほしい疑問:
      ・イベント数が膨大になったら？→ スナップショット
      ・過去のイベントは変更してよいか？→ 不変。新イベントで補正
      ・スキーマ変更（イベントの構造変更）にどう対応する？→ Upcasting
    """
    def __init__(self) -> None:
        self.events: dict[str, list[DomainEvent]] = defaultdict(list)

    def append(self, event: DomainEvent) -> None:
        stream = self.events[event.aggregate_id]
        if stream and stream[-1].version >= event.version:
            raise ValueError(f"Optimistic concurrency violation: "
                             f"expected version > {stream[-1].version}")
        stream.append(event)

    def get_events(self, aggregate_id: str, after_version: int = 0) -> list[DomainEvent]:
        return [e for e in self.events[aggregate_id] if e.version > after_version]

    def get_all_events(self) -> list[DomainEvent]:
        all_events = []
        for stream in self.events.values():
            all_events.extend(stream)
        all_events.sort(key=lambda e: e.timestamp)
        return all_events


class BankAccount:
    """Event-sourced 銀行口座 Aggregate"""
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self.balance = 0
        self.version = 0
        self.pending_events: list[DomainEvent] = []

    def deposit(self, amount: int) -> None:
        self._apply(DomainEvent(
            event_id=str(uuid.uuid4())[:8],
            aggregate_id=self.account_id,
            event_type="MoneyDeposited",
            data={"amount": amount},
            timestamp=time.time(),
            version=self.version + 1,
        ))

    def withdraw(self, amount: int) -> None:
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self._apply(DomainEvent(
            event_id=str(uuid.uuid4())[:8],
            aggregate_id=self.account_id,
            event_type="MoneyWithdrawn",
            data={"amount": amount},
            timestamp=time.time(),
            version=self.version + 1,
        ))

    def _apply(self, event: DomainEvent) -> None:
        self._handle(event)
        self.pending_events.append(event)

    def _handle(self, event: DomainEvent) -> None:
        if event.event_type == "MoneyDeposited":
            self.balance += event.data["amount"]
        elif event.event_type == "MoneyWithdrawn":
            self.balance -= event.data["amount"]
        self.version = event.version

    @classmethod
    def from_events(cls, account_id: str, events: list[DomainEvent]) -> "BankAccount":
        account = cls(account_id)
        for event in events:
            account._handle(event)
        return account


def demo_event_sourcing() -> None:
    print("  ── Event Sourcing ──")
    store = EventStore()
    account = BankAccount("ACC-001")
    account.deposit(1000)
    account.deposit(500)
    account.withdraw(200)

    for event in account.pending_events:
        store.append(event)

    print(f"  Current balance: {account.balance}")
    print(f"  Events in store: {len(store.get_events('ACC-001'))}")

    # Rebuild from events
    rebuilt = BankAccount.from_events("ACC-001", store.get_events("ACC-001"))
    print(f"  Rebuilt balance: {rebuilt.balance}")
    print(f"  Balances match: {account.balance == rebuilt.balance}")

    for e in store.get_events("ACC-001"):
        print(f"    v{e.version}: {e.event_type} {e.data}")
    print()


# ── 2.2 CQRS (Command Query Responsibility Segregation) ──

class WriteModel:
    """Command side: ビジネスロジック + イベント発行"""
    def __init__(self, event_store: EventStore) -> None:
        self.event_store = event_store

    def handle_command(self, command: str, data: dict) -> DomainEvent:
        if command == "CreateProduct":
            event = DomainEvent(
                event_id=str(uuid.uuid4())[:8],
                aggregate_id=data["product_id"],
                event_type="ProductCreated",
                data=data,
                timestamp=time.time(),
                version=1,
            )
        elif command == "UpdatePrice":
            events = self.event_store.get_events(data["product_id"])
            version = events[-1].version if events else 0
            event = DomainEvent(
                event_id=str(uuid.uuid4())[:8],
                aggregate_id=data["product_id"],
                event_type="PriceUpdated",
                data=data,
                timestamp=time.time(),
                version=version + 1,
            )
        else:
            raise ValueError(f"Unknown command: {command}")
        self.event_store.append(event)
        return event


class ReadModel:
    """
    Query side: 読み取り専用の非正規化ビュー

    考えてほしい疑問:
      ・Write Model と Read Model が一時的に不整合になる
        (Eventual Consistency) を許容できるユースケースは？
      ・Read Model を複数用途で持つ利点は？（検索用、レポート用、etc.）
    """
    def __init__(self) -> None:
        self.products: dict[str, dict] = {}

    def handle_event(self, event: DomainEvent) -> None:
        """イベントを受けて Read Model を更新（プロジェクション）"""
        if event.event_type == "ProductCreated":
            self.products[event.aggregate_id] = {
                "id": event.aggregate_id,
                "name": event.data.get("name", ""),
                "price": event.data.get("price", 0),
                "category": event.data.get("category", ""),
            }
        elif event.event_type == "PriceUpdated":
            if event.aggregate_id in self.products:
                self.products[event.aggregate_id]["price"] = event.data["price"]

    def query_by_category(self, category: str) -> list[dict]:
        return [p for p in self.products.values() if p["category"] == category]

    def query_by_id(self, product_id: str) -> Optional[dict]:
        return self.products.get(product_id)


def demo_cqrs() -> None:
    print("  ── CQRS (Command Query Responsibility Segregation) ──")
    store = EventStore()
    write = WriteModel(store)
    read = ReadModel()

    # Commands
    events = []
    events.append(write.handle_command("CreateProduct",
        {"product_id": "P1", "name": "Laptop", "price": 999, "category": "Electronics"}))
    events.append(write.handle_command("CreateProduct",
        {"product_id": "P2", "name": "Keyboard", "price": 79, "category": "Electronics"}))
    events.append(write.handle_command("CreateProduct",
        {"product_id": "P3", "name": "Desk", "price": 250, "category": "Furniture"}))
    events.append(write.handle_command("UpdatePrice",
        {"product_id": "P1", "price": 899}))

    # Project events to read model
    for event in events:
        read.handle_event(event)

    # Queries (against denormalized read model)
    electronics = read.query_by_category("Electronics")
    print(f"  Electronics: {json.dumps(electronics, indent=4)}")
    print(f"  P1 after price update: {read.query_by_id('P1')}")
    print()


# ── 2.3 Event Bus / Message Broker Simulation ──

class EventBus:
    """
    メッセージブローカーシミュレーション

    トピックベースの Pub/Sub。Kafka / RabbitMQ / SNS+SQS の概念モデル。

    [実装してみよう] Consumer Group（同一グループ内は1つだけ受信）を追加する
    """
    def __init__(self) -> None:
        self.topics: dict[str, list[Callable]] = defaultdict(list)
        self.dead_letter: list[tuple[str, dict, str]] = []
        self.processed_ids: set[str] = set()

    def subscribe(self, topic: str, handler: Callable) -> None:
        self.topics[topic].append(handler)

    def publish(self, topic: str, message: dict) -> None:
        for handler in self.topics.get(topic, []):
            try:
                handler(message)
            except Exception as e:
                self.dead_letter.append((topic, message, str(e)))

    def publish_idempotent(self, topic: str, message: dict) -> None:
        """Idempotent consumer: message_id で重複排除"""
        msg_id = message.get("message_id", "")
        if msg_id in self.processed_ids:
            return  # Skip duplicate
        self.processed_ids.add(msg_id)
        self.publish(topic, message)


# ── 2.4 Outbox Pattern ──

class TransactionalOutbox:
    """
    Outbox パターン: DB トランザクションとイベント発行の一貫性を保証

    手順:
      1. ビジネスデータと Outbox テーブルを同一トランザクションで書き込み
      2. 別プロセス (CDC / Polling) が Outbox テーブルからイベントを発行
      3. 発行後 Outbox レコードをマーク

    考えてほしい疑問:
      ・なぜ「DB書き込み後にイベントを発行する」だけではダメなのか？
        → DB成功 + イベント発行失敗 = 不整合
      ・CDC (Change Data Capture) vs Polling の使い分けは？
    """
    def __init__(self) -> None:
        self.db_records: list[dict] = []
        self.outbox: list[dict] = []
        self.published: list[dict] = []

    def save_with_outbox(self, entity: dict, event: dict) -> None:
        """疑似トランザクション: エンティティと Outbox を同時書き込み"""
        self.db_records.append(entity)
        outbox_entry = {
            "id": str(uuid.uuid4())[:8],
            "event": event,
            "published": False,
            "created_at": time.time(),
        }
        self.outbox.append(outbox_entry)

    def poll_and_publish(self, event_bus: EventBus) -> int:
        """Polling publisher: 未発行のイベントを発行"""
        count = 0
        for entry in self.outbox:
            if not entry["published"]:
                event_bus.publish(entry["event"]["topic"], entry["event"]["data"])
                entry["published"] = True
                self.published.append(entry)
                count += 1
        return count


# ── 2.5 Dead Letter Queue ──

class DeadLetterQueue:
    """
    Dead Letter Queue: 処理失敗メッセージの退避先

    考えてほしい疑問:
      ・DLQ のメッセージをいつ再処理する？（手動/自動）
      ・リトライ回数の上限はどう決める？
    """
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.dlq: list[dict] = []
        self.retry_counts: dict[str, int] = defaultdict(int)

    def process_with_retry(self, message_id: str, processor: Callable,
                           message: dict) -> bool:
        while self.retry_counts[message_id] < self.max_retries:
            try:
                processor(message)
                return True
            except Exception:
                self.retry_counts[message_id] += 1
        # Max retries exceeded → move to DLQ
        self.dlq.append({"message_id": message_id, "message": message,
                         "retries": self.retry_counts[message_id]})
        return False


def demo_event_driven() -> None:
    print("  ── Event Bus + Outbox + DLQ ──")
    bus = EventBus()
    received: list[str] = []

    def order_handler(msg: dict) -> None:
        received.append(f"Order processed: {msg['order_id']}")

    def failing_handler(msg: dict) -> None:
        raise RuntimeError("Processing failed!")

    bus.subscribe("orders", order_handler)
    bus.subscribe("payments", failing_handler)

    # Outbox pattern
    outbox = TransactionalOutbox()
    outbox.save_with_outbox(
        entity={"order_id": "ORD-99", "total": 150},
        event={"topic": "orders", "data": {"order_id": "ORD-99"}},
    )
    count = outbox.poll_and_publish(bus)
    print(f"  Outbox published: {count} events")
    print(f"  Received: {received}")

    # DLQ
    dlq = DeadLetterQueue(max_retries=3)
    result = dlq.process_with_retry("msg-1", failing_handler, {"data": "test"})
    print(f"  DLQ processing result: {result}")
    print(f"  Messages in DLQ: {len(dlq.dlq)}")

    # Idempotent consumer
    bus.subscribe("idempotent-topic", lambda m: received.append(f"idempotent: {m}"))
    bus.publish_idempotent("idempotent-topic", {"message_id": "ID-1", "data": "first"})
    bus.publish_idempotent("idempotent-topic", {"message_id": "ID-1", "data": "duplicate"})
    print(f"  After idempotent publish (2 calls, same ID): "
          f"{sum(1 for r in received if 'idempotent' in r)} received")
    print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. DDD (Domain-Driven Design)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 3.1 Value Object ──

@dataclass(frozen=True)
class Money:
    """
    Value Object: 同値性は属性で判定。不変。

    考えてほしい疑問:
      ・Entity と Value Object の違いは？（Identity vs 属性による同値性）
      ・なぜ frozen=True（不変）にするか？（副作用防止、スレッドセーフ）
    """
    amount: int
    currency: str

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclass(frozen=True)
class Address:
    """Value Object: 住所"""
    street: str
    city: str
    country: str
    postal_code: str


# ── 3.2 Entity ──

@dataclass
class OrderItem:
    product_id: str
    product_name: str
    price: Money
    quantity: int

    @property
    def subtotal(self) -> Money:
        return Money(self.price.amount * self.quantity, self.price.currency)


# ── 3.3 Aggregate ──

class OrderStatus(Enum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


@dataclass
class Order:
    """
    Aggregate Root: Order

    DDD のルール:
      ・外部から Aggregate 内部のエンティティに直接アクセスしない
      ・Aggregate Root を通して操作する
      ・Aggregate 間の参照は ID のみ

    考えてほしい疑問:
      ・Aggregate の境界はどう決める？
        → トランザクション整合性が必要な範囲
      ・Aggregate を小さく保つ理由は？
        → パフォーマンス（ロック範囲）とスケーラビリティ
    """
    order_id: str
    customer_id: str
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.DRAFT
    shipping_address: Optional[Address] = None
    domain_events: list[dict] = field(default_factory=list)

    @property
    def total(self) -> Money:
        if not self.items:
            return Money(0, "JPY")
        result = Money(0, self.items[0].price.currency)
        for item in self.items:
            result = result.add(item.subtotal)
        return result

    def add_item(self, item: OrderItem) -> None:
        if self.status != OrderStatus.DRAFT:
            raise ValueError("Cannot modify a non-draft order")
        self.items.append(item)

    def place(self, shipping_address: Address) -> None:
        if not self.items:
            raise ValueError("Cannot place an empty order")
        self.shipping_address = shipping_address
        self.status = OrderStatus.PLACED
        self.domain_events.append({
            "type": "OrderPlaced",
            "order_id": self.order_id,
            "total": str(self.total),
        })

    def cancel(self) -> None:
        if self.status in (OrderStatus.SHIPPED,):
            raise ValueError("Cannot cancel a shipped order")
        self.status = OrderStatus.CANCELLED
        self.domain_events.append({
            "type": "OrderCancelled", "order_id": self.order_id,
        })


# ── 3.4 Repository Pattern ──

class OrderRepository:
    """
    Repository: Aggregate の永続化を抽象化

    [実装してみよう] Event-Sourced Repository に書き換える
    """
    def __init__(self) -> None:
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._store[order.order_id] = order

    def find_by_id(self, order_id: str) -> Optional[Order]:
        return self._store.get(order_id)

    def find_by_customer(self, customer_id: str) -> list[Order]:
        return [o for o in self._store.values() if o.customer_id == customer_id]


# ── 3.5 Bounded Context Mapping ──

class AntiCorruptionLayer:
    """
    Anti-Corruption Layer: 外部コンテキストのモデルを自コンテキストに変換

    考えてほしい疑問:
      ・レガシーシステムと統合するときなぜ ACL が必要か？
      ・Shared Kernel vs ACL: どちらを選ぶ？
        → チーム間の信頼度と結合度で判断
    """
    @staticmethod
    def translate_external_product(external: dict) -> OrderItem:
        """外部 Product Catalog の形式を Order コンテキストのモデルに変換"""
        return OrderItem(
            product_id=external["sku"],
            product_name=external["title"],
            price=Money(int(external["price_cents"]), external.get("currency", "JPY")),
            quantity=1,
        )


def demo_ddd() -> None:
    print("  ── DDD: Aggregate, Entity, Value Object ──")
    # Value Object
    price1 = Money(1000, "JPY")
    price2 = Money(500, "JPY")
    print(f"  Value Objects equal: {Money(100, 'JPY') == Money(100, 'JPY')}")
    print(f"  Money add: {price1.add(price2)}")

    # Aggregate
    order = Order(order_id="ORD-001", customer_id="CUST-42")
    order.add_item(OrderItem("P1", "Laptop", Money(99900, "JPY"), 1))
    order.add_item(OrderItem("P2", "Mouse", Money(3000, "JPY"), 2))
    print(f"  Order total: {order.total}")

    addr = Address("Shibuya 1-1", "Tokyo", "Japan", "150-0002")
    order.place(addr)
    print(f"  Order status: {order.status.value}")
    print(f"  Domain events: {order.domain_events}")

    # Repository
    repo = OrderRepository()
    repo.save(order)
    found = repo.find_by_id("ORD-001")
    print(f"  Repository find: {found is not None}")

    # Anti-Corruption Layer
    external = {"sku": "EXT-99", "title": "External Product",
                "price_cents": "4500", "currency": "JPY"}
    item = AntiCorruptionLayer.translate_external_product(external)
    print(f"  ACL translated: {item.product_name} ({item.price})")
    print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 分散システムパターン (Distributed Systems Patterns)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 4.1 CAP Theorem ──

def demo_cap_theorem() -> None:
    """
    CAP 定理: Consistency, Availability, Partition tolerance の3つから2つ

    考えてほしい疑問:
      ・「CA」は実質選べない。なぜか？→ ネットワーク分断は必ず起こる
      ・CP を選ぶ: 銀行システム（整合性重視）
      ・AP を選ぶ: SNS のタイムライン（可用性重視、結果整合性で OK）
    """
    print("  ── CAP Theorem ──")
    systems = {
        "CP (整合性 + 分断耐性)": {
            "examples": ["ZooKeeper", "HBase", "MongoDB (default)"],
            "tradeoff": "分断時に一部リクエストを拒否（可用性を犠牲）",
            "use_case": "金融取引、在庫管理",
        },
        "AP (可用性 + 分断耐性)": {
            "examples": ["Cassandra", "DynamoDB", "CouchDB"],
            "tradeoff": "分断時に古いデータを返す可能性（整合性を犠牲）",
            "use_case": "SNS タイムライン、DNS、ショッピングカート",
        },
    }
    for cat, info in systems.items():
        print(f"  {cat}")
        print(f"    Examples:  {', '.join(info['examples'])}")
        print(f"    Tradeoff:  {info['tradeoff']}")
        print(f"    Use case:  {info['use_case']}")
    print()


# ── 4.2 Consistent Hashing ──

class ConsistentHashRing:
    """
    Consistent Hashing: ノード追加/削除時の再配置を最小限に

    仮想ノードで負荷を均等に分散する。
    Dynamo, Cassandra, CDN のリクエストルーティングで使用。

    考えてほしい疑問:
      ・仮想ノードがないと何が問題か？→ 偏りが大きくなる
      ・ノード追加時に移動するキーはどれだけか？→ 約 K/N (K=キー数, N=ノード数)

    [実装してみよう] ノード重み付け（高性能サーバーに多くの仮想ノード）を追加
    """
    def __init__(self, num_virtual_nodes: int = 150) -> None:
        self.num_virtual_nodes = num_virtual_nodes
        self.ring: dict[int, str] = {}
        self.sorted_keys: list[int] = []
        self.nodes: set[str] = set()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        self.nodes.add(node)
        for i in range(self.num_virtual_nodes):
            vnode_key = f"{node}#vn{i}"
            h = self._hash(vnode_key)
            self.ring[h] = node
            self.sorted_keys.append(h)
        self.sorted_keys.sort()

    def remove_node(self, node: str) -> None:
        self.nodes.discard(node)
        keys_to_remove = [k for k, v in self.ring.items() if v == node]
        for k in keys_to_remove:
            del self.ring[k]
            self.sorted_keys.remove(k)

    def get_node(self, key: str) -> Optional[str]:
        if not self.sorted_keys:
            return None
        h = self._hash(key)
        # Binary search for the first hash >= h
        lo, hi = 0, len(self.sorted_keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.sorted_keys[mid] < h:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(self.sorted_keys):
            lo = 0  # Wrap around
        return self.ring[self.sorted_keys[lo]]


def demo_consistent_hashing() -> None:
    print("  ── Consistent Hashing ──")
    ring = ConsistentHashRing(num_virtual_nodes=100)
    for node in ["server-A", "server-B", "server-C"]:
        ring.add_node(node)

    keys = [f"user:{i}" for i in range(1000)]
    dist_before: dict[str, int] = defaultdict(int)
    mapping_before: dict[str, str] = {}
    for k in keys:
        node = ring.get_node(k)
        dist_before[node] += 1
        mapping_before[k] = node

    print("  Distribution (3 nodes):")
    for node, count in sorted(dist_before.items()):
        print(f"    {node}: {count} keys ({count/10:.1f}%)")

    # Add a 4th node
    ring.add_node("server-D")
    moved = 0
    dist_after: dict[str, int] = defaultdict(int)
    for k in keys:
        node = ring.get_node(k)
        dist_after[node] += 1
        if mapping_before[k] != node:
            moved += 1

    print(f"  After adding server-D:")
    for node, count in sorted(dist_after.items()):
        print(f"    {node}: {count} keys ({count/10:.1f}%)")
    print(f"  Keys moved: {moved} ({moved/10:.1f}%) — ideal: ~{1000//4}")
    print()


# ── 4.3 Leader Election ──

class LeaderElection:
    """
    リーダー選出シミュレーション (Bully Algorithm 風)

    考えてほしい疑問:
      ・Split-brain を防ぐには？→ 過半数合意 (Majority quorum)
      ・ZooKeeper, etcd がリーダー選出に使われる理由は？

    [実装してみよう] Raft の簡易実装（term, vote, log replication）
    """
    def __init__(self, nodes: list[str]) -> None:
        self.nodes = {n: True for n in nodes}  # name → alive
        self.leader: Optional[str] = None
        self.term = 0

    def elect(self) -> str:
        self.term += 1
        alive = [n for n, is_alive in self.nodes.items() if is_alive]
        if not alive:
            raise RuntimeError("No alive nodes")
        # Bully: highest ID wins
        self.leader = max(alive)
        return self.leader

    def heartbeat(self) -> bool:
        """Check if leader is still alive"""
        if self.leader and self.nodes.get(self.leader, False):
            return True
        # Re-election needed
        self.leader = None
        return False

    def kill_node(self, node: str) -> None:
        self.nodes[node] = False

    def revive_node(self, node: str) -> None:
        self.nodes[node] = True


def demo_leader_election() -> None:
    print("  ── Leader Election (Bully Algorithm) ──")
    le = LeaderElection(["node-1", "node-2", "node-3"])
    leader = le.elect()
    print(f"  Initial leader: {leader} (term={le.term})")

    le.kill_node("node-3")
    alive = le.heartbeat()
    print(f"  Heartbeat after killing node-3: {alive}")
    if not alive:
        new_leader = le.elect()
        print(f"  New leader: {new_leader} (term={le.term})")

    le.revive_node("node-3")
    newest = le.elect()
    print(f"  After reviving node-3: {newest} (term={le.term})")
    print()


# ── 4.4 Distributed Lock (Redlock Algorithm) ──

class RedlockSimulator:
    """
    Redlock アルゴリズムシミュレーション

    Redis クラスタ (N=5) の過半数 (3+) でロック取得 → 成功
    有効期限: lock_ttl - 取得にかかった時間

    考えてほしい疑問:
      ・なぜ単一 Redis インスタンスのロックでは不十分か？
        → SPOF (Single Point of Failure)
      ・Martin Kleppmann の Redlock 批判は何か？
        → GC pause でロック切れに気づかない可能性
    """
    def __init__(self, num_instances: int = 5, lock_ttl: float = 10.0) -> None:
        self.num_instances = num_instances
        self.lock_ttl = lock_ttl
        self.instances: list[dict[str, Any]] = [
            {"id": i, "locks": {}, "alive": True} for i in range(num_instances)
        ]
        self.quorum = num_instances // 2 + 1

    def try_lock(self, resource: str, client_id: str) -> tuple[bool, str]:
        start_time = time.monotonic()
        acquired = 0
        failed_instances = []

        for inst in self.instances:
            if not inst["alive"]:
                failed_instances.append(inst["id"])
                continue
            if resource not in inst["locks"]:
                inst["locks"][resource] = {
                    "client": client_id,
                    "expires": time.monotonic() + self.lock_ttl,
                }
                acquired += 1
            elif inst["locks"][resource]["expires"] < time.monotonic():
                # Expired lock, take it
                inst["locks"][resource] = {
                    "client": client_id,
                    "expires": time.monotonic() + self.lock_ttl,
                }
                acquired += 1

        elapsed = time.monotonic() - start_time
        validity_time = self.lock_ttl - elapsed

        if acquired >= self.quorum and validity_time > 0:
            return True, f"Lock acquired ({acquired}/{self.num_instances} instances)"
        else:
            # Release all acquired locks
            self._release(resource, client_id)
            return False, (f"Failed ({acquired}/{self.num_instances}, "
                           f"need {self.quorum})")

    def _release(self, resource: str, client_id: str) -> None:
        for inst in self.instances:
            lock = inst["locks"].get(resource)
            if lock and lock["client"] == client_id:
                del inst["locks"][resource]

    def unlock(self, resource: str, client_id: str) -> None:
        self._release(resource, client_id)


def demo_distributed_lock() -> None:
    print("  ── Distributed Lock (Redlock) ──")
    redlock = RedlockSimulator(num_instances=5)

    ok, msg = redlock.try_lock("order:123", "client-A")
    print(f"  Client-A lock: {ok} — {msg}")

    ok2, msg2 = redlock.try_lock("order:123", "client-B")
    print(f"  Client-B lock (same resource): {ok2} — {msg2}")

    redlock.unlock("order:123", "client-A")
    ok3, msg3 = redlock.try_lock("order:123", "client-B")
    print(f"  Client-B lock (after A unlocks): {ok3} — {msg3}")

    # Simulate 2 instances down
    redlock.instances[0]["alive"] = False
    redlock.instances[1]["alive"] = False
    redlock.unlock("order:123", "client-B")
    ok4, msg4 = redlock.try_lock("order:456", "client-C")
    print(f"  Client-C lock (2 instances down): {ok4} — {msg4}")

    redlock.instances[2]["alive"] = False  # Now 3 down, quorum lost
    redlock.unlock("order:456", "client-C")
    ok5, msg5 = redlock.try_lock("order:789", "client-D")
    print(f"  Client-D lock (3 instances down): {ok5} — {msg5}")
    print()


# ── 4.5 Two-Phase Commit ──

class TwoPhaseCommitCoordinator:
    """
    2PC (Two-Phase Commit) シミュレーション

    Phase 1 (Prepare): 全参加者に prepare を要求
    Phase 2 (Commit/Abort): 全員 OK → commit、1人でも NG → abort

    考えてほしい疑問:
      ・2PC のブロッキング問題とは？→ Coordinator がダウンすると全参加者がブロック
      ・3PC は何を改善するか？→ タイムアウトで自動的に決定できる
      ・Saga パターンとの使い分けは？→ 2PC は同期、Saga は非同期

    [実装してみよう] タイムアウト付き 2PC を実装する
    """
    def __init__(self) -> None:
        self.participants: list["TwoPhaseParticipant"] = []
        self.log: list[str] = []

    def add_participant(self, p: "TwoPhaseParticipant") -> None:
        self.participants.append(p)

    def execute(self, transaction_id: str) -> bool:
        self.log.append(f"  [Coordinator] Starting 2PC for {transaction_id}")

        # Phase 1: Prepare
        self.log.append("  [Phase 1] Sending PREPARE to all participants")
        votes = []
        for p in self.participants:
            vote = p.prepare(transaction_id)
            votes.append(vote)
            self.log.append(f"    {p.name}: {'VOTE_COMMIT' if vote else 'VOTE_ABORT'}")

        # Phase 2: Commit or Abort
        if all(votes):
            self.log.append("  [Phase 2] All voted COMMIT → sending COMMIT")
            for p in self.participants:
                p.commit(transaction_id)
            return True
        else:
            self.log.append("  [Phase 2] Some voted ABORT → sending ABORT")
            for p in self.participants:
                p.abort(transaction_id)
            return False


class TwoPhaseParticipant:
    def __init__(self, name: str, will_vote_yes: bool = True) -> None:
        self.name = name
        self.will_vote_yes = will_vote_yes
        self.committed: list[str] = []
        self.aborted: list[str] = []

    def prepare(self, transaction_id: str) -> bool:
        return self.will_vote_yes

    def commit(self, transaction_id: str) -> None:
        self.committed.append(transaction_id)

    def abort(self, transaction_id: str) -> None:
        self.aborted.append(transaction_id)


def demo_two_phase_commit() -> None:
    print("  ── Two-Phase Commit ──")
    # Success case
    coord = TwoPhaseCommitCoordinator()
    coord.add_participant(TwoPhaseParticipant("OrderDB", True))
    coord.add_participant(TwoPhaseParticipant("PaymentDB", True))
    coord.add_participant(TwoPhaseParticipant("InventoryDB", True))
    result = coord.execute("TXN-001")
    for line in coord.log:
        print(f"    {line}")
    print(f"  Result: {'COMMITTED' if result else 'ABORTED'}")

    # Failure case
    print()
    coord2 = TwoPhaseCommitCoordinator()
    coord2.add_participant(TwoPhaseParticipant("OrderDB", True))
    coord2.add_participant(TwoPhaseParticipant("PaymentDB", False))
    coord2.add_participant(TwoPhaseParticipant("InventoryDB", True))
    result2 = coord2.execute("TXN-002")
    for line in coord2.log:
        print(f"    {line}")
    print(f"  Result: {'COMMITTED' if result2 else 'ABORTED'}")
    print()


# ── 4.6 Vector Clock ──

class VectorClock:
    """
    Vector Clock: 分散システムでイベントの因果関係を追跡

    考えてほしい疑問:
      ・Lamport Clock との違いは？
        → Lamport は全順序、Vector Clock は因果関係を正確に判定
      ・Vector Clock のサイズがノード数に比例する問題は？
        → Dotted Version Vectors で改善 (Riak)

    [実装してみよう] マージ衝突の検出と解決ロジックを追加する
    """
    def __init__(self, node_id: str, initial: dict[str, int] | None = None) -> None:
        self.node_id = node_id
        self.clock: dict[str, int] = initial or {}
        if node_id not in self.clock:
            self.clock[node_id] = 0

    def increment(self) -> "VectorClock":
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1
        return self

    def merge(self, other: "VectorClock") -> "VectorClock":
        all_nodes = set(self.clock.keys()) | set(other.clock.keys())
        for node in all_nodes:
            self.clock[node] = max(self.clock.get(node, 0),
                                    other.clock.get(node, 0))
        self.increment()
        return self

    def happens_before(self, other: "VectorClock") -> bool:
        """self → other (self happened before other)"""
        at_least_one_less = False
        for node in set(self.clock.keys()) | set(other.clock.keys()):
            s = self.clock.get(node, 0)
            o = other.clock.get(node, 0)
            if s > o:
                return False
            if s < o:
                at_least_one_less = True
        return at_least_one_less

    def is_concurrent(self, other: "VectorClock") -> bool:
        return not self.happens_before(other) and not other.happens_before(self)

    def __repr__(self) -> str:
        return f"VC({self.clock})"


def demo_vector_clock() -> None:
    print("  ── Vector Clock ──")
    vc_a = VectorClock("A")
    vc_b = VectorClock("B")
    vc_c = VectorClock("C")

    # A performs local event
    vc_a.increment()
    print(f"  A local event:  {vc_a}")

    # A sends message to B (B merges)
    vc_b.merge(VectorClock("B", dict(vc_a.clock)))
    print(f"  B receives A:   {vc_b}")

    # C performs local event independently
    vc_c.increment()
    print(f"  C local event:  {vc_c}")

    # Check causality
    print(f"  A → B? {vc_a.happens_before(vc_b)}")
    print(f"  B → A? {vc_b.happens_before(vc_a)}")
    print(f"  A || C? {vc_a.is_concurrent(vc_c)} (concurrent)")
    print()


# ── 4.7 Gossip Protocol ──

class GossipNode:
    """
    Gossip Protocol: 疫学的な情報伝播

    各ノードがランダムに隣人に情報を伝播。最終的に全ノードに到達。
    Cassandra, Consul のメンバーシップ管理に使用。

    考えてほしい疑問:
      ・収束にかかるラウンド数は？→ O(log N)
      ・Push vs Pull vs Push-Pull の違いは？
    """
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.data: dict[str, Any] = {}
        self.peers: list["GossipNode"] = []
        self.generation = 0

    def update_local(self, key: str, value: Any) -> None:
        self.generation += 1
        self.data[key] = {"value": value, "gen": self.generation, "origin": self.node_id}

    def gossip_round(self) -> int:
        """Push gossip to a random peer. Returns number of updates propagated."""
        if not self.peers:
            return 0
        target = random.choice(self.peers)
        updates = 0
        for key, info in self.data.items():
            target_info = target.data.get(key)
            if target_info is None or target_info["gen"] < info["gen"]:
                target.data[key] = dict(info)
                updates += 1
        return updates


def demo_gossip_protocol() -> None:
    print("  ── Gossip Protocol ──")
    random.seed(42)
    nodes = [GossipNode(f"node-{i}") for i in range(8)]
    # Create a mesh: each node knows 3 random peers
    for node in nodes:
        others = [n for n in nodes if n is not node]
        node.peers = random.sample(others, min(3, len(others)))

    # Node 0 has some data
    nodes[0].update_local("leader", "node-0")
    nodes[0].update_local("config_version", 42)

    # Run gossip rounds
    for round_num in range(10):
        total_updates = 0
        for node in nodes:
            total_updates += node.gossip_round()
        informed = sum(1 for n in nodes if "leader" in n.data)
        if round_num < 5 or informed == len(nodes):
            print(f"  Round {round_num+1}: {informed}/{len(nodes)} nodes informed, "
                  f"{total_updates} updates")
        if informed == len(nodes):
            print(f"  Full convergence in {round_num+1} rounds!")
            break
    print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 汎用システム設計問題 (System Design Interview Problems)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 5.1 URL Shortener ──

class URLShortener:
    """
    URL 短縮サービス設計

    要件: 10億URL、短縮URL 7文字（Base62 → 62^7 ≈ 3.5兆通り）
    設計ポイント:
      ・Base62 エンコーディング (0-9, a-z, A-Z)
      ・ハッシュ衝突の処理
      ・301 (Permanent) vs 302 (Temporary) リダイレクト
      ・カスタム短縮URL

    考えてほしい疑問:
      ・なぜ UUID をそのまま使わないのか？→ 長すぎる（32文字）
      ・書き込み vs 読み込みの比率は？→ 1:100（読み重い → キャッシュ重要）
      ・分析機能（クリック数、地域）をどう追加する？

    [実装してみよう] ブルームフィルタで存在チェックを高速化する
    """
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self) -> None:
        self.url_to_short: dict[str, str] = {}
        self.short_to_url: dict[str, str] = {}
        self.counter = 100000  # Auto-increment ID
        self.click_stats: dict[str, int] = defaultdict(int)

    def _base62_encode(self, num: int) -> str:
        if num == 0:
            return self.BASE62[0]
        digits = []
        while num > 0:
            digits.append(self.BASE62[num % 62])
            num //= 62
        return "".join(reversed(digits))

    def _hash_url(self, url: str) -> str:
        """MD5 の先頭7文字を Base62 エンコード"""
        h = int(hashlib.md5(url.encode()).hexdigest()[:12], 16)
        return self._base62_encode(h)[:7]

    def shorten(self, long_url: str, custom_alias: str | None = None) -> str:
        if long_url in self.url_to_short:
            return self.url_to_short[long_url]

        if custom_alias:
            if custom_alias in self.short_to_url:
                raise ValueError(f"Alias '{custom_alias}' already taken")
            short = custom_alias
        else:
            # Try hash first, fallback to counter
            short = self._hash_url(long_url)
            if short in self.short_to_url:
                self.counter += 1
                short = self._base62_encode(self.counter)[:7]

        self.url_to_short[long_url] = short
        self.short_to_url[short] = long_url
        return short

    def resolve(self, short_url: str, redirect_type: int = 301) -> tuple[Optional[str], int]:
        """
        301 Permanent: ブラウザがキャッシュ → サーバー負荷低減、分析不可
        302 Temporary: 毎回サーバーに問い合わせ → 分析可能
        """
        url = self.short_to_url.get(short_url)
        if url:
            self.click_stats[short_url] += 1
            return url, redirect_type
        return None, 404


def demo_url_shortener() -> None:
    print("  ── URL Shortener ──")
    shortener = URLShortener()

    urls = [
        "https://example.com/very/long/path/to/resource?param=value",
        "https://docs.google.com/spreadsheets/d/1234567890/edit#gid=0",
        "https://github.com/user/repo/pull/42",
    ]
    for url in urls:
        short = shortener.shorten(url)
        resolved, status = shortener.resolve(short, 302)
        print(f"  {url[:50]}... → {short} (resolve: {status})")

    # Custom alias
    custom = shortener.shorten("https://special.example.com", custom_alias="mylink")
    print(f"  Custom alias: mylink → {shortener.resolve('mylink')[0]}")

    # Base62 encoding demo
    print(f"  Base62(100000) = {shortener._base62_encode(100000)}")
    print(f"  Base62(62^7-1) = {shortener._base62_encode(62**7-1)} (max 7 chars)")
    print()


# ── 5.2 Rate Limiter (3 algorithms) ──

class TokenBucketLimiter:
    """
    Token Bucket: トークンが一定レートで補充。リクエスト毎にトークン消費。

    特徴: バースト許容（バケットに溜まったトークン分）
    用途: API Gateway、AWS API Gateway の制限
    """
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class SlidingWindowLogLimiter:
    """
    Sliding Window Log: タイムスタンプのログを保持し、ウィンドウ内のカウント

    特徴: 正確だがメモリ使用量が多い
    用途: 精密なレート制限が必要な場面
    """
    def __init__(self, window_seconds: float, max_requests: int) -> None:
        self.window = window_seconds
        self.max_requests = max_requests
        self.logs: dict[str, deque] = defaultdict(deque)

    def allow(self, client_id: str = "default") -> bool:
        now = time.monotonic()
        log = self.logs[client_id]
        # Remove expired entries
        while log and log[0] <= now - self.window:
            log.popleft()
        if len(log) < self.max_requests:
            log.append(now)
            return True
        return False


class FixedWindowCounterLimiter:
    """
    Fixed Window Counter: 固定時間ウィンドウ内のカウンター

    特徴: シンプル、メモリ効率良い。ウィンドウ境界でバースト可能
    用途: 大まかなレート制限で十分な場面

    考えてほしい疑問:
      ・ウィンドウ境界のバースト問題とは？
        → 59秒と61秒で合計2倍のリクエストが通る
      ・Sliding Window Counter は何を改善する？→ 前後ウィンドウの加重平均
    """
    def __init__(self, window_seconds: float, max_requests: int) -> None:
        self.window = window_seconds
        self.max_requests = max_requests
        self.counters: dict[str, dict] = {}

    def allow(self, client_id: str = "default") -> bool:
        now = time.monotonic()
        window_key = int(now / self.window)

        if client_id not in self.counters:
            self.counters[client_id] = {"window": window_key, "count": 0}

        entry = self.counters[client_id]
        if entry["window"] != window_key:
            entry["window"] = window_key
            entry["count"] = 0

        if entry["count"] < self.max_requests:
            entry["count"] += 1
            return True
        return False


def demo_rate_limiter() -> None:
    print("  ── Rate Limiter (3 Algorithms) ──")

    # Token Bucket
    tb = TokenBucketLimiter(capacity=5, refill_rate=2.0)
    results = [tb.allow() for _ in range(8)]
    print(f"  Token Bucket (cap=5, 8 requests): "
          f"{sum(results)} allowed, {len(results)-sum(results)} rejected")

    # Sliding Window Log
    sw = SlidingWindowLogLimiter(window_seconds=1.0, max_requests=3)
    results = [sw.allow("client-1") for _ in range(5)]
    print(f"  Sliding Window Log (3/sec, 5 requests): "
          f"{sum(results)} allowed, {len(results)-sum(results)} rejected")

    # Fixed Window Counter
    fw = FixedWindowCounterLimiter(window_seconds=1.0, max_requests=4)
    results = [fw.allow("client-1") for _ in range(6)]
    print(f"  Fixed Window Counter (4/sec, 6 requests): "
          f"{sum(results)} allowed, {len(results)-sum(results)} rejected")

    print("""
  アルゴリズム比較:
  ┌──────────────────────┬────────┬──────────┬────────────┐
  │ Algorithm            │ Memory │ Accuracy │ Burst      │
  ├──────────────────────┼────────┼──────────┼────────────┤
  │ Token Bucket         │ O(1)   │ Medium   │ Allowed    │
  │ Sliding Window Log   │ O(N)   │ High     │ Controlled │
  │ Fixed Window Counter │ O(1)   │ Low      │ Boundary   │
  └──────────────────────┴────────┴──────────┴────────────┘
  """)


# ── 5.3 Chat System ──

@dataclass
class ChatMessage:
    message_id: str
    sender_id: str
    channel_id: str
    content: str
    timestamp: float
    sequence: int  # Per-channel ordering


class PresenceService:
    """ユーザーのオンライン/オフライン状態管理"""
    def __init__(self) -> None:
        self.status: dict[str, dict] = {}

    def heartbeat(self, user_id: str) -> None:
        self.status[user_id] = {"online": True, "last_seen": time.monotonic()}

    def disconnect(self, user_id: str) -> None:
        if user_id in self.status:
            self.status[user_id]["online"] = False

    def is_online(self, user_id: str) -> bool:
        info = self.status.get(user_id)
        if not info:
            return False
        # Consider offline if no heartbeat for 30 seconds
        if time.monotonic() - info["last_seen"] > 30:
            return False
        return info["online"]


class ChatService:
    """
    チャットシステム設計

    設計ポイント:
      ・WebSocket でリアルタイム配信
      ・メッセージ順序保証（per-channel sequence number）
      ・Fan-out: グループチャットで全メンバーに配信
      ・オフラインユーザーへのプッシュ通知

    考えてほしい疑問:
      ・1対1 と グループチャットで設計がどう変わるか？
      ・E2E 暗号化はどの層で実装する？
      ・メッセージの既読管理はどう設計する？

    [実装してみよう] メッセージ既読 (read receipt) を追加する
    """
    def __init__(self) -> None:
        self.channels: dict[str, list[str]] = {}  # channel → [user_ids]
        self.messages: dict[str, list[ChatMessage]] = defaultdict(list)
        self.sequence_counters: dict[str, int] = defaultdict(int)
        self.presence = PresenceService()
        self.undelivered: dict[str, list[ChatMessage]] = defaultdict(list)

    def create_channel(self, channel_id: str, members: list[str]) -> None:
        self.channels[channel_id] = members

    def send_message(self, sender_id: str, channel_id: str,
                     content: str) -> ChatMessage:
        self.sequence_counters[channel_id] += 1
        msg = ChatMessage(
            message_id=str(uuid.uuid4())[:8],
            sender_id=sender_id,
            channel_id=channel_id,
            content=content,
            timestamp=time.time(),
            sequence=self.sequence_counters[channel_id],
        )
        self.messages[channel_id].append(msg)

        # Fan-out to channel members
        for member in self.channels.get(channel_id, []):
            if member == sender_id:
                continue
            if self.presence.is_online(member):
                pass  # Would push via WebSocket
            else:
                self.undelivered[member].append(msg)

        return msg

    def get_history(self, channel_id: str, limit: int = 50) -> list[ChatMessage]:
        return self.messages[channel_id][-limit:]

    def get_undelivered(self, user_id: str) -> list[ChatMessage]:
        msgs = self.undelivered.pop(user_id, [])
        return msgs


def demo_chat_system() -> None:
    print("  ── Chat System Design ──")
    chat = ChatService()
    chat.create_channel("team-alpha", ["alice", "bob", "charlie"])

    chat.presence.heartbeat("alice")
    chat.presence.heartbeat("bob")
    # Charlie is offline

    msg1 = chat.send_message("alice", "team-alpha", "Hey team!")
    msg2 = chat.send_message("bob", "team-alpha", "Hi Alice!")
    msg3 = chat.send_message("alice", "team-alpha", "Let's discuss the design")

    history = chat.get_history("team-alpha")
    print(f"  Channel history ({len(history)} messages):")
    for m in history:
        print(f"    seq={m.sequence} [{m.sender_id}]: {m.content}")

    undelivered = chat.get_undelivered("charlie")
    print(f"  Charlie's undelivered: {len(undelivered)} messages")
    print(f"  Alice online: {chat.presence.is_online('alice')}")
    print(f"  Charlie online: {chat.presence.is_online('charlie')}")
    print()


# ── 5.4 News Feed System ──

class NewsFeedService:
    """
    ニュースフィード設計 (Twitter / Instagram)

    Push Model (Fan-out on Write):
      投稿時に全フォロワーのフィードに書き込み
      → 読み取り高速、書き込み重い（セレブ問題）

    Pull Model (Fan-out on Read):
      読み取り時にフォロー先の投稿を集約
      → 書き込み軽い、読み取り重い

    Hybrid: 一般ユーザーは Push、セレブは Pull

    考えてほしい疑問:
      ・Twitter で 1億フォロワーの人が投稿したら Fan-out on Write で何が起こる？
      ・タイムラインのランキング（時系列 vs 関連性）はどう実装する？
      ・Sharding key に user_id を使う理由は？
    """
    CELEBRITY_THRESHOLD = 100

    def __init__(self) -> None:
        self.follows: dict[str, set[str]] = defaultdict(set)  # follower → {followees}
        self.followers: dict[str, set[str]] = defaultdict(set)  # followee → {followers}
        self.posts: dict[str, list[dict]] = defaultdict(list)  # user → [posts]
        self.feed_cache: dict[str, list[dict]] = defaultdict(list)  # user → precomputed feed

    def follow(self, follower: str, followee: str) -> None:
        self.follows[follower].add(followee)
        self.followers[followee].add(follower)

    def is_celebrity(self, user_id: str) -> bool:
        return len(self.followers[user_id]) >= self.CELEBRITY_THRESHOLD

    def post(self, user_id: str, content: str) -> dict:
        p = {"id": str(uuid.uuid4())[:8], "user": user_id,
             "content": content, "ts": time.time()}
        self.posts[user_id].append(p)

        # Fan-out on Write (for non-celebrities)
        if not self.is_celebrity(user_id):
            for follower in self.followers[user_id]:
                self.feed_cache[follower].append(p)
                # Keep feed bounded
                if len(self.feed_cache[follower]) > 200:
                    self.feed_cache[follower] = self.feed_cache[follower][-200:]
        return p

    def get_feed(self, user_id: str, limit: int = 10) -> list[dict]:
        """Hybrid: merge cached feed with celebrity pull"""
        feed = list(self.feed_cache.get(user_id, []))

        # Pull from celebrities
        for followee in self.follows[user_id]:
            if self.is_celebrity(followee):
                feed.extend(self.posts[followee][-limit:])

        # Sort by timestamp, most recent first
        feed.sort(key=lambda p: p["ts"], reverse=True)
        return feed[:limit]


def demo_news_feed() -> None:
    print("  ── News Feed (Push vs Pull vs Hybrid) ──")
    feed_svc = NewsFeedService()
    NewsFeedService.CELEBRITY_THRESHOLD = 3  # Lower for demo

    # Create follows
    for i in range(5):
        feed_svc.follow(f"user-{i}", "celebrity")
    feed_svc.follow("user-0", "user-1")
    feed_svc.follow("user-0", "user-2")

    print(f"  Celebrity has {len(feed_svc.followers['celebrity'])} followers "
          f"(threshold={NewsFeedService.CELEBRITY_THRESHOLD})")
    print(f"  Is celebrity: {feed_svc.is_celebrity('celebrity')}")

    # Regular user posts (fan-out on write)
    feed_svc.post("user-1", "Hello from user-1!")
    feed_svc.post("user-2", "Regular user post")

    # Celebrity posts (no fan-out)
    feed_svc.post("celebrity", "Big announcement!")

    feed = feed_svc.get_feed("user-0", limit=5)
    print(f"  user-0's feed ({len(feed)} items):")
    for item in feed:
        mode = "(pull)" if feed_svc.is_celebrity(item["user"]) else "(push)"
        print(f"    [{item['user']}] {item['content']} {mode}")
    print()


# ── 5.5 Notification System ──

class NotificationPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Notification:
    notification_id: str
    user_id: str
    channel: str  # push, email, sms
    title: str
    body: str
    priority: NotificationPriority
    created_at: float = field(default_factory=time.time)
    attempts: int = 0
    delivered: bool = False


class NotificationService:
    """
    通知システム設計

    設計ポイント:
      ・優先度キュー（CRITICAL は即座に、LOW はバッチ）
      ・レート制限（ユーザーへのスパム防止）
      ・リトライ（Exponential Backoff）
      ・チャネル別配信（Push / Email / SMS）
      ・ユーザー設定（通知オフ、時間帯制限）

    考えてほしい疑問:
      ・1日1億通知をどう処理する？→ メッセージキュー + ワーカー群
      ・Exactly-once delivery は必要か？→ At-least-once + 冪等性で十分
    """
    def __init__(self) -> None:
        self.queue: list[tuple[int, float, Notification]] = []  # Priority queue
        self.delivered: list[Notification] = []
        self.failed: list[Notification] = []
        self.rate_limits: dict[str, list[float]] = defaultdict(list)
        self.max_per_hour = 10
        self.user_preferences: dict[str, dict] = {}

    def set_preferences(self, user_id: str, prefs: dict) -> None:
        self.user_preferences[user_id] = prefs

    def _check_rate_limit(self, user_id: str) -> bool:
        now = time.monotonic()
        timestamps = self.rate_limits[user_id]
        # Remove entries older than 1 hour
        self.rate_limits[user_id] = [t for t in timestamps if now - t < 3600]
        return len(self.rate_limits[user_id]) < self.max_per_hour

    def enqueue(self, notification: Notification) -> bool:
        # Check user preferences
        prefs = self.user_preferences.get(notification.user_id, {})
        if prefs.get("muted", False):
            return False

        # Rate limit check
        if not self._check_rate_limit(notification.user_id):
            return False

        heapq.heappush(self.queue,
                       (notification.priority.value, notification.created_at,
                        notification))
        self.rate_limits[notification.user_id].append(time.monotonic())
        return True

    def process_batch(self, batch_size: int = 10,
                      delivery_sim: Callable | None = None) -> int:
        """Process notifications from priority queue"""
        delivered = 0
        for _ in range(min(batch_size, len(self.queue))):
            _, _, notif = heapq.heappop(self.queue)
            notif.attempts += 1
            # Simulate delivery
            success = True
            if delivery_sim:
                try:
                    delivery_sim(notif)
                except Exception:
                    success = False

            if success:
                notif.delivered = True
                self.delivered.append(notif)
                delivered += 1
            else:
                # Retry with exponential backoff (max 3 attempts)
                if notif.attempts < 3:
                    heapq.heappush(self.queue,
                                   (notif.priority.value, notif.created_at, notif))
                else:
                    self.failed.append(notif)
        return delivered


def demo_notification_system() -> None:
    print("  ── Notification System ──")
    svc = NotificationService()
    svc.max_per_hour = 5

    notifications = [
        Notification("N1", "user-1", "push", "Order Shipped",
                     "Your order is on the way", NotificationPriority.HIGH),
        Notification("N2", "user-1", "email", "Weekly Digest",
                     "Here's what you missed", NotificationPriority.LOW),
        Notification("N3", "user-2", "sms", "Security Alert",
                     "New login detected", NotificationPriority.CRITICAL),
        Notification("N4", "user-1", "push", "Flash Sale",
                     "50% off today only", NotificationPriority.MEDIUM),
    ]

    for n in notifications:
        queued = svc.enqueue(n)
        print(f"  Enqueue {n.notification_id} ({n.priority.name}): "
              f"{'queued' if queued else 'rejected'}")

    delivered = svc.process_batch(10)
    print(f"  Processed: {delivered} delivered, {len(svc.failed)} failed")
    print(f"  Delivery order (by priority):")
    for n in svc.delivered:
        print(f"    {n.notification_id}: {n.title} [{n.priority.name}] "
              f"→ {n.channel}")

    # Test rate limiting
    svc2 = NotificationService()
    svc2.max_per_hour = 3
    count = 0
    for i in range(5):
        n = Notification(f"RL-{i}", "user-X", "push", f"Msg {i}", "body",
                         NotificationPriority.MEDIUM)
        if svc2.enqueue(n):
            count += 1
    print(f"  Rate limiting (max 3/hr, 5 attempts): {count} queued")
    print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. スケーラビリティパターン (Scalability Patterns)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 6.1 Database Sharding ──

class ShardingStrategy(Enum):
    RANGE = "range"
    HASH = "hash"
    DIRECTORY = "directory"


class ShardManager:
    """
    データベースシャーディング

    Range: キーの範囲で分割（ホットスポットの可能性）
    Hash: キーのハッシュで分割（均等だがレンジクエリ困難）
    Directory: ルックアップテーブルで分割（柔軟だが SPOF リスク）

    考えてほしい疑問:
      ・シャーディングキーの選び方は？→ カーディナリティが高く均等分散するもの
      ・Cross-shard JOIN はなぜ避けるべきか？
      ・Re-sharding（シャード追加）はどうする？→ Consistent Hashing

    [実装してみよう] Consistent Hashing ベースのシャーディングを実装する
    """
    def __init__(self, num_shards: int, strategy: ShardingStrategy) -> None:
        self.num_shards = num_shards
        self.strategy = strategy
        self.shards: dict[int, list[dict]] = {i: [] for i in range(num_shards)}
        self.directory: dict[str, int] = {}
        # Range boundaries
        self.range_boundaries: list[int] = []
        if strategy == ShardingStrategy.RANGE:
            step = 1000000 // num_shards
            self.range_boundaries = [step * (i + 1) for i in range(num_shards - 1)]

    def _get_shard_hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.num_shards

    def _get_shard_range(self, key: int) -> int:
        for i, boundary in enumerate(self.range_boundaries):
            if key < boundary:
                return i
        return self.num_shards - 1

    def _get_shard_directory(self, key: str) -> int:
        if key not in self.directory:
            # Assign to least-loaded shard
            min_shard = min(range(self.num_shards),
                            key=lambda s: len(self.shards[s]))
            self.directory[key] = min_shard
        return self.directory[key]

    def insert(self, key: str, record: dict) -> int:
        if self.strategy == ShardingStrategy.HASH:
            shard_id = self._get_shard_hash(key)
        elif self.strategy == ShardingStrategy.RANGE:
            shard_id = self._get_shard_range(int(key) if key.isdigit() else hash(key) % 1000000)
        else:
            shard_id = self._get_shard_directory(key)

        self.shards[shard_id].append({"key": key, **record})
        return shard_id

    def get_distribution(self) -> dict[int, int]:
        return {s: len(records) for s, records in self.shards.items()}


def demo_sharding() -> None:
    print("  ── Database Sharding Strategies ──")
    for strategy in ShardingStrategy:
        sm = ShardManager(num_shards=4, strategy=strategy)
        for i in range(100):
            sm.insert(str(i * 1000), {"data": f"record-{i}"})
        dist = sm.get_distribution()
        total = sum(dist.values())
        print(f"  {strategy.value.upper()} sharding (4 shards, {total} records):")
        for shard_id, count in sorted(dist.items()):
            bar = "#" * (count // 2)
            print(f"    Shard {shard_id}: {count:3d} records {bar}")
    print()


# ── 6.2 Read Replica Pattern ──

class ReadReplicaCluster:
    """
    Read Replica: 書き込みは Primary、読み取りは Replica に分散

    考えてほしい疑問:
      ・Replication Lag がある間の読み取りは古いデータを返す。
        どうする？→ Read-your-own-writes 保証
      ・Replica の数はどう決める？→ 読み取り負荷 / 1台のスループット
    """
    def __init__(self, num_replicas: int = 3) -> None:
        self.primary: dict[str, Any] = {}
        self.replicas: list[dict[str, Any]] = [{} for _ in range(num_replicas)]
        self.write_count = 0
        self.read_counts: list[int] = [0] * num_replicas
        self.replication_lag: list[int] = [0] * num_replicas

    def write(self, key: str, value: Any) -> None:
        self.primary[key] = value
        self.write_count += 1
        # Simulate async replication
        for i, replica in enumerate(self.replicas):
            replica[key] = value
            self.replication_lag[i] = 0

    def read(self, key: str) -> Any:
        # Round-robin across replicas
        idx = sum(self.read_counts) % len(self.replicas)
        self.read_counts[idx] += 1
        return self.replicas[idx].get(key)


def demo_read_replica() -> None:
    print("  ── Read Replica Pattern ──")
    cluster = ReadReplicaCluster(num_replicas=3)
    cluster.write("user:1", {"name": "Alice"})
    cluster.write("user:2", {"name": "Bob"})

    for _ in range(9):
        cluster.read("user:1")

    print(f"  Writes to primary: {cluster.write_count}")
    print(f"  Reads per replica: {cluster.read_counts}")
    print(f"  Read load balanced: {'Yes' if max(cluster.read_counts) - min(cluster.read_counts) <= 1 else 'No'}")
    print()


# ── 6.3 Cache Strategies ──

class CacheStrategy(Enum):
    CACHE_ASIDE = "Cache-Aside"
    WRITE_THROUGH = "Write-Through"
    WRITE_BEHIND = "Write-Behind"
    READ_THROUGH = "Read-Through"


class CacheSimulator:
    """
    キャッシュ戦略

    Cache-Aside (Lazy Loading):
      読み取り: キャッシュ確認 → ミスなら DB → キャッシュに格納
      書き込み: DB に書き込み → キャッシュ無効化

    Write-Through:
      書き込み: キャッシュ + DB 同時書き込み
      → 整合性高い、書き込みレイテンシ増

    Write-Behind (Write-Back):
      書き込み: キャッシュのみ → 非同期で DB
      → 書き込み高速、データロスリスク

    Read-Through:
      読み取り: キャッシュが自ら DB に問い合わせ
      → Cache-Aside と似るがキャッシュ側にロジック

    考えてほしい疑問:
      ・キャッシュの TTL はどう決める？
      ・Thundering Herd 問題とは？→ TTL 切れで全リクエストが DB に殺到
      ・Cache Stampede の防止策は？→ Mutex lock, Probabilistic early expiration

    [実装してみよう] LRU 淘汰ポリシーを実装する
    """
    def __init__(self, strategy: CacheStrategy) -> None:
        self.strategy = strategy
        self.cache: dict[str, Any] = {}
        self.db: dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_reads = 0
        self.db_writes = 0
        self.write_behind_queue: list[tuple[str, Any]] = []

    def read(self, key: str) -> Any:
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]

        self.cache_misses += 1
        self.db_reads += 1
        value = self.db.get(key)
        if value is not None:
            self.cache[key] = value
        return value

    def write(self, key: str, value: Any) -> None:
        if self.strategy == CacheStrategy.CACHE_ASIDE:
            self.db[key] = value
            self.db_writes += 1
            self.cache.pop(key, None)  # Invalidate

        elif self.strategy == CacheStrategy.WRITE_THROUGH:
            self.cache[key] = value
            self.db[key] = value
            self.db_writes += 1

        elif self.strategy == CacheStrategy.WRITE_BEHIND:
            self.cache[key] = value
            self.write_behind_queue.append((key, value))
            # Flush periodically (simulated)

        elif self.strategy == CacheStrategy.READ_THROUGH:
            self.db[key] = value
            self.db_writes += 1
            self.cache.pop(key, None)

    def flush_write_behind(self) -> int:
        """Flush write-behind queue to DB"""
        count = len(self.write_behind_queue)
        for key, value in self.write_behind_queue:
            self.db[key] = value
            self.db_writes += 1
        self.write_behind_queue.clear()
        return count

    def stats(self) -> dict:
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total * 100 if total > 0 else 0
        return {
            "strategy": self.strategy.value,
            "hit_rate": f"{hit_rate:.1f}%",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "db_reads": self.db_reads,
            "db_writes": self.db_writes,
        }


def demo_cache_strategies() -> None:
    print("  ── Cache Strategies ──")
    for strategy in CacheStrategy:
        sim = CacheSimulator(strategy)
        # Pre-populate DB
        for i in range(10):
            sim.db[f"key-{i}"] = f"value-{i}"

        # Read pattern: some keys repeatedly
        for _ in range(3):
            for i in range(5):
                sim.read(f"key-{i}")

        # Write
        sim.write("key-0", "updated")
        sim.read("key-0")

        if strategy == CacheStrategy.WRITE_BEHIND:
            sim.flush_write_behind()

        stats = sim.stats()
        print(f"  {stats['strategy']:16s} | Hit rate: {stats['hit_rate']:6s} | "
              f"DB reads: {stats['db_reads']} | DB writes: {stats['db_writes']}")
    print()


# ── 6.4 CDN Patterns ──

class CDNSimulator:
    """
    CDN (Content Delivery Network) シミュレーション

    考えてほしい疑問:
      ・Pull CDN vs Push CDN の違いは？
        → Pull: 初回リクエスト時にオリジンから取得 (一般的)
        → Push: 事前にエッジにデプロイ (変更少ないコンテンツ)
      ・Cache-Control ヘッダーのベストプラクティスは？
        → 静的: max-age=31536000, immutable
        → 動的: no-cache or short max-age
    """
    def __init__(self, edge_locations: list[str]) -> None:
        self.origin: dict[str, str] = {}
        self.edges: dict[str, dict[str, str]] = {loc: {} for loc in edge_locations}
        self.origin_hits = 0
        self.edge_hits = 0

    def upload_to_origin(self, path: str, content: str) -> None:
        self.origin[path] = content

    def request(self, path: str, edge_location: str) -> tuple[str, str]:
        """Returns (content, source)"""
        edge = self.edges.get(edge_location, {})
        if path in edge:
            self.edge_hits += 1
            return edge[path], f"edge:{edge_location}"

        # Cache miss → fetch from origin
        if path in self.origin:
            self.origin_hits += 1
            content = self.origin[path]
            if edge_location in self.edges:
                self.edges[edge_location][path] = content
            return content, "origin"
        return "", "404"


def demo_cdn() -> None:
    print("  ── CDN Pattern ──")
    cdn = CDNSimulator(["tokyo", "singapore", "us-west"])
    cdn.upload_to_origin("/static/logo.png", "PNG_DATA_HERE")
    cdn.upload_to_origin("/api/data.json", '{"key": "value"}')

    requests = [
        ("/static/logo.png", "tokyo"),
        ("/static/logo.png", "tokyo"),     # Cache hit
        ("/static/logo.png", "singapore"), # Different edge
        ("/static/logo.png", "singapore"), # Cache hit
        ("/api/data.json", "us-west"),
    ]
    for path, edge in requests:
        _, source = cdn.request(path, edge)
        print(f"  {path} @ {edge:12s} → {source}")
    print(f"  Origin hits: {cdn.origin_hits}, Edge hits: {cdn.edge_hits}")
    print()


# ── 6.5 Back-pressure Handling ──

class BackPressureQueue:
    """
    Back-pressure: 下流が処理しきれない場合の制御

    戦略:
      1. Drop (最新 or 最古) - メトリクス、ログ
      2. Buffer (バッファリング) - メッセージキュー
      3. Throttle (上流を減速) - TCP フロー制御
      4. Sample (サンプリング) - 高頻度テレメトリ

    考えてほしい疑問:
      ・Reactive Streams の back-pressure は何を標準化した？
      ・Kafka がバックプレッシャーに強い理由は？→ Consumer が Pull する設計
    """
    def __init__(self, capacity: int, strategy: str = "drop_oldest") -> None:
        self.capacity = capacity
        self.strategy = strategy
        self.queue: deque = deque()
        self.dropped = 0
        self.processed = 0

    def push(self, item: Any) -> bool:
        if len(self.queue) >= self.capacity:
            if self.strategy == "drop_oldest":
                self.queue.popleft()
                self.dropped += 1
            elif self.strategy == "drop_newest":
                self.dropped += 1
                return False
            elif self.strategy == "block":
                return False  # Would block in real implementation
        self.queue.append(item)
        return True

    def pop(self) -> Any:
        if self.queue:
            self.processed += 1
            return self.queue.popleft()
        return None

    def stats(self) -> dict:
        return {
            "queued": len(self.queue),
            "dropped": self.dropped,
            "processed": self.processed,
        }


def demo_back_pressure() -> None:
    print("  ── Back-pressure Handling ──")
    for strategy in ["drop_oldest", "drop_newest", "block"]:
        q = BackPressureQueue(capacity=5, strategy=strategy)

        # Producer is faster than consumer
        for i in range(10):
            q.push(f"item-{i}")

        # Consumer processes some
        for _ in range(3):
            q.pop()

        stats = q.stats()
        print(f"  {strategy:12s}: queued={stats['queued']}, "
              f"dropped={stats['dropped']}, processed={stats['processed']}")
    print()


# ── 6.6 Horizontal vs Vertical Scaling ──

def demo_scaling_comparison() -> None:
    print("  ── Horizontal vs Vertical Scaling ──")
    print("""
  ┌─────────────────────┬──────────────────────┬──────────────────────┐
  │                     │ Vertical (Scale Up)  │ Horizontal (Scale Out)│
  ├─────────────────────┼──────────────────────┼──────────────────────┤
  │ How                 │ Bigger machine       │ More machines        │
  │ Cost                │ Exponential          │ Linear               │
  │ Limit               │ Hardware ceiling     │ Theoretically none   │
  │ Complexity          │ Low                  │ High (distributed)   │
  │ Downtime            │ Usually required     │ Zero-downtime        │
  │ Data Consistency    │ Easy (single node)   │ Hard (distributed)   │
  │ Failure Impact      │ Total                │ Partial              │
  │ Examples            │ Bigger RDS instance  │ Add more EC2s / pods │
  └─────────────────────┴──────────────────────┴──────────────────────┘

  いつ Vertical を選ぶか:
    ・初期段階でシンプルさを優先したいとき
    ・データベースで強い整合性が必要なとき
    ・スケール要件が予測可能で上限が見えているとき

  いつ Horizontal を選ぶか:
    ・高可用性が必要なとき（SPOF を排除）
    ・トラフィックが予測困難で弾力的にスケールしたいとき
    ・地理的に分散する必要があるとき
  """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main() -> None:
    print("=" * 68)
    print("  System Design Patterns - FAANG Tech Lead / PM 面接対策")
    print("=" * 68)

    # 1. Microservices
    print("\n" + "=" * 68)
    print("  1. マイクロサービスパターン (Microservices Patterns)")
    print("=" * 68)
    demo_service_decomposition()
    demo_api_gateway()
    demo_service_discovery()
    demo_saga()
    demo_circuit_breaker()
    demo_sidecar()

    # 2. Event-Driven Architecture
    print("=" * 68)
    print("  2. イベント駆動アーキテクチャ (Event-Driven Architecture)")
    print("=" * 68)
    demo_event_sourcing()
    demo_cqrs()
    demo_event_driven()

    # 3. DDD
    print("=" * 68)
    print("  3. DDD (Domain-Driven Design)")
    print("=" * 68)
    demo_ddd()

    # 4. Distributed Systems
    print("=" * 68)
    print("  4. 分散システムパターン (Distributed Systems)")
    print("=" * 68)
    demo_cap_theorem()
    demo_consistent_hashing()
    demo_leader_election()
    demo_distributed_lock()
    demo_two_phase_commit()
    demo_vector_clock()
    demo_gossip_protocol()

    # 5. System Design Interview Problems
    print("=" * 68)
    print("  5. 汎用システム設計問題 (System Design Interview)")
    print("=" * 68)
    demo_url_shortener()
    demo_rate_limiter()
    demo_chat_system()
    demo_news_feed()
    demo_notification_system()

    # 6. Scalability Patterns
    print("=" * 68)
    print("  6. スケーラビリティパターン (Scalability Patterns)")
    print("=" * 68)
    demo_scaling_comparison()
    demo_sharding()
    demo_read_replica()
    demo_cache_strategies()
    demo_cdn()
    demo_back_pressure()

    print("=" * 68)
    print("  Complete! 全パターンの実行が完了しました。")
    print("=" * 68)

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - URL Shortener設計 (ハッシュ, Base62, DB選定)
    - Rate Limiter設計 (Token Bucket, Sliding Window)
    - マイクロサービス基礎 (サービス分割, 通信パターン)
    - API Gateway (認証・ルーティング・負荷分散)

  【Tier 2: 重要 — 実務で頻出】
    - Event Sourcing / CQRS (イベント駆動設計)
    - DDD (Aggregate, Bounded Context, Ubiquitous Language)
    - Circuit Breaker (障害伝搬防止)
    - Sharding (水平分割, パーティションキー選定)

  【Tier 3: 上級 — シニア以上で差がつく】
    - Saga Orchestration (分散トランザクション)
    - Consistent Hashing (ノード追加/削除の影響最小化)
    - Back-pressure (過負荷制御)
    - Gossip Protocol (分散ノード間の情報伝搬)

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Vector Clock実装 (因果関係の追跡)
    - CRDT (Conflict-free Replicated Data Types)
    - Phi Accrual Failure Detector (障害検知)
    - Cell-Based Architecture (障害分離アーキテクチャ)
""")


if __name__ == "__main__":
    main()
