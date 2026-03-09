"""
phase7_data/sql_nosql_deep_dive.py
===================================
SQL上級 & NoSQLデータモデリング 完全ガイド

なぜこれが重要か:
  FAANG / Big Tech のシニア面接では:
  - 「Window Functionで連続ログイン日数を求めよ」
  - 「DynamoDBのSingle Table Designを説明せよ」
  - 「RDB vs NoSQL をどう使い分けるか」
  が頻出。SQLを"書ける"だけでなく"なぜそう書くか"を説明できる必要がある。

実行方法:
  python sql_nosql_deep_dive.py
  (Python標準ライブラリのみ / sqlite3 使用)

考えてほしい疑問:
  Q1. Window Function と GROUP BY の違いは何か？
      → GROUP BY は行を集約する。Window Function は元の行を保持したまま集計値を付与する。
  Q2. なぜ DynamoDB は Single Table Design を推奨するのか？
      → JOINがないため、1回のクエリで必要なデータを全て取得する設計が必要。
  Q3. CAP定理で「3つ全ては取れない」とはどういう意味か？
      → ネットワーク分断(P)は避けられないので、実質CかAの選択になる。
  Q4. インデックスを貼りすぎると何が起きるか？
      → 書き込み性能が劣化し、ストレージも増える。SELECT最適化とのトレードオフ。
  Q5. 正規化と非正規化、どちらが「正しい」か？
      → ワークロード次第。OLTP→正規化、OLAP→非正規化(Star Schema)が基本。

[実装してみよう]:
  1. Window Functionで「部署別給与ランキング」を書いてみよう
  2. 再帰CTEで組織図ツリーを辿ってみよう
  3. DynamoDB Single Table Design をPythonで模擬してみよう
  4. Redisのキャッシュパターンを実装してみよう
  5. 連続ログイン日数を求めるSQLを書いてみよう
"""

from __future__ import annotations

import sqlite3
import time
import json
import random
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Optional

SEP = "━" * 60
SUB = "─" * 40


def print_header(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def print_sub(title: str) -> None:
    print(f"\n  {SUB}")
    print(f"  {title}")
    print(f"  {SUB}")


def run_query(conn: sqlite3.Connection, sql: str, params: tuple = (),
              label: str = "", show: bool = True) -> list:
    """SQLを実行し結果を表示するヘルパー"""
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    if show and label:
        print(f"\n  ▶ {label}")
        cols = [desc[0] for desc in cur.description] if cur.description else []
        if cols:
            header = " | ".join(f"{c:>15}" for c in cols)
            print(f"    {header}")
            print(f"    {'─' * len(header)}")
        for row in rows:
            print(f"    {' | '.join(f'{str(v):>15}' for v in row)}")
        if not rows:
            print("    (no rows)")
    return rows


# ============================================================
# Part 1: SQL上級テクニック (Advanced SQL with SQLite)
# ============================================================

def section_window_functions():
    """Window Functions: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, NTILE"""
    print_header("1-1. Window Functions — 行を保持したまま集計する")

    print("""
  Window Function の本質:
    GROUP BY → 行をまとめて1行にする（集約）
    Window   → 全行を保持したまま、各行に集計値を「窓」から付与する

  構文: function_name() OVER (
           PARTITION BY col     -- グループ分け（省略可）
           ORDER BY col         -- 順序（省略可）
           ROWS/RANGE BETWEEN   -- 窓の範囲（省略可）
        )

  主要関数:
    ROW_NUMBER() — 連番（同値でも異なる番号）
    RANK()       — 順位（同値は同順位、次はスキップ）
    DENSE_RANK() — 順位（同値は同順位、次はスキップしない）
    LAG(col, n)  — n行前の値
    LEAD(col, n) — n行後の値
    NTILE(n)     — n等分グループ番号
    SUM/AVG/COUNT() OVER(...) — ウィンドウ集計
    """)

    conn = sqlite3.connect(":memory:")

    # テストデータ: 社員テーブル
    conn.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary INTEGER,
            hire_date TEXT
        )
    """)
    employees = [
        (1, "Alice",   "Engineering", 120000, "2020-01-15"),
        (2, "Bob",     "Engineering", 110000, "2019-06-01"),
        (3, "Charlie", "Engineering", 120000, "2021-03-20"),
        (4, "Diana",   "Sales",       90000, "2020-07-10"),
        (5, "Eve",     "Sales",       95000, "2018-11-01"),
        (6, "Frank",   "Sales",       90000, "2021-01-15"),
        (7, "Grace",   "Marketing",   85000, "2020-02-28"),
        (8, "Hank",    "Marketing",  100000, "2019-08-15"),
        (9, "Ivy",     "Marketing",   85000, "2022-05-01"),
    ]
    conn.executemany(
        "INSERT INTO employees VALUES (?,?,?,?,?)", employees
    )

    # --- ROW_NUMBER, RANK, DENSE_RANK ---
    print_sub("ROW_NUMBER vs RANK vs DENSE_RANK")
    print("  同じ給与(tie)があるとき、番号の振り方が異なる:")
    run_query(conn, """
        SELECT name, department, salary,
            ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as row_num,
            RANK()       OVER (PARTITION BY department ORDER BY salary DESC) as rank_val,
            DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) as dense_rank_val
        FROM employees
        ORDER BY department, salary DESC
    """, label="部署別給与ランキング (ROW_NUMBER / RANK / DENSE_RANK)")

    print("""
  ポイント:
    Engineering: Alice(120k)とCharlie(120k)は同給与
      ROW_NUMBER → 1, 2 (一意の番号を振る)
      RANK       → 1, 1, 3 (同順位、次を3にスキップ)
      DENSE_RANK → 1, 1, 2 (同順位、次を2に)
    面接で「Top N per group」を求めるときは ROW_NUMBER が定番。
    """)

    # --- LAG / LEAD ---
    print_sub("LAG / LEAD — 前後の行の値を参照")
    run_query(conn, """
        SELECT name, department, salary,
            LAG(salary, 1)  OVER (PARTITION BY department ORDER BY hire_date) as prev_salary,
            LEAD(salary, 1) OVER (PARTITION BY department ORDER BY hire_date) as next_salary,
            salary - LAG(salary, 1) OVER (PARTITION BY department ORDER BY hire_date) as diff
        FROM employees
        ORDER BY department, hire_date
    """, label="部署内の入社順で前後の給与を比較")

    # --- NTILE ---
    print_sub("NTILE — N等分グループ分け")
    run_query(conn, """
        SELECT name, salary,
            NTILE(3) OVER (ORDER BY salary DESC) as salary_tier
        FROM employees
        ORDER BY salary DESC
    """, label="給与を3等分 (Tier 1=上位, Tier 3=下位)")

    # --- Running Total / Moving Average ---
    print_sub("Running Total & Moving Average")

    conn.execute("""
        CREATE TABLE daily_sales (
            sale_date TEXT, amount INTEGER
        )
    """)
    sales_data = []
    base = datetime(2024, 1, 1)
    random.seed(42)
    for i in range(20):
        d = (base + timedelta(days=i)).strftime("%Y-%m-%d")
        sales_data.append((d, random.randint(100, 500)))
    conn.executemany("INSERT INTO daily_sales VALUES (?,?)", sales_data)

    run_query(conn, """
        SELECT sale_date, amount,
            SUM(amount) OVER (ORDER BY sale_date
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total,
            ROUND(AVG(amount * 1.0) OVER (ORDER BY sale_date
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) as moving_avg_3day
        FROM daily_sales
        ORDER BY sale_date
        LIMIT 10
    """, label="累積売上 & 3日移動平均 (先頭10行)")

    print("""
  ウィンドウフレーム指定:
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW → 累積
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW         → 直近3行
    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING          → 前後1行ずつ
    """)

    conn.close()


def section_cte():
    """Common Table Expressions (CTE) — 再帰CTEでツリー構造"""
    print_header("1-2. CTE (Common Table Expressions) — 再帰でツリーを辿る")

    print("""
  CTEとは:
    WITH句で一時的な名前付き結果セットを定義する。
    サブクエリを何度も書く必要がなくなり、可読性が大幅に向上する。

  再帰CTE:
    ツリー構造（組織図、カテゴリ階層、ファイルシステム）の走査に使う。
    UNION ALL で「ベースケース」と「再帰ステップ」を結合する。
    """)

    conn = sqlite3.connect(":memory:")

    # 組織図テーブル
    conn.execute("""
        CREATE TABLE org_chart (
            id INTEGER PRIMARY KEY,
            name TEXT,
            manager_id INTEGER,
            title TEXT
        )
    """)
    org = [
        (1, "CEO太郎",     None, "CEO"),
        (2, "VP花子",      1,    "VP Engineering"),
        (3, "VP次郎",      1,    "VP Sales"),
        (4, "Dir美咲",     2,    "Director"),
        (5, "Dir健太",     2,    "Director"),
        (6, "Mgr陽子",    4,    "Manager"),
        (7, "Eng翔太",    6,    "Senior Engineer"),
        (8, "Eng愛",      6,    "Engineer"),
        (9, "Mgr拓也",    3,    "Manager"),
        (10, "Sales恵",   9,    "Sales Rep"),
    ]
    conn.executemany("INSERT INTO org_chart VALUES (?,?,?,?)", org)

    # 再帰CTEで部下を全て辿る
    print_sub("再帰CTE: CEO からの組織ツリー全展開")
    run_query(conn, """
        WITH RECURSIVE org_tree AS (
            -- ベースケース: CEOから開始
            SELECT id, name, title, manager_id, 0 as depth,
                   name as path
            FROM org_chart
            WHERE manager_id IS NULL

            UNION ALL

            -- 再帰ステップ: 部下を追加
            SELECT c.id, c.name, c.title, c.manager_id, t.depth + 1,
                   t.path || ' > ' || c.name
            FROM org_chart c
            JOIN org_tree t ON c.manager_id = t.id
        )
        SELECT depth,
               CASE WHEN depth = 0 THEN name
                    ELSE substr('            ', 1, depth * 2) || '└ ' || name
               END as org_display,
               title
        FROM org_tree
        ORDER BY path
    """, label="組織ツリー (再帰CTE)")

    # 特定の人の上司チェーンを辿る
    print_sub("再帰CTE: 特定の人 → CEO までの上司チェーン")
    run_query(conn, """
        WITH RECURSIVE chain AS (
            SELECT id, name, title, manager_id, 0 as level
            FROM org_chart WHERE name = 'Eng翔太'

            UNION ALL

            SELECT o.id, o.name, o.title, o.manager_id, c.level + 1
            FROM org_chart o
            JOIN chain c ON o.id = c.manager_id
        )
        SELECT level, name, title FROM chain
    """, label="Eng翔太 → CEO への報告チェーン")

    # 非再帰CTE: 複雑なクエリの整理
    print_sub("非再帰CTE: 部署別統計を整理")
    conn.execute("""
        CREATE TABLE sales_records (
            id INTEGER, rep_name TEXT, region TEXT, amount REAL, quarter TEXT
        )
    """)
    recs = [
        (1, "A", "East", 1000, "Q1"), (2, "A", "East", 1500, "Q2"),
        (3, "B", "West", 2000, "Q1"), (4, "B", "West", 1800, "Q2"),
        (5, "C", "East", 900,  "Q1"), (6, "C", "East", 1100, "Q2"),
    ]
    conn.executemany("INSERT INTO sales_records VALUES (?,?,?,?,?)", recs)

    run_query(conn, """
        WITH quarterly_totals AS (
            SELECT region, quarter, SUM(amount) as total
            FROM sales_records GROUP BY region, quarter
        ),
        region_avg AS (
            SELECT region, AVG(total) as avg_total
            FROM quarterly_totals GROUP BY region
        )
        SELECT q.region, q.quarter, q.total,
               ROUND(r.avg_total, 0) as region_avg,
               CASE WHEN q.total > r.avg_total THEN 'Above' ELSE 'Below' END as vs_avg
        FROM quarterly_totals q
        JOIN region_avg r ON q.region = r.region
        ORDER BY q.region, q.quarter
    """, label="CTEで段階的に集計 (四半期別 vs 地域平均)")

    conn.close()


def section_subquery_vs_join():
    """Subquery vs JOIN のパフォーマンス比較"""
    print_header("1-3. Subquery vs JOIN — パフォーマンスと可読性")

    print("""
  原則:
    - 相関サブクエリ (Correlated Subquery) は外側の各行に対して実行される → 遅い
    - JOIN は一度だけ結合処理を行う → 一般的に速い
    - ただし、オプティマイザが変換する場合もある

  使い分け:
    EXISTS    → 存在チェックに最適（早期終了できる）
    IN        → 小さなリストに対して
    JOIN      → 結合して複数カラムが必要なとき
    相関サブクエリ → 避けられるなら避ける
    """)

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL)")
    conn.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, region TEXT)")

    random.seed(123)
    for i in range(1, 101):
        conn.execute("INSERT INTO customers VALUES (?,?,?)",
                     (i, f"Customer_{i}", random.choice(["East", "West", "North"])))
    for i in range(1, 1001):
        conn.execute("INSERT INTO orders VALUES (?,?,?)",
                     (i, random.randint(1, 100), round(random.uniform(10, 500), 2)))

    # 相関サブクエリ vs JOIN
    print_sub("相関サブクエリ vs JOIN")

    t1 = time.perf_counter()
    run_query(conn, """
        SELECT c.name, c.region,
            (SELECT SUM(o.total) FROM orders o WHERE o.customer_id = c.id) as order_total
        FROM customers c
        WHERE c.region = 'East'
        ORDER BY order_total DESC
        LIMIT 5
    """, label="相関サブクエリ版 (各行でサブクエリ実行)")
    t2 = time.perf_counter()
    print(f"    Time: {(t2-t1)*1000:.2f}ms")

    t1 = time.perf_counter()
    run_query(conn, """
        SELECT c.name, c.region, SUM(o.total) as order_total
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        WHERE c.region = 'East'
        GROUP BY c.id, c.name, c.region
        ORDER BY order_total DESC
        LIMIT 5
    """, label="JOIN + GROUP BY 版 (推奨)")
    t2 = time.perf_counter()
    print(f"    Time: {(t2-t1)*1000:.2f}ms")

    # EXISTS vs IN
    print_sub("EXISTS vs IN")
    run_query(conn, """
        SELECT name FROM customers c
        WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id AND o.total > 400)
        LIMIT 5
    """, label="EXISTS: 高額注文がある顧客 (先頭5名)")

    conn.close()


def section_explain_plan():
    """EXPLAIN QUERY PLAN の読み方"""
    print_header("1-4. EXPLAIN QUERY PLAN — クエリ実行計画を読む")

    print("""
  SQLite の EXPLAIN QUERY PLAN:
    - SCAN TABLE    → フルテーブルスキャン（遅い）
    - SEARCH TABLE  → インデックス使用（速い）
    - USE TEMP B-TREE → ソートに一時B-Tree使用
    - COVERING INDEX → インデックスだけで完結（最速）

  PostgreSQL の場合は EXPLAIN ANALYZE で実行時間も見れる。
    """)

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE big_table (id INTEGER PRIMARY KEY, category TEXT, value REAL, status TEXT)")
    random.seed(42)
    data = [(i, f"cat_{i%20}", random.uniform(1, 1000), random.choice(["active", "inactive"]))
            for i in range(10000)]
    conn.executemany("INSERT INTO big_table VALUES (?,?,?,?)", data)

    print_sub("インデックスなしの実行計画")
    rows = run_query(conn, "EXPLAIN QUERY PLAN SELECT * FROM big_table WHERE category = 'cat_5'",
                     label="Without index")
    print("  → SCAN TABLE = フルスキャン。全行を走査する。")

    conn.execute("CREATE INDEX idx_category ON big_table(category)")
    print_sub("インデックスありの実行計画")
    run_query(conn, "EXPLAIN QUERY PLAN SELECT * FROM big_table WHERE category = 'cat_5'",
              label="With index on category")
    print("  → SEARCH TABLE USING INDEX = インデックスで絞り込み。高速。")

    # カバリングインデックス
    conn.execute("CREATE INDEX idx_covering ON big_table(category, value)")
    print_sub("カバリングインデックス")
    run_query(conn, "EXPLAIN QUERY PLAN SELECT category, value FROM big_table WHERE category = 'cat_5'",
              label="Covering index (category, value)")
    print("  → COVERING INDEX: テーブルへのアクセス不要。インデックスだけで結果を返す。")

    conn.close()


def section_index_strategy():
    """インデックス戦略: B-Tree, 複合インデックス, パフォーマンス比較"""
    print_header("1-5. インデックス戦略 — B-Tree と複合インデックス")

    print("""
  B-Tree インデックスの仕組み:
    ┌─────────────────────────┐
    │       Root Node         │ ← ルート
    │   [10 | 20 | 30]       │
    └──┬──────┬──────┬───────┘
       ▼      ▼      ▼
    [1-9]  [11-19] [21-29]  [31-...]  ← リーフ（実データへのポインタ）

    検索: O(log N)    フルスキャン: O(N)

  複合インデックスの順序が重要:
    INDEX(a, b, c) は以下のクエリに有効:
      WHERE a = ?            ✅ 先頭カラムを使用
      WHERE a = ? AND b = ?  ✅ 左から順に使用
      WHERE a = ? AND b = ? AND c = ?  ✅ 全カラム使用
      WHERE b = ?            ❌ 先頭カラムがない
      WHERE a = ? AND c = ?  △ aのみインデックス使用

    → 「最も選択性の高いカラムを先頭に」が基本戦略
    """)

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE access_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            action TEXT,
            created_at TEXT,
            ip_address TEXT
        )
    """)

    random.seed(42)
    actions = ["login", "view", "click", "purchase", "logout"]
    base_date = datetime(2024, 1, 1)
    data = []
    for i in range(50000):
        uid = random.randint(1, 1000)
        act = random.choice(actions)
        dt = (base_date + timedelta(seconds=random.randint(0, 86400 * 30))).isoformat()
        ip = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
        data.append((i, uid, act, dt, ip))
    conn.executemany("INSERT INTO access_log VALUES (?,?,?,?,?)", data)

    query = "SELECT * FROM access_log WHERE user_id = 42 AND action = 'purchase'"

    # No index
    print_sub("パフォーマンス比較: インデックスなし vs あり")
    t1 = time.perf_counter()
    for _ in range(100):
        conn.execute(query).fetchall()
    t2 = time.perf_counter()
    no_idx = (t2 - t1) * 1000
    print(f"  No index:       {no_idx:.1f}ms (100回実行)")

    # Single index
    conn.execute("CREATE INDEX idx_user ON access_log(user_id)")
    t1 = time.perf_counter()
    for _ in range(100):
        conn.execute(query).fetchall()
    t2 = time.perf_counter()
    single_idx = (t2 - t1) * 1000
    print(f"  Single index:   {single_idx:.1f}ms (100回実行)")

    # Composite index
    conn.execute("CREATE INDEX idx_user_action ON access_log(user_id, action)")
    t1 = time.perf_counter()
    for _ in range(100):
        conn.execute(query).fetchall()
    t2 = time.perf_counter()
    composite_idx = (t2 - t1) * 1000
    print(f"  Composite index: {composite_idx:.1f}ms (100回実行)")

    speedup = no_idx / composite_idx if composite_idx > 0 else float('inf')
    print(f"\n  → 複合インデックスで約 {speedup:.1f}x 高速化")

    conn.close()


def section_upsert_and_transactions():
    """UPSERT, トランザクション分離レベル"""
    print_header("1-6. UPSERT & トランザクション")

    print("""
  UPSERT (INSERT OR REPLACE / ON CONFLICT):
    「なければ挿入、あれば更新」を1文で実現する。
    PostgreSQL: INSERT ... ON CONFLICT DO UPDATE
    MySQL:      INSERT ... ON DUPLICATE KEY UPDATE
    SQLite:     INSERT OR REPLACE / INSERT ... ON CONFLICT

  トランザクション分離レベル (低→高):
    ┌─────────────────┬──────────┬─────────────┬───────────┐
    │ Level           │Dirty Read│Non-Repeatable│Phantom    │
    ├─────────────────┼──────────┼─────────────┼───────────┤
    │READ UNCOMMITTED │ ○ 発生   │ ○ 発生      │ ○ 発生    │
    │READ COMMITTED   │ × 防止   │ ○ 発生      │ ○ 発生    │
    │REPEATABLE READ  │ × 防止   │ × 防止      │ ○ 発生    │
    │SERIALIZABLE     │ × 防止   │ × 防止      │ × 防止    │
    └─────────────────┴──────────┴─────────────┴───────────┘

    Dirty Read: 未コミットのデータを読める
    Non-Repeatable Read: 同じクエリで結果が変わる
    Phantom Read: 同じ範囲クエリで行数が変わる

    PostgreSQL デフォルト: READ COMMITTED
    MySQL InnoDB デフォルト: REPEATABLE READ
    SQLite: SERIALIZABLE (最も厳密)
    """)

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE user_stats (
            user_id INTEGER PRIMARY KEY,
            login_count INTEGER DEFAULT 0,
            last_login TEXT
        )
    """)

    # INSERT OR REPLACE
    print_sub("UPSERT: INSERT OR REPLACE")
    conn.execute("INSERT OR REPLACE INTO user_stats VALUES (1, 1, '2024-01-01')")
    run_query(conn, "SELECT * FROM user_stats", label="初回挿入")

    conn.execute("INSERT OR REPLACE INTO user_stats VALUES (1, 2, '2024-01-02')")
    run_query(conn, "SELECT * FROM user_stats", label="UPSERT: 同じPKで更新")

    # ON CONFLICT (SQLite 3.24+)
    print_sub("UPSERT: ON CONFLICT DO UPDATE")
    conn.execute("""
        INSERT INTO user_stats (user_id, login_count, last_login)
        VALUES (1, 1, '2024-01-03')
        ON CONFLICT(user_id) DO UPDATE SET
            login_count = login_count + 1,
            last_login = excluded.last_login
    """)
    run_query(conn, "SELECT * FROM user_stats",
              label="ON CONFLICT: login_count をインクリメント")

    # Pivot simulation
    print_sub("Pivot シミュレーション")
    conn.execute("""
        CREATE TABLE quarterly_sales (
            product TEXT, quarter TEXT, revenue REAL
        )
    """)
    pivot_data = [
        ("Widget", "Q1", 100), ("Widget", "Q2", 150),
        ("Widget", "Q3", 200), ("Widget", "Q4", 180),
        ("Gadget", "Q1", 80),  ("Gadget", "Q2", 120),
        ("Gadget", "Q3", 160), ("Gadget", "Q4", 140),
    ]
    conn.executemany("INSERT INTO quarterly_sales VALUES (?,?,?)", pivot_data)

    run_query(conn, """
        SELECT product,
            SUM(CASE WHEN quarter='Q1' THEN revenue END) as Q1,
            SUM(CASE WHEN quarter='Q2' THEN revenue END) as Q2,
            SUM(CASE WHEN quarter='Q3' THEN revenue END) as Q3,
            SUM(CASE WHEN quarter='Q4' THEN revenue END) as Q4,
            SUM(revenue) as total
        FROM quarterly_sales
        GROUP BY product
    """, label="PIVOT: 行→列変換 (CASE WHEN)")

    conn.close()


# ============================================================
# Part 2: NoSQL データモデリング (Python シミュレーション)
# ============================================================

class DynamoDBSimulator:
    """
    DynamoDB Single Table Design シミュレーター

    DynamoDB の設計原則:
      1. アクセスパターンを先に定義する
      2. 1つのテーブルに複数エンティティを格納 (Single Table Design)
      3. PK (Partition Key) + SK (Sort Key) で柔軟にクエリ
      4. GSI (Global Secondary Index) で逆引きパターンに対応

    なぜ Single Table Design か:
      - DynamoDB は JOIN がない
      - 1回のクエリで関連データを全て取得する必要がある
      - BatchGetItem でも効率的に取得可能
    """

    def __init__(self):
        self.table: list[dict] = []
        self.gsi: dict[str, list[dict]] = defaultdict(list)

    def put_item(self, item: dict) -> None:
        # PK + SK でユニーク
        self.table = [
            r for r in self.table
            if not (r["PK"] == item["PK"] and r["SK"] == item["SK"])
        ]
        self.table.append(item)
        # GSI 更新
        for gsi_name, items in self.gsi.items():
            gsi_pk = f"GSI1PK"
            gsi_sk = f"GSI1SK"
            if gsi_pk in item and gsi_sk in item:
                self.gsi[gsi_name] = [
                    r for r in self.gsi[gsi_name]
                    if not (r.get(gsi_pk) == item[gsi_pk] and r.get(gsi_sk) == item[gsi_sk])
                ]
                self.gsi[gsi_name].append(item)

    def query(self, pk: str, sk_prefix: str = None) -> list[dict]:
        """Partition Key でクエリ（Sort Key のプレフィックス検索も可能）"""
        results = [r for r in self.table if r["PK"] == pk]
        if sk_prefix:
            results = [r for r in results if r["SK"].startswith(sk_prefix)]
        return sorted(results, key=lambda x: x["SK"])

    def query_gsi(self, gsi_pk_value: str, gsi_sk_prefix: str = None) -> list[dict]:
        """GSI でクエリ"""
        results = [r for r in self.table if r.get("GSI1PK") == gsi_pk_value]
        if gsi_sk_prefix:
            results = [r for r in results if r.get("GSI1SK", "").startswith(gsi_sk_prefix)]
        return sorted(results, key=lambda x: x.get("GSI1SK", ""))

    def scan(self, filter_fn=None) -> list[dict]:
        if filter_fn:
            return [r for r in self.table if filter_fn(r)]
        return list(self.table)


def section_dynamodb_modeling():
    """DynamoDB Single Table Design のシミュレーション"""
    print_header("2-1. DynamoDB — Single Table Design")

    print("""
  DynamoDB Single Table Design:
    Eコマースの例で、以下のエンティティを1テーブルに格納:
      - Customer (顧客)
      - Order (注文)
      - OrderItem (注文明細)

  アクセスパターン:
    1. 顧客情報を取得              → PK=CUSTOMER#id, SK=PROFILE
    2. 顧客の全注文を取得          → PK=CUSTOMER#id, SK begins_with ORDER#
    3. 特定注文の明細を取得        → PK=ORDER#id, SK begins_with ITEM#
    4. 日付範囲で注文を検索        → GSI1: PK=STATUS#shipped, SK=date

  PK/SK 設計:
    ┌────────────────────┬──────────────────┬──────────────┐
    │ PK                 │ SK               │ Entity       │
    ├────────────────────┼──────────────────┼──────────────┤
    │ CUSTOMER#123       │ PROFILE          │ Customer     │
    │ CUSTOMER#123       │ ORDER#2024-01-01#001 │ Order    │
    │ ORDER#001          │ ITEM#1           │ OrderItem    │
    │ ORDER#001          │ ITEM#2           │ OrderItem    │
    └────────────────────┴──────────────────┴──────────────┘
    """)

    db = DynamoDBSimulator()

    # データ投入
    customers = [
        {"PK": "CUSTOMER#C001", "SK": "PROFILE", "type": "Customer",
         "name": "Alice", "email": "alice@example.com", "tier": "Premium"},
        {"PK": "CUSTOMER#C002", "SK": "PROFILE", "type": "Customer",
         "name": "Bob", "email": "bob@example.com", "tier": "Standard"},
    ]
    orders = [
        {"PK": "CUSTOMER#C001", "SK": "ORDER#2024-01-15#O001", "type": "Order",
         "order_id": "O001", "total": 250.00, "status": "shipped",
         "GSI1PK": "STATUS#shipped", "GSI1SK": "2024-01-15"},
        {"PK": "CUSTOMER#C001", "SK": "ORDER#2024-02-20#O002", "type": "Order",
         "order_id": "O002", "total": 89.99, "status": "delivered",
         "GSI1PK": "STATUS#delivered", "GSI1SK": "2024-02-20"},
        {"PK": "CUSTOMER#C002", "SK": "ORDER#2024-01-20#O003", "type": "Order",
         "order_id": "O003", "total": 175.50, "status": "shipped",
         "GSI1PK": "STATUS#shipped", "GSI1SK": "2024-01-20"},
    ]
    order_items = [
        {"PK": "ORDER#O001", "SK": "ITEM#1", "type": "OrderItem",
         "product": "Widget A", "quantity": 2, "price": 100.00},
        {"PK": "ORDER#O001", "SK": "ITEM#2", "type": "OrderItem",
         "product": "Widget B", "quantity": 1, "price": 50.00},
        {"PK": "ORDER#O003", "SK": "ITEM#1", "type": "OrderItem",
         "product": "Gadget C", "quantity": 3, "price": 58.50},
    ]

    for item in customers + orders + order_items:
        db.put_item(item)

    # クエリ実行
    print_sub("アクセスパターン 1: 顧客情報取得")
    results = db.query("CUSTOMER#C001", "PROFILE")
    for r in results:
        print(f"    {r['name']} ({r['email']}) - Tier: {r['tier']}")

    print_sub("アクセスパターン 2: 顧客の全注文取得")
    results = db.query("CUSTOMER#C001", "ORDER#")
    for r in results:
        print(f"    Order {r['order_id']}: ${r['total']} ({r['status']})")

    print_sub("アクセスパターン 3: 注文の明細取得")
    results = db.query("ORDER#O001", "ITEM#")
    for r in results:
        print(f"    {r['product']} x{r['quantity']} @ ${r['price']}")

    print_sub("アクセスパターン 4: GSI — ステータスで検索")
    results = db.query_gsi("STATUS#shipped")
    for r in results:
        print(f"    Order {r['order_id']}: ${r['total']} (shipped on {r.get('GSI1SK')})")

    print("""
  DynamoDB Streams のユースケース:
    - 注文ステータス変更時に通知を送信
    - データ変更をElasticsearchに同期
    - 集計テーブルの非同期更新
    - イベント駆動アーキテクチャの起点
    """)


def section_mongodb_patterns():
    """MongoDB-style ドキュメントモデル（dictで実装）"""
    print_header("2-2. MongoDB パターン — Embedding vs Referencing")

    print("""
  MongoDB データモデリングの2大パターン:

  1. Embedding (埋め込み):
     { user: "Alice", addresses: [{city: "Tokyo"}, {city: "Osaka"}] }
     → 1回のreadで全データ取得。更新が複雑になる場合がある。

  2. Referencing (参照):
     { user: "Alice", address_ids: ["addr_1", "addr_2"] }
     → 正規化に近い。$lookup (JOIN) が必要。

  判断基準:
    ┌───────────────┬─────────────┬──────────────┐
    │               │ Embedding   │ Referencing  │
    ├───────────────┼─────────────┼──────────────┤
    │ 読み込み      │ ◎ 1回で取得 │ △ 複数回     │
    │ 書き込み      │ △ 更新が複雑│ ◎ 独立更新   │
    │ データサイズ  │ △ 16MB制限  │ ◎ 制限なし   │
    │ 1:少 の関係   │ ◎ 向いている│ △ 過剰       │
    │ N:M の関係    │ ✕ 不向き    │ ◎ 向いている │
    └───────────────┴─────────────┴──────────────┘
    """)

    # MongoDB-like Collection Simulator
    class MongoCollection:
        def __init__(self):
            self.docs: list[dict] = []
            self._id_counter = 0

        def insert(self, doc: dict) -> str:
            self._id_counter += 1
            doc["_id"] = f"doc_{self._id_counter}"
            self.docs.append(doc)
            return doc["_id"]

        def find(self, query: dict) -> list[dict]:
            results = []
            for doc in self.docs:
                match = True
                for k, v in query.items():
                    if isinstance(v, dict):
                        # 演算子サポート: $gt, $lt, $in, $regex
                        for op, val in v.items():
                            if op == "$gt" and not doc.get(k, 0) > val:
                                match = False
                            elif op == "$lt" and not doc.get(k, 0) < val:
                                match = False
                            elif op == "$in" and doc.get(k) not in val:
                                match = False
                            elif op == "$exists" and (k in doc) != val:
                                match = False
                    elif doc.get(k) != v:
                        match = False
                if match:
                    results.append(doc)
            return results

        def aggregate(self, pipeline: list[dict]) -> list[dict]:
            """Aggregation Pipeline シミュレーション"""
            data = list(self.docs)
            for stage in pipeline:
                if "$match" in stage:
                    query = stage["$match"]
                    data = [d for d in data if all(
                        (d.get(k) == v if not isinstance(v, dict) else
                         all(self._eval_op(d.get(k), op, val) for op, val in v.items()))
                        for k, v in query.items()
                    )]
                elif "$group" in stage:
                    group_spec = stage["$group"]
                    group_key = group_spec["_id"]
                    groups: dict[Any, list] = defaultdict(list)
                    for d in data:
                        key = d.get(group_key.lstrip("$")) if isinstance(group_key, str) else "all"
                        groups[key].append(d)
                    result = []
                    for key, items in groups.items():
                        row = {"_id": key}
                        for field, op_spec in group_spec.items():
                            if field == "_id":
                                continue
                            if isinstance(op_spec, dict):
                                for op, col in op_spec.items():
                                    col_name = col.lstrip("$")
                                    vals = [i.get(col_name, 0) for i in items]
                                    if op == "$sum":
                                        row[field] = sum(vals)
                                    elif op == "$avg":
                                        row[field] = sum(vals) / len(vals) if vals else 0
                                    elif op == "$count":
                                        row[field] = len(items)
                                    elif op == "$max":
                                        row[field] = max(vals)
                                    elif op == "$min":
                                        row[field] = min(vals)
                        result.append(row)
                    data = result
                elif "$sort" in stage:
                    sort_spec = stage["$sort"]
                    for field, direction in reversed(list(sort_spec.items())):
                        data.sort(key=lambda x: x.get(field, 0),
                                  reverse=(direction == -1))
                elif "$limit" in stage:
                    data = data[:stage["$limit"]]
                elif "$unwind" in stage:
                    field = stage["$unwind"].lstrip("$")
                    unwound = []
                    for d in data:
                        arr = d.get(field, [])
                        if isinstance(arr, list):
                            for item in arr:
                                new_doc = dict(d)
                                new_doc[field] = item
                                unwound.append(new_doc)
                        else:
                            unwound.append(d)
                    data = unwound
            return data

        @staticmethod
        def _eval_op(val, op, target):
            if op == "$gt":
                return val is not None and val > target
            if op == "$lt":
                return val is not None and val < target
            if op == "$gte":
                return val is not None and val >= target
            if op == "$in":
                return val in target
            return True

    # Embedding パターン
    print_sub("Embedding パターン: ブログ記事 + コメント")
    posts = MongoCollection()
    posts.insert({
        "title": "DynamoDB設計入門",
        "author": "Alice",
        "tags": ["database", "aws", "nosql"],
        "views": 1500,
        "comments": [
            {"user": "Bob", "text": "とても参考になりました", "likes": 10},
            {"user": "Charlie", "text": "Single Table Design難しい", "likes": 5},
        ]
    })
    posts.insert({
        "title": "Redis キャッシュ戦略",
        "author": "Alice",
        "tags": ["database", "cache", "redis"],
        "views": 2300,
        "comments": [
            {"user": "Diana", "text": "Cache-Aside分かりやすい", "likes": 8},
        ]
    })
    posts.insert({
        "title": "GraphQL vs REST",
        "author": "Bob",
        "tags": ["api", "graphql"],
        "views": 800,
        "comments": []
    })

    result = posts.find({"author": "Alice"})
    for doc in result:
        print(f"    {doc['title']} (views: {doc['views']}, comments: {len(doc['comments'])})")

    # Aggregation Pipeline
    print_sub("Aggregation Pipeline: 著者別統計")
    pipeline_result = posts.aggregate([
        {"$group": {
            "_id": "$author",
            "total_views": {"$sum": "$views"},
            "post_count": {"$count": "$_id"},
            "avg_views": {"$avg": "$views"},
        }},
        {"$sort": {"total_views": -1}},
    ])
    for r in pipeline_result:
        print(f"    Author: {r['_id']}, Posts: {r['post_count']}, "
              f"Total Views: {r['total_views']}, Avg: {r['avg_views']:.0f}")

    # $unwind + $group
    print_sub("$unwind: タグ別集計")
    tag_stats = posts.aggregate([
        {"$unwind": "$tags"},
        {"$group": {
            "_id": "$tags",
            "count": {"$count": "$_id"},
            "total_views": {"$sum": "$views"},
        }},
        {"$sort": {"total_views": -1}},
    ])
    for r in tag_stats:
        print(f"    Tag: {r['_id']:>10}, Count: {r['count']}, Views: {r['total_views']}")


def section_redis_patterns():
    """Redis パターン（dictでシミュレーション）"""
    print_header("2-3. Redis パターン — キャッシュ・ランキング・Pub/Sub")

    class RedisSimulator:
        """Redis をPython dictでシミュレーション"""
        def __init__(self):
            self.store: dict[str, Any] = {}
            self.expiry: dict[str, float] = {}
            self.sorted_sets: dict[str, dict[str, float]] = defaultdict(dict)
            self.subscribers: dict[str, list] = defaultdict(list)
            self.locks: dict[str, str] = {}

        def set(self, key: str, value: str, ex: int = None) -> bool:
            self.store[key] = value
            if ex:
                self.expiry[key] = time.time() + ex
            return True

        def get(self, key: str) -> Optional[str]:
            if key in self.expiry and time.time() > self.expiry[key]:
                del self.store[key]
                del self.expiry[key]
                return None
            return self.store.get(key)

        def delete(self, key: str) -> bool:
            return self.store.pop(key, None) is not None

        def setnx(self, key: str, value: str, ex: int = 30) -> bool:
            """SET if Not eXists — 分散ロックの基礎"""
            if key not in self.store:
                self.set(key, value, ex=ex)
                return True
            return False

        def zadd(self, key: str, member: str, score: float) -> None:
            """Sorted Set に追加"""
            self.sorted_sets[key][member] = score

        def zincrby(self, key: str, member: str, increment: float) -> float:
            self.sorted_sets[key][member] = self.sorted_sets[key].get(member, 0) + increment
            return self.sorted_sets[key][member]

        def zrevrange(self, key: str, start: int, stop: int) -> list[tuple[str, float]]:
            """スコア降順で取得"""
            items = sorted(self.sorted_sets.get(key, {}).items(),
                           key=lambda x: x[1], reverse=True)
            return items[start:stop + 1]

        def zrank(self, key: str, member: str) -> Optional[int]:
            items = sorted(self.sorted_sets.get(key, {}).items(),
                           key=lambda x: x[1], reverse=True)
            for i, (m, _) in enumerate(items):
                if m == member:
                    return i
            return None

        def subscribe(self, channel: str, callback) -> None:
            self.subscribers[channel].append(callback)

        def publish(self, channel: str, message: str) -> int:
            for cb in self.subscribers.get(channel, []):
                cb(channel, message)
            return len(self.subscribers.get(channel, []))

    redis = RedisSimulator()

    # --- Cache-Aside パターン ---
    print_sub("Cache-Aside パターン")
    print("""
  Cache-Aside (Lazy Loading):
    1. アプリがキャッシュを確認
    2. ヒット → キャッシュから返す
    3. ミス → DBから取得 → キャッシュに保存 → 返す

    メリット: 読まれたデータのみキャッシュ
    デメリット: 初回は必ずミス(cold start)
    """)

    fake_db = {"user:1": '{"name":"Alice","age":30}', "user:2": '{"name":"Bob","age":25}'}

    def get_user(user_id: str) -> dict:
        cache_key = f"user:{user_id}"
        cached = redis.get(cache_key)
        if cached:
            print(f"    Cache HIT: {cache_key}")
            return json.loads(cached)
        print(f"    Cache MISS: {cache_key} → DB lookup")
        data = fake_db.get(cache_key, '{}')
        redis.set(cache_key, data, ex=3600)
        return json.loads(data)

    print("  1回目 (Cold):")
    get_user("1")
    print("  2回目 (Warm):")
    get_user("1")

    # --- Write-Through パターン ---
    print_sub("Write-Through パターン")
    print("""
  Write-Through:
    1. アプリがキャッシュとDBに同時に書き込み
    2. キャッシュが常に最新状態

    メリット: キャッシュが常に一貫
    デメリット: 書き込みレイテンシ増加
    """)

    def update_user_write_through(user_id: str, data: dict) -> None:
        cache_key = f"user:{user_id}"
        json_data = json.dumps(data)
        fake_db[cache_key] = json_data
        redis.set(cache_key, json_data, ex=3600)
        print(f"    Write-Through: DB + Cache updated for {cache_key}")

    update_user_write_through("1", {"name": "Alice", "age": 31})
    result = get_user("1")
    print(f"    Result after write-through: {result}")

    # --- Sorted Set でランキング ---
    print_sub("Sorted Set — リアルタイムランキング")
    players = [
        ("Alice", 1500), ("Bob", 2300), ("Charlie", 1800),
        ("Diana", 2100), ("Eve", 1900), ("Frank", 2500),
    ]
    for name, score in players:
        redis.zadd("leaderboard", name, score)

    # スコア更新
    redis.zincrby("leaderboard", "Alice", 500)  # Alice +500
    redis.zincrby("leaderboard", "Charlie", 800)  # Charlie +800

    top = redis.zrevrange("leaderboard", 0, 4)
    print("  Top 5 ランキング:")
    for i, (name, score) in enumerate(top, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
        print(f"    {medal} #{i} {name}: {score:.0f}")

    rank = redis.zrank("leaderboard", "Alice")
    print(f"\n    Alice の順位: #{rank + 1}" if rank is not None else "    Not found")

    # --- Pub/Sub ---
    print_sub("Pub/Sub パターン")
    received_messages = []

    def on_notification(channel, msg):
        received_messages.append(f"[{channel}] {msg}")

    def on_alert(channel, msg):
        received_messages.append(f"[ALERT:{channel}] {msg}")

    redis.subscribe("order_events", on_notification)
    redis.subscribe("order_events", on_alert)

    redis.publish("order_events", "Order O001 shipped")
    redis.publish("order_events", "Order O002 delivered")

    for msg in received_messages:
        print(f"    {msg}")

    # --- 分散ロック ---
    print_sub("分散ロック (SETNX)")
    print("""
  分散ロック:
    複数プロセスが同じリソースに同時アクセスするのを防ぐ。
    Redis の SETNX (SET if Not eXists) + TTL で実現。

    lock_key = "lock:resource_id"
    1. SETNX lock_key owner_id EX 30  → True: ロック取得
    2. (処理実行)
    3. DEL lock_key                    → ロック解放

    注意: Redlock アルゴリズム (複数Redisノード) が推奨
    """)

    lock_key = "lock:inventory:item_42"
    acquired = redis.setnx(lock_key, "worker_A", ex=30)
    print(f"    Worker A lock: {'acquired' if acquired else 'failed'}")

    acquired2 = redis.setnx(lock_key, "worker_B", ex=30)
    print(f"    Worker B lock: {'acquired' if acquired2 else 'BLOCKED (lock held by A)'}")

    redis.delete(lock_key)
    acquired3 = redis.setnx(lock_key, "worker_B", ex=30)
    print(f"    Worker B retry: {'acquired' if acquired3 else 'failed'}")


def section_graph_db():
    """Graph DB パターン — BFS/DFS でソーシャルグラフ探索"""
    print_header("2-4. Graph DB パターン — ソーシャルグラフ探索")

    print("""
  グラフDBの2つの実装方式:

  1. 隣接リスト (Adjacency List) — RDBでも実現可能
     edges テーブル: (from_id, to_id, relationship)
     → JOINの連鎖が必要で、深い探索は遅い

  2. ネイティブグラフ (Neo4j等) — インデックスフリー隣接
     各ノードが直接隣接ノードへのポインタを持つ
     → O(1) でトラバース。深い探索に強い

  ユースケース:
    - ソーシャルグラフ (友達の友達)
    - レコメンデーション (共通の購買)
    - 不正検知 (不審な送金パターン)
    - ナレッジグラフ
    """)

    class SocialGraph:
        def __init__(self):
            self.nodes: dict[str, dict] = {}
            self.edges: dict[str, list[tuple[str, str]]] = defaultdict(list)

        def add_user(self, user_id: str, name: str, **attrs) -> None:
            self.nodes[user_id] = {"name": name, **attrs}

        def add_edge(self, from_id: str, to_id: str, rel: str = "FOLLOWS") -> None:
            self.edges[from_id].append((to_id, rel))

        def bfs(self, start: str, max_depth: int = 3) -> dict[str, int]:
            """BFS: 幅優先探索 — 最短距離を求める"""
            visited = {start: 0}
            queue = deque([(start, 0)])
            while queue:
                node, depth = queue.popleft()
                if depth >= max_depth:
                    continue
                for neighbor, _ in self.edges.get(node, []):
                    if neighbor not in visited:
                        visited[neighbor] = depth + 1
                        queue.append((neighbor, depth + 1))
            return visited

        def dfs(self, start: str, target: str, visited: set = None) -> list[str]:
            """DFS: 深さ優先探索 — パスを見つける"""
            if visited is None:
                visited = set()
            visited.add(start)
            if start == target:
                return [start]
            for neighbor, _ in self.edges.get(start, []):
                if neighbor not in visited:
                    path = self.dfs(neighbor, target, visited)
                    if path:
                        return [start] + path
            return []

        def friends_of_friends(self, user_id: str) -> list[tuple[str, int]]:
            """2ホップ以内のユーザー(友達の友達)"""
            distances = self.bfs(user_id, max_depth=2)
            fof = [(uid, d) for uid, d in distances.items()
                   if uid != user_id and d == 2]
            return fof

        def mutual_friends(self, user_a: str, user_b: str) -> list[str]:
            """共通の友達"""
            friends_a = {n for n, _ in self.edges.get(user_a, [])}
            friends_b = {n for n, _ in self.edges.get(user_b, [])}
            return list(friends_a & friends_b)

    graph = SocialGraph()
    users = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace"]
    for u in users:
        graph.add_user(u, u.capitalize())

    edges = [
        ("alice", "bob"), ("alice", "charlie"), ("alice", "diana"),
        ("bob", "charlie"), ("bob", "eve"),
        ("charlie", "diana"), ("charlie", "frank"),
        ("diana", "grace"),
        ("eve", "frank"),
        ("frank", "grace"),
    ]
    for a, b in edges:
        graph.add_edge(a, b, "FOLLOWS")
        graph.add_edge(b, a, "FOLLOWS")

    print_sub("BFS: Alice からの距離")
    distances = graph.bfs("alice", max_depth=3)
    for uid, depth in sorted(distances.items(), key=lambda x: x[1]):
        name = graph.nodes[uid]["name"]
        print(f"    Distance {depth}: {name}")

    print_sub("DFS: Alice → Grace のパス")
    path = graph.dfs("alice", "grace")
    print(f"    Path: {' → '.join(p.capitalize() for p in path)}")

    print_sub("Friends of Friends (2ホップ)")
    fof = graph.friends_of_friends("alice")
    for uid, d in fof:
        print(f"    {graph.nodes[uid]['name']} (distance: {d})")

    print_sub("共通の友達: Alice & Eve")
    mutual = graph.mutual_friends("alice", "eve")
    print(f"    Mutual friends: {[m.capitalize() for m in mutual]}")


# ============================================================
# Part 3: DB選択の意思決定フレームワーク
# ============================================================

def section_db_selection():
    """DB選択の意思決定フレームワーク"""
    print_header("3. DB選択の意思決定フレームワーク")

    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ACID vs BASE
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ACID (RDB):
    Atomicity    — トランザクションは全か無
    Consistency  — 制約が常に満たされる
    Isolation    — 同時実行でも独立
    Durability   — コミット後は永続

  BASE (NoSQL):
    Basically Available — 基本的に利用可能
    Soft state          — 状態は時間と共に変化しうる
    Eventually consistent — 最終的に一貫性が保たれる

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CAP定理
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  分散システムは以下の3つを同時に満たせない:
    C (Consistency)   — 全ノードが同じデータを返す
    A (Availability)  — 全リクエストにレスポンスを返す
    P (Partition tolerance) — ネットワーク分断に耐える

  現実: P は避けられない → C か A の選択
    CP: MongoDB, HBase, Redis Cluster
       → 分断時にエラーを返してでも一貫性を保つ
    AP: DynamoDB, Cassandra, CouchDB
       → 分断時に古いデータを返してでも可用性を保つ
    CA: 単一ノードRDB (PostgreSQL単体)
       → 分散していないので P は不要

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DB使い分け一覧
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌──────────────┬──────────────┬───────────────┬──────────────────────┐
  │ DB           │ タイプ       │ 得意          │ ユースケース         │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ PostgreSQL   │ RDB          │ 複雑なクエリ  │ 一般的なWebアプリ    │
  │              │              │ ACID保証      │ 金融・会計           │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ DynamoDB     │ Key-Value    │ 水平スケール  │ ゲーム・IoT          │
  │              │              │ 低レイテンシ  │ セッション管理       │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ MongoDB      │ Document     │ 柔軟スキーマ  │ CMS・カタログ        │
  │              │              │ 開発速度      │ プロトタイプ         │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ Redis        │ In-Memory    │ 超低レイテンシ│ キャッシュ           │
  │              │              │ データ構造豊富│ ランキング・セッション│
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ Elasticsearch│ 検索エンジン │ 全文検索      │ ログ分析             │
  │              │              │ 集計          │ Eコマース検索        │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ Neo4j        │ Graph        │ 関係の探索    │ SNS・不正検知        │
  │              │              │ パス検索      │ レコメンデーション   │
  ├──────────────┼──────────────┼───────────────┼──────────────────────┤
  │ TimescaleDB  │ 時系列       │ 時系列集計    │ IoTセンサー          │
  │              │              │ データ圧縮    │ メトリクス監視       │
  └──────────────┴──────────────┴───────────────┴──────────────────────┘

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  面接回答テンプレート: 「なぜDynamoDBを選んだか」
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STAR フレームワーク:
    Situation: 「ゲームのセッション管理で、ピーク時に数万RPS、
                レイテンシ要件が single-digit ms だった」
    Task:      「RDB (Aurora) では水平スケールが難しく、
                コネクションプールも枯渇していた」
    Action:    「アクセスパターンを洗い出し、Single Table Design を採用。
                GSI でステータス検索もカバー。
                DAX (DynamoDB Accelerator) でホットキー対策」
    Result:    「p99 レイテンシが 50ms → 3ms に改善。
                Auto Scaling で運用負荷も大幅削減」

  ポイント:
    - 「なぜ他のDBではダメだったか」を明確にする
    - トレードオフ (JOINがない、Scan が遅い) も言及する
    - 具体的な数字 (RPS, レイテンシ, コスト) を含める
    """)


# ============================================================
# Part 4: データモデリング実践
# ============================================================

def section_normalization():
    """正規化 (1NF→3NF→BCNF) の実例"""
    print_header("4-1. 正規化 — 1NF → 3NF → BCNF")

    print("""
  正規化の目的: データの冗長性を排除し、更新異常を防ぐ

  非正規化テーブル (問題あり):
    ┌────┬────────┬──────────┬───────────┬───────────────┐
    │ ID │ 学生名 │ 科目     │ 教授      │ 教授の部署    │
    ├────┼────────┼──────────┼───────────┼───────────────┤
    │ 1  │ 太郎   │ DB,AI    │ 田中,鈴木 │ CS,CS         │
    │ 2  │ 花子   │ DB       │ 田中      │ CS            │
    └────┴────────┴──────────┴───────────┴───────────────┘
    問題: 1つのセルに複数値 → 1NFに違反

  ━━━━ 1NF: 各セルはアトミック（原子的）━━━━
    → 科目ごとに行を分ける

  ━━━━ 2NF: 部分関数従属の排除 ━━━━
    → 複合キー(学生ID, 科目)に対して、学生名は学生IDだけに依存
    → 学生テーブルと受講テーブルに分割

  ━━━━ 3NF: 推移的関数従属の排除 ━━━━
    → 教授 → 部署 は科目に直接依存しない（推移的）
    → 教授テーブルを別に分割

  ━━━━ BCNF: 全ての決定子が候補キー ━━━━
    → 3NFより厳密。稀なケースで差が出る。
    """)

    conn = sqlite3.connect(":memory:")

    # 3NF のテーブル構造
    conn.executescript("""
        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE professors (
            professor_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL
        );
        CREATE TABLE courses (
            course_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            professor_id INTEGER REFERENCES professors
        );
        CREATE TABLE enrollments (
            student_id INTEGER REFERENCES students,
            course_id TEXT REFERENCES courses,
            grade TEXT,
            PRIMARY KEY (student_id, course_id)
        );

        INSERT INTO students VALUES (1, '太郎'), (2, '花子'), (3, '次郎');
        INSERT INTO professors VALUES (1, '田中', 'CS'), (2, '鈴木', 'CS'), (3, '山田', 'Math');
        INSERT INTO courses VALUES ('CS101', 'データベース', 1), ('CS201', 'AI入門', 2), ('MATH101', '線形代数', 3);
        INSERT INTO enrollments VALUES (1, 'CS101', 'A'), (1, 'CS201', 'B'),
                                       (2, 'CS101', 'A'), (3, 'MATH101', 'C');
    """)

    run_query(conn, """
        SELECT s.name as student, c.title as course, p.name as professor,
               p.department, e.grade
        FROM enrollments e
        JOIN students s ON e.student_id = s.student_id
        JOIN courses c ON e.course_id = c.course_id
        JOIN professors p ON c.professor_id = p.professor_id
        ORDER BY s.name
    """, label="3NF: 正規化されたJOINクエリ")

    conn.close()


def section_ecommerce_model():
    """Eコマースの注文データモデル設計"""
    print_header("4-2. Eコマース注文データモデル")

    print("""
  要件:
    - ユーザーが商品を注文
    - 1注文に複数の商品
    - 在庫管理
    - 注文ステータス追跡
    - 配送先住所

  テーブル設計 (3NF):
    users → addresses → orders → order_items → products
                                                 ↑
                                              inventory
    """)

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY, username TEXT, email TEXT, created_at TEXT
        );
        CREATE TABLE addresses (
            id INTEGER PRIMARY KEY, user_id INTEGER,
            street TEXT, city TEXT, country TEXT, is_default INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY, name TEXT, price REAL, category TEXT
        );
        CREATE TABLE inventory (
            product_id INTEGER PRIMARY KEY, quantity INTEGER, reserved INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY, user_id INTEGER, address_id INTEGER,
            status TEXT DEFAULT 'pending', total REAL, created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (address_id) REFERENCES addresses(id)
        );
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
            quantity INTEGER, unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        CREATE TABLE order_status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER,
            status TEXT, changed_at TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        INSERT INTO users VALUES (1,'alice','alice@ex.com','2024-01-01'),
                                 (2,'bob','bob@ex.com','2024-01-15');
        INSERT INTO addresses VALUES (1,1,'123 Main St','Tokyo','JP',1),
                                     (2,2,'456 Oak Ave','Osaka','JP',1);
        INSERT INTO products VALUES (1,'Laptop',999.99,'Electronics'),
                                    (2,'Mouse',29.99,'Electronics'),
                                    (3,'Book',19.99,'Books'),
                                    (4,'Headphones',149.99,'Electronics');
        INSERT INTO inventory VALUES (1,50,0),(2,200,0),(3,100,0),(4,75,0);
        INSERT INTO orders VALUES (1,1,1,'shipped',1059.97,'2024-02-01'),
                                  (2,1,1,'delivered',19.99,'2024-02-15'),
                                  (3,2,2,'pending',179.98,'2024-03-01');
        INSERT INTO order_items VALUES (1,1,1,1,999.99),(2,1,2,2,29.99),
                                       (3,2,3,1,19.99),(4,3,2,1,29.99),
                                       (5,3,4,1,149.99);
        INSERT INTO order_status_history VALUES (NULL,1,'pending','2024-02-01'),
            (NULL,1,'confirmed','2024-02-01'),(NULL,1,'shipped','2024-02-02'),
            (NULL,2,'pending','2024-02-15'),(NULL,2,'shipped','2024-02-16'),
            (NULL,2,'delivered','2024-02-18'),
            (NULL,3,'pending','2024-03-01');
    """)

    run_query(conn, """
        SELECT u.username, o.id as order_id, o.status, o.total,
               COUNT(oi.id) as items, o.created_at
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id
        ORDER BY o.created_at
    """, label="注文一覧")

    run_query(conn, """
        SELECT o.id as order_id, p.name, oi.quantity, oi.unit_price,
               oi.quantity * oi.unit_price as subtotal
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.id = 1
    """, label="注文 #1 の明細")

    # 非正規化: よくある読み込みパフォーマンス最適化
    print("""
  非正規化のトレードオフ:
    正規化状態: 注文サマリを表示するのに5テーブルJOIN
    非正規化案: orders テーブルに item_count, product_names を持たせる

    メリット: JOINなしで高速表示
    デメリット: 商品名変更時に orders も更新が必要（不整合リスク）

    判断基準:
      読み込み >> 書き込み → 非正規化を検討
      書き込み頻度が高い    → 正規化を維持
      マテリアライズドビュー → 中間的な解決策
    """)

    conn.close()


def section_social_feed():
    """ソーシャルメディアのフィード設計"""
    print_header("4-3. ソーシャルメディア フィード設計")

    print("""
  フィード配信の2大アプローチ:

  1. Pull モデル (Fan-out on read):
     ┌──────┐  read   ┌──────────────┐
     │ User │ ──────→ │ 全フォロー先  │ ← 読み込み時に集約
     └──────┘         │ の投稿をJOIN │
                      └──────────────┘
     メリット: 書き込みが軽い
     デメリット: フォロー数が多いと読み込みが遅い

  2. Push モデル (Fan-out on write):
     ┌──────┐  write  ┌──────────────┐
     │ User │ ──────→ │ 全フォロワー  │ ← 書き込み時に配信
     └──────┘  post   │ のフィードに  │
                      │ コピー       │
                      └──────────────┘
     メリット: 読み込みが超高速 (自分のフィードを読むだけ)
     デメリット: フォロワーが多い人の投稿が重い (セレブ問題)

  Twitter/X の解決策: ハイブリッド
    - 通常ユーザー → Push (fan-out on write)
    - セレブ (100万+ followers) → Pull (fan-out on read)
    """)

    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT);
        CREATE TABLE follows (follower_id INTEGER, following_id INTEGER,
                              PRIMARY KEY (follower_id, following_id));
        CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER,
                           content TEXT, created_at TEXT);
        CREATE TABLE feed_cache (user_id INTEGER, post_id INTEGER,
                                 created_at TEXT,
                                 PRIMARY KEY (user_id, post_id));

        INSERT INTO users VALUES (1,'alice'),(2,'bob'),(3,'charlie'),
                                 (4,'diana'),(5,'eve');
        INSERT INTO follows VALUES (1,2),(1,3),(2,1),(2,3),(3,4),(4,5),(5,1);

        INSERT INTO posts VALUES
            (1,1,'Alice: Hello world!','2024-03-01 10:00'),
            (2,2,'Bob: Learning SQL','2024-03-01 11:00'),
            (3,3,'Charlie: NoSQL rocks','2024-03-01 12:00'),
            (4,1,'Alice: Window functions are cool','2024-03-02 09:00'),
            (5,2,'Bob: CTE is powerful','2024-03-02 10:00'),
            (6,4,'Diana: Graph DB ftw','2024-03-02 11:00');
    """)

    # Pull モデル
    print_sub("Pull モデル: Alice のフィード (フォロー先の投稿をJOIN)")
    run_query(conn, """
        SELECT u.username, p.content, p.created_at
        FROM posts p
        JOIN follows f ON f.following_id = p.user_id
        JOIN users u ON p.user_id = u.id
        WHERE f.follower_id = 1
        ORDER BY p.created_at DESC
        LIMIT 5
    """, label="Alice のフィード (Pull)")

    # Push モデル: フィードキャッシュ作成
    conn.execute("""
        INSERT OR IGNORE INTO feed_cache (user_id, post_id, created_at)
        SELECT f.follower_id, p.id, p.created_at
        FROM posts p
        JOIN follows f ON f.following_id = p.user_id
    """)

    print_sub("Push モデル: Alice のフィード (feed_cache から直接取得)")
    run_query(conn, """
        SELECT u.username, p.content, fc.created_at
        FROM feed_cache fc
        JOIN posts p ON fc.post_id = p.id
        JOIN users u ON p.user_id = u.id
        WHERE fc.user_id = 1
        ORDER BY fc.created_at DESC
        LIMIT 5
    """, label="Alice のフィード (Push / cached)")

    conn.close()


def section_timeseries():
    """時系列データのモデリング"""
    print_header("4-4. 時系列データモデリング")

    print("""
  時系列データの特徴:
    - 書き込みが圧倒的に多い (append-only)
    - 時間範囲での読み取りが中心
    - 古いデータの集約・アーカイブが必要

  設計パターン:
    1. ワイドテーブル: timestamp, metric_name, value
    2. バケット化: 1時間/1日分をまとめて1行に
    3. ダウンサンプリング: 古いデータは1時間/1日平均に集約

  時系列DB:
    TimescaleDB — PostgreSQL拡張。SQLで使える
    InfluxDB    — 専用DB。高速書き込み
    Prometheus  — メトリクス監視特化
    """)

    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE sensor_data (
            sensor_id TEXT,
            recorded_at TEXT,
            temperature REAL,
            humidity REAL
        )
    """)
    conn.execute("CREATE INDEX idx_sensor_time ON sensor_data(sensor_id, recorded_at)")

    random.seed(42)
    base = datetime(2024, 1, 1)
    data = []
    for sensor in ["sensor_A", "sensor_B"]:
        temp_base = 20.0 if sensor == "sensor_A" else 25.0
        for i in range(720):  # 30 days x 24 hours
            ts = (base + timedelta(hours=i)).strftime("%Y-%m-%d %H:00:00")
            temp = temp_base + 5 * (0.5 + 0.5 * random.gauss(0, 1))
            hum = 50 + 20 * random.gauss(0, 1)
            data.append((sensor, ts, round(temp, 1), round(hum, 1)))
    conn.executemany("INSERT INTO sensor_data VALUES (?,?,?,?)", data)

    # 日次集約 (ダウンサンプリング)
    print_sub("日次集約 (ダウンサンプリング)")
    run_query(conn, """
        SELECT sensor_id,
               substr(recorded_at, 1, 10) as date,
               ROUND(AVG(temperature), 1) as avg_temp,
               ROUND(MIN(temperature), 1) as min_temp,
               ROUND(MAX(temperature), 1) as max_temp,
               COUNT(*) as readings
        FROM sensor_data
        WHERE sensor_id = 'sensor_A'
        GROUP BY sensor_id, substr(recorded_at, 1, 10)
        LIMIT 7
    """, label="Sensor A の日次統計 (先頭7日)")

    # 移動平均
    print_sub("時間帯別パターン分析")
    run_query(conn, """
        SELECT sensor_id,
               CAST(substr(recorded_at, 12, 2) AS INTEGER) as hour,
               ROUND(AVG(temperature), 1) as avg_temp
        FROM sensor_data
        GROUP BY sensor_id, hour
        HAVING hour IN (0, 6, 12, 18)
        ORDER BY sensor_id, hour
    """, label="時間帯別平均気温 (0時, 6時, 12時, 18時)")

    conn.close()


# ============================================================
# Part 5: 面接で問われるSQLクエリ
# ============================================================

def section_interview_sql():
    """面接頻出のSQLクエリ問題"""
    print_header("5. 面接で問われるSQLクエリ")

    conn = sqlite3.connect(":memory:")

    # ===== 問題1: 連続ログイン日数 (Streak) =====
    print_sub("問題1: 連続ログイン日数 (Login Streak)")
    print("""
  問題: ユーザーの最大連続ログイン日数を求めよ
  テクニック: date - ROW_NUMBER() でグループ化

  アイデア:
    日付から連番を引くと、連続日なら同じ値になる
    2024-01-01 - 1 = 2024-01-00  ┐
    2024-01-02 - 2 = 2024-01-00  ├ 同じグループ = 連続3日
    2024-01-03 - 3 = 2024-01-00  ┘
    2024-01-05 - 4 = 2024-01-01  ┐ 別グループ
    2024-01-06 - 5 = 2024-01-01  ┘
    """)

    conn.execute("""
        CREATE TABLE logins (user_id INTEGER, login_date TEXT)
    """)
    login_data = [
        (1, "2024-01-01"), (1, "2024-01-02"), (1, "2024-01-03"),
        (1, "2024-01-05"), (1, "2024-01-06"),
        (1, "2024-01-10"), (1, "2024-01-11"), (1, "2024-01-12"), (1, "2024-01-13"),
        (2, "2024-01-01"), (2, "2024-01-03"), (2, "2024-01-04"), (2, "2024-01-05"),
    ]
    conn.executemany("INSERT INTO logins VALUES (?,?)", login_data)

    run_query(conn, """
        WITH numbered AS (
            SELECT user_id, login_date,
                DATE(login_date, '-' || ROW_NUMBER() OVER (
                    PARTITION BY user_id ORDER BY login_date
                ) || ' days') as grp
            FROM (SELECT DISTINCT user_id, login_date FROM logins)
        ),
        streaks AS (
            SELECT user_id, grp,
                   MIN(login_date) as streak_start,
                   MAX(login_date) as streak_end,
                   COUNT(*) as streak_days
            FROM numbered
            GROUP BY user_id, grp
        )
        SELECT user_id, streak_start, streak_end, streak_days
        FROM streaks
        ORDER BY user_id, streak_start
    """, label="全ストリーク一覧")

    run_query(conn, """
        WITH numbered AS (
            SELECT user_id, login_date,
                DATE(login_date, '-' || ROW_NUMBER() OVER (
                    PARTITION BY user_id ORDER BY login_date
                ) || ' days') as grp
            FROM (SELECT DISTINCT user_id, login_date FROM logins)
        )
        SELECT user_id, MAX(cnt) as max_streak
        FROM (
            SELECT user_id, grp, COUNT(*) as cnt
            FROM numbered GROUP BY user_id, grp
        )
        GROUP BY user_id
    """, label="ユーザー別最大連続ログイン日数")

    # ===== 問題2: 中央値の計算 =====
    print_sub("問題2: 中央値 (Median)")
    print("  SQLには標準のMEDIAN関数がない → Window Functionで求める")

    conn.execute("CREATE TABLE salaries (dept TEXT, salary INTEGER)")
    sal_data = [
        ("Eng", 100), ("Eng", 120), ("Eng", 110), ("Eng", 150), ("Eng", 130),
        ("Sales", 80), ("Sales", 90), ("Sales", 85), ("Sales", 95),
    ]
    conn.executemany("INSERT INTO salaries VALUES (?,?)", sal_data)

    run_query(conn, """
        WITH ranked AS (
            SELECT dept, salary,
                ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary) as rn,
                COUNT(*) OVER (PARTITION BY dept) as cnt
            FROM salaries
        )
        SELECT dept,
               AVG(salary) as median_salary
        FROM ranked
        WHERE rn IN (cnt / 2, cnt / 2 + 1)
           OR (cnt % 2 = 1 AND rn = (cnt + 1) / 2)
        GROUP BY dept
    """, label="部署別中央値")

    # ===== 問題3: 累積分布 =====
    print_sub("問題3: 累積分布 (Percentile)")
    run_query(conn, """
        SELECT dept, salary,
            ROUND(PERCENT_RANK() OVER (PARTITION BY dept ORDER BY salary) * 100, 1)
                as percentile,
            ROUND(CUME_DIST() OVER (PARTITION BY dept ORDER BY salary) * 100, 1)
                as cume_dist_pct
        FROM salaries
        ORDER BY dept, salary
    """, label="部署別パーセンタイル & 累積分布")

    # ===== 問題4: セッション分析 =====
    print_sub("問題4: セッション分析 (Session Detection)")
    print("  30分以上間隔があいたら新しいセッションとみなす")

    conn.execute("""
        CREATE TABLE page_views (
            user_id INTEGER, url TEXT, viewed_at TEXT
        )
    """)
    views = [
        (1, "/home",    "2024-01-01 10:00:00"),
        (1, "/product", "2024-01-01 10:05:00"),
        (1, "/cart",    "2024-01-01 10:12:00"),
        (1, "/home",    "2024-01-01 14:00:00"),
        (1, "/search",  "2024-01-01 14:10:00"),
        (2, "/home",    "2024-01-01 09:00:00"),
        (2, "/product", "2024-01-01 09:20:00"),
    ]
    conn.executemany("INSERT INTO page_views VALUES (?,?,?)", views)

    run_query(conn, """
        WITH time_diffs AS (
            SELECT user_id, url, viewed_at,
                LAG(viewed_at) OVER (PARTITION BY user_id ORDER BY viewed_at) as prev_time,
                CASE
                    WHEN (julianday(viewed_at) - julianday(
                        LAG(viewed_at) OVER (PARTITION BY user_id ORDER BY viewed_at)
                    )) * 24 * 60 > 30
                    OR LAG(viewed_at) OVER (PARTITION BY user_id ORDER BY viewed_at) IS NULL
                    THEN 1
                    ELSE 0
                END as new_session
            FROM page_views
        ),
        sessions AS (
            SELECT *,
                SUM(new_session) OVER (PARTITION BY user_id
                    ORDER BY viewed_at ROWS UNBOUNDED PRECEDING) as session_id
            FROM time_diffs
        )
        SELECT user_id, session_id, url, viewed_at
        FROM sessions
        ORDER BY user_id, viewed_at
    """, label="セッション検出結果")

    # ===== 問題5: コホート分析 =====
    print_sub("問題5: コホート分析 (Cohort Retention)")
    print("  月ごとのユーザー登録コホートの維持率を求める")

    conn.execute("CREATE TABLE user_activity (user_id INTEGER, activity_date TEXT)")
    conn.execute("CREATE TABLE user_signups (user_id INTEGER, signup_date TEXT)")

    signup_data = [(i, f"2024-0{(i % 3) + 1}-01") for i in range(1, 31)]
    conn.executemany("INSERT INTO user_signups VALUES (?,?)", signup_data)

    random.seed(42)
    activity_data = []
    for uid in range(1, 31):
        month_start = (uid % 3) + 1
        for m in range(month_start, 7):
            if random.random() < (0.9 - 0.15 * (m - month_start)):
                activity_data.append((uid, f"2024-0{m}-15"))
    conn.executemany("INSERT INTO user_activity VALUES (?,?)", activity_data)

    run_query(conn, """
        WITH cohorts AS (
            SELECT s.user_id,
                   substr(s.signup_date, 1, 7) as cohort_month,
                   substr(a.activity_date, 1, 7) as activity_month
            FROM user_signups s
            JOIN user_activity a ON s.user_id = a.user_id
        ),
        retention AS (
            SELECT cohort_month, activity_month,
                   COUNT(DISTINCT user_id) as active_users,
                   CAST(
                       (CAST(substr(activity_month,6,2) AS INT) -
                        CAST(substr(cohort_month,6,2) AS INT)) AS INT
                   ) as months_since_signup
            FROM cohorts
            GROUP BY cohort_month, activity_month
        )
        SELECT cohort_month,
               months_since_signup,
               active_users,
               ROUND(active_users * 100.0 / MAX(active_users) OVER (
                   PARTITION BY cohort_month
               ), 1) as retention_pct
        FROM retention
        WHERE months_since_signup >= 0
        ORDER BY cohort_month, months_since_signup
    """, label="コホートリテンション分析")

    # ===== 問題6: ファネル分析 =====
    print_sub("問題6: ファネル分析 (Conversion Funnel)")

    conn.execute("""
        CREATE TABLE events (
            user_id INTEGER, event_type TEXT, event_time TEXT
        )
    """)
    funnel_data = [
        # ユーザー1: 全ステップ完了
        (1, "page_view", "2024-01-01 10:00"), (1, "add_to_cart", "2024-01-01 10:05"),
        (1, "checkout", "2024-01-01 10:10"), (1, "purchase", "2024-01-01 10:15"),
        # ユーザー2: カートまで
        (2, "page_view", "2024-01-01 11:00"), (2, "add_to_cart", "2024-01-01 11:05"),
        # ユーザー3: 全完了
        (3, "page_view", "2024-01-01 12:00"), (3, "add_to_cart", "2024-01-01 12:05"),
        (3, "checkout", "2024-01-01 12:10"), (3, "purchase", "2024-01-01 12:15"),
        # ユーザー4: ページビューのみ
        (4, "page_view", "2024-01-01 13:00"),
        # ユーザー5: チェックアウトまで
        (5, "page_view", "2024-01-01 14:00"), (5, "add_to_cart", "2024-01-01 14:05"),
        (5, "checkout", "2024-01-01 14:10"),
        # ユーザー6: 全完了
        (6, "page_view", "2024-01-02 10:00"), (6, "add_to_cart", "2024-01-02 10:05"),
        (6, "checkout", "2024-01-02 10:10"), (6, "purchase", "2024-01-02 10:20"),
    ]
    conn.executemany("INSERT INTO events VALUES (?,?,?)", funnel_data)

    run_query(conn, """
        WITH funnel AS (
            SELECT
                COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN user_id END) as step1_view,
                COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN user_id END) as step2_cart,
                COUNT(DISTINCT CASE WHEN event_type = 'checkout' THEN user_id END) as step3_checkout,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) as step4_purchase
            FROM events
        )
        SELECT
            step1_view as "1_PageView",
            step2_cart as "2_AddToCart",
            ROUND(step2_cart * 100.0 / step1_view, 1) as "Cart%",
            step3_checkout as "3_Checkout",
            ROUND(step3_checkout * 100.0 / step1_view, 1) as "Checkout%",
            step4_purchase as "4_Purchase",
            ROUND(step4_purchase * 100.0 / step1_view, 1) as "Purchase%"
        FROM funnel
    """, label="コンバージョンファネル")

    run_query(conn, """
        WITH step_users AS (
            SELECT user_id,
                   MAX(CASE WHEN event_type = 'page_view' THEN 1 ELSE 0 END) as viewed,
                   MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) as carted,
                   MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) as checked_out,
                   MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchased
            FROM events GROUP BY user_id
        )
        SELECT
            CASE
                WHEN purchased = 1 THEN 'Completed Purchase'
                WHEN checked_out = 1 THEN 'Dropped at Checkout'
                WHEN carted = 1 THEN 'Dropped at Cart'
                WHEN viewed = 1 THEN 'Dropped at View'
            END as drop_off_point,
            COUNT(*) as user_count
        FROM step_users
        GROUP BY drop_off_point
        ORDER BY user_count DESC
    """, label="ドロップオフ分析 (どこで離脱したか)")

    conn.close()


# ============================================================
# Part 6 (Bonus): RDB vs NoSQL 判断 シミュレーション
# ============================================================

def section_decision_simulator():
    """DB選択の意思決定シミュレーション"""
    print_header("Bonus: DB選択シミュレーター")

    requirements = [
        {
            "scenario": "Eコマースの注文管理",
            "needs_acid": True, "complex_queries": True,
            "high_write_throughput": False, "flexible_schema": False,
            "graph_relations": False, "caching_needed": True,
            "recommendation": "PostgreSQL + Redis",
            "reason": "ACID保証が必要な注文処理 + 商品ページのキャッシュ"
        },
        {
            "scenario": "IoTセンサーデータ収集",
            "needs_acid": False, "complex_queries": False,
            "high_write_throughput": True, "flexible_schema": True,
            "graph_relations": False, "caching_needed": False,
            "recommendation": "DynamoDB or TimescaleDB",
            "reason": "大量書き込みに対応。時系列クエリが中心"
        },
        {
            "scenario": "ソーシャルネットワーク",
            "needs_acid": False, "complex_queries": True,
            "high_write_throughput": True, "flexible_schema": True,
            "graph_relations": True, "caching_needed": True,
            "recommendation": "PostgreSQL + Neo4j + Redis",
            "reason": "ユーザーデータはRDB、フレンド関係はGraph、フィードはRedis"
        },
        {
            "scenario": "リアルタイムゲームランキング",
            "needs_acid": False, "complex_queries": False,
            "high_write_throughput": True, "flexible_schema": False,
            "graph_relations": False, "caching_needed": True,
            "recommendation": "Redis (Sorted Set)",
            "reason": "超低レイテンシでスコア更新・ランキング取得"
        },
        {
            "scenario": "CMS / ブログプラットフォーム",
            "needs_acid": False, "complex_queries": False,
            "high_write_throughput": False, "flexible_schema": True,
            "graph_relations": False, "caching_needed": False,
            "recommendation": "MongoDB",
            "reason": "記事の構造が多様。柔軟なスキーマが開発速度を上げる"
        },
    ]

    for req in requirements:
        print(f"\n  ■ シナリオ: {req['scenario']}")
        flags = []
        if req["needs_acid"]:
            flags.append("ACID必要")
        if req["complex_queries"]:
            flags.append("複雑クエリ")
        if req["high_write_throughput"]:
            flags.append("高書き込み")
        if req["flexible_schema"]:
            flags.append("柔軟スキーマ")
        if req["graph_relations"]:
            flags.append("グラフ関係")
        if req["caching_needed"]:
            flags.append("キャッシュ要")
        print(f"    要件: {', '.join(flags)}")
        print(f"    推奨: {req['recommendation']}")
        print(f"    理由: {req['reason']}")

    print("""
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  判断フローチャート:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ACID必要？ ─Yes─→ PostgreSQL / MySQL
      │
      No
      │
  複雑な関係性？ ─Yes─→ Neo4j (Graph)
      │
      No
      │
  超低レイテンシ？ ─Yes─→ Redis (In-Memory)
      │
      No
      │
  大量書き込み＆予測可能なクエリ？ ─Yes─→ DynamoDB / Cassandra
      │
      No
      │
  柔軟なスキーマ？ ─Yes─→ MongoDB
      │
      No
      │
  全文検索？ ─Yes─→ Elasticsearch
      │
      No
      │
  → とりあえず PostgreSQL (万能)
    """)


# ============================================================
# メイン実行
# ============================================================

def main():
    print("=" * 60)
    print("  SQL/NoSQL Deep Dive — FAANG面接対策 完全ガイド")
    print("=" * 60)

    # Part 1: SQL上級
    section_window_functions()
    section_cte()
    section_subquery_vs_join()
    section_explain_plan()
    section_index_strategy()
    section_upsert_and_transactions()

    # Part 2: NoSQL
    section_dynamodb_modeling()
    section_mongodb_patterns()
    section_redis_patterns()
    section_graph_db()

    # Part 3: 意思決定
    section_db_selection()

    # Part 4: データモデリング実践
    section_normalization()
    section_ecommerce_model()
    section_social_feed()
    section_timeseries()

    # Part 5: 面接SQL
    section_interview_sql()

    # Bonus
    section_decision_simulator()

    print(f"\n{SEP}")
    print("  完了！全セクション実行成功")
    print(SEP)
    print("""
  次のステップ:
    1. Window Function を自分の手で書き換えてみよう
    2. DynamoDB のアクセスパターンを自分のプロジェクトで設計してみよう
    3. LeetCode Database 問題を解いてみよう
    4. 「なぜこのDBを選んだか」を STAR フレームワークで答える練習
    """)


if __name__ == "__main__":
    main()
