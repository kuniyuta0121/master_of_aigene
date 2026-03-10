"""
===============================================================================
 並行処理 & 並列処理 ディープガイド
 ― Concurrency & Parallelism: メモリモデルからLock-Freeまで ―
===============================================================================
Python 標準ライブラリのみ使用 / そのまま実行可能

目次:
  1. メモリモデル (概念 + シミュレーション)
  2. 同期プリミティブ完全ガイド
  3. Lock-Free / Wait-Free
  4. 並行パターン
  5. デッドロック (検出 + 回避)
  6. async/await vs Thread vs Process
  7. 並行バグのパターン
  8. 優先度マップ (Tier 1-4)
"""

import threading
import multiprocessing
import queue
import time
import random
import asyncio
import concurrent.futures
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Optional

# ============================================================================
# 1. メモリモデル (概念 + シミュレーション)
# ============================================================================

def section_memory_model():
    """
    メモリモデル: CPU/コンパイラがメモリアクセスをどう扱うかの仕様。
    マルチスレッドでの「見え方」を決定する。

    ■ Sequential Consistency (逐次一貫性)
      - すべてのスレッドが同じ順序でメモリ操作を観測する
      - 直感的だが遅い（最適化の余地がない）

    ■ Relaxed Ordering (緩和順序)
      - CPU/コンパイラが命令を並び替え可能
      - x86: Store-Load のみ並び替え (TSO: Total Store Order)
      - ARM/RISC-V: ほぼ何でも並び替え可能

    ■ Java Memory Model (JMM)
      - happens-before 関係で可視性を保証:
        (1) 同一スレッド内のプログラム順序
        (2) synchronized の unlock → 別スレッドの lock
        (3) volatile の write → 別スレッドの read
        (4) Thread.start() → そのスレッドの最初のアクション
        (5) Thread の最後のアクション → join() の戻り

    ■ Python の GIL (Global Interpreter Lock)
      - CPython では一度に1スレッドしかバイトコード実行しない
      - GIL がメモリ可視性を「偶然」保証するが、仕様ではない
      - マルチコア CPU を活かせない → multiprocessing を使う
    """
    print("=== メモリモデル シミュレーション ===\n")

    # --- Visibility 問題のシミュレーション ---
    # volatile がない場合、あるスレッドの書き込みが他スレッドから見えない
    class VisibilityDemo:
        """
        Java の volatile に相当する問題のデモ。
        Python は GIL のおかげで表面化しにくいが、概念理解のため。
        """
        def __init__(self):
            self.flag = False       # volatile でない → 見えない可能性
            self.data = 0
            self.lock = threading.Lock()  # 可視性を保証するには Lock が必要

        def writer_unsafe(self):
            """Lock なし: data の変更が flag の後に見える保証なし"""
            self.data = 42
            # ↑ コンパイラ/CPU がここを並び替える可能性 (Java の場合)
            self.flag = True

        def writer_safe(self):
            """Lock あり: happens-before 関係が成立"""
            with self.lock:
                self.data = 42
                self.flag = True

        def reader(self):
            """flag が True でも data が 42 とは限らない (unsafe の場合)"""
            if self.flag:
                return self.data
            return None

    demo = VisibilityDemo()
    demo.writer_safe()
    result = demo.reader()
    print(f"  Visibility デモ: flag={demo.flag}, data={result}")

    # --- Reordering シミュレーション ---
    # 命令の並び替えが起こるとどうなるか
    reorder_results = defaultdict(int)
    iterations = 10000

    for _ in range(iterations):
        x = y = 0
        r1 = r2 = 0

        def thread1():
            nonlocal x, r1
            x = 1          # S1
            r1 = y          # L1

        def thread2():
            nonlocal y, r2
            y = 1          # S2
            r2 = x          # L2

        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)
        t1.start(); t2.start()
        t1.join(); t2.join()
        reorder_results[(r1, r2)] += 1

    print(f"\n  Reordering テスト ({iterations}回):")
    for (r1, r2), count in sorted(reorder_results.items()):
        label = ""
        if r1 == 0 and r2 == 0:
            label = " ← 両方 0 = 並び替え発生！"
        print(f"    r1={r1}, r2={r2}: {count}回{label}")

    # --- Memory Barrier 概念 ---
    print("""
  ■ Memory Barrier / Fence:
    - Store Barrier: barrier 前の store が barrier 後の store より先に完了
    - Load Barrier:  barrier 前の load が barrier 後の load より先に完了
    - Full Barrier:  両方
    - Python: threading.Lock の acquire/release が暗黙のバリア
    - Java: volatile read/write がバリアを挿入
    """)


# ============================================================================
# 2. 同期プリミティブ完全ガイド
# ============================================================================

def section_sync_primitives():
    print("=== 同期プリミティブ完全ガイド ===\n")

    # --- 2a. Peterson's Algorithm (Mutex 自作) ---
    class PetersonLock:
        """
        Peterson の相互排除アルゴリズム (2スレッド用)。
        ハードウェア支援なしで mutual exclusion を実現。
        注意: メモリ並び替えがある現代CPUでは不完全。概念理解用。
        """
        def __init__(self):
            self.flag = [False, False]  # 各スレッドが臨界区域に入りたいか
            self.turn = 0               # 譲り合い用

        def lock(self, tid: int):
            other = 1 - tid
            self.flag[tid] = True
            self.turn = other           # 相手に譲る
            # busy wait: 相手が入りたくて、かつ相手のターンなら待つ
            while self.flag[other] and self.turn == other:
                pass  # spin

        def unlock(self, tid: int):
            self.flag[tid] = False

    # Peterson テスト
    counter = [0]
    peterson = PetersonLock()

    def peterson_worker(tid, n):
        for _ in range(n):
            peterson.lock(tid)
            counter[0] += 1  # 臨界区域
            peterson.unlock(tid)

    counter[0] = 0
    t0 = threading.Thread(target=peterson_worker, args=(0, 5000))
    t1 = threading.Thread(target=peterson_worker, args=(1, 5000))
    t0.start(); t1.start()
    t0.join(); t1.join()
    print(f"  Peterson Lock: counter={counter[0]} (期待値: 10000)")

    # --- 2b. カウンティングセマフォ ---
    class CountingSemaphore:
        """
        カウンティングセマフォの自作実装。
        同時に N スレッドまでリソースにアクセス可能。
        """
        def __init__(self, initial: int):
            self._count = initial
            self._lock = threading.Lock()
            self._condition = threading.Condition(self._lock)

        def acquire(self):
            with self._condition:
                while self._count <= 0:
                    self._condition.wait()
                self._count -= 1

        def release(self):
            with self._condition:
                self._count += 1
                self._condition.notify()

    # セマフォテスト: 同時3スレッドまで
    sem = CountingSemaphore(3)
    active = [0]
    max_active = [0]
    active_lock = threading.Lock()

    def sem_worker(worker_id):
        sem.acquire()
        with active_lock:
            active[0] += 1
            max_active[0] = max(max_active[0], active[0])
        time.sleep(0.01)
        with active_lock:
            active[0] -= 1
        sem.release()

    threads = [threading.Thread(target=sem_worker, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  Semaphore: 最大同時実行数={max_active[0]} (上限: 3)")

    # --- 2c. ReadWriteLock ---
    class ReadWriteLock:
        """
        読者/書者問題の実装 (読者優先)。
        - 複数の読者が同時に読める
        - 書者は排他的にアクセス
        """
        def __init__(self):
            self._readers = 0
            self._lock = threading.Lock()          # readers カウンタ保護
            self._write_lock = threading.Lock()    # 書者排他用

        def read_acquire(self):
            with self._lock:
                self._readers += 1
                if self._readers == 1:
                    self._write_lock.acquire()  # 最初の読者が書者をブロック

        def read_release(self):
            with self._lock:
                self._readers -= 1
                if self._readers == 0:
                    self._write_lock.release()  # 最後の読者が解放

        def write_acquire(self):
            self._write_lock.acquire()

        def write_release(self):
            self._write_lock.release()

    rw = ReadWriteLock()
    shared_data = {"value": 0}
    rw_log = []

    def reader(rid):
        rw.read_acquire()
        val = shared_data["value"]
        rw_log.append(f"R{rid}={val}")
        time.sleep(0.005)
        rw.read_release()

    def writer(wid, val):
        rw.write_acquire()
        shared_data["value"] = val
        rw_log.append(f"W{wid}={val}")
        time.sleep(0.005)
        rw.write_release()

    threads = []
    for i in range(3): threads.append(threading.Thread(target=reader, args=(i,)))
    threads.append(threading.Thread(target=writer, args=(0, 99)))
    for i in range(3, 6): threads.append(threading.Thread(target=reader, args=(i,)))
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  ReadWriteLock 操作ログ: {rw_log}")

    # --- 2d. Condition Variable: Producer/Consumer ---
    buf = deque()
    buf_lock = threading.Lock()
    not_empty = threading.Condition(buf_lock)
    not_full = threading.Condition(buf_lock)
    BUF_SIZE = 5
    produced = []
    consumed = []

    def producer(pid, count):
        for i in range(count):
            item = f"P{pid}-{i}"
            with not_full:
                while len(buf) >= BUF_SIZE:
                    not_full.wait()
                buf.append(item)
                produced.append(item)
                not_empty.notify()

    def consumer(cid, count):
        for _ in range(count):
            with not_empty:
                while len(buf) == 0:
                    not_empty.wait()
                item = buf.popleft()
                consumed.append(item)
                not_full.notify()

    t_p = threading.Thread(target=producer, args=(0, 8))
    t_c = threading.Thread(target=consumer, args=(0, 8))
    t_p.start(); t_c.start()
    t_p.join(); t_c.join()
    print(f"  Condition Variable: produced={len(produced)}, consumed={len(consumed)}")

    # --- 2e. Barrier ---
    class SimpleBarrier:
        """全スレッドが到着するまで待つ合流ポイント。"""
        def __init__(self, parties: int):
            self._parties = parties
            self._count = 0
            self._lock = threading.Lock()
            self._condition = threading.Condition(self._lock)
            self._generation = 0

        def wait(self):
            with self._condition:
                gen = self._generation
                self._count += 1
                if self._count == self._parties:
                    self._count = 0
                    self._generation += 1
                    self._condition.notify_all()
                else:
                    while gen == self._generation:
                        self._condition.wait()

    barrier = SimpleBarrier(3)
    arrival_order = []
    arrival_lock = threading.Lock()

    def barrier_worker(wid):
        time.sleep(random.uniform(0, 0.02))
        with arrival_lock:
            arrival_order.append(f"arrive-{wid}")
        barrier.wait()
        with arrival_lock:
            arrival_order.append(f"passed-{wid}")

    threads = [threading.Thread(target=barrier_worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  Barrier: {arrival_order}")

    # --- 2f. CountDownLatch ---
    class CountDownLatch:
        """N回の countDown() が呼ばれるまで await() でブロック。"""
        def __init__(self, count: int):
            self._count = count
            self._lock = threading.Lock()
            self._condition = threading.Condition(self._lock)

        def count_down(self):
            with self._condition:
                self._count -= 1
                if self._count <= 0:
                    self._condition.notify_all()

        def await_(self, timeout=None):
            with self._condition:
                while self._count > 0:
                    if not self._condition.wait(timeout):
                        return False
            return True

    latch = CountDownLatch(3)
    latch_log = []

    def latch_worker(wid):
        time.sleep(random.uniform(0, 0.02))
        latch_log.append(f"done-{wid}")
        latch.count_down()

    threads = [threading.Thread(target=latch_worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    latch.await_()
    latch_log.append("all-done")
    for t in threads: t.join()
    print(f"  CountDownLatch: {latch_log}")


# ============================================================================
# 3. Lock-Free / Wait-Free
# ============================================================================

def section_lock_free():
    """
    Lock-Free: 少なくとも1つのスレッドが常に進行できる
    Wait-Free: すべてのスレッドが有限ステップで完了する
    """
    print("\n=== Lock-Free / Wait-Free ===\n")

    # --- 3a. CAS (Compare-And-Swap) シミュレーション ---
    class AtomicInteger:
        """
        CAS を使ったアトミックカウンタ。
        Python ではロックでCASをシミュレート。
        実際のCPUでは CMPXCHG (x86) や LL/SC (ARM) 命令。
        """
        def __init__(self, initial=0):
            self._value = initial
            self._lock = threading.Lock()  # CAS のアトミック性をシミュレート

        def get(self):
            return self._value

        def compare_and_swap(self, expected, new_value) -> bool:
            """アトミックに: value == expected なら value = new_value"""
            with self._lock:
                if self._value == expected:
                    self._value = new_value
                    return True
                return False

        def increment(self):
            """CAS ループによるインクリメント (lock-free パターン)"""
            while True:
                old = self._value
                if self.compare_and_swap(old, old + 1):
                    return old + 1
                # 失敗 → リトライ (他スレッドが先に変更した)

        def get_and_add(self, delta):
            while True:
                old = self._value
                if self.compare_and_swap(old, old + delta):
                    return old

    atomic = AtomicInteger(0)
    threads = []
    for _ in range(10):
        t = threading.Thread(target=lambda: [atomic.increment() for _ in range(1000)])
        threads.append(t)
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"  CAS AtomicInteger: {atomic.get()} (期待値: 10000)")

    # --- 3b. Treiber Stack (Lock-Free Stack) ---
    class TreiberStack:
        """
        Lock-Free Stack (Treiber, 1986)。
        push/pop を CAS で実現。
        """
        def __init__(self):
            self._top = None       # (value, next) のタプルチェーン
            self._lock = threading.Lock()  # CAS シミュレート

        def _cas_top(self, expected, new_val) -> bool:
            with self._lock:
                if self._top is expected:  # identity比較
                    self._top = new_val
                    return True
                return False

        def push(self, value):
            while True:
                old_top = self._top
                new_node = (value, old_top)
                if self._cas_top(old_top, new_node):
                    return

        def pop(self):
            while True:
                old_top = self._top
                if old_top is None:
                    return None
                new_top = old_top[1]  # next
                if self._cas_top(old_top, new_top):
                    return old_top[0]  # value

    stack = TreiberStack()
    push_count = [0]
    pop_results = []
    pop_lock = threading.Lock()

    def pusher():
        for i in range(500):
            stack.push(i)

    def popper():
        local = []
        for _ in range(500):
            val = stack.pop()
            if val is not None:
                local.append(val)
        with pop_lock:
            pop_results.extend(local)

    threads = [threading.Thread(target=pusher) for _ in range(4)]
    threads += [threading.Thread(target=popper) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    # 残りを全部 pop
    while True:
        v = stack.pop()
        if v is None:
            break
        pop_results.append(v)
    print(f"  Treiber Stack: pushed=2000, popped={len(pop_results)}")

    # --- 3c. ABA問題 ---
    print("""
  ■ ABA問題:
    1. スレッドAが top=X を読む
    2. スレッドBが X を pop → Y を pop → X を push (top=X に戻る)
    3. スレッドAの CAS は成功するが、スタックの状態は変わっている

  ■ 対策:
    - Tagged Pointer: ポインタにバージョン番号を付加
      (value, next, version) で CAS → version も比較
    - Hazard Pointer: 使用中のノードを宣言して回収を防ぐ
    - Epoch-Based Reclamation: エポック単位でメモリ回収
    """)

    # Tagged Pointer による ABA 対策のデモ
    class TaggedTreiberStack:
        """バージョン番号付き Treiber Stack (ABA対策)。"""
        def __init__(self):
            self._top = None
            self._version = 0
            self._lock = threading.Lock()

        def push(self, value):
            while True:
                with self._lock:
                    old_top = self._top
                    old_ver = self._version
                with self._lock:
                    if self._top is old_top and self._version == old_ver:
                        self._top = (value, old_top)
                        self._version += 1
                        return

        def pop(self):
            while True:
                with self._lock:
                    old_top = self._top
                    old_ver = self._version
                if old_top is None:
                    return None
                with self._lock:
                    if self._top is old_top and self._version == old_ver:
                        self._top = old_top[1]
                        self._version += 1
                        return old_top[0]

    tagged_stack = TaggedTreiberStack()
    for i in range(5):
        tagged_stack.push(i)
    popped = [tagged_stack.pop() for _ in range(5)]
    print(f"  Tagged Stack (ABA対策): popped={popped}")

    # --- 3d. Lock-Free vs Lock-Based ベンチマーク ---
    def bench_lock_based(n):
        lock = threading.Lock()
        counter = [0]
        def worker():
            for _ in range(n):
                with lock:
                    counter[0] += 1
        threads = [threading.Thread(target=worker) for _ in range(4)]
        start = time.perf_counter()
        for t in threads: t.start()
        for t in threads: t.join()
        return time.perf_counter() - start

    def bench_lock_free(n):
        ai = AtomicInteger(0)
        def worker():
            for _ in range(n):
                ai.increment()
        threads = [threading.Thread(target=worker) for _ in range(4)]
        start = time.perf_counter()
        for t in threads: t.start()
        for t in threads: t.join()
        return time.perf_counter() - start

    n = 5000
    t_lock = bench_lock_based(n)
    t_free = bench_lock_free(n)
    print(f"\n  ベンチマーク ({n}回 x 4スレッド):")
    print(f"    Lock-Based: {t_lock:.4f}秒")
    print(f"    Lock-Free:  {t_free:.4f}秒")
    print(f"    ※ Python GIL 下では差が出にくい。C/Java では Lock-Free が有利な場合が多い")


# ============================================================================
# 4. 並行パターン
# ============================================================================

def section_concurrency_patterns():
    print("\n=== 並行パターン ===\n")

    # --- 4a. Producer-Consumer (Bounded Buffer) ---
    print("  [Producer-Consumer]")
    buffer = queue.Queue(maxsize=5)
    total_items = 20
    produced_items = []
    consumed_items = []
    c_lock = threading.Lock()

    def producer_pc(pid, count):
        for i in range(count):
            item = f"P{pid}-{i}"
            buffer.put(item)  # maxsize に達したらブロック
            produced_items.append(item)

    def consumer_pc(cid, count):
        for _ in range(count):
            item = buffer.get()
            with c_lock:
                consumed_items.append(item)
            buffer.task_done()

    tp = threading.Thread(target=producer_pc, args=(0, total_items))
    tc = threading.Thread(target=consumer_pc, args=(0, total_items))
    tp.start(); tc.start()
    tp.join(); tc.join()
    print(f"    produced={len(produced_items)}, consumed={len(consumed_items)}")

    # --- 4b. Reader-Writer (書者優先版) ---
    print("\n  [Reader-Writer: 書者優先]")

    class WriterPreferredRWLock:
        """
        書者優先の ReadWriteLock。
        書者が待っている間、新しい読者はブロックされる。
        """
        def __init__(self):
            self._readers = 0
            self._writers = 0
            self._write_waiters = 0
            self._lock = threading.Lock()
            self._read_ok = threading.Condition(self._lock)
            self._write_ok = threading.Condition(self._lock)

        def read_acquire(self):
            with self._read_ok:
                # 書者が実行中 or 書者が待っている間は読者をブロック
                while self._writers > 0 or self._write_waiters > 0:
                    self._read_ok.wait()
                self._readers += 1

        def read_release(self):
            with self._read_ok:
                self._readers -= 1
                if self._readers == 0:
                    self._write_ok.notify()

        def write_acquire(self):
            with self._write_ok:
                self._write_waiters += 1
                while self._readers > 0 or self._writers > 0:
                    self._write_ok.wait()
                self._write_waiters -= 1
                self._writers += 1

        def write_release(self):
            with self._write_ok:
                self._writers -= 1
                self._write_ok.notify()         # 次の書者を起こす
                self._read_ok.notify_all()      # 読者も起こす

    wp_rw = WriterPreferredRWLock()
    wp_log = []
    wp_lock = threading.Lock()

    def wp_reader(rid):
        wp_rw.read_acquire()
        with wp_lock:
            wp_log.append(f"R{rid}")
        time.sleep(0.005)
        wp_rw.read_release()

    def wp_writer(wid):
        wp_rw.write_acquire()
        with wp_lock:
            wp_log.append(f"W{wid}")
        time.sleep(0.005)
        wp_rw.write_release()

    threads = []
    for i in range(3): threads.append(threading.Thread(target=wp_reader, args=(i,)))
    threads.append(threading.Thread(target=wp_writer, args=(0,)))
    for i in range(3, 5): threads.append(threading.Thread(target=wp_reader, args=(i,)))
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"    操作順序: {wp_log}")

    # --- 4c. Dining Philosophers (3戦略) ---
    print("\n  [Dining Philosophers: デッドロック回避3戦略]")

    NUM_PHILOSOPHERS = 5
    forks = [threading.Lock() for _ in range(NUM_PHILOSOPHERS)]

    # 戦略1: Resource Ordering (フォークに番号を付け、小さい方から取る)
    def philosopher_ordered(pid, eat_count):
        left = pid
        right = (pid + 1) % NUM_PHILOSOPHERS
        first, second = (min(left, right), max(left, right))
        meals = 0
        for _ in range(eat_count):
            forks[first].acquire()
            forks[second].acquire()
            meals += 1  # 食事中
            forks[second].release()
            forks[first].release()
        return meals

    threads = []
    results_ph = [0] * NUM_PHILOSOPHERS
    def phil_worker(pid):
        results_ph[pid] = philosopher_ordered(pid, 10)
    for i in range(NUM_PHILOSOPHERS):
        threads.append(threading.Thread(target=phil_worker, args=(i,)))
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"    戦略1 (Resource Ordering): meals={results_ph} (全員10回)")

    # 戦略2: Try-Lock (trylock で取れなければ両方解放してリトライ)
    # 戦略3: Arbitrator (ウェイターがフォークを管理)
    print("""    戦略2 (Try-Lock): trylock 失敗時に両方解放してリトライ
    戦略3 (Arbitrator): 中央のウェイターが許可 → 最大 N-1 人まで同時着席""")

    # --- 4d. Actor Model ---
    print("\n  [Actor Model: メッセージパッシング]")

    class Actor:
        """
        Actor: 各アクターが専用の mailbox (queue) を持ち、
        メッセージ受信でのみ状態を変更する。共有メモリなし。
        """
        def __init__(self, name):
            self.name = name
            self.mailbox = queue.Queue()
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        def _run(self):
            while self._running:
                try:
                    msg = self.mailbox.get(timeout=0.1)
                    self.on_receive(msg)
                except queue.Empty:
                    continue

        def on_receive(self, msg):
            """サブクラスでオーバーライド"""
            pass

        def send(self, msg):
            self.mailbox.put(msg)

        def stop(self):
            self._running = False
            self._thread.join(timeout=1)

    class CounterActor(Actor):
        def __init__(self, name):
            self.count = 0
            self.results = []
            super().__init__(name)

        def on_receive(self, msg):
            if msg == "increment":
                self.count += 1
            elif msg == "get":
                self.results.append(self.count)

    counter_actor = CounterActor("counter")
    for _ in range(100):
        counter_actor.send("increment")
    counter_actor.send("get")
    time.sleep(0.3)
    counter_actor.stop()
    print(f"    Actor count={counter_actor.count} (期待値: 100)")

    # --- 4e. CSP (Go の channel モデル) ---
    print("\n  [CSP: Channel ベースの通信]")

    class Channel:
        """
        Go の channel を模倣。
        送信側と受信側が同期する (unbuffered) or バッファリング。
        """
        def __init__(self, capacity=0):
            self._queue = queue.Queue(maxsize=max(capacity, 1))
            self._closed = False

        def send(self, value):
            if self._closed:
                raise RuntimeError("send on closed channel")
            self._queue.put(value)

        def recv(self):
            try:
                return self._queue.get(timeout=1), True
            except queue.Empty:
                return None, False

        def close(self):
            self._closed = True

    ch = Channel(capacity=5)
    ch_results = []

    def ch_producer():
        for i in range(10):
            ch.send(i)
        ch.close()

    def ch_consumer():
        while True:
            val, ok = ch.recv()
            if not ok:
                break
            ch_results.append(val)

    tp = threading.Thread(target=ch_producer)
    tc = threading.Thread(target=ch_consumer)
    tp.start(); tc.start()
    tp.join(); tc.join()
    print(f"    Channel: received={ch_results}")

    # --- 4f. Fork-Join (分割統治の並列化) ---
    print("\n  [Fork-Join: 並列マージソート]")

    def parallel_merge_sort(arr, pool, depth=0, max_depth=2):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        if depth < max_depth:
            # Fork: 左半分を別スレッドで処理
            future_left = pool.submit(
                parallel_merge_sort, arr[:mid], pool, depth + 1, max_depth)
            right = parallel_merge_sort(arr[mid:], pool, depth + 1, max_depth)
            left = future_left.result()  # Join
        else:
            left = sorted(arr[:mid])
            right = sorted(arr[mid:])
        # Merge
        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i]); i += 1
            else:
                merged.append(right[j]); j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged

    data = [random.randint(0, 999) for _ in range(100)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        sorted_data = parallel_merge_sort(data, pool)
    print(f"    Fork-Join sort: sorted={sorted_data == sorted(data)}, len={len(sorted_data)}")


# ============================================================================
# 5. デッドロック (検出 + 回避)
# ============================================================================

def section_deadlock():
    print("\n=== デッドロック ===\n")

    # --- Coffman の4条件 ---
    print("""  ■ デッドロックの4条件 (Coffman, 1971):
    1. Mutual Exclusion: リソースは排他的に使用
    2. Hold and Wait: リソースを保持しながら別のリソースを待つ
    3. No Preemption: リソースは強制的に奪えない
    4. Circular Wait: 循環的な待ちが存在
    → 1つでも崩せばデッドロックは発生しない
    """)

    # --- 5a. Wait-for Graph によるデッドロック検出 ---
    class DeadlockDetector:
        """
        Wait-for Graph を構築し、サイクル検出でデッドロックを発見。
        """
        def __init__(self):
            # thread_id -> set of thread_ids it's waiting for
            self._wait_for = defaultdict(set)
            self._lock = threading.Lock()

        def add_wait(self, waiter, holder):
            """waiter が holder の持つリソースを待っている"""
            with self._lock:
                self._wait_for[waiter].add(holder)

        def remove_wait(self, waiter, holder):
            with self._lock:
                self._wait_for[waiter].discard(holder)
                if not self._wait_for[waiter]:
                    del self._wait_for[waiter]

        def detect_cycle(self) -> list:
            """DFS でサイクルを検出。サイクルのノードリストを返す。"""
            with self._lock:
                visited = set()
                rec_stack = set()
                path = []

                def dfs(node):
                    visited.add(node)
                    rec_stack.add(node)
                    path.append(node)
                    for neighbor in self._wait_for.get(node, set()):
                        if neighbor not in visited:
                            cycle = dfs(neighbor)
                            if cycle is not None:
                                return cycle
                        elif neighbor in rec_stack:
                            # サイクル発見
                            idx = path.index(neighbor)
                            return path[idx:]
                    path.pop()
                    rec_stack.discard(node)
                    return None

                for node in list(self._wait_for.keys()):
                    if node not in visited:
                        cycle = dfs(node)
                        if cycle:
                            return cycle
                return []

    detector = DeadlockDetector()
    # デッドロック状況をシミュレート: T1→T2→T3→T1
    detector.add_wait("T1", "T2")
    detector.add_wait("T2", "T3")
    detector.add_wait("T3", "T1")
    cycle = detector.detect_cycle()
    print(f"  Wait-for Graph サイクル検出: {cycle}")

    # サイクルなし
    detector2 = DeadlockDetector()
    detector2.add_wait("T1", "T2")
    detector2.add_wait("T2", "T3")
    cycle2 = detector2.detect_cycle()
    print(f"  サイクルなし: {cycle2}")

    # --- 5b. Lock Ordering ---
    print("\n  [Lock Ordering: ロックに全順序を付ける]")

    class OrderedLockManager:
        """ロックを ID 順に取得することでデッドロックを回避。"""
        def __init__(self, num_locks):
            self.locks = {i: threading.Lock() for i in range(num_locks)}

        def acquire_multiple(self, *lock_ids):
            """昇順にロックを取得"""
            for lid in sorted(lock_ids):
                self.locks[lid].acquire()

        def release_multiple(self, *lock_ids):
            """降順にロックを解放"""
            for lid in sorted(lock_ids, reverse=True):
                self.locks[lid].release()

    olm = OrderedLockManager(5)
    deadlock_free_count = [0]

    def ordered_worker(w_id, locks_needed):
        for _ in range(100):
            olm.acquire_multiple(*locks_needed)
            deadlock_free_count[0] += 1
            olm.release_multiple(*locks_needed)

    t1 = threading.Thread(target=ordered_worker, args=(0, [0, 1, 2]))
    t2 = threading.Thread(target=ordered_worker, args=(1, [2, 1, 0]))  # 逆順でも OK
    t1.start(); t2.start()
    t1.join(); t2.join()
    print(f"    Lock Ordering: {deadlock_free_count[0]} 回成功 (デッドロックなし)")

    # --- 5c. Try-Lock with Timeout ---
    print("\n  [Try-Lock with Timeout]")

    lock_a = threading.Lock()
    lock_b = threading.Lock()
    trylock_success = [0]

    def trylock_worker(first, second, wid):
        for _ in range(100):
            acquired_first = first.acquire(timeout=0.01)
            if not acquired_first:
                continue
            acquired_second = second.acquire(timeout=0.01)
            if not acquired_second:
                first.release()  # 持っているロックを解放してリトライ
                continue
            trylock_success[0] += 1
            second.release()
            first.release()

    t1 = threading.Thread(target=trylock_worker, args=(lock_a, lock_b, 0))
    t2 = threading.Thread(target=trylock_worker, args=(lock_b, lock_a, 1))
    t1.start(); t2.start()
    t1.join(); t2.join()
    print(f"    Try-Lock: {trylock_success[0]} 回成功")

    # --- Banker's Algorithm 概念 ---
    print("""
  ■ Banker's Algorithm (銀行家のアルゴリズム):
    - リソース割り当て前に「安全状態」かチェック
    - 安全状態: 全プロセスが完了可能な実行順序が存在
    - 実用性: オーバーヘッドが大きく、実システムではほぼ使われない
    - 学術的意義: デッドロック回避の理論的基盤
    """)

    # --- 5d. Livelock ---
    print("  [Livelock の例]")
    print("""    Livelock: スレッドが互いに譲り合い続けて進まない状態
    例: 廊下で2人がすれ違おうとして同じ方向に避け続ける
    対策: ランダムなバックオフ (Ethernet の CSMA/CD と同じ原理)""")


# ============================================================================
# 6. async/await vs Thread vs Process
# ============================================================================

def section_async_vs_thread_vs_process():
    print("\n=== async/await vs Thread vs Process ===\n")

    # --- 6a. I/O-bound 比較 ---
    print("  [I/O-bound ワークロード比較]")

    def io_task_sync(task_id, duration=0.05):
        time.sleep(duration)  # I/O シミュレーション
        return task_id

    async def io_task_async(task_id, duration=0.05):
        await asyncio.sleep(duration)
        return task_id

    num_tasks = 50

    # 逐次実行
    start = time.perf_counter()
    for i in range(num_tasks):
        io_task_sync(i)
    sequential_time = time.perf_counter() - start

    # threading
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        list(ex.map(io_task_sync, range(num_tasks)))
    thread_time = time.perf_counter() - start

    # asyncio
    async def run_async_io():
        tasks = [io_task_async(i) for i in range(num_tasks)]
        return await asyncio.gather(*tasks)

    start = time.perf_counter()
    asyncio.run(run_async_io())
    async_time = time.perf_counter() - start

    print(f"    逐次:     {sequential_time:.3f}秒")
    print(f"    Thread:   {thread_time:.3f}秒")
    print(f"    asyncio:  {async_time:.3f}秒")
    print(f"    → I/O-bound では asyncio が軽量で高速")

    # --- 6b. CPU-bound 比較 ---
    print("\n  [CPU-bound ワークロード比較]")

    def cpu_task(n):
        """CPU集約タスク: 素数判定"""
        total = 0
        for i in range(2, n):
            if all(i % j != 0 for j in range(2, int(i**0.5) + 1)):
                total += 1
        return total

    n = 3000

    # 逐次
    start = time.perf_counter()
    for _ in range(4):
        cpu_task(n)
    seq_cpu = time.perf_counter() - start

    # threading (GIL で並列化されない)
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, [n]*4))
    thread_cpu = time.perf_counter() - start

    # multiprocessing
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, [n]*4))
    process_cpu = time.perf_counter() - start

    print(f"    逐次:            {seq_cpu:.3f}秒")
    print(f"    Thread (GIL):    {thread_cpu:.3f}秒")
    print(f"    Process:         {process_cpu:.3f}秒")
    print(f"    → CPU-bound では multiprocessing が真の並列化")

    # --- 6c. Mixed workload ---
    print("\n  [Mixed workload: ThreadPool + ProcessPool]")
    print("""    パターン: ProcessPoolExecutor で CPU 処理
               ThreadPoolExecutor で I/O 処理
               asyncio で全体のオーケストレーション""")

    # --- 6d. Event Loop 内部動作 ---
    print("""
  ■ Event Loop の仕組み:
    while True:
        events = epoll.wait()      # I/O イベントを待つ
        for event in events:
            callback = registry[event.fd]
            callback(event)         # コールバックを実行
        run_scheduled_callbacks()   # タイマー系コールバック

    - select: 古い (O(n) でFDをスキャン)
    - poll:   select の改良 (FD数制限なし)
    - epoll:  Linux 最適 (O(1) でイベント通知)
    - kqueue: macOS/BSD 版 epoll
    """)

    # --- 6e. Coroutine の仕組み ---
    print("  [Coroutine の仕組み: generator → async]")

    # Step 1: generator ベースのコルーチン (旧スタイル)
    def old_style_coroutine():
        """generator を使った協調的マルチタスク"""
        result = yield "step1"
        result = yield f"step2 (received: {result})"
        yield "step3"

    gen = old_style_coroutine()
    s1 = next(gen)           # "step1"
    s2 = gen.send("data")    # "step2 (received: data)"
    s3 = gen.send(None)      # "step3"
    print(f"    Generator coroutine: {s1} → {s2} → {s3}")

    # Step 2: async/await (現在のスタイル)
    async def modern_coroutine():
        await asyncio.sleep(0)
        return "async result"

    result = asyncio.run(modern_coroutine())
    print(f"    async/await: {result}")
    print("""    内部: async def は coroutine オブジェクトを返す
           await で制御を event loop に返す (yield と同じ原理)""")


# ============================================================================
# 7. 並行バグのパターン
# ============================================================================

def section_concurrency_bugs():
    print("\n=== 並行バグのパターン ===\n")

    # --- 7a. Race Condition (TOCTOU) ---
    print("  [Race Condition: TOCTOU]")

    class BankAccount:
        """TOCTOU (Time Of Check to Time Of Use) バグの例"""
        def __init__(self, balance):
            self.balance = balance

        def withdraw_unsafe(self, amount):
            """チェックと更新の間に別スレッドが割り込む可能性"""
            if self.balance >= amount:      # TOCTOU: Check
                time.sleep(0.001)           # ← ここで別スレッドが実行
                self.balance -= amount      # TOCTOU: Use
                return True
            return False

        def withdraw_safe(self, amount, lock):
            """ロックで保護"""
            with lock:
                if self.balance >= amount:
                    self.balance -= amount
                    return True
                return False

    # TOCTOU デモ
    account = BankAccount(100)
    results = []

    def withdraw_worker(acc, amount):
        success = acc.withdraw_unsafe(amount)
        results.append(("success" if success else "fail", acc.balance))

    t1 = threading.Thread(target=withdraw_worker, args=(account, 80))
    t2 = threading.Thread(target=withdraw_worker, args=(account, 80))
    t1.start(); t2.start()
    t1.join(); t2.join()
    print(f"    TOCTOU: 残高={account.balance} (マイナスになる可能性あり)")
    print(f"    結果: {results}")

    # --- 7b. Data Race vs Race Condition ---
    print("""
  ■ Data Race vs Race Condition:
    - Data Race: 2つのスレッドが同じメモリに同時アクセスし、
                 少なくとも1つが書き込み (未定義動作)
    - Race Condition: タイミングにより結果が変わるロジックバグ
                      (Data Race がなくても起こりうる)

    例: Data Race なし + Race Condition あり
      lock.acquire(); tmp = balance; lock.release()
      lock.acquire(); balance = tmp - amount; lock.release()
      → 各操作はアトミックだが、間に別スレッドが割り込む
    """)

    # --- 7c. Priority Inversion ---
    print("  [Priority Inversion]")
    print("""    Mars Pathfinder (1997) の事例:
      1. 低優先度タスクがバスロックを取得
      2. 高優先度タスクがバスロックを待つ (ブロック)
      3. 中優先度タスクが低優先度タスクをプリエンプト
      4. 高優先度タスクがスターベーション → ウォッチドッグリセット

    対策:
      - Priority Inheritance: ロック保持者の優先度を引き上げ
      - Priority Ceiling: ロックに最大優先度を設定
    """)

    # Priority Inversion シミュレーション
    shared_lock = threading.Lock()
    pi_log = []
    pi_log_lock = threading.Lock()

    def low_priority_task():
        shared_lock.acquire()
        with pi_log_lock: pi_log.append("Low: lock acquired")
        time.sleep(0.05)  # 長時間ロック保持
        with pi_log_lock: pi_log.append("Low: releasing lock")
        shared_lock.release()

    def high_priority_task():
        time.sleep(0.01)  # 少し遅れて開始
        with pi_log_lock: pi_log.append("High: waiting for lock")
        shared_lock.acquire()
        with pi_log_lock: pi_log.append("High: lock acquired")
        shared_lock.release()

    t_low = threading.Thread(target=low_priority_task)
    t_high = threading.Thread(target=high_priority_task)
    t_low.start(); t_high.start()
    t_low.join(); t_high.join()
    print(f"    Priority Inversion ログ: {pi_log}")

    # --- 7d. Starvation ---
    print("""
  ■ Starvation (飢餓):
    - 優先度の低いスレッドが永遠にリソースを得られない
    - 読者優先の RWLock で書者が飢餓状態になる例
    - 対策: 公平なスケジューリング (FIFO ロック)
    """)

    # --- 7e. Thundering Herd ---
    print("  [Thundering Herd]")

    class ThunderingHerdDemo:
        """
        Thundering Herd: Condition.notify_all() で大量のスレッドが
        同時に起床し、1つだけが成功して残りは再度スリープ。
        """
        def __init__(self):
            self.resource_ready = False
            self.lock = threading.Lock()
            self.cond = threading.Condition(self.lock)
            self.wakeup_count = 0
            self.success_count = 0

        def wait_for_resource(self, tid):
            with self.cond:
                while not self.resource_ready:
                    self.cond.wait()
                self.wakeup_count += 1
                # 最初の1スレッドだけがリソースを使える
                if self.resource_ready:
                    self.resource_ready = False
                    self.success_count += 1

        def signal_resource(self):
            with self.cond:
                self.resource_ready = True
                self.cond.notify_all()  # 全員起こす → Thundering Herd!
                # 対策: notify() で1つだけ起こす

    th_demo = ThunderingHerdDemo()
    th_threads = [
        threading.Thread(target=th_demo.wait_for_resource, args=(i,))
        for i in range(10)
    ]
    for t in th_threads: t.start()
    time.sleep(0.05)
    th_demo.signal_resource()
    time.sleep(0.1)
    # 残りのスレッドを解放するためにリソースを追加提供
    for _ in range(9):
        with th_demo.cond:
            th_demo.resource_ready = True
            th_demo.cond.notify_all()
        time.sleep(0.01)
    for t in th_threads: t.join()
    print(f"    Thundering Herd: wakeups={th_demo.wakeup_count}, "
          f"success={th_demo.success_count}")
    print(f"    対策: notify_all() → notify() に変更して1スレッドだけ起こす")


# ============================================================================
# 8. 優先度マップ (Tier 1-4)
# ============================================================================

def section_priority_map():
    print("\n=== 並行処理 優先度マップ ===\n")

    tiers = {
        "Tier 1 (最優先 ― 実務で毎日使う)": [
            "threading.Lock / RLock / Condition の使い方",
            "Race Condition の理解と回避",
            "asyncio (async/await) の基本と Event Loop",
            "Producer-Consumer パターン (queue.Queue)",
            "ThreadPoolExecutor / ProcessPoolExecutor の使い分け",
            "GIL の理解 (CPU-bound → multiprocessing)",
        ],
        "Tier 2 (重要 ― 設計判断に必要)": [
            "デッドロックの4条件と回避戦略 (Lock Ordering)",
            "Reader-Writer Lock (読者/書者問題)",
            "Semaphore / Barrier / CountDownLatch",
            "Actor Model / CSP パターン",
            "I/O-bound vs CPU-bound の判別と最適化",
            "TOCTOU バグの検出と防止",
        ],
        "Tier 3 (差別化 ― シニアエンジニアの武器)": [
            "メモリモデル (happens-before, Sequential Consistency)",
            "Lock-Free データ構造 (CAS, Treiber Stack)",
            "ABA問題と対策 (Tagged Pointer, Hazard Pointer)",
            "Wait-for Graph によるデッドロック検出",
            "Fork-Join パターン (分割統治の並列化)",
            "Priority Inversion と対策",
        ],
        "Tier 4 (専門知識 ― 特定領域で必要)": [
            "Memory Barrier / Fence (CPU アーキテクチャ依存)",
            "Wait-Free アルゴリズム",
            "Banker's Algorithm",
            "Michael-Scott Queue",
            "Epoch-Based Reclamation",
            "Thundering Herd の根本対策 (epoll + EPOLLEXCLUSIVE)",
        ],
    }

    for tier, items in tiers.items():
        print(f"  {tier}:")
        for item in items:
            print(f"    - {item}")
        print()

    print("  学習ロードマップ:")
    print("    Week 1-2: Tier 1 (threading, asyncio, queue)")
    print("    Week 3-4: Tier 2 (デッドロック, パターン, 同期プリミティブ)")
    print("    Week 5-6: Tier 3 (メモリモデル, Lock-Free, Fork-Join)")
    print("    Week 7+:  Tier 4 (必要に応じて深掘り)")

    # --- 面接頻出トピック ---
    print("""
  ■ 面接頻出トピック:
    Q: Thread と Process の違いは？
    A: Thread はメモリ空間共有 (軽量、同期が必要)
       Process は独立メモリ空間 (重い、IPC が必要)

    Q: デッドロックをどう防ぐ？
    A: Lock Ordering (全ロックに順序付け) が最も実用的。
       Try-lock + timeout でリカバリも可能。

    Q: Python で CPU-bound を並列化するには？
    A: multiprocessing or concurrent.futures.ProcessPoolExecutor
       GIL のため threading では並列化されない。

    Q: async/await と threading の使い分けは？
    A: I/O-bound → async/await (コルーチン、軽量)
       CPU-bound → multiprocessing
       ブロッキング I/O → threading
    """)


# ============================================================================
# メイン実行
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print(" 並行処理 & 並列処理 ディープガイド")
    print(" Concurrency & Parallelism Deep Dive")
    print("=" * 70)

    section_memory_model()
    section_sync_primitives()
    section_lock_free()
    section_concurrency_patterns()
    section_deadlock()
    section_async_vs_thread_vs_process()
    section_concurrency_bugs()
    section_priority_map()

    print("\n" + "=" * 70)
    print(" 完了! すべてのセクションを実行しました。")
    print("=" * 70)
