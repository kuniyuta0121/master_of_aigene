#!/usr/bin/env python3
"""
CI/CD & デプロイメントパターン - FAANG レベル完全ガイド
=======================================================
標準ライブラリのみで動作する教材ファイル。
実行: python cicd_patterns.py
"""

import json
import hashlib
import time
import random
import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from collections import defaultdict


def sep(title: str = ""):
    print("\n" + "━" * 60)
    if title:
        print(f"  {title}")
        print("━" * 60)


# ============================================================
# 1. CI/CD パイプライン設計
# ============================================================
sep("1. CI/CD パイプライン設計")

print("""
■ パイプラインの基本ステージ

  ┌──────┐   ┌──────┐   ┌───────┐   ┌────────┐   ┌────────┐
  │ Lint │──▶│ Test │──▶│ Build │──▶│ Deploy │──▶│ Verify │
  └──────┘   └──────┘   └───────┘   │  (Stg)  │   └────────┘
                                     └────────┘
  ※ 各ステージは前段が成功した場合のみ実行される (fail-fast)

■ 並列化の考え方
  - Lint と Unit Test は独立 → 並列実行可能
  - Integration Test は Build 後に実行
  - E2E Test は Deploy(Staging) 後に実行

  ┌─── Lint ──────────┐
  │                    ├──▶ Build ──▶ Deploy(Stg) ──▶ E2E
  └─── Unit Test ─────┘
       ↑ 並列実行

■ キャッシュ戦略
  - 依存関係キャッシュ: pip cache, npm cache, Maven .m2
  - Docker Layer Cache: BuildKit --mount=type=cache
  - テスト結果キャッシュ: 変更ファイルに関連するテストのみ再実行

■ Monorepo vs Polyrepo CI
  ┌─────────────────────────────────────────────────────┐
  │  Monorepo CI                                        │
  │  - 変更検知: git diff で影響範囲を特定              │
  │  - 選択的ビルド: 変更されたパッケージのみ CI 実行   │
  │  - ツール: Bazel, Nx, Turborepo                     │
  │  - 利点: 横断的変更を1PRで、依存関係の一貫性        │
  │  - 課題: CI 時間の増大、権限管理の複雑さ            │
  ├─────────────────────────────────────────────────────┤
  │  Polyrepo CI                                        │
  │  - 各リポジトリが独立した CI パイプラインを持つ      │
  │  - Contract Testing で API 互換性を担保             │
  │  - 利点: 独立したデプロイサイクル                    │
  │  - 課題: 横断的変更が困難、バージョン地獄            │
  └─────────────────────────────────────────────────────┘
""")


class PipelineStage(enum.Enum):
    LINT = "lint"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    BUILD = "build"
    DEPLOY_STAGING = "deploy_staging"
    E2E_TEST = "e2e_test"
    DEPLOY_PROD = "deploy_production"


@dataclass
class StageResult:
    stage: PipelineStage
    success: bool
    duration_ms: int
    cached: bool = False


class CIPipeline:
    """CI パイプラインのシミュレーション"""

    def __init__(self, name: str):
        self.name = name
        self.results: List[StageResult] = []
        self._cache: Dict[str, str] = {}

    def _compute_cache_key(self, stage: PipelineStage, source_hash: str) -> str:
        return hashlib.md5(f"{stage.value}:{source_hash}".encode()).hexdigest()[:8]

    def run_stage(self, stage: PipelineStage, source_hash: str,
                  fail_prob: float = 0.0) -> StageResult:
        cache_key = self._compute_cache_key(stage, source_hash)

        # キャッシュヒット判定
        if cache_key in self._cache:
            result = StageResult(stage=stage, success=True, duration_ms=5, cached=True)
            self.results.append(result)
            return result

        # ステージ実行シミュレーション
        duration = random.randint(500, 3000)
        success = random.random() > fail_prob
        if success:
            self._cache[cache_key] = "passed"

        result = StageResult(stage=stage, success=success, duration_ms=duration)
        self.results.append(result)
        return result

    def run_pipeline(self, source_hash: str) -> bool:
        """fail-fast でパイプライン全体を実行"""
        stages = [
            (PipelineStage.LINT, 0.05),
            (PipelineStage.UNIT_TEST, 0.1),
            (PipelineStage.BUILD, 0.05),
            (PipelineStage.DEPLOY_STAGING, 0.02),
            (PipelineStage.E2E_TEST, 0.15),
        ]
        print(f"  Pipeline [{self.name}] 開始 (hash: {source_hash[:8]})")
        for stage, fail_prob in stages:
            result = self.run_stage(stage, source_hash, fail_prob)
            status = "✓ CACHED" if result.cached else ("✓ PASS" if result.success else "✗ FAIL")
            print(f"    {stage.value:25s} {result.duration_ms:5d}ms  {status}")
            if not result.success:
                print(f"  Pipeline FAILED at {stage.value}")
                return False
        print(f"  Pipeline PASSED")
        return True


# デモ実行
pipeline = CIPipeline("my-service")
pipeline.run_pipeline(hashlib.md5(b"v1-source").hexdigest())
print("\n  2回目 (キャッシュ効果):")
pipeline.run_pipeline(hashlib.md5(b"v1-source").hexdigest())

print("""
  考えてほしい疑問:
  Q: CI パイプラインが15分かかっている。どこから最適化する？
  A: 1) テストの並列化 2) キャッシュ導入 3) 不要なステップ削除
     4) テストの選択的実行 5) より高速なランナー(大きいインスタンス)
""")


# ============================================================
# 2. テスト戦略
# ============================================================
sep("2. テスト戦略 - Test Pyramid & Beyond")

print("""
■ テストピラミッド

            ╱╲
           ╱ E2E ╲          少数・遅い・高コスト・高信頼
          ╱────────╲
         ╱Integration╲      中程度
        ╱──────────────╲
       ╱   Unit Tests    ╲  大量・高速・低コスト
      ╱────────────────────╲

  ※ 逆ピラミッド(E2E 過多)は「アイスクリームコーン」アンチパターン

■ Test Doubles の種類
  ┌──────────┬─────────────────────────────────────────────┐
  │ 種類     │ 説明                                        │
  ├──────────┼─────────────────────────────────────────────┤
  │ Stub     │ 固定値を返す。呼び出し検証なし              │
  │ Mock     │ 呼び出し回数・引数を検証する                │
  │ Fake     │ 簡易実装(InMemoryDB など)                   │
  │ Spy      │ 実オブジェクトをラップし呼び出しを記録      │
  └──────────┴─────────────────────────────────────────────┘
""")


# --- Test Doubles の実装例 ---
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: int, currency: str) -> dict:
        pass


class StubPaymentGateway(PaymentGateway):
    """Stub: 常に成功を返す"""
    def charge(self, amount: int, currency: str) -> dict:
        return {"status": "success", "transaction_id": "stub-txn-001"}


class MockPaymentGateway(PaymentGateway):
    """Mock: 呼び出しを記録し検証可能"""
    def __init__(self):
        self.calls: List[Tuple[int, str]] = []

    def charge(self, amount: int, currency: str) -> dict:
        self.calls.append((amount, currency))
        return {"status": "success", "transaction_id": f"mock-txn-{len(self.calls)}"}

    def assert_called_with(self, amount: int, currency: str):
        assert (amount, currency) in self.calls, f"Expected call ({amount}, {currency}) not found"

    def assert_call_count(self, expected: int):
        assert len(self.calls) == expected, f"Expected {expected} calls, got {len(self.calls)}"


class FakePaymentGateway(PaymentGateway):
    """Fake: 簡易だが動作するロジックを持つ"""
    def __init__(self):
        self.balance: Dict[str, int] = defaultdict(lambda: 100000)
        self.transactions: List[dict] = []

    def charge(self, amount: int, currency: str) -> dict:
        if self.balance[currency] < amount:
            return {"status": "declined", "reason": "insufficient_funds"}
        self.balance[currency] -= amount
        txn = {"id": f"fake-{len(self.transactions)}", "amount": amount}
        self.transactions.append(txn)
        return {"status": "success", "transaction_id": txn["id"]}


# Mock を使ったテスト例
mock_gw = MockPaymentGateway()
mock_gw.charge(1000, "JPY")
mock_gw.charge(2000, "USD")
mock_gw.assert_called_with(1000, "JPY")
mock_gw.assert_call_count(2)
print("  Mock テスト: PASSED (呼び出し回数・引数を検証)")

# Fake を使ったテスト例
fake_gw = FakePaymentGateway()
fake_gw.balance["JPY"] = 500
result = fake_gw.charge(1000, "JPY")
assert result["status"] == "declined"
print("  Fake テスト: PASSED (残高不足で declined)")

print("""
■ Property-Based Testing の考え方
  - 具体的な入力値ではなく「性質(property)」を検証する
  - 例: 「ソート後のリストは元のリストと同じ要素を含む」
  - 例: 「エンコード→デコードすると元に戻る」
  - ツール: Hypothesis (Python), QuickCheck (Haskell), jqwik (Java)

■ Mutation Testing
  - テストコード自体の品質を測定する手法
  - ソースコードに意図的な変異(mutation)を加える
    例: `if x > 0` → `if x >= 0`, `return a + b` → `return a - b`
  - 変異を検出できないテスト = 不十分なテスト
  - ツール: mutmut (Python), PIT (Java), Stryker (JS)

■ Coverage の限界
  - Line coverage 100% でもバグは見つかる
  - 境界値、組み合わせ、並行処理のバグは coverage に現れない
  - Coverage は「テストされていない箇所」を見つけるツール
  - 「テストの質」を測るには Mutation Testing が有効
""")


# ============================================================
# 3. デプロイメント戦略
# ============================================================
sep("3. デプロイメント戦略")

print("""
■ 3-1. Rolling Update
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  段階的にインスタンスを入れ替える

  時刻 T1:  [v1] [v1] [v1] [v1]     ← 全て旧バージョン
  時刻 T2:  [v2] [v1] [v1] [v1]     ← 1台ずつ更新開始
  時刻 T3:  [v2] [v2] [v1] [v1]
  時刻 T4:  [v2] [v2] [v2] [v2]     ← 全て新バージョン

  利点: リソース効率が良い (追加インスタンス不要)
  欠点: 更新中に v1/v2 が混在する (API 互換性が必要)
  K8s: Deployment のデフォルト戦略 (maxSurge, maxUnavailable)

■ 3-2. Blue/Green Deployment
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  2つの環境を用意し、ロードバランサーで切り替え

  ┌─────────┐      ┌────────────────────┐
  │   LB    │─────▶│ Blue  (v1) ← LIVE │
  └─────────┘      └────────────────────┘
                   ┌────────────────────┐
                   │ Green (v2) ← IDLE │  ← デプロイ & テスト
                   └────────────────────┘

  切り替え後:
  ┌─────────┐      ┌────────────────────┐
  │   LB    │      │ Blue  (v1) ← IDLE │  ← ロールバック用に保持
  └─────────┘      └────────────────────┘
       │           ┌────────────────────┐
       └──────────▶│ Green (v2) ← LIVE │
                   └────────────────────┘

  利点: 瞬時の切り替え & ロールバック
  欠点: 2倍のリソースが必要、DB マイグレーション注意

■ 3-3. Canary Deployment
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  少量のトラフィックを新バージョンに流し、段階的に拡大

        ┌──── 95% ────▶ [v1] [v1] [v1] [v1]
  LB ───┤
        └───  5% ────▶ [v2]  ← Canary

  メトリクス監視 → OK なら徐々に拡大:
  Phase 1:  5%  → Canary    (エラー率, レイテンシ監視)
  Phase 2: 25%  → Canary    (ビジネスメトリクス監視)
  Phase 3: 50%  → Canary
  Phase 4: 100% → 全面切替

  利点: リスク最小化、メトリクスベースの判断
  欠点: 複雑なルーティング設定、監視基盤が必須

■ 3-4. Feature Flags
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  デプロイとリリースを分離する

  if feature_flag("new_checkout"):
      return new_checkout_flow()    ← 特定ユーザーのみ
  else:
      return legacy_checkout_flow()

  利点: デプロイ = コードの配置、リリース = 機能の有効化
  欠点: フラグ管理の技術的負債、テスト組み合わせ爆発

■ 3-5. Shadow / Dark Launch
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  本番トラフィックを複製し、新バージョンに流すがレスポンスは返さない

  User ──▶ LB ──▶ [v1] ──▶ Response (ユーザーに返す)
                    │
                    └──▶ [v2] ──▶ (結果を記録するだけ)

  利点: 本番トラフィックで性能・正確性を検証、ユーザー影響ゼロ
  欠点: 副作用(DB書込み, 外部API)の扱いが難しい、2倍の処理負荷
""")


# --- デプロイメント戦略のシミュレーション ---

@dataclass
class Server:
    id: int
    version: str
    healthy: bool = True
    traffic_weight: float = 0.0


class DeploymentStrategy(ABC):
    @abstractmethod
    def deploy(self, servers: List[Server], new_version: str) -> List[Server]:
        pass


class RollingUpdate(DeploymentStrategy):
    def __init__(self, max_unavailable: int = 1):
        self.max_unavailable = max_unavailable

    def deploy(self, servers: List[Server], new_version: str) -> List[Server]:
        print(f"\n  Rolling Update: v{servers[0].version} → v{new_version}")
        total = len(servers)
        for i in range(0, total, self.max_unavailable):
            batch = servers[i:i + self.max_unavailable]
            for s in batch:
                s.version = new_version
            versions = [s.version for s in servers]
            print(f"    Step {i // self.max_unavailable + 1}: {versions}")
        return servers


class BlueGreenDeployment(DeploymentStrategy):
    def deploy(self, servers: List[Server], new_version: str) -> List[Server]:
        print(f"\n  Blue/Green: v{servers[0].version} → v{new_version}")
        blue = servers  # 現在の本番
        green = [Server(id=s.id + 100, version=new_version) for s in servers]
        print(f"    Blue (LIVE): {[s.version for s in blue]}")
        print(f"    Green (IDLE): {[s.version for s in green]}")

        # ヘルスチェック通過後に切り替え
        print(f"    Green ヘルスチェック... OK")
        print(f"    LB 切り替え → Green が LIVE に")
        for s in green:
            s.traffic_weight = 1.0 / len(green)
        return green


class CanaryDeployment(DeploymentStrategy):
    def __init__(self, phases: List[float] = None):
        self.phases = phases or [0.05, 0.25, 0.50, 1.0]

    def deploy(self, servers: List[Server], new_version: str) -> List[Server]:
        print(f"\n  Canary: v{servers[0].version} → v{new_version}")
        canary = Server(id=99, version=new_version)

        for pct in self.phases:
            error_rate = random.uniform(0, 0.02)  # シミュレーション
            latency_p99 = random.uniform(50, 200)
            status = "✓" if error_rate < 0.05 and latency_p99 < 500 else "✗"
            print(f"    Phase {pct*100:5.1f}%: "
                  f"error_rate={error_rate:.3f}, p99={latency_p99:.0f}ms {status}")
            if status == "✗":
                print(f"    Canary FAILED → ロールバック")
                return servers

        print(f"    Canary PROMOTED → 全面切替")
        for s in servers:
            s.version = new_version
        return servers


# デモ
servers = [Server(id=i, version="1.0") for i in range(4)]
RollingUpdate(max_unavailable=1).deploy(servers, "2.0")

servers = [Server(id=i, version="1.0") for i in range(4)]
BlueGreenDeployment().deploy(servers, "2.0")

servers = [Server(id=i, version="1.0") for i in range(4)]
CanaryDeployment().deploy(servers, "2.0")


# --- Feature Flag 実装 ---
sep("3-4. Feature Flags 実装")


class FeatureFlagService:
    """シンプルな Feature Flag サービス"""

    def __init__(self):
        self._flags: Dict[str, dict] = {}

    def register(self, name: str, enabled: bool = False,
                 rollout_pct: float = 0.0,
                 allowed_users: Optional[List[str]] = None):
        self._flags[name] = {
            "enabled": enabled,
            "rollout_pct": rollout_pct,
            "allowed_users": allowed_users or [],
        }

    def is_enabled(self, name: str, user_id: str = "") -> bool:
        flag = self._flags.get(name)
        if not flag or not flag["enabled"]:
            return False
        if user_id in flag["allowed_users"]:
            return True
        # user_id ベースの決定論的ロールアウト
        user_hash = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
        return (user_hash % 100) < (flag["rollout_pct"] * 100)


ff = FeatureFlagService()
ff.register("new_checkout", enabled=True, rollout_pct=0.1, allowed_users=["beta-user-1"])

# テスト
print("  Feature Flag テスト:")
print(f"    beta-user-1:  {ff.is_enabled('new_checkout', 'beta-user-1')}")  # True
print(f"    random-user:  {ff.is_enabled('new_checkout', 'random-user')}")
print(f"    disabled flag: {ff.is_enabled('nonexistent', 'anyone')}")  # False

print("""
  考えてほしい疑問:
  Q: Feature Flag のライフサイクル管理をどうする？
  A: 1) フラグ作成時に有効期限を設定
     2) 全ユーザーにロールアウト完了後、コードからフラグを削除
     3) 定期的な棚卸し (stale flag の検出)
     4) フラグの依存関係を追跡
""")


# ============================================================
# 4. Artifact 管理
# ============================================================
sep("4. Artifact 管理")

print("""
■ Docker イメージ管理のベストプラクティス

  タグ戦略:
  ┌──────────────────────────────────────────────────────┐
  │ ✗ BAD:  myapp:latest            (何が入ってるか不明) │
  │ ✓ GOOD: myapp:1.2.3             (Semantic Version)   │
  │ ✓ GOOD: myapp:1.2.3-abc1234     (+ Git SHA)          │
  │ ✓ BEST: myapp@sha256:deadbeef.. (Immutable Digest)   │
  └──────────────────────────────────────────────────────┘

  Semantic Versioning (SemVer): MAJOR.MINOR.PATCH
  - MAJOR: 後方互換性のない変更
  - MINOR: 後方互換性のある機能追加
  - PATCH: バグ修正

■ 脆弱性スキャン
  - Trivy: Docker イメージ、IaC、依存関係をスキャン
  - Snyk: SBOM (Software Bill of Materials) 生成
  - CI で CRITICAL/HIGH は自動ブロック
""")


@dataclass
class Artifact:
    name: str
    version: str
    git_sha: str
    digest: str = ""
    vulnerabilities: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.digest:
            content = f"{self.name}:{self.version}:{self.git_sha}"
            self.digest = f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:12]}"

    @property
    def full_tag(self) -> str:
        return f"{self.name}:{self.version}-{self.git_sha[:7]}"

    def scan(self) -> bool:
        """脆弱性スキャンのシミュレーション"""
        self.vulnerabilities = {
            "CRITICAL": random.randint(0, 1),
            "HIGH": random.randint(0, 3),
            "MEDIUM": random.randint(0, 10),
            "LOW": random.randint(0, 20),
        }
        return self.vulnerabilities["CRITICAL"] == 0

    def promotion_gate(self) -> Tuple[bool, str]:
        """プロモーションゲート: CRITICAL があればブロック"""
        if not self.vulnerabilities:
            self.scan()
        if self.vulnerabilities.get("CRITICAL", 0) > 0:
            return False, f"BLOCKED: {self.vulnerabilities['CRITICAL']} critical vulnerabilities"
        return True, f"PASSED: {self.full_tag} ({self.digest})"


artifact = Artifact(name="myapp", version="1.2.3", git_sha="abc1234def5678")
passed, msg = artifact.promotion_gate()
print(f"  Artifact: {artifact.full_tag}")
print(f"  Digest:   {artifact.digest}")
print(f"  Scan:     {msg}")
print(f"  Vulns:    {json.dumps(artifact.vulnerabilities)}")


# ============================================================
# 5. Infrastructure as Code パイプライン
# ============================================================
sep("5. Infrastructure as Code パイプライン")

print("""
■ Terraform CI/CD フロー

  PR 作成時:
  ┌──────────┐    ┌───────────────┐    ┌──────────────────┐
  │ PR Push  │──▶│ terraform plan│──▶│ Plan を PR に投稿 │
  └──────────┘    └───────────────┘    └──────────────────┘

  PR マージ時:
  ┌──────────┐    ┌────────────────┐    ┌──────────────────┐
  │ Merge    │──▶│ terraform apply│──▶│ State Lock 解除   │
  └──────────┘    └────────────────┘    └──────────────────┘

■ ドリフト検出
  - 定期的に terraform plan を実行し差分を検出
  - 手動変更 (ClickOps) を検知してアラート
  - 自動修復 or チケット作成

■ State 管理
  - Remote State: S3 + DynamoDB (ロック)
  - State の分割: 環境別、チーム別、ライフサイクル別
  - 機密情報は state に入れない (Vault 連携)

■ セキュリティ
  - tfsec / checkov: IaC の静的解析
  - Sentinel / OPA: Policy as Code
  - 最小権限の原則: apply 用の IAM Role
""")


class TerraformPipeline:
    """Terraform CI/CD のシミュレーション"""

    def __init__(self):
        self.state: Dict[str, dict] = {}  # 現在のインフラ状態
        self.lock_holder: Optional[str] = None

    def plan(self, desired: Dict[str, dict]) -> dict:
        """Plan: 現状と desired の差分を計算"""
        changes = {"add": [], "change": [], "destroy": []}
        for name, config in desired.items():
            if name not in self.state:
                changes["add"].append(name)
            elif self.state[name] != config:
                changes["change"].append(name)
        for name in self.state:
            if name not in desired:
                changes["destroy"].append(name)
        return changes

    def apply(self, desired: Dict[str, dict], run_id: str) -> bool:
        """Apply: State Lock を取得してから適用"""
        if self.lock_holder:
            print(f"    ✗ State ロック中 (holder: {self.lock_holder})")
            return False
        self.lock_holder = run_id
        try:
            plan = self.plan(desired)
            print(f"    Plan: +{len(plan['add'])} ~{len(plan['change'])} -{len(plan['destroy'])}")
            self.state = dict(desired)
            print(f"    Apply: 完了")
            return True
        finally:
            self.lock_holder = None

    def drift_detect(self, actual: Dict[str, dict]) -> List[str]:
        """ドリフト検出: State と実際のインフラの差分"""
        drifted = []
        for name, config in self.state.items():
            if name in actual and actual[name] != config:
                drifted.append(name)
        return drifted


tf = TerraformPipeline()
desired = {
    "aws_instance.web": {"type": "t3.medium", "ami": "ami-123"},
    "aws_rds.db": {"engine": "postgres", "size": "db.r5.large"},
}
print("  Terraform Plan & Apply:")
tf.apply(desired, run_id="ci-run-001")

# ドリフト検出
actual_infra = {
    "aws_instance.web": {"type": "t3.large", "ami": "ami-123"},  # 手動変更!
    "aws_rds.db": {"engine": "postgres", "size": "db.r5.large"},
}
drifted = tf.drift_detect(actual_infra)
print(f"  ドリフト検出: {drifted if drifted else 'なし'}")


# ============================================================
# 6. Database マイグレーション
# ============================================================
sep("6. Database マイグレーション - ゼロダウンタイム")

print("""
■ Forward-Only マイグレーション
  - ロールバック用のマイグレーションは書かない
  - 代わりに「修正マイグレーション」を追加する
  - 理由: データ変換を含むロールバックは危険

■ Expand-and-Contract パターン
  カラム名変更の例: email → email_address

  Phase 1 (Expand): 新カラム追加 + 両方に書き込み
  ┌──────────────────────────────────┐
  │ users                            │
  │ ├── email        (既存, NOT NULL)│
  │ └── email_address (新規, NULL OK)│  ← アプリは両方に書き込む
  └──────────────────────────────────┘

  Phase 2 (Migrate): 既存データを移行
  UPDATE users SET email_address = email WHERE email_address IS NULL;

  Phase 3 (Contract): アプリを新カラムのみ使用に変更
  Phase 4 (Cleanup): 旧カラムを削除

  ※ 各 Phase は独立したデプロイ。Phase 間で安全にロールバック可能

■ ゼロダウンタイム Schema 変更の原則
  - ADD COLUMN: NULL 許容 or DEFAULT 付きなら安全
  - DROP COLUMN: 先にアプリから参照を削除
  - RENAME COLUMN: Expand-and-Contract で対応
  - ADD INDEX: CREATE INDEX CONCURRENTLY (PostgreSQL)
  - 大量データ変更: バッチ処理 + 進捗監視
""")


class MigrationRunner:
    """簡易マイグレーションランナー"""

    def __init__(self):
        self.schema: Dict[str, List[str]] = {}
        self.applied: List[str] = []

    def migrate(self, migration_id: str, up_fn):
        if migration_id in self.applied:
            print(f"    SKIP: {migration_id} (already applied)")
            return
        up_fn(self.schema)
        self.applied.append(migration_id)
        print(f"    APPLIED: {migration_id}")

    def show_schema(self, table: str):
        cols = self.schema.get(table, [])
        print(f"    Schema [{table}]: {cols}")


runner = MigrationRunner()

# Expand-and-Contract パターンのデモ
runner.migrate("001_create_users", lambda s: s.update(
    {"users": ["id", "name", "email"]}))
runner.migrate("002_add_email_address", lambda s: s["users"].append("email_address"))
runner.show_schema("users")
runner.migrate("003_drop_old_email", lambda s: s["users"].remove("email"))
runner.show_schema("users")

print("""
  考えてほしい疑問:
  Q: 1億行のテーブルにインデックスを追加したい。どうする？
  A: 1) CREATE INDEX CONCURRENTLY (ロックを取らない)
     2) メンテナンスウィンドウ外で実行
     3) pg_stat_progress_create_index で進捗監視
     4) レプリカへの影響も考慮
""")


# ============================================================
# 7. シークレット管理
# ============================================================
sep("7. シークレット管理")

print("""
■ シークレット管理の階層

  ┌─────────────────────────────────────────────────┐
  │  Level 1: 環境変数 (基本だが限界あり)            │
  │  - 12-Factor App の原則                          │
  │  - プロセスの env に残る、ログに漏れるリスク     │
  ├─────────────────────────────────────────────────┤
  │  Level 2: シークレットマネージャー               │
  │  - AWS Secrets Manager / GCP Secret Manager     │
  │  - HashiCorp Vault                               │
  │  - アプリが起動時に取得、メモリ上のみ保持        │
  ├─────────────────────────────────────────────────┤
  │  Level 3: 短命クレデンシャル                     │
  │  - Vault Dynamic Secrets (使い捨て DB 認証情報)  │
  │  - AWS STS AssumeRole (一時トークン)             │
  │  - Service Mesh mTLS (自動証明書ローテーション)  │
  └─────────────────────────────────────────────────┘

■ Kubernetes でのシークレット管理
  ✗ K8s Secret (Base64 エンコードのみ、暗号化ではない)
  ✓ Sealed Secrets: 暗号化して Git に保存
  ✓ External Secrets Operator: Vault/AWS SM から同期
  ✓ CSI Secret Store Driver: ボリュームとしてマウント

■ ローテーション戦略
  1. 新旧両方のシークレットを一時的に有効化
  2. アプリを新シークレットに切り替え
  3. 旧シークレットを無効化
  ※ 二重書き込み期間を設けることでダウンタイムを回避
""")


class VaultSimulator:
    """HashiCorp Vault のシミュレーション"""

    def __init__(self):
        self._secrets: Dict[str, dict] = {}
        self._lease: Dict[str, float] = {}
        self._audit_log: List[dict] = []

    def put_secret(self, path: str, data: dict, ttl: int = 3600):
        self._secrets[path] = data
        self._lease[path] = time.time() + ttl
        self._audit(f"PUT {path}")

    def get_secret(self, path: str, accessor: str = "app") -> Optional[dict]:
        self._audit(f"GET {path} by {accessor}")
        if path not in self._secrets:
            return None
        if time.time() > self._lease.get(path, 0):
            self._audit(f"EXPIRED {path}")
            return None
        return self._secrets[path]

    def rotate(self, path: str, new_data: dict):
        """ローテーション: 旧→新の安全な切り替え"""
        old = self._secrets.get(path)
        self._secrets[path] = new_data
        self._lease[path] = time.time() + 3600
        self._audit(f"ROTATE {path}")
        return old

    def _audit(self, action: str):
        self._audit_log.append({"time": time.time(), "action": action})

    def show_audit(self, last_n: int = 5):
        for entry in self._audit_log[-last_n:]:
            print(f"    [AUDIT] {entry['action']}")


vault = VaultSimulator()
vault.put_secret("secret/db/postgres", {"username": "app", "password": "s3cur3!"})
creds = vault.get_secret("secret/db/postgres", accessor="my-service")
print(f"  Vault GET: {creds}")
vault.rotate("secret/db/postgres", {"username": "app", "password": "n3w-p@ss!"})
vault.show_audit()


# ============================================================
# 8. Progressive Delivery
# ============================================================
sep("8. Progressive Delivery")

print("""
■ Progressive Delivery とは
  Canary + 自動分析 + 自動ロールバック = Progressive Delivery

  ツール:
  - Flagger (Kubernetes, Istio/Linkerd 連携)
  - Argo Rollouts (Kubernetes ネイティブ)
  - AWS AppConfig + CloudWatch

■ Argo Rollouts の仕組み

  ┌──────────┐     ┌──────────────┐     ┌──────────────┐
  │ Rollout  │────▶│ Analysis Run │────▶│  Promotion   │
  │ (Canary) │     │ (メトリクス  │     │  or Rollback │
  └──────────┘     │  自動評価)   │     └──────────────┘
                   └──────────────┘
  AnalysisTemplate:
    - Prometheus query: error_rate < 0.01
    - Datadog query: p99_latency < 500ms
    - 一定期間評価して自動判断
""")


@dataclass
class AnalysisMetric:
    name: str
    query: str
    threshold: float
    operator: str  # "<" or ">"


class ProgressiveDeliveryController:
    """Argo Rollouts 風の Progressive Delivery シミュレーション"""

    def __init__(self, metrics: List[AnalysisMetric],
                 phases: List[Tuple[float, int]] = None):
        """
        phases: [(traffic_pct, analysis_duration_sec), ...]
        """
        self.metrics = metrics
        self.phases = phases or [(5, 60), (25, 120), (50, 180), (100, 0)]

    def _evaluate_metric(self, metric: AnalysisMetric) -> Tuple[bool, float]:
        """メトリクス評価のシミュレーション"""
        value = random.uniform(0, metric.threshold * 1.5)
        if metric.operator == "<":
            passed = value < metric.threshold
        else:
            passed = value > metric.threshold
        return passed, value

    def rollout(self, version: str) -> bool:
        print(f"\n  Progressive Delivery: v{version}")
        for pct, duration in self.phases:
            print(f"\n    Phase: {pct}% traffic (analysis: {duration}s)")
            all_passed = True
            for metric in self.metrics:
                passed, value = self._evaluate_metric(metric)
                status = "✓" if passed else "✗"
                print(f"      {metric.name}: {value:.4f} "
                      f"(threshold {metric.operator} {metric.threshold}) {status}")
                if not passed:
                    all_passed = False

            if not all_passed:
                print(f"\n    ✗ Analysis FAILED → 自動ロールバック")
                return False
            print(f"    ✓ Analysis PASSED → 次の Phase へ")

        print(f"\n    全 Phase 完了 → v{version} を全面展開")
        return True


pd_controller = ProgressiveDeliveryController(
    metrics=[
        AnalysisMetric("error_rate", "rate(http_errors[5m])", 0.01, "<"),
        AnalysisMetric("p99_latency", "histogram_quantile(0.99, ...)", 500.0, "<"),
        AnalysisMetric("success_rate", "rate(http_success[5m])", 0.95, ">"),
    ]
)
pd_controller.rollout("2.1.0")


# ============================================================
# 9. ML パイプライン CI/CD
# ============================================================
sep("9. ML パイプライン CI/CD")

print("""
■ ML CI/CD は通常の CI/CD + データ & モデルの管理

  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ データ   │──▶│ Training │──▶│ 評価 &   │──▶│ Registry │
  │ 検証     │    │          │    │ Validation│    │ 登録     │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                       │
                                                       ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ Monitor  │◀──│ A/B Test │◀──│ Canary   │◀──│ Staging  │
  │ (Drift)  │    │          │    │ Deploy   │    │ Deploy   │
  └──────────┘    └──────────┘    └──────────┘    └──────────┘

■ コードの CI/CD との違い
  ┌─────────────────────┬───────────────────────────────────┐
  │ 通常のアプリ        │ ML パイプライン                    │
  ├─────────────────────┼───────────────────────────────────┤
  │ コードの変更で CI   │ コード + データ + パラメータの変更 │
  │ バイナリ Artifact   │ モデル Artifact + メタデータ       │
  │ A/B テスト (任意)   │ A/B テスト (必須に近い)            │
  │ メトリクス: latency │ メトリクス: accuracy, drift, bias │
  │ ロールバック: 即座  │ ロールバック: 前モデルに切替       │
  └─────────────────────┴───────────────────────────────────┘
""")


@dataclass
class MLModel:
    name: str
    version: str
    accuracy: float
    latency_ms: float
    training_data_hash: str
    stage: str = "staging"  # staging → canary → production → archived


class MLModelRegistry:
    """ML Model Registry のシミュレーション"""

    def __init__(self):
        self.models: Dict[str, List[MLModel]] = defaultdict(list)

    def register(self, model: MLModel):
        self.models[model.name].append(model)
        print(f"    Registered: {model.name} v{model.version} "
              f"(accuracy={model.accuracy:.3f}, stage={model.stage})")

    def promote(self, name: str, version: str, target_stage: str) -> bool:
        for m in self.models.get(name, []):
            if m.version == version:
                old_stage = m.stage
                m.stage = target_stage
                print(f"    Promoted: {name} v{version} {old_stage} → {target_stage}")
                return True
        return False

    def get_production_model(self, name: str) -> Optional[MLModel]:
        for m in self.models.get(name, []):
            if m.stage == "production":
                return m
        return None

    def ab_test(self, name: str, challenger_version: str,
                traffic_split: float = 0.1) -> dict:
        """A/B テストのシミュレーション"""
        champion = self.get_production_model(name)
        challenger = None
        for m in self.models.get(name, []):
            if m.version == challenger_version:
                challenger = m
                break

        if not champion or not challenger:
            return {"error": "Model not found"}

        results = {
            "champion": {"version": champion.version, "accuracy": champion.accuracy},
            "challenger": {"version": challenger.version, "accuracy": challenger.accuracy},
            "traffic_split": f"{(1-traffic_split)*100:.0f}/{traffic_split*100:.0f}",
            "winner": challenger.version if challenger.accuracy > champion.accuracy
                      else champion.version,
        }
        return results


registry = MLModelRegistry()
registry.register(MLModel("fraud-detector", "1.0", 0.92, 15.0, "data-hash-v1"))
registry.promote("fraud-detector", "1.0", "production")
registry.register(MLModel("fraud-detector", "1.1", 0.95, 18.0, "data-hash-v2"))

ab_result = registry.ab_test("fraud-detector", "1.1", traffic_split=0.1)
print(f"    A/B Test: {json.dumps(ab_result, indent=6)}")


# ============================================================
# 10. 面接問題: Design CI/CD for 1M req/sec Service
# ============================================================
sep("10. 面接問題: 1M req/sec サービスの CI/CD 設計")

print("""
■ 問題: 1M requests/sec を処理するサービスの CI/CD を設計せよ

  ステップ 1: 要件の明確化
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - SLA: 99.99% (年間ダウンタイム ~52分)
  - デプロイ頻度: 日に複数回
  - リージョン: マルチリージョン (US, EU, AP)
  - ロールバック: 5分以内

  ステップ 2: パイプライン設計
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PR → Lint/Test → Build → Staging → Canary (1%) → Regional
  Rollout (10%/25%/50%/100%) → Post-Deploy Verification

  ┌────────────────────────────────────────────────────────┐
  │ Stage 1: Pre-merge (PR)                                │
  │ ├── Static Analysis (lint, type check)     [並列]      │
  │ ├── Unit Tests (pytest, 高速)              [並列]      │
  │ ├── Integration Tests (TestContainers)     [並列]      │
  │ └── Security Scan (SAST, dependency)       [並列]      │
  ├────────────────────────────────────────────────────────┤
  │ Stage 2: Post-merge (main branch)                      │
  │ ├── Build Docker Image (BuildKit, layer cache)         │
  │ ├── Push to ECR (immutable tag: v1.2.3-abc1234)        │
  │ ├── Vulnerability Scan (Trivy)                         │
  │ └── Deploy to Staging                                  │
  ├────────────────────────────────────────────────────────┤
  │ Stage 3: Staging Verification                          │
  │ ├── E2E Tests                                          │
  │ ├── Performance Tests (k6/Locust, baseline 比較)       │
  │ ├── Chaos Tests (Litmus, abort on failure)             │
  │ └── Approval Gate (自動 or 手動)                       │
  ├────────────────────────────────────────────────────────┤
  │ Stage 4: Production Rollout (Progressive)              │
  │ ├── Canary 1% (5分間メトリクス分析)                    │
  │ ├── Region 1: 10% → 25% → 50% → 100%                 │
  │ ├── Region 2: 同様に段階展開                           │
  │ ├── Region 3: 同様に段階展開                           │
  │ └── 各段階で自動ロールバック判定                       │
  └────────────────────────────────────────────────────────┘

  ステップ 3: ロールバック戦略
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - 自動ロールバックトリガー:
    1) Error rate > 0.1% (baseline + 2σ)
    2) P99 latency > 500ms
    3) Success rate < 99.9%
  - ロールバック手段:
    1) Canary 中: 即座にトラフィック切り戻し (< 1分)
    2) 全面展開後: 前バージョンの Deployment にロールバック (< 3分)
    3) DB マイグレーション: Forward-only (expand-and-contract)

  ステップ 4: 監視 & アラート
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - デプロイ時の監視ダッシュボード (Grafana)
  - Golden Signals: Latency, Traffic, Errors, Saturation
  - デプロイイベントのアノテーション
  - PagerDuty 連携 (自動ロールバック失敗時)

  ステップ 5: スケールへの対応
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - 1M req/sec → 各リージョン ~333K req/sec
  - Canary 1% でも ~3,300 req/sec (統計的有意性を確保)
  - 段階展開により blast radius を制限
  - Feature Flag で機能単位のロールバックも可能

  ステップ 6: 補足 (差別化ポイント)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Build 再現性: Hermetic Build (Bazel)
  - Supply Chain Security: SLSA Level 3, Sigstore で署名
  - Deployment Freeze: 金曜夜・祝日前は自動ブロック
  - Rollout Window: 各リージョンのピーク時間を避ける
  - Post-Deploy Soak Test: 24時間メトリクス監視

  考えてほしい疑問:
  Q: Canary で「統計的に有意な差」をどう判断する？
  A: 1) 十分なサンプルサイズ (最低数千リクエスト)
     2) χ² 検定 or ベイズ推定でエラー率を比較
     3) 偽陽性を減らすため複数メトリクスを総合判断
     4) Canary 期間を短くしすぎない (最低5分)
""")


# ============================================================
# まとめ & 実装課題
# ============================================================
sep("まとめ & 実装課題")

print("""
■ CI/CD 設計の原則
  1. Fail Fast: 問題を早期に発見 (左にシフト)
  2. Immutable Artifacts: ビルドしたものをそのままデプロイ
  3. Progressive Delivery: 段階的にリスクを減らす
  4. Automated Rollback: 人間の判断を待たない
  5. Everything as Code: パイプライン, インフラ, ポリシー

■ [実装してみよう] 課題一覧

  課題 1 (初級): GitHub Actions のワークフロー
  ──────────────────────────────────────────
  - Python プロジェクト用の CI を作成
  - Lint (flake8) → Test (pytest) → Build (Docker) の3ステージ
  - PR 時は Lint + Test のみ、main merge 時は Build も実行

  課題 2 (中級): Canary デプロイメントコントローラー
  ──────────────────────────────────────────
  - K8s Deployment を2つ作成 (stable / canary)
  - Istio VirtualService でトラフィック分割
  - Prometheus メトリクスで自動判定
  - 失敗時の自動ロールバック

  課題 3 (上級): ML モデルの CI/CD パイプライン
  ──────────────────────────────────────────
  - データ検証 (Great Expectations)
  - モデル学習 + ハイパーパラメータ記録 (MLflow)
  - 精度が baseline を超えたら Model Registry に登録
  - Shadow Deploy で本番トラフィックと比較
  - A/B テストで統計的有意差を確認後プロモート

  課題 4 (上級): ゼロダウンタイム DB マイグレーション
  ──────────────────────────────────────────
  - 大規模テーブル (1億行) のスキーマ変更を設計
  - Expand-and-Contract パターンで実装
  - 各 Phase のロールバック手順を文書化
  - バッチ処理のモニタリング (進捗%, ETA)

  課題 5 (面接対策): システム設計
  ──────────────────────────────────────────
  - 上記「1M req/sec サービスの CI/CD 設計」を
    ホワイトボードに描けるレベルで練習
  - 各デプロイ戦略の trade-off を説明できるように
  - 「なぜその戦略を選んだか」を論理的に説明
""")

sep("END")
print("  実行完了: CI/CD & デプロイメントパターン")
print("  次のステップ: phase5_cloud/ でクラウドアーキテクチャを学習")
print("━" * 60)

print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - テストピラミッド
    - GitHub Actions基礎
    - Rolling Deploy
    - 基本CI パイプライン

  【Tier 2: 重要 — 実務で頻出】
    - Blue/Green Deploy
    - Canary Deploy
    - DB マイグレーション戦略
    - シークレット管理

  【Tier 3: 上級 — シニア以上で差がつく】
    - Feature Flags
    - Progressive Delivery
    - ML CI/CD
    - テスト並列化

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Shadow Deploy
    - GitOps(ArgoCD)
    - Trunk-Based Development
    - カスタムランナー
""")
