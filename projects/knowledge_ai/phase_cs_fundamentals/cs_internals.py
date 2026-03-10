#!/usr/bin/env python3
"""
CS Internals Deep Dive — OS・ネットワーク・DB内部・並行処理・GC

FAANG Staff+ 面接で問われるCS基盤知識を実装ベースで理解する。
「なぜそうなっているのか」を説明できるレベルを目指す。

実行: python cs_internals.py
依存: Python 3.9+ 標準ライブラリのみ
"""

import hashlib
import heapq
import math
import random
import struct
import threading
import time
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Chapter 1: Operating Systems Internals
# ============================================================

def chapter1_os_internals():
    print("=" * 70)
    print("Chapter 1: Operating Systems Internals")
    print("  プロセス・メモリ・I/O — すべての基盤")
    print("=" * 70)

    # --- 1.1 Process Scheduler ---
    print("\n" + "─" * 60)
    print("1.1 CPU スケジューラ実装")
    print("─" * 60)

    @dataclass
    class Process:
        pid: int
        name: str
        burst_time: int      # CPU実行時間
        arrival_time: int    # 到着時刻
        priority: int = 0    # 小さいほど高優先
        remaining: int = 0
        completion: int = 0
        waiting: int = 0

        def __post_init__(self):
            self.remaining = self.burst_time

    def round_robin(processes: List[Process], quantum: int = 2) -> List[Tuple[str, int, int]]:
        """Round Robin スケジューリング"""
        queue = deque()
        timeline = []
        procs = sorted(processes, key=lambda p: p.arrival_time)
        current_time = 0
        idx = 0
        remaining = {p.pid: p.burst_time for p in procs}

        while idx < len(procs) or queue:
            # 到着したプロセスをキューに追加
            while idx < len(procs) and procs[idx].arrival_time <= current_time:
                queue.append(procs[idx])
                idx += 1

            if not queue:
                current_time = procs[idx].arrival_time if idx < len(procs) else current_time + 1
                continue

            proc = queue.popleft()
            exec_time = min(quantum, remaining[proc.pid])
            timeline.append((proc.name, current_time, current_time + exec_time))
            current_time += exec_time
            remaining[proc.pid] -= exec_time

            # 新しく到着したプロセスを先に追加
            while idx < len(procs) and procs[idx].arrival_time <= current_time:
                queue.append(procs[idx])
                idx += 1

            if remaining[proc.pid] > 0:
                queue.append(proc)
            else:
                proc.completion = current_time
                proc.waiting = proc.completion - proc.arrival_time - proc.burst_time

        return timeline

    procs = [
        Process(1, "P1", burst_time=6, arrival_time=0),
        Process(2, "P2", burst_time=4, arrival_time=1),
        Process(3, "P3", burst_time=2, arrival_time=2),
        Process(4, "P4", burst_time=3, arrival_time=3),
    ]

    print("\n  Round Robin (quantum=2):")
    print(f"  {'Process':<8} {'Arrival':>8} {'Burst':>6}")
    for p in procs:
        print(f"  {p.name:<8} {p.arrival_time:>8} {p.burst_time:>6}")

    timeline = round_robin(procs, quantum=2)
    print("\n  Gantt Chart:")
    gantt = "  |"
    for name, start, end in timeline:
        width = (end - start) * 3
        gantt += f"{name:^{width}}|"
    print(gantt)

    times = "  "
    prev_end = 0
    for name, start, end in timeline:
        if start == prev_end:
            times += f"{start:<3}" + " " * ((end - start) * 3 - 3)
        prev_end = end
    times += str(timeline[-1][2])
    print(times)

    avg_waiting = sum(p.waiting for p in procs) / len(procs)
    print(f"\n  Average Waiting Time: {avg_waiting:.1f}")

    print("""
    ★ スケジューリングアルゴリズム比較:
    ┌──────────────────┬──────────┬──────────┬──────────────┐
    │ Algorithm         │ Preemptive│ Starvation│ 用途          │
    ├──────────────────┼──────────┼──────────┼──────────────┤
    │ FCFS              │ No       │ No       │ バッチ処理     │
    │ SJF               │ No       │ Yes      │ 平均待ち最小   │
    │ SRTF (SJF+割込)   │ Yes      │ Yes      │ 理論最適       │
    │ Round Robin       │ Yes      │ No       │ タイムシェア   │
    │ Priority          │ Yes      │ Yes      │ リアルタイム   │
    │ MLFQ              │ Yes      │ No       │ Linux/macOS   │
    └──────────────────┴──────────┴──────────┴──────────────┘

    Linux CFS (Completely Fair Scheduler):
    - Red-Black Tree でプロセスを管理
    - vruntime (仮想実行時間) が最小のプロセスを次に実行
    - nice 値で重み付け: nice -20 (最高優先) → nice +19 (最低)
    """)

    # --- 1.2 Virtual Memory ---
    print("─" * 60)
    print("1.2 仮想メモリ: ページテーブル & TLB シミュレーション")
    print("─" * 60)

    class PageTable:
        """簡易ページテーブル + LRU ページ置換"""
        def __init__(self, num_frames: int):
            self.num_frames = num_frames
            self.frames: OrderedDict = OrderedDict()  # page_num → frame_num
            self.page_faults = 0
            self.tlb_hits = 0
            self.tlb_misses = 0
            self.tlb: OrderedDict = OrderedDict()  # 4エントリのTLB
            self.tlb_size = 4
            self.next_frame = 0

        def access(self, page_num: int) -> Tuple[str, int]:
            # TLB check
            if page_num in self.tlb:
                self.tlb_hits += 1
                self.tlb.move_to_end(page_num)
                return "TLB_HIT", self.tlb[page_num]

            self.tlb_misses += 1

            # Page table check
            if page_num in self.frames:
                self.frames.move_to_end(page_num)
                frame = self.frames[page_num]
                self._update_tlb(page_num, frame)
                return "PAGE_HIT", frame

            # Page fault
            self.page_faults += 1
            if len(self.frames) >= self.num_frames:
                # LRU eviction
                evicted_page, _ = self.frames.popitem(last=False)
                if evicted_page in self.tlb:
                    del self.tlb[evicted_page]

            frame = self.next_frame
            self.next_frame += 1
            self.frames[page_num] = frame
            self._update_tlb(page_num, frame)
            return "PAGE_FAULT", frame

        def _update_tlb(self, page_num: int, frame: int):
            if len(self.tlb) >= self.tlb_size:
                self.tlb.popitem(last=False)
            self.tlb[page_num] = frame

    pt = PageTable(num_frames=4)
    # Reference string: typical exam sequence
    references = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]

    print(f"\n  Physical frames: {pt.num_frames}, TLB entries: {pt.tlb_size}")
    print(f"  Reference string: {references}")
    print(f"\n  {'Page':>5} {'Result':<12} {'Frame':>6} {'Frames in Memory'}")
    print("  " + "-" * 50)

    for page in references:
        result, frame = pt.access(page)
        frames_str = str(list(pt.frames.keys()))
        print(f"  {page:>5} {result:<12} {frame:>6} {frames_str}")

    total = len(references)
    print(f"\n  Page Faults:  {pt.page_faults}/{total} ({pt.page_faults/total*100:.0f}%)")
    print(f"  TLB Hit Rate: {pt.tlb_hits}/{total} ({pt.tlb_hits/total*100:.0f}%)")

    print("""
    ★ 面接で聞かれるポイント:
    - TLB (Translation Lookaside Buffer): ページテーブルのキャッシュ
    - ページフォルト時: ディスクI/O → ~10ms (CPUサイクルの100万倍)
    - Thrashing: フレーム不足でページフォルト連発 → 性能崩壊
    - Working Set: プロセスが頻繁にアクセスするページ集合
    - Belady's Anomaly: フレーム増やしてもFault増えることがある (FIFO)
      → LRU では起きない (Stack Algorithm)
    """)

    # --- 1.3 Memory Allocator ---
    print("─" * 60)
    print("1.3 メモリアロケータ: Buddy System")
    print("─" * 60)

    class BuddyAllocator:
        """Buddy System メモリアロケータ"""
        def __init__(self, total_size: int):
            self.total = total_size
            self.max_order = int(math.log2(total_size))
            # free_lists[order] = list of free blocks of size 2^order
            self.free_lists: Dict[int, List[int]] = {i: [] for i in range(self.max_order + 1)}
            self.free_lists[self.max_order] = [0]  # 1つの大きなブロック
            self.allocated: Dict[int, int] = {}  # addr → order

        def alloc(self, size: int) -> Optional[int]:
            order = max(0, math.ceil(math.log2(size))) if size > 1 else 0
            # 適切なサイズの空きブロックを探す
            for o in range(order, self.max_order + 1):
                if self.free_lists[o]:
                    addr = self.free_lists[o].pop(0)
                    # 大きすぎるブロックを分割
                    while o > order:
                        o -= 1
                        buddy_addr = addr + (1 << o)
                        self.free_lists[o].append(buddy_addr)
                    self.allocated[addr] = order
                    return addr
            return None  # Out of memory

        def free(self, addr: int):
            if addr not in self.allocated:
                return
            order = self.allocated.pop(addr)
            # バディと統合
            while order < self.max_order:
                buddy = addr ^ (1 << order)
                if buddy in self.free_lists.get(order, []):
                    self.free_lists[order].remove(buddy)
                    addr = min(addr, buddy)
                    order += 1
                else:
                    break
            self.free_lists[order].append(addr)

    alloc = BuddyAllocator(64)
    print("\n  Buddy System (64 bytes total):")
    ops = [
        ("alloc", 8), ("alloc", 4), ("alloc", 16),
        ("free", None), ("alloc", 8),
    ]

    addresses = []
    for op, size in ops:
        if op == "alloc":
            addr = alloc.alloc(size)
            addresses.append(addr)
            print(f"    alloc({size}) → addr={addr} (block=2^{alloc.allocated.get(addr, '?')}={1 << alloc.allocated.get(addr, 0)})")
        else:
            freed = addresses[0]
            alloc.free(freed)
            print(f"    free(addr={freed})")

    print("""
    Buddy System の特徴:
    - 分割: 要求サイズに合うまで2分割 (2^n のサイズのみ)
    - 統合: 解放時にバディ(隣接する同サイズブロック)と自動統合
    - 内部断片化: 最大50% (7bytes要求 → 8bytes割当)
    - 外部断片化: なし (統合で解消)
    - Linux kernel の物理メモリ管理で使用

    ★ malloc の実際の実装 (glibc):
    - 小さい割当 (< 128KB): sbrk() でヒープ拡張、bins で管理
    - 大きい割当 (>= 128KB): mmap() で直接マッピング
    - tcmalloc (Google): スレッドごとのキャッシュで高速化
    - jemalloc (Meta): サイズクラス + arena でスケーラブル
    """)

    # --- 1.4 I/O Models ---
    print("─" * 60)
    print("1.4 I/O モデル (Unix の 5つの I/O モデル)")
    print("─" * 60)
    print("""
    1. Blocking I/O (同期ブロッキング)
       Application    Kernel
       ──────────    ──────────
       read() ──────→ wait for data...
                      data ready
                    ← copy to user
       ← return
       → 最もシンプル、スレッド数 = 同時接続数

    2. Non-blocking I/O (同期ノンブロッキング)
       read() ──────→ no data → EAGAIN
       read() ──────→ no data → EAGAIN  (busy loop = CPU浪費)
       read() ──────→ data ready → copy → return
       → 単独ではほぼ使わない

    3. I/O Multiplexing (select/poll/epoll)
       select() ────→ wait for ANY fd ready
                    ← fd 3 is ready
       read(fd3) ──→ copy → return
       → 1スレッドで数千接続を処理 (Nginx, Node.js, Redis)

       select vs poll vs epoll:
       ┌────────┬──────────┬──────────────┬──────────────┐
       │         │ select    │ poll          │ epoll         │
       ├────────┼──────────┼──────────────┼──────────────┤
       │ fd上限  │ 1024      │ 無制限        │ 無制限        │
       │ 計算量  │ O(n)      │ O(n)          │ O(1) amortized│
       │ fd渡し  │ 毎回コピー │ 毎回コピー    │ カーネル管理   │
       │ macOS   │ ✓         │ ✓             │ ✗ (kqueue)   │
       │ Linux   │ ✓         │ ✓             │ ✓            │
       └────────┴──────────┴──────────────┴──────────────┘

    4. Signal-driven I/O
       → SIGIO シグナルで通知、実用上はほぼ使わない

    5. Asynchronous I/O (AIO / io_uring)
       aio_read() ──→ return immediately
       ... do other work ...
       signal/callback ← data is ready in user buffer
       → カーネルがコピーまで完了、真の非同期
       → Linux io_uring (2019〜): 高性能非同期I/O

    ★ 面接での答え方:
    「Nginx は epoll (Level-Triggered) で I/O 多重化、
     Node.js は libuv (epoll/kqueue の抽象化) でイベントループ、
     Go は goroutine + netpoller (epoll) でM:N スケジューリング」
    """)

    # --- 1.5 Deadlock ---
    print("─" * 60)
    print("1.5 デッドロック検出: Resource Allocation Graph")
    print("─" * 60)

    def detect_deadlock(
        processes: List[str],
        resources: List[str],
        holds: List[Tuple[str, str]],     # (process, resource)
        waits: List[Tuple[str, str]],     # (process, resource)
    ) -> Optional[List[str]]:
        """Wait-For Graph でデッドロック検出 (サイクル検出)"""
        # Build wait-for graph: P1 waits R → R held by P2 → P1 → P2 edge
        resource_holder = {}
        for proc, res in holds:
            resource_holder[res] = proc

        # Wait-for graph (process → process)
        wait_for: Dict[str, List[str]] = defaultdict(list)
        for proc, res in waits:
            if res in resource_holder:
                holder = resource_holder[res]
                if holder != proc:
                    wait_for[proc].append(holder)

        # DFS cycle detection
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in wait_for.get(node, []):
                if neighbor not in visited:
                    result = dfs(neighbor)
                    if result:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.discard(node)
            return None

        for proc in processes:
            if proc not in visited:
                cycle = dfs(proc)
                if cycle:
                    return cycle
        return None

    print("\n  Scenario: Dining Philosophers (simplified)")
    holds = [("P1", "R1"), ("P2", "R2"), ("P3", "R3")]
    waits = [("P1", "R2"), ("P2", "R3"), ("P3", "R1")]

    print("    P1 holds R1, waits R2")
    print("    P2 holds R2, waits R3")
    print("    P3 holds R3, waits R1")

    cycle = detect_deadlock(
        ["P1", "P2", "P3"], ["R1", "R2", "R3"], holds, waits
    )
    print(f"\n  Deadlock detected: {' → '.join(cycle)}" if cycle else "  No deadlock")

    print("""
    デッドロックの4条件 (Coffman conditions):
    1. Mutual Exclusion (排他制御)
    2. Hold and Wait (保持と待機)
    3. No Preemption (横取り不可)
    4. Circular Wait (循環待ち)
    → 1つでも崩せばデッドロックは発生しない

    Prevention strategies:
    - Resource ordering: R1 < R2 < R3 の順でしか取得しない
    - Lock timeout: タイムアウトで解放 (データベースの一般的手法)
    - Banker's algorithm: 安全状態かチェックしてからalloc (理論的)
    """)


# ============================================================
# Chapter 2: Networking Deep Dive
# ============================================================

def chapter2_networking():
    print("\n" + "=" * 70)
    print("Chapter 2: Networking Deep Dive")
    print("  TCP/IP・HTTP/2・TLS — 全ての通信の基盤")
    print("=" * 70)

    # --- 2.1 TCP State Machine ---
    print("\n" + "─" * 60)
    print("2.1 TCP ステートマシン")
    print("─" * 60)

    class TCPState(Enum):
        CLOSED = auto()
        LISTEN = auto()
        SYN_SENT = auto()
        SYN_RECEIVED = auto()
        ESTABLISHED = auto()
        FIN_WAIT_1 = auto()
        FIN_WAIT_2 = auto()
        TIME_WAIT = auto()
        CLOSE_WAIT = auto()
        LAST_ACK = auto()

    class TCPConnection:
        def __init__(self, name: str):
            self.name = name
            self.state = TCPState.CLOSED
            self.seq = random.randint(1000, 9999)
            self.ack = 0
            self.log = []

        def _transition(self, new_state: TCPState, action: str):
            old = self.state
            self.state = new_state
            self.log.append(f"{self.name}: {old.name} → {new_state.name} ({action})")

    # 3-way handshake simulation
    client = TCPConnection("Client")
    server = TCPConnection("Server")

    # Server: LISTEN
    server._transition(TCPState.LISTEN, "passive open")

    # Client → Server: SYN
    client._transition(TCPState.SYN_SENT, f"send SYN seq={client.seq}")
    server.ack = client.seq + 1
    server._transition(TCPState.SYN_RECEIVED, f"recv SYN, send SYN-ACK seq={server.seq} ack={server.ack}")

    # Client: recv SYN-ACK
    client.ack = server.seq + 1
    client._transition(TCPState.ESTABLISHED, f"recv SYN-ACK, send ACK ack={client.ack}")
    server._transition(TCPState.ESTABLISHED, "recv ACK")

    # Connection close (4-way)
    client._transition(TCPState.FIN_WAIT_1, "send FIN")
    server._transition(TCPState.CLOSE_WAIT, "recv FIN, send ACK")
    client._transition(TCPState.FIN_WAIT_2, "recv ACK")
    server._transition(TCPState.LAST_ACK, "send FIN")
    client._transition(TCPState.TIME_WAIT, "recv FIN, send ACK (wait 2MSL)")
    server._transition(TCPState.CLOSED, "recv ACK")

    print("\n  3-Way Handshake + 4-Way Close:")
    for entry in client.log + server.log:
        print(f"    {entry}")

    print("""
    ★ TIME_WAIT (2MSL = 2 × Maximum Segment Lifetime):
    - なぜ必要？ 最後のACKが失われた場合に再送できるため
    - 問題: 高トラフィックサーバーで TIME_WAIT ソケットが溜まる
    - 対策: SO_REUSEADDR, tcp_tw_reuse (Linux)

    ★ TCP vs UDP:
    ┌──────────┬──────────────────┬──────────────────┐
    │           │ TCP               │ UDP               │
    ├──────────┼──────────────────┼──────────────────┤
    │ 接続      │ コネクション型     │ コネクションレス   │
    │ 信頼性    │ 再送・順序保証     │ なし (ベストエフォート)│
    │ ヘッダ    │ 20+ bytes         │ 8 bytes           │
    │ 用途      │ HTTP, DB, SSH     │ DNS, 動画, ゲーム  │
    │ 輻輳制御  │ あり              │ なし               │
    └──────────┴──────────────────┴──────────────────┘
    """)

    # --- 2.2 TCP Congestion Control ---
    print("─" * 60)
    print("2.2 TCP 輻輳制御シミュレーション")
    print("─" * 60)

    def simulate_congestion_control(rounds: int = 20) -> List[Tuple[int, float, str]]:
        cwnd = 1.0        # Congestion Window (MSS単位)
        ssthresh = 16.0   # Slow Start Threshold
        history = []
        phase = "Slow Start"

        for t in range(rounds):
            if cwnd < ssthresh:
                phase = "Slow Start"
                cwnd *= 2  # 指数増加
            else:
                phase = "Congestion Avoidance"
                cwnd += 1  # 線形増加

            # Simulate packet loss at cwnd=24
            if cwnd >= 24 and t > 5:
                history.append((t, cwnd, f"{phase} → LOSS"))
                ssthresh = cwnd / 2
                cwnd = 1  # Tahoe (1に戻る) / Reno なら ssthresh に
                phase = "Fast Recovery"
                continue

            history.append((t, cwnd, phase))

        return history

    history = simulate_congestion_control()
    print("\n  AIMD (Additive Increase, Multiplicative Decrease):")
    print(f"  {'Round':>6} {'cwnd':>8} {'Phase'}")
    print("  " + "-" * 45)
    for t, cwnd, phase in history[:16]:
        bar = "█" * min(int(cwnd), 40)
        print(f"  {t:>6} {cwnd:>8.0f} {bar} {phase}")

    print("""
    輻輳制御アルゴリズムの進化:
    - Tahoe (1988): Loss → cwnd=1, Slow Start から再開
    - Reno  (1990): Fast Recovery, Loss → cwnd=ssthresh/2
    - CUBIC (2008): Linux デフォルト, 3次関数で cwnd 増加
    - BBR   (2016): Google, 帯域幅とRTTを推定して最適化
      → 従来: ロスベース (パケット落ちてから減速)
      → BBR: モデルベース (帯域推定に基づき制御)
    """)

    # --- 2.3 HTTP/1.1 vs HTTP/2 vs HTTP/3 ---
    print("─" * 60)
    print("2.3 HTTP バージョン比較")
    print("─" * 60)
    print("""
    HTTP/1.1 の Head-of-Line Blocking:
    ┌──────────┐     ┌──────────┐
    │ Browser   │     │ Server   │
    │           │     │          │
    │ GET /a ──→│     │          │  1つのTCPで
    │ (wait...) │     │←── /a    │  1リクエスト/レスポンスずつ
    │ GET /b ──→│     │          │  → 遅いレスポンスが後続をブロック
    │ (wait...) │     │←── /b    │
    └──────────┘     └──────────┘
    → 対策: 6並列TCP接続 (ブラウザ), ドメインシャーディング

    HTTP/2 のストリーム多重化:
    ┌──────────┐     ┌──────────┐
    │ Browser   │     │ Server   │
    │           │     │          │  1つのTCPで
    │ Stream 1 ←→ GET /a        │  複数ストリームを多重化
    │ Stream 3 ←→ GET /b        │  → アプリ層の HoL は解消
    │ Stream 5 ←→ GET /c        │  → TCP層の HoL は残る
    └──────────┘     └──────────┘

    HTTP/2 の追加機能:
    - HPACK: ヘッダ圧縮 (Huffman + 動的テーブル)
    - Server Push: リクエスト前にリソースをプッシュ
    - Stream Priority: 優先度付きリソース配信

    HTTP/3 (QUIC):
    ┌──────────┐     ┌──────────┐
    │ Browser   │     │ Server   │
    │           │     │          │  UDP上のQUICプロトコル
    │ Stream 1 ←→ independent   │  ストリーム間で独立
    │ Stream 3 ←→ independent   │  → TCP層の HoL も解消
    │ Stream 5 ←→ independent   │  → 0-RTT接続確立
    └──────────┘     └──────────┘

    ┌────────────┬──────────┬──────────┬──────────┐
    │             │ HTTP/1.1  │ HTTP/2    │ HTTP/3    │
    ├────────────┼──────────┼──────────┼──────────┤
    │ Transport   │ TCP       │ TCP       │ QUIC(UDP) │
    │ Multiplexing│ No        │ Yes       │ Yes       │
    │ Header圧縮  │ No        │ HPACK     │ QPACK     │
    │ HoL Blocking│ App+TCP   │ TCP only  │ None      │
    │ 接続確立    │ 1-3 RTT   │ 1-3 RTT   │ 0-1 RTT   │
    │ TLS        │ Optional  │ Optional  │ Built-in  │
    └────────────┴──────────┴──────────┴──────────┘
    """)

    # --- 2.4 DNS Resolution ---
    print("─" * 60)
    print("2.4 DNS 解決シミュレーション")
    print("─" * 60)

    @dataclass
    class DNSRecord:
        name: str
        record_type: str  # A, AAAA, CNAME, NS, MX
        value: str
        ttl: int

    class DNSResolver:
        def __init__(self):
            self.cache: Dict[str, Tuple[DNSRecord, float]] = {}
            self.queries = 0
            # Simulated DNS hierarchy
            self.root_servers = {"com.": "ns.com", "org.": "ns.org"}
            self.tld_servers = {
                "google.com.": "ns.google.com",
                "example.com.": "ns.example.com",
            }
            self.auth_servers = {
                "www.google.com.": DNSRecord("www.google.com.", "A", "142.250.80.4", 300),
                "api.google.com.": DNSRecord("api.google.com.", "A", "142.250.80.5", 60),
            }

        def resolve(self, name: str) -> Tuple[Optional[DNSRecord], List[str]]:
            steps = []
            # Check cache
            if name in self.cache:
                record, expiry = self.cache[name]
                if time.time() < expiry:
                    steps.append(f"Cache HIT: {name} → {record.value} (TTL remaining)")
                    return record, steps
                else:
                    del self.cache[name]
                    steps.append(f"Cache EXPIRED: {name}")

            # Recursive resolution
            self.queries += 1
            steps.append(f"1. Query Root Server (.)")
            for tld, ns in self.root_servers.items():
                if name.endswith(tld):
                    steps.append(f"   Root → TLD NS: {ns}")
                    break

            steps.append(f"2. Query TLD Server (.com)")
            domain = ".".join(name.split(".")[-3:]) + "."
            if domain in self.tld_servers:
                steps.append(f"   TLD → Auth NS: {self.tld_servers[domain]}")

            steps.append(f"3. Query Authoritative Server")
            full = name + "." if not name.endswith(".") else name
            if full in self.auth_servers:
                record = self.auth_servers[full]
                self.cache[name] = (record, time.time() + record.ttl)
                steps.append(f"   Auth → {record.value} (TTL={record.ttl}s)")
                return record, steps

            steps.append(f"   NXDOMAIN (not found)")
            return None, steps

    resolver = DNSResolver()
    for domain in ["www.google.com", "www.google.com", "api.google.com"]:
        record, steps = resolver.resolve(domain)
        print(f"\n  Resolving: {domain}")
        for step in steps:
            print(f"    {step}")

    print("""
    ★ DNS の重要概念:
    - 再帰クエリ: クライアント→リゾルバ (リゾルバが全部やる)
    - 反復クエリ: リゾルバ→各サーバー (参照を返す)
    - Anycast: 同じIPを複数拠点に、最寄りのサーバーに到達
    - DNS over HTTPS (DoH): プライバシー保護、ポート443
    - TTL設計: 短い(60s)=柔軟だがクエリ増、長い(86400s)=効率的だが変更遅い
    """)

    # --- 2.5 Load Balancing ---
    print("─" * 60)
    print("2.5 ロードバランシングアルゴリズム")
    print("─" * 60)

    class LoadBalancer:
        def __init__(self, servers: List[Tuple[str, int]]):
            """servers: [(name, weight)]"""
            self.servers = servers
            self.rr_index = 0
            self.connections = {name: 0 for name, _ in servers}

        def round_robin(self) -> str:
            server = self.servers[self.rr_index % len(self.servers)][0]
            self.rr_index += 1
            return server

        def weighted_round_robin(self) -> str:
            expanded = []
            for name, weight in self.servers:
                expanded.extend([name] * weight)
            server = expanded[self.rr_index % len(expanded)]
            self.rr_index += 1
            return server

        def least_connections(self) -> str:
            min_conn = min(self.connections.values())
            for name, _ in self.servers:
                if self.connections[name] == min_conn:
                    self.connections[name] += 1
                    return name
            return self.servers[0][0]

        def ip_hash(self, client_ip: str) -> str:
            h = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
            idx = h % len(self.servers)
            return self.servers[idx][0]

    lb = LoadBalancer([("web-1", 3), ("web-2", 2), ("web-3", 1)])

    print("\n  Servers: web-1 (weight=3), web-2 (weight=2), web-3 (weight=1)")
    print("\n  Weighted Round Robin (12 requests):")
    dist = defaultdict(int)
    for i in range(12):
        server = lb.weighted_round_robin()
        dist[server] += 1
    for name, count in sorted(dist.items()):
        bar = "█" * count
        print(f"    {name}: {count} {bar}")

    print("""
    ┌────────────────────┬────────────────────────────────┐
    │ Algorithm           │ 特徴                            │
    ├────────────────────┼────────────────────────────────┤
    │ Round Robin         │ シンプル、均等分散               │
    │ Weighted RR         │ サーバー性能差を考慮             │
    │ Least Connections   │ 動的負荷に適応                  │
    │ IP Hash             │ セッション維持 (Sticky)          │
    │ Consistent Hashing  │ サーバー増減時の再分散が最小     │
    │ Random              │ シンプル、大量サーバーで有効     │
    │ Power of 2 Choices  │ ランダム2台から少ない方を選択   │
    └────────────────────┴────────────────────────────────┘

    L4 vs L7 Load Balancer:
    - L4 (Transport): IP+Port で振り分け、高速 (AWS NLB)
    - L7 (Application): URL/Header で振り分け、柔軟 (AWS ALB, Nginx)
    """)


# ============================================================
# Chapter 3: Database Internals
# ============================================================

def chapter3_db_internals():
    print("\n" + "=" * 70)
    print("Chapter 3: Database Internals")
    print("  B-Tree・LSM-Tree・MVCC — DBの中身を理解する")
    print("=" * 70)

    # --- 3.1 B-Tree ---
    print("\n" + "─" * 60)
    print("3.1 B-Tree 実装")
    print("─" * 60)

    class BTreeNode:
        def __init__(self, leaf: bool = True):
            self.keys: List[int] = []
            self.children: List['BTreeNode'] = []
            self.leaf = leaf

    class BTree:
        """B-Tree (order=3: 各ノード最大2キー, 最小1キー)"""
        def __init__(self, order: int = 3):
            self.root = BTreeNode()
            self.order = order
            self.max_keys = order - 1

        def search(self, key: int, node: Optional[BTreeNode] = None) -> bool:
            node = node or self.root
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            if i < len(node.keys) and key == node.keys[i]:
                return True
            if node.leaf:
                return False
            return self.search(key, node.children[i])

        def insert(self, key: int):
            root = self.root
            if len(root.keys) == self.max_keys:
                new_root = BTreeNode(leaf=False)
                new_root.children.append(root)
                self._split(new_root, 0)
                self.root = new_root
            self._insert_non_full(self.root, key)

        def _insert_non_full(self, node: BTreeNode, key: int):
            i = len(node.keys) - 1
            if node.leaf:
                node.keys.append(0)
                while i >= 0 and key < node.keys[i]:
                    node.keys[i + 1] = node.keys[i]
                    i -= 1
                node.keys[i + 1] = key
            else:
                while i >= 0 and key < node.keys[i]:
                    i -= 1
                i += 1
                if len(node.children[i].keys) == self.max_keys:
                    self._split(node, i)
                    if key > node.keys[i]:
                        i += 1
                self._insert_non_full(node.children[i], key)

        def _split(self, parent: BTreeNode, idx: int):
            child = parent.children[idx]
            mid = len(child.keys) // 2
            new_node = BTreeNode(leaf=child.leaf)
            parent.keys.insert(idx, child.keys[mid])
            parent.children.insert(idx + 1, new_node)
            new_node.keys = child.keys[mid + 1:]
            child.keys = child.keys[:mid]
            if not child.leaf:
                new_node.children = child.children[mid + 1:]
                child.children = child.children[:mid + 1]

        def print_tree(self, node: Optional[BTreeNode] = None, level: int = 0):
            node = node or self.root
            indent = "    " * level
            print(f"{indent}[{', '.join(map(str, node.keys))}]")
            for child in node.children:
                self.print_tree(child, level + 1)

    btree = BTree(order=3)
    keys = [10, 20, 5, 6, 12, 30, 7, 17]
    print(f"\n  Inserting: {keys}")
    for k in keys:
        btree.insert(k)

    print("\n  B-Tree structure:")
    btree.print_tree()

    print(f"\n  Search 12: {btree.search(12)}")
    print(f"  Search 15: {btree.search(15)}")

    print("""
    B-Tree vs B+ Tree:
    ┌──────────────┬──────────────────┬──────────────────┐
    │               │ B-Tree            │ B+ Tree           │
    ├──────────────┼──────────────────┼──────────────────┤
    │ データ格納    │ 全ノード          │ リーフのみ         │
    │ リーフ連結    │ なし              │ リンクドリスト     │
    │ 範囲検索      │ 遅い (木を走査)   │ 速い (リーフ走査)  │
    │ ディスクI/O  │ 多い              │ 少ない (ファンアウト大)│
    │ 使用例       │ MongoDB           │ MySQL InnoDB, PostgreSQL│
    └──────────────┴──────────────────┴──────────────────┘

    ★ B+ Tree が DB で好まれる理由:
    1. 高いファンアウト → 木の深さが浅い → ディスクI/O少ない
    2. リーフの連結 → 範囲クエリ (WHERE x BETWEEN 10 AND 20) が高速
    3. 内部ノードにデータなし → メモリに載りやすい
    """)

    # --- 3.2 LSM-Tree ---
    print("─" * 60)
    print("3.2 LSM-Tree (Log-Structured Merge-Tree)")
    print("─" * 60)

    class LSMTree:
        """簡易 LSM-Tree: MemTable → SSTable flush → Compaction"""
        def __init__(self, memtable_limit: int = 4):
            self.memtable: Dict[str, Optional[str]] = {}  # sorted in-memory
            self.memtable_limit = memtable_limit
            self.sstables: List[Dict[str, Optional[str]]] = []  # L0 SSTables
            self.wal: List[Tuple[str, Optional[str]]] = []  # Write-Ahead Log

        def put(self, key: str, value: str) -> str:
            self.wal.append((key, value))
            self.memtable[key] = value
            if len(self.memtable) >= self.memtable_limit:
                return self._flush()
            return f"PUT {key}={value}"

        def delete(self, key: str) -> str:
            self.wal.append((key, None))
            self.memtable[key] = None  # tombstone
            return f"DELETE {key} (tombstone)"

        def get(self, key: str) -> Tuple[Optional[str], str]:
            # 1. Check MemTable
            if key in self.memtable:
                val = self.memtable[key]
                if val is None:
                    return None, "MemTable (tombstone → deleted)"
                return val, "MemTable (HIT)"

            # 2. Check SSTables (newest first)
            for i, sst in enumerate(reversed(self.sstables)):
                if key in sst:
                    val = sst[key]
                    if val is None:
                        return None, f"SSTable-L{len(self.sstables)-1-i} (tombstone)"
                    return val, f"SSTable-L{len(self.sstables)-1-i} (HIT)"

            return None, "NOT FOUND"

        def _flush(self) -> str:
            sorted_data = dict(sorted(self.memtable.items()))
            self.sstables.append(sorted_data)
            result = f"FLUSH MemTable → SSTable-L{len(self.sstables)-1} ({len(sorted_data)} keys)"
            self.memtable = {}
            self.wal = []

            # Auto-compact if too many SSTables
            if len(self.sstables) >= 3:
                self._compact()
                result += " + COMPACTION"
            return result

        def _compact(self):
            merged: Dict[str, Optional[str]] = {}
            for sst in self.sstables:
                merged.update(sst)
            # Remove tombstones during compaction
            merged = {k: v for k, v in merged.items() if v is not None}
            self.sstables = [dict(sorted(merged.items()))]

    lsm = LSMTree(memtable_limit=3)
    ops = [
        ("put", "user:1", "Alice"),
        ("put", "user:2", "Bob"),
        ("put", "user:3", "Charlie"),  # triggers flush
        ("put", "user:1", "Alice_v2"),
        ("get", "user:1", None),
        ("delete", "user:2", None),
        ("get", "user:2", None),
        ("put", "user:4", "Dave"),
        ("put", "user:5", "Eve"),  # triggers flush
    ]

    print("\n  LSM-Tree Operations:")
    for op, key, val in ops:
        if op == "put":
            result = lsm.put(key, val)
            print(f"    {result}")
        elif op == "get":
            value, location = lsm.get(key)
            print(f"    GET {key} → {value} ({location})")
        elif op == "delete":
            result = lsm.delete(key)
            print(f"    {result}")

    print("""
    LSM-Tree の特徴:
    - Write 最適化: 全ての書き込みはシーケンシャル (WAL + MemTable)
    - Read: MemTable → L0 → L1 → ... (Bloom Filter で高速化)
    - Compaction: SSTable をマージ → tombstone 削除、read 高速化
      - Size-Tiered (STCS): 同サイズのSSTableをマージ (Cassandra default)
      - Leveled (LCS): レベルごとにサイズ制限 (RocksDB default)
    - Write Amplification: 同じデータが複数回書かれる (compactionのため)

    B-Tree vs LSM-Tree:
    ┌──────────────┬──────────────────┬──────────────────┐
    │               │ B-Tree            │ LSM-Tree          │
    ├──────────────┼──────────────────┼──────────────────┤
    │ Write         │ ランダムI/O       │ シーケンシャルI/O  │
    │ Read          │ O(log n)          │ 複数レベル走査     │
    │ Space         │ 断片化あり        │ コンパクト          │
    │ 使用例       │ MySQL, PostgreSQL │ Cassandra, RocksDB │
    └──────────────┴──────────────────┴──────────────────┘
    """)

    # --- 3.3 MVCC ---
    print("─" * 60)
    print("3.3 MVCC (Multi-Version Concurrency Control)")
    print("─" * 60)

    @dataclass
    class Version:
        value: Any
        txn_id: int       # 作成したトランザクション
        created_at: int   # タイムスタンプ
        deleted_at: Optional[int] = None

    class MVCCStore:
        """Snapshot Isolation ベースの MVCC"""
        def __init__(self):
            self.versions: Dict[str, List[Version]] = defaultdict(list)
            self.next_txn = 1
            self.next_ts = 1
            self.active_txns: Dict[int, int] = {}  # txn_id → snapshot_ts

        def begin(self) -> int:
            txn_id = self.next_txn
            self.next_txn += 1
            snapshot_ts = self.next_ts
            self.active_txns[txn_id] = snapshot_ts
            return txn_id

        def read(self, txn_id: int, key: str) -> Optional[Any]:
            snapshot = self.active_txns[txn_id]
            versions = self.versions.get(key, [])
            # 自分のスナップショット時点で見えるバージョンを探す
            for v in reversed(versions):
                if v.created_at <= snapshot and (v.deleted_at is None or v.deleted_at > snapshot):
                    return v.value
            return None

        def write(self, txn_id: int, key: str, value: Any):
            ts = self.next_ts
            self.next_ts += 1
            self.versions[key].append(Version(value, txn_id, ts))

        def commit(self, txn_id: int):
            del self.active_txns[txn_id]

    store = MVCCStore()

    # Demonstrate snapshot isolation
    print("\n  Snapshot Isolation デモ:")
    print("    T1: begin → write x=10 → commit")
    print("    T2: begin (before T1 commit) → read x → ???")

    t1 = store.begin()
    t2 = store.begin()  # T2 starts before T1 commits

    store.write(t1, "x", 10)
    store.commit(t1)

    val = store.read(t2, "x")
    print(f"\n    T2 reads x = {val}")
    print("    → T2 は T1 の書き込みを見えない (Snapshot Isolation)")
    print("    → T2 のスナップショットは T1 commit 前だから")

    t3 = store.begin()  # T3 starts after T1 commits
    val3 = store.read(t3, "x")
    print(f"\n    T3 (after T1 commit) reads x = {val3}")
    print("    → T3 は T1 の書き込みが見える")

    print("""
    Transaction Isolation Levels:
    ┌────────────────────┬────────┬──────────┬─────────┬──────────┐
    │ Level               │Dirty   │Non-repeat│Phantom  │Write Skew│
    │                     │Read    │able Read │Read     │          │
    ├────────────────────┼────────┼──────────┼─────────┼──────────┤
    │ Read Uncommitted    │ ✗      │ ✗        │ ✗       │ ✗        │
    │ Read Committed      │ ✓      │ ✗        │ ✗       │ ✗        │
    │ Repeatable Read     │ ✓      │ ✓        │ ✗       │ ✗        │
    │ Snapshot Isolation  │ ✓      │ ✓        │ ✓       │ ✗        │
    │ Serializable        │ ✓      │ ✓        │ ✓       │ ✓        │
    └────────────────────┴────────┴──────────┴─────────┴──────────┘
    ✓ = prevented, ✗ = possible

    Write Skew の例:
    - 医師2人がオンコール、最低1人必要
    - T1: 「2人いるから自分は外れよう」→ UPDATE set oncall=false WHERE id=1
    - T2: 「2人いるから自分は外れよう」→ UPDATE set oncall=false WHERE id=2
    - 結果: 0人になる (Snapshot Isolation では防げない)
    - 対策: SELECT FOR UPDATE, Serializable Snapshot Isolation (SSI)
    """)

    # --- 3.4 WAL ---
    print("─" * 60)
    print("3.4 Write-Ahead Log (WAL)")
    print("─" * 60)
    print("""
    WAL の原則: データを変更する前に、変更内容をログに書く。

    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Client    │───→│ WAL      │───→│ Data Page │
    │ (INSERT)  │    │ (disk)   │    │ (memory)  │
    └──────────┘    └──────────┘    └──────────┘
                     ↓ fsync()        ↓ checkpoint
                    永続化保証        遅延書き込み

    Crash Recovery:
    1. WAL をスキャン
    2. committed だがデータページに反映されてない → REDO
    3. uncommitted でデータページに書かれてしまった → UNDO
    → ARIES アルゴリズム (Analysis, Redo, Undo)

    PostgreSQL の WAL:
    - WAL segment: 16MB ファイル
    - LSN (Log Sequence Number): WAL 内の位置
    - Replication: WAL を replica に送信 (Streaming Replication)
    - Point-in-Time Recovery: WAL をリプレイして任意時点に復元

    ★ 面接で聞かれるポイント:
    Q: 「なぜ直接データファイルに書かないのか？」
    A: 「データページの更新はランダムI/O。WALはシーケンシャルI/Oで
       高速。また、部分書き込み(torn write)からも保護される。
       1回のトランザクションで複数ページを更新する場合、
       WALなしではアトミック性を保証できない。」
    """)


# ============================================================
# Chapter 4: Concurrency & Parallelism
# ============================================================

def chapter4_concurrency():
    print("\n" + "=" * 70)
    print("Chapter 4: Concurrency & Parallelism")
    print("  ロック・ロックフリー・CAS — 正しく並行処理を書く")
    print("=" * 70)

    # --- 4.1 Lock implementations ---
    print("\n" + "─" * 60)
    print("4.1 ロック実装の比較")
    print("─" * 60)

    class SpinLock:
        """スピンロック: ビジーウェイト (CPUを浪費するが低レイテンシ)"""
        def __init__(self):
            self._locked = False
            self._real_lock = threading.Lock()

        def acquire(self):
            while True:
                with self._real_lock:
                    if not self._locked:
                        self._locked = True
                        return

        def release(self):
            with self._real_lock:
                self._locked = False

    print("""
    ┌──────────────┬──────────────────────────────────────────┐
    │ Lock Type     │ 特徴                                      │
    ├──────────────┼──────────────────────────────────────────┤
    │ Spinlock      │ ビジーウェイト、短いCS向け、コンテキスト切替なし│
    │ Mutex         │ スリープ、長いCS向け、カーネル介入あり       │
    │ RWLock        │ 読み取り並行、書き込み排他                  │
    │ Semaphore     │ N個同時アクセス (リソースプール)             │
    │ Condition Var │ 条件を満たすまで待機 (Producer-Consumer)     │
    └──────────────┴──────────────────────────────────────────┘

    CS = Critical Section (臨界領域)

    いつどれを使うか:
    - Spinlock: マイクロ秒以下のCS、マルチコア、カーネル内
    - Mutex: ミリ秒以上のCS、ユーザースペース
    - RWLock: 読み取り >> 書き込み (キャッシュ, 設定)
    - Semaphore: コネクションプール (max=10 など)
    """)

    # --- 4.2 Lock-Free Stack (CAS) ---
    print("─" * 60)
    print("4.2 Lock-Free データ構造 (Compare-And-Swap)")
    print("─" * 60)

    class LockFreeStack:
        """CAS ベースのロックフリースタック (シミュレーション)"""
        def __init__(self):
            self._head: Optional[List] = None  # [value, next]
            self._lock = threading.Lock()  # CAS のシミュレーション用
            self.cas_retries = 0

        def _cas(self, expected, new_val) -> bool:
            """Compare-And-Swap: atomic operation のシミュレーション"""
            with self._lock:
                if self._head is expected:
                    self._head = new_val
                    return True
                self.cas_retries += 1
                return False

        def push(self, value):
            while True:
                old_head = self._head
                new_node = [value, old_head]
                if self._cas(old_head, new_node):
                    return

        def pop(self) -> Optional[Any]:
            while True:
                old_head = self._head
                if old_head is None:
                    return None
                new_head = old_head[1]
                if self._cas(old_head, new_head):
                    return old_head[0]

    stack = LockFreeStack()
    for v in [1, 2, 3, 4, 5]:
        stack.push(v)
    print(f"\n  Lock-Free Stack: pushed 1,2,3,4,5")
    results = []
    for _ in range(5):
        results.append(stack.pop())
    print(f"  Popped: {results}")
    print(f"  CAS retries: {stack.cas_retries}")

    print("""
    CAS (Compare-And-Swap):
    ┌─────────────────────────────────────────┐
    │ CAS(addr, expected, new):                │
    │   atomic {                               │
    │     if *addr == expected:                 │
    │       *addr = new                        │
    │       return true                        │
    │     else:                                │
    │       return false  // 他スレッドが変更済 │
    │   }                                      │
    └─────────────────────────────────────────┘

    ABA 問題:
    - Thread 1: read A, prepare CAS(A→C)
    - Thread 2: change A→B→A  (元に戻った!)
    - Thread 1: CAS succeeds (Aに見えるから) → 危険
    - 対策: Tagged pointer (バージョン番号を付与)

    Lock-Free vs Lock-Based:
    - Lock-Free: デッドロックなし、Priority Inversion なし
    - Lock-Free: 実装が複雑、ABA問題、メモリ管理が困難
    - 実用: java.util.concurrent, C++ <atomic>, Go sync/atomic
    """)

    # --- 4.3 Thread Pool ---
    print("─" * 60)
    print("4.3 スレッドプール & Work Stealing")
    print("─" * 60)
    print("""
    Thread Pool アーキテクチャ:

    ┌─────────────────────────────────────────────┐
    │                Task Queue                    │
    │  [Task1] [Task2] [Task3] [Task4] [Task5]    │
    └─────────────────┬───────────────────────────┘
                      │ dequeue
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    ┌───────┐    ┌───────┐    ┌───────┐
    │Worker 1│    │Worker 2│    │Worker 3│
    │(Thread)│    │(Thread)│    │(Thread)│
    └───────┘    └───────┘    └───────┘

    Work Stealing (Java ForkJoinPool):
    - 各ワーカーが自分のデキュー(両端キュー)を持つ
    - 自分のキューが空 → 他のワーカーのキューから steal
    - LIFO で自分のタスク実行、FIFO で他から steal
    → キャッシュ局所性 + 負荷分散を両立

    サイズ設計:
    - CPU-bound: threads = CPU cores (or cores + 1)
    - I/O-bound: threads = CPU cores × (1 + wait_time/compute_time)
    - 例: 4 cores, I/O 80%/CPU 20% → 4 × (1 + 4) = 20 threads

    Python の制約:
    - GIL: CPU-bound は threading で並列化できない
    - 対策: multiprocessing, C拡張, asyncio (I/O-bound)
    """)

    # --- 4.4 Concurrency Patterns ---
    print("─" * 60)
    print("4.4 並行処理パターン")
    print("─" * 60)
    print("""
    1. Producer-Consumer (Bounded Buffer)
       ┌──────────┐   ┌─────────┐   ┌──────────┐
       │ Producer  │──→│ Queue   │──→│ Consumer  │
       │ (produce) │   │ (N=10)  │   │ (consume) │
       └──────────┘   └─────────┘   └──────────┘
       - Queue満 → Producerブロック
       - Queue空 → Consumerブロック
       - Python: queue.Queue (thread-safe)

    2. Reader-Writer Lock
       - 複数Reader同時OK、Writer排他
       - Writer starvation に注意
       → Write-preferring or Fair lock

    3. Double-Checked Locking (Singleton)
       if instance is None:         # 1st check (no lock)
           with lock:
               if instance is None:  # 2nd check (with lock)
                   instance = create()
       → Java: volatile, Python: threading.Lock

    4. Read-Copy-Update (RCU)
       - Read: ロックなし、古いバージョンを読む可能性
       - Update: コピー→変更→ポインタ差し替え (atomic)
       - 古いバージョンの解放: Grace Period 後
       → Linux kernel で多用 (routing table, etc.)

    5. Actor Model (Erlang, Akka)
       - 各Actor: 独自のstate + mailbox
       - 共有状態なし → ロック不要
       - メッセージパッシングで通信
       → Erlang/OTP: 10万+の軽量プロセス
    """)


# ============================================================
# Chapter 5: Compiler & Runtime Internals
# ============================================================

def chapter5_runtime():
    print("\n" + "=" * 70)
    print("Chapter 5: Compiler & Runtime Internals")
    print("  Pythonの中身・GC・JIT — 言語の裏側を理解する")
    print("=" * 70)

    # --- 5.1 Lexer + Parser ---
    print("\n" + "─" * 60)
    print("5.1 簡易コンパイラ: Lexer → Parser → AST → 評価")
    print("─" * 60)

    class TokenType(Enum):
        NUMBER = auto()
        PLUS = auto()
        MINUS = auto()
        STAR = auto()
        SLASH = auto()
        LPAREN = auto()
        RPAREN = auto()
        EOF = auto()

    @dataclass
    class Token:
        type: TokenType
        value: Any

    def lexer(text: str) -> List[Token]:
        tokens = []
        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
            elif text[i].isdigit():
                j = i
                while j < len(text) and (text[j].isdigit() or text[j] == '.'):
                    j += 1
                tokens.append(Token(TokenType.NUMBER, float(text[i:j])))
                i = j
            elif text[i] == '+': tokens.append(Token(TokenType.PLUS, '+')); i += 1
            elif text[i] == '-': tokens.append(Token(TokenType.MINUS, '-')); i += 1
            elif text[i] == '*': tokens.append(Token(TokenType.STAR, '*')); i += 1
            elif text[i] == '/': tokens.append(Token(TokenType.SLASH, '/')); i += 1
            elif text[i] == '(': tokens.append(Token(TokenType.LPAREN, '(')); i += 1
            elif text[i] == ')': tokens.append(Token(TokenType.RPAREN, ')')); i += 1
            else:
                raise ValueError(f"Unexpected character: {text[i]}")
        tokens.append(Token(TokenType.EOF, None))
        return tokens

    class Parser:
        """Recursive Descent Parser (演算子の優先度を再帰で表現)"""
        def __init__(self, tokens: List[Token]):
            self.tokens = tokens
            self.pos = 0

        def parse(self) -> Any:
            result = self.expr()
            return result

        def expr(self) -> Any:
            """expr = term (('+' | '-') term)*"""
            result = self.term()
            while self.current().type in (TokenType.PLUS, TokenType.MINUS):
                op = self.current().type
                self.advance()
                right = self.term()
                if op == TokenType.PLUS:
                    result = ('+', result, right)
                else:
                    result = ('-', result, right)
            return result

        def term(self) -> Any:
            """term = factor (('*' | '/') factor)*"""
            result = self.factor()
            while self.current().type in (TokenType.STAR, TokenType.SLASH):
                op = self.current().type
                self.advance()
                right = self.factor()
                if op == TokenType.STAR:
                    result = ('*', result, right)
                else:
                    result = ('/', result, right)
            return result

        def factor(self) -> Any:
            """factor = NUMBER | '(' expr ')'"""
            if self.current().type == TokenType.NUMBER:
                val = self.current().value
                self.advance()
                return val
            elif self.current().type == TokenType.LPAREN:
                self.advance()
                result = self.expr()
                self.advance()  # skip RPAREN
                return result
            raise ValueError(f"Unexpected token: {self.current()}")

        def current(self) -> Token:
            return self.tokens[self.pos]

        def advance(self):
            self.pos += 1

    def evaluate(ast) -> float:
        if isinstance(ast, (int, float)):
            return ast
        op, left, right = ast
        l, r = evaluate(left), evaluate(right)
        if op == '+': return l + r
        if op == '-': return l - r
        if op == '*': return l * r
        if op == '/': return l / r
        raise ValueError(f"Unknown op: {op}")

    def format_ast(ast, indent: int = 0) -> str:
        prefix = "  " * indent
        if isinstance(ast, (int, float)):
            return f"{prefix}{ast}"
        op, left, right = ast
        return f"{prefix}({op}\n{format_ast(left, indent+1)}\n{format_ast(right, indent+1)})"

    expr = "(2 + 3) * 4 - 6 / 2"
    tokens = lexer(expr)
    ast = Parser(tokens).parse()
    result = evaluate(ast)

    print(f"\n  Expression: {expr}")
    print(f"\n  Tokens: {[(t.type.name, t.value) for t in tokens if t.type != TokenType.EOF]}")
    print(f"\n  AST:")
    print("  " + format_ast(ast, indent=2))
    print(f"\n  Result: {result}")

    # --- 5.2 GC Algorithms ---
    print("\n" + "─" * 60)
    print("5.2 Garbage Collection アルゴリズム")
    print("─" * 60)

    class MarkSweepGC:
        """Mark-and-Sweep ガーベジコレクタ"""
        def __init__(self):
            self.objects: Dict[str, Dict] = {}  # name → {refs: [name], marked: bool}
            self.roots: List[str] = []

        def allocate(self, name: str, refs: List[str] = None):
            self.objects[name] = {"refs": refs or [], "marked": False}

        def set_root(self, names: List[str]):
            self.roots = names

        def collect(self) -> List[str]:
            # Mark phase
            for obj in self.objects.values():
                obj["marked"] = False

            # Mark reachable objects (BFS)
            queue = deque(self.roots)
            while queue:
                name = queue.popleft()
                if name in self.objects and not self.objects[name]["marked"]:
                    self.objects[name]["marked"] = True
                    for ref in self.objects[name]["refs"]:
                        queue.append(ref)

            # Sweep phase
            garbage = [name for name, obj in self.objects.items() if not obj["marked"]]
            for name in garbage:
                del self.objects[name]

            return garbage

    gc = MarkSweepGC()
    gc.allocate("A", ["B", "C"])
    gc.allocate("B", ["D"])
    gc.allocate("C", [])
    gc.allocate("D", [])
    gc.allocate("E", ["F"])  # unreachable cycle
    gc.allocate("F", ["E"])  # unreachable cycle
    gc.allocate("G", [])     # unreachable

    gc.set_root(["A"])

    print("\n  Object Graph:")
    print("    Root → A → B → D")
    print("             → C")
    print("    E ↔ F (cycle, no root)")
    print("    G (isolated)")

    garbage = gc.collect()
    print(f"\n  Collected (garbage): {garbage}")
    print(f"  Remaining: {list(gc.objects.keys())}")

    print("""
    GC アルゴリズム比較:
    ┌─────────────────┬───────────┬──────────┬───────────────┐
    │ Algorithm         │ Pause Time│ Throughput│ 使用例         │
    ├─────────────────┼───────────┼──────────┼───────────────┤
    │ Mark-Sweep        │ 長い      │ 高い     │ 基本形          │
    │ Mark-Compact      │ 長い      │ 高い     │ 断片化防止       │
    │ Copying GC        │ 中        │ 中       │ 世代別の若い世代 │
    │ Generational      │ 短い(Minor)│ 高い     │ JVM, Python     │
    │ G1 (Garbage First)│ 制御可能  │ 高い     │ Java 11+ default│
    │ ZGC / Shenandoah  │ < 10ms    │ やや低い │ Java 15+, 大ヒープ│
    └─────────────────┴───────────┴──────────┴───────────────┘

    CPython の GC:
    1. Reference Counting (主要): 参照が0になったら即解放
       → メリット: 確定的、低レイテンシ
       → デメリット: 循環参照を回収できない
    2. Generational GC (補助): 循環参照を回収
       → 世代0 (新) → 世代1 (中) → 世代2 (老)
       → 世代0が最も頻繁にGC実行
       → gc.collect() で手動実行可能

    ★ 面接質問: 「循環参照があるとPythonではメモリリークする？」
    回答: 「しない。参照カウントでは回収できないが、
          世代別GCが定期的に循環参照を検出・回収する。
          ただし __del__ を持つオブジェクトの循環参照は
          Python 3.4 未満では回収できなかった (PEP 442 で修正)」
    """)

    # --- 5.3 Python Dict Internals ---
    print("─" * 60)
    print("5.3 Python dict の内部実装")
    print("─" * 60)
    print("""
    CPython dict: Open Addressing + Perturbation Probing

    ┌──────────────────────────────────────────────┐
    │ Hash Table (compact dict, Python 3.6+)       │
    │                                               │
    │ indices:  [_, 0, _, _, 1, _, _, 2]            │
    │ entries:  [(hash_a, 'key_a', val_a),          │
    │            (hash_b, 'key_b', val_b),          │
    │            (hash_c, 'key_c', val_c)]          │
    └──────────────────────────────────────────────┘

    Probing (衝突解決):
    j = hash(key) & mask
    perturb = hash(key)
    while slot_occupied:
        j = (5 * j + perturb + 1) & mask
        perturb >>= 5
    → 線形探索より分散が良い

    Resize:
    - 2/3 以上埋まったら拡張 (×2 or ×4)
    - テーブルサイズは常に 2^n
    - 全エントリを再ハッシュ (O(n))

    サイズの実際:
    - 空 dict: 64 bytes (Python 3.12)
    - key追加ごとに entries に追加
    - 大きなdictは indices + entries で効率的

    ★ 面接: 「Python の dict の計算量は？」
    - 平均: O(1) (lookup, insert, delete)
    - 最悪: O(n) (全キーが衝突)
    - 実際: ハッシュ関数が良いため、ほぼ O(1)
    - 順序保証: Python 3.7+ で挿入順序を保証 (仕様)
    """)


# ============================================================
# Main
# ============================================================

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  CS Internals Deep Dive                                        ║")
    print("║  OS・ネットワーク・DB内部・並行処理・GC                          ║")
    print("║  「なぜそうなっているのか」を説明できるレベルへ                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    chapter1_os_internals()
    chapter2_networking()
    chapter3_db_internals()
    chapter4_concurrency()
    chapter5_runtime()

    print("\n" + "=" * 70)
    print("推奨書籍 (CS Internals)")
    print("=" * 70)
    print("""
    - "Operating Systems: Three Easy Pieces" (OSTEP) — 無料オンライン
    - "Computer Networking: A Top-Down Approach" by Kurose & Ross
    - "Database Internals" by Alex Petrov
    - "Designing Data-Intensive Applications" by Martin Kleppmann
    - "The Art of Multiprocessor Programming" by Herlihy & Shavit
    - "Crafting Interpreters" by Robert Nystrom — 無料オンライン
    """)

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    ・TCP/IP基礎 (3-way handshake, 輻輳ウィンドウの概念)
    ・プロセス/スレッド (違い, コンテキストスイッチ, スケジューリング基礎)
    ・B-Tree/インデックス (B+ Tree, なぜDBで使われるか)
    ・メモリ管理基礎 (仮想メモリ, ページング, スタック vs ヒープ)

  【Tier 2: 重要 — 実務で頻出】
    ・HTTP/1.1 vs 2 vs 3 (多重化, QUIC, ヘッド・オブ・ライン・ブロッキング)
    ・MVCC/トランザクション分離レベル (Snapshot Isolation, Write Skew)
    ・デッドロック検出 (Wait-for Graph, タイムアウト, 予防戦略)

  【Tier 3: 上級 — シニア以上で差がつく】
    ・LSM-Tree (Write最適化, Compaction戦略, B-Treeとの比較)
    ・輻輳制御 (CUBIC/BBR) (なぜBBRが優れるか, 帯域推定)
    ・Lock-Free データ構造 (CAS, ABA問題, Tagged Pointer)
    ・Work Stealing (ForkJoinPool, デキューベースの負荷分散)

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    ・Buddy System (メモリアロケータ, 断片化管理)
    ・Lexer/Parser/AST (コンパイラフロントエンド, DSL設計)
    ・GC実装 (Mark-Sweep, Generational, ZGC/Shenandoah)
    ・epoll/io_uring (非同期I/O, イベント駆動サーバーの内部)
""")


if __name__ == "__main__":
    main()
