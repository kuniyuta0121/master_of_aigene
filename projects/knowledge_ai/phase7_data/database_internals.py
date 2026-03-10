#!/usr/bin/env python3
"""
=============================================================================
Database Internals & Query Optimization Deep Dive
=============================================================================
データベースの内部構造とクエリ最適化を実装を通じて理解する。

対象:
  - クエリプランナー / オプティマイザ
  - JOIN アルゴリズム (3種)
  - インデックス (B+ Tree, Hash Index)
  - WAL & Recovery
  - Vacuum / Compaction
  - Connection Pool & Query Lifecycle
  - 分散DB アーキテクチャ
  - EXPLAIN 読解ガイド

Python 標準ライブラリのみ使用。
"""

import time
import random
import hashlib
import math
import bisect
import os
import json
import tempfile
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum, auto

# ============================================================================
# 1. クエリプランナー / オプティマイザ
# ============================================================================
"""
【Cost-Based Optimizer (CBO) の仕組み】

SQL が実行されるまでの流れ:
  Parse → Analyze → Rewrite → Plan (★ここ) → Execute

プランナーは複数の実行計画候補を生成し、最もコストが低いものを選ぶ。

コスト = (CPU コスト) + (I/O コスト)
       = (タプル処理数 × cpu_tuple_cost) + (ページ読み込み数 × seq_page_cost)

【Statistics (統計情報)】
  - pg_class.reltuples    : テーブルの推定行数
  - pg_class.relpages     : テーブルのページ数 (8KB 単位)
  - pg_stats.n_distinct   : カラムのカーディナリティ
  - pg_stats.most_common_vals : 最頻値リスト
  - pg_stats.histogram_bounds : ヒストグラム境界値

Selectivity (選択率) = 条件に一致する行の割合
  - 等値: selectivity = 1 / n_distinct
  - 範囲: selectivity = (upper - lower) / (max - min)
  - 推定行数 = total_rows × selectivity
"""


class ScanType(Enum):
    SEQ_SCAN = auto()       # 全件走査
    INDEX_SCAN = auto()     # インデックス走査
    BITMAP_SCAN = auto()    # ビットマップ走査


class JoinType(Enum):
    NESTED_LOOP = auto()
    HASH_JOIN = auto()
    MERGE_JOIN = auto()


@dataclass
class TableStats:
    """テーブルの統計情報 (ANALYZE で収集されるもの)"""
    name: str
    row_count: int          # 推定行数
    page_count: int         # ページ数 (8KB 単位)
    avg_row_width: int      # 平均行幅 (bytes)
    columns: dict = field(default_factory=dict)
    # columns[col_name] = {"n_distinct": int, "histogram": [...]}


@dataclass
class PlanNode:
    """実行計画ツリーのノード"""
    operation: str          # "SeqScan", "IndexScan", "HashJoin", etc.
    table: str = ""
    estimated_rows: int = 0
    estimated_cost: float = 0.0
    children: list = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def display(self, indent: int = 0) -> str:
        """EXPLAIN 風に表示"""
        prefix = "  " * indent + ("-> " if indent > 0 else "")
        cost_str = f"(cost={self.estimated_cost:.2f} rows={self.estimated_rows})"
        line = f"{prefix}{self.operation}"
        if self.table:
            line += f" on {self.table}"
        line += f"  {cost_str}"
        if self.details:
            detail_parts = [f"{k}: {v}" for k, v in self.details.items()]
            line += f"  [{', '.join(detail_parts)}]"
        lines = [line]
        for child in self.children:
            lines.append(child.display(indent + 1))
        return "\n".join(lines)


class SimpleQueryPlanner:
    """
    簡易クエリプランナー:
    SQL 文字列を解析し、コストベースで最適な実行計画を生成する。
    """
    # PostgreSQL 互換のコスト定数
    SEQ_PAGE_COST = 1.0
    RANDOM_PAGE_COST = 4.0     # ランダム I/O は 4 倍高い
    CPU_TUPLE_COST = 0.01
    CPU_INDEX_TUPLE_COST = 0.005
    CPU_OPERATOR_COST = 0.0025

    def __init__(self):
        self.table_stats: dict[str, TableStats] = {}
        self.indexes: dict[str, list[str]] = {}  # table -> [indexed_columns]

    def register_table(self, stats: TableStats):
        self.table_stats[stats.name] = stats

    def register_index(self, table: str, column: str):
        self.indexes.setdefault(table, []).append(column)

    def estimate_selectivity(self, table: str, column: str,
                             operator: str, value: Any) -> float:
        """選択率の推定"""
        stats = self.table_stats.get(table)
        if not stats or column not in stats.columns:
            return 0.1  # デフォルト: 10%

        col_stats = stats.columns[column]
        n_distinct = col_stats.get("n_distinct", 100)
        histogram = col_stats.get("histogram", [])

        if operator == "=":
            # 等値: 1 / カーディナリティ
            return 1.0 / n_distinct
        elif operator in ("<", "<=", ">", ">=") and histogram:
            # 範囲: ヒストグラムベースの推定
            min_val, max_val = histogram[0], histogram[-1]
            if max_val == min_val:
                return 0.5
            if operator in ("<", "<="):
                return (value - min_val) / (max_val - min_val)
            else:
                return (max_val - value) / (max_val - min_val)
        return 0.33  # デフォルト

    def cost_seq_scan(self, table: str, selectivity: float = 1.0) -> PlanNode:
        """Sequential Scan のコスト計算"""
        stats = self.table_stats[table]
        # I/O: 全ページ読み込み + CPU: 全タプル処理
        io_cost = stats.page_count * self.SEQ_PAGE_COST
        cpu_cost = stats.row_count * self.CPU_TUPLE_COST
        total_cost = io_cost + cpu_cost
        estimated_rows = int(stats.row_count * selectivity)

        return PlanNode(
            operation="Seq Scan",
            table=table,
            estimated_rows=max(1, estimated_rows),
            estimated_cost=total_cost,
            details={"filter_selectivity": f"{selectivity:.4f}"}
        )

    def cost_index_scan(self, table: str, column: str,
                        selectivity: float) -> Optional[PlanNode]:
        """Index Scan のコスト計算"""
        if table not in self.indexes or column not in self.indexes[table]:
            return None

        stats = self.table_stats[table]
        estimated_rows = max(1, int(stats.row_count * selectivity))

        # I/O: ランダムアクセス (インデックス + テーブル)
        index_pages = max(1, int(math.log2(stats.row_count + 1)) + 1)
        heap_pages = min(estimated_rows, stats.page_count)
        io_cost = (index_pages + heap_pages) * self.RANDOM_PAGE_COST
        cpu_cost = estimated_rows * self.CPU_INDEX_TUPLE_COST

        return PlanNode(
            operation="Index Scan",
            table=table,
            estimated_rows=estimated_rows,
            estimated_cost=io_cost + cpu_cost,
            details={"index_column": column}
        )

    def choose_best_scan(self, table: str, column: str = None,
                         operator: str = None, value: Any = None) -> PlanNode:
        """最適なスキャン方法を選択"""
        selectivity = 1.0
        if column and operator:
            selectivity = self.estimate_selectivity(table, column, operator, value)

        seq = self.cost_seq_scan(table, selectivity)
        candidates = [seq]

        if column:
            idx = self.cost_index_scan(table, column, selectivity)
            if idx:
                candidates.append(idx)

        # コスト最小のプランを選択
        return min(candidates, key=lambda p: p.estimated_cost)

    def choose_join_method(self, left: PlanNode, right: PlanNode,
                           join_column: str) -> PlanNode:
        """最適な JOIN アルゴリズムを選択"""
        nl_cost = left.estimated_rows * right.estimated_rows * self.CPU_TUPLE_COST
        hash_cost = ((left.estimated_rows + right.estimated_rows)
                     * self.CPU_TUPLE_COST * 2)
        merge_cost = ((left.estimated_rows * math.log2(max(1, left.estimated_rows))
                       + right.estimated_rows * math.log2(max(1, right.estimated_rows)))
                      * self.CPU_TUPLE_COST)

        costs = {
            "Nested Loop": nl_cost,
            "Hash Join": hash_cost,
            "Merge Join": merge_cost,
        }
        best = min(costs, key=costs.get)
        estimated_rows = max(1, min(left.estimated_rows, right.estimated_rows))

        return PlanNode(
            operation=best,
            estimated_rows=estimated_rows,
            estimated_cost=left.estimated_cost + right.estimated_cost + costs[best],
            children=[left, right],
            details={"join_on": join_column}
        )

    def plan_query(self, tables: list[str],
                   conditions: list[dict] = None,
                   join_column: str = None) -> PlanNode:
        """
        簡易クエリプランニング: テーブル・条件・結合情報から実行計画を生成

        conditions: [{"table": "t", "column": "c", "op": "=", "value": 42}, ...]
        """
        conditions = conditions or []
        # テーブルごとのスキャンプラン
        scan_plans = {}
        for t in tables:
            cond = next((c for c in conditions if c["table"] == t), None)
            if cond:
                scan_plans[t] = self.choose_best_scan(
                    t, cond["column"], cond["op"], cond["value"])
            else:
                scan_plans[t] = self.choose_best_scan(t)

        if len(tables) == 1:
            return scan_plans[tables[0]]

        # 複数テーブル: JOIN (小さい方を内側に)
        sorted_tables = sorted(tables, key=lambda t: scan_plans[t].estimated_rows)
        result = scan_plans[sorted_tables[0]]
        for t in sorted_tables[1:]:
            result = self.choose_join_method(result, scan_plans[t],
                                            join_column or "id")
        return result


def demo_query_planner():
    """クエリプランナーのデモ"""
    print("=" * 70)
    print("1. クエリプランナー / オプティマイザ")
    print("=" * 70)

    planner = SimpleQueryPlanner()

    # テーブル統計を登録 (ANALYZE 相当)
    orders = TableStats(
        name="orders", row_count=1_000_000, page_count=50_000,
        avg_row_width=120,
        columns={
            "customer_id": {"n_distinct": 50_000, "histogram": list(range(1, 50001))},
            "status": {"n_distinct": 5, "histogram": [0, 1, 2, 3, 4]},
            "amount": {"n_distinct": 10_000, "histogram": list(range(0, 100001, 10))},
        }
    )
    customers = TableStats(
        name="customers", row_count=50_000, page_count=2_500,
        avg_row_width=200,
        columns={
            "id": {"n_distinct": 50_000, "histogram": list(range(1, 50001))},
            "country": {"n_distinct": 100, "histogram": list(range(1, 101))},
        }
    )
    planner.register_table(orders)
    planner.register_table(customers)
    planner.register_index("orders", "customer_id")
    planner.register_index("customers", "id")

    # ケース1: 単純な Seq Scan (フィルタなし)
    print("\n--- ケース1: SELECT * FROM orders (フィルタなし) ---")
    plan = planner.plan_query(["orders"])
    print(plan.display())

    # ケース2: インデックスが効く等値検索
    print("\n--- ケース2: SELECT * FROM orders WHERE customer_id = 12345 ---")
    plan = planner.plan_query(
        ["orders"],
        conditions=[{"table": "orders", "column": "customer_id",
                      "op": "=", "value": 12345}]
    )
    print(plan.display())
    print("  → 選択率 1/50000 なので Index Scan が選ばれる")

    # ケース3: 選択率が高いと Seq Scan
    print("\n--- ケース3: SELECT * FROM orders WHERE status = 1 ---")
    plan = planner.plan_query(
        ["orders"],
        conditions=[{"table": "orders", "column": "status",
                      "op": "=", "value": 1}]
    )
    print(plan.display())
    print("  → status のカーディナリティ=5 → 選択率 20% → Seq Scan")

    # ケース4: JOIN
    print("\n--- ケース4: orders JOIN customers ON customer_id ---")
    plan = planner.plan_query(
        ["orders", "customers"],
        conditions=[
            {"table": "orders", "column": "customer_id", "op": "=", "value": 12345},
        ],
        join_column="customer_id"
    )
    print(plan.display())
    print("  → 小テーブル(customers)を内側に配置、Hash Join を選択")


# ============================================================================
# 2. JOIN アルゴリズム (3種の実装 + ベンチマーク)
# ============================================================================
"""
【JOIN アルゴリズム判定フローチャート】

Q: 結合条件は等値(=)か？
  No → Nested Loop Join (唯一の選択肢)
  Yes ↓
Q: 両テーブルとも小さい (< 1000行) か？
  Yes → Nested Loop Join (オーバーヘッドが小さい)
  No ↓
Q: 片方がメモリに収まるか？
  Yes → Hash Join (最速, work_mem 以内)
  No ↓
Q: 両方ソート済み or インデックスあり？
  Yes → Sort-Merge Join
  No → Hash Join (ディスクスピル覚悟)
"""


def nested_loop_join(left: list[dict], right: list[dict],
                     left_key: str, right_key: str) -> list[dict]:
    """
    Nested Loop Join: O(n × m)
    - 最もシンプル
    - 小テーブル同士の結合に適する
    - 内側テーブルにインデックスがあると O(n × log m)
    """
    result = []
    for l_row in left:
        for r_row in right:
            if l_row[left_key] == r_row[right_key]:
                merged = {**l_row, **{f"r_{k}": v for k, v in r_row.items()}}
                result.append(merged)
    return result


def hash_join(left: list[dict], right: list[dict],
              left_key: str, right_key: str) -> list[dict]:
    """
    Hash Join: O(n + m)
    - Build フェーズ: 小さいテーブルでハッシュテーブル構築
    - Probe フェーズ: 大きいテーブルをスキャンして照合
    - 等値結合のみ対応
    - メモリ使用量: 小さいテーブル分
    """
    # Build フェーズ (小さいテーブルを選ぶ)
    if len(left) <= len(right):
        build_table, probe_table = left, right
        build_key, probe_key = left_key, right_key
        is_left_build = True
    else:
        build_table, probe_table = right, left
        build_key, probe_key = right_key, left_key
        is_left_build = False

    hash_map = defaultdict(list)
    for row in build_table:
        hash_map[row[build_key]].append(row)

    # Probe フェーズ
    result = []
    for probe_row in probe_table:
        key_val = probe_row[probe_key]
        if key_val in hash_map:
            for build_row in hash_map[key_val]:
                if is_left_build:
                    merged = {**build_row,
                              **{f"r_{k}": v for k, v in probe_row.items()}}
                else:
                    merged = {**probe_row,
                              **{f"r_{k}": v for k, v in build_row.items()}}
                result.append(merged)
    return result


def sort_merge_join(left: list[dict], right: list[dict],
                    left_key: str, right_key: str) -> list[dict]:
    """
    Sort-Merge Join: O(n log n + m log m)
    - 両テーブルをソートして同時に走査
    - ソート済みデータならO(n + m)
    - 範囲結合にも対応可能
    - ディスクスピル時にも効率的
    """
    sorted_left = sorted(left, key=lambda r: r[left_key])
    sorted_right = sorted(right, key=lambda r: r[right_key])

    result = []
    i, j = 0, 0

    while i < len(sorted_left) and j < len(sorted_right):
        lv = sorted_left[i][left_key]
        rv = sorted_right[j][right_key]

        if lv < rv:
            i += 1
        elif lv > rv:
            j += 1
        else:
            # 一致 → 同じ値のグループを全て結合
            left_group = []
            while i < len(sorted_left) and sorted_left[i][left_key] == lv:
                left_group.append(sorted_left[i])
                i += 1
            right_group = []
            while j < len(sorted_right) and sorted_right[j][right_key] == rv:
                right_group.append(sorted_right[j])
                j += 1
            for lr in left_group:
                for rr in right_group:
                    merged = {**lr, **{f"r_{k}": v for k, v in rr.items()}}
                    result.append(merged)
    return result


def demo_join_algorithms():
    """JOIN アルゴリズムのベンチマーク比較"""
    print("\n" + "=" * 70)
    print("2. JOIN アルゴリズム (3種の実装 + ベンチマーク)")
    print("=" * 70)

    sizes = [(100, 100), (500, 500), (1000, 1000)]

    for left_size, right_size in sizes:
        # テストデータ生成
        random.seed(42)
        left = [{"id": i, "value": f"L{i}", "join_key": random.randint(1, left_size // 2)}
                for i in range(left_size)]
        right = [{"id": i, "name": f"R{i}", "join_key": random.randint(1, right_size // 2)}
                 for i in range(right_size)]

        print(f"\n--- Left: {left_size}行 × Right: {right_size}行 ---")

        results = {}
        for name, func in [
            ("Nested Loop", nested_loop_join),
            ("Hash Join", hash_join),
            ("Sort-Merge", sort_merge_join),
        ]:
            start = time.perf_counter()
            result = func(left, right, "join_key", "join_key")
            elapsed = time.perf_counter() - start
            results[name] = (len(result), elapsed)
            print(f"  {name:15s}: {elapsed*1000:8.2f} ms  結果: {len(result)} 行")

        # 結果の一致を確認
        counts = set(r[0] for r in results.values())
        assert len(counts) == 1, "全 JOIN で結果行数が一致すべき"

    print("\n【判定フローチャート】")
    print("  等値結合? → No → Nested Loop")
    print("  両テーブル小? → Yes → Nested Loop")
    print("  片方メモリ内? → Yes → Hash Join (★最も一般的)")
    print("  ソート済み? → Yes → Sort-Merge Join")
    print("  それ以外 → Hash Join (ディスクスピルあり)")


# ============================================================================
# 3. インデックス Deep Dive (B+ Tree & Hash Index)
# ============================================================================
"""
【B-Tree vs B+ Tree】
  B-Tree : 全ノードにデータ格納 → 内部ノードが大きい → ツリーが深い
  B+ Tree: リーフのみデータ格納 → 内部ノード軽量 → ファンアウト大 → 浅い
           リーフが双方向リンクリスト → 範囲検索が高速

【インデックスの種類】
  - B+ Tree Index  : 範囲検索・ソート・等値検索すべて対応 (デフォルト)
  - Hash Index     : 等値検索のみ、O(1)、範囲検索不可
  - GIN Index      : 全文検索・配列・JSONB 用
  - GiST Index     : 地理データ・幾何学データ用
  - BRIN Index     : 巨大テーブルで物理順序と相関があるカラム用

【Multi-Column Index の最左プレフィックスルール】
  CREATE INDEX idx ON t (a, b, c);
  → WHERE a = 1                    ✅ 使える
  → WHERE a = 1 AND b = 2          ✅ 使える
  → WHERE a = 1 AND b = 2 AND c=3  ✅ 使える
  → WHERE b = 2                    ❌ 使えない (先頭がない)
  → WHERE a = 1 AND c = 3          ⚠️ a のみ使える

【Index Scan vs Seq Scan の閾値】
  一般的に取得行数がテーブルの 5-10% を超えると Seq Scan が有利
  理由: Index Scan はランダム I/O (4×高い) + インデックスのページ読み込み
"""


class BPlusTreeNode:
    """B+ Tree のノード"""
    def __init__(self, order: int, is_leaf: bool = False):
        self.order = order          # 最大キー数
        self.keys: list = []
        self.children: list = []    # 内部ノード: 子ノード, リーフ: 値
        self.is_leaf = is_leaf
        self.next_leaf: Optional['BPlusTreeNode'] = None  # リーフのリンクリスト
        self.prev_leaf: Optional['BPlusTreeNode'] = None

    @property
    def is_full(self) -> bool:
        return len(self.keys) >= self.order


class BPlusTree:
    """
    B+ Tree 実装
    - 内部ノード: キーのみ保持 (ルーティング)
    - リーフノード: キーと値を保持
    - リーフは双方向リンクリスト → 範囲スキャンが O(k)
    """
    def __init__(self, order: int = 4):
        self.order = order
        self.root = BPlusTreeNode(order, is_leaf=True)

    def search(self, key) -> Optional[Any]:
        """キーを検索: O(log n)"""
        node = self._find_leaf(key)
        for i, k in enumerate(node.keys):
            if k == key:
                return node.children[i]
        return None

    def range_search(self, low, high) -> list[tuple]:
        """範囲検索: リーフのリンクリストを辿る"""
        node = self._find_leaf(low)
        result = []
        while node:
            for i, k in enumerate(node.keys):
                if low <= k <= high:
                    result.append((k, node.children[i]))
                elif k > high:
                    return result
            node = node.next_leaf
        return result

    def insert(self, key, value):
        """キーと値を挿入"""
        leaf = self._find_leaf(key)

        # 既存キーの更新
        for i, k in enumerate(leaf.keys):
            if k == key:
                leaf.children[i] = value
                return

        # 挿入位置を決定
        idx = bisect.bisect_left(leaf.keys, key)
        leaf.keys.insert(idx, key)
        leaf.children.insert(idx, value)

        # ノードが溢れたら分割
        if leaf.is_full:
            self._split(leaf)

    def _find_leaf(self, key) -> BPlusTreeNode:
        """キーが属するリーフノードを探す"""
        node = self.root
        while not node.is_leaf:
            idx = bisect.bisect_right(node.keys, key)
            node = node.children[idx]
        return node

    def _split(self, node: BPlusTreeNode):
        """ノード分割 (B+ Tree の核心)"""
        mid = len(node.keys) // 2

        new_node = BPlusTreeNode(self.order, is_leaf=node.is_leaf)

        if node.is_leaf:
            # リーフ分割: 右半分を新ノードに
            new_node.keys = node.keys[mid:]
            new_node.children = node.children[mid:]
            node.keys = node.keys[:mid]
            node.children = node.children[:mid]

            # リンクリスト更新
            new_node.next_leaf = node.next_leaf
            new_node.prev_leaf = node
            if node.next_leaf:
                node.next_leaf.prev_leaf = new_node
            node.next_leaf = new_node

            up_key = new_node.keys[0]  # リーフ: 最小キーを親に上げる
        else:
            # 内部ノード分割
            up_key = node.keys[mid]
            new_node.keys = node.keys[mid + 1:]
            new_node.children = node.children[mid + 1:]
            node.keys = node.keys[:mid]
            node.children = node.children[:mid + 1]

        # 親に挿入
        if node == self.root:
            new_root = BPlusTreeNode(self.order, is_leaf=False)
            new_root.keys = [up_key]
            new_root.children = [node, new_node]
            self.root = new_root
        else:
            parent = self._find_parent(self.root, node)
            idx = bisect.bisect_right(parent.keys, up_key)
            parent.keys.insert(idx, up_key)
            parent.children.insert(idx + 1, new_node)
            if parent.is_full:
                self._split(parent)

    def _find_parent(self, current: BPlusTreeNode,
                     target: BPlusTreeNode) -> Optional[BPlusTreeNode]:
        """親ノードを探す"""
        if current.is_leaf:
            return None
        for child in current.children:
            if child == target:
                return current
            if not child.is_leaf:
                result = self._find_parent(child, target)
                if result:
                    return result
        return None

    def display(self, node=None, level=0):
        """ツリー構造を表示"""
        if node is None:
            node = self.root
        indent = "  " * level
        leaf_mark = " [LEAF]" if node.is_leaf else ""
        print(f"{indent}Level {level}{leaf_mark}: keys={node.keys}")
        if not node.is_leaf:
            for child in node.children:
                self.display(child, level + 1)


class HashIndex:
    """
    Hash Index 実装
    - O(1) の等値検索
    - 範囲検索は不可
    - PostgreSQL 10+ で WAL 対応、それ以前はクラッシュ非安全
    """
    def __init__(self, bucket_count: int = 64):
        self.bucket_count = bucket_count
        self.buckets: list[list[tuple]] = [[] for _ in range(bucket_count)]
        self.size = 0

    def _hash(self, key) -> int:
        h = hashlib.md5(str(key).encode()).hexdigest()
        return int(h, 16) % self.bucket_count

    def insert(self, key, value):
        bucket_idx = self._hash(key)
        bucket = self.buckets[bucket_idx]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self.size += 1

    def search(self, key) -> Optional[Any]:
        bucket_idx = self._hash(key)
        for k, v in self.buckets[bucket_idx]:
            if k == key:
                return v
        return None

    def stats(self) -> dict:
        lengths = [len(b) for b in self.buckets]
        return {
            "total_entries": self.size,
            "bucket_count": self.bucket_count,
            "avg_chain_length": sum(lengths) / self.bucket_count,
            "max_chain_length": max(lengths),
            "empty_buckets": sum(1 for l in lengths if l == 0),
        }


def demo_indexes():
    """インデックスのデモ"""
    print("\n" + "=" * 70)
    print("3. インデックス Deep Dive (B+ Tree & Hash Index)")
    print("=" * 70)

    # B+ Tree
    print("\n--- B+ Tree (order=4) ---")
    tree = BPlusTree(order=4)
    keys = [10, 20, 5, 15, 25, 30, 35, 40, 3, 7, 12, 18]
    for k in keys:
        tree.insert(k, f"val_{k}")

    print("ツリー構造:")
    tree.display()

    print(f"\n検索 search(15) = {tree.search(15)}")
    print(f"検索 search(99) = {tree.search(99)}")

    print(f"\n範囲検索 range(10, 25) = {tree.range_search(10, 25)}")
    print("  → リーフのリンクリストで効率的に走査")

    # ベンチマーク: B+ Tree vs リスト
    print("\n--- ベンチマーク: B+ Tree vs 線形探索 ---")
    n = 10000
    tree = BPlusTree(order=32)
    data_list = []
    random.seed(42)
    keys = random.sample(range(n * 10), n)
    for k in keys:
        tree.insert(k, k * 100)
        data_list.append((k, k * 100))

    search_keys = random.sample(keys, min(1000, n))

    start = time.perf_counter()
    for k in search_keys:
        tree.search(k)
    tree_time = time.perf_counter() - start

    start = time.perf_counter()
    for k in search_keys:
        next((v for key, v in data_list if key == k), None)
    linear_time = time.perf_counter() - start

    print(f"  B+ Tree  : {tree_time*1000:.2f} ms ({len(search_keys)} 回検索)")
    print(f"  線形探索 : {linear_time*1000:.2f} ms")
    print(f"  速度比   : {linear_time/tree_time:.1f}x 高速")

    # Hash Index
    print("\n--- Hash Index ---")
    hidx = HashIndex(bucket_count=128)
    for k in keys:
        hidx.insert(k, k * 100)
    print(f"  search({keys[0]}) = {hidx.search(keys[0])}")
    print(f"  統計: {hidx.stats()}")

    # Covering Index の説明
    print("\n【Covering Index (カバリングインデックス)】")
    print("  CREATE INDEX idx_cover ON orders(customer_id) INCLUDE (amount, status);")
    print("  → SELECT amount, status FROM orders WHERE customer_id = 123;")
    print("  → Index Only Scan: テーブル本体へのアクセス不要 (ヒープフェッチ=0)")
    print("  → Visibility Map が all-visible なページは MVCC チェックも不要")

    print("\n【Partial Index (部分インデックス)】")
    print("  CREATE INDEX idx_active ON orders(created_at) WHERE status = 'active';")
    print("  → active な行だけインデックス化 → サイズ激減 → 更新も軽い")


# ============================================================================
# 4. WAL (Write-Ahead Log) & Recovery
# ============================================================================
"""
【WAL の原則】
  データを変更する前に、必ずログを先にディスクに書く (fsync)
  → クラッシュしてもログから復旧可能

【ARIES Recovery アルゴリズム】
  1. Analysis: 最後の Checkpoint から WAL を読み、ダーティページを特定
  2. Redo   : WAL を先頭から再生し、コミット済みの変更を反映
  3. Undo   : 未コミットのトランザクションを巻き戻す

【Checkpoint の役割】
  - 定期的にダーティページをディスクにフラッシュ
  - Recovery の開始位置を進める → 起動時間短縮
  - PostgreSQL: checkpoint_timeout (default 5 min)

【PITR (Point-in-Time Recovery)】
  ベースバックアップ + WAL アーカイブ → 任意の時点に復旧可能
  recovery_target_time = '2024-01-15 14:30:00'
"""


class WALRecord:
    """WAL レコード"""
    def __init__(self, lsn: int, txn_id: int, operation: str,
                 table: str, key: Any, old_value: Any, new_value: Any):
        self.lsn = lsn              # Log Sequence Number
        self.txn_id = txn_id
        self.operation = operation  # "INSERT", "UPDATE", "DELETE", "COMMIT", "ABORT"
        self.table = table
        self.key = key
        self.old_value = old_value  # Undo 用
        self.new_value = new_value  # Redo 用
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "lsn": self.lsn, "txn_id": self.txn_id, "op": self.operation,
            "table": self.table, "key": self.key,
            "old": self.old_value, "new": self.new_value,
        }


class SimpleWALEngine:
    """
    簡易 WAL エンジン
    - Write-Ahead Logging: データ変更前にログを書く
    - ARIES Recovery: Analysis → Redo → Undo
    """
    def __init__(self, wal_dir: str):
        self.wal_dir = wal_dir
        self.wal_file = os.path.join(wal_dir, "wal.json")
        self.data_file = os.path.join(wal_dir, "data.json")
        self.checkpoint_file = os.path.join(wal_dir, "checkpoint.json")

        os.makedirs(wal_dir, exist_ok=True)

        self.data: dict[str, dict] = {}       # table -> {key: value}
        self.wal_records: list[WALRecord] = []
        self.lsn_counter = 0
        self.active_txns: set[int] = set()
        self.committed_txns: set[int] = set()
        self.next_txn_id = 1

    def begin_txn(self) -> int:
        """トランザクション開始"""
        txn_id = self.next_txn_id
        self.next_txn_id += 1
        self.active_txns.add(txn_id)
        return txn_id

    def write(self, txn_id: int, table: str, key: Any, value: Any):
        """データ書き込み (WAL を先に書く)"""
        self.data.setdefault(table, {})
        old_value = self.data[table].get(key)

        # Step 1: WAL にログを書く (先行書き込み)
        self.lsn_counter += 1
        record = WALRecord(
            lsn=self.lsn_counter, txn_id=txn_id,
            operation="UPDATE" if old_value else "INSERT",
            table=table, key=key,
            old_value=old_value, new_value=value
        )
        self.wal_records.append(record)
        self._flush_wal()  # fsync 相当

        # Step 2: メモリ上のデータを更新 (バッファプール)
        self.data[table][key] = value

    def commit(self, txn_id: int):
        """コミット"""
        self.lsn_counter += 1
        record = WALRecord(
            lsn=self.lsn_counter, txn_id=txn_id,
            operation="COMMIT", table="", key=None,
            old_value=None, new_value=None
        )
        self.wal_records.append(record)
        self._flush_wal()
        self.active_txns.discard(txn_id)
        self.committed_txns.add(txn_id)

    def abort(self, txn_id: int):
        """アボート (Undo)"""
        # この txn の変更を巻き戻す
        for record in reversed(self.wal_records):
            if record.txn_id == txn_id and record.operation in ("INSERT", "UPDATE"):
                if record.old_value is None:
                    self.data[record.table].pop(record.key, None)
                else:
                    self.data[record.table][record.key] = record.old_value

        self.lsn_counter += 1
        abort_rec = WALRecord(
            lsn=self.lsn_counter, txn_id=txn_id,
            operation="ABORT", table="", key=None,
            old_value=None, new_value=None
        )
        self.wal_records.append(abort_rec)
        self._flush_wal()
        self.active_txns.discard(txn_id)

    def checkpoint(self):
        """チェックポイント: データをディスクに書き出す"""
        with open(self.data_file, "w") as f:
            json.dump(self.data, f)
        checkpoint_info = {
            "lsn": self.lsn_counter,
            "committed_txns": list(self.committed_txns),
        }
        with open(self.checkpoint_file, "w") as f:
            json.dump(checkpoint_info, f)

    def _flush_wal(self):
        """WAL をディスクに書き出す (fsync)"""
        records = [r.to_dict() for r in self.wal_records]
        with open(self.wal_file, "w") as f:
            json.dump(records, f)

    def simulate_crash(self):
        """クラッシュをシミュレート: メモリデータ消失"""
        self.data = {}
        self.active_txns = set()
        self.committed_txns = set()

    def recover(self) -> dict:
        """
        ARIES Recovery: WAL からデータを復旧

        1. Analysis: チェックポイントから WAL を読む
        2. Redo: コミット済み txn の変更を再生
        3. Undo: 未コミット txn の変更を巻き戻す
        """
        report = {"phase": [], "recovered_data": {}}

        # チェックポイントからデータを読み込み
        if os.path.exists(self.data_file):
            with open(self.data_file) as f:
                self.data = json.load(f)
        checkpoint_lsn = 0
        committed_at_checkpoint = set()
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file) as f:
                cp = json.load(f)
                checkpoint_lsn = cp["lsn"]
                committed_at_checkpoint = set(cp["committed_txns"])

        # WAL を読み込み
        if not os.path.exists(self.wal_file):
            return report
        with open(self.wal_file) as f:
            wal_data = json.load(f)

        # Phase 1: Analysis - コミット済み/未コミット txn を分類
        report["phase"].append("Analysis")
        committed = set(committed_at_checkpoint)
        aborted = set()
        all_txns = set()
        for rec in wal_data:
            if rec["txn_id"]:
                all_txns.add(rec["txn_id"])
            if rec["op"] == "COMMIT":
                committed.add(rec["txn_id"])
            elif rec["op"] == "ABORT":
                aborted.add(rec["txn_id"])
        uncommitted = all_txns - committed - aborted

        # Phase 2: Redo - チェックポイント以降のコミット済み変更を再生
        report["phase"].append(f"Redo (from LSN {checkpoint_lsn})")
        for rec in wal_data:
            if rec["lsn"] > checkpoint_lsn and rec["txn_id"] in committed:
                if rec["op"] in ("INSERT", "UPDATE"):
                    self.data.setdefault(rec["table"], {})
                    self.data[rec["table"]][str(rec["key"])] = rec["new"]

        # Phase 3: Undo - 未コミットの変更を巻き戻す
        report["phase"].append(f"Undo (txns: {uncommitted})")
        for rec in reversed(wal_data):
            if rec["txn_id"] in uncommitted and rec["op"] in ("INSERT", "UPDATE"):
                if rec["old"] is None:
                    self.data.get(rec["table"], {}).pop(str(rec["key"]), None)
                else:
                    self.data.setdefault(rec["table"], {})
                    self.data[rec["table"]][str(rec["key"])] = rec["old"]

        report["recovered_data"] = self.data
        self.committed_txns = committed
        return report


def demo_wal_recovery():
    """WAL & Recovery のデモ"""
    print("\n" + "=" * 70)
    print("4. WAL (Write-Ahead Log) & Recovery")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        engine = SimpleWALEngine(os.path.join(tmpdir, "db"))

        # 正常なトランザクション
        txn1 = engine.begin_txn()
        engine.write(txn1, "users", 1, {"name": "Alice", "age": 30})
        engine.write(txn1, "users", 2, {"name": "Bob", "age": 25})
        engine.commit(txn1)

        # チェックポイント
        engine.checkpoint()

        # チェックポイント後のトランザクション
        txn2 = engine.begin_txn()
        engine.write(txn2, "users", 3, {"name": "Charlie", "age": 35})
        engine.commit(txn2)

        # 未コミットのトランザクション (クラッシュ時に Undo される)
        txn3 = engine.begin_txn()
        engine.write(txn3, "users", 4, {"name": "GHOST", "age": 0})
        # txn3 は commit されていない!

        print("\n--- クラッシュ前のデータ ---")
        for key, val in engine.data.get("users", {}).items():
            print(f"  users[{key}] = {val}")

        # クラッシュ!
        print("\n💥 クラッシュ発生! メモリデータ消失")
        engine.simulate_crash()
        print(f"  データ: {engine.data}")

        # Recovery
        print("\n--- ARIES Recovery 開始 ---")
        report = engine.recover()
        for phase in report["phase"]:
            print(f"  Phase: {phase}")

        print("\n--- 復旧後のデータ ---")
        for key, val in engine.data.get("users", {}).items():
            print(f"  users[{key}] = {val}")
        print("  → GHOST(未コミット) は Undo され、Alice/Bob/Charlie は復旧")


# ============================================================================
# 5. Vacuum / Compaction
# ============================================================================
"""
【PostgreSQL MVCC + Vacuum】

MVCC (Multi-Version Concurrency Control):
  - UPDATE = 旧行を「dead」にして新行を INSERT
  - DELETE = 行を「dead」にする
  - dead tuple はすぐに消えない → Vacuum が回収

Dead Tuple の蓄積問題:
  - テーブル膨張 (Bloat) → ディスク浪費 + Seq Scan 遅延
  - インデックス膨張 → 検索性能低下
  - Transaction ID Wraparound → 最悪データ消失

Autovacuum チューニング:
  autovacuum_vacuum_threshold = 50        # 最小 dead tuple 数
  autovacuum_vacuum_scale_factor = 0.2    # テーブルの 20% が dead
  → トリガー条件: dead >= threshold + scale_factor × total_rows

  よく使うチューニング:
    ALTER TABLE hot_table SET (autovacuum_vacuum_scale_factor = 0.01);
    ALTER TABLE hot_table SET (autovacuum_vacuum_cost_delay = 10);

【LSM-Tree の Compaction 戦略】

LSM-Tree (Log-Structured Merge Tree):
  書き込み最適化: MemTable → SSTable (ソート済みファイル) → Compaction

  Size-Tiered Compaction (Cassandra デフォルト):
    - 同サイズの SSTable が溜まったらマージ
    - 書き込み高速、スペース増幅大 (一時的に 2× 必要)

  Leveled Compaction (RocksDB / LevelDB):
    - Level 0 → Level 1 → ... とマージ
    - 読み取り高速、書き込み増幅大 (最大 10×)
"""


class MVCCTable:
    """
    PostgreSQL の MVCC + Vacuum を再現したテーブル
    """
    def __init__(self, name: str):
        self.name = name
        self.rows: list[dict] = []  # 全バージョン (dead 含む)
        self.next_xid = 1  # トランザクションID

    def insert(self, data: dict) -> int:
        xid = self.next_xid
        self.next_xid += 1
        row = {
            "xmin": xid,      # 作成した txn
            "xmax": None,     # 削除した txn (None = 生存)
            "data": data,
            "dead": False,
        }
        self.rows.append(row)
        return xid

    def update(self, index: int, new_data: dict) -> int:
        """UPDATE = 旧行を dead にして新行を作成"""
        xid = self.next_xid
        self.next_xid += 1

        # 旧行を dead に
        old_row = self.rows[index]
        old_row["xmax"] = xid
        old_row["dead"] = True

        # 新行を追加
        new_row = {
            "xmin": xid, "xmax": None,
            "data": new_data, "dead": False,
        }
        self.rows.append(new_row)
        return xid

    def delete(self, index: int) -> int:
        """DELETE = 行を dead にする (即座には消さない)"""
        xid = self.next_xid
        self.next_xid += 1
        self.rows[index]["xmax"] = xid
        self.rows[index]["dead"] = True
        return xid

    def vacuum(self) -> dict:
        """Vacuum: Dead tuple を回収"""
        before = len(self.rows)
        dead_count = sum(1 for r in self.rows if r["dead"])
        self.rows = [r for r in self.rows if not r["dead"]]
        after = len(self.rows)
        return {
            "before": before,
            "dead_removed": dead_count,
            "after": after,
            "space_reclaimed_pct": f"{dead_count/max(before,1)*100:.1f}%"
        }

    def stats(self) -> dict:
        live = sum(1 for r in self.rows if not r["dead"])
        dead = sum(1 for r in self.rows if r["dead"])
        return {"total": len(self.rows), "live": live, "dead": dead,
                "bloat_pct": f"{dead/max(len(self.rows),1)*100:.1f}%"}


class LSMTree:
    """
    LSM-Tree の簡易実装 (Compaction 戦略のデモ)
    MemTable → Immutable MemTable → SSTable(Level 0) → Compaction
    """
    def __init__(self, memtable_size: int = 4):
        self.memtable_size = memtable_size
        self.memtable: dict = {}                # 現在の MemTable
        self.sstables: list[list[tuple]] = []   # Level 0 の SSTable リスト
        self.tombstones: set = set()            # 削除マーカー
        self.compaction_count = 0

    def put(self, key, value):
        """書き込み: MemTable に追加"""
        self.memtable[key] = value
        self.tombstones.discard(key)
        if len(self.memtable) >= self.memtable_size:
            self._flush_memtable()

    def delete(self, key):
        """削除: Tombstone を書く (実データはCompaction時に消える)"""
        self.tombstones.add(key)
        self.memtable.pop(key, None)

    def get(self, key):
        """読み取り: MemTable → SSTable の順に検索"""
        if key in self.tombstones:
            return None
        if key in self.memtable:
            return self.memtable[key]
        # 新しい SSTable から順に検索
        for sstable in reversed(self.sstables):
            for k, v in sstable:
                if k == key:
                    return v
        return None

    def _flush_memtable(self):
        """MemTable → SSTable に変換"""
        sorted_data = sorted(self.memtable.items())
        self.sstables.append(sorted_data)
        self.memtable = {}

        # SSTable が溜まったら Compaction
        if len(self.sstables) >= 3:
            self._compact()

    def _compact(self):
        """
        Size-Tiered Compaction: 全 SSTable をマージ
        - Tombstone のキーは除外
        - 重複キーは最新を採用
        """
        merged = {}
        for sstable in self.sstables:
            for k, v in sstable:
                if k not in self.tombstones:
                    merged[k] = v

        self.sstables = [sorted(merged.items())]
        self.compaction_count += 1

    def stats(self) -> dict:
        total_entries = sum(len(s) for s in self.sstables) + len(self.memtable)
        return {
            "memtable_size": len(self.memtable),
            "sstable_count": len(self.sstables),
            "total_entries": total_entries,
            "tombstones": len(self.tombstones),
            "compactions": self.compaction_count,
        }


def demo_vacuum_compaction():
    """Vacuum / Compaction のデモ"""
    print("\n" + "=" * 70)
    print("5. Vacuum / Compaction")
    print("=" * 70)

    # PostgreSQL MVCC + Vacuum
    print("\n--- PostgreSQL MVCC + Vacuum ---")
    table = MVCCTable("orders")

    # 初期データ投入
    for i in range(10):
        table.insert({"id": i, "amount": i * 100})

    # UPDATE を繰り返す → dead tuple が蓄積
    for i in range(10):
        # 最新の live 行のインデックスを探す
        live_indices = [j for j, r in enumerate(table.rows)
                        if not r["dead"] and r["data"]["id"] == i]
        if live_indices:
            table.update(live_indices[0], {"id": i, "amount": i * 200})

    print(f"  UPDATE 後の統計: {table.stats()}")
    print("  → dead tuple が蓄積し、テーブルが膨張している")

    # Vacuum 実行
    result = table.vacuum()
    print(f"  Vacuum 結果: {result}")
    print(f"  Vacuum 後の統計: {table.stats()}")

    # LSM-Tree Compaction
    print("\n--- LSM-Tree Compaction ---")
    lsm = LSMTree(memtable_size=4)

    # 書き込み
    for i in range(15):
        lsm.put(f"key_{i:03d}", f"value_{i}")
    print(f"  15件書き込み後: {lsm.stats()}")

    # 削除 (Tombstone)
    lsm.delete("key_003")
    lsm.delete("key_007")
    print(f"  2件削除後: {lsm.stats()}")

    # 読み取り
    print(f"  get('key_005') = {lsm.get('key_005')}")
    print(f"  get('key_003') = {lsm.get('key_003')}  ← Tombstone で削除済み")

    print("\n【Compaction 戦略の比較】")
    print("  ┌─────────────────┬──────────────────┬──────────────────┐")
    print("  │                 │ Size-Tiered      │ Leveled          │")
    print("  ├─────────────────┼──────────────────┼──────────────────┤")
    print("  │ 書き込み増幅    │ 低 (良)          │ 高 (10×)         │")
    print("  │ スペース増幅    │ 高 (2×)          │ 低 (1.1×)        │")
    print("  │ 読み取り増幅    │ 高               │ 低 (良)          │")
    print("  │ 用途            │ 書き込みヘビー   │ 読み取りヘビー   │")
    print("  │ 実装例          │ Cassandra        │ RocksDB/LevelDB  │")
    print("  └─────────────────┴──────────────────┴──────────────────┘")


# ============================================================================
# 6. Connection Pool & Query Lifecycle
# ============================================================================
"""
【Connection Pool の仕組み】

DB 接続は高コスト:
  TCP handshake → SSL → 認証 → セッション初期化 = 50-200ms

Connection Pool:
  - 事前に接続を確立してプールに保持
  - リクエスト時にプールから取得 → 返却
  - idle 接続のタイムアウト管理

設定パラメータ:
  min_connections = 5     # 最小常駐接続数
  max_connections = 20    # 最大接続数
  idle_timeout = 300      # idle 接続のタイムアウト (秒)
  connection_timeout = 5  # 接続取得の待機タイムアウト (秒)

Pool 枯渇の原因:
  1. 長時間トランザクション (LOCK 待ち等)
  2. 接続リーク (close 忘れ)
  3. N+1 クエリによる大量接続
  4. 突発的なトラフィック増

対策:
  - PgBouncer (外部プーラー) の導入
  - Statement-level pooling で接続共有
  - idle_in_transaction_session_timeout の設定

【Query の実行フロー】
  1. Parse    : SQL文字列 → 構文木 (Abstract Syntax Tree)
  2. Analyze  : テーブル/カラムの存在確認、型チェック
  3. Rewrite  : ビュー展開、ルール適用
  4. Plan     : 実行計画生成 (CBO)
  5. Execute  : 実行計画に従ってデータ取得

Prepared Statement:
  PREPARE stmt AS SELECT * FROM users WHERE id = $1;
  EXECUTE stmt(123);
  → Parse/Analyze/Rewrite を 1 回だけ実行 → 2 回目以降は Plan+Execute のみ
  → Parse キャッシュで高速化 (10-30% 改善)
"""


class ConnectionPool:
    """Connection Pool の簡易実装"""

    class Connection:
        def __init__(self, conn_id: int):
            self.id = conn_id
            self.in_use = False
            self.created_at = time.time()
            self.last_used = time.time()
            self.queries_executed = 0

        def execute(self, query: str) -> str:
            self.queries_executed += 1
            self.last_used = time.time()
            return f"[Conn#{self.id}] Executed: {query}"

    def __init__(self, min_conn: int = 2, max_conn: int = 10,
                 idle_timeout: float = 30.0):
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.idle_timeout = idle_timeout
        self.connections: list[ConnectionPool.Connection] = []
        self.next_id = 1
        self.total_acquired = 0
        self.total_wait = 0

        # 最小接続数を事前確立
        for _ in range(min_conn):
            self._create_connection()

    def _create_connection(self) -> 'ConnectionPool.Connection':
        conn = self.Connection(self.next_id)
        self.next_id += 1
        self.connections.append(conn)
        return conn

    def acquire(self) -> Optional['ConnectionPool.Connection']:
        """プールから接続を取得"""
        # idle 接続を探す
        for conn in self.connections:
            if not conn.in_use:
                conn.in_use = True
                self.total_acquired += 1
                return conn

        # idle なし → 新規作成 (max 以内)
        if len(self.connections) < self.max_conn:
            conn = self._create_connection()
            conn.in_use = True
            self.total_acquired += 1
            return conn

        # Pool 枯渇
        self.total_wait += 1
        return None

    def release(self, conn: 'ConnectionPool.Connection'):
        """接続をプールに返却"""
        conn.in_use = False
        conn.last_used = time.time()

    def cleanup_idle(self):
        """タイムアウトした idle 接続を閉じる"""
        now = time.time()
        active = []
        closed = 0
        for conn in self.connections:
            if (not conn.in_use
                    and now - conn.last_used > self.idle_timeout
                    and len(active) >= self.min_conn):
                closed += 1
            else:
                active.append(conn)
        self.connections = active
        return closed

    def stats(self) -> dict:
        in_use = sum(1 for c in self.connections if c.in_use)
        idle = sum(1 for c in self.connections if not c.in_use)
        return {
            "total": len(self.connections),
            "in_use": in_use,
            "idle": idle,
            "max": self.max_conn,
            "total_acquired": self.total_acquired,
            "total_wait (pool枯渇)": self.total_wait,
        }


def demo_connection_pool():
    """Connection Pool のデモ"""
    print("\n" + "=" * 70)
    print("6. Connection Pool & Query Lifecycle")
    print("=" * 70)

    pool = ConnectionPool(min_conn=3, max_conn=5)
    print(f"\n--- 初期状態 ---")
    print(f"  {pool.stats()}")

    # 接続取得と使用
    conns = []
    print("\n--- 接続取得 ---")
    for i in range(6):
        conn = pool.acquire()
        if conn:
            result = conn.execute(f"SELECT * FROM users WHERE id = {i}")
            print(f"  {result}")
            conns.append(conn)
        else:
            print(f"  ⚠ Pool 枯渇! 接続取得失敗 (max={pool.max_conn})")

    print(f"\n--- 全接続使用中 ---")
    print(f"  {pool.stats()}")

    # 一部返却
    for conn in conns[:3]:
        pool.release(conn)
    print(f"\n--- 3接続返却後 ---")
    print(f"  {pool.stats()}")

    print("\n【Query の実行フロー】")
    print("  Client → Parse → Analyze → Rewrite → Plan → Execute → Result")
    print("           ↑       ↑          ↑")
    print("           └───────┴──────────┘")
    print("           Prepared Statement は")
    print("           ここをキャッシュして省略")


# ============================================================================
# 7. 分散DB のアーキテクチャ
# ============================================================================
"""
【レプリケーション戦略】

Single-Leader (Master-Slave):
  ┌────────┐     ┌────────┐     ┌────────┐
  │ Leader │────→│Follower│────→│Follower│
  │ (R/W)  │     │ (R)    │     │ (R)    │
  └────────┘     └────────┘     └────────┘
  ✅ 一貫性が高い   ❌ Leader がボトルネック
  用途: PostgreSQL, MySQL

Multi-Leader:
  ┌────────┐     ┌────────┐
  │Leader A│←───→│Leader B│
  │ (R/W)  │     │ (R/W)  │
  └────────┘     └────────┘
  ✅ 書き込みスケール  ❌ コンフリクト解決が複雑
  用途: CockroachDB, 地理分散システム

Leaderless (Dynamo-style):
  ┌──────┐  ┌──────┐  ┌──────┐
  │Node A│  │Node B│  │Node C│
  └──────┘  └──────┘  └──────┘
  W=2, R=2 (Quorum: W+R > N で一貫性保証)
  ✅ 高可用性   ❌ 一貫性が弱い (eventual)
  用途: Cassandra, DynamoDB

【Partitioning (シャーディング)】

Range Partitioning:
  Shard A: user_id 1-1000
  Shard B: user_id 1001-2000
  ✅ 範囲クエリ効率的  ❌ ホットスポット (新しいIDに集中)

Hash Partitioning:
  Shard = hash(user_id) % N
  ✅ 均等分散  ❌ 範囲クエリが全シャードに

Consistent Hashing:
  ノード追加/削除時に再配置が最小限
  用途: DynamoDB, Cassandra

【分散トランザクション】

2PC (Two-Phase Commit):
  Phase 1: Coordinator → 全ノードに PREPARE 要求
  Phase 2: 全ノードが OK → COMMIT / 1つでも NG → ABORT
  ❌ Coordinator 障害でブロッキング

Saga パターン:
  T1 → T2 → T3 (各ステップにCompensation)
  失敗時: C3 → C2 → C1 (補償トランザクション)
  ✅ ブロッキングなし  ❌ 実装が複雑

【NewSQL の仕組み】

Google Spanner:
  - TrueTime API (原子時計 + GPS) で厳密な時刻同期
  - External Consistency (線形化可能性)
  - 自動シャーディング + 自動フェイルオーバー

CockroachDB (Spanner inspired):
  - Raft でコンセンサス
  - Hybrid Logical Clock (HLC) でスケール
  - PostgreSQL 互換 SQL

TiDB:
  - MySQL 互換
  - TiKV (RocksDB ベース) + PD (Placement Driver)
  - HTAP (OLTP + OLAP 同時処理)
"""


class ConsistentHash:
    """
    Consistent Hashing の実装
    ノード追加/削除時の再配置を最小化する分散アルゴリズム
    """
    def __init__(self, replicas: int = 150):
        self.replicas = replicas    # 仮想ノード数
        self.ring: list[tuple[int, str]] = []  # (hash, node_name)
        self.nodes: set[str] = set()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str):
        """ノード追加 (仮想ノードをリングに配置)"""
        self.nodes.add(node)
        for i in range(self.replicas):
            h = self._hash(f"{node}:{i}")
            bisect.insort(self.ring, (h, node))

    def remove_node(self, node: str):
        """ノード削除"""
        self.nodes.discard(node)
        self.ring = [(h, n) for h, n in self.ring if n != node]

    def get_node(self, key: str) -> str:
        """キーの担当ノードを検索"""
        if not self.ring:
            raise ValueError("No nodes in ring")
        h = self._hash(key)
        idx = bisect.bisect_left(self.ring, (h,))
        if idx >= len(self.ring):
            idx = 0
        return self.ring[idx][1]

    def get_distribution(self, num_keys: int = 10000) -> dict[str, int]:
        """キー分散の統計"""
        dist = defaultdict(int)
        for i in range(num_keys):
            node = self.get_node(f"key_{i}")
            dist[node] += 1
        return dict(dist)


def demo_distributed_db():
    """分散DB アーキテクチャのデモ"""
    print("\n" + "=" * 70)
    print("7. 分散DB のアーキテクチャ")
    print("=" * 70)

    # Consistent Hashing
    print("\n--- Consistent Hashing ---")
    ch = ConsistentHash(replicas=150)
    for node in ["node-A", "node-B", "node-C"]:
        ch.add_node(node)

    dist = ch.get_distribution(10000)
    print("  3ノードでの分散:")
    for node, count in sorted(dist.items()):
        bar = "#" * (count // 100)
        print(f"    {node}: {count} keys ({count/100:.1f}%)  {bar}")

    # ノード追加時の影響
    old_assignments = {f"key_{i}": ch.get_node(f"key_{i}") for i in range(1000)}
    ch.add_node("node-D")
    new_assignments = {f"key_{i}": ch.get_node(f"key_{i}") for i in range(1000)}
    moved = sum(1 for k in old_assignments if old_assignments[k] != new_assignments[k])
    print(f"\n  ノード追加 (3→4) 時の再配置: {moved}/1000 keys ({moved/10:.1f}%)")
    print("  → 理想は 25% (1/4)、Consistent Hashing で近似")

    dist4 = ch.get_distribution(10000)
    print("\n  4ノードでの分散:")
    for node, count in sorted(dist4.items()):
        bar = "#" * (count // 100)
        print(f"    {node}: {count} keys ({count/100:.1f}%)  {bar}")

    # 2PC シミュレーション
    print("\n--- 2PC (Two-Phase Commit) シミュレーション ---")

    class TwoPhaseCoordinator:
        def __init__(self, participants: list[str]):
            self.participants = participants

        def execute(self, all_vote_yes: bool = True) -> str:
            print("  Phase 1 (Prepare):")
            votes = {}
            for p in self.participants:
                vote = "YES" if all_vote_yes or p != self.participants[-1] else "NO"
                votes[p] = vote
                print(f"    {p} → {vote}")

            print("  Phase 2 (Decision):")
            if all(v == "YES" for v in votes.values()):
                for p in self.participants:
                    print(f"    {p} ← COMMIT")
                return "COMMITTED"
            else:
                for p in self.participants:
                    print(f"    {p} ← ABORT")
                return "ABORTED"

    coordinator = TwoPhaseCoordinator(["shard-1", "shard-2", "shard-3"])
    print("\n  ケース1: 全員 YES")
    result = coordinator.execute(all_vote_yes=True)
    print(f"  結果: {result}")

    print("\n  ケース2: 1つが NO")
    result = coordinator.execute(all_vote_yes=False)
    print(f"  結果: {result}")


# ============================================================================
# 8. EXPLAIN 読解ガイド
# ============================================================================
"""
【EXPLAIN の読み方】

PostgreSQL:
  EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;

出力例:
  Index Scan using idx_customer_id on orders
    (cost=0.43..8.45 rows=1 width=120)
    (actual time=0.025..0.026 rows=1 loops=1)

コストの読み方:
  cost=0.43..8.45
       ↑       ↑
  startup cost  total cost (1行目を返すまで..最終行まで)

  rows=1    : 推定行数 (ANALYZE で実測値も出る)
  width=120 : 平均行幅 (bytes)
  loops=1   : 実行回数 (Nested Loop の内側は N 回)

【主要なノードタイプ】

Scan:
  Seq Scan         : 全件走査 (フィルタ率高い or テーブル小さい)
  Index Scan       : インデックス→ヒープ (選択率低い時)
  Index Only Scan  : インデックスのみ (カバリングインデックス)
  Bitmap Index Scan: ビットマップ作成→ヒープ一括 (中間的選択率)

Join:
  Nested Loop      : 小テーブル同士 or Index付き内側
  Hash Join        : 大テーブル等値結合 (片方メモリ内)
  Merge Join       : ソート済みデータの結合

Aggregate:
  HashAggregate    : ハッシュテーブルで GROUP BY
  GroupAggregate   : ソートしてから GROUP BY
  Sort             : ORDER BY or Merge Join の前処理

【「遅いSQL」チューニングの5ステップ】
  1. EXPLAIN ANALYZE で実行計画を確認
  2. actual rows vs estimated rows の乖離をチェック
     → 大きな乖離 = 統計情報が古い → ANALYZE 実行
  3. Seq Scan を探す → インデックス追加を検討
  4. Nested Loop の loops が多い → Hash Join に変えられないか
  5. Sort がメモリ溢れていないか → work_mem 調整
"""


def generate_explain_examples():
    """EXPLAIN 出力の例を生成"""

    examples = [
        {
            "query": "SELECT * FROM orders WHERE id = 12345",
            "plan": [
                "Index Scan using orders_pkey on orders",
                "  (cost=0.43..8.45 rows=1 width=120)",
                "  (actual time=0.025..0.026 rows=1 loops=1)",
                "  Index Cond: (id = 12345)",
                "Planning Time: 0.085 ms",
                "Execution Time: 0.045 ms",
            ],
            "analysis": "PK による Index Scan → 最適。改善不要。",
        },
        {
            "query": "SELECT * FROM orders WHERE status = 'pending'",
            "plan": [
                "Seq Scan on orders  (cost=0.00..25000.00 rows=200000 width=120)",
                "  (actual time=0.015..180.523 rows=195000 loops=1)",
                "  Filter: (status = 'pending')",
                "  Rows Removed by Filter: 805000",
                "Planning Time: 0.100 ms",
                "Execution Time: 210.456 ms",
            ],
            "analysis": (
                "20% の行がヒット → Seq Scan は妥当。"
                "\nもし status が少量なら Partial Index を検討:"
                "\n  CREATE INDEX idx_pending ON orders(created_at) "
                "WHERE status = 'pending';"
            ),
        },
        {
            "query": (
                "SELECT o.*, c.name FROM orders o "
                "JOIN customers c ON o.customer_id = c.id "
                "WHERE o.created_at > '2024-01-01'"
            ),
            "plan": [
                "Hash Join  (cost=1500.00..35000.00 rows=50000 width=200)",
                "  (actual time=15.234..250.789 rows=48500 loops=1)",
                "  Hash Cond: (o.customer_id = c.id)",
                "  -> Bitmap Heap Scan on orders o",
                "       (cost=500.00..30000.00 rows=50000 width=120)",
                "     -> Bitmap Index Scan on idx_orders_created_at",
                "          (cost=0.00..487.50 rows=50000 width=0)",
                "          Index Cond: (created_at > '2024-01-01')",
                "  -> Hash  (cost=750.00..750.00 rows=50000 width=80)",
                "     -> Seq Scan on customers c",
                "          (cost=0.00..750.00 rows=50000 width=80)",
                "Planning Time: 0.500 ms",
                "Execution Time: 280.123 ms",
            ],
            "analysis": (
                "Bitmap Index Scan で日付フィルタ → Hash Join で結合。"
                "\n妥当な計画。改善するなら:"
                "\n  - orders に Covering Index: "
                "CREATE INDEX idx ON orders(created_at) INCLUDE (customer_id)"
                "\n  - customers が大きいなら、先にフィルタしてから Join"
            ),
        },
        {
            "query": (
                "SELECT customer_id, SUM(amount) FROM orders "
                "GROUP BY customer_id ORDER BY SUM(amount) DESC LIMIT 10"
            ),
            "plan": [
                "Limit  (cost=80000.00..80000.03 rows=10 width=40)",
                "  -> Sort  (cost=80000.00..80125.00 rows=50000 width=40)",
                "       Sort Key: (sum(amount)) DESC",
                "       Sort Method: top-N heapsort  Memory: 25kB",
                "       -> HashAggregate",
                "            (cost=70000.00..70500.00 rows=50000 width=40)",
                "            Group Key: customer_id",
                "            -> Seq Scan on orders",
                "                 (cost=0.00..25000.00 rows=1000000 width=16)",
                "Planning Time: 0.200 ms",
                "Execution Time: 1500.456 ms",
            ],
            "analysis": (
                "全件 Seq Scan → HashAggregate → Sort → Limit。"
                "\n100万行の Seq Scan が支配的。改善策:"
                "\n  1. Materialized View で集計結果をキャッシュ"
                "\n  2. BRIN Index (created_at と相関がある場合)"
                "\n  3. パーティショニングで対象行を削減"
            ),
        },
    ]
    return examples


def demo_explain_guide():
    """EXPLAIN 読解ガイドのデモ"""
    print("\n" + "=" * 70)
    print("8. EXPLAIN 読解ガイド")
    print("=" * 70)

    examples = generate_explain_examples()

    for i, ex in enumerate(examples, 1):
        print(f"\n--- 例{i}: {ex['query'][:60]}... ---")
        print()
        for line in ex["plan"]:
            print(f"  {line}")
        print(f"\n  📊 分析: {ex['analysis']}")

    print("\n" + "-" * 50)
    print("【遅い SQL チューニングの5ステップ】")
    print("  Step 1: EXPLAIN ANALYZE で実行計画を見る")
    print("  Step 2: estimated vs actual rows の乖離チェック")
    print("          → 乖離大 = ANALYZE でテーブル統計を更新")
    print("  Step 3: Seq Scan を探す → インデックス追加を検討")
    print("          → 取得行 < 5-10% なら Index Scan が有利")
    print("  Step 4: Nested Loop (loops 多) → Hash Join 検討")
    print("          → enable_nestloop = off で効果を確認")
    print("  Step 5: Sort が disk に溢れてないか確認")
    print("          → Sort Method: external merge → work_mem 増加")


# ============================================================================
# 9. Tier 1-4 優先度セクション
# ============================================================================
def show_priority_tiers():
    """学習優先度の表示"""
    print("\n" + "=" * 70)
    print("9. 学習優先度 (Tier 1-4)")
    print("=" * 70)

    tiers = {
        "Tier 1 (最優先 - 日常業務で毎日使う)": [
            "EXPLAIN ANALYZE の読み方と遅い SQL の特定",
            "インデックスの基礎 (B+ Tree, 作成/削除の判断)",
            "JOIN の種類と選択基準",
            "Connection Pool の設定と監視",
            "クエリライフサイクル (Parse → Plan → Execute)",
        ],
        "Tier 2 (重要 - 設計・障害対応で必要)": [
            "WAL & Recovery の仕組み",
            "MVCC と Vacuum / Autovacuum チューニング",
            "クエリプランナー (CBO) の仕組み",
            "統計情報 (ANALYZE) とカーディナリティ推定",
            "パーティショニング戦略 (Range / Hash / List)",
        ],
        "Tier 3 (応用 - アーキテクチャ選定で重要)": [
            "分散DB のレプリケーション戦略",
            "Consistent Hashing",
            "分散トランザクション (2PC / Saga)",
            "LSM-Tree と Compaction 戦略",
            "NewSQL (Spanner / CockroachDB / TiDB)",
        ],
        "Tier 4 (専門 - 深い知識として)": [
            "B+ Tree の分割/マージアルゴリズム",
            "ARIES Recovery の詳細",
            "Cost-Based Optimizer のコスト関数実装",
            "Index Only Scan の Visibility Map",
            "Cross-Partition Query の最適化",
        ],
    }

    for tier, items in tiers.items():
        print(f"\n  【{tier}】")
        for item in items:
            print(f"    - {item}")

    print("\n  推奨学習パス:")
    print("    Tier 1 (2-3週間) → Tier 2 (2-3週間) → Tier 3 (1ヶ月)")
    print("    → Tier 4 は必要に応じて深掘り")


# ============================================================================
# メイン実行
# ============================================================================
def main():
    """全セクションのデモを実行"""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║       Database Internals & Query Optimization Deep Dive           ║")
    print("║       データベース内部構造とクエリ最適化                             ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    demo_query_planner()
    demo_join_algorithms()
    demo_indexes()
    demo_wal_recovery()
    demo_vacuum_compaction()
    demo_connection_pool()
    demo_distributed_db()
    demo_explain_guide()
    show_priority_tiers()

    print("\n" + "=" * 70)
    print("全セクション完了!")
    print("=" * 70)


if __name__ == "__main__":
    main()
