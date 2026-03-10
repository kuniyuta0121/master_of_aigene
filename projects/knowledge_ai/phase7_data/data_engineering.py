"""
FAANG レベル データエンジニアリング パターン完全ガイド
=====================================================
対象: データエンジニア面接 / シニアレベルの設計力
実行: python data_engineering.py
外部ライブラリ不要 (Python 標準ライブラリのみ)
"""

import time
import hashlib
import json
import uuid
import threading
import queue
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Any, Callable
from abc import ABC, abstractmethod

SEP = "━" * 60


# ============================================================
# 1. データモデリング
# ============================================================
def section_data_modeling():
    print(f"\n{SEP}")
    print("1. データモデリング — Star / Snowflake / Data Vault 2.0")
    print(SEP)

    print("""
■ 3大モデリング手法の比較

┌─────────────┬──────────────────┬──────────────────┬──────────────────┐
│             │ Star Schema      │ Snowflake Schema │ Data Vault 2.0   │
├─────────────┼──────────────────┼──────────────────┼──────────────────┤
│ 正規化      │ 非正規化         │ 正規化           │ ハブ/リンク/サテライト │
│ クエリ性能  │ ◎ 高速           │ △ JOIN多い       │ ○ 柔軟           │
│ 柔軟性      │ △ 変更に弱い     │ ○ 中程度         │ ◎ 変更に強い     │
│ ユースケース│ BI / OLAP        │ 厳密な分析       │ EDW / 監査要件   │
│ FAANG利用   │ Redshift/BQ      │ レガシーDWH      │ 金融/ヘルスケア  │
└─────────────┴──────────────────┴──────────────────┴──────────────────┘
""")

    # --- Star Schema 実装 ---
    print("■ Star Schema を Python dict で実装\n")

    # ファクトテーブル: 売上
    fact_sales = [
        {"sale_id": 1, "date_key": 20240101, "product_key": 101,
         "store_key": 1, "quantity": 3, "amount": 1500},
        {"sale_id": 2, "date_key": 20240101, "product_key": 102,
         "store_key": 2, "quantity": 1, "amount": 8000},
        {"sale_id": 3, "date_key": 20240102, "product_key": 101,
         "store_key": 1, "quantity": 5, "amount": 2500},
    ]

    # ディメンションテーブル群
    dim_date = {
        20240101: {"date": "2024-01-01", "month": "January",
                   "quarter": "Q1", "year": 2024, "is_weekend": False},
        20240102: {"date": "2024-01-02", "month": "January",
                   "quarter": "Q1", "year": 2024, "is_weekend": False},
    }
    dim_product = {
        101: {"name": "ワイヤレスマウス", "category": "周辺機器", "brand": "TechCo"},
        102: {"name": "4Kモニター", "category": "ディスプレイ", "brand": "ViewMax"},
    }
    dim_store = {
        1: {"name": "東京本店", "region": "関東", "type": "直営"},
        2: {"name": "大阪支店", "region": "関西", "type": "FC"},
    }

    # Star Schema クエリ: 地域別・カテゴリ別 売上集計
    print("  クエリ: 地域別 × カテゴリ別 売上集計")
    agg = defaultdict(lambda: {"quantity": 0, "amount": 0})
    for sale in fact_sales:
        region = dim_store[sale["store_key"]]["region"]
        category = dim_product[sale["product_key"]]["category"]
        key = (region, category)
        agg[key]["quantity"] += sale["quantity"]
        agg[key]["amount"] += sale["amount"]

    for (region, category), metrics in sorted(agg.items()):
        print(f"    {region} / {category}: "
              f"数量={metrics['quantity']}, 金額=¥{metrics['amount']:,}")

    # --- SCD (Slowly Changing Dimension) ---
    print(f"\n■ SCD Types (Slowly Changing Dimension)\n")
    print("""
  Type 1: 上書き更新 — 履歴なし。最新値のみ保持
  Type 2: 新行追加   — effective_from/to で履歴管理 (最も一般的)
  Type 3: 新列追加   — current_value + previous_value 列
  Type 4: ミニDIM    — 現在値テーブル + 履歴テーブルを分離
""")

    # SCD Type 2 実装
    print("  SCD Type 2 実装例:")
    scd2_customer = [
        {"customer_id": 1, "name": "田中太郎", "city": "東京",
         "effective_from": "2023-01-01", "effective_to": "2024-06-30",
         "is_current": False},
        {"customer_id": 1, "name": "田中太郎", "city": "大阪",
         "effective_from": "2024-07-01", "effective_to": "9999-12-31",
         "is_current": True},
    ]
    for row in scd2_customer:
        flag = "★現在" if row["is_current"] else "  過去"
        print(f"    {flag} ID={row['customer_id']} {row['name']} "
              f"都市={row['city']} ({row['effective_from']}〜{row['effective_to']})")

    print("""
  💡 考えてほしい疑問:
    - SCD Type 2 でサロゲートキー (surrogate key) はなぜ必要か？
    - ファクトテーブルが参照する dim のキーは natural key か surrogate key か？
    - Data Vault 2.0 のハッシュキーは何を解決するか？
""")


# ============================================================
# 2. バッチ vs ストリーム処理
# ============================================================
def section_batch_vs_stream():
    print(f"\n{SEP}")
    print("2. バッチ vs ストリーム処理 — Lambda / Kappa Architecture")
    print(SEP)

    print("""
■ アーキテクチャ比較

  Lambda Architecture (Nathan Marz):
    ┌──────────────────────────────────────────────┐
    │  Raw Data → Batch Layer (正確・遅い)          │
    │          → Speed Layer (近似・速い)           │
    │          → Serving Layer (マージして提供)      │
    └──────────────────────────────────────────────┘
    問題: 同じロジックを2箇所で実装 → メンテ地獄

  Kappa Architecture (Jay Kreps / LinkedIn):
    ┌──────────────────────────────────────────────┐
    │  Raw Data → Stream Layer のみ (再処理も可能)   │
    │  バッチ = ストリームの特殊ケース               │
    └──────────────────────────────────────────────┘
    利点: ロジック一元管理、Kafka がイミュータブルログ

■ Exactly-Once Semantics
  - At-most-once:  送りっぱなし (UDP的)
  - At-least-once: 再送あり、重複あり (Kafka default)
  - Exactly-once:  冪等性 + トランザクション (Kafka EOS, Flink checkpoint)
""")

    # --- 簡易バッチプロセッサ ---
    print("■ 簡易バッチプロセッサ実装\n")

    raw_events = [
        {"user": "A", "action": "click", "ts": "2024-01-01 10:00:00"},
        {"user": "B", "action": "purchase", "ts": "2024-01-01 10:05:00"},
        {"user": "A", "action": "purchase", "ts": "2024-01-01 10:10:00"},
        {"user": "C", "action": "click", "ts": "2024-01-01 10:15:00"},
        {"user": "A", "action": "click", "ts": "2024-01-01 10:20:00"},
    ]

    def batch_process(events: list[dict]) -> dict:
        """バッチ: 全データを一括処理して集計"""
        result = defaultdict(lambda: defaultdict(int))
        for e in events:
            result[e["user"]][e["action"]] += 1
        return dict(result)

    batch_result = batch_process(raw_events)
    print("  バッチ結果 (ユーザー別アクション集計):")
    for user, actions in sorted(batch_result.items()):
        print(f"    User {user}: {dict(actions)}")

    # --- 簡易ストリームプロセッサ ---
    print("\n■ 簡易ストリームプロセッサ実装 (タンブリングウィンドウ)\n")

    class TumblingWindowProcessor:
        """固定時間ウィンドウでイベントを集計"""
        def __init__(self, window_seconds: int):
            self.window_seconds = window_seconds
            self.windows: dict[str, dict] = {}  # window_key -> aggregation

        def _window_key(self, ts_str: str) -> str:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            window_start = ts.replace(
                minute=(ts.minute // (self.window_seconds // 60))
                * (self.window_seconds // 60),
                second=0
            )
            return window_start.strftime("%H:%M")

        def process_event(self, event: dict):
            wk = self._window_key(event["ts"])
            if wk not in self.windows:
                self.windows[wk] = defaultdict(int)
            self.windows[wk][event["action"]] += 1
            print(f"    イベント受信: user={event['user']} "
                  f"action={event['action']} → window={wk}")

        def get_results(self) -> dict:
            return {k: dict(v) for k, v in self.windows.items()}

    processor = TumblingWindowProcessor(window_seconds=600)  # 10分窓
    for event in raw_events:
        processor.process_event(event)

    print(f"\n  ウィンドウ集計結果:")
    for window, counts in sorted(processor.get_results().items()):
        print(f"    Window [{window}]: {counts}")

    print("""
■ ウォーターマーク (Watermark)
  - 「この時刻以前のイベントはもう来ない」という宣言
  - 遅延データの許容範囲を決定
  - Flink: WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(5))

  💡 考えてほしい疑問:
    - ウォーターマークが進みすぎると何が起きる？ (遅延データのドロップ)
    - ウォーターマークが進まないと何が起きる？ (ウィンドウが閉じない→メモリ枯渇)
""")


# ============================================================
# 3. ETL vs ELT
# ============================================================
def section_etl_vs_elt():
    print(f"\n{SEP}")
    print("3. ETL vs ELT — パラダイムシフト")
    print(SEP)

    print("""
■ 従来の ETL (Extract → Transform → Load)
  ┌─────────┐    ┌───────────┐    ┌─────────┐
  │  Source  │ →  │ ETL Server│ →  │   DWH   │
  │ (RDBMS) │    │(Informatica│    │(Teradata)│
  └─────────┘    │ DataStage)│    └─────────┘
                 └───────────┘
  問題: ETLサーバーがボトルネック、スケールしない

■ モダン ELT (Extract → Load → Transform)
  ┌─────────┐    ┌───────────┐    ┌──────────────┐
  │  Source  │ →  │ Ingestion │ →  │  Cloud DWH   │
  │(多様な   │    │(Fivetran  │    │(BigQuery/    │
  │ ソース)  │    │ Airbyte)  │    │ Snowflake)   │
  └─────────┘    └───────────┘    │  + dbt で    │
                                  │  Transform   │
                                  └──────────────┘
  利点: DWHの計算力でTransform、SQLで変換ロジック管理

■ Transformation Push-down
  - 変換処理をDWH側に押し下げる
  - DWH (BigQuery等) は MPP (大規模並列処理) エンジン
  - ETLサーバーで Python で処理するより圧倒的に速い

■ dbt の革命
  - SELECT 文だけ書けばテーブル/ビューを自動生成
  - Git でバージョン管理、CI/CD でテスト
  - リネージ (データ血統) を自動追跡
""")

    # 簡易 ELT デモ
    print("■ 簡易 ELT パイプライン実装\n")

    # Extract: ソースデータ
    raw_orders = [
        {"id": 1, "customer": "田中", "amount": 1000, "status": "completed",
         "created_at": "2024-01-01"},
        {"id": 2, "customer": "鈴木", "amount": 500, "status": "cancelled",
         "created_at": "2024-01-01"},
        {"id": 3, "customer": "田中", "amount": 2000, "status": "completed",
         "created_at": "2024-01-02"},
    ]

    # Load: そのまま raw レイヤーに格納
    raw_layer = list(raw_orders)
    print(f"  [L] Raw レイヤーに {len(raw_layer)} 件ロード")

    # Transform: DWH 内で SQL 的に変換
    # staging: クレンジング
    stg_orders = [
        {**o, "amount_jpy": o["amount"], "is_completed": o["status"] == "completed"}
        for o in raw_layer
    ]
    print(f"  [T] Staging: {len(stg_orders)} 件変換 (金額正規化, フラグ追加)")

    # mart: ビジネス集計
    customer_summary = defaultdict(lambda: {"total_orders": 0, "total_amount": 0,
                                            "completed_orders": 0})
    for o in stg_orders:
        c = customer_summary[o["customer"]]
        c["total_orders"] += 1
        c["total_amount"] += o["amount_jpy"]
        if o["is_completed"]:
            c["completed_orders"] += 1

    print(f"  [T] Mart: 顧客サマリ生成")
    for name, summary in customer_summary.items():
        rate = summary["completed_orders"] / summary["total_orders"] * 100
        print(f"      {name}: 注文={summary['total_orders']}件, "
              f"金額=¥{summary['total_amount']:,}, 完了率={rate:.0f}%")

    print("""
  💡 考えてほしい疑問:
    - ELT で raw データをそのまま保存するメリットは？ (再変換可能性)
    - dbt の incremental model はなぜ重要か？ (コスト削減)
    - Fivetran vs Airbyte: マネージド vs OSS のトレードオフは？
""")


# ============================================================
# 4. データパイプライン設計 — DAG エグゼキュータ
# ============================================================
def section_pipeline_design():
    print(f"\n{SEP}")
    print("4. データパイプライン設計 — DAG エグゼキュータ実装")
    print(SEP)

    print("""
■ DAG 設計原則 (Airflow / Dagster / Prefect)
  1. 冪等性 (Idempotency): 同じ入力 → 同じ出力。再実行しても安全
  2. 原子性 (Atomicity): タスクは成功 or 失敗。中間状態なし
  3. バックフィル: 過去日付の再処理が容易な設計
  4. データリネージ: 各テーブルの上流・下流を追跡可能
  5. SLA管理: 遅延アラート、タイムアウト設定
""")

    class Task:
        def __init__(self, name: str, func: Callable, depends_on: list[str] = None):
            self.name = name
            self.func = func
            self.depends_on = depends_on or []
            self.status = "pending"  # pending → running → success/failed
            self.result = None
            self.start_time = None
            self.end_time = None

    class DAGExecutor:
        """トポロジカルソートに基づく DAG 実行エンジン"""

        def __init__(self, name: str):
            self.name = name
            self.tasks: dict[str, Task] = {}
            self.execution_log: list[str] = []

        def add_task(self, task: Task):
            self.tasks[task.name] = task

        def _topological_sort(self) -> list[str]:
            """カーンのアルゴリズムでトポロジカルソート"""
            in_degree = {name: 0 for name in self.tasks}
            for task in self.tasks.values():
                for dep in task.depends_on:
                    in_degree[task.name] += 1

            q = deque([n for n, d in in_degree.items() if d == 0])
            order = []

            while q:
                node = q.popleft()
                order.append(node)
                for task in self.tasks.values():
                    if node in task.depends_on:
                        in_degree[task.name] -= 1
                        if in_degree[task.name] == 0:
                            q.append(task.name)

            if len(order) != len(self.tasks):
                raise ValueError("循環依存を検出しました！")
            return order

        def execute(self, context: dict = None) -> bool:
            """DAGを実行"""
            context = context or {}
            order = self._topological_sort()
            print(f"\n  DAG '{self.name}' 実行開始")
            print(f"  実行順序: {' → '.join(order)}\n")

            all_success = True
            for task_name in order:
                task = self.tasks[task_name]

                # 依存タスクの成否チェック
                deps_ok = all(
                    self.tasks[d].status == "success" for d in task.depends_on
                )
                if not deps_ok:
                    task.status = "skipped"
                    self.execution_log.append(
                        f"  ⏭ {task_name}: SKIPPED (依存タスク失敗)")
                    print(f"    SKIP  {task_name} (上流タスク失敗)")
                    all_success = False
                    continue

                task.status = "running"
                task.start_time = time.time()
                try:
                    task.result = task.func(context)
                    task.status = "success"
                    task.end_time = time.time()
                    elapsed = (task.end_time - task.start_time) * 1000
                    print(f"    OK    {task_name} ({elapsed:.1f}ms)")
                    self.execution_log.append(f"  ✓ {task_name}: SUCCESS")
                except Exception as e:
                    task.status = "failed"
                    task.end_time = time.time()
                    print(f"    FAIL  {task_name}: {e}")
                    self.execution_log.append(f"  ✗ {task_name}: FAILED - {e}")
                    all_success = False

            print(f"\n  DAG 完了: {'全タスク成功' if all_success else '一部失敗あり'}")
            return all_success

    # DAG 定義と実行
    print("■ DAG エグゼキュータ実装デモ\n")

    def extract_users(ctx):
        ctx["users"] = [
            {"id": 1, "name": "Alice", "country": "JP"},
            {"id": 2, "name": "Bob", "country": "US"},
        ]
        return f"{len(ctx['users'])} users extracted"

    def extract_orders(ctx):
        ctx["orders"] = [
            {"order_id": 1, "user_id": 1, "amount": 100},
            {"order_id": 2, "user_id": 1, "amount": 200},
            {"order_id": 3, "user_id": 2, "amount": 150},
        ]
        return f"{len(ctx['orders'])} orders extracted"

    def transform_join(ctx):
        user_map = {u["id"]: u for u in ctx["users"]}
        ctx["enriched_orders"] = [
            {**o, "user_name": user_map[o["user_id"]]["name"],
             "country": user_map[o["user_id"]]["country"]}
            for o in ctx["orders"]
        ]
        return f"{len(ctx['enriched_orders'])} enriched records"

    def load_summary(ctx):
        summary = defaultdict(float)
        for o in ctx["enriched_orders"]:
            summary[o["country"]] += o["amount"]
        ctx["summary"] = dict(summary)
        return f"Summary: {ctx['summary']}"

    dag = DAGExecutor("daily_sales_pipeline")
    dag.add_task(Task("extract_users", extract_users))
    dag.add_task(Task("extract_orders", extract_orders))
    dag.add_task(Task("transform_join", transform_join,
                      depends_on=["extract_users", "extract_orders"]))
    dag.add_task(Task("load_summary", load_summary,
                      depends_on=["transform_join"]))

    context = {}
    dag.execute(context)
    print(f"\n  最終結果: {context.get('summary', {})}")

    print("""
■ バックフィル戦略
  - パーティション分割: dt=2024-01-01 単位で再処理可能に
  - 冪等な書き込み: MERGE / INSERT OVERWRITE で重複防止
  - Airflow: catchup=True + execution_date でバックフィル

  💡 考えてほしい疑問:
    - DAG でタスクの並列実行をどう実現する？ (依存なしタスクの同時実行)
    - バックフィル時に下流タスクへの影響をどう制御する？

  [実装してみよう]
    - 上記 DAGExecutor にリトライ機能 (max_retries, retry_delay) を追加せよ
    - 並列実行対応版を threading で実装せよ
""")


# ============================================================
# 5. データ品質チェッカー
# ============================================================
def section_data_quality():
    print(f"\n{SEP}")
    print("5. データ品質 — 品質チェッカー実装")
    print(SEP)

    print("""
■ データ品質の4次元
  1. Freshness  (鮮度):   データは最新か？
  2. Completeness (完全性): NULL や欠損はないか？
  3. Accuracy   (正確性): 値の範囲は妥当か？
  4. Consistency (一貫性): テーブル間で整合しているか？

■ Great Expectations / dbt tests / Monte Carlo
  - Great Expectations: Python ベースの期待値定義
  - dbt tests: YAML で品質ルール宣言、CI で自動チェック
  - Monte Carlo: ML ベースの異常検知 (Data Observability)

■ データコントラクト
  - プロデューサーとコンシューマー間の品質契約
  - スキーマ、鮮度SLA、NULL許容率を明示的に定義
""")

    class DataQualityChecker:
        """Great Expectations ライクなデータ品質チェッカー"""

        def __init__(self, dataset_name: str):
            self.dataset_name = dataset_name
            self.results: list[dict] = []

        def _record(self, check_name: str, passed: bool, detail: str):
            self.results.append({
                "check": check_name,
                "passed": passed,
                "detail": detail,
            })

        def expect_column_not_null(self, data: list[dict], column: str):
            """列にNULLがないことを検証"""
            nulls = sum(1 for row in data if row.get(column) is None)
            passed = nulls == 0
            self._record(
                f"not_null({column})", passed,
                f"NULL件数: {nulls}/{len(data)}"
            )
            return self

        def expect_column_values_in_set(self, data: list[dict],
                                        column: str, valid_set: set):
            """列の値が許容セットに含まれることを検証"""
            invalid = [row[column] for row in data
                       if row.get(column) not in valid_set]
            passed = len(invalid) == 0
            self._record(
                f"in_set({column})", passed,
                f"不正値: {invalid[:5]}" if invalid else "OK"
            )
            return self

        def expect_column_values_between(self, data: list[dict],
                                         column: str,
                                         min_val: float, max_val: float):
            """列の値が範囲内であることを検証"""
            out_of_range = [
                row[column] for row in data
                if row.get(column) is not None
                and not (min_val <= row[column] <= max_val)
            ]
            passed = len(out_of_range) == 0
            self._record(
                f"between({column}, {min_val}, {max_val})", passed,
                f"範囲外: {out_of_range[:5]}" if out_of_range else "OK"
            )
            return self

        def expect_unique(self, data: list[dict], column: str):
            """列の値がユニークであることを検証"""
            values = [row.get(column) for row in data]
            dupes = len(values) - len(set(values))
            passed = dupes == 0
            self._record(
                f"unique({column})", passed,
                f"重複: {dupes}件" if dupes else "OK"
            )
            return self

        def expect_referential_integrity(self, data: list[dict],
                                         column: str,
                                         reference_keys: set):
            """外部キー参照整合性を検証"""
            orphans = [row[column] for row in data
                       if row.get(column) not in reference_keys]
            passed = len(orphans) == 0
            self._record(
                f"ref_integrity({column})", passed,
                f"孤立キー: {orphans[:5]}" if orphans else "OK"
            )
            return self

        def expect_freshness(self, latest_ts: str,
                             max_delay_hours: int):
            """データ鮮度チェック"""
            latest = datetime.strptime(latest_ts, "%Y-%m-%d %H:%M:%S")
            now = datetime(2024, 1, 2, 12, 0, 0)  # デモ用固定時刻
            delay = (now - latest).total_seconds() / 3600
            passed = delay <= max_delay_hours
            self._record(
                f"freshness(max={max_delay_hours}h)", passed,
                f"遅延: {delay:.1f}時間"
            )
            return self

        def report(self):
            """品質レポート出力"""
            print(f"\n  品質レポート: {self.dataset_name}")
            print(f"  {'─' * 50}")
            passed_count = 0
            for r in self.results:
                icon = "PASS" if r["passed"] else "FAIL"
                print(f"    [{icon}] {r['check']}: {r['detail']}")
                if r["passed"]:
                    passed_count += 1
            total = len(self.results)
            rate = passed_count / total * 100 if total else 0
            print(f"  {'─' * 50}")
            print(f"  結果: {passed_count}/{total} 通過 ({rate:.0f}%)")
            return all(r["passed"] for r in self.results)

    # 品質チェック実行
    print("■ 品質チェッカー実行デモ\n")

    test_data = [
        {"id": 1, "name": "Alice", "age": 28, "status": "active",
         "dept_id": 10},
        {"id": 2, "name": "Bob", "age": 150, "status": "active",
         "dept_id": 20},
        {"id": 3, "name": None, "age": 35, "status": "inactive",
         "dept_id": 30},
        {"id": 3, "name": "Dave", "age": 42, "status": "unknown",
         "dept_id": 99},
    ]
    valid_depts = {10, 20, 30, 40}

    checker = DataQualityChecker("employees")
    all_pass = (
        checker
        .expect_column_not_null(test_data, "name")
        .expect_unique(test_data, "id")
        .expect_column_values_between(test_data, "age", 0, 120)
        .expect_column_values_in_set(
            test_data, "status", {"active", "inactive", "suspended"})
        .expect_referential_integrity(test_data, "dept_id", valid_depts)
        .expect_freshness("2024-01-02 08:00:00", max_delay_hours=6)
        .report()
    )

    print(f"\n  全チェック通過: {all_pass}")

    print("""
  💡 考えてほしい疑問:
    - 品質チェック失敗時、パイプラインを止めるべきか続行すべきか？
    - データコントラクト違反をどうプロデューサーに通知する？

  [実装してみよう]
    - 品質チェック結果をJSONで出力する report_json() を追加せよ
    - 閾値ベースのチェック (NULL率5%以下なら PASS) を実装せよ
""")


# ============================================================
# 6. レイクハウスアーキテクチャ
# ============================================================
def section_lakehouse():
    print(f"\n{SEP}")
    print("6. レイクハウスアーキテクチャ — Delta / Iceberg / Hudi")
    print(SEP)

    print("""
■ データレイクの問題
  - ACID なし → 部分書き込みで壊れる
  - スキーマ管理なし → "データスワンプ" 化
  - タイムトラベル不可 → 過去状態の復元不能

■ レイクハウス = データレイク + DWH の利点を統合

┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │ Delta Lake   │ Apache Iceberg│ Apache Hudi │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 開発元       │ Databricks   │ Netflix→Apache│ Uber→Apache │
│ ACID         │ ○            │ ○             │ ○           │
│ Time Travel  │ ○ (バージョン)│ ○ (スナップ)  │ ○ (タイムライン)│
│ Schema Evol. │ ○            │ ◎ (最も柔軟)  │ ○           │
│ Partition    │ 静的         │ 動的 (hidden) │ 静的        │
│ エンジン     │ Spark中心    │ マルチエンジン │ Spark中心   │
│ 採用企業     │ Databricks系 │ Apple/Netflix │ Uber/AWS    │
└──────────────┴──────────────┴──────────────┴──────────────┘

■ 主要概念

  1. ACID on Data Lake
     - トランザクションログ (Delta: _delta_log/, Iceberg: metadata/)
     - Optimistic Concurrency Control で競合解決

  2. Time Travel
     Delta: SELECT * FROM table VERSION AS OF 5
     Iceberg: SELECT * FROM table FOR SYSTEM_TIME AS OF '2024-01-01'

  3. Schema Evolution
     - 列追加・型拡張を安全に実行
     - Iceberg: 列ID ベースで物理列名に依存しない

  4. Partition Evolution (Iceberg の強み)
     - パーティション変更時にデータ書き換え不要
     - days(ts) → hours(ts) へ透過的に変更可能

  5. Compaction / Optimize
     - 小さいファイルをマージして読み取り性能改善
     - OPTIMIZE table ZORDER BY (column)

  💡 考えてほしい疑問:
    - Delta Lake の VACUUM コマンドは何をする？リスクは？
    - Iceberg のスナップショット分離はどう MVCC を実現する？
    - Hudi の COW (Copy on Write) vs MOR (Merge on Read) の使い分けは？
    - Z-Order とは何か？なぜ多次元クエリに効くのか？
""")


# ============================================================
# 7. ストリーム処理 — Kafka / Flink
# ============================================================
def section_stream_processing():
    print(f"\n{SEP}")
    print("7. ストリーム処理 — Kafka / Flink アーキテクチャ")
    print(SEP)

    print("""
■ Kafka アーキテクチャ

  Producer → [Topic: Partition 0] → Consumer Group A
             [Topic: Partition 1] → Consumer Group A
             [Topic: Partition 2] → Consumer Group B

  - Broker: Kafka サーバーノード (3+ for HA)
  - Partition: 並列処理の単位。パーティション数 = 最大並列度
  - Consumer Group: グループ内で分担消費 (各パーティションに1consumer)
  - Offset: パーティション内の位置。コンシューマーが自己管理
  - ISR (In-Sync Replicas): 同期済みレプリカ。acks=all で全ISR書き込み確認

■ パーティション設計
  - キー指定: hash(key) % partition_count → 同じキーは同じパーティション
  - 順序保証: パーティション内のみ。グローバル順序は保証なし
  - リバランス: コンシューマー増減時にパーティション再割当

■ Flink ウィンドウ種別
  1. Tumbling Window: 固定長・重複なし [0-5min][5-10min]
  2. Sliding Window:  固定長・重複あり [0-5min][2-7min][4-9min]
  3. Session Window:  非活動ギャップで区切る [活動...gap...活動]
""")

    # --- ストリームウィンドウ実装 ---
    print("■ 3種類のウィンドウ実装デモ\n")

    events_with_ts = [
        {"user": "A", "ts": 0},
        {"user": "A", "ts": 1},
        {"user": "B", "ts": 2},
        {"user": "A", "ts": 4},
        {"user": "B", "ts": 6},
        {"user": "A", "ts": 7},
        {"user": "A", "ts": 12},
        {"user": "B", "ts": 15},
        {"user": "A", "ts": 16},
    ]

    # Tumbling Window
    def tumbling_window(events, window_size):
        windows = defaultdict(list)
        for e in events:
            window_start = (e["ts"] // window_size) * window_size
            windows[f"[{window_start}-{window_start + window_size})"].append(e)
        return dict(windows)

    print("  Tumbling Window (size=5):")
    for window, evts in sorted(tumbling_window(events_with_ts, 5).items()):
        users = [e["user"] for e in evts]
        print(f"    {window}: {users}")

    # Sliding Window
    def sliding_window(events, window_size, slide):
        windows = defaultdict(list)
        if not events:
            return {}
        max_ts = max(e["ts"] for e in events)
        start = 0
        while start <= max_ts:
            end = start + window_size
            key = f"[{start}-{end})"
            for e in events:
                if start <= e["ts"] < end:
                    windows[key].append(e)
            start += slide
        return {k: v for k, v in windows.items() if v}

    print("\n  Sliding Window (size=5, slide=3):")
    for window, evts in sorted(sliding_window(events_with_ts, 5, 3).items()):
        users = [e["user"] for e in evts]
        print(f"    {window}: {users}")

    # Session Window
    def session_window(events, gap):
        if not events:
            return {}
        sorted_events = sorted(events, key=lambda e: e["ts"])
        sessions = []
        current_session = [sorted_events[0]]
        for e in sorted_events[1:]:
            if e["ts"] - current_session[-1]["ts"] > gap:
                sessions.append(list(current_session))
                current_session = [e]
            else:
                current_session.append(e)
        sessions.append(current_session)
        return {f"Session{i}[{s[0]['ts']}-{s[-1]['ts']}]": s
                for i, s in enumerate(sessions)}

    print("\n  Session Window (gap=3):")
    for window, evts in session_window(events_with_ts, 3).items():
        users = [e["user"] for e in evts]
        print(f"    {window}: {users}")

    print("""
■ バックプレッシャー (Backpressure)
  - 下流が処理しきれない場合に上流を減速させるメカニズム
  - Flink: credit-based flow control
  - Kafka: consumer lag の監視 → パーティション/コンシューマー追加

  💡 考えてほしい疑問:
    - Kafka の retention period を超えたデータはどうなる？
    - Flink のチェックポイントはどう exactly-once を保証する？
    - Consumer Group のリバランスはなぜ "stop the world" 問題を起こす？

  [実装してみよう]
    - 上記 Session Window をユーザー別に分離して実装せよ
    - Sliding Window で「直近5秒のイベント数」をリアルタイム計算する関数を実装せよ
""")


# ============================================================
# 8. dbt パターン
# ============================================================
def section_dbt_patterns():
    print(f"\n{SEP}")
    print("8. dbt パターン — Staging → Intermediate → Marts")
    print(SEP)

    print("""
■ dbt のレイヤー構成

  sources (raw)
      ↓ source()
  staging (stg_*):  1 source = 1 model, リネーム・型変換・フィルタ
      ↓ ref()
  intermediate (int_*):  ビジネスロジック、JOIN、集計
      ↓ ref()
  marts (fct_*, dim_*):  BI ツールに公開するテーブル

■ 重要な dbt 機能

  1. ref() と source()
     - ref('stg_orders') → テーブル間の依存を宣言 → DAG 自動構築
     - source('stripe', 'payments') → 外部ソースの参照を一元管理

  2. Incremental Model (増分処理)
     ```sql
     {{config(materialized='incremental',
              unique_key='order_id',
              incremental_strategy='merge')}}

     SELECT * FROM {{ ref('stg_orders') }}
     {% if is_incremental() %}
       WHERE updated_at > (SELECT max(updated_at) FROM {{ this }})
     {% endif %}
     ```
     - 初回: 全件INSERT
     - 2回目以降: 更新分のみ MERGE

  3. Snapshot (SCD Type 2 自動化)
     ```sql
     {% snapshot orders_snapshot %}
     {{config(strategy='timestamp',
              unique_key='order_id',
              updated_at='updated_at')}}
     SELECT * FROM {{ source('app', 'orders') }}
     {% endsnapshot %}
     ```
     - dbt が自動で valid_from/valid_to/dbt_scd_id を管理

  4. Tests
     - Generic: not_null, unique, accepted_values, relationships
     - Singular: カスタムSQLテスト
     ```yaml
     models:
       - name: fct_orders
         columns:
           - name: order_id
             tests: [not_null, unique]
           - name: status
             tests:
               - accepted_values:
                   values: ['completed', 'cancelled', 'pending']
     ```

  5. Documentation & Lineage
     - description でドキュメント記述
     - dbt docs generate → リネージグラフ自動生成

■ dbt のベストプラクティス
  - staging は 1:1 マッピング (ソーステーブル1つに1モデル)
  - marts は機能ドメイン別 (marketing/, finance/, product/)
  - ephemeral は使いすぎない (デバッグ困難)
  - tags でモデルをグルーピング (dbt run --select tag:daily)

  💡 考えてほしい疑問:
    - incremental_strategy の merge vs delete+insert vs insert_overwrite の違いは？
    - dbt の macro はどう DRY 原則を支援するか？
    - dbt test は CI で実行すべきか、本番パイプラインに組み込むべきか？

  [実装してみよう]
    - Python で dbt の ref() 的な依存管理システムを実装せよ
    - Snapshot 的な SCD Type 2 自動管理を dict ベースで実装せよ
""")


# ============================================================
# 9. Spark 最適化
# ============================================================
def section_spark_optimization():
    print(f"\n{SEP}")
    print("9. Spark 最適化 — パフォーマンスチューニング")
    print(SEP)

    print("""
■ Partitioning vs Bucketing

  Partitioning:
    - ディレクトリ分割 (year=2024/month=01/)
    - フィルタ時にディレクトリスキップ (partition pruning)
    - 高カーディナリティ列には不向き (小さいファイル大量発生)

  Bucketing:
    - ファイル内でハッシュ分割
    - JOIN 時にシャッフル不要 (同じバケットID同士をJOIN)
    - Spark 限定機能 (Hive 互換)

■ Join 戦略

  1. Sort-Merge Join (デフォルト)
     - 両テーブルをキーでソート → マージ
     - 大テーブル × 大テーブル向け

  2. Broadcast Join
     - 小テーブルを全ワーカーにコピー
     - spark.sql.autoBroadcastJoinThreshold = 10MB (デフォルト)
     - 設定: df.hint("broadcast") or /*+ BROADCAST(small_table) */

  3. Shuffle Hash Join
     - ハッシュでパーティション → 同キー同ノードで JOIN
     - Sort-Merge より速い場合あり

■ AQE (Adaptive Query Execution) - Spark 3.0+
  1. Coalesce Shuffle Partitions
     - 実行時に空/小パーティションを結合
     - spark.sql.adaptive.coalescePartitions.enabled = true

  2. Switch Join Strategy
     - 実行時統計でブロードキャストJOINに切替

  3. Skew Join Optimization
     - 偏ったパーティションを自動分割
     - spark.sql.adaptive.skewJoin.enabled = true

■ データスキュー対策
  1. Salting: キーにランダム接頭辞追加 → 分散 → 後で集約
     ```python
     df = df.withColumn("salted_key",
              concat(col("join_key"), lit("_"), (rand()*10).cast("int")))
     ```
  2. Broadcast: 片方が小さければ broadcast
  3. AQE: Spark 3.x で自動対処

■ Explain Plan の読み方
  ```
  == Physical Plan ==
  *(5) HashAggregate(keys=[region], functions=[sum(amount)])
  +- Exchange hashpartitioning(region, 200)    ← シャッフル！
     +- *(4) HashAggregate(keys=[region], functions=[partial_sum(amount)])
        +- *(3) Project [region, amount]
           +- *(2) BroadcastHashJoin [store_id], [id]  ← ブロードキャスト
              :- *(1) Scan parquet [sales]
              +- BroadcastExchange
                 +- Scan parquet [stores]
  ```
  注目ポイント:
  - Exchange → シャッフル発生 (高コスト)
  - Scan → FileScan で partition pruning 確認
  - BroadcastExchange → 小テーブルのブロードキャスト

■ よくあるチューニング設定
  spark.sql.shuffle.partitions = 200 → データ量に応じて調整
  spark.sql.files.maxPartitionBytes = 128MB
  spark.serializer = org.apache.spark.serializer.KryoSerializer
  spark.memory.fraction = 0.6 → 実行/キャッシュメモリ比率

  💡 考えてほしい疑問:
    - パーティション数が多すぎると何が起きる？ (タスクオーバーヘッド)
    - パーティション数が少なすぎると何が起きる？ (OOM, 並列度低下)
    - cache() vs persist() の違いは？いつ使うべきか？
    - repartition() vs coalesce() の違いは？

  [実装してみよう]
    - Python の list で salting 手法 (キーにランダム接頭辞) を疑似実装せよ
    - 簡易的な hash partitioner を実装し、データ分散の偏りを可視化せよ
""")


# ============================================================
# 10. 面接問題
# ============================================================
def section_interview():
    print(f"\n{SEP}")
    print("10. 面接問題: リアルタイム分析パイプライン設計")
    print(SEP)

    print("""
■ 問題:
  「配車アプリ (Uber/Lyft 規模) で 1M events/sec のリアルタイム分析
   パイプラインを設計せよ」

■ 要件整理 (まず確認すべきこと)
  - イベント種類: ride_request, driver_location, trip_start, trip_end,
                  payment, rating
  - レイテンシ要件: リアルタイムダッシュボード (< 5sec), 日次レポート
  - データ量: 1M events/sec × 500B/event ≈ 500MB/sec ≈ 43TB/day
  - 保持期間: ホットデータ 30日, コールドデータ 7年
  - 分析要件: エリア別需要予測、動的価格設定、ドライバー最適配置

■ アーキテクチャ設計

  ┌─────────────────────────────────────────────────────────┐
  │                    Data Sources                        │
  │  Mobile App → API Gateway → Kafka (Event Ingestion)    │
  │  Driver GPS → Direct Kafka Producer                    │
  └──────────┬──────────────────────────┬──────────────────┘
             │                          │
  ┌──────────▼──────────┐  ┌───────────▼──────────────────┐
  │  Stream Processing  │  │  Batch Processing            │
  │  (Flink Cluster)    │  │  (Spark on K8s)              │
  │                     │  │                              │
  │  - Surge Pricing    │  │  - Daily Aggregation         │
  │  - Fraud Detection  │  │  - ML Feature Engineering    │
  │  - Real-time ETAs   │  │  - Historical Analytics      │
  │  - Geo Aggregation  │  │                              │
  └──────────┬──────────┘  └───────────┬──────────────────┘
             │                          │
  ┌──────────▼──────────┐  ┌───────────▼──────────────────┐
  │  Serving Layer      │  │  Data Lake (Iceberg on S3)   │
  │  - Redis (real-time)│  │  - Bronze: raw events        │
  │  - Druid (OLAP)     │  │  - Silver: cleansed/enriched │
  │  - ES (search)      │  │  - Gold: aggregated marts    │
  └─────────────────────┘  └──────────────────────────────┘

■ Kafka 設計詳細
  - Topic 分割: ride_events (100 partitions), driver_locations (200 partitions)
  - パーティションキー: ride_events → rider_id, locations → driver_id
  - Replication Factor: 3 (ISR min = 2)
  - Retention: 7 days (再処理のバッファ)
  - Schema Registry: Avro + Confluent Schema Registry

■ Flink ストリーム処理詳細
  1. Surge Pricing:
     - Sliding Window (5min, slide 1min) でエリア別需要集計
     - 需要/供給比率から価格倍率算出 → Redis に即時書き込み

  2. リアルタイム ETA:
     - Session Window でドライバーの移動パターン追跡
     - H3 地理インデックスでエリア集約

  3. 不正検知:
     - CEP (Complex Event Processing) で異常パターン検出
     - 同一カードで5分以内に異なるエリアから決済 → アラート

■ スケーリング戦略
  - Kafka: パーティション追加で水平スケール
  - Flink: パラレリズム調整 + チェックポイント間隔最適化
  - 1M events/sec の場合:
    - Kafka Broker: 6-9 台 (3 rack)
    - Flink TaskManager: 20-30 台
    - 推定コスト: $50-80K/month (AWS)

■ データ品質・運用
  - Schema Registry で前方/後方互換性を強制
  - Dead Letter Queue で処理失敗イベントを退避
  - Consumer Lag モニタリング (Burrow / Kafka Exporter + Prometheus)
  - SLA: p99 processing latency < 3sec

■ 面接での差別化ポイント
  1. Kappa Architecture を選ぶ理由を説明できる
  2. Exactly-once の実現方法を具体的に語れる
  3. データスキュー対策 (特定エリアに集中) を提案できる
  4. コスト見積もりができる
  5. 障害シナリオ (Kafka broker 障害、Flink checkpoint 失敗) を議論できる
""")

    # --- 簡易リアルタイム集計デモ ---
    print("■ 簡易リアルタイムエリア需要集計デモ\n")

    class RealTimeAreaDemand:
        """スライディングウィンドウでエリア別需要をリアルタイム集計"""

        def __init__(self, window_size_sec: int, slide_sec: int):
            self.window_size = window_size_sec
            self.slide = slide_sec
            self.events: deque = deque()

        def add_event(self, area: str, ts: float):
            self.events.append({"area": area, "ts": ts})
            # ウィンドウ外のイベントを削除
            cutoff = ts - self.window_size
            while self.events and self.events[0]["ts"] < cutoff:
                self.events.popleft()

        def get_demand(self, current_ts: float) -> dict[str, int]:
            """現在ウィンドウ内のエリア別需要"""
            cutoff = current_ts - self.window_size
            demand = defaultdict(int)
            for e in self.events:
                if e["ts"] >= cutoff:
                    demand[e["area"]] += 1
            return dict(demand)

        def calculate_surge(self, demand: dict,
                            supply: dict) -> dict[str, float]:
            """需要/供給比率からサージ倍率算出"""
            surge = {}
            for area, d in demand.items():
                s = supply.get(area, 1)
                ratio = d / max(s, 1)
                if ratio > 2.0:
                    surge[area] = min(ratio * 0.8, 5.0)
                else:
                    surge[area] = 1.0
            return surge

    # シミュレーション
    analyzer = RealTimeAreaDemand(window_size_sec=10, slide_sec=2)

    ride_requests = [
        ("渋谷", 1), ("渋谷", 2), ("渋谷", 3), ("新宿", 2),
        ("渋谷", 5), ("六本木", 6), ("渋谷", 7), ("新宿", 8),
        ("渋谷", 9), ("渋谷", 10), ("六本木", 11),
    ]

    supply = {"渋谷": 2, "新宿": 3, "六本木": 2}

    print("  タイムステップごとの需要とサージ:")
    for area, ts in ride_requests:
        analyzer.add_event(area, ts)

    # ts=12 時点のスナップショット
    demand = analyzer.get_demand(12)
    surge = analyzer.calculate_surge(demand, supply)
    print(f"\n  ts=12 時点の需要: {demand}")
    print(f"  供給: {supply}")
    print(f"  サージ倍率:")
    for area in sorted(surge.keys()):
        multiplier = surge[area]
        bar = "█" * int(multiplier * 5)
        print(f"    {area}: {multiplier:.1f}x {bar}")

    print(f"""
■ 面接のフォローアップ質問に備える

  Q: 「Kafka のパーティション数を後から増やすと何が起きる？」
  A: 既存キーのパーティション割当が変わる → 順序保証が崩れる
     → 対策: パーティション数は最初に余裕を持って設定

  Q: 「Flink のチェックポイントが遅い場合どうする？」
  A: 1) incremental checkpoint に切替
     2) RocksDB state backend 使用
     3) チェックポイント間隔を延長 (ただしリカバリ時間増)

  Q: 「データスキュー (渋谷に集中) にどう対処する？」
  A: 1) H3 で細粒度エリア分割
     2) Flink の key group 再分配
     3) Salting + 2段階集約

  Q: 「コスト削減するには？」
  A: 1) ホットデータのみ Druid、コールドは Iceberg on S3
     2) Spot Instance for Flink TaskManager
     3) Tiered Storage for Kafka (KIP-405)
     4) 集計粒度を落とす (1sec → 10sec)

  💡 考えてほしい疑問:
    - この設計で Single Point of Failure はどこか？
    - GDPR でユーザーデータ削除要求が来たらどう対応する？
    - マルチリージョン展開する場合の課題は？
""")


# ============================================================
# メイン実行
# ============================================================
def main():
    print("=" * 60)
    print("  FAANG レベル データエンジニアリング パターン完全ガイド")
    print("=" * 60)
    print(f"  実行日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Python 標準ライブラリのみ使用")

    section_data_modeling()
    section_batch_vs_stream()
    section_etl_vs_elt()
    section_pipeline_design()
    section_data_quality()
    section_lakehouse()
    section_stream_processing()
    section_dbt_patterns()
    section_spark_optimization()
    section_interview()

    print(f"\n{SEP}")
    print("まとめ: データエンジニアリング学習ロードマップ")
    print(SEP)
    print("""
  Level 1 (基礎): SQL高度化, データモデリング, ETL/ELT 概念
  Level 2 (実践): dbt, Airflow, Spark 基礎, Kafka 基礎
  Level 3 (応用): ストリーム処理, レイクハウス, データ品質
  Level 4 (FAANG): システム設計, 大規模最適化, コスト見積もり

  次のステップ:
    - dbt のハンズオン → phase7_data/dbt_project/
    - DAG設計の実践  → phase7_data/dags/
    - Kafka / Flink のローカル環境構築 (Docker Compose)
""")

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - Star Schema
    - バッチ vs ストリーム
    - データ品質チェック
    - DAG設計

  【Tier 2: 重要 — 実務で頻出】
    - Data Vault 2.0
    - Tumbling/Sliding Window
    - レイクハウス(Delta/Iceberg)

  【Tier 3: 上級 — シニア以上で差がつく】
    - Lambda vs Kappa Architecture
    - Session Window
    - Schema Evolution

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Data Mesh
    - Data Contract
    - Slowly Changing Dimension Type 2
""")


if __name__ == "__main__":
    main()
