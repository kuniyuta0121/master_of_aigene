#!/usr/bin/env python3
"""
Production Engineering / On-Call / デバッグ方法論ガイド
=====================================================

本番運用に必要な障害対応・デバッグ・キャパシティプランニング・
デプロイ安全性・SLA/SLO管理を体系的に学ぶモジュール。

実行: python production_engineering.py
"""

import json
import math
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


# ============================================================
# 1. 障害対応フレームワーク (Incident Response)
# ============================================================

class Severity(Enum):
    """障害の重大度レベル"""
    SEV1 = 1  # サービス全体停止 / データ損失
    SEV2 = 2  # 主要機能の大幅劣化
    SEV3 = 3  # 一部機能に影響、回避策あり
    SEV4 = 4  # 軽微な問題、次スプリントで対応可


# --- Severity 分類とSLA ---
SEVERITY_SLA = {
    Severity.SEV1: {
        "応答時間": "5分以内",
        "更新頻度": "15分毎",
        "解決目標": "1時間以内",
        "関係者通知": "VP以上 + 全エンジニア",
        "War Room": True,
        "StatusPage": "Major Outage",
        "例": "決済不能 / 全ユーザーアクセス不可 / データ損失",
    },
    Severity.SEV2: {
        "応答時間": "15分以内",
        "更新頻度": "30分毎",
        "解決目標": "4時間以内",
        "関係者通知": "EM + On-Callチーム",
        "War Room": True,
        "StatusPage": "Partial Outage",
        "例": "主要APIの50%以上がエラー / レイテンシ10倍以上",
    },
    Severity.SEV3: {
        "応答時間": "1時間以内",
        "更新頻度": "2時間毎",
        "解決目標": "24時間以内",
        "関係者通知": "On-Callエンジニア",
        "War Room": False,
        "StatusPage": "Degraded Performance",
        "例": "一部エンドポイントの遅延 / 非主要機能の障害",
    },
    Severity.SEV4: {
        "応答時間": "次営業日",
        "更新頻度": "必要に応じて",
        "解決目標": "1週間以内",
        "関係者通知": "チケット起票のみ",
        "War Room": False,
        "StatusPage": "不要",
        "例": "UIの軽微な表示崩れ / ログの警告レベル増加",
    },
}


@dataclass
class OODALoop:
    """
    OODA Loop — 障害対応の意思決定フレームワーク
    軍事戦略家ジョン・ボイドが提唱。
    高速で繰り返すことが重要（ループの速度が勝敗を分ける）。
    """
    incident_id: str
    severity: Severity
    iterations: list = field(default_factory=list)

    def observe(self, observations: list[str]) -> dict:
        """Observe: 何が起きているかを観察する"""
        # アラート、メトリクス、ログ、ユーザー報告を収集
        return {
            "phase": "Observe",
            "timestamp": datetime.now().isoformat(),
            "data": observations,
            "questions": [
                "いつから発生しているか？",
                "影響範囲はどこまでか？",
                "何が変わったか？(デプロイ/設定変更/トラフィック)",
                "関連するメトリクスに異常はあるか？",
            ],
        }

    def orient(self, observations: dict, hypotheses: list[str]) -> dict:
        """Orient: 状況を分析し、仮説を立てる"""
        # 過去の類似障害、メンタルモデル、経験を活用
        return {
            "phase": "Orient",
            "timestamp": datetime.now().isoformat(),
            "observations_summary": observations,
            "hypotheses": hypotheses,
            "priority_hypothesis": hypotheses[0] if hypotheses else "不明",
            "checklist": [
                "直近のデプロイ確認",
                "依存サービスの状態確認",
                "リソース使用率確認 (CPU/Mem/Disk/Net)",
                "エラーログのパターン分析",
            ],
        }

    def decide(self, orientation: dict, action_plan: str) -> dict:
        """Decide: 対処方針を決定する"""
        return {
            "phase": "Decide",
            "timestamp": datetime.now().isoformat(),
            "chosen_hypothesis": orientation["priority_hypothesis"],
            "action_plan": action_plan,
            "rollback_plan": "効果なしの場合のフォールバック手順を明記",
            "risk_assessment": "対処により追加リスクがないか確認",
        }

    def act(self, decision: dict, result: str) -> dict:
        """Act: 対処を実行し、結果を観察する"""
        iteration = {
            "phase": "Act",
            "timestamp": datetime.now().isoformat(),
            "action_taken": decision["action_plan"],
            "result": result,
            "resolved": "解決" in result or "回復" in result,
        }
        self.iterations.append(iteration)
        return iteration

    def run_loop(self, observations, hypotheses, action_plan, result):
        """OODAループ1回転を実行"""
        obs = self.observe(observations)
        orient = self.orient(obs, hypotheses)
        decide = self.decide(orient, action_plan)
        act = self.act(decide, result)
        return {
            "incident_id": self.incident_id,
            "severity": self.severity.name,
            "loop_count": len(self.iterations),
            "phases": [obs, orient, decide, act],
            "resolved": act["resolved"],
        }


def generate_war_room_procedure() -> dict:
    """War Room の運営手順"""
    return {
        "開始条件": "SEV1 または SEV2 が宣言された時",
        "役割分担": {
            "Incident Commander (IC)": "全体統括。意思決定の最終権限",
            "Communication Lead": "ステークホルダーへの状況報告",
            "Operations Lead": "実際の調査・復旧作業の指揮",
            "Scribe": "タイムライン・決定事項の記録",
        },
        "手順": [
            "1. IC がチャンネル/通話を開設",
            "2. 参加者の役割を明確にアナウンス",
            "3. 現状の共有 (Observe フェーズの結果)",
            "4. 仮説の列挙と優先順位付け",
            "5. 調査タスクの分担（並列実行を意識）",
            "6. 15分毎にチェックポイント",
            "7. 解決確認後、モニタリング期間を設定",
            "8. War Room クローズ宣言",
        ],
        "禁止事項": [
            "犯人探し（Blameless を徹底）",
            "ICの許可なく本番変更を行うこと",
            "未確認情報の外部発信",
        ],
    }


def generate_comms_template(
    severity: Severity, service: str, summary: str, eta: str
) -> dict:
    """障害コミュニケーションテンプレート"""
    slack_template = textwrap.dedent(f"""\
        :rotating_light: *[{severity.name}] {service} 障害発生*
        ━━━━━━━━━━━━━━━━━━━
        *概要*: {summary}
        *影響*: ユーザーへの影響を記載
        *ステータス*: 調査中
        *IC*: @担当者名
        *復旧見込み*: {eta}
        *次回更新*: {SEVERITY_SLA[severity]['更新頻度']}後
        ━━━━━━━━━━━━━━━━━━━
        :thread: 詳細はスレッドで更新します
    """)

    statuspage_template = textwrap.dedent(f"""\
        Title: [{severity.name}] {service} Service Disruption
        Status: {SEVERITY_SLA[severity]['StatusPage']}
        Body:
        We are currently investigating an issue affecting {service}.
        Summary: {summary}
        Estimated resolution: {eta}
        We will provide updates every {SEVERITY_SLA[severity]['更新頻度']}.
    """)

    return {
        "slack": slack_template,
        "statuspage": statuspage_template,
        "escalation_targets": SEVERITY_SLA[severity]["関係者通知"],
    }


# ============================================================
# 2. 体系的デバッグ手法
# ============================================================

def use_method_checklist(resource: str = "all") -> dict:
    """
    USE Method — Brendan Gregg が提唱
    すべてのリソースに対して Utilization / Saturation / Errors を確認

    リソースごとに具体的なコマンド・メトリクスを提示
    """
    checks = {
        "CPU": {
            "Utilization": {
                "what": "CPU使用率（user + system）",
                "commands": ["top -bn1", "mpstat -P ALL 1", "vmstat 1"],
                "metrics": ["system.cpu.user", "system.cpu.system"],
                "threshold": "持続的に >80% は要注意",
            },
            "Saturation": {
                "what": "実行待ちプロセス数（ロードアベレージ）",
                "commands": ["uptime", "cat /proc/loadavg"],
                "metrics": ["system.load.1", "system.load.5"],
                "threshold": "コア数を超えたら飽和",
            },
            "Errors": {
                "what": "CPU関連エラー（MCE等）",
                "commands": ["dmesg | grep -i mce", "perf stat -a sleep 5"],
                "metrics": ["hardware.cpu.errors"],
                "threshold": "0 でなければ調査",
            },
        },
        "Memory": {
            "Utilization": {
                "what": "メモリ使用率",
                "commands": ["free -m", "cat /proc/meminfo"],
                "metrics": ["system.mem.used_percent"],
                "threshold": ">90% かつ swap 使用中は危険",
            },
            "Saturation": {
                "what": "ページスワップ・OOMの発生",
                "commands": ["vmstat 1 (si/so列)", "dmesg | grep -i oom"],
                "metrics": ["system.swap.used", "system.mem.oom_kill"],
                "threshold": "swap I/O > 0 は性能劣化のサイン",
            },
            "Errors": {
                "what": "メモリアロケーション失敗",
                "commands": ["dmesg | grep -i 'out of memory'"],
                "metrics": ["process.memory.allocation_failures"],
                "threshold": "発生したら即対応",
            },
        },
        "Disk": {
            "Utilization": {
                "what": "ディスク使用率・I/O使用率",
                "commands": ["df -h", "iostat -x 1"],
                "metrics": ["system.disk.used_percent", "system.io.util"],
                "threshold": ">85% で警告、>95% で危険",
            },
            "Saturation": {
                "what": "I/Oキュー長",
                "commands": ["iostat -x 1 (avgqu-sz列)", "iotop"],
                "metrics": ["system.io.queue_length"],
                "threshold": "avgqu-sz > 1 で飽和傾向",
            },
            "Errors": {
                "what": "ディスクI/Oエラー",
                "commands": ["dmesg | grep -i 'i/o error'", "smartctl -a /dev/sda"],
                "metrics": ["system.disk.errors"],
                "threshold": "エラー発生でディスク交換検討",
            },
        },
        "Network": {
            "Utilization": {
                "what": "帯域使用率",
                "commands": ["sar -n DEV 1", "ip -s link"],
                "metrics": ["system.net.bytes_sent", "system.net.bytes_recv"],
                "threshold": "帯域の >70% で注意",
            },
            "Saturation": {
                "what": "TCPリトランスミット・ドロップ",
                "commands": ["netstat -s | grep retrans", "ss -s"],
                "metrics": ["system.net.tcp.retransmits"],
                "threshold": "retransmit増加は輻輳のサイン",
            },
            "Errors": {
                "what": "パケットエラー・ドロップ",
                "commands": ["ip -s link (errorsの行)", "ethtool -S eth0"],
                "metrics": ["system.net.errors", "system.net.drops"],
                "threshold": "0 でなければ調査",
            },
        },
    }
    if resource == "all":
        return checks
    return checks.get(resource, {"error": f"未知のリソース: {resource}"})


def red_method_checklist(service_type: str = "all") -> dict:
    """
    RED Method — Tom Wilkie が提唱
    サービス（リクエスト駆動型ワークロード）ごとに
    Rate / Errors / Duration を確認
    """
    checks = {
        "API Gateway": {
            "Rate": {
                "what": "リクエスト/秒",
                "metrics": ["http.requests.count", "nginx.requests.total"],
                "alert_on": "急激な増減（通常の2倍以上、または50%以下）",
            },
            "Errors": {
                "what": "エラー率 (4xx/5xx)",
                "metrics": ["http.errors.5xx.rate", "http.errors.4xx.rate"],
                "alert_on": "5xx > 1% または 4xx の急増",
            },
            "Duration": {
                "what": "レイテンシ (p50/p95/p99)",
                "metrics": ["http.request.duration.p50", "http.request.duration.p99"],
                "alert_on": "p99 > SLO閾値 または p50 の2倍以上の悪化",
            },
        },
        "Database": {
            "Rate": {
                "what": "クエリ/秒",
                "metrics": ["db.queries.count", "db.connections.active"],
                "alert_on": "クエリ数の急増 or コネクション枯渇",
            },
            "Errors": {
                "what": "クエリエラー率",
                "metrics": ["db.queries.errors", "db.deadlocks"],
                "alert_on": "エラー > 0 またはデッドロック検出",
            },
            "Duration": {
                "what": "クエリ実行時間",
                "metrics": ["db.query.duration.p95", "db.slow_queries.count"],
                "alert_on": "スロークエリ急増 or p95 > 100ms",
            },
        },
        "Message Queue": {
            "Rate": {
                "what": "メッセージ処理レート",
                "metrics": ["queue.messages.published", "queue.messages.consumed"],
                "alert_on": "published >> consumed (バックログ蓄積)",
            },
            "Errors": {
                "what": "処理失敗・DLQ行き",
                "metrics": ["queue.messages.failed", "queue.dlq.count"],
                "alert_on": "DLQ が増加傾向",
            },
            "Duration": {
                "what": "処理時間・キュー滞留時間",
                "metrics": ["queue.message.age", "queue.consumer.lag"],
                "alert_on": "consumer lag が増加傾向",
            },
        },
    }
    if service_type == "all":
        return checks
    return checks.get(service_type, {"error": f"未知のサービスタイプ: {service_type}"})


class FiveWhys:
    """5 Whys 分析ツール — 根本原因分析 (RCA)"""

    def __init__(self, problem: str):
        self.problem = problem
        self.chain: list[dict] = []

    def ask_why(self, answer: str, evidence: str = "") -> "FiveWhys":
        """なぜ？に対する回答を追加"""
        depth = len(self.chain) + 1
        self.chain.append({
            "depth": depth,
            "question": f"なぜ{depth}: "
                        + (self.chain[-1]["answer"] if self.chain else self.problem)
                        + " が発生したのか？",
            "answer": answer,
            "evidence": evidence,
        })
        return self  # メソッドチェーン可能

    def get_root_cause(self) -> str:
        """最後の回答を根本原因とする"""
        if not self.chain:
            return "分析未実施"
        return self.chain[-1]["answer"]

    def report(self) -> str:
        lines = [f"=== 5 Whys 分析 ===", f"問題: {self.problem}", ""]
        for item in self.chain:
            lines.append(f"  {item['question']}")
            lines.append(f"  → {item['answer']}")
            if item["evidence"]:
                lines.append(f"    (根拠: {item['evidence']})")
            lines.append("")
        lines.append(f"根本原因: {self.get_root_cause()}")
        return "\n".join(lines)


@dataclass
class FaultTreeNode:
    """故障木分析 (FTA) のノード"""
    event: str
    gate: str = "AND"  # "AND" or "OR"
    probability: float = 0.0  # 基本事象の場合の発生確率
    children: list = field(default_factory=list)

    def calculate_probability(self) -> float:
        """ゲートタイプに応じた確率計算"""
        if not self.children:
            return self.probability  # 基本事象（リーフ）

        child_probs = [c.calculate_probability() for c in self.children]
        if self.gate == "AND":
            # AND: すべてが発生する確率 = 各確率の積
            result = 1.0
            for p in child_probs:
                result *= p
            return result
        elif self.gate == "OR":
            # OR: いずれかが発生する確率 = 1 - (すべて発生しない確率)
            result = 1.0
            for p in child_probs:
                result *= (1 - p)
            return 1 - result
        return 0.0

    def display(self, indent: int = 0) -> str:
        """ツリー構造を文字列で表示"""
        prefix = "  " * indent
        prob = self.calculate_probability()
        gate_str = f" [{self.gate}]" if self.children else " (基本事象)"
        lines = [f"{prefix}├── {self.event}{gate_str} P={prob:.6f}"]
        for child in self.children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)


def binary_search_debug(versions: list[str], is_broken) -> dict:
    """
    二分探索デバッグ — git bisect の一般化
    バグが混入したバージョン/コミットを効率的に特定する

    Args:
        versions: 時系列順のバージョンリスト（古い→新しい）
        is_broken: バージョンを受け取り、壊れているか判定する関数
    """
    left, right = 0, len(versions) - 1
    steps = []
    total_checks = 0

    while left < right:
        mid = (left + right) // 2
        total_checks += 1
        broken = is_broken(versions[mid])
        steps.append({
            "step": total_checks,
            "checking": versions[mid],
            "index": mid,
            "result": "broken" if broken else "good",
            "remaining_range": f"{versions[left]} ~ {versions[right]}",
        })
        if broken:
            right = mid
        else:
            left = mid + 1

    return {
        "first_broken_version": versions[left],
        "total_versions": len(versions),
        "checks_performed": total_checks,
        "theoretical_max_checks": math.ceil(math.log2(len(versions))),
        "steps": steps,
    }


# ============================================================
# 3. Postmortem テンプレート + 実例
# ============================================================

BLAMELESS_PRINCIPLES = [
    "個人を非難しない — システムと仕組みの改善に焦点を当てる",
    "障害は学習の機会 — 起こるべくして起きた結果と捉える",
    "再発防止が目的 — 犯人探しではなく、同じ失敗を繰り返さない仕組みを作る",
    "心理的安全性の確保 — 正直に報告できる文化が品質を上げる",
    "ヒューマンエラーは原因ではなく症状 — なぜその操作が可能だったか？を問う",
]


@dataclass
class PostmortemEntry:
    """Postmortem テンプレート"""
    title: str
    date: str
    severity: Severity
    duration: str
    authors: list[str]
    summary: str
    impact: dict       # ユーザー影響・ビジネス影響
    timeline: list[dict]  # [{time, event}]
    root_cause: str
    contributing_factors: list[str]
    detection: str     # どうやって検知したか
    resolution: str    # どうやって解決したか
    action_items: list[dict]  # [{action, owner, priority, deadline}]
    lessons_learned: list[str]

    def to_report(self) -> str:
        lines = [
            f"{'='*60}",
            f"POSTMORTEM: {self.title}",
            f"{'='*60}",
            f"日付: {self.date}",
            f"重大度: {self.severity.name}",
            f"継続時間: {self.duration}",
            f"執筆者: {', '.join(self.authors)}",
            "",
            f"## 概要",
            self.summary,
            "",
            f"## 影響",
        ]
        for k, v in self.impact.items():
            lines.append(f"  - {k}: {v}")
        lines.extend(["", "## タイムライン"])
        for entry in self.timeline:
            lines.append(f"  {entry['time']} - {entry['event']}")
        lines.extend([
            "", "## 根本原因", f"  {self.root_cause}",
            "", "## 寄与要因",
        ])
        for f in self.contributing_factors:
            lines.append(f"  - {f}")
        lines.extend([
            "", f"## 検知方法", f"  {self.detection}",
            "", f"## 解決方法", f"  {self.resolution}",
            "", "## アクションアイテム",
        ])
        for ai in self.action_items:
            lines.append(
                f"  [{ai['priority']}] {ai['action']} "
                f"(担当: {ai['owner']}, 期限: {ai['deadline']})"
            )
        lines.extend(["", "## 教訓"])
        for l in self.lessons_learned:
            lines.append(f"  - {l}")
        return "\n".join(lines)


def postmortem_examples() -> list[PostmortemEntry]:
    """3つの実例 Postmortem"""
    examples = []

    # --- 実例1: DBコネクションプール枯渇 ---
    examples.append(PostmortemEntry(
        title="DBコネクションプール枯渇によるAPI全断",
        date="2025-11-15",
        severity=Severity.SEV1,
        duration="47分",
        authors=["田中", "鈴木"],
        summary="新機能デプロイ後、DBコネクションプールが枯渇し "
                "全APIエンドポイントが503を返す状態が47分間続いた。",
        impact={
            "影響ユーザー数": "全ユーザー（約50万人）",
            "エラー率": "100%（全リクエスト503）",
            "推定損失": "約300万円（EC売上逸失）",
        },
        timeline=[
            {"time": "14:00", "event": "新機能リリースのデプロイ完了"},
            {"time": "14:12", "event": "DB接続エラーのアラート発報"},
            {"time": "14:15", "event": "IC が SEV1 宣言、War Room 開設"},
            {"time": "14:20", "event": "全APIが503を返していることを確認"},
            {"time": "14:25", "event": "DBコネクション数が上限に張り付いていることを確認"},
            {"time": "14:30", "event": "新機能のコードにコネクションリークを発見"},
            {"time": "14:35", "event": "ロールバック開始"},
            {"time": "14:47", "event": "ロールバック完了、コネクション回復"},
            {"time": "14:59", "event": "エラー率0%確認、SEV1クローズ"},
        ],
        root_cause="新機能のバッチ処理で try-finally を使わずにDB接続を取得しており、"
                   "例外発生時にコネクションが返却されなかった。",
        contributing_factors=[
            "コードレビューでリソース管理のチェックリストがなかった",
            "コネクションプールの監視アラートの閾値が高すぎた（90%で初報）",
            "ステージング環境のDB接続数が本番と異なり再現しなかった",
        ],
        detection="Datadog のDB接続数アラート（閾値90%）",
        resolution="該当デプロイをロールバック。その後 with 文（コンテキストマネージャ）"
                   "でリソース管理を修正し再デプロイ。",
        action_items=[
            {"action": "コネクション管理の静的解析ルール追加", "owner": "田中",
             "priority": "P0", "deadline": "2025-11-22"},
            {"action": "コネクションプール閾値を70%に下げる", "owner": "鈴木",
             "priority": "P0", "deadline": "2025-11-17"},
            {"action": "ステージング環境のDB設定を本番と同期", "owner": "山田",
             "priority": "P1", "deadline": "2025-11-30"},
        ],
        lessons_learned=[
            "リソース管理（DB接続, ファイルハンドル等）は必ず with 文を使う",
            "コネクションプール監視は早期警告（70%）と緊急（90%）の2段階に",
            "ステージング環境は本番と同一パラメータで設定する",
        ],
    ))

    # --- 実例2: キャッシュ stampede ---
    examples.append(PostmortemEntry(
        title="キャッシュ Stampede によるサービスダウン",
        date="2025-12-03",
        severity=Severity.SEV1,
        duration="23分",
        authors=["佐藤", "高橋"],
        summary="キャッシュTTL一斉期限切れにより、数万リクエストが同時にDBへ到達。"
                "DB負荷が限界を超え全サービスが応答不能に。",
        impact={
            "影響ユーザー数": "全ユーザー",
            "エラー率": "95%以上",
            "推定損失": "約150万円",
        },
        timeline=[
            {"time": "03:00", "event": "日次バッチでキャッシュ全更新（TTL=24h 一律設定）"},
            {"time": "翌03:00", "event": "キャッシュが一斉に期限切れ"},
            {"time": "03:01", "event": "DB CPU 100%、レイテンシ急上昇"},
            {"time": "03:03", "event": "PagerDuty アラート、On-Call エンジニア対応開始"},
            {"time": "03:10", "event": "キャッシュヒット率 0% を確認、stampede と判断"},
            {"time": "03:15", "event": "緊急でキャッシュをウォームアップするスクリプト実行"},
            {"time": "03:23", "event": "キャッシュ復旧、DB負荷正常化"},
        ],
        root_cause="全キャッシュキーに同一TTL（24時間）を設定しており、"
                   "日次バッチ実行時刻に全キーが同時に期限切れとなった。",
        contributing_factors=[
            "TTLにジッター（ランダム幅）を入れていなかった",
            "キャッシュウォームアップの仕組みがなかった",
            "深夜帯でも高トラフィックだった（想定外）",
        ],
        detection="DB CPU アラート + API レイテンシアラート",
        resolution="手動キャッシュウォームアップ後、TTLにランダムジッター "
                   "(±10%) を追加するパッチを適用。",
        action_items=[
            {"action": "TTLにジッター追加（base_ttl ± 10%）", "owner": "佐藤",
             "priority": "P0", "deadline": "2025-12-05"},
            {"action": "キャッシュウォームアップジョブ作成", "owner": "高橋",
             "priority": "P1", "deadline": "2025-12-15"},
            {"action": "Probabilistic Early Recomputation 導入検討", "owner": "佐藤",
             "priority": "P2", "deadline": "2026-01-15"},
        ],
        lessons_learned=[
            "キャッシュTTLには必ずジッターを入れる（stampede防止の基本）",
            "ホットキーは事前ウォームアップする仕組みが必要",
            "Thundering Herd 対策はキャッシュ設計時に必ず検討する",
        ],
    ))

    # --- 実例3: デプロイ後のメモリリーク ---
    examples.append(PostmortemEntry(
        title="デプロイ後のメモリリークによる段階的サービス劣化",
        date="2026-01-20",
        severity=Severity.SEV2,
        duration="3時間12分（検知まで2時間45分）",
        authors=["伊藤", "渡辺"],
        summary="ライブラリアップグレード後にメモリリークが発生。"
                "Pod が徐々にメモリを消費し OOMKill されるが、"
                "再起動後も同様にリークが進行。検知が遅れた。",
        impact={
            "影響ユーザー数": "約30%のユーザー（Pod再起動中のリクエスト失敗）",
            "エラー率": "5-15%（Pod OOMKill の頻度に連動）",
            "推定損失": "約50万円",
        },
        timeline=[
            {"time": "10:00", "event": "ライブラリバージョンアップのデプロイ"},
            {"time": "10:30", "event": "メモリ使用量が通常より速いペースで増加開始"},
            {"time": "11:45", "event": "最初のPodがOOMKillされ自動再起動"},
            {"time": "12:00", "event": "複数Podが順次OOMKill、エラー率上昇"},
            {"time": "12:45", "event": "アラート発報（Pod再起動回数の閾値超過）"},
            {"time": "12:50", "event": "メモリプロファイリング開始"},
            {"time": "13:00", "event": "新ライブラリのイベントリスナー未解放を特定"},
            {"time": "13:12", "event": "ロールバック完了、メモリ使用量安定"},
        ],
        root_cause="アップグレードしたHTTPクライアントライブラリが、リクエスト毎に "
                   "イベントリスナーを登録するが解放しないバグを内包していた。",
        contributing_factors=[
            "ライブラリアップグレード時のメモリプロファイリングテストがなかった",
            "メモリ使用量の傾き（増加率）ベースのアラートがなかった",
            "Canaryデプロイの観測期間が15分と短く、リークを検出できなかった",
        ],
        detection="Pod 再起動回数アラート（検知遅延あり）",
        resolution="ライブラリのバージョンをロールバック。"
                   "上流にバグレポート提出、パッチ適用後に再アップグレード。",
        action_items=[
            {"action": "メモリ使用量の増加率アラート追加", "owner": "伊藤",
             "priority": "P0", "deadline": "2026-01-25"},
            {"action": "Canary観測期間を1時間に延長", "owner": "渡辺",
             "priority": "P0", "deadline": "2026-01-27"},
            {"action": "ライブラリアップグレード時のロードテスト必須化", "owner": "伊藤",
             "priority": "P1", "deadline": "2026-02-10"},
        ],
        lessons_learned=[
            "メモリリークは即座に顕在化しない — 増加率ベースのアラートが有効",
            "Canaryの観測期間は最低1時間、リソース系は傾きで判定",
            "サードパーティライブラリのアップグレードも破壊的変更と同等に扱う",
        ],
    ))

    return examples


# ============================================================
# 4. On-Call Runbook
# ============================================================

@dataclass
class RunbookEntry:
    """Runbook テンプレート"""
    title: str
    symptom: str           # 症状（何が起きているか）
    diagnosis_steps: list[str]   # 診断手順
    remediation_steps: list[str]  # 対処手順
    escalation: dict       # エスカレーション条件
    auto_diagnosis_script: str    # 自動診断スクリプト

    def display(self) -> str:
        lines = [
            f"{'='*50}",
            f"RUNBOOK: {self.title}",
            f"{'='*50}",
            f"\n■ 症状: {self.symptom}",
            "\n■ 診断手順:",
        ]
        for i, step in enumerate(self.diagnosis_steps, 1):
            lines.append(f"  {i}. {step}")
        lines.append("\n■ 対処手順:")
        for i, step in enumerate(self.remediation_steps, 1):
            lines.append(f"  {i}. {step}")
        lines.append("\n■ エスカレーション:")
        for k, v in self.escalation.items():
            lines.append(f"  - {k}: {v}")
        lines.extend(["\n■ 自動診断スクリプト:", self.auto_diagnosis_script])
        return "\n".join(lines)


def create_standard_runbooks() -> list[RunbookEntry]:
    """5つの典型障害パターンの Runbook"""

    runbooks = []

    # --- High CPU ---
    runbooks.append(RunbookEntry(
        title="High CPU Usage",
        symptom="CPU使用率が持続的に80%を超えている",
        diagnosis_steps=[
            "top / htop でCPU消費の上位プロセスを確認",
            "該当プロセスのスレッドダンプ取得 (kill -3 <pid> or jstack)",
            "最近のデプロイ・設定変更の有無を確認",
            "リクエストレートの急増がないか確認",
            "プロファイラ (perf, py-spy等) でホットスポット特定",
        ],
        remediation_steps=[
            "暴走プロセスがあれば再起動（影響範囲を確認の上）",
            "トラフィック急増の場合: スケールアウト実施",
            "特定のリクエストパターンが原因の場合: rate limit 適用",
            "コードのバグの場合: ロールバック実施",
        ],
        escalation={
            "条件": "15分以内に改善しない場合",
            "連絡先": "プラットフォームチーム → EM",
            "SEV判定": "ユーザー影響ありなら SEV2 以上に昇格",
        },
        auto_diagnosis_script=textwrap.dedent("""\
            #!/bin/bash
            # High CPU 自動診断スクリプト
            echo "=== CPU使用率 ==="
            top -bn1 | head -20
            echo ""
            echo "=== ロードアベレージ ==="
            uptime
            echo ""
            echo "=== CPU消費上位プロセス ==="
            ps aux --sort=-%cpu | head -10
            echo ""
            echo "=== 最近のOOM/エラー ==="
            dmesg -T | tail -20
        """),
    ))

    # --- High Memory ---
    runbooks.append(RunbookEntry(
        title="High Memory Usage",
        symptom="メモリ使用率が90%を超えている、またはOOMKillが発生",
        diagnosis_steps=[
            "free -m でメモリ・swap使用状況を確認",
            "ps aux --sort=-rss | head でメモリ消費上位を確認",
            "OOMKill の履歴を確認 (dmesg | grep -i oom)",
            "メモリ使用量の時系列推移をグラフで確認（リーク有無）",
            "ヒープダンプ取得（Java: jmap, Python: tracemalloc）",
        ],
        remediation_steps=[
            "不要なプロセスがあれば停止",
            "キャッシュクリア可能であれば実行 (echo 3 > /proc/sys/vm/drop_caches)",
            "メモリリークが疑われる場合: 該当プロセスを再起動",
            "根本原因がコードの場合: ロールバック",
            "恒久対策: メモリ制限 (cgroup) の見直し",
        ],
        escalation={
            "条件": "OOMKill が繰り返し発生する場合",
            "連絡先": "アプリケーションチーム → SRE",
            "SEV判定": "サービス影響ありなら SEV2",
        },
        auto_diagnosis_script=textwrap.dedent("""\
            #!/bin/bash
            echo "=== メモリ使用状況 ==="
            free -m
            echo ""
            echo "=== Swap使用状況 ==="
            swapon --summary
            echo ""
            echo "=== メモリ消費上位 ==="
            ps aux --sort=-rss | head -10
            echo ""
            echo "=== OOMKill履歴 ==="
            dmesg -T | grep -i "out of memory" | tail -5
        """),
    ))

    # --- Disk Full ---
    runbooks.append(RunbookEntry(
        title="Disk Full",
        symptom="ディスク使用率が95%を超えている",
        diagnosis_steps=[
            "df -h で全マウントポイントの使用率を確認",
            "du -sh /* --max-depth=1 で大きいディレクトリを特定",
            "find / -type f -size +100M で巨大ファイルを探す",
            "ログローテーションの設定を確認",
            "削除済みだがプロセスが掴んでいるファイルを確認 (lsof +L1)",
        ],
        remediation_steps=[
            "古いログファイルの圧縮・削除",
            "不要な一時ファイルの削除 (/tmp, /var/tmp)",
            "削除済みファイルを掴んでいるプロセスの再起動",
            "ログローテーション設定の修正",
            "根本対策: ディスク容量の拡張",
        ],
        escalation={
            "条件": "98%超 or 書き込み不可になった場合",
            "連絡先": "インフラチーム → EM",
            "SEV判定": "DB のディスクフルは即 SEV1",
        },
        auto_diagnosis_script=textwrap.dedent("""\
            #!/bin/bash
            echo "=== ディスク使用状況 ==="
            df -h
            echo ""
            echo "=== 大きいディレクトリ TOP10 ==="
            du -sh /* 2>/dev/null | sort -rh | head -10
            echo ""
            echo "=== 巨大ファイル (>100MB) ==="
            find / -type f -size +100M -exec ls -lh {} \\; 2>/dev/null | head -10
            echo ""
            echo "=== 削除済み未解放ファイル ==="
            lsof +L1 2>/dev/null | head -10
        """),
    ))

    # --- Connection Timeout ---
    runbooks.append(RunbookEntry(
        title="Connection Timeout",
        symptom="外部/内部サービスへの接続がタイムアウトする",
        diagnosis_steps=[
            "対象ホストへの疎通確認 (ping, telnet, curl)",
            "DNS解決の確認 (nslookup, dig)",
            "ネットワーク経路の確認 (traceroute, mtr)",
            "対象サービスの死活確認（ヘルスチェックエンドポイント）",
            "コネクション数の確認 (ss -s, netstat -an | wc -l)",
            "ファイアウォール/セキュリティグループの変更有無を確認",
        ],
        remediation_steps=[
            "DNS問題: リゾルバ変更 or キャッシュクリア",
            "対象サービスダウン: 相手チームにエスカレーション",
            "コネクション枯渇: プール設定の見直し + 再起動",
            "ネットワーク問題: インフラチームにエスカレーション",
            "暫定対策: タイムアウト値の調整 + リトライ + サーキットブレーカー",
        ],
        escalation={
            "条件": "5分以内に原因特定できない場合",
            "連絡先": "ネットワークチーム / 対象サービスチーム",
            "SEV判定": "主要機能に影響なら SEV2",
        },
        auto_diagnosis_script=textwrap.dedent("""\
            #!/bin/bash
            TARGET_HOST="${1:-example.com}"
            TARGET_PORT="${2:-443}"
            echo "=== DNS解決 ==="
            nslookup $TARGET_HOST
            echo ""
            echo "=== TCP接続テスト ==="
            timeout 5 bash -c "echo > /dev/tcp/$TARGET_HOST/$TARGET_PORT" 2>&1 && echo "OK" || echo "FAIL"
            echo ""
            echo "=== コネクション状態 ==="
            ss -s
            echo ""
            echo "=== TIME_WAIT数 ==="
            ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn
        """),
    ))

    # --- 5xx Spike ---
    runbooks.append(RunbookEntry(
        title="5xx Error Spike",
        symptom="5xxエラー率が急上昇している",
        diagnosis_steps=[
            "エラーログでスタックトレース/エラーメッセージを確認",
            "直近のデプロイ有無を確認",
            "依存サービスの状態を確認（DB, キャッシュ, 外部API）",
            "特定のエンドポイントに集中しているか確認",
            "リクエストレートの変動を確認（DDoS等）",
            "リソース（CPU/Mem/Disk/Conn）の状態を確認",
        ],
        remediation_steps=[
            "直近デプロイが原因: 即ロールバック",
            "依存サービス障害: サーキットブレーカー発動 or フォールバック",
            "リソース枯渇: 該当リソースの Runbook を参照",
            "DDoS: WAF/Rate Limit の強化",
            "特定エンドポイント: 一時的に disable + 調査",
        ],
        escalation={
            "条件": "エラー率 >5% が5分以上継続",
            "連絡先": "On-Callエンジニア → EM → VP (SEV1の場合)",
            "SEV判定": "5xx >50% で SEV1, >10% で SEV2",
        },
        auto_diagnosis_script=textwrap.dedent("""\
            #!/bin/bash
            echo "=== 直近のエラーログ ==="
            journalctl -u myapp --since "5 min ago" --priority=err | tail -20
            echo ""
            echo "=== 最近のデプロイ ==="
            kubectl rollout history deployment/myapp 2>/dev/null | tail -5
            echo ""
            echo "=== Pod状態 ==="
            kubectl get pods -l app=myapp 2>/dev/null
            echo ""
            echo "=== リソース使用状況 ==="
            kubectl top pods -l app=myapp 2>/dev/null
        """),
    ))

    return runbooks


# ============================================================
# 5. Capacity Planning
# ============================================================

def capacity_plan(
    current_qps: float,
    growth_rate: float,
    target_months: int,
    peak_multiplier: float = 3.0,
    safety_margin: float = 1.3,
    cpu_per_1000qps: float = 2.0,
    mem_gb_per_1000qps: float = 4.0,
    disk_gb_per_month: float = 50.0,
    net_mbps_per_1000qps: float = 100.0,
) -> dict:
    """
    キャパシティプランニング計算

    Args:
        current_qps: 現在の平均QPS
        growth_rate: 月次成長率 (0.1 = 10%)
        target_months: 計画対象月数
        peak_multiplier: ピーク倍率（平均に対する比率）
        safety_margin: 安全率
        cpu_per_1000qps: 1000QPSあたりの必要CPU (vCPU)
        mem_gb_per_1000qps: 1000QPSあたりの必要メモリ (GB)
        disk_gb_per_month: 月次ディスク増分 (GB)
        net_mbps_per_1000qps: 1000QPSあたりの帯域 (Mbps)

    Returns:
        各月のリソース見積もりとオートスケーリング閾値
    """
    monthly_projections = []

    for month in range(target_months + 1):
        # トラフィック予測（指数成長 + 簡易季節性）
        base_qps = current_qps * ((1 + growth_rate) ** month)
        # 季節性: 12月がピーク（1.2倍）、2月が谷（0.8倍）
        seasonal_factor = 1.0 + 0.2 * math.sin(2 * math.pi * (month % 12 - 3) / 12)
        projected_qps = base_qps * seasonal_factor

        # ピーク QPS
        peak_qps = projected_qps * peak_multiplier

        # リソース見積もり（ピーク × 安全率）
        required_qps = peak_qps * safety_margin
        cpu_needed = required_qps / 1000 * cpu_per_1000qps
        mem_needed = required_qps / 1000 * mem_gb_per_1000qps
        disk_needed = disk_gb_per_month * (month + 1)
        net_needed = required_qps / 1000 * net_mbps_per_1000qps

        monthly_projections.append({
            "month": month,
            "avg_qps": round(projected_qps, 1),
            "peak_qps": round(peak_qps, 1),
            "headroom_qps": round(required_qps, 1),
            "cpu_vcpu": round(cpu_needed, 1),
            "memory_gb": round(mem_needed, 1),
            "disk_gb": round(disk_needed, 1),
            "network_mbps": round(net_needed, 1),
        })

    # オートスケーリング閾値
    autoscaling = {
        "scale_out_cpu_threshold": "70%",
        "scale_in_cpu_threshold": "30%",
        "scale_out_memory_threshold": "80%",
        "cooldown_period": "300秒",
        "min_instances": max(2, round(current_qps / 500)),
        "max_instances": max(10, round(
            monthly_projections[-1]["headroom_qps"] / 500
        )),
        "target_utilization": "50-70%（ヘッドルーム確保）",
    }

    return {
        "parameters": {
            "current_qps": current_qps,
            "growth_rate_monthly": f"{growth_rate*100}%",
            "target_months": target_months,
            "peak_multiplier": f"{peak_multiplier}x",
            "safety_margin": f"{safety_margin}x",
        },
        "monthly_projections": monthly_projections,
        "autoscaling_config": autoscaling,
        "summary": {
            "current": monthly_projections[0],
            "final": monthly_projections[-1],
            "growth_factor": round(
                monthly_projections[-1]["avg_qps"] / monthly_projections[0]["avg_qps"], 2
            ),
        },
    }


# ============================================================
# 6. Deployment Safety
# ============================================================

def pre_deploy_checklist(
    service: str,
    has_db_migration: bool = False,
    has_api_change: bool = False,
    has_config_change: bool = False,
) -> dict:
    """デプロイ前チェックリスト自動生成"""
    checks = {
        "必須項目": [
            {"item": "全テスト通過（unit / integration / e2e）", "status": "未確認"},
            {"item": "コードレビュー承認済み", "status": "未確認"},
            {"item": "ステージング環境で動作確認済み", "status": "未確認"},
            {"item": "ロールバック手順の確認", "status": "未確認"},
            {"item": "モニタリングダッシュボード準備", "status": "未確認"},
            {"item": "On-Callエンジニアへの事前連絡", "status": "未確認"},
        ],
    }

    if has_db_migration:
        checks["DB マイグレーション"] = [
            {"item": "マイグレーションが backward compatible か確認", "status": "未確認"},
            {"item": "Expand-and-Contract パターンの適用", "status": "未確認"},
            {"item": "マイグレーション実行時間の見積もり", "status": "未確認"},
            {"item": "ロック取得の影響確認（大テーブルの ALTER等）", "status": "未確認"},
            {"item": "ロールバック用の逆マイグレーション準備", "status": "未確認"},
        ]

    if has_api_change:
        checks["API 変更"] = [
            {"item": "後方互換性の確認", "status": "未確認"},
            {"item": "APIバージョニングの適用", "status": "未確認"},
            {"item": "クライアントへの事前通知", "status": "未確認"},
            {"item": "非推奨（deprecated）エンドポイントの移行期間設定", "status": "未確認"},
        ]

    if has_config_change:
        checks["設定変更"] = [
            {"item": "設定値の妥当性確認", "status": "未確認"},
            {"item": "Feature Flag による段階的有効化", "status": "未確認"},
            {"item": "ロールバック時の設定復元手順", "status": "未確認"},
        ]

    return {"service": service, "checklist": checks}


def canary_analysis(
    baseline_error_rate: float,
    canary_error_rate: float,
    baseline_p99_ms: float,
    canary_p99_ms: float,
    error_threshold: float = 2.0,
    latency_threshold: float = 1.5,
) -> dict:
    """
    Canary分析 — ベースラインとCanaryの比較

    Args:
        baseline_error_rate: ベースラインのエラー率 (%)
        canary_error_rate: Canaryのエラー率 (%)
        baseline_p99_ms: ベースラインのp99レイテンシ (ms)
        canary_p99_ms: Canaryのp99レイテンシ (ms)
        error_threshold: エラー率の許容倍率
        latency_threshold: レイテンシの許容倍率
    """
    error_ratio = (
        canary_error_rate / baseline_error_rate
        if baseline_error_rate > 0 else (1.0 if canary_error_rate == 0 else float("inf"))
    )
    latency_ratio = (
        canary_p99_ms / baseline_p99_ms
        if baseline_p99_ms > 0 else 1.0
    )

    error_ok = error_ratio <= error_threshold
    latency_ok = latency_ratio <= latency_threshold

    verdict = "PASS" if (error_ok and latency_ok) else "FAIL"

    return {
        "verdict": verdict,
        "error_analysis": {
            "baseline": f"{baseline_error_rate}%",
            "canary": f"{canary_error_rate}%",
            "ratio": round(error_ratio, 2),
            "threshold": f"{error_threshold}x",
            "pass": error_ok,
        },
        "latency_analysis": {
            "baseline_p99": f"{baseline_p99_ms}ms",
            "canary_p99": f"{canary_p99_ms}ms",
            "ratio": round(latency_ratio, 2),
            "threshold": f"{latency_threshold}x",
            "pass": latency_ok,
        },
        "recommendation": (
            "Canary を本番に昇格して問題ありません"
            if verdict == "PASS"
            else "ロールバックを推奨します。メトリクスが閾値を超えています"
        ),
    }


def rollback_decision(
    error_rate: float,
    latency_p99_ms: float,
    error_budget_remaining: float,
    time_since_deploy_min: int,
    auto_rollback_error_threshold: float = 10.0,
    auto_rollback_latency_threshold: float = 5000.0,
) -> dict:
    """
    ロールバック判定ロジック

    Args:
        error_rate: 現在のエラー率 (%)
        latency_p99_ms: 現在のp99レイテンシ (ms)
        error_budget_remaining: Error Budget残量 (%)
        time_since_deploy_min: デプロイからの経過時間 (分)
        auto_rollback_error_threshold: 自動ロールバック閾値 (エラー率%)
        auto_rollback_latency_threshold: 自動ロールバック閾値 (レイテンシms)
    """
    reasons = []
    auto_rollback = False

    if error_rate >= auto_rollback_error_threshold:
        reasons.append(f"エラー率 {error_rate}% ≥ 閾値 {auto_rollback_error_threshold}%")
        auto_rollback = True

    if latency_p99_ms >= auto_rollback_latency_threshold:
        reasons.append(
            f"p99レイテンシ {latency_p99_ms}ms ≥ 閾値 {auto_rollback_latency_threshold}ms"
        )
        auto_rollback = True

    if error_budget_remaining <= 10:
        reasons.append(f"Error Budget残量 {error_budget_remaining}% ≤ 10%")
        auto_rollback = True

    if not reasons and error_rate > 1.0:
        reasons.append(f"エラー率 {error_rate}% が通常より高い（手動判断推奨）")

    decision = "AUTO_ROLLBACK" if auto_rollback else (
        "MANUAL_REVIEW" if reasons else "CONTINUE"
    )

    return {
        "decision": decision,
        "reasons": reasons if reasons else ["異常なし"],
        "metrics": {
            "error_rate": f"{error_rate}%",
            "latency_p99": f"{latency_p99_ms}ms",
            "error_budget_remaining": f"{error_budget_remaining}%",
            "time_since_deploy": f"{time_since_deploy_min}分",
        },
        "action": {
            "AUTO_ROLLBACK": "即座にロールバックを実行してください",
            "MANUAL_REVIEW": "状況を確認し、手動でロールバック判断してください",
            "CONTINUE": "問題ありません。モニタリングを継続してください",
        }[decision],
    }


@dataclass
class FeatureFlag:
    """Feature Flag 管理"""
    name: str
    enabled: bool
    created_at: str
    last_modified: str
    owner: str
    description: str
    percentage: int = 100  # ロールアウト率

    def is_stale(self, stale_days: int = 30) -> bool:
        """Stale flag かどうかを判定"""
        last_mod = datetime.fromisoformat(self.last_modified)
        return (datetime.now() - last_mod).days > stale_days


def detect_stale_flags(flags: list[FeatureFlag], stale_days: int = 30) -> dict:
    """Stale な Feature Flag を検出"""
    stale = [f for f in flags if f.is_stale(stale_days)]
    active = [f for f in flags if not f.is_stale(stale_days)]
    return {
        "total_flags": len(flags),
        "stale_flags": len(stale),
        "active_flags": len(active),
        "stale_flag_details": [
            {
                "name": f.name,
                "owner": f.owner,
                "last_modified": f.last_modified,
                "days_since_update": (
                    datetime.now() - datetime.fromisoformat(f.last_modified)
                ).days,
                "recommendation": "削除を検討（コードから完全に除去）",
            }
            for f in stale
        ],
        "cleanup_policy": (
            f"{stale_days}日以上更新のないフラグはクリーンアップ対象。"
            "フラグ数が増えると技術的負債になるため定期的に棚卸しする。"
        ),
    }


def db_migration_safety_check(migration: dict) -> dict:
    """
    DB マイグレーション安全性チェック (Expand-and-Contract パターン)

    Expand-and-Contract の原則:
      Phase 1 (Expand): 新カラム追加、新テーブル作成（既存を壊さない）
      Phase 2 (Migrate): データ移行、アプリケーションの切り替え
      Phase 3 (Contract): 古いカラム/テーブルの削除
    """
    dangerous_operations = {
        "DROP COLUMN": "データ消失リスク。先にアプリから参照を外す (Contract Phase)",
        "DROP TABLE": "データ消失リスク。バックアップ確認必須",
        "RENAME COLUMN": "アプリが旧名参照でエラー。新カラム追加→データコピー→旧カラム削除",
        "RENAME TABLE": "同上。新テーブル作成→ビュー切替→旧テーブル削除",
        "ALTER COLUMN TYPE": "暗黙の型変換失敗リスク。新カラム追加パターン推奨",
        "NOT NULL 追加": "既存データにNULLがあると失敗。デフォルト値設定が必要",
        "UNIQUE 制約追加": "既存データに重複があると失敗。事前チェック必須",
    }

    sql = migration.get("sql", "").upper()
    warnings = []
    for op, risk in dangerous_operations.items():
        if op.replace(" ", "") in sql.replace(" ", "") or op in sql:
            warnings.append({"operation": op, "risk": risk})

    safe = len(warnings) == 0
    return {
        "migration": migration,
        "safe": safe,
        "warnings": warnings if warnings else ["安全な操作です"],
        "expand_and_contract_guide": {
            "Phase 1 (Expand)": "新しい構造を追加（既存に影響なし）",
            "Phase 2 (Migrate)": "データ移行 + アプリ切替（両方の構造をサポート）",
            "Phase 3 (Contract)": "古い構造を削除（アプリが新構造のみ参照を確認後）",
        },
        "recommendation": (
            "マイグレーションを実行してOKです"
            if safe
            else "Expand-and-Contract パターンでの段階的移行を推奨します"
        ),
    }


# ============================================================
# 7. SLA/SLO 計算器
# ============================================================

def uptime_calculator(availability_percent: float) -> dict:
    """
    稼働率からダウンタイムを計算

    例: 99.9% → 年間8.76時間, 月43.8分, 週10.08分
    """
    downtime_fraction = 1 - (availability_percent / 100)

    minutes_per_year = 365.25 * 24 * 60
    minutes_per_month = 30.44 * 24 * 60
    minutes_per_week = 7 * 24 * 60
    minutes_per_day = 24 * 60

    def fmt(minutes):
        if minutes >= 60:
            h = int(minutes // 60)
            m = round(minutes % 60, 1)
            return f"{h}時間{m}分"
        elif minutes >= 1:
            return f"{round(minutes, 1)}分"
        else:
            return f"{round(minutes * 60, 1)}秒"

    return {
        "availability": f"{availability_percent}%",
        "nines": f"{'9' * int(-math.log10(downtime_fraction))} nines"
                 if downtime_fraction > 0 else "100%",
        "allowed_downtime": {
            "per_year": fmt(minutes_per_year * downtime_fraction),
            "per_month": fmt(minutes_per_month * downtime_fraction),
            "per_week": fmt(minutes_per_week * downtime_fraction),
            "per_day": fmt(minutes_per_day * downtime_fraction),
        },
    }


def composite_sla(
    services: list[dict],
    topology: str = "serial",
) -> dict:
    """
    複合サービスの SLA 計算

    Args:
        services: [{"name": str, "sla": float}] — 各サービスのSLA (%)
        topology: "serial" (直列) or "parallel" (並列/冗長)

    直列: SLA_total = SLA_1 × SLA_2 × ...
    並列: SLA_total = 1 - (1-SLA_1) × (1-SLA_2) × ...
    """
    if topology == "serial":
        # 直列: 全てが稼働している必要がある
        combined = 1.0
        for svc in services:
            combined *= svc["sla"] / 100
        combined_pct = combined * 100
        explanation = "直列構成: 全サービスが稼働している確率の積"
    elif topology == "parallel":
        # 並列: いずれか1つでも稼働していればOK
        all_down = 1.0
        for svc in services:
            all_down *= (1 - svc["sla"] / 100)
        combined_pct = (1 - all_down) * 100
        explanation = "並列構成: 全サービスが同時にダウンしない確率"
    else:
        return {"error": f"未知のトポロジー: {topology}"}

    result = uptime_calculator(combined_pct)
    result.update({
        "topology": topology,
        "explanation": explanation,
        "services": services,
        "composite_sla": f"{combined_pct:.6f}%",
    })
    return result


def error_budget_tracker(
    slo_target: float,
    measurement_window_days: int,
    total_requests: int,
    failed_requests: int,
) -> dict:
    """
    Error Budget 消費率トラッカー

    Args:
        slo_target: SLO目標 (例: 99.9)
        measurement_window_days: 測定ウィンドウ (例: 30日)
        total_requests: 期間内の総リクエスト数
        failed_requests: 期間内の失敗リクエスト数
    """
    # 許容エラー数
    allowed_error_rate = 1 - (slo_target / 100)
    allowed_errors = total_requests * allowed_error_rate

    # 消費率
    budget_consumed = (failed_requests / allowed_errors * 100) if allowed_errors > 0 else 100
    budget_remaining = max(0, 100 - budget_consumed)

    # 残り日数あたりの消費ペース
    elapsed_fraction = 1.0  # 簡易: ウィンドウ全体を測定済みと仮定

    # Burn Rate 計算
    # burn_rate = 1 なら予算通り消費、>1 なら超過ペース
    expected_consumed = elapsed_fraction * 100
    burn_rate = budget_consumed / expected_consumed if expected_consumed > 0 else 0

    return {
        "slo_target": f"{slo_target}%",
        "measurement_window": f"{measurement_window_days}日",
        "actual_availability": f"{(1 - failed_requests/total_requests)*100:.4f}%"
                               if total_requests > 0 else "N/A",
        "error_budget": {
            "allowed_errors": int(allowed_errors),
            "actual_errors": failed_requests,
            "budget_consumed": f"{budget_consumed:.1f}%",
            "budget_remaining": f"{budget_remaining:.1f}%",
        },
        "burn_rate": {
            "current": round(burn_rate, 2),
            "interpretation": (
                "正常ペース" if burn_rate <= 1.0
                else "超過ペース（要注意）" if burn_rate <= 2.0
                else "危険水準（即座にアクション必要）"
            ),
        },
        "alert_thresholds": {
            "1h_burn_rate_14x": "14倍速で消費中 → 即座にページング",
            "6h_burn_rate_6x": "6倍速で消費中 → 高優先度チケット",
            "1d_burn_rate_3x": "3倍速で消費中 → 通常優先度チケット",
            "3d_burn_rate_1x": "予算通り消費 → ダッシュボード監視",
        },
    }


def burn_rate_alert_config(
    slo_target: float,
    window_days: int = 30,
) -> dict:
    """
    Burn Rate ベースのアラート閾値設計

    Google SRE Book 準拠の多段アラート設計
    """
    error_budget_fraction = 1 - (slo_target / 100)
    total_budget_minutes = window_days * 24 * 60

    # Google推奨の多段バーンレートアラート
    alerts = [
        {
            "name": "Critical (Page)",
            "burn_rate": 14.4,
            "short_window": "5分",
            "long_window": "1時間",
            "budget_consumed_in_window": f"{14.4 / window_days * 100:.1f}%",
            "action": "即座にページング（On-Call対応必須）",
            "budget_exhaustion": f"{total_budget_minutes / 14.4:.0f}分 ({total_budget_minutes / 14.4 / 60:.1f}時間)",
        },
        {
            "name": "High (Page)",
            "burn_rate": 6.0,
            "short_window": "30分",
            "long_window": "6時間",
            "budget_consumed_in_window": f"{6.0 / window_days * 100:.1f}%",
            "action": "ページング（当日中に対応）",
            "budget_exhaustion": f"{total_budget_minutes / 6.0:.0f}分 ({total_budget_minutes / 6.0 / 60:.1f}時間)",
        },
        {
            "name": "Medium (Ticket)",
            "burn_rate": 3.0,
            "short_window": "2時間",
            "long_window": "1日",
            "budget_consumed_in_window": f"{3.0 / window_days * 100:.1f}%",
            "action": "チケット起票（今週中に対応）",
            "budget_exhaustion": f"{total_budget_minutes / 3.0:.0f}分 ({total_budget_minutes / 3.0 / 60 / 24:.1f}日)",
        },
        {
            "name": "Low (Dashboard)",
            "burn_rate": 1.0,
            "short_window": "6時間",
            "long_window": "3日",
            "budget_consumed_in_window": f"{1.0 / window_days * 100:.1f}%",
            "action": "ダッシュボード監視（通常ペース）",
            "budget_exhaustion": f"{window_days}日（予算通り）",
        },
    ]

    return {
        "slo_target": f"{slo_target}%",
        "error_budget": f"{error_budget_fraction * 100:.3f}%",
        "measurement_window": f"{window_days}日",
        "alerts": alerts,
        "implementation_note": (
            "Long window でトレンドを確認し、Short window で直近の悪化を検出する。"
            "両方の条件を満たした場合のみアラートを発火させることで、"
            "ノイズ（一時的スパイク）を抑制する。"
        ),
    }


# ============================================================
# 8. 優先度セクション (Tier 1-4)
# ============================================================

PRIORITY_TIERS = {
    "Tier 1 — 最優先（本番稼働の基本）": {
        "対象者": "On-Call に入る全エンジニア",
        "スキル": [
            "障害対応フレームワーク (OODA Loop + Severity分類)",
            "基本的なデバッグ手法 (USE Method / RED Method)",
            "Runbook の読み方と基本対応 (CPU/Mem/Disk/5xx)",
            "SLA/SLO の基本概念と稼働率計算",
            "エスカレーションの判断と実行",
        ],
        "目標": "SEV3以下の障害を自力で対応でき、SEV1-2は適切にエスカレーションできる",
        "学習時間目安": "2-3週間",
    },
    "Tier 2 — 重要（信頼性エンジニアリング）": {
        "対象者": "SREチーム / シニアエンジニア",
        "スキル": [
            "Postmortem の作成と運営 (Blameless文化)",
            "5 Whys / Fault Tree Analysis による根本原因分析",
            "Error Budget の運用とBurn Rateアラート設計",
            "Canary Analysis とデプロイ安全性",
            "Capacity Planning の基本",
        ],
        "目標": "SEV1-2 の IC を務められ、再発防止策を主導できる",
        "学習時間目安": "1-2ヶ月",
    },
    "Tier 3 — 発展（プロダクションエクセレンス）": {
        "対象者": "テックリード / Staff Engineer",
        "スキル": [
            "複合サービスのSLA設計と依存関係管理",
            "Auto-scaling戦略とコスト最適化",
            "Feature Flag 管理とリリースエンジニアリング",
            "DB Migration Safety (Expand-and-Contract)",
            "組織的なOn-Call体制の設計と改善",
        ],
        "目標": "プロダクション品質の文化を組織全体に浸透させられる",
        "学習時間目安": "3-6ヶ月",
    },
    "Tier 4 — 専門（SREプラットフォーム）": {
        "対象者": "SRE Platform Team / Principal Engineer",
        "スキル": [
            "トラフィック予測モデルの構築と精度改善",
            "Chaos Engineering の計画と実行",
            "大規模障害の組織横断的な対応指揮",
            "SLO ベースの開発優先度判断フレームワーク",
            "プロダクションエンジニアリングの標準化と教育",
        ],
        "目標": "組織のレジリエンスを戦略的に向上させられる",
        "学習時間目安": "6ヶ月-1年",
    },
}


# ============================================================
# デモ実行
# ============================================================

def demo_incident_response():
    """障害対応フレームワークのデモ"""
    print("\n" + "=" * 60)
    print("  1. 障害対応フレームワーク (Incident Response)")
    print("=" * 60)

    # Severity SLA 表示
    print("\n--- Severity 分類と SLA ---")
    for sev, sla in SEVERITY_SLA.items():
        print(f"\n  [{sev.name}]")
        for k, v in sla.items():
            print(f"    {k}: {v}")

    # OODA Loop デモ
    print("\n--- OODA Loop デモ ---")
    ooda = OODALoop("INC-2025-042", Severity.SEV1)
    result = ooda.run_loop(
        observations=["API 5xx率 95%", "DB CPU 100%", "10分前にデプロイ実施"],
        hypotheses=["デプロイによるDB負荷増大", "DB障害", "トラフィック急増"],
        action_plan="直近デプロイをロールバック",
        result="ロールバック完了、5xx率 0% に回復",
    )
    print(f"  Incident: {result['incident_id']}")
    print(f"  Severity: {result['severity']}")
    print(f"  Resolved: {result['resolved']}")
    print(f"  Loop count: {result['loop_count']}")

    # Communication template
    print("\n--- Communication Template ---")
    comms = generate_comms_template(
        Severity.SEV1, "Payment API", "決済処理が全て失敗", "調査中（30分以内に更新）"
    )
    print(comms["slack"][:200] + "...")


def demo_debugging():
    """体系的デバッグ手法のデモ"""
    print("\n" + "=" * 60)
    print("  2. 体系的デバッグ手法")
    print("=" * 60)

    # USE Method
    print("\n--- USE Method (CPU) ---")
    cpu_checks = use_method_checklist("CPU")
    for aspect, detail in cpu_checks.items():
        print(f"  {aspect}: {detail['what']}")
        print(f"    閾値: {detail['threshold']}")

    # 5 Whys
    print("\n--- 5 Whys 分析 ---")
    analysis = FiveWhys("本番サービスが応答不能になった")
    analysis.ask_why(
        "APIサーバーがOOMKillされた", "dmesg に OOM killer のログ"
    ).ask_why(
        "メモリ使用量が上限を超えた", "メモリ使用量グラフで線形増加を確認"
    ).ask_why(
        "HTTPクライアントがコネクションを解放しなかった", "ヒープダンプで未解放の接続オブジェクト多数"
    ).ask_why(
        "ライブラリのバージョンアップでリソース管理のバグが混入", "CHANGELOGにリグレッションの記載"
    ).ask_why(
        "ライブラリ更新時のメモリリークテストが存在しなかった", "テストカバレッジの不足"
    )
    print(analysis.report())

    # 故障木分析
    print("\n--- Fault Tree Analysis ---")
    tree = FaultTreeNode("サービス全断", gate="OR", children=[
        FaultTreeNode("アプリケーション障害", gate="OR", children=[
            FaultTreeNode("メモリリーク", probability=0.05),
            FaultTreeNode("デッドロック", probability=0.02),
        ]),
        FaultTreeNode("インフラ障害", gate="AND", children=[
            FaultTreeNode("プライマリDB障害", probability=0.01),
            FaultTreeNode("レプリカDB障害", probability=0.01),
        ]),
        FaultTreeNode("ネットワーク障害", probability=0.005),
    ])
    print(tree.display())
    print(f"  トップイベント発生確率: {tree.calculate_probability():.6f}")

    # 二分探索デバッグ
    print("\n--- 二分探索デバッグ ---")
    versions = [f"v1.{i}" for i in range(20)]
    # v1.13 でバグが混入したと仮定
    result = binary_search_debug(versions, lambda v: int(v.split(".")[1]) >= 13)
    print(f"  初めて壊れたバージョン: {result['first_broken_version']}")
    print(f"  チェック回数: {result['checks_performed']}/{result['total_versions']}")
    print(f"  理論上限: {result['theoretical_max_checks']}回")


def demo_postmortem():
    """Postmortem のデモ"""
    print("\n" + "=" * 60)
    print("  3. Postmortem テンプレート + 実例")
    print("=" * 60)

    print("\n--- Blameless の原則 ---")
    for p in BLAMELESS_PRINCIPLES:
        print(f"  - {p}")

    examples = postmortem_examples()
    print(f"\n--- 実例 Postmortem ({len(examples)}件) ---")
    # 1件目の要約のみ表示
    pm = examples[0]
    print(f"\n  タイトル: {pm.title}")
    print(f"  重大度: {pm.severity.name}")
    print(f"  継続時間: {pm.duration}")
    print(f"  根本原因: {pm.root_cause[:60]}...")
    print(f"  アクションアイテム数: {len(pm.action_items)}")


def demo_runbook():
    """Runbook のデモ"""
    print("\n" + "=" * 60)
    print("  4. On-Call Runbook")
    print("=" * 60)

    runbooks = create_standard_runbooks()
    print(f"\n  標準Runbook数: {len(runbooks)}")
    for rb in runbooks:
        print(f"\n  [{rb.title}]")
        print(f"    症状: {rb.symptom}")
        print(f"    診断ステップ数: {len(rb.diagnosis_steps)}")
        print(f"    対処ステップ数: {len(rb.remediation_steps)}")


def demo_capacity_planning():
    """Capacity Planning のデモ"""
    print("\n" + "=" * 60)
    print("  5. Capacity Planning")
    print("=" * 60)

    plan = capacity_plan(
        current_qps=1000,
        growth_rate=0.15,  # 月15%成長
        target_months=12,
    )
    print(f"\n  現在のQPS: {plan['parameters']['current_qps']}")
    print(f"  月次成長率: {plan['parameters']['growth_rate_monthly']}")
    print(f"  12ヶ月後の予測:")
    final = plan["summary"]["final"]
    print(f"    平均QPS: {final['avg_qps']}")
    print(f"    ピークQPS: {final['peak_qps']}")
    print(f"    必要CPU: {final['cpu_vcpu']} vCPU")
    print(f"    必要メモリ: {final['memory_gb']} GB")
    print(f"  成長倍率: {plan['summary']['growth_factor']}x")
    print(f"\n  AutoScaling設定:")
    for k, v in plan["autoscaling_config"].items():
        print(f"    {k}: {v}")


def demo_deployment_safety():
    """Deployment Safety のデモ"""
    print("\n" + "=" * 60)
    print("  6. Deployment Safety")
    print("=" * 60)

    # チェックリスト
    print("\n--- Pre-deploy Checklist ---")
    checklist = pre_deploy_checklist(
        "payment-service", has_db_migration=True, has_api_change=True
    )
    for category, items in checklist["checklist"].items():
        print(f"\n  [{category}]")
        for item in items:
            print(f"    [ ] {item['item']}")

    # Canary分析
    print("\n--- Canary Analysis ---")
    canary = canary_analysis(
        baseline_error_rate=0.5, canary_error_rate=0.7,
        baseline_p99_ms=200, canary_p99_ms=250,
    )
    print(f"  判定: {canary['verdict']}")
    print(f"  エラー率比: {canary['error_analysis']['ratio']}x")
    print(f"  レイテンシ比: {canary['latency_analysis']['ratio']}x")
    print(f"  推奨: {canary['recommendation']}")

    # ロールバック判定
    print("\n--- Rollback Decision ---")
    decision = rollback_decision(
        error_rate=15.0, latency_p99_ms=3000,
        error_budget_remaining=5.0, time_since_deploy_min=10,
    )
    print(f"  判定: {decision['decision']}")
    for reason in decision["reasons"]:
        print(f"    理由: {reason}")
    print(f"  アクション: {decision['action']}")

    # DB Migration Safety
    print("\n--- DB Migration Safety Check ---")
    migration_check = db_migration_safety_check({
        "name": "add_email_index",
        "sql": "ALTER TABLE users DROP COLUMN legacy_name, ADD COLUMN display_name VARCHAR(255)",
    })
    print(f"  安全: {migration_check['safe']}")
    for w in migration_check["warnings"]:
        if isinstance(w, dict):
            print(f"    警告: {w['operation']} — {w['risk'][:50]}...")

    # Feature Flag
    print("\n--- Stale Feature Flag Detection ---")
    flags = [
        FeatureFlag("new_checkout_flow", True, "2025-06-01", "2025-06-15", "田中",
                     "新決済フロー"),
        FeatureFlag("dark_mode", True, "2026-02-01", "2026-03-01", "鈴木",
                     "ダークモード"),
        FeatureFlag("legacy_api_v1", False, "2024-01-01", "2024-03-01", "佐藤",
                     "旧API互換"),
    ]
    stale = detect_stale_flags(flags)
    print(f"  総フラグ数: {stale['total_flags']}")
    print(f"  Staleフラグ数: {stale['stale_flags']}")
    for sf in stale["stale_flag_details"]:
        print(f"    {sf['name']}: {sf['days_since_update']}日未更新")


def demo_sla_slo():
    """SLA/SLO 計算器のデモ"""
    print("\n" + "=" * 60)
    print("  7. SLA/SLO 計算器")
    print("=" * 60)

    # 稼働率計算
    print("\n--- 稼働率 → ダウンタイム ---")
    for avail in [99.0, 99.9, 99.95, 99.99, 99.999]:
        result = uptime_calculator(avail)
        print(f"  {result['availability']:>8s}: "
              f"年間 {result['allowed_downtime']['per_year']:>12s} / "
              f"月間 {result['allowed_downtime']['per_month']:>10s}")

    # 複合SLA
    print("\n--- 複合SLA計算 ---")
    services = [
        {"name": "API Gateway", "sla": 99.99},
        {"name": "App Server", "sla": 99.95},
        {"name": "Database", "sla": 99.99},
        {"name": "Cache", "sla": 99.9},
    ]
    serial = composite_sla(services, "serial")
    print(f"  直列構成のSLA: {serial['composite_sla']}")
    print(f"    年間ダウンタイム: {serial['allowed_downtime']['per_year']}")

    # 並列（冗長）のDB
    db_redundant = composite_sla(
        [{"name": "DB Primary", "sla": 99.99}, {"name": "DB Replica", "sla": 99.99}],
        "parallel",
    )
    print(f"  並列DB構成のSLA: {db_redundant['composite_sla']}")

    # Error Budget
    print("\n--- Error Budget トラッカー ---")
    budget = error_budget_tracker(
        slo_target=99.9, measurement_window_days=30,
        total_requests=10_000_000, failed_requests=15_000,
    )
    print(f"  SLO: {budget['slo_target']}")
    print(f"  実績: {budget['actual_availability']}")
    print(f"  Budget消費: {budget['error_budget']['budget_consumed']}")
    print(f"  Burn Rate: {budget['burn_rate']['current']}x "
          f"({budget['burn_rate']['interpretation']})")

    # Burn Rate アラート
    print("\n--- Burn Rate アラート設計 ---")
    alerts = burn_rate_alert_config(99.9, window_days=30)
    for a in alerts["alerts"]:
        print(f"  [{a['name']}] burn_rate={a['burn_rate']}x "
              f"→ {a['action']}")


def demo_priority_tiers():
    """優先度セクションのデモ"""
    print("\n" + "=" * 60)
    print("  8. 学習優先度 (Tier 1-4)")
    print("=" * 60)

    for tier_name, tier_info in PRIORITY_TIERS.items():
        print(f"\n  [{tier_name}]")
        print(f"    対象: {tier_info['対象者']}")
        print(f"    目標: {tier_info['目標']}")
        print(f"    学習時間: {tier_info['学習時間目安']}")
        for skill in tier_info["スキル"]:
            print(f"      - {skill}")


# ============================================================
# メイン
# ============================================================

def main():
    print("=" * 60)
    print("  Production Engineering / On-Call / デバッグ方法論ガイド")
    print("=" * 60)
    print("  本番運用の全体像を体系的に学ぶモジュール")
    print("  対象: On-Callエンジニア → SRE → テックリード")

    demo_incident_response()
    demo_debugging()
    demo_postmortem()
    demo_runbook()
    demo_capacity_planning()
    demo_deployment_safety()
    demo_sla_slo()
    demo_priority_tiers()

    print("\n" + "=" * 60)
    print("  ガイド完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
