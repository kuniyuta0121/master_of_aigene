"""
Phase PM: テクニカルPM・リーダーシップ完全ガイド
=================================================
学習目標:
  - FAANG PM/テックリード面接で必要なフレームワークを実装で理解する
  - プロダクトディスカバリー・戦略・メトリクスを数値で語れるようになる
  - アジャイル/スクラムを「儀式」でなく「原理」から理解する
  - テクニカルリーダーシップの実践的スキルを身につける

考えてほしい疑問:
  Q1. PMとエンジニアの「良い判断」の違いは何か？（技術最適 vs ビジネス最適）
  Q2. OKRとKPIの違いは？OKRの達成率70%が理想な理由は？
  Q3. 「ユーザーが欲しいと言ったもの」を作るのはなぜ危険か？
  Q4. Tech Debtを「返済しない」という判断が正しい場合はあるか？
  Q5. 10人のチームと100人の組織で、意思決定の方法はどう変わるべきか？

実行方法:
  python tech_pm_leadership.py
  # 依存: 標準ライブラリのみ
"""

from __future__ import annotations

import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Optional


# === ユーティリティ ===

def section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def subsection(title: str) -> None:
    print(f"\n  -- {title} --\n")

def demo(text: str) -> None:
    print(f"    {text}")

def point(text: str) -> None:
    print(f"    > {text}")


# =====================================================================
# Chapter 1: アジャイル・スクラム実践
# =====================================================================

def chapter_1_agile():
    section("Chapter 1: アジャイル・スクラム実践")

    # ── 1.1 Sprint Planning シミュレーション ──
    subsection("1.1 Sprint Planning シミュレーション")

    @dataclass
    class UserStory:
        id: str
        title: str
        story_points: int
        priority: int  # 1=highest
        acceptance_criteria: list[str] = field(default_factory=list)

    @dataclass
    class Sprint:
        number: int
        capacity: int  # story points
        stories: list[UserStory] = field(default_factory=list)
        velocity_history: list[int] = field(default_factory=list)

        @property
        def committed_points(self) -> int:
            return sum(s.story_points for s in self.stories)

        @property
        def avg_velocity(self) -> float:
            if not self.velocity_history:
                return self.capacity
            return statistics.mean(self.velocity_history)

        def plan(self, backlog: list[UserStory]) -> list[UserStory]:
            """ベロシティに基づいてスプリントに入れるストーリーを選択"""
            target = min(self.capacity, int(self.avg_velocity * 1.1))
            sorted_backlog = sorted(backlog, key=lambda s: s.priority)
            for story in sorted_backlog:
                if self.committed_points + story.story_points <= target:
                    self.stories.append(story)
            return self.stories

    backlog = [
        UserStory("US-1", "ユーザー登録画面", 5, 1,
                  ["Given 未登録ユーザー When メール入力 Then 確認メール送信"]),
        UserStory("US-2", "ログイン機能", 3, 1,
                  ["Given 登録済みユーザー When 正しいPW Then ダッシュボード表示"]),
        UserStory("US-3", "プロフィール編集", 2, 2),
        UserStory("US-4", "通知設定", 3, 2),
        UserStory("US-5", "検索機能", 8, 3),
        UserStory("US-6", "お気に入り機能", 3, 3),
        UserStory("US-7", "CSV エクスポート", 5, 4),
    ]

    sprint = Sprint(number=5, capacity=15, velocity_history=[12, 14, 11, 13])
    planned = sprint.plan(backlog)

    demo(f"Sprint #{sprint.number}")
    demo(f"  チーム平均ベロシティ: {sprint.avg_velocity:.1f} pts")
    demo(f"  今回のコミット: {sprint.committed_points} pts")
    for s in planned:
        demo(f"    [{s.id}] {s.title} ({s.story_points}pt) P{s.priority}")

    point("ベロシティは予測ツールであり、パフォーマンス指標ではない")
    point("コミットは avg_velocity ± 10% を目安にする")

    # ── 1.2 Burndown Chart (ASCII) ──
    subsection("1.2 Sprint Burndown Chart")

    total_pts = sprint.committed_points
    days = 10
    # シミュレーション: 理想線 vs 実績
    ideal = [total_pts * (1 - i/days) for i in range(days+1)]
    random.seed(42)
    actual = [total_pts]
    for i in range(1, days+1):
        burned = random.choice([0, 1, 2, 2, 3]) if i < days else actual[-1]
        actual.append(max(0, actual[-1] - burned))

    demo("Burndown Chart (Sprint #{})".format(sprint.number))
    demo(f"{'Day':>5} | {'Ideal':>6} | {'Actual':>6} | Chart")
    max_bar = 30
    for d in range(days+1):
        i_bar = int(ideal[d] / total_pts * max_bar)
        a_bar = int(actual[d] / total_pts * max_bar)
        chart = ""
        for p in range(max_bar):
            if p < min(i_bar, a_bar):
                chart += "="  # both
            elif p < a_bar:
                chart += "#"  # actual above ideal (behind)
            elif p < i_bar:
                chart += "-"  # ideal above actual (ahead)
            else:
                chart += " "
        demo(f"  {d:>3} | {ideal[d]:>5.1f} | {actual[d]:>5.0f}  | [{chart}]")

    point("Burndown が理想線より上 = 遅延リスク → スコープ調整を検討")
    point("毎日の差異ではなく「トレンド」を見る")

    # ── 1.3 Kanban vs Scrum ──
    subsection("1.3 Kanban vs Scrum 比較")

    comparison = {
        "イテレーション": ("固定Sprint(1-4週)", "連続フロー"),
        "計画": ("Sprint Planning", "必要時にPull"),
        "WIP制限": ("Sprint容量で暗黙的", "列ごとに明示的"),
        "役割": ("PO/SM/Dev 明確", "必須役割なし"),
        "変更": ("Sprint中は原則不可", "いつでもOK"),
        "メトリクス": ("ベロシティ", "リードタイム/サイクルタイム"),
        "適する場面": ("新規開発・チーム形成期", "運用・保守・サポート"),
    }

    demo(f"{'項目':<15} {'Scrum':<30} {'Kanban':<30}")
    demo("-" * 75)
    for item, (scrum, kanban) in comparison.items():
        demo(f"{item:<15} {scrum:<30} {kanban:<30}")

    # ── 1.4 WIP制限の効果シミュレーション ──
    subsection("1.4 WIP制限の効果シミュレーション")

    def simulate_flow(wip_limit: int, tasks: int = 20, steps: int = 50) -> dict:
        """WIP制限がリードタイムに与える影響をシミュレート"""
        random.seed(123)
        queue: list[int] = list(range(tasks))  # 待機タスク
        in_progress: list[tuple[int, int]] = []  # (task_id, remaining_work)
        completed: list[tuple[int, int]] = []  # (task_id, completion_step)
        start_times: dict[int, int] = {}

        for step in range(steps):
            # 進行中タスクを進める
            new_in_progress = []
            for task_id, remaining in in_progress:
                remaining -= 1
                if remaining <= 0:
                    completed.append((task_id, step))
                else:
                    new_in_progress.append((task_id, remaining))
            in_progress = new_in_progress

            # WIP制限内で新タスクを開始
            while queue and len(in_progress) < wip_limit:
                task_id = queue.pop(0)
                work = random.randint(2, 6)
                in_progress.append((task_id, work))
                start_times[task_id] = step

        lead_times = [comp_step - start_times[tid]
                      for tid, comp_step in completed if tid in start_times]
        return {
            "wip_limit": wip_limit,
            "completed": len(completed),
            "avg_lead_time": statistics.mean(lead_times) if lead_times else 0,
            "max_lead_time": max(lead_times) if lead_times else 0,
        }

    demo(f"{'WIP制限':>8} | {'完了数':>6} | {'平均リードタイム':>14} | {'最大':>6}")
    demo("-" * 50)
    for wip in [2, 3, 5, 10, 20]:
        result = simulate_flow(wip)
        demo(f"  {result['wip_limit']:>5}   | {result['completed']:>5}  | "
             f"{result['avg_lead_time']:>12.1f}  | {result['max_lead_time']:>5}")

    point("WIP制限が小さすぎると完了数が減り、大きすぎるとリードタイムが増大")
    point("Little's Law: リードタイム = WIP / スループット")

    # ── 1.5 User Story テンプレート ──
    subsection("1.5 User Story / Acceptance Criteria テンプレート")

    demo("■ User Story フォーマット:")
    demo("  As a [ペルソナ],")
    demo("  I want [機能],")
    demo("  So that [ビジネス価値].")
    demo("")
    demo("■ Acceptance Criteria (Given-When-Then):")
    demo("  Given [前提条件],")
    demo("  When [アクション],")
    demo("  Then [期待結果].")
    demo("")
    demo("■ INVEST チェックリスト:")
    for item in ["Independent（独立している）", "Negotiable（交渉可能）",
                 "Valuable（価値がある）", "Estimable（見積もれる）",
                 "Small（小さい）", "Testable（テスト可能）"]:
        demo(f"  [x] {item}")

    demo("")
    demo("■ Definition of Done:")
    for item in ["コードレビュー完了", "単体テストカバレッジ80%以上",
                 "結合テスト通過", "ドキュメント更新", "QA検証完了",
                 "PO承認", "staging環境で動作確認"]:
        demo(f"  [ ] {item}")

    point("[実装してみよう] 自分のプロジェクトの機能を3つ、User Story形式で書いてみよう")


# =====================================================================
# Chapter 2: プロダクトディスカバリー
# =====================================================================

def chapter_2_discovery():
    section("Chapter 2: プロダクトディスカバリー")

    # ── 2.1 RICE スコアリング ──
    subsection("2.1 RICE スコアリング")

    @dataclass
    class Feature:
        name: str
        reach: int        # 影響ユーザー数/四半期
        impact: float     # 0.25=最小, 0.5=低, 1=中, 2=高, 3=最大
        confidence: float # 0-100%
        effort: float     # 人月

        @property
        def rice_score(self) -> float:
            return (self.reach * self.impact * self.confidence) / self.effort

    features = [
        Feature("検索フィルター改善", 5000, 2.0, 0.8, 2),
        Feature("ダークモード", 3000, 0.5, 0.9, 1),
        Feature("AI レコメンド", 8000, 3.0, 0.5, 6),
        Feature("CSV エクスポート", 1000, 1.0, 1.0, 0.5),
        Feature("モバイルアプリ", 10000, 2.0, 0.6, 12),
        Feature("2FA 認証", 2000, 1.0, 0.9, 1.5),
    ]

    sorted_features = sorted(features, key=lambda f: f.rice_score, reverse=True)

    demo(f"{'Feature':<22} {'Reach':>6} {'Impact':>7} {'Conf':>5} "
         f"{'Effort':>7} {'RICE':>8}")
    demo("-" * 65)
    for f in sorted_features:
        demo(f"{f.name:<22} {f.reach:>6} {f.impact:>6.1f}x {f.confidence:>4.0%} "
             f"{f.effort:>5.1f}pm {f.rice_score:>8.0f}")

    point("RICE は「直感」を「数値」に変えるツール")
    point("Confidence が低い機能は、まずプロトタイプで検証する")

    # ── 2.2 ICE スコアリング比較 ──
    subsection("2.2 ICE vs RICE 比較")

    demo("RICE: Reach × Impact × Confidence ÷ Effort")
    demo("  → ユーザー数を重視、B2C向き")
    demo("")
    demo("ICE: Impact × Confidence × Ease (Effortの逆数)")
    demo("  → シンプル、スタートアップ向き")
    demo("")
    demo("使い分け:")
    demo("  RICE → 大規模プロダクト（ユーザーリーチが重要）")
    demo("  ICE  → 初期スタートアップ（スピード重視）")

    # ── 2.3 Impact Mapping ──
    subsection("2.3 Impact Mapping")

    demo("Goal → Actor → Impact → Deliverable")
    demo("")
    demo("例: 月間アクティブユーザーを30%増加させる")
    demo("  │")
    demo("  ├─ Actor: 新規ユーザー")
    demo("  │   ├─ Impact: サインアップを簡単にする")
    demo("  │   │   ├─ Deliverable: ソーシャルログイン")
    demo("  │   │   └─ Deliverable: チュートリアル改善")
    demo("  │   └─ Impact: 友達に紹介してもらう")
    demo("  │       └─ Deliverable: リファラルプログラム")
    demo("  │")
    demo("  └─ Actor: 既存ユーザー")
    demo("      ├─ Impact: 毎日使う理由を作る")
    demo("      │   ├─ Deliverable: デイリーサマリー通知")
    demo("      │   └─ Deliverable: ストリーク機能")
    demo("      └─ Impact: 離脱を防ぐ")
    demo("          └─ Deliverable: オンボーディング改善")

    point("Impact Mapping は「なぜこの機能を作るのか」を可視化する")
    point("Deliverable から逆算するのではなく、Goal から順に考える")

    # ── 2.4 Jobs-to-be-Done (JTBD) ──
    subsection("2.4 Jobs-to-be-Done (JTBD)")

    demo("■ JTBD フォーマット:")
    demo("  When [状況],")
    demo("  I want to [動機],")
    demo("  So I can [期待する結果].")
    demo("")
    demo("■ 例（音楽ストリーミング）:")
    demo("  When 朝の通勤電車に乗っているとき,")
    demo("  I want to 気分に合った音楽をすぐに聴きたい,")
    demo("  So I can 通勤のストレスを減らして1日を良い気分で始められる.")
    demo("")
    demo("■ 競合分析（同じ Job を解決する代替手段）:")
    for alt in ["Spotify のプレイリスト", "ラジオ", "ポッドキャスト",
                "YouTube Music", "自分で作ったプレイリスト", "無音（瞑想）"]:
        demo(f"  - {alt}")

    point("JTBD の核心: ユーザーはドリルが欲しいのではなく、穴が欲しい")
    point("競合は同じカテゴリの製品だけではない")

    # ── 2.5 Lean Canvas ──
    subsection("2.5 Lean Canvas シミュレーション")

    @dataclass
    class LeanCanvas:
        problem: list[str]
        customer_segments: list[str]
        unique_value_prop: str
        solution: list[str]
        channels: list[str]
        revenue_streams: list[str]
        cost_structure: list[str]
        key_metrics: list[str]
        unfair_advantage: str

        def display(self) -> None:
            demo("┌─────────────────────────────────────────────────┐")
            demo(f"│ Problem: {', '.join(self.problem[:2])}")
            demo(f"│ Solution: {', '.join(self.solution[:2])}")
            demo(f"│ UVP: {self.unique_value_prop}")
            demo(f"│ Segments: {', '.join(self.customer_segments)}")
            demo(f"│ Channels: {', '.join(self.channels)}")
            demo(f"│ Revenue: {', '.join(self.revenue_streams)}")
            demo(f"│ Costs: {', '.join(self.cost_structure)}")
            demo(f"│ Metrics: {', '.join(self.key_metrics)}")
            demo(f"│ Unfair Advantage: {self.unfair_advantage}")
            demo("└─────────────────────────────────────────────────┘")

    canvas = LeanCanvas(
        problem=["ナレッジが散在して見つからない", "新人の立ち上がりが遅い"],
        customer_segments=["50-200人のテック企業", "リモートチーム"],
        unique_value_prop="AIがチームの暗黙知を自動で構造化・検索可能にする",
        solution=["Slack/Notion自動取り込み", "AIセマンティック検索", "自動FAQ生成"],
        channels=["PLG(Product-Led Growth)", "テックブログ", "DevRel"],
        revenue_streams=["SaaS月額 $10/user", "エンタープライズ契約"],
        cost_structure=["LLM API費用", "エンジニア人件費", "インフラ(AWS)"],
        key_metrics=["WAU", "検索成功率", "新人オンボーディング日数"],
        unfair_advantage="独自のRAGモデル + 業界特化データ",
    )
    canvas.display()

    point("[実装してみよう] 自分のプロジェクトの Lean Canvas を書いてみよう")


# =====================================================================
# Chapter 3: OKR・メトリクス
# =====================================================================

def chapter_3_metrics():
    section("Chapter 3: OKR・プロダクトメトリクス")

    # ── 3.1 OKR ──
    subsection("3.1 OKR 設定と進捗追跡")

    @dataclass
    class KeyResult:
        description: str
        target: float
        current: float
        unit: str

        @property
        def progress(self) -> float:
            return min(self.current / self.target, 1.5) if self.target > 0 else 0

        @property
        def on_track(self) -> str:
            if self.progress >= 0.7:
                return "On Track"
            elif self.progress >= 0.4:
                return "At Risk"
            return "Off Track"

    @dataclass
    class Objective:
        title: str
        key_results: list[KeyResult]

        @property
        def overall_progress(self) -> float:
            if not self.key_results:
                return 0
            return statistics.mean(kr.progress for kr in self.key_results)

    okrs = [
        Objective("ユーザーエンゲージメントを向上させる", [
            KeyResult("DAU/MAU ratio", 0.4, 0.32, "ratio"),
            KeyResult("平均セッション時間", 8.0, 6.5, "分"),
            KeyResult("D7 リテンション", 0.45, 0.38, "%"),
        ]),
        Objective("プラットフォームの信頼性を高める", [
            KeyResult("月間アップタイム", 99.95, 99.92, "%"),
            KeyResult("P99レイテンシ", 200, 180, "ms (低い方が良い)"),
            KeyResult("インシデント数", 3, 2, "件 (低い方が良い)"),
        ]),
    ]

    for obj in okrs:
        demo(f"O: {obj.title} (進捗: {obj.overall_progress:.0%})")
        for kr in obj.key_results:
            bar_len = int(kr.progress * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            demo(f"  KR: {kr.description}")
            demo(f"      {kr.current}/{kr.target} {kr.unit} "
                 f"[{bar}] {kr.progress:.0%} {kr.on_track}")
        demo("")

    point("OKRの達成率 70% が理想（100%なら目標が低すぎた）")
    point("KPI = 健康診断、OKR = ストレッチゴール")

    # ── 3.2 AARRR パイレーツメトリクス ──
    subsection("3.2 AARRR パイレーツメトリクス（ファネル分析）")

    funnel = {
        "Acquisition (獲得)":   10000,
        "Activation (活性化)":   3500,
        "Retention (継続)":      1400,
        "Revenue (収益化)":       420,
        "Referral (紹介)":        126,
    }

    prev = None
    for stage, count in funnel.items():
        conv = f"({count/prev:.1%} conversion)" if prev else "(top of funnel)"
        bar = "█" * (count // 250)
        demo(f"  {stage:<28} {count:>6} {conv}")
        demo(f"    {bar}")
        prev = count

    point("ボトルネックは Acquisition→Activation の変換率 (35%)")
    point("改善インパクト: ファネル上部を1%改善すると全体に波及する")

    # ── 3.3 LTV / CAC ──
    subsection("3.3 LTV / CAC 計算")

    @dataclass
    class UnitEconomics:
        arpu: float  # Average Revenue Per User (月額)
        churn_rate: float  # 月次解約率
        cac: float  # Customer Acquisition Cost
        gross_margin: float  # 粗利率

        @property
        def ltv(self) -> float:
            """LTV = ARPU × 粗利率 / 解約率"""
            return self.arpu * self.gross_margin / self.churn_rate

        @property
        def ltv_cac_ratio(self) -> float:
            return self.ltv / self.cac if self.cac > 0 else 0

        @property
        def payback_months(self) -> float:
            monthly_contribution = self.arpu * self.gross_margin
            return self.cac / monthly_contribution if monthly_contribution > 0 else 0

    economics = UnitEconomics(arpu=50, churn_rate=0.05, cac=200, gross_margin=0.7)

    demo(f"ARPU (月額):     ${economics.arpu}")
    demo(f"解約率 (月次):    {economics.churn_rate:.1%}")
    demo(f"CAC:             ${economics.cac}")
    demo(f"粗利率:           {economics.gross_margin:.0%}")
    demo(f"---")
    demo(f"LTV:             ${economics.ltv:.0f}")
    demo(f"LTV/CAC ratio:   {economics.ltv_cac_ratio:.1f}x")
    demo(f"Payback period:  {economics.payback_months:.1f} months")
    demo("")
    demo("判定基準:")
    demo(f"  LTV/CAC > 3x: {'✓ 健全' if economics.ltv_cac_ratio > 3 else '✗ 要改善'}")
    demo(f"  Payback < 12m: {'✓ 健全' if economics.payback_months < 12 else '✗ 要改善'}")

    point("SaaS の健全な指標: LTV/CAC > 3x, Payback < 12ヶ月")
    point("CACを下げる: PLG, コンテンツマーケ / LTVを上げる: 解約防止, アップセル")

    # ── 3.4 Retention Curve ──
    subsection("3.4 Retention Curve 分析")

    # D1, D7, D14, D30, D60, D90
    retention_data = {
        "良いアプリ":   [100, 60, 45, 35, 28, 22, 20],
        "普通のアプリ": [100, 40, 25, 18, 12, 8, 6],
        "悪いアプリ":   [100, 25, 12, 6, 3, 1, 0.5],
    }
    days = ["D0", "D1", "D7", "D14", "D30", "D60", "D90"]

    demo(f"{'':>14} " + " ".join(f"{d:>5}" for d in days))
    for name, rates in retention_data.items():
        vals = " ".join(f"{r:>4.0f}%" for r in rates)
        demo(f"{name:>14} {vals}")

    demo("")
    demo("D30リテンションの目安:")
    demo("  Consumer app: 20%+ → 良い")
    demo("  SaaS B2B:     80%+ → 良い")
    demo("  ゲーム:       10%+ → 良い")

    point("カーブが平坦化するポイント = プロダクトの「コア価値」を見つけた層")

    # ── 3.5 A/Bテスト設計 ──
    subsection("3.5 A/Bテスト サンプルサイズ計算")

    def calc_sample_size(baseline: float, mde: float,
                         alpha: float = 0.05, power: float = 0.8) -> int:
        """サンプルサイズ計算（近似式）"""
        # Z-scores
        z_alpha = 1.96 if alpha == 0.05 else 2.576  # 95% or 99%
        z_beta = 0.84 if power == 0.8 else 1.28  # 80% or 90%

        p1 = baseline
        p2 = baseline * (1 + mde)
        p_avg = (p1 + p2) / 2

        n = ((z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) +
              z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2) / \
            ((p2 - p1) ** 2)
        return int(math.ceil(n))

    scenarios = [
        ("CTR改善", 0.03, 0.10),  # 3% CTR, 10% MDE
        ("CVR改善", 0.05, 0.05),  # 5% CVR, 5% MDE
        ("解約率削減", 0.10, 0.15),  # 10% churn, 15% MDE
    ]

    for name, baseline, mde in scenarios:
        n = calc_sample_size(baseline, mde)
        demo(f"  {name}: baseline={baseline:.0%}, MDE={mde:.0%}")
        demo(f"    → 必要サンプル: {n:,}/群 (合計 {n*2:,})")
        demo(f"    → DAU 1万の場合: {n*2/10000:.0f} 日必要")
        demo("")

    point("MDE (Minimum Detectable Effect) を小さくするほどサンプルが膨大に")
    point("「1%の改善を検出したい」は現実的か？ → トラフィックと相談")


# =====================================================================
# Chapter 4: ステークホルダー管理
# =====================================================================

def chapter_4_stakeholder():
    section("Chapter 4: ステークホルダー管理")

    # ── 4.1 RACI マトリクス ──
    subsection("4.1 RACI マトリクス")

    @dataclass
    class RACIMatrix:
        tasks: list[str]
        roles: list[str]
        assignments: dict[tuple[str, str], str]  # (task, role) -> R/A/C/I

        def display(self) -> None:
            header = f"{'Task':<30}" + "".join(f"{r:>10}" for r in self.roles)
            demo(header)
            demo("-" * len(header))
            for task in self.tasks:
                row = f"{task:<30}"
                for role in self.roles:
                    val = self.assignments.get((task, role), "-")
                    row += f"{val:>10}"
                demo(row)

    raci = RACIMatrix(
        tasks=["API設計", "フロント実装", "インフラ構築", "リリース判断", "障害対応"],
        roles=["PM", "FE Lead", "BE Lead", "SRE", "VP Eng"],
        assignments={
            ("API設計", "PM"): "C", ("API設計", "FE Lead"): "C",
            ("API設計", "BE Lead"): "R", ("API設計", "SRE"): "I",
            ("API設計", "VP Eng"): "A",
            ("フロント実装", "PM"): "I", ("フロント実装", "FE Lead"): "R",
            ("フロント実装", "BE Lead"): "C", ("フロント実装", "SRE"): "-",
            ("フロント実装", "VP Eng"): "A",
            ("インフラ構築", "PM"): "I", ("インフラ構築", "FE Lead"): "-",
            ("インフラ構築", "BE Lead"): "C", ("インフラ構築", "SRE"): "R",
            ("インフラ構築", "VP Eng"): "A",
            ("リリース判断", "PM"): "R", ("リリース判断", "FE Lead"): "C",
            ("リリース判断", "BE Lead"): "C", ("リリース判断", "SRE"): "C",
            ("リリース判断", "VP Eng"): "A",
            ("障害対応", "PM"): "I", ("障害対応", "FE Lead"): "C",
            ("障害対応", "BE Lead"): "C", ("障害対応", "SRE"): "R",
            ("障害対応", "VP Eng"): "A",
        }
    )
    raci.display()

    demo("")
    demo("R = Responsible (実行者), A = Accountable (承認者)")
    demo("C = Consulted (相談先), I = Informed (報告先)")

    point("各タスクに R は1人以上、A は必ず1人だけ")
    point("A がいないタスクは責任の所在が不明確になる")

    # ── 4.2 Power/Interest Grid ──
    subsection("4.2 Power/Interest Grid")

    @dataclass
    class Stakeholder:
        name: str
        power: int  # 1-10
        interest: int  # 1-10
        strategy: str = ""

        def __post_init__(self):
            if self.power >= 6 and self.interest >= 6:
                self.strategy = "Manage Closely (密に管理)"
            elif self.power >= 6:
                self.strategy = "Keep Satisfied (満足を維持)"
            elif self.interest >= 6:
                self.strategy = "Keep Informed (情報共有)"
            else:
                self.strategy = "Monitor (監視)"

    stakeholders = [
        Stakeholder("CEO", 10, 4),
        Stakeholder("VP Engineering", 8, 9),
        Stakeholder("プロダクトデザイナー", 3, 8),
        Stakeholder("法務チーム", 6, 3),
        Stakeholder("エンドユーザー代表", 2, 9),
        Stakeholder("外部パートナー", 5, 5),
    ]

    demo("  Power/Interest Grid:")
    demo("         High Interest    Low Interest")
    demo("  High   ┌───────────┬───────────┐")
    demo("  Power  │ Manage    │ Keep      │")
    demo("         │ Closely   │ Satisfied │")
    demo("         ├───────────┼───────────┤")
    demo("  Low    │ Keep      │ Monitor   │")
    demo("  Power  │ Informed  │           │")
    demo("         └───────────┴───────────┘")
    demo("")

    for s in stakeholders:
        demo(f"  {s.name:<22} P={s.power:>2} I={s.interest:>2} → {s.strategy}")

    # ── 4.3 SBI フィードバック ──
    subsection("4.3 SBI フィードバックモデル")

    demo("■ SBI = Situation - Behavior - Impact")
    demo("")
    demo("  良い例:")
    demo("    S: 昨日のスプリントレビューで")
    demo("    B: デモ中にバグが出たとき、すぐにワークアラウンドを見せた")
    demo("    I: ステークホルダーが問題解決力を評価してくれた")
    demo("")
    demo("  改善を促す例:")
    demo("    S: 先週のコードレビューで")
    demo("    B: 修正依頼に「時間がない」とだけ返した")
    demo("    I: レビュアーがモチベーションを失い、次回のレビューが遅れた")
    demo("")
    demo("  NG例（SBIでない）:")
    demo("    × 「いつもコードが雑だ」（具体性なし）")
    demo("    × 「頑張ってるね」（行動が不明確）")

    point("フィードバックは72時間以内に。遅れると記憶が薄れる")


# =====================================================================
# Chapter 5: テクニカルPM
# =====================================================================

def chapter_5_tech_pm():
    section("Chapter 5: テクニカルPM")

    # ── 5.1 ADR (Architecture Decision Record) ──
    subsection("5.1 ADR テンプレート")

    @dataclass
    class ADR:
        number: int
        title: str
        status: str  # Proposed, Accepted, Deprecated, Superseded
        context: str
        decision: str
        consequences_positive: list[str]
        consequences_negative: list[str]
        alternatives_considered: list[tuple[str, str]]  # (option, reason_rejected)

        def render(self) -> str:
            lines = [
                f"# ADR-{self.number:04d}: {self.title}",
                f"Status: {self.status}",
                f"Date: {datetime.now().strftime('%Y-%m-%d')}",
                "",
                "## Context",
                self.context,
                "",
                "## Decision",
                self.decision,
                "",
                "## Alternatives Considered",
            ]
            for opt, reason in self.alternatives_considered:
                lines.append(f"  - {opt}: {reason}")
            lines.extend(["", "## Consequences", "  Positive:"])
            for p in self.consequences_positive:
                lines.append(f"    + {p}")
            lines.append("  Negative:")
            for n in self.consequences_negative:
                lines.append(f"    - {n}")
            return "\n".join(lines)

    adr = ADR(
        number=7,
        title="メッセージキューに SQS を採用する",
        status="Accepted",
        context="マイクロサービス間の非同期通信が必要。現在は同期HTTPで密結合。",
        decision="AWS SQS (Standard Queue) を採用する。",
        consequences_positive=[
            "サービス間の疎結合化", "AWS マネージドで運用コスト低",
            "チームに AWS 経験者が多い",
        ],
        consequences_negative=[
            "AWS ロックイン", "メッセージ順序保証なし (Standard Queue)",
            "最大メッセージサイズ 256KB",
        ],
        alternatives_considered=[
            ("Kafka", "運用コストが高い。現在の規模では過剰"),
            ("RabbitMQ", "セルフホストの運用負荷"),
            ("EventBridge", "イベントルーティングが主用途。キュー機能が弱い"),
        ],
    )
    for line in adr.render().split("\n"):
        demo(line)

    point("ADRは「なぜその決定をしたか」の記録。未来の自分/チームへのメッセージ")
    point("[実装してみよう] 自分のプロジェクトの技術選定を ADR で書いてみよう")

    # ── 5.2 Tech Debt 管理 ──
    subsection("5.2 Tech Debt 分類と管理")

    class DebtType(Enum):
        PRUDENT_DELIBERATE = "意図的・慎重"
        PRUDENT_INADVERTENT = "無意識・慎重"
        RECKLESS_DELIBERATE = "意図的・無謀"
        RECKLESS_INADVERTENT = "無意識・無謀"

    debts = [
        (DebtType.PRUDENT_DELIBERATE,
         "「リリース優先で簡易実装。Q2でリファクタ」",
         "計画的に返済すべき"),
        (DebtType.PRUDENT_INADVERTENT,
         "「今ならもっと良い設計がわかった」",
         "学びとして受け入れ、次回に活かす"),
        (DebtType.RECKLESS_DELIBERATE,
         "「テスト書く時間ないからスキップ」",
         "最も危険。すぐに返済計画を立てる"),
        (DebtType.RECKLESS_INADVERTENT,
         "「デザインパターン？何それ？」",
         "教育・ペアプログラミングで防ぐ"),
    ]

    demo("Tech Debt Quadrant (Martin Fowler):")
    demo("              Prudent (慎重)         Reckless (無謀)")
    demo("  Deliberate  計画的に後で返済       テスト省略（危険！）")
    demo("  (意図的)    ")
    demo("  Inadvertent 学びで設計改善を認識    知識不足による問題")
    demo("  (無意識)    ")
    demo("")

    for debt_type, example, action in debts:
        demo(f"  {debt_type.value}:")
        demo(f"    例: {example}")
        demo(f"    対応: {action}")
        demo("")

    # ── 5.3 トレードオフ分析 ──
    subsection("5.3 トレードオフ分析フレームワーク")

    @dataclass
    class TradeoffOption:
        name: str
        scores: dict[str, int]  # criteria -> score (1-5)

    @dataclass
    class TradeoffAnalysis:
        question: str
        criteria: dict[str, float]  # criteria -> weight (0-1)
        options: list[TradeoffOption]

        def evaluate(self) -> list[tuple[str, float]]:
            results = []
            for opt in self.options:
                score = sum(opt.scores.get(c, 0) * w
                           for c, w in self.criteria.items())
                results.append((opt.name, score))
            return sorted(results, key=lambda x: x[1], reverse=True)

    analysis = TradeoffAnalysis(
        question="認証基盤: Build vs Buy?",
        criteria={
            "開発コスト": 0.2,
            "運用コスト": 0.15,
            "カスタマイズ性": 0.25,
            "セキュリティ": 0.3,
            "立ち上げ速度": 0.1,
        },
        options=[
            TradeoffOption("自前実装 (JWT)", {"開発コスト": 2, "運用コスト": 2,
                "カスタマイズ性": 5, "セキュリティ": 2, "立ち上げ速度": 3}),
            TradeoffOption("Auth0", {"開発コスト": 4, "運用コスト": 3,
                "カスタマイズ性": 3, "セキュリティ": 5, "立ち上げ速度": 5}),
            TradeoffOption("AWS Cognito", {"開発コスト": 3, "運用コスト": 4,
                "カスタマイズ性": 2, "セキュリティ": 5, "立ち上げ速度": 4}),
            TradeoffOption("Keycloak (Self-hosted)", {"開発コスト": 3, "運用コスト": 2,
                "カスタマイズ性": 5, "セキュリティ": 4, "立ち上げ速度": 2}),
        ],
    )

    demo(f"Q: {analysis.question}")
    demo(f"  基準 (重み): {', '.join(f'{c}({w:.0%})' for c, w in analysis.criteria.items())}")
    demo("")

    header = f"{'Option':<25}" + "".join(f"{c:>12}" for c in analysis.criteria) + f"{'Total':>10}"
    demo(header)
    demo("-" * len(header))

    results = analysis.evaluate()
    for opt in analysis.options:
        row = f"{opt.name:<25}"
        for c in analysis.criteria:
            row += f"{opt.scores.get(c, 0):>12}"
        total = next(s for n, s in results if n == opt.name)
        row += f"{total:>10.2f}"
        demo(row)

    demo("")
    winner = results[0]
    demo(f"  → 推奨: {winner[0]} (スコア: {winner[1]:.2f})")

    # ── 5.4 見積もり手法 ──
    subsection("5.4 見積もり手法比較")

    demo("■ T-Shirt Sizing:")
    demo("  XS=1pt, S=2pt, M=3pt, L=5pt, XL=8pt, XXL=13pt")
    demo("  用途: 初期の粗い見積もり、ロードマップ計画")
    demo("")
    demo("■ Fibonacci (1,2,3,5,8,13,21):")
    demo("  用途: Sprint Planning での Story Points 見積もり")
    demo("  なぜFibonacci: 大きいタスクほど不確実性が増す")
    demo("")
    demo("■ Planning Poker:")
    demo("  1. PO がストーリーを説明")
    demo("  2. 全員が同時にカードを出す")
    demo("  3. 最大と最小の人が理由を説明")
    demo("  4. 合意するまで繰り返す")
    demo("")
    demo("■ #NoEstimates:")
    demo("  ストーリーを均一サイズに分割し、数だけ数える")
    demo("  用途: 成熟したチーム、予測可能な作業")

    # ── 5.5 ロードマップ ──
    subsection("5.5 Now/Next/Later ロードマップ")

    roadmap = {
        "Now (今Sprint)": [
            ("検索フィルター改善", "In Progress", "BE/FE"),
            ("認証バグ修正", "Done", "BE"),
            ("パフォーマンスモニタリング", "In Progress", "SRE"),
        ],
        "Next (次の1-2Sprint)": [
            ("AI レコメンデーション", "Planning", "ML/BE"),
            ("モバイル対応", "Design", "FE/Design"),
        ],
        "Later (3ヶ月以内)": [
            ("多言語対応", "Idea", "全チーム"),
            ("API公開 (Partner)", "Research", "BE/PM"),
        ],
    }

    for phase, items in roadmap.items():
        demo(f"  ■ {phase}")
        for title, status, team in items:
            demo(f"    [{status:<12}] {title:<30} ({team})")
        demo("")

    point("Now = コミット、Next = 高確度、Later = 方向性のみ")
    point("日付ベースのロードマップは避ける（約束になってしまう）")

    # ── 5.6 Incident Management ──
    subsection("5.6 Incident Severity & Postmortem")

    demo("■ Severity レベル:")
    severities = [
        ("SEV1 - Critical", "全ユーザー影響、データ損失", "即座", "15分以内"),
        ("SEV2 - Major", "主要機能停止、一部ユーザー影響", "1時間以内", "30分以内"),
        ("SEV3 - Minor", "機能低下、ワークアラウンドあり", "4時間以内", "1時間以内"),
        ("SEV4 - Low", "見た目の問題、次Sprint修正", "次Sprint", "N/A"),
    ]
    demo(f"  {'Level':<20} {'影響範囲':<28} {'対応開始':<12} {'エスカレ'}")
    demo("  " + "-" * 80)
    for sev, impact, response, escalate in severities:
        demo(f"  {sev:<20} {impact:<28} {response:<12} {escalate}")

    demo("")
    demo("■ Blameless Postmortem テンプレート:")
    demo("  1. インシデント概要 (What happened?)")
    demo("  2. タイムライン (When?)")
    demo("  3. 根本原因 (5 Whys)")
    demo("  4. 影響範囲 (Who was affected?)")
    demo("  5. 対応内容 (What did we do?)")
    demo("  6. 再発防止策 (Action items with owners and deadlines)")
    demo("  7. 学び (What went well? What didn't?)")

    point("Blameless = 人を責めない。システムの問題として捉える")
    point("[実装してみよう] 過去のバグを1つ選び、Postmortemを書いてみよう")


# =====================================================================
# Chapter 6: プロダクト戦略
# =====================================================================

def chapter_6_strategy():
    section("Chapter 6: プロダクト戦略")

    # ── 6.1 TAM/SAM/SOM ──
    subsection("6.1 TAM/SAM/SOM 市場規模計算")

    @dataclass
    class MarketSizing:
        product: str
        tam_users: int
        tam_arpu: float
        sam_ratio: float  # TAMのうちアクセス可能な比率
        som_ratio: float  # SAMのうち獲得可能な比率

        @property
        def tam(self) -> float: return self.tam_users * self.tam_arpu * 12
        @property
        def sam(self) -> float: return self.tam * self.sam_ratio
        @property
        def som(self) -> float: return self.sam * self.som_ratio

    market = MarketSizing(
        product="AI ナレッジ管理 SaaS",
        tam_users=50_000_000,  # 全世界のナレッジワーカー
        tam_arpu=10,  # $10/月/ユーザー
        sam_ratio=0.05,  # テック企業 50-500人
        som_ratio=0.02,  # 初年度の獲得目標
    )

    demo(f"Product: {market.product}")
    demo(f"TAM (Total Addressable Market):     ${market.tam/1e9:.1f}B")
    demo(f"  {market.tam_users/1e6:.0f}M users × ${market.tam_arpu}/mo × 12")
    demo(f"SAM (Serviceable Addressable Market): ${market.sam/1e6:.0f}M")
    demo(f"  TAM × {market.sam_ratio:.0%} (ターゲットセグメント)")
    demo(f"SOM (Serviceable Obtainable Market):  ${market.som/1e6:.1f}M")
    demo(f"  SAM × {market.som_ratio:.0%} (初年度獲得率)")

    point("投資家へのピッチ: TAMで市場の大きさ、SOMで現実的な計画を示す")

    # ── 6.2 Porter's Five Forces ──
    subsection("6.2 Porter's Five Forces 分析")

    @dataclass
    class FiveForces:
        industry: str
        forces: dict[str, tuple[int, str]]  # force -> (1-5 threat, reason)

        def display(self) -> None:
            demo(f"Industry: {self.industry}")
            demo("")
            for force, (level, reason) in self.forces.items():
                bar = "█" * level + "░" * (5 - level)
                threat = {1: "Very Low", 2: "Low", 3: "Medium",
                         4: "High", 5: "Very High"}[level]
                demo(f"  {force:<30} [{bar}] {threat}")
                demo(f"    {reason}")

    analysis = FiveForces(
        industry="AI SaaS (ナレッジ管理)",
        forces={
            "新規参入の脅威": (4, "LLM APIで参入障壁低下。差別化がカギ"),
            "代替品の脅威": (3, "Notion AI, Confluence, Google Search"),
            "買い手の交渉力": (3, "スイッチングコスト中程度。データ移行が壁"),
            "供給者の交渉力": (4, "OpenAI/Anthropic APIへの依存度が高い"),
            "業界内競争": (4, "Glean, Guru, Notion AI など競合多数"),
        }
    )
    analysis.display()

    # ── 6.3 Product-Market Fit ──
    subsection("6.3 Product-Market Fit 判定")

    demo("■ Sean Ellis Test (PMF Survey):")
    demo("  Q: 「このプロダクトが使えなくなったらどう感じますか？」")
    demo("    - 非常に残念 (Very Disappointed)")
    demo("    - やや残念 (Somewhat Disappointed)")
    demo("    - 残念ではない (Not Disappointed)")
    demo("")

    pmf_responses = {"very_disappointed": 42, "somewhat": 35, "not": 23}
    total = sum(pmf_responses.values())
    vd_pct = pmf_responses["very_disappointed"] / total

    demo(f"  結果: Very Disappointed = {vd_pct:.0%}")
    demo(f"  判定: {'✓ PMF達成!' if vd_pct >= 0.40 else '✗ PMF未達'}")
    demo(f"  基準: 40%以上が「非常に残念」→ PMF達成")
    demo("")

    demo("■ その他のPMF指標:")
    indicators = [
        ("NPS (Net Promoter Score)", "> 40", "推奨者 - 批判者"),
        ("Organic Growth Rate", "> 50%", "有料マーケ以外の成長率"),
        ("D30 Retention", "> 20% (consumer)", "30日後の継続率"),
        ("Payback Period", "< 12 months", "顧客獲得コスト回収期間"),
    ]
    for metric, threshold, desc in indicators:
        demo(f"  {metric:<25} {threshold:<20} {desc}")

    # ── 6.4 Crossing the Chasm ──
    subsection("6.4 Crossing the Chasm (キャズム理論)")

    demo("Technology Adoption Lifecycle:")
    demo("")
    demo("  Innovators  Early      Early      Late       Laggards")
    demo("  (2.5%)     Adopters   Majority   Majority   (16%)")
    demo("             (13.5%)    (34%)      (34%)")
    demo("  ┌──┐ ┌────┐  ╳  ┌────────┐ ┌────────┐ ┌──────┐")
    demo("  │  │ │    │CHASM│        │ │        │ │      │")
    demo("  └──┘ └────┘     └────────┘ └────────┘ └──────┘")
    demo("")
    demo("キャズムを超える戦略:")
    demo("  1. ターゲットセグメントを1つに絞る（ボウリングピン戦略）")
    demo("  2. Whole Product を提供する（導入・運用・サポート含む）")
    demo("  3. 参照顧客を獲得する（同業種の成功事例）")
    demo("  4. 適切なポジショニング（既存カテゴリ vs 新カテゴリ）")

    point("スタートアップの死因の多くは「キャズム落ち」")


# =====================================================================
# Chapter 7: テクニカルリーダーシップ
# =====================================================================

def chapter_7_leadership():
    section("Chapter 7: テクニカルリーダーシップ")

    # ── 7.1 1:1 ミーティング ──
    subsection("7.1 1:1 ミーティング テンプレート")

    demo("■ 1:1 の3つの軸:")
    demo("")
    demo("  1. キャリア開発 (月1回)")
    demo("    - 6ヶ月後にどうなっていたい？")
    demo("    - 今のプロジェクトで伸びていると感じるスキルは？")
    demo("    - 学びたいけど機会がないことは？")
    demo("")
    demo("  2. パフォーマンス (隔週)")
    demo("    - 先週一番うまくいったことは？")
    demo("    - ブロッカーはある？ 何か手伝えることは？")
    demo("    - フィードバック（SBIフレームワーク）")
    demo("")
    demo("  3. ウェルビーイング (毎週)")
    demo("    - 仕事の量はどう？ 持続可能？")
    demo("    - チーム内で困っていることはない？")
    demo("    - 1-10でモチベーションスコアは？")

    point("1:1は部下のための時間。マネージャーの報告の場ではない")
    point("メモを取り、Action Items を追跡する")

    # ── 7.2 Spotify Squad Health Check ──
    subsection("7.2 チーム健康度チェック")

    @dataclass
    class HealthCheck:
        dimensions: dict[str, tuple[str, str, str]]  # dim -> (green, yellow, red)
        scores: dict[str, int]  # dim -> score (-1, 0, 1) and trend

        def display(self) -> None:
            for dim, (green, _, red) in self.dimensions.items():
                score = self.scores.get(dim, 0)
                emoji = {1: "[GREEN]", 0: "[YELLOW]", -1: "[RED]"}[score]
                demo(f"  {emoji} {dim}")
                if score == 1:
                    demo(f"       → {green}")
                elif score == -1:
                    demo(f"       → {red}")

    health = HealthCheck(
        dimensions={
            "ミッション": ("チームの目的が明確", "", "何のためにやっているか不明"),
            "楽しさ": ("仕事が楽しい", "", "退屈・やりがいがない"),
            "学び": ("常に新しいことを学んでいる", "", "学びの機会がない"),
            "デリバリー": ("定期的にリリースしている", "", "リリースが滞っている"),
            "品質": ("コードに自信がある", "", "技術的負債で苦しんでいる"),
            "スピード": ("素早く動けている", "", "プロセスが邪魔をしている"),
            "サポート": ("必要な支援を受けている", "", "孤立している"),
            "チームワーク": ("一体感がある", "", "サイロ化している"),
        },
        scores={
            "ミッション": 1, "楽しさ": 0, "学び": 1, "デリバリー": 1,
            "品質": -1, "スピード": 0, "サポート": 1, "チームワーク": 1,
        }
    )
    health.display()

    point("四半期ごとに実施。トレンド（改善/悪化）も追跡する")

    # ── 7.3 スキルマトリクス ──
    subsection("7.3 チームスキルマトリクス")

    skills = ["Python", "Go", "K8s", "ML", "SQL", "AWS", "React"]
    members = {
        "Alice":  [4, 2, 3, 4, 3, 4, 1],
        "Bob":    [3, 4, 4, 1, 3, 4, 2],
        "Carol":  [4, 1, 2, 5, 4, 3, 3],
        "Dave":   [2, 3, 2, 2, 2, 2, 5],
    }

    header = f"{'Member':<10}" + "".join(f"{s:>8}" for s in skills) + f"{'Avg':>8}"
    demo(header)
    demo("-" * len(header))
    for name, scores in members.items():
        row = f"{name:<10}" + "".join(f"{s:>8}" for s in scores)
        row += f"{statistics.mean(scores):>7.1f}"
        demo(row)

    # Bus Factor
    demo("")
    demo("Bus Factor (各スキルで3以上の人数):")
    for i, skill in enumerate(skills):
        count = sum(1 for scores in members.values() if scores[i] >= 3)
        risk = "⚠ RISK" if count <= 1 else ""
        demo(f"  {skill:<10}: {count}人 {risk}")

    point("Bus Factor 1 = その人がいなくなったらチームが止まる")
    point("対策: ペアプログラミング、ドキュメント、ローテーション")

    # ── 7.4 Delegation Poker ──
    subsection("7.4 Delegation Poker (7レベル)")

    levels = [
        ("1. Tell", "マネージャーが決定して伝える"),
        ("2. Sell", "マネージャーが決定し、理由を説明して納得させる"),
        ("3. Consult", "チームの意見を聞いてからマネージャーが決定"),
        ("4. Agree", "チームとマネージャーが合意して決定"),
        ("5. Advise", "チームが決定、マネージャーはアドバイス"),
        ("6. Inquire", "チームが決定、マネージャーは結果を聞く"),
        ("7. Delegate", "チームに完全に委任"),
    ]

    for level, desc in levels:
        demo(f"  {level:<14} {desc}")

    demo("")
    demo("例:")
    demo("  技術スタック選定      → Level 4 (Agree)")
    demo("  タスクの優先順位      → Level 5 (Advise)")
    demo("  個人の休暇取得        → Level 7 (Delegate)")
    demo("  四半期目標設定        → Level 3 (Consult)")
    demo("  採用基準の設定        → Level 2 (Sell)")

    point("Level 4 が最も多く使うべき（チームの主体性を尊重しつつ合意）")


# =====================================================================
# Chapter 8: 面接対応
# =====================================================================

def chapter_8_interview():
    section("Chapter 8: FAANG PM/Tech Lead 面接対応")

    # ── 8.1 STAR メソッド ──
    subsection("8.1 STAR メソッド")

    @dataclass
    class STARStory:
        question: str
        situation: str
        task: str
        action: list[str]
        result: str
        learnings: str

    story = STARStory(
        question="技術的に難しい判断を迫られた経験を教えてください",
        situation="マイクロサービス移行の途中、APIレスポンスが3倍に悪化。"
                  "リリース2週間前で、ロールバックかパフォーマンス修正かの判断が必要だった。",
        task="PMとして、リリーススケジュールを守りながらパフォーマンス問題を解決する",
        action=[
            "1. データ収集: P50/P99レイテンシを計測し、影響範囲を特定",
            "2. 選択肢の整理: (A)ロールバック (B)部分修正 (C)キャッシュ層追加",
            "3. トレードオフ分析: 各選択肢のリスクとリリースへの影響を評価",
            "4. ステークホルダーと合意: VP Engに3つの選択肢を提示し、Bを選択",
            "5. 実行: BE チームに集中的にペアプロで修正。3日で解決",
        ],
        result="リリースは3日遅延で済み、パフォーマンスは移行前より20%改善。"
               "VP Engから「判断プロセスが素晴らしい」とフィードバック。",
        learnings="パフォーマンステストをCI/CDに組み込む仕組みを導入した。"
                  "以降、同様の問題は事前に検出できるようになった。",
    )

    demo(f"Q: {story.question}")
    demo(f"")
    demo(f"S (Situation): {story.situation}")
    demo(f"T (Task): {story.task}")
    demo(f"A (Action):")
    for a in story.action:
        demo(f"  {a}")
    demo(f"R (Result): {story.result}")
    demo(f"Learning: {story.learnings}")

    point("Action は具体的に。「頑張った」ではなく「何をしたか」")
    point("Result は数字で。「改善した」ではなく「20%改善」")

    # ── 8.2 Product Sense 問題 ──
    subsection("8.2 Product Sense 問題")

    demo("Q: 「Google Maps を改善するとしたら？」")
    demo("")
    demo("回答フレームワーク:")
    demo("  1. Clarify: ユーザーセグメント確認")
    demo("     「どのユーザーを想定しますか？通勤者？旅行者？配送ドライバー？」")
    demo("")
    demo("  2. User & Pain Points:")
    demo("     - 通勤者: 毎日同じルートなのに毎回検索が面倒")
    demo("     - 旅行者: 現地の隠れスポットが見つからない")
    demo("     - 配送ドライバー: 複数配達先の最適ルートがない")
    demo("")
    demo("  3. Prioritize (RICE):")
    demo("     通勤者が最大セグメント → ここにフォーカス")
    demo("")
    demo("  4. Solution:")
    demo("     「スマートコミュート」機能")
    demo("     - 学習型: 毎朝の通勤時間にプッシュ通知")
    demo("     - リアルタイム: 事故・渋滞で代替ルート自動提案")
    demo("     - 予測: 「今日は10分遅れそうです。7:50に出発推奨」")
    demo("")
    demo("  5. Metrics:")
    demo("     - Primary: 通勤ユーザーのDAU")
    demo("     - Secondary: 通知のCTR, 到着時刻の予測精度")
    demo("")
    demo("  6. Tradeoffs:")
    demo("     - Pro: エンゲージメント向上、習慣形成")
    demo("     - Con: 通知過多のリスク、プライバシー懸念")

    # ── 8.3 Execution 問題 ──
    subsection("8.3 Execution 問題")

    demo("Q: 「DAUが先週から15%下がった。どう対処する？」")
    demo("")
    demo("回答フレームワーク:")
    demo("  1. Clarify: 計測の正確性を確認")
    demo("     - データパイプラインのバグではないか？")
    demo("     - 季節性（祝日・長期休暇）ではないか？")
    demo("")
    demo("  2. Segment: どのユーザー層が減少したか？")
    demo("     - 新規 vs 既存？ → Activation問題 or Retention問題")
    demo("     - 地域別？ → 特定地域のサーバー障害？")
    demo("     - プラットフォーム別？ → iOS/Android アプデの影響？")
    demo("")
    demo("  3. Timeline: いつから始まったか？")
    demo("     - リリースと相関？ → ロールバック検討")
    demo("     - 競合のリリースと相関？ → 競合分析")
    demo("     - 外部要因？ → ニュース、規制変更")
    demo("")
    demo("  4. Prioritize: 影響度 × 可逆性で対応順を決定")
    demo("  5. Action: 短期（今週）と中期（今月）の計画")
    demo("  6. Prevention: 異常検知アラートの設定")

    # ── 8.4 Google Tech Lead 面接 ──
    subsection("8.4 Tech Lead 面接で聞かれる質問10選")

    questions = [
        "チームの技術的方向性について意見が分かれた。どう対処した？",
        "レガシーシステムの書き換えを提案した経験は？どう説得した？",
        "本番障害の対応で最も学びがあった経験は？",
        "ジュニアエンジニアの成長をどう支援したか？",
        "技術的負債とビジネス要件のバランスをどう取ったか？",
        "チームのパフォーマンスが落ちた時にどう対処したか？",
        "間違った技術選定をした経験は？どう修正した？",
        "クロスファンクショナルチームとの協業で困難だった経験は？",
        "スケールの問題に直面した経験は？（技術 or 組織）",
        "自分の提案が却下された経験は？その後どうした？",
    ]

    for i, q in enumerate(questions, 1):
        demo(f"  {i:>2}. {q}")

    demo("")
    demo("回答のコツ:")
    demo("  - 必ず STAR フレームワークで構造化する")
    demo("  - 「I」ではなく「We」を使う（チームの成果として語る）")
    demo("  - 失敗談は「学び」と「その後の改善」をセットで語る")
    demo("  - 数字を入れる（「チームの生産性が30%向上」）")

    point("[実装してみよう] 上の10問から3つ選び、STAR で回答を書いてみよう")


# =====================================================================
# Chapter 9: リスク管理
# =====================================================================

def chapter_9_risk():
    section("Chapter 9: リスク管理")

    subsection("9.1 リスクマトリクス")

    @dataclass
    class Risk:
        description: str
        probability: int  # 1-5
        impact: int  # 1-5
        mitigation: str

        @property
        def score(self) -> int:
            return self.probability * self.impact

        @property
        def level(self) -> str:
            s = self.score
            if s >= 15: return "CRITICAL"
            if s >= 10: return "HIGH"
            if s >= 5: return "MEDIUM"
            return "LOW"

    risks = [
        Risk("LLM API の料金値上げ", 3, 4, "マルチプロバイダー対応、コスト上限設定"),
        Risk("主要エンジニアの退職", 4, 4, "ナレッジ共有、ドキュメント、クロストレーニング"),
        Risk("セキュリティインシデント", 2, 5, "ペネトレーションテスト、WAF、暗号化"),
        Risk("競合のAI機能リリース", 4, 3, "差別化戦略、顧客との密な関係構築"),
        Risk("データセンター障害", 1, 5, "マルチAZ、DR計画、自動フェイルオーバー"),
        Risk("規制変更 (AI規制法)", 3, 3, "法務チームとの連携、コンプライアンス監視"),
    ]

    risks_sorted = sorted(risks, key=lambda r: r.score, reverse=True)

    demo(f"{'Risk':<28} {'P':>3} {'I':>3} {'Score':>6} {'Level':<10} Mitigation")
    demo("-" * 90)
    for r in risks_sorted:
        demo(f"{r.description:<28} {r.probability:>3} {r.impact:>3} "
             f"{r.score:>5}  {r.level:<10} {r.mitigation}")

    demo("")
    demo("Risk Matrix:")
    demo("  Impact →  1    2    3    4    5")
    demo("  Prob 5   [5]  [10] [15] [20] [25]")
    demo("       4   [4]  [8]  [12] [16] [20]")
    demo("       3   [3]  [6]  [9]  [12] [15]")
    demo("       2   [2]  [4]  [6]  [8]  [10]")
    demo("       1   [1]  [2]  [3]  [4]  [5]")

    point("CRITICAL/HIGH は即座に対策。MEDIUM は監視。LOW は受容")
    point("四半期ごとにリスクレビューを実施する")


# =====================================================================
# メイン
# =====================================================================

def main():
    print("=" * 70)
    print("  Phase PM: テクニカルPM・リーダーシップ完全ガイド")
    print("  対象: FAANG PM / Tech Lead 志望者")
    print("  依存: 標準ライブラリのみ")
    print("=" * 70)

    chapter_1_agile()
    chapter_2_discovery()
    chapter_3_metrics()
    chapter_4_stakeholder()
    chapter_5_tech_pm()
    chapter_6_strategy()
    chapter_7_leadership()
    chapter_8_interview()
    chapter_9_risk()

    print("\n" + "=" * 70)
    print("  全チャプター完了!")
    print("")
    print("  次のステップ:")
    print("    1. RICE/ICE で自分のプロジェクトの機能を優先順位付けする")
    print("    2. OKR を設定して2週間追跡してみる")
    print("    3. ADR を1つ書いてみる")
    print("    4. STAR で面接回答を3つ準備する")
    print("    5. Lean Canvas で自分のプロダクトを整理する")
    print("=" * 70)


if __name__ == "__main__":
    main()
