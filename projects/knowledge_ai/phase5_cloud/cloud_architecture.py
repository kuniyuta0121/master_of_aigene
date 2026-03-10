"""
Cloud Architecture Patterns - FAANG Level
==========================================
AWS Well-Architected Framework, マルチリージョン設計、サーバーレス、
イベント駆動、コスト最適化、災害復旧を体系的に学ぶ。

実行: python cloud_architecture.py
依存: 標準ライブラリのみ
"""

import json
import time
import random
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


def print_section(title: str) -> None:
    print("\n" + "━" * 60)
    print(f"  {title}")
    print("━" * 60)


def print_subsection(title: str) -> None:
    print(f"\n--- {title} ---")


def print_question(q: str) -> None:
    print(f"\n  [考えてほしい疑問] {q}")


def print_task(t: str) -> None:
    print(f"\n  [実装してみよう] {t}")


# ============================================================
# 1. AWS Well-Architected Framework - 6 Pillars
# ============================================================

class Pillar(Enum):
    OPERATIONAL_EXCELLENCE = "運用上の優秀性"
    SECURITY = "セキュリティ"
    RELIABILITY = "信頼性"
    PERFORMANCE_EFFICIENCY = "パフォーマンス効率"
    COST_OPTIMIZATION = "コスト最適化"
    SUSTAINABILITY = "持続可能性"


@dataclass
class WellArchitectedPillar:
    """Well-Architected Framework の各柱を表現"""
    pillar: Pillar
    design_principles: List[str]
    key_services: List[str]
    anti_patterns: List[str]

    def evaluate(self, score: int) -> str:
        """0-100のスコアで評価"""
        if score >= 80:
            return f"[優] {self.pillar.value}: 十分に最適化されています"
        elif score >= 50:
            return f"[良] {self.pillar.value}: 改善の余地があります"
        else:
            return f"[要改善] {self.pillar.value}: 重大なリスクがあります"


def demo_well_architected():
    print_section("1. AWS Well-Architected Framework - 6つの柱")

    pillars = {
        Pillar.OPERATIONAL_EXCELLENCE: WellArchitectedPillar(
            pillar=Pillar.OPERATIONAL_EXCELLENCE,
            design_principles=[
                "Operations as Code (IaCで運用を自動化)",
                "小さく頻繁に可逆的な変更を行う",
                "運用手順を頻繁に改善する",
                "障害を予測する (Game Day演習)",
                "すべての運用イベントから学ぶ",
            ],
            key_services=["CloudFormation", "AWS Config", "CloudWatch", "Systems Manager"],
            anti_patterns=["手動デプロイ", "ドキュメントなし", "障害時の場当たり対応"],
        ),
        Pillar.SECURITY: WellArchitectedPillar(
            pillar=Pillar.SECURITY,
            design_principles=[
                "強力なアイデンティティ基盤の実装",
                "トレーサビリティの確保",
                "全レイヤーでセキュリティを適用",
                "セキュリティのベストプラクティスを自動化",
                "転送中・保管中のデータを保護",
                "最小権限の原則",
            ],
            key_services=["IAM", "KMS", "WAF", "GuardDuty", "Security Hub"],
            anti_patterns=["ルートアカウント常用", "ハードコードされた認証情報", "暗号化なし"],
        ),
        Pillar.RELIABILITY: WellArchitectedPillar(
            pillar=Pillar.RELIABILITY,
            design_principles=[
                "障害から自動的に復旧する",
                "リカバリ手順をテストする",
                "水平スケーリングで可用性を向上",
                "キャパシティの推測をやめる",
                "自動化による変更管理",
            ],
            key_services=["Route53", "ELB", "Auto Scaling", "CloudWatch", "S3"],
            anti_patterns=["単一AZ構成", "バックアップなし", "自動復旧メカニズムなし"],
        ),
        Pillar.PERFORMANCE_EFFICIENCY: WellArchitectedPillar(
            pillar=Pillar.PERFORMANCE_EFFICIENCY,
            design_principles=[
                "先端技術の民主化 (マネージドサービス活用)",
                "数分でグローバル展開",
                "サーバーレスアーキテクチャを使用",
                "より頻繁に実験する",
                "技術への共感 (Mechanical Sympathy)",
            ],
            key_services=["Auto Scaling", "ElastiCache", "CloudFront", "Lambda"],
            anti_patterns=["過剰プロビジョニング", "キャッシュなし", "不適切なインスタンスタイプ"],
        ),
        Pillar.COST_OPTIMIZATION: WellArchitectedPillar(
            pillar=Pillar.COST_OPTIMIZATION,
            design_principles=[
                "クラウド財務管理を実践",
                "消費モデルを採用 (使った分だけ)",
                "全体的な効率を測定",
                "差別化につながらない作業への支出をやめる",
                "支出を分析し帰属させる",
            ],
            key_services=["Cost Explorer", "Budgets", "Trusted Advisor", "Savings Plans"],
            anti_patterns=["オンデマンドのみ", "未使用リソース放置", "コストタグなし"],
        ),
        Pillar.SUSTAINABILITY: WellArchitectedPillar(
            pillar=Pillar.SUSTAINABILITY,
            design_principles=[
                "影響を理解する",
                "持続可能性の目標を設定する",
                "利用率を最大化する",
                "より効率的な新しいハードウェアを採用",
                "マネージドサービスを使用する",
                "ダウンストリームの影響を軽減する",
            ],
            key_services=["Graviton", "Auto Scaling", "S3 Intelligent-Tiering"],
            anti_patterns=["過剰プロビジョニング", "非効率なコード", "不要データの保持"],
        ),
    }

    print("""
    AWS Well-Architected Framework は、クラウドアーキテクチャを
    評価・改善するための6つの柱からなるフレームワークです。

    ┌─────────────────────────────────────────────┐
    │        Well-Architected Framework            │
    │                                              │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
    │  │ 運用優秀性│ │セキュリティ│ │  信頼性  │     │
    │  └──────────┘ └──────────┘ └──────────┘     │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
    │  │パフォーマンス│ │コスト最適化│ │持続可能性│     │
    │  └──────────┘ └──────────┘ └──────────┘     │
    └─────────────────────────────────────────────┘
    """)

    for pillar_enum, pillar_obj in pillars.items():
        print(f"\n  ■ {pillar_obj.pillar.value}")
        print(f"    設計原則:")
        for p in pillar_obj.design_principles[:3]:
            print(f"      - {p}")
        print(f"    主要サービス: {', '.join(pillar_obj.key_services)}")
        print(f"    アンチパターン: {', '.join(pillar_obj.anti_patterns)}")

    # シミュレーション: スコア評価
    print_subsection("Well-Architected Review シミュレーション")
    sample_scores = {
        Pillar.OPERATIONAL_EXCELLENCE: 72,
        Pillar.SECURITY: 85,
        Pillar.RELIABILITY: 60,
        Pillar.PERFORMANCE_EFFICIENCY: 78,
        Pillar.COST_OPTIMIZATION: 45,
        Pillar.SUSTAINABILITY: 55,
    }
    for pillar_enum, score in sample_scores.items():
        result = pillars[pillar_enum].evaluate(score)
        print(f"    {result} (スコア: {score})")

    print_question(
        "セキュリティと信頼性はトレードオフになることがある。\n"
        "    例: 厳格なアクセス制御 vs 障害時の迅速な復旧。どう両立させるか？"
    )


# ============================================================
# 2. マルチAZ / マルチリージョン設計
# ============================================================

class RoutingPolicy(Enum):
    SIMPLE = "Simple Routing"
    WEIGHTED = "Weighted Routing"
    LATENCY = "Latency-Based Routing"
    FAILOVER = "Failover Routing"
    GEOLOCATION = "Geolocation Routing"
    GEOPROXIMITY = "Geoproximity Routing"
    MULTIVALUE = "Multi-Value Answer Routing"


@dataclass
class Region:
    name: str
    azs: List[str]
    is_primary: bool = False
    replication_lag_ms: float = 0.0


@dataclass
class MultiRegionDesign:
    """マルチリージョン設計のモデル"""
    regions: List[Region]
    pattern: str  # "active-active" or "active-passive"
    routing_policy: RoutingPolicy
    data_replication: str  # "sync" or "async"

    def failover_simulation(self) -> List[str]:
        events = []
        primary = next((r for r in self.regions if r.is_primary), None)
        if not primary:
            return ["ERROR: プライマリリージョンが見つかりません"]

        events.append(f"[障害検知] {primary.name} でヘルスチェック失敗")
        events.append(f"[DNS更新] Route53 が {self.routing_policy.value} に基づきフェイルオーバー")

        secondary = next((r for r in self.regions if not r.is_primary), None)
        if secondary:
            events.append(f"[切替先] {secondary.name} がトラフィックを受信開始")
            if self.data_replication == "async":
                events.append(
                    f"[警告] 非同期レプリケーション: 最大 {secondary.replication_lag_ms}ms のデータ損失の可能性"
                )
            elif self.data_replication == "sync":
                events.append("[確認] 同期レプリケーション: データ損失なし (ただしレイテンシコストあり)")

        if self.pattern == "active-active":
            events.append("[復旧] 他リージョンが既にトラフィック処理中のため影響最小")
        else:
            events.append("[復旧] Warm Standby からのスケールアップが必要 (数分)")
        return events


def demo_multi_region():
    print_section("2. マルチAZ / マルチリージョン設計")

    print("""
    ■ Active-Active vs Active-Passive

    【Active-Active】
    ┌─────────┐    Route53     ┌─────────┐
    │us-east-1│◄──(Latency)──►│eu-west-1│
    │ [R/W]   │                │  [R/W]  │
    │ App+DB  │◄──Replication─►│ App+DB  │
    └─────────┘                └─────────┘
    - 両リージョンがリクエストを処理
    - Global Accelerator / CloudFront 併用
    - 書き込み競合の解決が課題 (Last Writer Wins, CRDTs)

    【Active-Passive】
    ┌─────────┐    Route53     ┌─────────┐
    │us-east-1│◄─(Failover)──►│us-west-2│
    │ [R/W]   │                │[Standby]│
    │ Primary │───Replication──►│Secondary│
    └─────────┘                └─────────┘
    - 障害時のみセカンダリがアクティブに
    - RPOは非同期レプリケーションのラグに依存
    """)

    # Route53 ルーティングポリシーの解説
    print_subsection("Route53 ルーティングポリシー")
    policies = [
        ("Simple", "1つのリソースへルーティング", "単純なWebサイト"),
        ("Weighted", "重み付けで複数リソースに分散", "Blue/Greenデプロイ, A/Bテスト"),
        ("Latency", "最もレイテンシの低いリージョンへ", "グローバルアプリケーション"),
        ("Failover", "プライマリ障害時にセカンダリへ", "DR構成"),
        ("Geolocation", "ユーザーの地理的位置で決定", "コンテンツのローカライズ"),
        ("Geoproximity", "リソースとの地理的近接性+バイアス", "トラフィックシフト"),
        ("Multi-Value", "複数の正常なリソースからランダム", "簡易ロードバランシング"),
    ]
    print(f"    {'ポリシー':<16} {'説明':<32} {'ユースケース'}")
    print("    " + "-" * 80)
    for name, desc, usecase in policies:
        print(f"    {name:<16} {desc:<32} {usecase}")

    # フェイルオーバーシミュレーション
    print_subsection("フェイルオーバーシミュレーション")
    design = MultiRegionDesign(
        regions=[
            Region("us-east-1", ["us-east-1a", "us-east-1b", "us-east-1c"], is_primary=True),
            Region("eu-west-1", ["eu-west-1a", "eu-west-1b"], replication_lag_ms=150),
        ],
        pattern="active-passive",
        routing_policy=RoutingPolicy.FAILOVER,
        data_replication="async",
    )
    events = design.failover_simulation()
    for e in events:
        print(f"    {e}")

    # データレプリケーションパターン
    print_subsection("データレプリケーションパターン")
    print("""
    1. 同期レプリケーション (Aurora Global Database - write forwarding)
       - RPO = 0 (データ損失なし)
       - レイテンシ増加 (リージョン間RTT追加)
       - 適用: 金融取引など一貫性が最重要

    2. 非同期レプリケーション (DynamoDB Global Tables)
       - RPO > 0 (レプリケーションラグ分のデータ損失)
       - 書き込みレイテンシへの影響なし
       - 適用: 大多数のアプリケーション

    3. イベントソーシング + CQRS
       - イベントストアへの書き込みは単一リージョン
       - リードレプリカは各リージョンで独立構築
       - 結果整合性を許容するデザイン
    """)

    print_question(
        "DynamoDB Global Tables は Last Writer Wins で競合解決する。\n"
        "    同じレコードが同時に2リージョンで更新された場合、\n"
        "    ビジネスロジック的にどう対処すべきか？"
    )


# ============================================================
# 3. サーバーレスアーキテクチャ
# ============================================================

@dataclass
class LambdaFunction:
    name: str
    memory_mb: int
    timeout_sec: int
    runtime: str
    cold_start_ms: float = 0.0
    provisioned_concurrency: int = 0

    def estimate_cold_start(self) -> float:
        """Cold start の推定時間を計算"""
        base = {"python3.12": 200, "nodejs20.x": 180, "java21": 800, "dotnet8": 600}
        base_ms = base.get(self.runtime, 300)
        memory_factor = 1.0 - (self.memory_mb - 128) / 10240 * 0.5
        self.cold_start_ms = base_ms * max(memory_factor, 0.3)
        return self.cold_start_ms

    def monthly_cost(self, invocations: int, avg_duration_ms: float) -> float:
        """月額コスト概算 (USD)"""
        gb_seconds = (self.memory_mb / 1024) * (avg_duration_ms / 1000) * invocations
        # 最初の100万リクエストと400,000 GB-sは無料
        request_cost = max(0, invocations - 1_000_000) * 0.0000002
        compute_cost = max(0, gb_seconds - 400_000) * 0.0000166667
        return request_cost + compute_cost


@dataclass
class StepFunctionWorkflow:
    """Step Functions ワークフローのシミュレーション"""
    name: str
    steps: List[Dict]

    def execute(self) -> List[str]:
        log = [f"[Start] ワークフロー '{self.name}' 開始"]
        for step in self.steps:
            step_type = step.get("type", "Task")
            step_name = step.get("name", "unnamed")
            if step_type == "Task":
                log.append(f"  [Task] {step_name} 実行中...")
            elif step_type == "Choice":
                log.append(f"  [Choice] {step_name} 条件分岐")
                chosen = step.get("default", "FallbackPath")
                log.append(f"    -> {chosen} を選択")
            elif step_type == "Parallel":
                branches = step.get("branches", [])
                log.append(f"  [Parallel] {len(branches)} ブランチを並列実行")
                for b in branches:
                    log.append(f"    - {b} 完了")
            elif step_type == "Wait":
                log.append(f"  [Wait] {step.get('seconds', 0)}秒待機")
            elif step_type == "Catch":
                log.append(f"  [Catch] エラーハンドリング: {step_name}")
        log.append(f"[End] ワークフロー '{self.name}' 完了")
        return log


def demo_serverless():
    print_section("3. サーバーレスアーキテクチャ")

    print("""
    ■ 典型的なサーバーレス構成

    ┌────────┐   ┌───────────┐   ┌────────┐   ┌──────────┐
    │ Client │──►│API Gateway│──►│ Lambda │──►│ DynamoDB │
    └────────┘   └───────────┘   └────────┘   └──────────┘
                       │              │
                       │              ├──►┌─────┐
                       │              │   │ SQS │──►Lambda (非同期)
                       │              │   └─────┘
                       │              │
                       │              └──►┌─────┐
                       │                  │ SNS │──►複数Subscriber
                       │                  └─────┘
                       │
                  ┌─────────────┐
                  │Lambda@Edge  │  (CloudFront)
                  │- A/Bテスト   │
                  │- 認証        │
                  │- URLリライト │
                  └─────────────┘
    """)

    # Cold Start 比較
    print_subsection("Cold Start 最適化")
    runtimes = ["python3.12", "nodejs20.x", "java21", "dotnet8"]
    memories = [128, 512, 1024, 3008]

    print(f"    {'Runtime':<14} {'Memory(MB)':<12} {'推定Cold Start(ms)':<20}")
    print("    " + "-" * 50)
    for rt in runtimes:
        fn = LambdaFunction(name="test", memory_mb=512, timeout_sec=30, runtime=rt)
        cs = fn.estimate_cold_start()
        print(f"    {rt:<14} {512:<12} {cs:<20.0f}")

    print("""
    Cold Start 削減テクニック:
      1. Provisioned Concurrency  - 事前にインスタンスをウォーム
      2. SnapStart (Java)         - スナップショットからの高速起動
      3. メモリ増加               - CPU比例で全体高速化
      4. 軽量ランタイム           - Python/Node > Java/C#
      5. レイヤーの最適化         - 不要な依存を削除
      6. init処理の最小化         - グローバル変数の遅延初期化
    """)

    # コスト計算
    print_subsection("Lambda コスト計算")
    fn = LambdaFunction(name="api-handler", memory_mb=256, timeout_sec=10, runtime="python3.12")
    scenarios = [
        (100_000, 100, "小規模API"),
        (10_000_000, 200, "中規模API"),
        (100_000_000, 150, "大規模API"),
    ]
    for invocations, duration, label in scenarios:
        cost = fn.monthly_cost(invocations, duration)
        print(f"    {label}: {invocations:>12,} req/月, {duration}ms平均 => ${cost:>8.2f}/月")

    # Step Functions
    print_subsection("Step Functions ワークフロー例: 画像処理パイプライン")
    workflow = StepFunctionWorkflow(
        name="image-processing",
        steps=[
            {"type": "Task", "name": "画像アップロード検証"},
            {"type": "Choice", "name": "ファイルサイズチェック", "default": "リサイズパス"},
            {"type": "Parallel", "name": "並列処理", "branches": ["サムネイル生成", "メタデータ抽出", "ウイルススキャン"]},
            {"type": "Task", "name": "DynamoDBにメタデータ保存"},
            {"type": "Task", "name": "SNS通知送信"},
            {"type": "Catch", "name": "DLQへエラー送信"},
        ],
    )
    for line in workflow.execute():
        print(f"    {line}")

    print_question(
        "API Gateway + Lambda で p99 レイテンシが 3秒を超えた。\n"
        "    Cold Start 以外に考えられるボトルネックは何か？"
    )


# ============================================================
# 4. コンテナ vs サーバーレス vs VM
# ============================================================

def demo_compute_comparison():
    print_section("4. コンテナ vs サーバーレス vs VM 意思決定マトリクス")

    print("""
    ■ 比較マトリクス

    ┌──────────────┬────────────┬──────────────┬────────────┐
    │ 観点          │ VM (EC2)   │ Container    │ Serverless │
    │              │            │ (ECS/EKS)    │ (Lambda)   │
    ├──────────────┼────────────┼──────────────┼────────────┤
    │ 起動時間      │ 数分       │ 数秒〜数十秒  │ 数百ms     │
    │ スケーリング  │ 分単位     │ 秒〜分単位    │ ミリ秒     │
    │ 最大実行時間  │ 無制限     │ 無制限        │ 15分       │
    │ 制御粒度      │ OS〜全て   │ コンテナ〜    │ コードのみ │
    │ 運用負荷      │ 高         │ 中            │ 低         │
    │ コスト(低負荷)│ 高         │ 中            │ 極めて低   │
    │ コスト(高負荷)│ 低〜中     │ 低〜中        │ 高くなる   │
    │ ステートフル  │ 可能       │ 条件付き可能  │ 不可       │
    │ GPU対応       │ 可能       │ 可能          │ 不可       │
    │ VPC制約       │ なし       │ なし          │ Cold Start増│
    └──────────────┴────────────┴──────────────┴────────────┘

    ■ 判断フローチャート

    処理時間 > 15分?
     ├─ Yes → コンテナ or VM
     │         └─ GPUが必要? → Yes → VM (p/g系インスタンス)
     │                        → No  → ECS Fargate
     └─ No  → リクエスト頻度は?
              ├─ 散発的 (< 1 req/sec) → Lambda (コスト最小)
              ├─ 中程度 → Lambda + Provisioned Concurrency
              └─ 高頻度 (> 1000 QPS) → ECS/EKS (コスト効率)

    ■ ECS vs EKS の選択

    ECS Fargate:
      - AWSネイティブ、シンプル
      - Task Definition ベース
      - AWS統合が容易 (ALB, CloudWatch, IAM)

    EKS:
      - Kubernetes標準、ポータビリティ
      - 豊富なエコシステム (Helm, Istio, ArgoCD)
      - マルチクラウド/ハイブリッドに有利
      - 学習コスト・運用コスト高い
    """)

    # コスト比較シミュレーション
    print_subsection("月額コスト比較 (100万リクエスト/月, 平均200ms)")

    scenarios = {
        "EC2 t3.medium (常時稼働)": 30.37,
        "EC2 t3.medium (Reserved 1yr)": 19.27,
        "ECS Fargate (0.25vCPU, 512MB)": 9.47,
        "Lambda (512MB, 200ms)": 2.10,
    }
    for name, cost in scenarios.items():
        bar = "█" * int(cost)
        print(f"    {name:<38} ${cost:>6.2f}  {bar}")

    print("""
    ※ Lambdaはリクエスト数が増えると逆転する:
       1億リクエスト/月: Lambda $210 vs Fargate $9.47 + スケーリング費用
       → 高トラフィックではコンテナの方がコスト効率が良い
    """)

    print_question(
        "マイクロサービスを10個運用する場合、\n"
        "    全部Lambdaにするか、全部ECSにするか、混在させるか。\n"
        "    それぞれのトレードオフは？"
    )


# ============================================================
# 5. データベース選択
# ============================================================

@dataclass
class DatabaseOption:
    name: str
    db_type: str
    max_storage: str
    max_throughput: str
    latency: str
    cost_model: str
    best_for: List[str]


def demo_database_selection():
    print_section("5. データベース選択 - Decision Tree")

    databases = [
        DatabaseOption("RDS (MySQL/PostgreSQL)", "Relational", "64TB", "高(スケールアップ)",
                       "数ms", "インスタンス時間", ["OLTP", "複雑なJOIN", "ACID必須"]),
        DatabaseOption("Aurora", "Relational", "128TB", "非常に高", "< 5ms",
                       "インスタンス+IO", ["大規模OLTP", "読取レプリカ15台", "Global Database"]),
        DatabaseOption("Aurora Serverless v2", "Relational", "128TB", "自動スケール",
                       "< 10ms", "ACU秒", ["可変負荷のRDB", "開発/テスト環境"]),
        DatabaseOption("DynamoDB", "Key-Value/Doc", "無制限", "無制限(水平)", "< 10ms",
                       "RCU/WCU or On-Demand", ["高スループット", "予測可能なアクセスパターン"]),
        DatabaseOption("ElastiCache Redis", "In-Memory", "数百GB", "超高速", "< 1ms",
                       "ノード時間", ["セッション管理", "キャッシュ", "リーダーボード"]),
        DatabaseOption("Neptune", "Graph", "64TB", "中", "数ms",
                       "インスタンス+IO", ["ソーシャルグラフ", "レコメンデーション", "不正検知"]),
        DatabaseOption("Timestream", "Time-Series", "無制限", "高", "数ms",
                       "書込み+クエリ+ストレージ", ["IoTデータ", "メトリクス", "ログ分析"]),
        DatabaseOption("OpenSearch", "Search/Analytics", "3PB", "高", "数十ms",
                       "インスタンス+ストレージ", ["全文検索", "ログ分析", "ダッシュボード"]),
    ]

    print(f"    {'DB名':<24} {'タイプ':<16} {'レイテンシ':<10} {'ベストユースケース'}")
    print("    " + "-" * 85)
    for db in databases:
        usecases = ", ".join(db.best_for[:2])
        print(f"    {db.name:<24} {db.db_type:<16} {db.latency:<10} {usecases}")

    print("""
    ■ Decision Tree

    データモデルは？
    ├─ リレーショナル (JOIN, トランザクション)
    │   ├─ 中小規模 → RDS
    │   ├─ 大規模, 高可用性 → Aurora
    │   └─ 負荷変動大 → Aurora Serverless v2
    │
    ├─ キーバリュー / ドキュメント
    │   ├─ 超低レイテンシ (< 1ms) → ElastiCache (DAX)
    │   └─ 水平スケール, 柔軟 → DynamoDB
    │
    ├─ グラフ (関係性が重要)
    │   └─ Neptune
    │
    ├─ 時系列データ
    │   └─ Timestream
    │
    └─ 全文検索 / ログ分析
        └─ OpenSearch

    ■ DynamoDB アクセスパターン設計の鉄則

    1. Single Table Design: 関連エンティティを1テーブルに
    2. PK/SK設計が全て: クエリパターンを先に決める
    3. GSI (Global Secondary Index) で追加アクセスパターン
    4. 書込みシャーディング: ホットパーティション回避
       例: PK = "ORDER#2024-01-15#" + random(0,9)
    """)

    # DynamoDBアクセスパターン例
    print_subsection("DynamoDB Single Table Design 例: Eコマース")
    table_data = [
        ("USER#123", "PROFILE", "name=田中, email=..."),
        ("USER#123", "ORDER#2024-001", "total=5000, status=shipped"),
        ("USER#123", "ORDER#2024-002", "total=3200, status=pending"),
        ("ORDER#2024-001", "ITEM#A", "product=Tシャツ, qty=2"),
        ("ORDER#2024-001", "ITEM#B", "product=靴, qty=1"),
        ("PRODUCT#A", "INFO", "name=Tシャツ, price=2500"),
    ]
    print(f"    {'PK':<20} {'SK':<20} {'Attributes'}")
    print("    " + "-" * 60)
    for pk, sk, attrs in table_data:
        print(f"    {pk:<20} {sk:<20} {attrs}")

    print("""
    クエリ例:
      - ユーザー情報取得: PK=USER#123, SK=PROFILE
      - ユーザーの全注文: PK=USER#123, SK begins_with ORDER#
      - 注文の全商品:     PK=ORDER#2024-001, SK begins_with ITEM#
    """)

    print_question(
        "1日100万件のセンサーデータを保存し、直近1時間のデータに対して\n"
        "    集計クエリを頻繁に実行する場合、DynamoDB と Timestream の\n"
        "    どちらが適切か？コストとクエリ性能の観点で考えよ。"
    )


# ============================================================
# 6. イベント駆動アーキテクチャ
# ============================================================

class MessageBrokerType(Enum):
    SQS = "Amazon SQS"
    SNS = "Amazon SNS"
    EVENTBRIDGE = "Amazon EventBridge"
    KINESIS = "Amazon Kinesis"


@dataclass
class Message:
    id: str
    body: str
    timestamp: float
    attributes: Dict[str, str] = field(default_factory=dict)
    delivery_count: int = 0


class SimpleQueue:
    """SQS風のキューシミュレーション"""

    def __init__(self, name: str, dead_letter_queue: Optional['SimpleQueue'] = None,
                 max_retries: int = 3):
        self.name = name
        self.messages: List[Message] = []
        self.in_flight: Dict[str, Message] = {}
        self.dlq = dead_letter_queue
        self.max_retries = max_retries
        self.processed = 0
        self.failed = 0

    def send(self, body: str, attrs: Optional[Dict] = None) -> str:
        msg_id = hashlib.md5(f"{body}{time.time()}".encode()).hexdigest()[:8]
        msg = Message(id=msg_id, body=body, timestamp=time.time(), attributes=attrs or {})
        self.messages.append(msg)
        return msg_id

    def receive(self) -> Optional[Message]:
        if not self.messages:
            return None
        msg = self.messages.pop(0)
        msg.delivery_count += 1
        self.in_flight[msg.id] = msg
        return msg

    def ack(self, msg_id: str, success: bool) -> str:
        msg = self.in_flight.pop(msg_id, None)
        if not msg:
            return "メッセージが見つかりません"
        if success:
            self.processed += 1
            return f"[ACK] メッセージ {msg_id} 処理完了"
        else:
            self.failed += 1
            if msg.delivery_count >= self.max_retries:
                if self.dlq:
                    self.dlq.messages.append(msg)
                    return f"[DLQ] メッセージ {msg_id} をDLQに移動 (リトライ上限 {self.max_retries} 回到達)"
                return f"[DROP] メッセージ {msg_id} を破棄 (DLQなし)"
            self.messages.append(msg)
            return f"[RETRY] メッセージ {msg_id} をキューに戻し (試行 {msg.delivery_count}/{self.max_retries})"


def demo_event_driven():
    print_section("6. イベント駆動アーキテクチャ")

    print("""
    ■ メッセージングサービス比較

    ┌──────────────┬──────────┬─────────┬───────────┬──────────┐
    │ 特性          │ SQS      │ SNS     │EventBridge│ Kinesis  │
    ├──────────────┼──────────┼─────────┼───────────┼──────────┤
    │ パターン      │ Queue    │ Pub/Sub │ Event Bus │ Stream   │
    │ 配信          │ Pull     │ Push    │ Push      │ Pull     │
    │ 順序保証      │ FIFO可   │ FIFO可  │ なし      │ シャード内│
    │ 重複排除      │ FIFO可   │ なし    │ なし      │ なし     │
    │ メッセージ保持│ 最大14日 │ なし    │ 最大24h   │ 最大365日│
    │ スループット  │ 無制限*  │ 無制限* │ 制限あり  │ シャード依存│
    │ ファンアウト  │ なし     │ あり    │ あり      │ なし     │
    │ フィルタリング│ なし     │ 属性    │ パターン  │ なし     │
    │ コスト/100万  │ $0.40    │ $0.50   │ $1.00     │ シャード/h│
    └──────────────┴──────────┴─────────┴───────────┴──────────┘

    ■ Fan-Out パターン

         ┌──────────────┐
         │  注文サービス │
         └──────┬───────┘
                │ OrderCreated Event
                ▼
         ┌──────────────┐
         │     SNS      │
         └──────┬───────┘
           ┌────┼────┐
           ▼    ▼    ▼
         ┌───┐┌───┐┌───┐
         │SQS││SQS││SQS│
         └─┬─┘└─┬─┘└─┬─┘
           ▼    ▼    ▼
        在庫  決済  通知
        更新  処理  送信
    """)

    # DLQシミュレーション
    print_subsection("Dead Letter Queue シミュレーション")
    dlq = SimpleQueue("order-processing-dlq")
    main_queue = SimpleQueue("order-processing", dead_letter_queue=dlq, max_retries=3)

    # メッセージ送信
    for i in range(5):
        msg_id = main_queue.send(f"Order-{i+1:03d}", {"type": "order", "priority": "high"})
        print(f"    [SEND] Order-{i+1:03d} (id: {msg_id})")

    print()
    # 処理シミュレーション (一部失敗)
    random.seed(42)
    while main_queue.messages:
        msg = main_queue.receive()
        if msg:
            success = msg.body != "Order-003"  # Order-003は常に失敗
            result = main_queue.ack(msg.id, success)
            print(f"    {result}")

    print(f"\n    処理成功: {main_queue.processed}, 処理失敗: {main_queue.failed}")
    print(f"    DLQ内メッセージ: {len(dlq.messages)}")

    # Exactly-Once Processing の課題
    print_subsection("Exactly-Once Processing の課題")
    print("""
    メッセージ配信の保証レベル:
      1. At-Most-Once:  メッセージは最大1回配信 (損失あり)
      2. At-Least-Once: メッセージは最低1回配信 (重複あり) ← SQS Standard
      3. Exactly-Once:  メッセージは正確に1回配信 ← SQS FIFO (制限あり)

    実務での Exactly-Once 実現パターン:
    ┌────────────────────────────────────────────────┐
    │ Idempotency (冪等性) パターン                    │
    │                                                │
    │ 1. メッセージIDをDynamoDBに記録                  │
    │ 2. 処理前に重複チェック                          │
    │ 3. 条件付き書き込み (ConditionalCheckFailed)     │
    │                                                │
    │ Consumer:                                      │
    │   if not dynamodb.get(msg.id):                 │
    │       process(msg)                             │
    │       dynamodb.put(msg.id, ttl=24h)            │
    │   else:                                        │
    │       skip (already processed)                 │
    └────────────────────────────────────────────────┘

    EventBridge のルールパターン例:
    {
      "source": ["order-service"],
      "detail-type": ["OrderCreated"],
      "detail": {
        "amount": [{"numeric": [">=", 10000]}],
        "region": ["ap-northeast-1"]
      }
    }
    → 1万円以上の東京リージョンの注文のみマッチ
    """)

    print_question(
        "SQS FIFO は 300 TPS (バッチで3000) の制限がある。\n"
        "    順序保証が必要で 10,000 TPS を処理するにはどうするか？"
    )
    print_task(
        "上記の SimpleQueue クラスに Visibility Timeout を実装せよ。\n"
        "    受信後 30秒以内にACKしないとキューに戻る仕組みを作れ。"
    )


# ============================================================
# 7. コスト最適化
# ============================================================

@dataclass
class EC2PricingOption:
    name: str
    hourly_rate: float
    commitment: str
    savings_pct: float
    risk: str


def demo_cost_optimization():
    print_section("7. コスト最適化 / FinOps")

    print("""
    ■ EC2 購入オプション比較 (m5.xlarge 東京リージョン基準)

    ┌──────────────────┬─────────┬──────────┬───────┬───────────────┐
    │ オプション        │ 時間単価 │ 割引率   │ 確約  │ リスク         │
    ├──────────────────┼─────────┼──────────┼───────┼───────────────┤
    │ On-Demand         │ $0.248  │ 0%      │ なし  │ なし           │
    │ Reserved 1yr NUI  │ $0.156  │ ~37%    │ 1年   │ 低 (変更可)    │
    │ Reserved 3yr AUI  │ $0.101  │ ~59%    │ 3年   │ 中 (全額前払)  │
    │ Savings Plans 1yr │ $0.155  │ ~38%    │ 1年   │ 低 (柔軟)      │
    │ Spot Instance     │ $0.074  │ ~70%    │ なし  │ 高 (中断あり)  │
    └──────────────────┴─────────┴──────────┴───────┴───────────────┘

    NUI=No Upfront, AUI=All Upfront
    """)

    options = [
        EC2PricingOption("On-Demand", 0.248, "なし", 0, "なし"),
        EC2PricingOption("Reserved 1yr", 0.156, "1年", 37, "低"),
        EC2PricingOption("Reserved 3yr", 0.101, "3年", 59, "中"),
        EC2PricingOption("Savings Plans", 0.155, "1年", 38, "低"),
        EC2PricingOption("Spot Instance", 0.074, "なし", 70, "高"),
    ]

    print_subsection("月額コスト比較 (10台 × 24h × 30日)")
    total_hours = 10 * 24 * 30
    for opt in options:
        monthly = opt.hourly_rate * total_hours
        bar = "█" * int(monthly / 30)
        print(f"    {opt.name:<18} ${monthly:>7.0f}/月 {bar}")

    # S3 Storage Tiers
    print_subsection("S3 ストレージ階層")
    print("""
    ┌──────────────────────┬──────────┬───────────┬──────────────────┐
    │ ストレージクラス      │ GB/月    │ 取出コスト │ 最適なユースケース│
    ├──────────────────────┼──────────┼───────────┼──────────────────┤
    │ S3 Standard           │ $0.025  │ 無料      │ 頻繁なアクセス    │
    │ S3 Intelligent-Tiering│ $0.025* │ 無料      │ アクセスパターン不明│
    │ S3 Standard-IA        │ $0.0138 │ $0.01/GB  │ 月1回程度アクセス  │
    │ S3 One Zone-IA        │ $0.011  │ $0.01/GB  │ 再作成可能データ   │
    │ S3 Glacier Instant    │ $0.005  │ $0.03/GB  │ 四半期1回アクセス  │
    │ S3 Glacier Flexible   │ $0.0045 │ 分〜時間  │ 年1-2回アクセス    │
    │ S3 Glacier Deep Arch  │ $0.002  │ 12〜48時間│ 7-10年保持の規制   │
    └──────────────────────┴──────────┴───────────┴──────────────────┘

    * Intelligent-Tiering: 監視料 $0.0025/1000obj/月が追加
    """)

    # FinOps実践
    print_subsection("FinOps 実践フレームワーク")
    print("""
    FinOps = クラウド支出の可視化・最適化・ガバナンスの文化

    1. Inform (可視化)
       - Cost Explorer でトレンド分析
       - タグ戦略: Environment, Team, Service, CostCenter
       - AWS Organizations + 統合請求

    2. Optimize (最適化)
       - Right-sizing: CloudWatch メトリクスで使用率確認
         → CPU使用率 < 20% のインスタンスをダウンサイズ
       - Unused リソース検出: 未アタッチEBS, 未使用EIP
       - Savings Plans / RI のカバレッジ目標: 70-80%

    3. Operate (運用)
       - 月次 FinOps レビュー会議
       - 異常コストアラート (AWS Budgets + SNS)
       - Spot Instance 活用 (バッチ処理, CI/CD)

    コスト削減の優先順位:
      1位: 不要リソースの削除        (即効性: 高, 効果: 大)
      2位: Right-sizing              (即効性: 高, 効果: 中)
      3位: Reserved / Savings Plans  (即効性: 中, 効果: 大)
      4位: Spot Instance 活用        (即効性: 中, 効果: 中)
      5位: アーキテクチャ見直し       (即効性: 低, 効果: 大)
    """)

    print_question(
        "チームのAWS月額が $50,000。RI カバレッジ 30%, Spot 未使用。\n"
        "    6ヶ月で 30% 削減する計画を立てよ。\n"
        "    何を最初に実行するか？"
    )


# ============================================================
# 8. 災害復旧 (DR)
# ============================================================

@dataclass
class DRStrategy:
    name: str
    rto: str  # Recovery Time Objective
    rpo: str  # Recovery Point Objective
    cost_relative: str
    description: str
    aws_services: List[str]


def demo_disaster_recovery():
    print_section("8. 災害復旧 (DR)")

    print("""
    ■ RPO と RTO

    RPO (Recovery Point Objective):
      データ損失をどこまで許容するか (時間)
      「最大何時間分のデータを失っても許容できるか」

    RTO (Recovery Time Objective):
      復旧にどこまで時間をかけられるか
      「障害発生から何時間以内にサービス復旧が必要か」

    ────────────────────────────────────────────────
    過去のデータ ◄─── RPO ───► 障害発生 ◄─── RTO ───► 復旧完了
    (最後のバックアップ)                    (サービス再開)
    ────────────────────────────────────────────────
    """)

    strategies = [
        DRStrategy(
            "Backup & Restore", "24時間", "24時間", "$ (最低)",
            "定期バックアップをS3/別リージョンに保存。障害時にバックアップから復元。",
            ["S3 Cross-Region Replication", "AWS Backup", "EBS Snapshots"],
        ),
        DRStrategy(
            "Pilot Light", "数時間", "数時間", "$$ (低)",
            "最小構成のインフラを常時稼働。障害時にスケールアップ。DBレプリケーションは常時。",
            ["RDS Read Replica (Cross-Region)", "Route53 Failover", "CloudFormation"],
        ),
        DRStrategy(
            "Warm Standby", "数分〜1時間", "数分", "$$$ (中)",
            "縮小版の本番環境を常時稼働。障害時にスケールアップ。",
            ["Auto Scaling", "Aurora Global Database", "Route53", "CloudFormation"],
        ),
        DRStrategy(
            "Multi-Site Active-Active", "ほぼゼロ", "ほぼゼロ", "$$$$ (高)",
            "複数リージョンで本番同等の環境を常時稼働。即座にフェイルオーバー。",
            ["DynamoDB Global Tables", "Aurora Global DB", "Global Accelerator", "Route53"],
        ),
    ]

    print_subsection("4つのDR戦略比較")
    print(f"    {'戦略':<28} {'RTO':<12} {'RPO':<12} {'コスト'}")
    print("    " + "-" * 70)
    for s in strategies:
        print(f"    {s.name:<28} {s.rto:<12} {s.rpo:<12} {s.cost_relative}")

    print()
    for s in strategies:
        print(f"\n    ■ {s.name}")
        print(f"      {s.description}")
        print(f"      主要サービス: {', '.join(s.aws_services)}")

    print("""
    ■ DR戦略のアーキテクチャ比較

    【Backup & Restore】
    Primary Region           DR Region
    ┌──────────┐            ┌──────────┐
    │  App+DB  │──Backup──►│  S3      │
    └──────────┘            └──────────┘
    障害時: S3からAMI/スナップショットで再構築

    【Pilot Light】
    Primary Region           DR Region
    ┌──────────┐            ┌──────────┐
    │  App+DB  │──Repl───►│  DB (min)│
    └──────────┘            └──────────┘
    障害時: App層を起動+DBスケールアップ

    【Warm Standby】
    Primary Region           DR Region
    ┌──────────┐            ┌──────────┐
    │ App (x10)│──Repl───►│App (x2) │
    │ DB (lg)  │           │ DB (sm) │
    └──────────┘            └──────────┘
    障害時: Auto Scalingでスケールアップ

    【Multi-Site Active-Active】
    Primary Region           Secondary Region
    ┌──────────┐            ┌──────────┐
    │ App (x10)│◄──Repl──►│App (x10)│
    │ DB (lg)  │           │ DB (lg) │
    └──────────┘            └──────────┘
    障害時: Route53が自動フェイルオーバー
    """)

    # RPO/RTO計算
    print_subsection("あなたのシステムに必要なDR戦略は？")
    print("""
    質問1: 1時間のダウンタイムの損失は？
      A) $1,000以下     → Backup & Restore で十分
      B) $1,000-$10,000 → Pilot Light を検討
      C) $10,000-$100K  → Warm Standby を検討
      D) $100K以上      → Multi-Site Active-Active

    質問2: データ損失の許容時間は？
      A) 24時間 → 日次バックアップ
      B) 1時間  → ポイントインタイムリカバリ
      C) 数分   → 非同期レプリケーション
      D) ゼロ   → 同期レプリケーション (コスト高)
    """)

    print_question(
        "金融系システムで RPO=0, RTO=5分 が要件。\n"
        "    Multi-Site Active-Active を採用した場合、\n"
        "    本番の2倍以上のコストがかかる。コストを正当化する方法は？"
    )


# ============================================================
# 9. AWS vs GCP サービス対応表
# ============================================================

def demo_aws_gcp_mapping():
    print_section("9. AWS vs GCP サービス対応表")

    mappings = [
        ("カテゴリ", "AWS", "GCP"),
        ("─" * 10, "─" * 24, "─" * 24),
        ("コンピュート", "EC2", "Compute Engine"),
        ("", "Lambda", "Cloud Functions"),
        ("", "ECS / EKS", "Cloud Run / GKE"),
        ("", "Fargate", "Cloud Run"),
        ("", "Elastic Beanstalk", "App Engine"),
        ("ストレージ", "S3", "Cloud Storage (GCS)"),
        ("", "EBS", "Persistent Disk"),
        ("", "EFS", "Filestore"),
        ("", "Glacier", "Archive Storage"),
        ("データベース", "RDS", "Cloud SQL"),
        ("", "Aurora", "AlloyDB / Cloud Spanner"),
        ("", "DynamoDB", "Firestore / Bigtable"),
        ("", "ElastiCache", "Memorystore"),
        ("", "Redshift", "BigQuery"),
        ("", "Neptune", "Neo4j on GCP"),
        ("ネットワーク", "VPC", "VPC"),
        ("", "Route53", "Cloud DNS"),
        ("", "CloudFront", "Cloud CDN"),
        ("", "ELB / ALB", "Cloud Load Balancing"),
        ("", "API Gateway", "Apigee / API Gateway"),
        ("", "Direct Connect", "Cloud Interconnect"),
        ("メッセージング", "SQS", "Cloud Tasks / Pub/Sub"),
        ("", "SNS", "Pub/Sub"),
        ("", "EventBridge", "Eventarc"),
        ("", "Kinesis", "Dataflow / Pub/Sub"),
        ("AI/ML", "SageMaker", "Vertex AI"),
        ("", "Bedrock", "Vertex AI (Model Garden)"),
        ("", "Rekognition", "Vision AI"),
        ("監視/運用", "CloudWatch", "Cloud Monitoring"),
        ("", "CloudTrail", "Cloud Audit Logs"),
        ("", "CloudFormation", "Deployment Manager / Terraform"),
        ("", "Systems Manager", "OS Config"),
        ("セキュリティ", "IAM", "IAM"),
        ("", "KMS", "Cloud KMS"),
        ("", "WAF", "Cloud Armor"),
        ("", "GuardDuty", "Security Command Center"),
    ]

    for cat, aws, gcp in mappings:
        print(f"    {cat:<14} {aws:<24} {gcp}")

    print("""
    ■ GCP の強み
    - BigQuery: サーバーレスDWH、ペタバイト規模のSQLが秒単位
    - GKE: Kubernetes のマネージドサービスとして最も成熟
    - Cloud Spanner: グローバル分散RDB (強整合性 + 水平スケール)
    - Vertex AI: MLOps統合プラットフォーム
    - Cloud Run: コンテナのサーバーレス実行が最もシンプル

    ■ AWS の強み
    - サービス数が圧倒的に多い (200+)
    - エンタープライズ採用実績
    - リージョン数が最多
    - コミュニティ・ドキュメントの充実
    - Lambda + Step Functions のエコシステム

    ■ マルチクラウド戦略の現実
    - Terraform/Pulumi で IaC を共通化
    - Kubernetes (EKS/GKE) でコンテナ層を抽象化
    - 各クラウドのマネージドサービスはロックイン覚悟で活用
    - データ転送コスト (Egress) がマルチクラウドの最大コスト
    """)

    print_question(
        "「全サービスをKubernetesに載せればマルチクラウドが実現できる」\n"
        "    この主張の問題点を3つ挙げよ。"
    )


# ============================================================
# 10. 面接設計問題: Global ML Inference Platform (100K QPS)
# ============================================================

def demo_interview_design():
    print_section("10. 面接設計問題")
    print('    "Design infrastructure for a global ML inference platform')
    print('     serving 100K QPS"')

    print("""
    ■ Step 1: 要件の明確化 (面接官に聞くべき質問)

    機能要件:
    - どのようなMLモデルか？ (NLP, 画像認識, レコメンド？)
    - 入力データのサイズは？ (テキスト数百B vs 画像数MB)
    - レイテンシ要件は？ (p99 < 100ms? < 500ms?)
    - モデルの更新頻度は？ (日次？リアルタイム？)

    非機能要件:
    - 可用性: 99.99% (年間52分のダウンタイム)
    - グローバル: 北米, 欧州, アジアの3リージョン
    - 100K QPS = ~100,000 requests/second
    - 推論レイテンシ: p50 < 50ms, p99 < 200ms

    ■ Step 2: バックオブエンベロープ計算

    100K QPS の内訳 (リージョン別):
    - us-east-1: 40K QPS (北米)
    - eu-west-1: 30K QPS (欧州)
    - ap-northeast-1: 30K QPS (アジア)

    1リクエストあたり:
    - 入力: ~1KB (テキスト)
    - 推論時間: ~20ms (GPU), ~100ms (CPU)
    - 出力: ~500B

    GPU インスタンス計算 (g5.xlarge: ~200 QPS/インスタンス):
    - us-east-1: 40,000 / 200 = 200 インスタンス
    - + 余裕 (50%): 300 インスタンス/リージョン

    帯域幅:
    - Ingress: 100K * 1KB = 100MB/s = 800Mbps
    - Egress:  100K * 500B = 50MB/s = 400Mbps
    """)

    print("""
    ■ Step 3: 高レベルアーキテクチャ

    ┌─────────────────────────────────────────────────────────┐
    │                    Global Architecture                  │
    │                                                         │
    │   Users ──► CloudFront ──► Global Accelerator           │
    │                              │                          │
    │             ┌────────────────┼────────────────┐         │
    │             ▼                ▼                ▼         │
    │        ┌─────────┐    ┌─────────┐    ┌─────────┐       │
    │        │us-east-1│    │eu-west-1│    │ap-ne-1  │       │
    │        │  (40K)  │    │  (30K)  │    │ (30K)   │       │
    │        └────┬────┘    └────┬────┘    └────┬────┘       │
    │             │              │              │             │
    └─────────────┼──────────────┼──────────────┼─────────────┘
                  ▼              ▼              ▼
    ┌─────────────────────────────────────────────────────────┐
    │              Per-Region Architecture                     │
    │                                                         │
    │  ALB ──► EKS Cluster                                    │
    │           │                                             │
    │           ├── Model Server Pods (GPU: g5.xlarge)        │
    │           │    ├── Triton Inference Server               │
    │           │    ├── Model A (v2.1) - 60%                 │
    │           │    └── Model B (v2.2) - 40% (canary)        │
    │           │                                             │
    │           ├── Pre-processor Pods (CPU)                  │
    │           │    └── 入力検証, トークナイズ, バッチング     │
    │           │                                             │
    │           └── Post-processor Pods (CPU)                 │
    │                └── 出力フォーマット, フィルタリング       │
    │                                                         │
    │  ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
    │  │ElastiCache│  │  S3      │  │ DynamoDB     │          │
    │  │(Feature   │  │(Model   │  │(Request Log, │          │
    │  │ Cache)    │  │ Store)  │  │ A/B Config)  │          │
    │  └──────────┘  └──────────┘  └──────────────┘          │
    └─────────────────────────────────────────────────────────┘
    """)

    print("""
    ■ Step 4: 深掘り設計

    【モデルサービング】
    - NVIDIA Triton Inference Server on EKS
    - Dynamic Batching: 小リクエストをバッチ化して GPU 効率向上
    - Model Warmup: 新バージョンデプロイ前にウォームアップ
    - GPU: g5.xlarge (NVIDIA A10G) or inf2 (AWS Inferentia2)
      → Inferentia2 は推論特化で ~40% コスト削減

    【スケーリング戦略】
    - Karpenter (EKS): GPU ノードの高速オートスケーリング
    - HPA: GPU使用率 70% で Pod スケール
    - 予測的スケーリング: 時間帯パターンで事前スケール
    - Spot Instance: GPU Spot は不安定なため推論には Reserved 推奨

    【キャッシング】
    - ElastiCache Redis: 同一入力の推論結果をキャッシュ
    - キャッシュヒット率 10% でも 10K QPS 削減 = GPU 50台分節約
    - TTL: モデルバージョンに紐づけ (モデル更新時にinvalidate)

    【モデル更新パイプライン】
    SageMaker Training → S3 (Model Store) → ECR (Container)
      → EKS Rolling Update (Canary: 10% → 50% → 100%)
      → 推論精度メトリクスで自動ロールバック

    【可観測性】
    - メトリクス: Prometheus + Grafana
      - GPU使用率, 推論レイテンシ p50/p99, バッチサイズ
      - QPS per model version, キャッシュヒット率
    - ログ: Fluent Bit → OpenSearch
    - トレース: AWS X-Ray / OpenTelemetry
    - アラート: p99 > 200ms or エラー率 > 0.1%

    【コスト最適化】
    - Reserved Instance (GPU): $0.816/h → $0.52/h (37%削減)
    - 300台 × $0.52 × 720h × 3リージョン = $336,960/月
    - キャッシュによる削減: -10% = $303,264/月
    - Inferentia2 移行: さらに -40% = $181,958/月

    【障害対策】
    - リージョン障害: Route53 Failover で他リージョンに振り分け
    - モデル障害: 前バージョンへの自動ロールバック
    - GPU障害: Karpenter が自動的にノード置換
    - 負荷急増: Circuit Breaker + Rate Limiting + Graceful Degradation
      → キャッシュヒットのみ返す「縮退運転モード」
    """)

    # 設計レビューチェックリスト
    print_subsection("設計レビューチェックリスト")
    checklist = [
        ("可用性",      "マルチAZ + マルチリージョン構成か", True),
        ("スケーラビリティ", "100K QPSを処理できる計算根拠があるか", True),
        ("レイテンシ",   "p99 < 200ms を満たす設計か", True),
        ("コスト",      "月額コストの概算があるか", True),
        ("運用",        "モデル更新のCI/CDパイプラインがあるか", True),
        ("監視",        "GPU/レイテンシ/エラー率の監視があるか", True),
        ("セキュリティ", "認証/認可/暗号化が考慮されているか", False),
        ("障害復旧",    "Circuit Breaker/Graceful Degradation があるか", True),
    ]
    for area, check, passed in checklist:
        status = "✓" if passed else "△"
        print(f"    [{status}] {area:<16} {check}")

    print_task(
        "上記設計を拡張して、以下を追加設計せよ:\n"
        "    1. A/Bテスト基盤 (トラフィックの5%を新モデルに振り分け)\n"
        "    2. Feature Store (リアルタイム特徴量サービング)\n"
        "    3. モデルの段階的ロールアウト戦略 (Canary → Linear → Full)"
    )


# ============================================================
# まとめと学習ロードマップ
# ============================================================

def demo_summary():
    print_section("まとめ: クラウドアーキテクチャ学習ロードマップ")

    print("""
    ■ 学習の優先順位 (PM志望エンジニア向け)

    Phase 1 (1-2ヶ月): 基礎
    ┌────────────────────────────────────────────┐
    │ □ Well-Architected Framework 6柱の理解      │
    │ □ VPC, EC2, S3, RDS, IAM の実践            │
    │ □ CloudFormation or Terraform で IaC       │
    │ □ AWS Solutions Architect Associate 取得    │
    └────────────────────────────────────────────┘

    Phase 2 (2-3ヶ月): 応用
    ┌────────────────────────────────────────────┐
    │ □ サーバーレス (Lambda + API GW + DynamoDB)  │
    │ □ コンテナ (ECS Fargate or EKS)             │
    │ □ イベント駆動 (SQS, SNS, EventBridge)      │
    │ □ CI/CD パイプライン構築                     │
    └────────────────────────────────────────────┘

    Phase 3 (3-6ヶ月): 上級
    ┌────────────────────────────────────────────┐
    │ □ マルチリージョン設計                       │
    │ □ DR戦略の設計と訓練                        │
    │ □ FinOps / コスト最適化の実践               │
    │ □ AWS Solutions Architect Professional 取得 │
    └────────────────────────────────────────────┘

    ■ 面接対策のキーポイント

    1. トレードオフを語れること
       - 「AがBより優れている」ではなく
       - 「この要件ではAが適切。理由は...。ただしBを選ぶ場合は...」

    2. 数字で語れること
       - 「スケールする」ではなく「100K QPSに対してg5.xlargeが300台必要」

    3. 障害シナリオを考えること
       - 「このコンポーネントが落ちたらどうなるか」を全要素で

    4. コストを意識すること
       - 月額概算を出せるとFAANG面接で差がつく
    """)


# ============================================================
# メイン実行
# ============================================================

def main():
    print("=" * 60)
    print("  Cloud Architecture Patterns - FAANG Level")
    print("  AWS Well-Architected, マルチリージョン, サーバーレス,")
    print("  イベント駆動, コスト最適化, 災害復旧")
    print("=" * 60)

    demo_well_architected()
    demo_multi_region()
    demo_serverless()
    demo_compute_comparison()
    demo_database_selection()
    demo_event_driven()
    demo_cost_optimization()
    demo_disaster_recovery()
    demo_aws_gcp_mapping()
    demo_interview_design()
    demo_summary()

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - Well-Architected 6本柱
    - VPC設計
    - IAM最小権限
    - RDS vs DynamoDB選定

  【Tier 2: 重要 — 実務で頻出】
    - マルチAZ/マルチリージョン
    - サーバーレス(Lambda+API GW)
    - DR戦略(RPO/RTO)

  【Tier 3: 上級 — シニア以上で差がつく】
    - Transit Gateway
    - FinOps/コスト最適化
    - CloudFront+WAF

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Outposts
    - Control Tower
    - Landing Zone
    - マルチアカウント戦略
""")

    print("\n" + "━" * 60)
    print("  学習完了！")
    print("  次のステップ: 実際にAWSコンソールで手を動かしてみよう")
    print("━" * 60)


if __name__ == "__main__":
    main()
