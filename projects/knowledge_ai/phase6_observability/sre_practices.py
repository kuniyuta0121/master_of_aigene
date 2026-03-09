#!/usr/bin/env python3
"""
FAANG レベル SRE & 可観測性 実践ガイド
========================================
Google SRE Book の原則からカオスエンジニアリングまで、
本番運用に必要な知識を体系的に学ぶ。

実行: python sre_practices.py
依存: 標準ライブラリのみ
"""

import math
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional
from collections import defaultdict

SEP = "━" * 60


# ============================================================
# 1. SRE の基本原則
# ============================================================
def section_sre_fundamentals():
    print(f"\n{SEP}")
    print("1. SRE の基本原則 — Google SRE Book Core Concepts")
    print(SEP)

    print("""
SRE (Site Reliability Engineering) は Google が提唱した運用の方法論。
「ソフトウェアエンジニアに運用を任せたらどうなるか」という問いへの答え。

■ 7 つの原則
  1) Embrace Risk — 100% 可用性は目指さない。リスクを定量化する
  2) SLO (Service Level Objectives) — 信頼性の目標を数値で定義
  3) Eliminate Toil — 手作業・繰り返し作業を自動化で排除
  4) Monitoring — 症状ベースのアラート、原因は調査で特定
  5) Release Engineering — 安全なデプロイの自動化
  6) Simplicity — 複雑性は信頼性の敵
  7) Capacity Planning — 需要予測に基づくリソース計画

■ Error Budget（エラー予算）
  SLO が 99.9% なら、月間で 0.1% のダウンタイムが「予算」。
  予算が残っている → 新機能リリースを加速
  予算を使い切った → リリース凍結、信頼性改善に集中

  月間 43,200 分 × 0.001 = 43.2 分のダウンタイムが許容範囲

■ 50% ルール
  SRE チームの時間配分:
    50% 以上 → エンジニアリング作業（自動化・ツール開発・設計）
    50% 未満 → 運用作業（トイル）
  トイルが 50% を超えたら、自動化の投資が必要というシグナル。

■ Toil の定義
  - 手動的（Manual）: 人間がコマンドを実行する
  - 繰り返し（Repetitive）: 同じ作業を何度もやる
  - 自動化可能（Automatable）: 機械にやらせられる
  - 戦術的（Tactical）: 長期的な価値を生まない
  - スケールしない（O(n)）: サービス成長に比例して増える
""")

    print("[考えてほしい疑問]")
    print("  Q: SLO 99.99% と 99.9% でエラー予算は何倍違う？")
    print("  A: 10倍。99.9% = 43.2分/月、99.99% = 4.32分/月")
    print("     この差が開発速度に直結する。過剰な SLO は組織を遅くする。")


# ============================================================
# 2. SLI / SLO / SLA
# ============================================================
@dataclass
class SLODefinition:
    """SLO の定義と計算"""
    name: str
    sli_type: str          # availability, latency, throughput, correctness
    target: float          # 例: 0.999 (99.9%)
    window_days: int       # 測定ウィンドウ（日数）

    def error_budget_minutes(self) -> float:
        total_minutes = self.window_days * 24 * 60
        return total_minutes * (1.0 - self.target)

    def remaining_budget(self, consumed_minutes: float) -> dict:
        budget = self.error_budget_minutes()
        remaining = budget - consumed_minutes
        pct = (remaining / budget) * 100 if budget > 0 else 0
        return {
            "total_budget_min": round(budget, 2),
            "consumed_min": round(consumed_minutes, 2),
            "remaining_min": round(remaining, 2),
            "remaining_pct": round(pct, 2),
            "action": self._recommend_action(pct),
        }

    def _recommend_action(self, remaining_pct: float) -> str:
        if remaining_pct > 50:
            return "GREEN: 新機能リリースを積極的に進めてよい"
        elif remaining_pct > 20:
            return "YELLOW: 慎重にリリース。リスクの高い変更は控える"
        elif remaining_pct > 0:
            return "ORANGE: リリース凍結を検討。信頼性改善に注力"
        else:
            return "RED: リリース凍結。全力で信頼性を回復せよ"


def section_sli_slo_sla():
    print(f"\n{SEP}")
    print("2. SLI / SLO / SLA — 信頼性を数値で語る")
    print(SEP)

    print("""
■ 用語の階層
  SLA (Service Level Agreement)
    └─ ビジネス契約。違反するとペナルティ（返金など）
  SLO (Service Level Objective)
    └─ 内部目標。SLA より厳しく設定する（バッファ）
  SLI (Service Level Indicator)
    └─ 実際の計測値。SLO の達成度を測る指標

■ SLI の選び方（The Four Golden Signals 拡張）
  1) Availability: 成功リクエスト数 / 全リクエスト数
  2) Latency: リクエストの応答時間（p50, p95, p99）
  3) Throughput: 単位時間あたりの処理量
  4) Correctness: 正しい結果を返した割合

■ SLO 設定の方法論
  Step 1: ユーザー体験から逆算（技術都合で決めない）
  Step 2: 過去データから現状の達成率を確認
  Step 3: 達成可能かつ意味のある目標を設定
  Step 4: Error Budget Policy を策定
  Step 5: 定期レビュー（四半期ごと）

■ Error Budget Policy（エラー予算ポリシー）の例
  - 予算残 > 50%: 通常運用
  - 予算残 20-50%: リリース頻度を下げる
  - 予算残 < 20%: 高リスク変更を凍結
  - 予算消尽: 全変更凍結、ポストモーテム必須
""")

    # SLO 計算デモ
    print("--- SLO Calculator デモ ---")
    slo = SLODefinition(
        name="API Gateway",
        sli_type="availability",
        target=0.999,
        window_days=30,
    )
    result = slo.remaining_budget(consumed_minutes=20.0)
    print(f"  サービス: {slo.name}")
    print(f"  SLO: {slo.target * 100}% ({slo.sli_type})")
    print(f"  ウィンドウ: {slo.window_days}日間")
    for k, v in result.items():
        print(f"    {k}: {v}")

    print()
    # 複数サービスの比較
    services = [
        SLODefinition("決済API", "availability", 0.9999, 30),
        SLODefinition("検索API", "latency_p99", 0.999, 30),
        SLODefinition("通知API", "availability", 0.99, 30),
    ]
    print("  サービス別エラー予算比較（30日間）:")
    for svc in services:
        budget = svc.error_budget_minutes()
        print(f"    {svc.name} (SLO {svc.target*100}%): "
              f"予算 {budget:.1f}分 = {budget/60:.1f}時間")


# ============================================================
# 3. 可観測性の3本柱 + Events
# ============================================================
class MetricType(Enum):
    COUNTER = auto()    # 単調増加（リクエスト数、エラー数）
    GAUGE = auto()      # 上下する値（CPU使用率、キュー長）
    HISTOGRAM = auto()  # 分布（レイテンシ）
    SUMMARY = auto()    # クライアント側の分位数


@dataclass
class Metric:
    name: str
    metric_type: MetricType
    labels: dict
    value: float
    timestamp: float = field(default_factory=time.time)

    def to_prometheus_format(self) -> str:
        label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
        return f"{self.name}{{{label_str}}} {self.value} {int(self.timestamp * 1000)}"


@dataclass
class StructuredLog:
    """構造化ログ — JSON 形式"""
    timestamp: str
    level: str
    service: str
    trace_id: str
    span_id: str
    message: str
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = {
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "message": self.message,
            **self.extra,
        }
        return json.dumps(data, ensure_ascii=False)


@dataclass
class Span:
    """分散トレーシングの Span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: float
    end_time: float = 0.0
    tags: dict = field(default_factory=dict)
    logs: list = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    def finish(self):
        self.end_time = time.time()


def generate_trace_id() -> str:
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:32]


def generate_span_id() -> str:
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:16]


def section_observability_pillars():
    print(f"\n{SEP}")
    print("3. 可観測性の3本柱 + Events")
    print(SEP)

    print("""
■ Metrics（メトリクス）
  「何が起きているか」を数値で表現する。集約された時系列データ。

  USE Method（リソース指向 — Brendan Gregg）:
    U - Utilization: リソースの使用率（CPU 80%）
    S - Saturation: 飽和度・キュー待ち（ディスク I/O キュー長）
    E - Errors: エラー数（ディスクエラー）

  RED Method（リクエスト指向 — Tom Wilkie）:
    R - Rate: リクエスト/秒
    E - Errors: エラーリクエスト/秒
    D - Duration: レイテンシ分布

  使い分け: インフラ監視 → USE、アプリ監視 → RED

■ Logs（ログ）
  「何が起きたか」の詳細な記録。構造化ログが必須。

  ログレベル:
    TRACE → 最も詳細（本番では通常無効）
    DEBUG → デバッグ用
    INFO  → 正常な動作記録
    WARN  → 注意が必要な状況
    ERROR → エラー発生（リカバリ可能）
    FATAL → 致命的エラー（プロセス停止）

■ Traces（トレース）
  「リクエストがどう流れたか」を可視化。マイクロサービスで必須。
  Trace = 複数の Span の集合
  Span = 1つの処理単位（DB クエリ、API 呼び出しなど）

■ Events（イベント）
  デプロイ、設定変更、スケールイベントなど。
  メトリクスの変化と相関させることで原因特定を加速。
""")

    # Metric デモ
    print("--- Prometheus 形式 Metric デモ ---")
    metrics = [
        Metric("http_requests_total", MetricType.COUNTER,
               {"method": "GET", "status": "200", "path": "/api/users"}, 15234),
        Metric("http_request_duration_seconds", MetricType.HISTOGRAM,
               {"method": "POST", "path": "/api/orders", "le": "0.5"}, 0.342),
        Metric("node_cpu_usage_percent", MetricType.GAUGE,
               {"instance": "web-01", "cpu": "0"}, 72.5),
    ]
    for m in metrics:
        print(f"  {m.to_prometheus_format()}")

    # 構造化ログデモ
    print("\n--- 構造化ログデモ ---")
    trace_id = generate_trace_id()
    log = StructuredLog(
        timestamp=datetime.now().isoformat(),
        level="ERROR",
        service="payment-service",
        trace_id=trace_id,
        span_id=generate_span_id(),
        message="決済処理タイムアウト",
        extra={"user_id": "u-12345", "amount": 9800, "currency": "JPY",
               "timeout_ms": 5000, "retry_count": 3},
    )
    print(f"  {log.to_json()}")

    # Span デモ
    print("\n--- 分散トレース Span デモ ---")
    root_span = Span(
        trace_id=trace_id,
        span_id=generate_span_id(),
        parent_span_id=None,
        operation_name="POST /api/orders",
        service_name="api-gateway",
        start_time=time.time(),
    )
    child_span = Span(
        trace_id=trace_id,
        span_id=generate_span_id(),
        parent_span_id=root_span.span_id,
        operation_name="INSERT orders",
        service_name="order-service",
        start_time=time.time() + 0.01,
    )
    child_span.end_time = child_span.start_time + 0.045
    root_span.end_time = root_span.start_time + 0.12
    print(f"  Root: {root_span.operation_name} ({root_span.service_name}) "
          f"duration={root_span.duration_ms:.1f}ms")
    print(f"    Child: {child_span.operation_name} ({child_span.service_name}) "
          f"duration={child_span.duration_ms:.1f}ms")

    print("\n[考えてほしい疑問]")
    print("  Q: ログとメトリクスとトレース、どれか1つしか使えないなら？")
    print("  A: メトリクス。異常の検知が最優先。ログとトレースは")
    print("     原因調査用だが、まず「何かおかしい」と気付けなければ始まらない。")


# ============================================================
# 4. アラート設計
# ============================================================
@dataclass
class BurnRateAlert:
    """Multi-Window Burn Rate アラート（Google SRE Workbook）"""
    slo_target: float          # 例: 0.999
    window_days: int           # SLO ウィンドウ（日数）
    long_window_hours: float   # 長期ウィンドウ
    short_window_hours: float  # 短期ウィンドウ（長期の 1/12 が目安）
    budget_consumption: float  # このアラートで検知する予算消費率
    severity: str

    @property
    def burn_rate_threshold(self) -> float:
        """
        burn_rate = (window_days * 24 / long_window_hours) * budget_consumption
        例: 30日SLO, 1時間窓, 2%消費 → burn_rate = (720/1) * 0.02 = 14.4
        """
        total_hours = self.window_days * 24
        return (total_hours / self.long_window_hours) * self.budget_consumption

    def check(self, error_rate_long: float, error_rate_short: float) -> dict:
        """
        error_rate = 1 - (good_events / total_events) を入力として、
        burn rate が閾値を超えているか判定
        """
        error_budget = 1.0 - self.slo_target
        if error_budget == 0:
            return {"firing": False, "reason": "SLO 100% は不正"}
        burn_long = error_rate_long / error_budget
        burn_short = error_rate_short / error_budget
        threshold = self.burn_rate_threshold
        firing = burn_long >= threshold and burn_short >= threshold
        return {
            "firing": firing,
            "severity": self.severity,
            "burn_rate_long": round(burn_long, 2),
            "burn_rate_short": round(burn_short, 2),
            "threshold": round(threshold, 2),
            "long_window_h": self.long_window_hours,
            "short_window_h": self.short_window_hours,
        }


def section_alert_design():
    print(f"\n{SEP}")
    print("4. アラート設計 — ノイズを減らし、本当の問題だけ通知する")
    print(SEP)

    print("""
■ Symptom-based vs Cause-based
  Symptom-based（症状ベース）: 推奨
    例: 「エラー率が 1% を超えた」「p99 レイテンシが 2s を超えた」
    → ユーザーに影響がある状態を検知

  Cause-based（原因ベース）: 補助的に使用
    例: 「CPU が 90% を超えた」「ディスク空き 10% 未満」
    → 問題の原因を特定する手がかり

■ アラート疲れ（Alert Fatigue）の防止
  - アクション不要なアラートは消す（アラートは行動を伴うべき）
  - 重複アラートを統合する
  - 閾値を適切に調整する（ノイズを減らす）
  - ルーティングを最適化（担当チームに直接届ける）

■ Multi-Window Multi-Burn-Rate アラート
  Google SRE Workbook 推奨のアラート戦略:

  高速燃焼（2% in 1h）  → Page（即時対応）
  中速燃焼（5% in 6h）  → Page（緊急対応）
  低速燃焼（10% in 3d） → Ticket（計画的対応）

  ポイント: 長期ウィンドウと短期ウィンドウの両方で閾値を超えた場合のみ発火。
  これにより一時的なスパイクでの誤報を防ぐ。
""")

    # Burn Rate Alert デモ
    print("--- Multi-Window Burn Rate Alert デモ ---")
    alerts = [
        BurnRateAlert(0.999, 30, 1, 5/60, 0.02, "PAGE_CRITICAL"),
        BurnRateAlert(0.999, 30, 6, 0.5, 0.05, "PAGE_HIGH"),
        BurnRateAlert(0.999, 30, 72, 6, 0.10, "TICKET"),
    ]

    scenarios = [
        ("正常運用",          0.0005, 0.0003),
        ("軽微なエラー増加",  0.003,  0.002),
        ("急激な障害発生",    0.02,   0.025),
    ]

    for scenario_name, err_long, err_short in scenarios:
        print(f"\n  シナリオ: {scenario_name} "
              f"(error_rate_long={err_long}, error_rate_short={err_short})")
        for alert in alerts:
            result = alert.check(err_long, err_short)
            status = "FIRING" if result["firing"] else "OK"
            print(f"    [{status}] {result['severity']}: "
                  f"burn_long={result['burn_rate_long']}, "
                  f"burn_short={result['burn_rate_short']}, "
                  f"threshold={result['threshold']}")

    print("\n[考えてほしい疑問]")
    print("  Q: 「CPU 90% 超え」のアラートは symptom-based か cause-based か？")
    print("  A: Cause-based。CPU が高くてもユーザーに影響がなければ問題ない。")
    print("     代わりに「レイテンシ p99 悪化」で検知すべき。")


# ============================================================
# 5. インシデント対応
# ============================================================
class Severity(Enum):
    SEV1 = "SEV1 — 全面障害。多数のユーザーに影響。即時対応"
    SEV2 = "SEV2 — 重大障害。主要機能が利用不可。30分以内に対応"
    SEV3 = "SEV3 — 部分障害。一部ユーザーに影響。営業時間内に対応"
    SEV4 = "SEV4 — 軽微な問題。回避策あり。計画的に対応"


@dataclass
class Incident:
    title: str
    severity: Severity
    started_at: datetime
    commander: str
    affected_services: list
    user_impact: str
    timeline: list = field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    action_items: list = field(default_factory=list)

    def add_event(self, description: str):
        self.timeline.append({
            "time": datetime.now().isoformat(),
            "event": description,
        })

    def generate_postmortem(self) -> str:
        lines = [
            "=" * 60,
            "BLAMELESS POSTMORTEM",
            "=" * 60,
            f"Title: {self.title}",
            f"Severity: {self.severity.value}",
            f"Date: {self.started_at.strftime('%Y-%m-%d %H:%M')}",
            f"Incident Commander: {self.commander}",
            f"Affected Services: {', '.join(self.affected_services)}",
            f"User Impact: {self.user_impact}",
            "",
            "--- Timeline ---",
        ]
        for entry in self.timeline:
            lines.append(f"  {entry['time']}: {entry['event']}")
        lines.extend([
            "",
            f"--- Root Cause ---",
            f"  {self.root_cause}",
            "",
            f"--- Resolution ---",
            f"  {self.resolution}",
            "",
            "--- Action Items ---",
        ])
        for i, item in enumerate(self.action_items, 1):
            lines.append(f"  {i}. [{item['priority']}] {item['action']} "
                         f"(Owner: {item['owner']}, Due: {item['due']})")
        lines.append("")
        lines.append("※ Blameless: 個人を責めず、システムの改善に焦点を当てる")
        return "\n".join(lines)


def classify_severity(error_rate: float, affected_users_pct: float,
                      revenue_impact: bool, data_loss: bool) -> Severity:
    """インシデントの重大度を自動分類する"""
    if data_loss or (error_rate > 0.5 and affected_users_pct > 80):
        return Severity.SEV1
    if revenue_impact or affected_users_pct > 50 or error_rate > 0.3:
        return Severity.SEV2
    if affected_users_pct > 10 or error_rate > 0.05:
        return Severity.SEV3
    return Severity.SEV4


def section_incident_response():
    print(f"\n{SEP}")
    print("5. インシデント対応 — 障害時に冷静に動くためのプロセス")
    print(SEP)

    print("""
■ Severity Levels（重大度レベル）
  SEV1: 全面障害。全ユーザーに影響。即座に War Room 開設
  SEV2: 重大障害。主要機能停止。30分以内に IC アサイン
  SEV3: 部分障害。一部ユーザーへの影響。営業時間内対応
  SEV4: 軽微な問題。チケットで計画対応

■ Incident Commander（IC）の役割
  - インシデント全体の指揮
  - コミュニケーションのハブ（情報を集約・配信）
  - 意思決定のボトルネックにならない（委任する）
  - タイムラインを記録する
  - 必要に応じてエスカレーション

■ War Room プロトコル
  1) IC が Slack チャンネル（#inc-YYYYMMDD-description）を作成
  2) 初期情報を投稿: 何が起きているか、影響範囲、担当者
  3) 5分ごとにステータスアップデート
  4) 外部コミュニケーション（ステータスページ更新）
  5) 解決後、ポストモーテムをスケジュール

■ コミュニケーションテンプレート
  「[SEVx] {サービス名} — {症状の要約}
   影響: {影響範囲の説明}
   現状: {調査/対応の状況}
   次のアクション: {何をするか}
   次回更新: {時刻}」
""")

    # Severity 分類デモ
    print("--- インシデント重大度分類デモ ---")
    test_cases = [
        (0.8, 90, True, False, "決済API完全停止"),
        (0.4, 60, True, False, "検索結果が部分的に空"),
        (0.08, 15, False, False, "通知遅延30分"),
        (0.01, 3, False, False, "管理画面のCSVダウンロード失敗"),
        (0.1, 5, False, True, "DBレプリカのデータ不整合"),
    ]
    for err, users, rev, data, desc in test_cases:
        sev = classify_severity(err, users, rev, data)
        print(f"  {desc}: {sev.value}")

    # ポストモーテムデモ
    print("\n--- Blameless Postmortem デモ ---")
    incident = Incident(
        title="決済サービス 30分間の全面停止",
        severity=Severity.SEV1,
        started_at=datetime(2025, 3, 15, 14, 30),
        commander="田中太郎",
        affected_services=["payment-service", "order-service", "checkout-ui"],
        user_impact="全ユーザーが決済不可。推定損失: 500万円",
    )
    incident.timeline = [
        {"time": "14:30", "event": "アラート発火: 決済API error rate > 50%"},
        {"time": "14:33", "event": "IC アサイン: 田中太郎"},
        {"time": "14:35", "event": "War Room 開設: #inc-20250315-payment"},
        {"time": "14:40", "event": "原因特定: DBコネクションプール枯渇"},
        {"time": "14:50", "event": "コネクションプールサイズを緊急拡大"},
        {"time": "15:00", "event": "サービス正常復旧を確認"},
    ]
    incident.root_cause = (
        "デプロイ時の設定変更で DB コネクションプールの max_size が "
        "100 → 5 に誤って変更された（config typo）"
    )
    incident.resolution = "コネクションプールサイズを 100 に復旧"
    incident.action_items = [
        {"priority": "P0", "action": "設定変更の自動バリデーション導入",
         "owner": "infra-team", "due": "2025-03-22"},
        {"priority": "P1", "action": "コネクションプール監視アラート追加",
         "owner": "sre-team", "due": "2025-03-29"},
        {"priority": "P2", "action": "設定変更の Canary デプロイ対応",
         "owner": "platform-team", "due": "2025-04-15"},
    ]
    print(incident.generate_postmortem())


# ============================================================
# 6. カオスエンジニアリング
# ============================================================
@dataclass
class ChaosExperiment:
    name: str
    hypothesis: str
    steady_state: dict
    method: str
    blast_radius: str
    rollback_plan: str
    duration_minutes: int

    def plan(self) -> str:
        lines = [
            f"  実験名: {self.name}",
            f"  仮説: {self.hypothesis}",
            f"  定常状態: {json.dumps(self.steady_state, ensure_ascii=False)}",
            f"  手法: {self.method}",
            f"  影響範囲: {self.blast_radius}",
            f"  ロールバック: {self.rollback_plan}",
            f"  実行時間: {self.duration_minutes}分",
        ]
        return "\n".join(lines)


def section_chaos_engineering():
    print(f"\n{SEP}")
    print("6. カオスエンジニアリング — 障害を意図的に起こして強くなる")
    print(SEP)

    print("""
■ 原則（Principles of Chaos Engineering）
  1) 定常状態の仮説を立てる（Steady State Hypothesis）
  2) 本番環境に近い環境で実験する（理想は本番）
  3) 影響範囲を限定する（Blast Radius Control）
  4) 自動で停止できるようにする（Safety Net）
  5) 結果を計測・分析する

■ 代表的なツール
  - Chaos Monkey (Netflix): ランダムにインスタンスを停止
  - Litmus Chaos (CNCF): Kubernetes ネイティブ
  - Gremlin: SaaS 型、GUI で操作
  - AWS Fault Injection Simulator: AWS サービス統合

■ GameDay
  組織全体でカオス実験を実施するイベント。
  手順:
    1) 対象サービスと仮説を事前に定義
    2) 観測体制を整える（ダッシュボード、オンコール）
    3) 実験を実行（段階的にスコープを広げる）
    4) 結果を記録
    5) 振り返りと改善アクション

■ 実験の段階
  Level 1: 開発環境での単一障害注入
  Level 2: ステージング環境でのマルチ障害
  Level 3: 本番の一部トラフィックに対する障害注入
  Level 4: 本番全体での大規模 GameDay
""")

    print("--- カオス実験計画デモ ---")
    experiments = [
        ChaosExperiment(
            name="API Gateway 単一インスタンス停止",
            hypothesis="ALB が自動的にヘルシーなインスタンスにルーティングし、"
                       "エラー率は 0.1% 未満を維持する",
            steady_state={"error_rate": "< 0.1%", "p99_latency": "< 500ms"},
            method="1台のEC2インスタンスを terminate",
            blast_radius="API Gateway の 1/6 のキャパシティ",
            rollback_plan="ASG が自動で新インスタンスを起動。手動復旧不要",
            duration_minutes=30,
        ),
        ChaosExperiment(
            name="データベース フェイルオーバー",
            hypothesis="RDS のフェイルオーバーが 30秒以内に完了し、"
                       "アプリケーションが自動再接続する",
            steady_state={"db_connection_errors": "0", "write_availability": "100%"},
            method="RDS reboot with failover",
            blast_radius="全書き込みが一時停止（読み取りはレプリカで継続）",
            rollback_plan="フェイルオーバー完了を待つ。失敗時は手動で元プライマリに切替",
            duration_minutes=15,
        ),
    ]
    for exp in experiments:
        print(exp.plan())
        print()

    print("[実装してみよう]")
    print("  1. 自分のサービスの「定常状態」を3つ定義してみよう")
    print("  2. 最もインパクトの大きい障害シナリオを1つ選び、実験計画を書こう")


# ============================================================
# 7. キャパシティプランニング
# ============================================================
@dataclass
class CapacityModel:
    """キャパシティプランニングモデル"""
    current_rps: float            # 現在の RPS
    monthly_growth_rate: float    # 月次成長率（例: 0.05 = 5%）
    planned_events: list          # 計画イベント [{month: int, multiplier: float}]
    instance_capacity_rps: float  # 1インスタンスあたりの処理能力
    current_instances: int

    def forecast(self, months: int = 12) -> list:
        results = []
        for m in range(1, months + 1):
            organic_rps = self.current_rps * ((1 + self.monthly_growth_rate) ** m)
            event_mult = 1.0
            for evt in self.planned_events:
                if evt["month"] == m:
                    event_mult = max(event_mult, evt["multiplier"])
            peak_rps = organic_rps * event_mult

            # N+1 冗長性: 1台故障しても耐えられる台数
            min_instances = math.ceil(peak_rps / self.instance_capacity_rps)
            n_plus_1 = min_instances + 1
            # N+2 冗長性: 2台故障 + デプロイ中の余裕
            n_plus_2 = min_instances + 2
            headroom_pct = ((n_plus_1 * self.instance_capacity_rps - peak_rps)
                           / (n_plus_1 * self.instance_capacity_rps)) * 100

            results.append({
                "month": m,
                "organic_rps": round(organic_rps, 1),
                "peak_rps": round(peak_rps, 1),
                "min_instances": min_instances,
                "n_plus_1": n_plus_1,
                "n_plus_2": n_plus_2,
                "headroom_pct": round(headroom_pct, 1),
            })
        return results


def section_capacity_planning():
    print(f"\n{SEP}")
    print("7. キャパシティプランニング — 将来の需要に備える")
    print(SEP)

    print("""
■ キャパシティプランニングの要素
  1) Organic Growth: 自然なトラフィック成長
  2) Planned Events: セール、キャンペーン、新機能リリース
  3) Inorganic Growth: 新規パートナー、M&A
  4) Headroom: 余裕（想定外のスパイク対応）

■ リソースヘッドルーム戦略
  N+1: 1台故障しても処理可能
  N+2: 2台故障 or デプロイ中でも安全
  一般的に 30-50% の余裕を持つ

■ 負荷テスト手法
  1) Load Test: 予想される負荷での動作確認
  2) Stress Test: 限界まで負荷をかけてブレイクポイントを特定
  3) Soak Test: 長時間の負荷でメモリリークなどを検出
  4) Spike Test: 急激な負荷増加への耐性確認

■ ツール
  - k6 (Grafana Labs): JavaScript でシナリオ記述
  - Locust: Python ベース
  - Gatling: Scala/Java ベース
  - wrk / wrk2: 軽量 HTTP ベンチマーク
""")

    print("--- キャパシティ予測デモ ---")
    model = CapacityModel(
        current_rps=1000,
        monthly_growth_rate=0.08,
        planned_events=[
            {"month": 3, "multiplier": 2.5, "name": "春セール"},
            {"month": 6, "multiplier": 1.5, "name": "新機能リリース"},
            {"month": 12, "multiplier": 3.0, "name": "年末セール"},
        ],
        instance_capacity_rps=250,
        current_instances=6,
    )

    forecast = model.forecast(12)
    print(f"  現在: {model.current_rps} RPS, {model.current_instances} instances")
    print(f"  成長率: 月 {model.monthly_growth_rate*100}%")
    print(f"  インスタンス処理能力: {model.instance_capacity_rps} RPS/台")
    print()
    print(f"  {'月':>3} {'通常RPS':>10} {'ピークRPS':>10} {'最小台数':>8} "
          f"{'N+1':>5} {'N+2':>5} {'余裕':>6}")
    print(f"  {'─'*3} {'─'*10} {'─'*10} {'─'*8} {'─'*5} {'─'*5} {'─'*6}")

    for r in forecast:
        print(f"  {r['month']:>3} {r['organic_rps']:>10} {r['peak_rps']:>10} "
              f"{r['min_instances']:>8} {r['n_plus_1']:>5} {r['n_plus_2']:>5} "
              f"{r['headroom_pct']:>5}%")


# ============================================================
# 8. Prometheus + Grafana
# ============================================================
class PromQLBuilder:
    """PromQL クエリビルダー"""

    @staticmethod
    def error_rate(job: str, window: str = "5m") -> str:
        return (
            f'sum(rate(http_requests_total{{job="{job}",status=~"5.."}}[{window}]))\n'
            f'  / sum(rate(http_requests_total{{job="{job}"}}[{window}]))'
        )

    @staticmethod
    def latency_percentile(job: str, percentile: float = 0.99,
                           window: str = "5m") -> str:
        return (
            f'histogram_quantile({percentile},\n'
            f'  sum(rate(http_request_duration_seconds_bucket'
            f'{{job="{job}"}}[{window}])) by (le)\n'
            f')'
        )

    @staticmethod
    def saturation_cpu(instance: str = ".*", window: str = "5m") -> str:
        return (
            f'1 - avg(rate(node_cpu_seconds_total'
            f'{{mode="idle",instance=~"{instance}"}}[{window}]))'
        )

    @staticmethod
    def request_rate(job: str, window: str = "5m") -> str:
        return f'sum(rate(http_requests_total{{job="{job}"}}[{window}]))'

    @staticmethod
    def memory_usage(instance: str = ".*") -> str:
        return (
            f'1 - (node_memory_MemAvailable_bytes{{instance=~"{instance}"}}\n'
            f'  / node_memory_MemTotal_bytes{{instance=~"{instance}"}})'
        )

    @staticmethod
    def burn_rate_alert(job: str, slo: float, long_window: str,
                        short_window: str, burn_rate: float) -> str:
        error_budget = 1 - slo
        threshold = error_budget * burn_rate
        return (
            f'# Burn Rate Alert: SLO={slo*100}%, threshold={burn_rate}x\n'
            f'(\n'
            f'  sum(rate(http_requests_total{{job="{job}",status=~"5.."}}[{long_window}]))\n'
            f'  / sum(rate(http_requests_total{{job="{job}"}}[{long_window}]))\n'
            f'  > {threshold}\n'
            f')\n'
            f'and\n'
            f'(\n'
            f'  sum(rate(http_requests_total{{job="{job}",status=~"5.."}}[{short_window}]))\n'
            f'  / sum(rate(http_requests_total{{job="{job}"}}[{short_window}]))\n'
            f'  > {threshold}\n'
            f')'
        )

    @staticmethod
    def recording_rule(record_name: str, expr: str, interval: str = "5m") -> str:
        """Recording Rule の YAML 表現"""
        return (
            f'# Recording Rule\n'
            f'- record: {record_name}\n'
            f'  expr: |\n'
            f'    {expr}\n'
            f'  # evaluation_interval: {interval}'
        )


def section_prometheus_grafana():
    print(f"\n{SEP}")
    print("8. Prometheus + Grafana — 監視基盤の定番スタック")
    print(SEP)

    print("""
■ Prometheus アーキテクチャ
  - Pull 型: 各サービスの /metrics エンドポイントをスクレイプ
  - TSDB: 時系列データベース（ローカルストレージ）
  - PromQL: 強力なクエリ言語
  - AlertManager: アラートのルーティング・グルーピング

■ PromQL の基本
  - Instant Vector: ある時点の値（http_requests_total）
  - Range Vector: 時間範囲の値（http_requests_total[5m]）
  - rate(): 毎秒の増加率を計算
  - histogram_quantile(): パーセンタイル計算
  - sum() by (label): ラベル別の集計

■ Recording Rules
  頻繁に使うクエリを事前計算して保存する。
  - ダッシュボードの読み込み高速化
  - アラートルールの簡潔化

■ Federation
  大規模環境での Prometheus の階層化。
  Global Prometheus → Regional Prometheus → Service Prometheus
""")

    builder = PromQLBuilder()

    queries = [
        ("エラー率 (5xx / total)", builder.error_rate("api-gateway")),
        ("p99 レイテンシ", builder.latency_percentile("api-gateway")),
        ("CPU 使用率", builder.saturation_cpu()),
        ("リクエストレート", builder.request_rate("api-gateway")),
        ("メモリ使用率", builder.memory_usage()),
    ]

    print("--- よく使う PromQL クエリ集 ---")
    for name, query in queries:
        print(f"\n  [{name}]")
        for line in query.strip().split("\n"):
            print(f"    {line}")

    # Burn Rate Alert
    print("\n--- Burn Rate Alert PromQL ---")
    alert_query = builder.burn_rate_alert(
        job="payment-service", slo=0.999,
        long_window="1h", short_window="5m", burn_rate=14.4,
    )
    for line in alert_query.split("\n"):
        print(f"    {line}")

    # Recording Rule
    print("\n--- Recording Rule 例 ---")
    rule = builder.recording_rule(
        "job:http_error_rate:ratio_rate5m",
        builder.error_rate("api-gateway"),
    )
    for line in rule.split("\n"):
        print(f"    {line}")

    print("\n[考えてほしい疑問]")
    print("  Q: rate() と irate() の違いは？")
    print("  A: rate() は Range Vector 全体の平均増加率。アラート向き。")
    print("     irate() は直近2点間の瞬間増加率。グラフ表示向き。")


# ============================================================
# 9. 分散トレーシング
# ============================================================
@dataclass
class TraceContext:
    """W3C TraceContext 準拠のコンテキスト"""
    version: str = "00"
    trace_id: str = ""
    parent_id: str = ""
    trace_flags: str = "01"  # 01 = sampled

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = generate_trace_id()
        if not self.parent_id:
            self.parent_id = generate_span_id()

    def to_traceparent(self) -> str:
        return f"{self.version}-{self.trace_id}-{self.parent_id}-{self.trace_flags}"

    @classmethod
    def from_traceparent(cls, header: str) -> "TraceContext":
        parts = header.split("-")
        return cls(
            version=parts[0],
            trace_id=parts[1],
            parent_id=parts[2],
            trace_flags=parts[3],
        )

    def create_child(self) -> "TraceContext":
        return TraceContext(
            version=self.version,
            trace_id=self.trace_id,
            parent_id=generate_span_id(),
            trace_flags=self.trace_flags,
        )


class SamplingStrategy(Enum):
    ALWAYS_ON = "always_on"
    ALWAYS_OFF = "always_off"
    PROBABILITY = "probability"
    RATE_LIMITING = "rate_limiting"
    TAIL_BASED = "tail_based"


@dataclass
class Sampler:
    strategy: SamplingStrategy
    param: float = 1.0  # probability の場合は確率、rate の場合は RPS

    def should_sample(self, trace_id: str, duration_ms: float = 0,
                      has_error: bool = False) -> bool:
        if self.strategy == SamplingStrategy.ALWAYS_ON:
            return True
        elif self.strategy == SamplingStrategy.ALWAYS_OFF:
            return False
        elif self.strategy == SamplingStrategy.PROBABILITY:
            # trace_id ベースで決定論的にサンプリング
            hash_val = int(hashlib.md5(trace_id.encode()).hexdigest()[:8], 16)
            return (hash_val / 0xFFFFFFFF) < self.param
        elif self.strategy == SamplingStrategy.TAIL_BASED:
            # エラーや高レイテンシのトレースは必ず保存
            if has_error:
                return True
            if duration_ms > self.param:
                return True
            return random.random() < 0.01  # ベースライン 1%
        return True


def section_distributed_tracing():
    print(f"\n{SEP}")
    print("9. 分散トレーシング — リクエストの旅路を追う")
    print(SEP)

    print("""
■ OpenTelemetry (OTel) アーキテクチャ
  SDK (計装) → Collector (収集・加工) → Backend (保存・可視化)

  SDK 層:
    - Auto-instrumentation: フレームワーク自動計装
    - Manual instrumentation: カスタム Span の追加
    - Context Propagation: サービス間でトレース ID を伝播

  Collector 層:
    - Receivers: データ受信（OTLP, Jaeger, Zipkin 形式）
    - Processors: フィルタリング、バッチ処理、サンプリング
    - Exporters: バックエンドへ送信

■ W3C TraceContext
  HTTP ヘッダー `traceparent` でコンテキストを伝播:
    traceparent: 00-{trace_id}-{parent_id}-{trace_flags}
    例: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

■ サンプリング戦略
  Head-based Sampling:
    - リクエスト開始時にサンプリング決定
    - 実装が簡単、オーバーヘッドが低い
    - 問題: エラーのトレースを見逃す可能性

  Tail-based Sampling:
    - リクエスト完了後にサンプリング決定
    - エラーや高レイテンシを確実にキャプチャ
    - 問題: 全 Span を一時保持する必要がありリソース消費大

■ バックエンド比較
  Jaeger:
    - CNCF 卒業プロジェクト
    - Elasticsearch / Cassandra をストレージに使用
    - 成熟した UI

  Grafana Tempo:
    - ログと連携が強い（Loki + Tempo）
    - オブジェクトストレージ（S3）で低コスト
    - TraceQL でトレース検索

  AWS X-Ray:
    - AWS サービスとのネイティブ統合
    - Lambda, ECS, EKS との連携が容易
    - サービスマップ自動生成
""")

    # TraceContext デモ
    print("--- W3C TraceContext デモ ---")
    ctx = TraceContext()
    print(f"  traceparent: {ctx.to_traceparent()}")

    child = ctx.create_child()
    print(f"  child span:  {child.to_traceparent()}")
    print(f"  同じ trace_id: {ctx.trace_id == child.trace_id}")

    parsed = TraceContext.from_traceparent(ctx.to_traceparent())
    print(f"  parsed trace_id: {parsed.trace_id}")

    # サンプリングデモ
    print("\n--- サンプリング戦略比較 ---")
    samplers = [
        Sampler(SamplingStrategy.ALWAYS_ON),
        Sampler(SamplingStrategy.PROBABILITY, 0.1),
        Sampler(SamplingStrategy.TAIL_BASED, 500),  # 500ms 以上は必ず保存
    ]

    test_traces = []
    for _ in range(1000):
        tid = generate_trace_id()
        dur = random.expovariate(1/200)  # 平均 200ms
        err = random.random() < 0.02     # 2% エラー
        test_traces.append((tid, dur, err))

    for sampler in samplers:
        sampled = sum(1 for tid, dur, err in test_traces
                      if sampler.should_sample(tid, dur, err))
        errors_sampled = sum(1 for tid, dur, err in test_traces
                             if err and sampler.should_sample(tid, dur, err))
        total_errors = sum(1 for _, _, err in test_traces if err)
        print(f"\n  Strategy: {sampler.strategy.value} (param={sampler.param})")
        print(f"    サンプル数: {sampled}/1000 ({sampled/10:.1f}%)")
        print(f"    エラー捕捉: {errors_sampled}/{total_errors} "
              f"({errors_sampled/max(total_errors,1)*100:.0f}%)")

    print("\n[考えてほしい疑問]")
    print("  Q: Tail-based sampling はなぜ Head-based より高コストか？")
    print("  A: 全 Span をメモリに一時保持してリクエスト完了を待つ必要があるため。")
    print("     Collector のメモリ消費が大きく、高トラフィック環境では課題になる。")


# ============================================================
# 10. 面接問題
# ============================================================
def section_interview_question():
    print(f"\n{SEP}")
    print("10. 面接問題: p99 レイテンシが 200ms → 2s に悪化")
    print(SEP)

    print("""
■ 問題
  "Your service's p99 latency increased from 200ms to 2s.
   Walk through your debugging process."

■ 模範回答の構造（5ステップ）

Step 1: 影響範囲の確認（1-2分）
  - p99 だけか？ p50, p95 も悪化しているか？
    → p50 も悪化: 全体的な問題（DB, 外部依存）
    → p99 だけ悪化: テールレイテンシ問題（GC, 特定パス）
  - どのエンドポイントが影響を受けているか？
  - いつから悪化したか？（変更との相関）
  - 影響を受けるユーザーの割合は？

Step 2: 変更の相関（2-3分）
  - デプロイ履歴を確認（デプロイと時刻が一致するか？）
  - 設定変更はあったか？
  - インフラ変更（スケーリング、ネットワーク）はあったか？
  - 依存サービスの変更は？
  - トラフィックパターンの変化は？

Step 3: リソース分析（3-5分）
  USE Method でインフラを確認:
  - CPU 使用率・飽和度
  - メモリ使用率（GC の頻度・停止時間）
  - ディスク I/O（特にキュー長）
  - ネットワーク（パケットロス、帯域）

  RED Method でアプリケーションを確認:
  - リクエストレート（急増していないか？）
  - エラー率（タイムアウト、5xx）
  - レイテンシ分布（特定のパスだけ遅い？）

Step 4: 依存関係の調査（3-5分）
  分散トレーシングで遅い Span を特定:
  - データベースクエリが遅い？（スロークエリログ確認）
  - 外部 API のレスポンスが遅い？
  - キャッシュヒット率が低下？
  - コネクションプール枯渇？
  - ロック競合？

Step 5: 仮説と対応（2-3分）
  よくある原因パターン:
  a) DB: N+1 クエリ、インデックス欠落、ロック競合
  b) GC: メモリリーク、ヒープ不足
  c) 外部依存: タイムアウト設定不適切、サーキットブレーカー未設定
  d) リソース: コネクションプール不足、スレッドプール飽和
  e) トラフィック: 予期しない負荷増加

  緩和策:
  - 即座: ロールバック（デプロイが原因の場合）
  - 短期: リソース追加、タイムアウト調整
  - 中期: クエリ最適化、キャッシュ追加
  - 長期: アーキテクチャ改善
""")

    print("[考えてほしい疑問]")
    print("  Q: p50 は正常で p99 だけ悪化している場合、何を疑う？")
    print("  A: GC の Stop-the-World、特定パスの分岐（重い処理への条件分岐）、")
    print("     外部依存の間欠的なタイムアウト、リソース競合（ロック）")

    # レイテンシ分析シミュレーション
    print("\n--- レイテンシ分析シミュレーション ---")
    print("  正常時と異常時のレイテンシ分布を比較:\n")

    random.seed(42)
    # 正常分布
    normal = sorted([random.gauss(100, 30) for _ in range(1000)])
    # 異常分布（バイモーダル: 通常 + 遅いリクエスト）
    abnormal = sorted([
        random.gauss(100, 30) if random.random() > 0.05
        else random.gauss(1800, 200)
        for _ in range(1000)
    ])

    def percentile(data, p):
        idx = int(len(data) * p)
        return data[min(idx, len(data) - 1)]

    print(f"  {'':>12} {'p50':>8} {'p90':>8} {'p95':>8} {'p99':>8} {'max':>8}")
    print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    for label, data in [("正常時", normal), ("異常時", abnormal)]:
        p50 = percentile(data, 0.50)
        p90 = percentile(data, 0.90)
        p95 = percentile(data, 0.95)
        p99 = percentile(data, 0.99)
        mx = max(data)
        print(f"  {label:>12} {p50:>7.0f}ms {p90:>7.0f}ms "
              f"{p95:>7.0f}ms {p99:>7.0f}ms {mx:>7.0f}ms")

    print("\n  → 異常時は p99 だけが大幅に悪化。5% のリクエストが外れ値。")
    print("    これは特定条件（キャッシュミス、重いクエリ）での劣化パターン。")


# ============================================================
# SLO Burn Rate Calculator（統合ツール）
# ============================================================
class SLOBurnRateCalculator:
    """
    Google SRE Workbook 準拠の Burn Rate 計算機。
    複数ウィンドウのアラート設定を自動生成する。
    """

    STANDARD_WINDOWS = [
        {"long_h": 1,   "short_h": 5/60,  "budget_pct": 0.02, "severity": "PAGE_CRITICAL"},
        {"long_h": 6,   "short_h": 0.5,   "budget_pct": 0.05, "severity": "PAGE_HIGH"},
        {"long_h": 24,  "short_h": 2,     "budget_pct": 0.10, "severity": "PAGE_MEDIUM"},
        {"long_h": 72,  "short_h": 6,     "budget_pct": 0.10, "severity": "TICKET"},
    ]

    def __init__(self, slo_target: float, window_days: int = 30):
        self.slo_target = slo_target
        self.window_days = window_days
        self.error_budget = 1.0 - slo_target
        self.total_hours = window_days * 24

    def compute_burn_rates(self) -> list:
        results = []
        for w in self.STANDARD_WINDOWS:
            burn_rate = (self.total_hours / w["long_h"]) * w["budget_pct"]
            error_threshold = self.error_budget * burn_rate
            detection_time_h = w["long_h"]
            budget_consumed_at_detection = w["budget_pct"] * 100
            results.append({
                "severity": w["severity"],
                "long_window": f"{w['long_h']}h",
                "short_window": f"{w['short_h']*60:.0f}m" if w['short_h'] < 1
                                else f"{w['short_h']}h",
                "burn_rate": round(burn_rate, 1),
                "error_rate_threshold": f"{error_threshold*100:.4f}%",
                "detection_time": f"{detection_time_h}h",
                "budget_consumed": f"{budget_consumed_at_detection:.0f}%",
            })
        return results

    def summary(self) -> str:
        lines = [
            f"SLO: {self.slo_target*100:.3f}% | "
            f"Error Budget: {self.error_budget*100:.3f}% | "
            f"Window: {self.window_days} days",
            f"Budget in minutes: {self.error_budget * self.total_hours * 60:.1f} min",
            "",
            f"{'Severity':<18} {'Long':>6} {'Short':>6} {'Burn':>6} "
            f"{'ErrThresh':>12} {'Detect':>8} {'Budget%':>8}",
            "─" * 70,
        ]
        for r in self.compute_burn_rates():
            lines.append(
                f"{r['severity']:<18} {r['long_window']:>6} "
                f"{r['short_window']:>6} {r['burn_rate']:>5}x "
                f"{r['error_rate_threshold']:>12} {r['detection_time']:>8} "
                f"{r['budget_consumed']:>8}"
            )
        return "\n".join(lines)


def section_integrated_tools():
    print(f"\n{SEP}")
    print("統合ツール: SLO Burn Rate Calculator")
    print(SEP)

    for slo in [0.999, 0.9995, 0.9999]:
        calc = SLOBurnRateCalculator(slo, window_days=30)
        print(f"\n{calc.summary()}\n")

    print("[実装してみよう]")
    print("  1. 自分のサービスの SLO を設定し、Burn Rate アラートを設計せよ")
    print("  2. PromQLBuilder を拡張して、Recording Rule を自動生成せよ")
    print("  3. Incident クラスに Slack 通知テンプレートを追加せよ")
    print("  4. CapacityModel にコスト計算（1台あたりの月額コスト）を追加せよ")
    print("  5. ChaosExperiment の結果を記録する仕組みを実装せよ")


# ============================================================
# まとめ
# ============================================================
def section_summary():
    print(f"\n{SEP}")
    print("まとめ: SRE の全体像")
    print(SEP)

    print("""
■ SRE は「信頼性をエンジニアリングする」ディシプリン

  基盤:
    SLI/SLO/SLA → 信頼性を定量化
    Error Budget → リリース速度と信頼性のバランス

  観測:
    Metrics (USE/RED) → 何が起きているか
    Logs (構造化)     → 何が起きたか
    Traces (分散)     → どう流れたか

  対応:
    アラート設計 (Burn Rate) → いつ人間を呼ぶか
    インシデント対応          → どう対処するか
    ポストモーテム            → どう学ぶか

  改善:
    カオスエンジニアリング → 事前に弱点を見つける
    キャパシティプランニング → 未来に備える
    Toil 削減              → 自動化で時間を作る

■ FAANG で求められる SRE の姿勢
  - 「動いている」は「信頼できる」を意味しない
  - 数値で語れないものは改善できない
  - 障害は起きる前提で設計する
  - 人を責めず、システムを改善する
  - 自動化は投資、手作業は負債
""")


# ============================================================
# メイン
# ============================================================
def main():
    print("=" * 60)
    print("  FAANG レベル SRE & 可観測性 実践ガイド")
    print("  Site Reliability Engineering — 信頼性をエンジニアリングする")
    print("=" * 60)

    section_sre_fundamentals()
    section_sli_slo_sla()
    section_observability_pillars()
    section_alert_design()
    section_incident_response()
    section_chaos_engineering()
    section_capacity_planning()
    section_prometheus_grafana()
    section_distributed_tracing()
    section_interview_question()
    section_integrated_tools()
    section_summary()

    print(f"\n{SEP}")
    print("学習完了。次のステップ:")
    print("  1. 自分のサービスで SLI/SLO を定義してみる")
    print("  2. 構造化ログを導入する")
    print("  3. Prometheus + Grafana のダッシュボードを作る")
    print("  4. 最初のカオス実験を計画する")
    print(SEP)


if __name__ == "__main__":
    main()
