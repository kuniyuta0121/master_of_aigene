#!/usr/bin/env python3
"""
Staff+ Engineering Leadership — FAANG Tech Lead / Staff Engineer の技術リーダーシップ

Senior → Staff+ の壁を越えるために必要な:
- 技術戦略とビジョン策定
- 組織設計とチームトポロジー
- 大規模な技術的意思決定
- DORA / SPACE メトリクス
- エグゼクティブコミュニケーション
- Staff+ 面接対策

実行: python staff_plus_leadership.py
依存: Python 3.9+ 標準ライブラリのみ
"""

import json
import math
import random
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ============================================================
# Chapter 1: Technical Strategy & Vision
# ============================================================

def chapter1_technical_strategy():
    print("=" * 70)
    print("Chapter 1: Technical Strategy & Vision")
    print("  Senior は「どう作るか」、Staff+ は「何を作るべきか」を決める")
    print("=" * 70)

    # --- 1.1 Technology Radar ---
    print("\n" + "─" * 60)
    print("1.1 Technology Radar")
    print("─" * 60)
    print("""
    ThoughtWorks が考案した技術評価フレームワーク。
    組織として技術選択を可視化し、統一的な判断基準を作る。

    4つのリング:
    ┌─────────────────────────────────┐
    │          HOLD (様子見)            │
    │    ┌───────────────────────┐     │
    │    │    ASSESS (評価中)      │     │
    │    │   ┌───────────────┐   │     │
    │    │   │  TRIAL (試用)   │   │     │
    │    │   │  ┌─────────┐  │   │     │
    │    │   │  │  ADOPT   │  │   │     │
    │    │   │  │ (採用)    │  │   │     │
    │    │   │  └─────────┘  │   │     │
    │    │   └───────────────┘   │     │
    │    └───────────────────────┘     │
    └─────────────────────────────────┘
    """)

    class Ring(Enum):
        ADOPT = "Adopt"
        TRIAL = "Trial"
        ASSESS = "Assess"
        HOLD = "Hold"

    class Quadrant(Enum):
        LANGUAGES = "Languages & Frameworks"
        PLATFORMS = "Platforms"
        TOOLS = "Tools"
        TECHNIQUES = "Techniques"

    @dataclass
    class RadarEntry:
        name: str
        ring: Ring
        quadrant: Quadrant
        rationale: str
        moved: str = "→"  # ↑ moved in, ↓ moved out, → unchanged, NEW

    radar = [
        RadarEntry("Python 3.12+", Ring.ADOPT, Quadrant.LANGUAGES,
                    "ML/DS標準、型ヒント成熟", "→"),
        RadarEntry("TypeScript 5.x", Ring.ADOPT, Quadrant.LANGUAGES,
                    "フルスタック型安全、エコシステム", "→"),
        RadarEntry("Go 1.22+", Ring.ADOPT, Quadrant.LANGUAGES,
                    "クラウドネイティブ標準、goroutine", "→"),
        RadarEntry("Rust", Ring.TRIAL, Quadrant.LANGUAGES,
                    "高性能ワークロード、WASM", "↑"),
        RadarEntry("Kubernetes", Ring.ADOPT, Quadrant.PLATFORMS,
                    "コンテナオーケストレーション標準", "→"),
        RadarEntry("Serverless (Lambda/Cloud Run)", Ring.ADOPT, Quadrant.PLATFORMS,
                    "イベント駆動、低運用コスト", "→"),
        RadarEntry("WebAssembly", Ring.ASSESS, Quadrant.PLATFORMS,
                    "エッジコンピューティング、プラグインシステム", "↑"),
        RadarEntry("Terraform", Ring.ADOPT, Quadrant.TOOLS,
                    "マルチクラウドIaC標準", "→"),
        RadarEntry("Pulumi", Ring.TRIAL, Quadrant.TOOLS,
                    "汎用言語でIaC、テスト容易性", "↑"),
        RadarEntry("OpenTelemetry", Ring.ADOPT, Quadrant.TOOLS,
                    "可観測性の標準化", "↑"),
        RadarEntry("Platform Engineering", Ring.ADOPT, Quadrant.TECHNIQUES,
                    "Internal Developer Platform", "↑"),
        RadarEntry("AI-Assisted Development", Ring.TRIAL, Quadrant.TECHNIQUES,
                    "Copilot/Claude Code、生産性向上", "NEW"),
        RadarEntry("Micro Frontends", Ring.ASSESS, Quadrant.TECHNIQUES,
                    "独立デプロイ可能なフロントエンド", "→"),
        RadarEntry("Monorepo (Nx/Turborepo)", Ring.TRIAL, Quadrant.TECHNIQUES,
                    "コード共有、一貫性、atomic commits", "↑"),
    ]

    print("  Our Technology Radar (2026 Q1)")
    print()
    for ring in Ring:
        entries = [e for e in radar if e.ring == ring]
        if entries:
            print(f"  [{ring.value}]")
            for e in entries:
                print(f"    {e.moved} {e.name:<30} ({e.quadrant.value})")
                print(f"      理由: {e.rationale}")
            print()

    # --- 1.2 Build vs Buy Framework ---
    print("\n" + "─" * 60)
    print("1.2 Build vs Buy 意思決定フレームワーク")
    print("─" * 60)

    @dataclass
    class BuildBuyOption:
        name: str
        scores: Dict[str, int]  # criteria → 1-5 score

    criteria_weights = {
        "strategic_value": 5,      # コア競争力か？
        "time_to_market": 4,       # 市場投入速度
        "total_cost_3yr": 4,       # 3年TCO
        "customizability": 3,      # カスタマイズ性
        "maintenance_burden": 3,   # 保守コスト (高=良い=保守楽)
        "team_expertise": 2,       # チームのスキル適合
        "vendor_risk": 2,          # ベンダーロックイン/倒産リスク (高=良い=低リスク)
    }

    print("""
    ★ Staff+ の仕事: 「作るか買うか」を組織として判断する

    判断基準 (重み付きスコアリング):
    """)
    for c, w in criteria_weights.items():
        bar = "█" * w
        print(f"    {c:<22} weight={w} {bar}")

    # Example evaluation
    options = [
        BuildBuyOption("自社構築 (Build)", {
            "strategic_value": 5, "time_to_market": 2, "total_cost_3yr": 3,
            "customizability": 5, "maintenance_burden": 2, "team_expertise": 4,
            "vendor_risk": 5
        }),
        BuildBuyOption("SaaS 導入 (Buy)", {
            "strategic_value": 2, "time_to_market": 5, "total_cost_3yr": 3,
            "customizability": 2, "maintenance_burden": 5, "team_expertise": 5,
            "vendor_risk": 2
        }),
        BuildBuyOption("OSS + カスタマイズ", {
            "strategic_value": 4, "time_to_market": 3, "total_cost_3yr": 4,
            "customizability": 4, "maintenance_burden": 3, "team_expertise": 3,
            "vendor_risk": 4
        }),
    ]

    print("\n  例: 認証基盤の選択")
    print(f"\n  {'Option':<25}", end="")
    for c in criteria_weights:
        print(f" {c[:8]:>8}", end="")
    print(f" {'TOTAL':>8}")
    print("  " + "-" * 95)

    best_score = 0
    best_name = ""
    for opt in options:
        total = sum(opt.scores[c] * criteria_weights[c] for c in criteria_weights)
        print(f"  {opt.name:<25}", end="")
        for c in criteria_weights:
            print(f" {opt.scores[c]:>8}", end="")
        print(f" {total:>8}")
        if total > best_score:
            best_score = total
            best_name = opt.name

    print(f"\n  → 推奨: {best_name} (スコア: {best_score})")

    # --- 1.3 TCO Calculator ---
    print("\n" + "─" * 60)
    print("1.3 Total Cost of Ownership (TCO) 計算")
    print("─" * 60)

    def calculate_tco(
        initial_cost: float,
        annual_license: float,
        annual_infra: float,
        fte_count: float,  # フルタイム換算の人数
        avg_salary: float,
        years: int = 3
    ) -> List[Dict]:
        results = []
        cumulative = initial_cost
        for year in range(1, years + 1):
            people_cost = fte_count * avg_salary
            annual = annual_license + annual_infra + people_cost
            cumulative += annual
            results.append({
                "year": year,
                "license": annual_license,
                "infra": annual_infra,
                "people": people_cost,
                "annual_total": annual,
                "cumulative": cumulative,
            })
        return results

    print("\n  Build vs Buy TCO 比較 (3年間, 万円)")
    print()

    build_tco = calculate_tco(
        initial_cost=3000, annual_license=0, annual_infra=500,
        fte_count=2.0, avg_salary=1200, years=3
    )
    buy_tco = calculate_tco(
        initial_cost=500, annual_license=1200, annual_infra=200,
        fte_count=0.3, avg_salary=1200, years=3
    )

    print(f"  {'Year':<6} {'Build':>10} {'Buy':>10} {'差額':>10}")
    print("  " + "-" * 40)
    for b, s in zip(build_tco, buy_tco):
        diff = b["cumulative"] - s["cumulative"]
        sign = "+" if diff > 0 else ""
        print(f"  Year {b['year']:<3} {b['cumulative']:>9.0f} {s['cumulative']:>9.0f} {sign}{diff:>9.0f}")

    print("""
    ★ 面接での答え方:
    「3年TCOだけでなく、戦略的価値・チーム成長・機会費用も考慮します。
     コア競争力に直結するなら Build、差別化に寄与しないなら Buy。
     中間解として OSS + カスタマイズも検討します。」
    """)

    # --- 1.4 Technical Vision Document ---
    print("─" * 60)
    print("1.4 Technical Vision Document テンプレート")
    print("─" * 60)
    print("""
    Staff+ エンジニアが書く最も重要なドキュメント。
    1-2年の技術方向性を組織全体に示す。

    ┌──────────────────────────────────────────┐
    │ Technical Vision: [領域名]                │
    ├──────────────────────────────────────────┤
    │ 1. Context (背景)                         │
    │    - ビジネスの方向性                       │
    │    - 現在の技術的課題                       │
    │    - 外部環境の変化                         │
    │                                           │
    │ 2. Current State (現状)                    │
    │    - アーキテクチャ図                       │
    │    - 技術的負債の棚卸                       │
    │    - チームの capability                   │
    │                                           │
    │ 3. Target State (目標状態)                 │
    │    - 1年後のあるべき姿                      │
    │    - 品質属性の目標値 (SLO, レイテンシ)     │
    │    - チーム構成の変化                       │
    │                                           │
    │ 4. Migration Path (移行計画)               │
    │    - Phase 1: Quick Wins (0-3ヶ月)        │
    │    - Phase 2: Foundation (3-6ヶ月)         │
    │    - Phase 3: Transformation (6-12ヶ月)    │
    │    - 各フェーズのリスクと緩和策              │
    │                                           │
    │ 5. Success Metrics (成功指標)              │
    │    - Leading indicators (先行指標)          │
    │    - Lagging indicators (遅行指標)          │
    │    - Anti-metrics (悪化させてはいけない指標)  │
    │                                           │
    │ 6. Alternatives Considered (検討した代替案) │
    │    - Option A: [概要] — 却下理由            │
    │    - Option B: [概要] — 却下理由            │
    └──────────────────────────────────────────┘

    ★ Key: Vision は「正解」ではなく「方向」を示す。
    完璧を求めず、チームが自律的に判断できる羅針盤にする。
    """)

    # --- 1.5 Platform Maturity Model ---
    print("─" * 60)
    print("1.5 Platform Maturity Model")
    print("─" * 60)

    maturity_levels = [
        ("Level 0: Ad-hoc", [
            "各チームが独自にツール選定",
            "手動デプロイ、手動テスト",
            "知識が個人に属人化",
        ]),
        ("Level 1: Standardized", [
            "共通ツール・テンプレートが存在",
            "CI/CDパイプラインが標準化",
            "ドキュメントが集約されている",
        ]),
        ("Level 2: Self-Service", [
            "開発者がUIやCLIでリソースを自己プロビジョニング",
            "Golden Path (推奨パス) が整備",
            "プラットフォームチームが内部顧客を持つ",
        ]),
        ("Level 3: Automated", [
            "ポリシーの自動適用 (セキュリティ, コスト)",
            "自動スケーリング, 自動修復",
            "AIによる最適化提案",
        ]),
        ("Level 4: Optimized", [
            "データ駆動の継続改善",
            "開発者体験の定量測定",
            "業界ベンチマークとの比較",
        ]),
    ]

    # DX Metrics
    print("""
    Developer Experience (DX) メトリクス:

    ┌────────────────────┬────────────────────┬──────────────┐
    │ メトリクス           │ 計測方法            │ 目標値        │
    ├────────────────────┼────────────────────┼──────────────┤
    │ Onboarding Time    │ 初commit までの日数  │ < 1日         │
    │ Inner Loop Speed   │ コード変更→確認      │ < 10秒        │
    │ Deployment Lead    │ merge→本番          │ < 15分        │
    │ CSAT (満足度)       │ 四半期サーベイ       │ > 4.0/5.0    │
    │ Cognitive Load     │ タスク切替回数/日     │ < 5回         │
    │ Tool Reliability   │ CI/CDの可用性        │ > 99.5%      │
    └────────────────────┴────────────────────┴──────────────┘
    """)

    for level, items in maturity_levels:
        print(f"  {level}")
        for item in items:
            print(f"    ✓ {item}")
        print()


# ============================================================
# Chapter 2: Organizational Design for Engineering
# ============================================================

def chapter2_org_design():
    print("\n" + "=" * 70)
    print("Chapter 2: Organizational Design for Engineering")
    print("  Conway's Law: システム構造は組織構造を反映する")
    print("=" * 70)

    # --- 2.1 Team Topologies ---
    print("\n" + "─" * 60)
    print("2.1 Team Topologies (Matthew Skelton & Manuel Pais)")
    print("─" * 60)
    print("""
    4つの基本チームタイプ:

    1. Stream-aligned Team (ストリーム沿いチーム)
       ┌─────────────────────────────────────┐
       │ ビジネスストリーム(顧客フロー)に沿う    │
       │ End-to-end のオーナーシップ             │
       │ 例: 検索チーム, 決済チーム, 通知チーム   │
       └─────────────────────────────────────┘

    2. Platform Team (プラットフォームチーム)
       ┌─────────────────────────────────────┐
       │ Stream-aligned チームの認知負荷を軽減   │
       │ セルフサービスAPI/ツールを提供           │
       │ 例: Infrastructure, CI/CD, Data Platform│
       └─────────────────────────────────────┘

    3. Enabling Team (支援チーム)
       ┌─────────────────────────────────────┐
       │ 他チームの capability 向上を支援         │
       │ 期間限定で embedded する                 │
       │ 例: SRE支援, セキュリティ支援, ML支援    │
       └─────────────────────────────────────┘

    4. Complicated-subsystem Team (複雑サブシステムチーム)
       ┌─────────────────────────────────────┐
       │ 高度な専門知識が必要な領域                │
       │ 例: ML推論エンジン, 暗号化基盤, 動画処理  │p＋＊
       └────────────────────・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・・；。。。。。─────────────────┘
    """)

    # Team interaction modes
    print("  3つのインタラクションモード:")
    print("""
    Collaboration  ──→  密結合、一緒に作る (期間限定)
    X-as-a-Service ──→  API/契約で疎結合
    Facilitating   ──→  支援・コーチング (Enabling Team)
    """)

    # --- 2.2 Cognitive Load Assessment ---
    print("─" * 60)
    print("2.2 チームの認知負荷アセスメント")
    print("─" * 60)

    @dataclass
    class TeamAssessment:
        name: str
        intrinsic: int    # 本質的複雑さ (ドメイン知識)
        extraneous: int   # 外来的複雑さ (ツール・プロセス)
        germane: int      # 有効的複雑さ (学習・成長)
        team_size: int
        services_owned: int
        languages: int
        on_call_burden: int  # 1-10

    teams = [
        TeamAssessment("検索チーム", 7, 5, 6, 6, 4, 2, 4),
        TeamAssessment("決済チーム", 8, 7, 5, 5, 6, 3, 8),
        TeamAssessment("通知チーム", 4, 8, 3, 4, 8, 4, 7),
        TeamAssessment("MLプラットフォーム", 9, 6, 8, 7, 3, 2, 3),
    ]

    print(f"\n  {'Team':<20} {'Intrinsic':>9} {'Extraneous':>10} {'Germane':>8} "
          f"{'Services':>8} {'Load Score':>10} {'Status':>10}")
    print("  " + "-" * 80)

    for t in teams:
        total_load = t.intrinsic + t.extraneous + t.germane
        per_person = total_load / t.team_size
        svc_per_person = t.services_owned / t.team_size
        status = "🔴 過負荷" if per_person > 3.5 or svc_per_person > 1.5 else \
                 "🟡 注意" if per_person > 2.5 else "🟢 適正"
        print(f"  {t.name:<20} {t.intrinsic:>9} {t.extraneous:>10} {t.germane:>8} "
              f"{t.services_owned:>8} {per_person:>9.1f} {status:>10}")

    print("""
    ★ 対策:
    - Extraneous が高い → プラットフォームチームに委譲
    - Services/人 > 1.5 → チーム分割 or サービス統合
    - On-call burden 高 → SRE支援 or 可観測性投資
    """)

    # --- 2.3 Engineering Levels ---
    print("─" * 60)
    print("2.3 Engineering Levels Framework (IC Track)")
    print("─" * 60)

    levels = [
        ("IC3 (Mid)", "機能単位", "個人", "チーム内"),
        ("IC4 (Senior)", "プロジェクト", "チーム", "チーム + 隣接"),
        ("IC5 (Staff)", "複数チームの技術方向", "組織", "部門横断"),
        ("IC6 (Sr. Staff)", "事業部の技術戦略", "事業部", "全社"),
        ("IC7 (Principal)", "会社の技術ビジョン", "会社", "業界"),
    ]

    print(f"\n  {'Level':<18} {'Scope':>20} {'Impact':>10} {'Influence':>15}")
    print("  " + "-" * 65)
    for level, scope, impact, influence in levels:
        print(f"  {level:<18} {scope:>20} {impact:>10} {influence:>15}")

    print("""
    ★ Senior → Staff の壁 (最も多くの人が止まるところ):

    Senior (IC4):
      - 「与えられた問題を高品質に解く」
      - 明確なタスク → 実装 → レビュー → デリバリー
      - チーム内で信頼されるエキスパート

    Staff (IC5):
      - 「解くべき問題を見つけて、組織を動かす」
      - 曖昧な状況 → 問題定義 → 戦略策定 → 複数チーム調整
      - 組織全体の技術品質に責任を持つ

    決定的な違い:
    ┌────────────────────┬────────────────────────┐
    │ Senior              │ Staff+                  │
    ├────────────────────┼────────────────────────┤
    │ 言われたことをやる    │ 何をすべきか決める       │
    │ 自分のコード品質      │ 組織のコード品質          │
    │ チーム内の影響力      │ チームを超えた影響力      │
    │ 技術的に正しい解      │ 組織として最適な解        │
    │ 1つの最適解を追求     │ トレードオフを明示        │
    │ コードで証明          │ ドキュメントで説得        │
    └────────────────────┴────────────────────────┘
    """)

    # --- 2.4 Hiring Loop Design ---
    print("─" * 60)
    print("2.4 面接ループ設計")
    print("─" * 60)
    print("""
    Google-style 面接ループ (Staff+ Engineer):

    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │  Recruiter   │───→│  Tech Screen │───→│  On-site     │
    │  Screen      │    │  (1hr)       │    │  (4-5 rounds)│
    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                  │
                          ┌───────────────────────┼───────────────────────┐
                          │                       │                       │
                    ┌─────┴─────┐           ┌─────┴─────┐          ┌─────┴─────┐
                    │ System     │           │ Coding     │          │ Behavioral │
                    │ Design x2  │           │ x1-2       │          │ x1-2       │
                    └───────────┘           └───────────┘          └───────────┘

    Scorecard 次元:
    1. Technical Competency    (コーディング力)
    2. System Design           (アーキテクチャ設計力)
    3. Problem Solving         (問題解決のアプローチ)
    4. Leadership & Influence  (リーダーシップ)
    5. Communication           (説明力・傾聴力)
    6. Culture Fit / Values    (バリュー適合)

    Bar Raiser (Amazon式):
    - 採用チーム外から参加する独立評価者
    - 「この人は入社後の50%以上より優秀か？」
    - バイアス防止: 急ぎの採用でも基準を下げさせない
    """)


# ============================================================
# Chapter 3: Technical Decision Making at Scale
# ============================================================

def chapter3_decision_making():
    print("\n" + "=" * 70)
    print("Chapter 3: Technical Decision Making at Scale")
    print("  「正しい判断」より「良い判断プロセス」が重要")
    print("=" * 70)

    # --- 3.1 Decision Frameworks ---
    print("\n" + "─" * 60)
    print("3.1 意思決定フレームワーク")
    print("─" * 60)

    print("""
    Amazon の One-Way Door / Two-Way Door:

    ┌─────────────────────────────────────────────┐
    │ Type 1: One-Way Door (不可逆)                │
    │  - 取り消しが困難 or 非常に高コスト            │
    │  - 慎重に、データを集めて、上位で判断           │
    │  - 例: DB移行, 言語変更, SaaS→自社構築        │
    ├─────────────────────────────────────────────┤
    │ Type 2: Two-Way Door (可逆)                   │
    │  - 失敗しても戻せる                           │
    │  - 速く判断、小さく試す                        │
    │  - 例: UIの変更, 新しいライブラリの試用         │
    └─────────────────────────────────────────────┘

    ★ Staff+ のスキル: Type 1 と Type 2 を見極めること。
    多くの判断を Type 2 に変換する力が生産性を決める。
    """)

    # DACI Framework
    print("  DACI Framework (Atlassian):")
    print("""
    ┌──────────────────────────────────────────────────┐
    │ D - Driver     : 意思決定プロセスを推進する人       │
    │                  (1人、Staff+ が担うことが多い)     │
    │ A - Approver   : 最終承認者 (1人)                  │
    │                  (VP/Director レベル)               │
    │ C - Contributor: 意見・専門知識を提供する人          │
    │                  (複数人OK)                         │
    │ I - Informed   : 結果を伝える人                     │
    │                  (影響を受けるチーム)                │
    └──────────────────────────────────────────────────┘

    vs RACI:
    - RACI は「タスクの責任」に適する
    - DACI は「意思決定」に特化
    - Staff+ は DACI の D を務める
    """)

    # --- 3.2 Pre-mortem Analysis ---
    print("─" * 60)
    print("3.2 Pre-mortem 分析")
    print("─" * 60)

    @dataclass
    class Risk:
        description: str
        probability: str  # High/Medium/Low
        impact: str       # High/Medium/Low
        mitigation: str
        owner: str

    print("""
    Pre-mortem: 「このプロジェクトが失敗したと仮定して、
                 なぜ失敗したかを逆算する」

    例: マイクロサービス移行プロジェクト
    """)

    risks = [
        Risk("データ移行でデータ欠損が発生",
             "Medium", "High",
             "Shadow write で並行運用、差分チェックツール実装",
             "Data Team"),
        Risk("レイテンシが 2x に悪化",
             "High", "High",
             "移行前にベンチマーク、Circuit Breaker、フォールバック設計",
             "Platform Team"),
        Risk("チームの認知負荷が想定を超える",
             "High", "Medium",
             "段階的移行、Enabling Team による支援、認知負荷を四半期で計測",
             "Engineering Manager"),
        Risk("SaaS ベンダーが値上げ/サービス終了",
             "Low", "High",
             "抽象化レイヤー実装、マルチベンダー対応設計",
             "Architect"),
        Risk("ビジネス優先度変更で中断",
             "Medium", "Medium",
             "Phase ごとに価値を出す設計、経営層との定期同期",
             "Tech Lead"),
    ]

    impact_map = {"High": 3, "Medium": 2, "Low": 1}

    print(f"  {'Risk':<40} {'Prob':>5} {'Impact':>7} {'Score':>6}")
    print("  " + "-" * 60)
    for r in risks:
        score = impact_map[r.probability] * impact_map[r.impact]
        indicator = "🔴" if score >= 6 else "🟡" if score >= 3 else "🟢"
        print(f"  {r.description:<40} {r.probability:>5} {r.impact:>7} {indicator} {score:>3}")
        print(f"    緩和策: {r.mitigation}")
        print(f"    Owner: {r.owner}")
        print()

    # --- 3.3 Tech Debt Management at Scale ---
    print("─" * 60)
    print("3.3 技術的負債管理 (組織レベル)")
    print("─" * 60)
    print("""
    Martin Fowler の技術的負債 四象限:

                     Deliberate (意図的)
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            │  Prudent    │  Prudent    │
            │  Deliberate │  Inadvertent│
     Reckless│ 「今は出荷   │ 「今振り返る │Prudent
            │  優先、後で  │  とこう書く  │(慎重)
            │  リファクタ」 │  べきだった」│
            │             │             │
            ├─────────────┼─────────────┤
            │             │             │
            │  Reckless   │  Reckless   │
            │  Deliberate │  Inadvertent│
            │ 「設計する   │ 「レイヤリン │
            │  時間ない」  │  グって何？」│
            │             │             │
            └─────────────┼─────────────┘
                          │
                     Inadvertent (無意識)

    ★ Prudent-Deliberate は許容される負債。
    ★ Reckless は早急に対処が必要。
    """)

    # Investment allocation
    print("  エンジニアリング投資配分:")
    allocations = [
        ("New Features", 60, "████████████"),
        ("Tech Debt", 20, "████"),
        ("Keep-the-lights-on", 15, "███"),
        ("Innovation/Spike", 5, "█"),
    ]

    for name, pct, bar in allocations:
        print(f"    {name:<25} {pct:>3}%  {bar}")

    print("""
    ★ 健全な組織: Tech Debt に 15-25% を割く。
    Tech Debt が 0% → 負債が見えてない (危険)
    Tech Debt が 40%+ → 過去の判断のツケ (要経営報告)
    """)

    # --- 3.4 Incident Management at Scale ---
    print("─" * 60)
    print("3.4 イン���デント管理")
    print("─" * 60)

    print("""
    Severity Matrix:

    ┌─────┬────────────────┬───────────────┬──────────────────┐
    │ SEV │ 影響             │ 応答時間       │ エスカレーション    │
    ├─────┼────────────────┼───────────────┼──────────────────┤
    │ SEV1│ 全体障害/データ損失│ 15分以内       │ VP + 全社通知      │
    │ SEV2│ 主要機能の停止    │ 30分以内       │ Director + チーム  │
    │ SEV3│ 部分的機能低下    │ 4時間以内      │ Manager           │
    │ SEV4│ 軽微な問題       │ 翌営業日       │ チーム内           │
    └─────┴────────────────┴───────────────┴──────────────────┘
    """)

    # MTTR/MTTD/MTBF Calculator
    incidents = [
        {"name": "DB failover", "detected_min": 3, "resolved_min": 45},
        {"name": "API latency spike", "detected_min": 8, "resolved_min": 120},
        {"name": "Memory leak", "detected_min": 30, "resolved_min": 90},
        {"name": "Certificate expiry", "detected_min": 1, "resolved_min": 15},
        {"name": "DDoS", "detected_min": 2, "resolved_min": 60},
    ]

    mttd = sum(i["detected_min"] for i in incidents) / len(incidents)
    mttr = sum(i["resolved_min"] for i in incidents) / len(incidents)

    print(f"  インシデントメトリクス (過去5件):")
    print(f"    MTTD (Mean Time To Detect): {mttd:.1f} 分")
    print(f"    MTTR (Mean Time To Resolve): {mttr:.1f} 分")
    print(f"    MTBF (Mean Time Between Failures): {30 * 24 * 60 / len(incidents):.0f} 分 ({30 * 24 / len(incidents):.0f} 時間)")

    print("""
    ★ Postmortem Quality Checklist:
    □ タイムライン (1分単位で正確か)
    □ Root Cause (5 Why で深堀りしたか)
    □ Impact (影響ユーザー数・売上損失を定量化)
    □ Action Items (具体的、期限あり、Owner あり)
    □ What Went Well (良かった点も記録)
    □ Blameless (人ではなくシステムの問題として記述)
    """)


# ============================================================
# Chapter 4: Metrics & Impact Measurement
# ============================================================

def chapter4_metrics():
    print("\n" + "=" * 70)
    print("Chapter 4: Metrics & Impact Measurement")
    print("  測れないものは改善できない — しかし測るものが間違うと害になる")
    print("=" * 70)

    # --- 4.1 DORA Metrics ---
    print("\n" + "─" * 60)
    print("4.1 DORA Metrics (DevOps Research and Assessment)")
    print("─" * 60)

    @dataclass
    class DORAMetrics:
        deployment_freq: str       # per day/week/month
        lead_time: str             # hours/days
        change_failure_rate: float  # percentage
        mttr: str                  # hours

    benchmarks = {
        "Elite": DORAMetrics("On-demand (1日複数回)", "< 1時間", 5.0, "< 1時間"),
        "High": DORAMetrics("1日〜1週間に1回", "1日〜1週間", 10.0, "< 1日"),
        "Medium": DORAMetrics("1週間〜1ヶ月に1回", "1週間〜1ヶ月", 15.0, "< 1週間"),
        "Low": DORAMetrics("1ヶ月〜6ヶ月に1回", "1ヶ月〜6ヶ月", 45.0, "6ヶ月+"),
    }

    print(f"\n  {'Level':<10} {'Deploy Freq':<25} {'Lead Time':<15} {'CFR':>5} {'MTTR':<12}")
    print("  " + "-" * 70)
    for level, m in benchmarks.items():
        print(f"  {level:<10} {m.deployment_freq:<25} {m.lead_time:<15} "
              f"{m.change_failure_rate:>4.0f}% {m.mttr:<12}")

    # Simulate our team's metrics
    our = DORAMetrics("1日3回", "2時間", 8.0, "45分")
    print(f"\n  Our Team: Deploy={our.deployment_freq}, Lead={our.lead_time}, "
          f"CFR={our.change_failure_rate}%, MTTR={our.mttr}")
    print("  → Classification: Elite")

    print("""
    ★ 重要な洞察:
    - Elite チームは速度と安定性を両立する (トレードオフではない)
    - 4つのメトリクスは相関する: 1つ改善すると他も改善する傾向
    - Deployment Frequency が最も改善しやすい starting point
    """)

    # --- 4.2 SPACE Framework ---
    print("\n" + "─" * 60)
    print("4.2 SPACE Framework (Developer Productivity)")
    print("─" * 60)
    print("""
    GitHub/Microsoft Research が提唱。
    「開発者生産性」を多角的に測定する。

    S - Satisfaction & Well-being
        定量: サーベイスコア, NPS, 離職率
        定性: 1:1 での感触, チームの雰囲気

    P - Performance
        定量: デプロイ頻度, SLO達成率, バグ率
        注意: コード行数は使わない

    A - Activity
        定量: PR数, レビュー数, デプロイ数
        注意: 単独では意味がない (ゲーム可能)

    C - Communication & Collaboration
        定量: PR レビュー応答時間, ドキュメント更新頻度
        定性: チーム間の依存関係, ブロッカー発生頻度

    E - Efficiency & Flow
        定量: Flow State 時間, コンテキストスイッチ回数
        定量: CI フィードバック時間, 手戻り率

    ★ 最低 3 つの次元から測定すること。
    1 つだけの測定は常に歪む (Goodhart's Law)。
    """)

    # --- 4.3 Business Impact Translation ---
    print("─" * 60)
    print("4.3 技術指標 → ビジネスインパクト変換")
    print("─" * 60)

    @dataclass
    class ImpactTranslation:
        technical: str
        business: str
        calculation: str

    translations = [
        ImpactTranslation(
            "P99 latency 500ms → 200ms",
            "Conversion +1.2%, Revenue +$3.6M/year",
            "100M visits × 0.012 × $30 avg order"
        ),
        ImpactTranslation(
            "Deploy lead time 1week → 2hours",
            "Feature velocity 5x, TTM -80%",
            "52 deploys/year → 260 deploys/year"
        ),
        ImpactTranslation(
            "Incident MTTR 4h → 30min",
            "Downtime cost saving $2.1M/year",
            "12 incidents × 3.5h saved × $50K/hour"
        ),
        ImpactTranslation(
            "Test coverage 40% → 85%",
            "Production bugs -60%, Support cost -$400K",
            "200 bugs/year → 80 bugs × $5K/bug"
        ),
        ImpactTranslation(
            "Developer onboarding 2weeks → 2days",
            "Hiring ROI +$800K, Productivity +30 dev-weeks",
            "20 hires/year × 8 days saved × $400/day"
        ),
    ]

    print("\n  ★ Staff+ は技術的成果をビジネス言語で語る")
    print()
    for t in translations:
        print(f"  Technical: {t.technical}")
        print(f"  Business:  {t.business}")
        print(f"  Calc:      {t.calculation}")
        print()

    # --- 4.4 OKR Cascade ---
    print("─" * 60)
    print("4.4 OKR カスケード (組織 → チーム → 個人)")
    print("─" * 60)

    okr_tree = {
        "Company": {
            "O": "市場シェアを25%に拡大する",
            "KRs": ["売上 $100M 達成", "NPS 50 以上", "新規顧客 10,000 件"],
            "children": {
                "Eng Org": {
                    "O": "世界最速のプロダクト開発組織になる",
                    "KRs": ["Deploy Frequency: 1日10回", "MTTR < 30分", "Developer NPS > 70"],
                    "children": {
                        "Platform Team": {
                            "O": "開発者が自律的にデリバリーできる基盤を提供",
                            "KRs": ["CI/CD 成功率 99.5%", "Onboarding < 1日", "セルフサービス化率 80%"],
                        },
                        "Search Team": {
                            "O": "検索品質と速度でユーザー体験を差別化",
                            "KRs": ["検索 P50 < 100ms", "Zero-result率 < 5%", "CTR +15%"],
                        },
                    }
                }
            }
        }
    }

    def print_okr(tree, indent=0):
        prefix = "  " * indent
        for name, data in tree.items():
            print(f"{prefix}[{name}]")
            print(f"{prefix}  O: {data['O']}")
            for i, kr in enumerate(data['KRs'], 1):
                print(f"{prefix}  KR{i}: {kr}")
            if 'children' in data:
                print_okr(data['children'], indent + 1)
            print()

    print_okr(okr_tree)

    print("""
    ★ OKR のアンチパターン:
    - KR がタスク (「Terraformを導入する」→ これはイニシアティブ)
    - O が曖昧 (「良いコードを書く」→ 測定不能)
    - 達成率が常に 100% → 野心的でない
    - チーム OKR が会社 OKR と無関係 → アラインメント欠如
    """)


# ============================================================
# Chapter 5: Communication & Influence
# ============================================================

def chapter5_communication():
    print("\n" + "=" * 70)
    print("Chapter 5: Communication & Influence")
    print("  Staff+ の仕事の 50% はコミュニケーション")
    print("=" * 70)

    # --- 5.1 Executive Communication ---
    print("\n" + "─" * 60)
    print("5.1 エグゼクティブコミュニケーション")
    print("─" * 60)
    print("""
    BLUF (Bottom Line Up Front):
    結論を最初に言う。背景説明から始めない。

    ✗ Bad:
    「先週からパフォーマンスの調査をしていて、DBのクエリを
     分析したところ、N+1問題が見つかって、ORMの設定を変更
     したら改善して、結果的にP99が500msから200msに...」

    ✓ Good:
    「P99レイテンシを500ms→200msに改善しました。
     原因はDBのN+1問題で、クエリバッチ化で解決。
     Conversionが1.2%向上する見込みです。」

    構造:
    1. 結論/推奨 (1文)
    2. インパクト (数字で)
    3. 根拠 (2-3点)
    4. リスク/次のステップ
    """)

    # --- 5.2 RFC Writing ---
    print("─" * 60)
    print("5.2 RFC (Request for Comments) テンプレート")
    print("─" * 60)
    print("""
    ┌──────────────────────────────────────────────────┐
    │ RFC-2026-003: [タイトル]                           │
    │ Author: [名前]     Status: [Draft/Review/Accepted] │
    │ Date: 2026-03-09   Reviewers: [名前1, 名前2]      │
    ├──────────────────────────────────────────────────┤
    │                                                   │
    │ ## TL;DR (3行以内)                                 │
    │                                                   │
    │ ## Problem Statement                              │
    │ 何が問題で、なぜ今解決する必要があるか               │
    │ データ: 影響ユーザー数、コスト、頻度                 │
    │                                                   │
    │ ## Goals                                          │
    │ この RFC で達成したいこと (2-3点、測定可能)          │
    │                                                   │
    │ ## Non-Goals                                      │
    │ 明示的にスコープ外とすること                        │
    │ (これがないと scope creep する)                     │
    │                                                   │
    │ ## Proposed Solution                              │
    │ アーキテクチャ図、データフロー、API設計              │
    │ 移行計画、ロールバック計画                          │
    │                                                   │
    │ ## Alternatives Considered                        │
    │ Option A: [概要] — 却下理由                        │
    │ Option B: [概要] — 却下理由                        │
    │ (最低2つの代替案を検討した証拠)                     │
    │                                                   │
    │ ## Risks & Mitigations                            │
    │ リスク1: [内容] → 緩和策                           │
    │                                                   │
    │ ## Timeline                                       │
    │ Phase 1 (Week 1-2): ...                           │
    │                                                   │
    │ ## Open Questions                                 │
    │ 議論が必要な未決事項                               │
    └──────────────────────────────────────────────────┘

    ★ RFC の目的は「承認を得る」ではなく「良い判断をする」。
    反対意見は歓迎。Disagree & Commit を促す。
    """)

    # --- 5.3 Pyramid Principle ---
    print("─" * 60)
    print("5.3 Pyramid Principle (Minto)")
    print("─" * 60)
    print("""
    Barbara Minto (McKinsey) の論理的思考法。
    Staff+ の提案・プレゼンの基本構造。

                    ┌─────────────┐
                    │   Main Point │  ← 最初に結論
                    └──────┬──────┘
              ┌────────────┼────────────┐
         ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
         │ Reason 1│  │ Reason 2│  │ Reason 3│  ← 根拠 (3つ)
         └────┬────┘  └────┬────┘  └────┬────┘
           ┌──┴──┐     ┌──┴──┐     ┌──┴──┐
           │Data │     │Data │     │Data │       ← 裏付け
           └─────┘     └─────┘     └─────┘

    MECE (Mutually Exclusive, Collectively Exhaustive):
    根拠は「漏れなく、ダブりなく」

    例: 「マイクロサービス移行を提案します」

    Main: モノリスからマイクロサービスへの段階的移行を推奨
    ├─ Reason 1: デプロイ速度が 10x 向上 (現在: 月1回→週5回)
    │  └─ Data: 競合他社は日次デプロイ、市場機会の損失 $5M/年
    ├─ Reason 2: チームの独立性向上 (依存関係による待ち 30%削減)
    │  └─ Data: 現在チーム間ブロッカー 平均 3日/sprint
    └─ Reason 3: 段階的移行により Risk を最小化
       └─ Data: Strangler Fig パターン、3チームが先行移行で検証済
    """)

    # --- 5.4 Difficult Conversations ---
    print("─" * 60)
    print("5.4 困難な会話のフレームワーク")
    print("─" * 60)
    print("""
    Staff+ は以下の困難な会話を避けられない:

    1. 技術的方向性の不一致
       Framework: "I think we're solving different problems"
       → 問題定義の合意から始める (解決策ではなく)

    2. プロジェ��ト中止の提案
       Framework: Sunk Cost を認め、Opportunity Cost を提示
       → 「投資した X は無駄ではなく学びだが、
          Y に投資した方が組織として Z のリターンがある」

    3. パフォーマンス問題のフィードバック
       SBI (Situation-Behavior-Impact):
       → 「先週のレビュー(S)で、コードの問題点だけ指摘し
          代替案を示さなかった(B)。ジュニアが萎縮して
          質問しなくなった(I)」

    4. 上位マネジメントへの Bad News
       → 問題 + 影響範囲 + 提案する対策 を同時に伝える
       → 「問題があります」で終わらない

    5. チーム間の対立調停
       → 双方の Interests (利害) を聞き出す
       → Position (主張) ではなく Interest で解決策を探す
       → Fisher & Ury の "Getting to Yes"
    """)

    # --- 5.5 Managing Up ---
    print("─" * 60)
    print("5.5 Managing Up (上位層への影響力)")
    print("─" * 60)
    print("""
    Staff+ が VP/Director と効果的に協働するためのパターン:

    1. No Surprises Rule
       悪いニュースは早く伝える。「知らなかった」は最悪の状態。

    2. Options, Not Problems
       「Xが問題です」→「Xが問題で、A/B/Cの3つの選択肢があり、
       Bを推奨します。理由は...」

    3. Signal vs Noise
       すべてを報告しない。経営判断に影響するものだけ上げる。
       判断基準: 「これを知らないとDirectorが困るか？」

    4. Calibrate Autonomy
       → 新しいマネージャー: 頻繁に状況共有、信頼構築
       → 信頼関係あり: 大きな判断のみ相談、結果を報告

    5. Weekly Status (RAG format)
       🔴 Red:   即座にアクション必要
       🟡 Amber: リスクあり、モニタリング中
       🟢 Green: 計画通り
       → 3行以内で、Action Required を明記
    """)


# ============================================================
# Chapter 6: Staff+ Interview Preparation
# ============================================================

def chapter6_interview():
    print("\n" + "=" * 70)
    print("Chapter 6: Staff+ Interview Preparation")
    print("  Senior 面接と Staff+ 面接は別の試験")
    print("=" * 70)

    # --- 6.1 System Design at Staff+ Level ---
    print("\n" + "─" * 60)
    print("6.1 Staff+ System Design (プラットフォーム設計)")
    print("─" * 60)
    print("""
    Senior の System Design: 「Twitter のタイムラインを設計して」
    Staff+ の System Design: 「1000人のエンジニアが使う CI/CD 基盤を設計して」

    違い:
    ┌─────────────────────┬────────────────────────────┐
    │ Senior               │ Staff+                      │
    ├─────────────────────┼────────────────────────────┤
    │ 1つのシステム設計      │ プラットフォーム/基盤設計     │
    │ 技術的な深さ           │ 技術 + 組織 + プロセス       │
    │ 正しいアーキテクチャ    │ 進化可能なアーキテクチャ     │
    │ スケーラビリティ       │ + 開発者体験 + 移行計画      │
    │ 45分で完結            │ 複数フェーズの段階的設計      │
    └─────────────────────┴────────────────────────────┘

    例: 「1000人のエンジニアのための CI/CD プラットフォーム」

    Phase 1: Requirements (5分)
    - 機能要件: build, test, deploy, rollback
    - 非機能: 1000+ pipelines/day, P95 < 15min, 99.9% availability
    - 組織: 50 チーム, 10 言語, monorepo + polyrepo 混在
    - 制約: 既存 Jenkins からの移行

    Phase 2: High-Level Architecture (10分)
    - API Layer → Queue → Worker Pool → Artifact Store
    - Multi-tenant isolation (チーム間の影響隔離)
    - Plugin system (各チームがカスタマイズ可能)

    Phase 3: Deep Dives (15分)
    - Scheduling: どうやって 1000 parallel builds を効率的に?
    - Caching: build cache, test cache, Docker layer cache
    - Security: secrets management, supply chain security
    - Observability: pipeline analytics, bottleneck detection

    Phase 4: Migration & Adoption (10分)  ← Staff+ ならでは
    - Strangler Fig: Jenkins → 新基盤を段階的に
    - Adoption metrics: 移行チーム数, 自発的採用率
    - Rollback plan: 新基盤に問題あれば Jenkins に戻せる
    - Team support: Enabling Team による移行支援

    Phase 5: Evolution (5分)  ← Staff+ ならでは
    - 今後の拡張: AI-powered test selection, auto-scaling
    - 技術的負債の管理方針
    - チームの成長計画
    """)

    # --- 6.2 Behavioral at Staff+ Level ---
    print("─" * 60)
    print("6.2 Behavioral Interview (Staff+ Level)")
    print("─" * 60)

    behavioral_questions = [
        {
            "question": "Tell me about a time you influenced a technical decision across multiple teams.",
            "what_they_want": "組織を動かす力、Disagree & Commit、データ駆動の説得",
            "star_template": textwrap.dedent("""\
                S: 3チームが異なるメッセージキューを使用 (Kafka/SQS/RabbitMQ)
                T: 統一して運用コスト削減 + 専門知識集約する必要
                A: 1) 各チームのユースケースを分析
                   2) RFC を書いて全チームのレビューを募集
                   3) PoC で性能比較データを提示
                   4) 反対意見を受け入れて設計修正
                R: Kafka に統一、運用コスト 40%削減、MTTR 60%改善
                   (定量的インパクトを必ず含める)"""),
        },
        {
            "question": "Describe a situation where you had to navigate ambiguity.",
            "what_they_want": "曖昧さの中で方向性を定める力、仮説駆動",
            "star_template": textwrap.dedent("""\
                S: 経営から「AIを活用して生産性向上」という漠然な指示
                T: 具体的な計画と成果指標を定義する
                A: 1) 開発者50人にインタビューで Pain Point 特定
                   2) 3つの仮説を立て、最小限の PoC で検証
                   3) データに基づき優先順位を決定
                   4) 段階的ロードマップを経営に提示
                R: Code Review AI 導入でレビュー時間 50%削減
                   (曖昧→具体化のプロセスを見せる)"""),
        },
        {
            "question": "How have you mentored or grown other engineers?",
            "what_they_want": "multiplier effect — 自分がいなくても組織が機能する",
            "star_template": textwrap.dedent("""\
                S: チームに Mid-level 5人、Senior候補なし
                T: 1年で2人を Senior に成長させる
                A: 1) 個別の成長計画を Strategy Session で策定
                   2) Stretch assignment: 各自にシステム設計をリード
                   3) 週次1:1でフィードバック + ブロッカー除去
                   4) 社内勉強会の運営を委譲
                R: 2人が Senior に昇格、1人が Tech Lead に
                   (Multiplier: 自分のアウトプットではなく、
                    チームのアウトプットの向上を語る)"""),
        },
    ]

    for q in behavioral_questions:
        print(f"\n  Q: {q['question']}")
        print(f"  求められること: {q['what_they_want']}")
        print(f"  STAR Template:")
        for line in q['star_template'].split('\n'):
            print(f"    {line}")
        print()

    # --- 6.3 Career Level Gap Analysis ---
    print("─" * 60)
    print("6.3 Career Level Gap Analysis Tool")
    print("─" * 60)

    dimensions = [
        "Technical Depth",
        "Technical Breadth",
        "System Design",
        "Execution",
        "Communication",
        "Leadership",
        "Strategic Thinking",
        "Mentorship",
    ]

    # Simulate: current (Senior) vs target (Staff)
    current = [8, 5, 6, 8, 5, 4, 3, 4]
    target =  [8, 7, 8, 8, 7, 7, 7, 7]

    print(f"\n  {'Dimension':<22} {'Current':>8} {'Target':>8} {'Gap':>5} {'Priority':>10}")
    print("  " + "-" * 56)

    gaps = []
    for dim, cur, tgt in zip(dimensions, current, target):
        gap = tgt - cur
        priority = "🔴 HIGH" if gap >= 3 else "🟡 MED" if gap >= 2 else "🟢 OK"
        print(f"  {dim:<22} {cur:>8} {tgt:>8} {gap:>5} {priority:>10}")
        gaps.append((dim, gap))

    # Radar chart (ASCII)
    print("\n  Skill Radar (Current ● vs Target ○):")
    max_val = 10
    for dim, cur, tgt in zip(dimensions, current, target):
        cur_bar = "█" * cur + "░" * (tgt - cur) + "·" * (max_val - tgt)
        print(f"  {dim:<22} |{cur_bar}| {cur}/{tgt}")

    # Top gaps
    gaps.sort(key=lambda x: x[1], reverse=True)
    print("\n  Development Plan (優先順位):")
    for i, (dim, gap) in enumerate(gaps[:4], 1):
        actions = {
            "Strategic Thinking": "Tech Vision document を書く、経営会議に参加、業界トレンド分析",
            "Leadership": "チーム横断プロジェクトをリード、RFC プロセス導入、メンタリング",
            "Mentorship": "1:1 で成長計画策定、Tech Talk 運営委譲、ペアプロ習慣化",
            "Communication": "RFC 月1本執筆、All-Hands で発表、ブログ記事公開",
            "Technical Breadth": "隣接チームの設計レビュー参加、OSS コントリビュート",
            "System Design": "週1回のmock interview、Designing Data-Intensive Applications 読了",
        }
        action = actions.get(dim, "具体的なアクションを設定")
        if gap > 0:
            print(f"    {i}. {dim} (gap: {gap})")
            print(f"       Action: {action}")
            print()


# ============================================================
# Main
# ============================================================

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  Staff+ Engineering Leadership                                 ║")
    print("║  Senior → Staff/Principal への道                               ║")
    print("║  「コードを書く人」から「組織を動かす人」へ                      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    chapter1_technical_strategy()
    chapter2_org_design()
    chapter3_decision_making()
    chapter4_metrics()
    chapter5_communication()
    chapter6_interview()

    print("\n" + "=" * 70)
    print("Summary: Staff+ Engineer の 5 つの柱")
    print("=" * 70)
    print("""
    1. Technical Vision    — 組織の技術方向を示す
    2. Organizational      — チームが最大限機能する構造を作る
    3. Decision Making     — 大きな判断を良いプロセスで行う
    4. Metrics & Impact    — 技術をビジネス言語で語る
    5. Communication       — 影響力で組織を動かす

    推奨書籍:
    - "Staff Engineer" by Will Larson
    - "An Elegant Puzzle" by Will Larson
    - "The Manager's Path" by Camille Fournier
    - "Designing Data-Intensive Applications" by Martin Kleppmann
    - "Team Topologies" by Skelton & Pais
    - "The Pyramid Principle" by Barbara Minto
    """)


if __name__ == "__main__":
    main()
