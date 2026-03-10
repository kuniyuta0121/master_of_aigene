#!/usr/bin/env python3
"""
Performance Engineering — CPU/メモリ/DB/システムレベルの最適化

FAANG Staff+ に必要なパフォーマンスエンジニアリング:
ボトルネック特定 → 計測 → 最適化 → 検証のサイクル

実行: python performance_engineering.py
依存: Python 3.9+ 標準ライブラリのみ
"""

import array
import hashlib
import math
import random
import struct
import sys
import time
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Chapter 1: CPU & Memory Performance
# ============================================================

def chapter1_cpu_memory():
    print("=" * 70)
    print("Chapter 1: CPU & Memory Performance")
    print("  キャッシュ・メモリレイアウト — ハードウェアを味方にする")
    print("=" * 70)

    # --- 1.1 Cache-Friendly Access ---
    print("\n" + "─" * 60)
    print("1.1 キャッシュフレンドリーなアクセスパターン")
    print("─" * 60)

    SIZE = 1000

    # Row-major (cache-friendly)
    matrix = [[random.random() for _ in range(SIZE)] for _ in range(SIZE)]

    start = time.perf_counter_ns()
    total = 0.0
    for i in range(SIZE):
        for j in range(SIZE):
            total += matrix[i][j]  # row-major: sequential access
    row_major_ns = time.perf_counter_ns() - start

    # Column-major (cache-unfriendly)
    start = time.perf_counter_ns()
    total = 0.0
    for j in range(SIZE):
        for i in range(SIZE):
            total += matrix[i][j]  # column-major: strided access
    col_major_ns = time.perf_counter_ns() - start

    print(f"\n  {SIZE}×{SIZE} matrix traversal:")
    print(f"    Row-major (cache-friendly):   {row_major_ns/1e6:>8.2f} ms")
    print(f"    Column-major (cache-hostile):  {col_major_ns/1e6:>8.2f} ms")
    print(f"    Ratio: {col_major_ns/row_major_ns:.2f}x slower")

    print("""
    なぜ差が出るか:
    ┌─────────────────────────────────────────────┐
    │ CPU Cache Hierarchy                          │
    │                                               │
    │ L1 Cache:  32-64 KB,  ~1 ns   (4 cycles)     │
    │ L2 Cache:  256-512 KB, ~3 ns  (12 cycles)    │
    │ L3 Cache:  8-32 MB,   ~10 ns  (40 cycles)    │
    │ Main RAM:             ~100 ns (400 cycles)    │
    │ SSD:                  ~100 μs (400K cycles)   │
    │ HDD:                  ~10 ms  (40M cycles)    │
    └─────────────────────────────────────────────┘

    Cache Line: 64 bytes (CPU は 64byte 単位でメモリを読む)
    Row-major: 次の要素が同じ cache line → L1 hit
    Column-major: 次の要素が SIZE × 8bytes 先 → cache miss
    """)

    # --- 1.2 Memory Layout ---
    print("─" * 60)
    print("1.2 Python オブジェクトのメモリサイズ")
    print("─" * 60)

    objects = [
        ("int (0)", 0),
        ("int (1)", 1),
        ("int (2**30)", 2**30),
        ("float", 3.14),
        ("bool", True),
        ("None", None),
        ("str (empty)", ""),
        ("str ('hello')", "hello"),
        ("list (empty)", []),
        ("list (10 ints)", list(range(10))),
        ("dict (empty)", {}),
        ("dict (10 items)", {i: i for i in range(10)}),
        ("set (empty)", set()),
        ("tuple (empty)", ()),
        ("tuple (10)", tuple(range(10))),
    ]

    print(f"\n  {'Object':<25} {'Size (bytes)':>12}")
    print("  " + "-" * 40)
    for name, obj in objects:
        print(f"  {name:<25} {sys.getsizeof(obj):>12}")

    # __slots__ comparison
    class WithoutSlots:
        def __init__(self):
            self.x = 1
            self.y = 2
            self.z = 3

    class WithSlots:
        __slots__ = ('x', 'y', 'z')
        def __init__(self):
            self.x = 1
            self.y = 2
            self.z = 3

    normal = WithoutSlots()
    slotted = WithSlots()
    print(f"\n  class WithoutSlots: {sys.getsizeof(normal) + sys.getsizeof(normal.__dict__)} bytes (obj + __dict__)")
    print(f"  class WithSlots:   {sys.getsizeof(slotted)} bytes")
    print(f"  → __slots__ で {(sys.getsizeof(normal) + sys.getsizeof(normal.__dict__) - sys.getsizeof(slotted))} bytes 削減/instance")

    print("""
    ★ 100万オブジェクトのとき:
    - WithoutSlots: ~152 bytes × 1M = 152 MB
    - WithSlots:    ~56 bytes × 1M  = 56 MB  (63% 削減)
    → 大量オブジェクトを扱う場合は __slots__ or dataclass(slots=True) を使う
    """)

    # --- 1.3 Struct of Arrays vs Array of Structs ---
    print("─" * 60)
    print("1.3 SoA vs AoS (データレイアウト)")
    print("─" * 60)
    print("""
    AoS (Array of Structs) — 一般的なOOP:
    [Point(x=1,y=2,z=3), Point(x=4,y=5,z=6), ...]
    Memory: |x1|y1|z1|x2|y2|z2|x3|y3|z3|...

    SoA (Struct of Arrays) — 数値計算/ゲーム/GPU向け:
    xs = [1, 4, 7, ...]
    ys = [2, 5, 8, ...]
    zs = [3, 6, 9, ...]
    Memory: |x1|x2|x3|...|y1|y2|y3|...|z1|z2|z3|...

    SoA のメリット:
    - SIMD (ベクトル演算) で一括処理可能
    - 特定フィールドだけアクセスする場合、cache line に無駄がない
    - NumPy / Pandas / Polars は内部的に SoA (columnar)
    """)

    # Benchmark SoA vs AoS
    N = 100_000
    # AoS
    aos = [{"x": random.random(), "y": random.random()} for _ in range(N)]
    start = time.perf_counter_ns()
    sum_x = sum(p["x"] for p in aos)
    aos_ns = time.perf_counter_ns() - start

    # SoA
    xs = [random.random() for _ in range(N)]
    ys = [random.random() for _ in range(N)]
    start = time.perf_counter_ns()
    sum_x = sum(xs)
    soa_ns = time.perf_counter_ns() - start

    print(f"  Summing x from {N:,} points:")
    print(f"    AoS (list of dicts): {aos_ns/1e6:.2f} ms")
    print(f"    SoA (separate lists): {soa_ns/1e6:.2f} ms")
    print(f"    Ratio: {aos_ns/soa_ns:.2f}x")


# ============================================================
# Chapter 2: Probabilistic Data Structures
# ============================================================

def chapter2_probabilistic():
    print("\n" + "=" * 70)
    print("Chapter 2: Probabilistic Data Structures")
    print("  正確さを少し犠牲にして、大幅にメモリ・速度を改善する")
    print("=" * 70)

    # --- 2.1 Bloom Filter ---
    print("\n" + "─" * 60)
    print("2.1 Bloom Filter")
    print("─" * 60)

    class BloomFilter:
        def __init__(self, capacity: int, fp_rate: float = 0.01):
            self.size = self._optimal_size(capacity, fp_rate)
            self.num_hashes = self._optimal_hashes(self.size, capacity)
            self.bits = [False] * self.size

        @staticmethod
        def _optimal_size(n: int, p: float) -> int:
            return int(-n * math.log(p) / (math.log(2) ** 2))

        @staticmethod
        def _optimal_hashes(m: int, n: int) -> int:
            return max(1, int(m / n * math.log(2)))

        def _hashes(self, item: str) -> List[int]:
            h1 = int(hashlib.md5(item.encode()).hexdigest(), 16)
            h2 = int(hashlib.sha1(item.encode()).hexdigest(), 16)
            return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

        def add(self, item: str):
            for pos in self._hashes(item):
                self.bits[pos] = True

        def contains(self, item: str) -> bool:
            return all(self.bits[pos] for pos in self._hashes(item))

    bf = BloomFilter(capacity=10000, fp_rate=0.01)
    print(f"\n  Capacity: 10,000, FP rate: 1%")
    print(f"  Bit array size: {bf.size:,} bits ({bf.size/8/1024:.1f} KB)")
    print(f"  Hash functions: {bf.num_hashes}")

    # Add 10,000 items
    for i in range(10000):
        bf.add(f"item:{i}")

    # Test false positive rate
    fp = 0
    tests = 10000
    for i in range(10000, 10000 + tests):
        if bf.contains(f"item:{i}"):
            fp += 1

    print(f"\n  False positive rate: {fp}/{tests} = {fp/tests*100:.2f}%")
    print(f"  vs Set: {sys.getsizeof(set(f'item:{i}' for i in range(10000)))/1024:.0f} KB")

    print("""
    用途:
    - DB: 「このキーは存在しない」を高速判定 (ディスクI/O 回避)
    - Web: ブラウザのフィッシングサイト検出 (Chrome Safe Browsing)
    - CDN: キャッシュヒット率向上
    - 分散システム: レプリカ間の差分検出の前段
    """)

    # --- 2.2 Count-Min Sketch ---
    print("─" * 60)
    print("2.2 Count-Min Sketch (頻度推定)")
    print("─" * 60)

    class CountMinSketch:
        def __init__(self, width: int = 1000, depth: int = 5):
            self.width = width
            self.depth = depth
            self.table = [[0] * width for _ in range(depth)]
            self.seeds = [random.randint(0, 2**32) for _ in range(depth)]

        def _hash(self, item: str, i: int) -> int:
            h = hashlib.md5(f"{self.seeds[i]}:{item}".encode()).hexdigest()
            return int(h, 16) % self.width

        def add(self, item: str, count: int = 1):
            for i in range(self.depth):
                self.table[i][self._hash(item, i)] += count

        def estimate(self, item: str) -> int:
            return min(self.table[i][self._hash(item, i)] for i in range(self.depth))

    cms = CountMinSketch(width=1000, depth=5)
    # Simulate access log with Zipf distribution
    items = [f"url:/page/{i}" for i in range(100)]
    actual = defaultdict(int)
    for _ in range(50000):
        idx = int(random.paretovariate(1.5)) % len(items)
        item = items[idx]
        cms.add(item)
        actual[item] += 1

    # Compare top items
    print(f"\n  50,000 URL accesses (Zipf distribution):")
    print(f"  Memory: {cms.width * cms.depth * 4 / 1024:.1f} KB (vs dict: ~{sys.getsizeof(actual)/1024:.0f} KB)")
    print(f"\n  {'URL':<20} {'Actual':>8} {'Estimated':>10} {'Error':>8}")
    print("  " + "-" * 50)
    top_items = sorted(actual.items(), key=lambda x: x[1], reverse=True)[:8]
    for item, count in top_items:
        est = cms.estimate(item)
        err = est - count
        print(f"  {item:<20} {count:>8} {est:>10} {err:>+8}")

    print("""
    用途: Top-K, Heavy Hitter 検出, ストリーム処理での頻度推定
    特徴: 常に過大推定 (never undercount), メモリ固定
    """)

    # --- 2.3 HyperLogLog ---
    print("─" * 60)
    print("2.3 HyperLogLog (カーディナリティ推定)")
    print("─" * 60)

    class HyperLogLog:
        def __init__(self, p: int = 14):
            self.p = p
            self.m = 1 << p  # number of registers
            self.registers = [0] * self.m
            self.alpha = 0.7213 / (1 + 1.079 / self.m)

        def add(self, item: str):
            h = int(hashlib.md5(item.encode()).hexdigest(), 16)
            idx = h & (self.m - 1)
            w = h >> self.p
            # Count leading zeros + 1
            rho = 1
            while w & 1 == 0 and rho <= 64 - self.p:
                rho += 1
                w >>= 1
            self.registers[idx] = max(self.registers[idx], rho)

        def count(self) -> int:
            indicator = sum(2 ** (-r) for r in self.registers)
            estimate = self.alpha * self.m * self.m / indicator
            # Small range correction
            if estimate <= 2.5 * self.m:
                zeros = self.registers.count(0)
                if zeros > 0:
                    estimate = self.m * math.log(self.m / zeros)
            return int(estimate)

    hll = HyperLogLog(p=14)  # 2^14 = 16384 registers
    actual_set = set()
    for i in range(100_000):
        item = f"user:{random.randint(0, 50000)}"
        hll.add(item)
        actual_set.add(item)

    estimated = hll.count()
    actual_count = len(actual_set)
    error = abs(estimated - actual_count) / actual_count * 100

    print(f"\n  Added 100,000 items (50,000 unique):")
    print(f"    Actual unique:    {actual_count:>10,}")
    print(f"    HLL estimated:    {estimated:>10,}")
    print(f"    Error:            {error:>9.2f}%")
    print(f"    Memory:           {hll.m * 1 / 1024:>9.1f} KB (vs Set: ~{sys.getsizeof(actual_set)/1024:.0f} KB)")

    print("""
    Redis の PFADD/PFCOUNT は HyperLogLog:
    - 12 KB で数十億のユニーク数を ~0.81% 誤差で推定
    - DAU (Daily Active Users) のカウントに最適
    """)


# ============================================================
# Chapter 3: Caching Strategies
# ============================================================

def chapter3_caching():
    print("\n" + "=" * 70)
    print("Chapter 3: Caching Strategies")
    print("  キャッシュの設計 — 正しく使えば 100x 速くなる")
    print("=" * 70)

    # --- 3.1 LRU vs LFU vs ARC ---
    print("\n" + "─" * 60)
    print("3.1 キャッシュ置換アルゴリズム比較")
    print("─" * 60)

    class LRUCache:
        def __init__(self, capacity: int):
            self.capacity = capacity
            self.cache: OrderedDict = OrderedDict()
            self.hits = 0
            self.misses = 0

        def get(self, key: str) -> Optional[Any]:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None

        def put(self, key: str, value: Any):
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

        def hit_rate(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0

    class LFUCache:
        def __init__(self, capacity: int):
            self.capacity = capacity
            self.cache: Dict[str, Any] = {}
            self.freq: Dict[str, int] = {}
            self.min_freq = 0
            self.freq_to_keys: Dict[int, OrderedDict] = defaultdict(OrderedDict)
            self.hits = 0
            self.misses = 0

        def get(self, key: str) -> Optional[Any]:
            if key not in self.cache:
                self.misses += 1
                return None
            self.hits += 1
            self._update_freq(key)
            return self.cache[key]

        def put(self, key: str, value: Any):
            if self.capacity <= 0:
                return
            if key in self.cache:
                self.cache[key] = value
                self._update_freq(key)
                return
            if len(self.cache) >= self.capacity:
                self._evict()
            self.cache[key] = value
            self.freq[key] = 1
            self.freq_to_keys[1][key] = None
            self.min_freq = 1

        def _update_freq(self, key: str):
            f = self.freq[key]
            del self.freq_to_keys[f][key]
            if not self.freq_to_keys[f] and f == self.min_freq:
                self.min_freq += 1
            self.freq[key] = f + 1
            self.freq_to_keys[f + 1][key] = None

        def _evict(self):
            keys = self.freq_to_keys[self.min_freq]
            evict_key, _ = keys.popitem(last=False)
            del self.cache[evict_key]
            del self.freq[evict_key]

        def hit_rate(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0

    # Generate workload: 80% hot keys (20 keys), 20% cold keys (1000 keys)
    random.seed(42)
    workload = []
    hot_keys = [f"hot:{i}" for i in range(20)]
    cold_keys = [f"cold:{i}" for i in range(1000)]
    for _ in range(10000):
        if random.random() < 0.8:
            workload.append(random.choice(hot_keys))
        else:
            workload.append(random.choice(cold_keys))

    # Test LRU
    lru = LRUCache(capacity=50)
    for key in workload:
        if lru.get(key) is None:
            lru.put(key, f"value_{key}")

    # Test LFU
    lfu = LFUCache(capacity=50)
    for key in workload:
        if lfu.get(key) is None:
            lfu.put(key, f"value_{key}")

    print(f"\n  Workload: 10,000 ops, 80% hot (20 keys), 20% cold (1000 keys)")
    print(f"  Cache capacity: 50")
    print(f"\n  {'Algorithm':<10} {'Hits':>8} {'Misses':>8} {'Hit Rate':>10}")
    print("  " + "-" * 40)
    print(f"  {'LRU':<10} {lru.hits:>8} {lru.misses:>8} {lru.hit_rate():>9.1%}")
    print(f"  {'LFU':<10} {lfu.hits:>8} {lfu.misses:>8} {lfu.hit_rate():>9.1%}")

    print("""
    キャッシュ戦略:
    ┌──────────────────┬────────────────────────────────┐
    │ Strategy          │ 説明                            │
    ├──────────────────┼────────────────────────────────┤
    │ Cache-Aside       │ App が Cache miss → DB → Cache  │
    │ Read-Through      │ Cache が DB から自動 load        │
    │ Write-Through     │ Cache + DB に同時書き込み        │
    │ Write-Behind      │ Cache に書いて後で DB に非同期   │
    │ Write-Around      │ DB に直接書き、Cache は read で │
    └──────────────────┴────────────────────────────────┘

    Cache Stampede (Thundering Herd):
    - 人気キーの TTL 期限切れ → 大量リクエストが同時に DB へ
    - 対策:
      1. Probabilistic Early Expiration: TTL前にランダムに更新
      2. Lock: 1つのリクエストだけ DB に行く、他は待機
      3. Stale-while-revalidate: 古いデータを返しつつバックグラウンド更新
    """)


# ============================================================
# Chapter 4: System-Level Optimization
# ============================================================

def chapter4_system():
    print("\n" + "=" * 70)
    print("Chapter 4: System-Level Optimization")
    print("  N+1 問題・コネクションプール・Rate Limiting")
    print("=" * 70)

    # --- 4.1 N+1 Problem ---
    print("\n" + "─" * 60)
    print("4.1 N+1 問題のデモ")
    print("─" * 60)

    class FakeDB:
        def __init__(self):
            self.query_count = 0
            self.users = {i: f"User_{i}" for i in range(100)}
            self.orders = {i: [f"Order_{j}" for j in range(3)] for i in range(100)}

        def get_users(self) -> List[int]:
            self.query_count += 1
            return list(self.users.keys())

        def get_orders(self, user_id: int) -> List[str]:
            self.query_count += 1
            return self.orders.get(user_id, [])

        def get_orders_batch(self, user_ids: List[int]) -> Dict[int, List[str]]:
            self.query_count += 1
            return {uid: self.orders.get(uid, []) for uid in user_ids}

    # N+1 problem
    db_bad = FakeDB()
    users = db_bad.get_users()[:20]
    for uid in users:
        db_bad.get_orders(uid)
    print(f"\n  N+1 pattern: {db_bad.query_count} queries (1 + N={len(users)})")

    # Batch solution
    db_good = FakeDB()
    users = db_good.get_users()[:20]
    db_good.get_orders_batch(users)
    print(f"  Batch pattern: {db_good.query_count} queries")
    print(f"  → {db_bad.query_count / db_good.query_count:.0f}x fewer queries")

    print("""
    N+1 の見つけ方:
    - ORMのログで同じクエリが N 回出てないか
    - SQLAlchemy: echo=True, Django: django-debug-toolbar
    - 解決: eager loading, DataLoader (GraphQL), IN句バッチ

    ★ 面接: 「あなたのアプリが遅い。どう調査する？」
    1. メトリクス確認: P50, P95, P99 のどこが遅い?
    2. APM/トレース: どのスパンが支配的? (DB? 外部API? 計算?)
    3. DBクエリ分析: slow query log, EXPLAIN ANALYZE
    4. N+1 チェック: クエリ数を確認
    5. プロファイリング: CPU (cProfile), Memory (tracemalloc)
    """)

    # --- 4.2 Rate Limiting Algorithms ---
    print("─" * 60)
    print("4.2 Rate Limiting アルゴリズム比較")
    print("─" * 60)

    class TokenBucket:
        def __init__(self, rate: float, capacity: int):
            self.rate = rate
            self.capacity = capacity
            self.tokens = capacity
            self.last_time = time.time()

        def allow(self) -> bool:
            now = time.time()
            elapsed = now - self.last_time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_time = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    class SlidingWindowCounter:
        def __init__(self, limit: int, window_sec: float):
            self.limit = limit
            self.window = window_sec
            self.current_count = 0
            self.previous_count = 0
            self.current_start = time.time()

        def allow(self) -> bool:
            now = time.time()
            elapsed = now - self.current_start
            if elapsed >= self.window:
                self.previous_count = self.current_count
                self.current_count = 0
                self.current_start = now
                elapsed = 0

            # Weighted count
            weight = 1 - (elapsed / self.window)
            estimated = self.previous_count * weight + self.current_count
            if estimated < self.limit:
                self.current_count += 1
                return True
            return False

    print("""
    ┌────────────────────┬─────────────────────────────────┐
    │ Algorithm           │ 特徴                             │
    ├────────────────────┼─────────────────────────────────┤
    │ Token Bucket        │ バースト許容、滑らかなレート      │
    │ Leaky Bucket        │ 一定レートで処理 (queue)          │
    │ Fixed Window        │ 実装簡単、境界でバースト問題      │
    │ Sliding Window Log  │ 正確、メモリ使用多                │
    │ Sliding Window Count│ 近似、メモリ効率良               │
    └────────────────────┴─────────────────────────────────┘

    Token Bucket (API Gateway のデファクト):
    ┌───────────────────────────────────┐
    │ Tokens: ████████░░ (8/10)         │
    │ Rate: 10 tokens/sec               │
    │ Request arrives → consume 1 token │
    │ No tokens → reject (429)          │
    └───────────────────────────────────┘

    分散 Rate Limiting:
    - Redis + Lua script で atomic にカウント
    - or Token Bucket の state を Redis に保存
    - 複数インスタンスで共有
    """)

    # --- 4.3 Connection Pool ---
    print("─" * 60)
    print("4.3 コネクションプールサイジング")
    print("─" * 60)
    print("""
    Little's Law: L = λ × W
    - L: 同時接続数 (pool size)
    - λ: リクエストレート (req/sec)
    - W: 平均レスポンスタイム (sec)

    例:
    - 1000 req/sec, 平均 50ms → L = 1000 × 0.05 = 50 connections
    - 1000 req/sec, 平均 200ms → L = 1000 × 0.2 = 200 connections

    HikariCP (Java) の推奨:
    pool_size = cpu_cores × 2 + disk_spindles
    → 4 cores × 2 + 1 SSD = 9 connections (意外と小さい!)

    ★ プールが大きすぎると:
    - DB 側のメモリ消費増
    - コンテキストスイッチ増
    - Lock contention 増
    → 「大きければ良い」は間違い
    """)


# ============================================================
# Chapter 5: Benchmarking & Production Performance
# ============================================================

def chapter5_production():
    print("\n" + "=" * 70)
    print("Chapter 5: Benchmarking & Production Performance")
    print("  正しく計測し、正しく判断する")
    print("=" * 70)

    # --- 5.1 Micro-Benchmark Harness ---
    print("\n" + "─" * 60)
    print("5.1 マイクロベンチマーク")
    print("─" * 60)

    def benchmark(func, iterations: int = 1000, warmup: int = 100) -> Dict:
        # Warmup
        for _ in range(warmup):
            func()

        times = []
        for _ in range(iterations):
            start = time.perf_counter_ns()
            func()
            elapsed = time.perf_counter_ns() - start
            times.append(elapsed)

        times.sort()
        n = len(times)
        return {
            "mean": sum(times) / n,
            "median": times[n // 2],
            "p95": times[int(n * 0.95)],
            "p99": times[int(n * 0.99)],
            "min": times[0],
            "max": times[-1],
            "stddev": (sum((t - sum(times)/n)**2 for t in times) / n) ** 0.5,
        }

    # Benchmark: dict lookup vs list search
    data_dict = {f"key:{i}": i for i in range(1000)}
    data_list = [(f"key:{i}", i) for i in range(1000)]

    def dict_lookup():
        return data_dict.get("key:500")

    def list_search():
        for k, v in data_list:
            if k == "key:500":
                return v

    result_dict = benchmark(dict_lookup, iterations=5000)
    result_list = benchmark(list_search, iterations=5000)

    print(f"\n  Lookup 'key:500' from 1000 items (5000 iterations):")
    print(f"\n  {'Metric':<10} {'dict (ns)':>12} {'list (ns)':>12} {'Ratio':>8}")
    print("  " + "-" * 45)
    for metric in ["mean", "median", "p95", "p99"]:
        d = result_dict[metric]
        l = result_list[metric]
        print(f"  {metric:<10} {d:>12.0f} {l:>12.0f} {l/d:>7.1f}x")

    print("""
    ★ ベンチマークの落とし穴:
    1. JIT/Warmup 不足: 最初の実行は遅い (JVM, V8)
    2. Dead Code Elimination: 結果を使わないとコンパイラが削除
    3. Constant Folding: 定数を事前計算してしまう
    4. メモリアロケーション: GC のタイミングで結果が歪む
    5. CPU周波数スケーリング: Turbo Boost で結果が不安定
    → 正しい計測: warmup + 十分な反復 + 統計分析
    """)

    # --- 5.2 Tail Latency ---
    print("─" * 60)
    print("5.2 Tail Latency Amplification")
    print("─" * 60)

    def simulate_fanout(num_backends: int, p99_ms: float, trials: int = 10000) -> Dict:
        """1リクエストが N バックエンドに fan-out した時の集約レイテンシ"""
        results = []
        for _ in range(trials):
            # Each backend: ~normal(10ms, 5ms) with occasional spike
            latencies = []
            for _ in range(num_backends):
                if random.random() < 0.01:  # 1% chance of P99
                    lat = p99_ms
                else:
                    lat = max(1, random.gauss(10, 5))
                latencies.append(lat)
            # Aggregate = max (all must complete)
            results.append(max(latencies))

        results.sort()
        n = len(results)
        return {
            "p50": results[n // 2],
            "p95": results[int(n * 0.95)],
            "p99": results[int(n * 0.99)],
        }

    print(f"\n  Backend P99 = 100ms, P50 = 10ms")
    print(f"\n  {'Fan-out':>10} {'Agg P50':>10} {'Agg P95':>10} {'Agg P99':>10}")
    print("  " + "-" * 45)

    for n_backends in [1, 5, 10, 50, 100]:
        result = simulate_fanout(n_backends, p99_ms=100)
        print(f"  {n_backends:>10} {result['p50']:>9.1f}ms {result['p95']:>9.1f}ms {result['p99']:>9.1f}ms")

    print("""
    ★ Jeff Dean's "The Tail at Scale" (Google):
    - 1台の P99 = 100ms でも、100台に fan-out すると
      P50 ≈ 100ms になる (63% の確率で1台以上が遅い)

    対策:
    1. Hedged Requests: 一定時間後に2台目にも送る
    2. Tied Requests: 最初から2台に送り、早い方を採用
    3. Micro-partitioning: 粒度を細かくして fan-out を減らす
    4. Backend optimization: P99 自体を改善する
    """)

    # --- 5.3 Apdex Score ---
    print("─" * 60)
    print("5.3 Apdex Score (Application Performance Index)")
    print("─" * 60)

    def calculate_apdex(latencies: List[float], threshold: float) -> float:
        satisfied = sum(1 for l in latencies if l <= threshold)
        tolerating = sum(1 for l in latencies if threshold < l <= 4 * threshold)
        total = len(latencies)
        return (satisfied + tolerating / 2) / total

    # Generate realistic latency distribution
    random.seed(42)
    latencies = []
    for _ in range(10000):
        r = random.random()
        if r < 0.7:
            latencies.append(random.gauss(50, 10))    # 70%: ~50ms
        elif r < 0.95:
            latencies.append(random.gauss(200, 50))   # 25%: ~200ms
        else:
            latencies.append(random.gauss(800, 200))   # 5%: ~800ms

    threshold = 100  # ms
    apdex = calculate_apdex(latencies, threshold)

    print(f"\n  Threshold (T): {threshold}ms")
    print(f"  Apdex = (Satisfied + Tolerating/2) / Total")
    print(f"  Apdex = {apdex:.3f}")

    rating = "Excellent" if apdex >= 0.94 else "Good" if apdex >= 0.85 else \
             "Fair" if apdex >= 0.7 else "Poor" if apdex >= 0.5 else "Unacceptable"
    print(f"  Rating: {rating}")

    print("""
    Apdex スコア解釈:
    ┌──────────┬──────────────┐
    │ Score     │ Rating        │
    ├──────────┼──────────────┤
    │ 0.94-1.00│ Excellent     │
    │ 0.85-0.93│ Good          │
    │ 0.70-0.84│ Fair          │
    │ 0.50-0.69│ Poor          │
    │ 0.00-0.49│ Unacceptable  │
    └──────────┴──────────────┘

    ★ SLO 設計の考え方:
    - P50 < 100ms (ユーザー体感の「速い」)
    - P95 < 500ms (大多数が許容)
    - P99 < 2000ms (99%のユーザーが不満を感じない)
    - Error Rate < 0.1% (99.9% SLO)
    - Error Budget = 1 - SLO = 0.1%
      → 月間で 43.2 分のダウンタイムまで許容
    """)


# ============================================================
# Main
# ============================================================

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  Performance Engineering                                       ║")
    print("║  計測 → 分析 → 最適化 → 検証 のサイクル                        ║")
    print("║  「推測するな、計測せよ」— Rob Pike                             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    chapter1_cpu_memory()
    chapter2_probabilistic()
    chapter3_caching()
    chapter4_system()
    chapter5_production()

    print("\n" + "=" * 70)
    print("Summary: パフォーマンスエンジニアリングの原則")
    print("=" * 70)
    print("""
    1. 計測が先: プロファイリングなしの最適化は時間の無駄
    2. Amdahl の法則: ボトルネック以外を最適化しても効果は小さい
    3. キャッシュは銀の弾丸: L1 → RAM で 100x, RAM → Disk で 1000x
    4. 確率的データ構造: 正確さを少し犠牲に → 桁違いの効率
    5. Tail Latency: P99 こそが本当のユーザー体験
    6. Little's Law: L = λW を使ってリソースサイジング

    推奨書籍:
    - "Systems Performance" by Brendan Gregg
    - "High Performance Python" by Gorelick & Ozsvald
    - "The Art of Capacity Planning" by John Allspaw
    """)

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    ・N+1問題 (ORMの罠, eager loading, DataLoader, IN句バッチ)
    ・キャッシュ戦略 LRU (Cache-Aside, Read-Through, Write-Through)
    ・Rate Limiting (Token Bucket, Sliding Window, 429レスポンス)
    ・ベンチマーク基礎 (warmup, P50/P95/P99, 統計的に正しい計測)

  【Tier 2: 重要 — 実務で頻出】
    ・Bloom Filter (偽陽性あり偽陰性なし, DB/CDNでの活用)
    ・Tail Latency (Fan-out amplification, Hedged Requests)
    ・Apdex Score (SLO設計, Satisfied/Tolerating/Frustrated)
    ・CPU cache効果 (Row-major vs Column-major, Cache Line 64B)

  【Tier 3: 上級 — シニア以上で差がつく】
    ・HyperLogLog (12KBで数十億のユニーク推定, Redis PFCOUNT)
    ・Count-Min Sketch (頻度推定, Top-K/Heavy Hitter検出)
    ・LFU キャッシュ (頻度ベース置換, LRUとの使い分け)
    ・Cache Stampede対策 (Probabilistic Early Expiration, Lock, Stale-while-revalidate)

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    ・__slots__最適化 (100万オブジェクトで63%メモリ削減)
    ・メモリプロファイリング (tracemalloc, SoA vs AoS レイアウト)
    ・Fan-out amplification (100台fan-outでP50≈P99, Jeff Dean論文)
""")


if __name__ == "__main__":
    main()
