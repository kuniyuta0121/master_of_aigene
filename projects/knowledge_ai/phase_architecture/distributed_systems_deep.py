#!/usr/bin/env python3
"""
Distributed Systems Deep Dive — 合意・一貫性・CRDT・分散トランザクション

FAANG Staff+ 面接の核心: 分散システムの「なぜ」を実装ベースで理解する。

実行: python distributed_systems_deep.py
依存: Python 3.9+ 標準ライブラリのみ
"""

import hashlib
import math
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Chapter 1: Consensus Protocols
# ============================================================

def chapter1_consensus():
    print("=" * 70)
    print("Chapter 1: Consensus Protocols")
    print("  分散合意 — 複数ノードが1つの値に合意する方法")
    print("=" * 70)

    # --- 1.1 Raft Consensus ---
    print("\n" + "─" * 60)
    print("1.1 Raft 合意アルゴリズム (完全実装)")
    print("─" * 60)

    class RaftState(Enum):
        FOLLOWER = "Follower"
        CANDIDATE = "Candidate"
        LEADER = "Leader"

    @dataclass
    class LogEntry:
        term: int
        command: str

    @dataclass
    class RaftNode:
        node_id: str
        state: RaftState = RaftState.FOLLOWER
        current_term: int = 0
        voted_for: Optional[str] = None
        log: List[LogEntry] = field(default_factory=list)
        commit_index: int = -1
        last_applied: int = -1
        # Leader state
        next_index: Dict[str, int] = field(default_factory=dict)
        match_index: Dict[str, int] = field(default_factory=dict)
        votes_received: Set[str] = field(default_factory=set)

    class RaftCluster:
        def __init__(self, node_ids: List[str]):
            self.nodes = {nid: RaftNode(nid) for nid in node_ids}
            self.node_ids = node_ids
            self.majority = len(node_ids) // 2 + 1
            self.log_messages: List[str] = []

        def _log(self, msg: str):
            self.log_messages.append(msg)

        def start_election(self, candidate_id: str):
            """候補者が選挙を開始"""
            node = self.nodes[candidate_id]
            node.current_term += 1
            node.state = RaftState.CANDIDATE
            node.voted_for = candidate_id
            node.votes_received = {candidate_id}
            self._log(f"  {candidate_id}: Term {node.current_term} — 選挙開始")

            # RequestVote RPC to all other nodes
            for peer_id in self.node_ids:
                if peer_id == candidate_id:
                    continue
                vote = self._request_vote(peer_id, candidate_id, node.current_term)
                if vote:
                    node.votes_received.add(peer_id)
                    self._log(f"    {peer_id} → 投票 YES")
                else:
                    self._log(f"    {peer_id} → 投票 NO")

            if len(node.votes_received) >= self.majority:
                node.state = RaftState.LEADER
                # Initialize leader state
                for peer_id in self.node_ids:
                    node.next_index[peer_id] = len(node.log)
                    node.match_index[peer_id] = -1
                self._log(f"  {candidate_id}: ★ LEADER 当選 (得票: {len(node.votes_received)}/{len(self.node_ids)})")
            else:
                node.state = RaftState.FOLLOWER
                self._log(f"  {candidate_id}: 落選")

        def _request_vote(self, voter_id: str, candidate_id: str, term: int) -> bool:
            voter = self.nodes[voter_id]
            if voter.state == RaftState.LEADER:
                return False  # 現Leaderは投票しない (simplified)
            if term > voter.current_term:
                voter.current_term = term
                voter.voted_for = candidate_id
                return True
            if voter.voted_for is None or voter.voted_for == candidate_id:
                voter.voted_for = candidate_id
                return True
            return False

        def replicate_log(self, leader_id: str, command: str) -> bool:
            """LeaderがログをFollowerに複製"""
            leader = self.nodes[leader_id]
            if leader.state != RaftState.LEADER:
                return False

            entry = LogEntry(term=leader.current_term, command=command)
            leader.log.append(entry)
            self._log(f"  {leader_id}: Append '{command}' (index={len(leader.log)-1})")

            ack_count = 1  # Leader自身
            for peer_id in self.node_ids:
                if peer_id == leader_id:
                    continue
                peer = self.nodes[peer_id]
                # AppendEntries RPC
                peer.log.append(entry)
                peer.current_term = leader.current_term
                ack_count += 1
                self._log(f"    → {peer_id}: replicated")

            if ack_count >= self.majority:
                leader.commit_index = len(leader.log) - 1
                self._log(f"  {leader_id}: COMMITTED '{command}' (acks={ack_count}/{len(self.node_ids)})")
                return True
            return False

        def simulate_leader_failure(self, failed_id: str):
            """Leader障害シミュレーション"""
            node = self.nodes[failed_id]
            old_state = node.state
            node.state = RaftState.FOLLOWER
            self._log(f"\n  ⚡ {failed_id} CRASHED (was {old_state.value})")

    # Run simulation
    cluster = RaftCluster(["N1", "N2", "N3", "N4", "N5"])

    print("\n  5ノードクラスタで Raft 合意シミュレーション:")
    print()

    # Phase 1: Leader election
    cluster.start_election("N1")
    print("\n".join(cluster.log_messages))
    cluster.log_messages.clear()

    # Phase 2: Log replication
    print()
    cluster.replicate_log("N1", "SET x=1")
    cluster.replicate_log("N1", "SET y=2")
    print("\n".join(cluster.log_messages))
    cluster.log_messages.clear()

    # Phase 3: Leader failure + re-election
    print()
    cluster.simulate_leader_failure("N1")
    cluster.start_election("N3")
    print("\n".join(cluster.log_messages))
    cluster.log_messages.clear()

    # Phase 4: New leader continues
    print()
    cluster.replicate_log("N3", "SET z=3")
    print("\n".join(cluster.log_messages))

    print("""
    Raft の安全性保証:
    1. Election Safety: 各 term で最大1人の Leader
    2. Leader Append-Only: Leader は自分のログを上書きしない
    3. Log Matching: 同じ index+term → 同じ entry
    4. Leader Completeness: committed entry は将来の Leader にもある
    5. State Machine Safety: 同じ index → 同じ command を適用

    Raft vs Paxos vs ZAB:
    ┌──────────────┬──────────┬──────────┬──────────┐
    │               │ Raft      │ Paxos     │ ZAB       │
    ├──────────────┼──────────┼──────────┼──────────┤
    │ 理解しやすさ  │ ◎        │ △         │ ○         │
    │ Leader必須   │ Yes       │ No*       │ Yes       │
    │ ログ順序保証  │ Yes       │ No*       │ Yes       │
    │ 使用例       │ etcd,Consul│ Chubby    │ ZooKeeper │
    └──────────────┴──────────┴──────────┴──────────┘
    * Multi-Paxos で Leader あり
    """)


# ============================================================
# Chapter 2: Consistency Models & CRDTs
# ============================================================

def chapter2_consistency():
    print("\n" + "=" * 70)
    print("Chapter 2: Consistency Models & CRDTs")
    print("  CAP の先にある一貫性の世界")
    print("=" * 70)

    # --- 2.1 Vector Clocks ---
    print("\n" + "─" * 60)
    print("2.1 Vector Clock (因果関係の追跡)")
    print("─" * 60)

    class VectorClock:
        def __init__(self, node_id: str, nodes: List[str]):
            self.node_id = node_id
            self.clock = {n: 0 for n in nodes}

        def increment(self):
            self.clock[self.node_id] += 1

        def send(self) -> Dict[str, int]:
            self.increment()
            return dict(self.clock)

        def receive(self, other_clock: Dict[str, int]):
            self.increment()
            for node, ts in other_clock.items():
                self.clock[node] = max(self.clock.get(node, 0), ts)

        def happens_before(self, other: 'VectorClock') -> bool:
            """self → other (self が other より前に発生)"""
            at_least_one_less = False
            for node in set(self.clock) | set(other.clock):
                s = self.clock.get(node, 0)
                o = other.clock.get(node, 0)
                if s > o:
                    return False
                if s < o:
                    at_least_one_less = True
            return at_least_one_less

        def concurrent(self, other: 'VectorClock') -> bool:
            return not self.happens_before(other) and not other.happens_before(self)

        def __repr__(self):
            return str(self.clock)

    nodes = ["A", "B", "C"]
    vc_a = VectorClock("A", nodes)
    vc_b = VectorClock("B", nodes)
    vc_c = VectorClock("C", nodes)

    # Simulate message passing
    print("\n  Event sequence:")

    # A does local event
    vc_a.increment()
    print(f"    A local event → A={vc_a}")

    # A sends to B
    msg = vc_a.send()
    print(f"    A sends to B  → A={vc_a}")
    vc_b.receive(msg)
    print(f"    B receives    → B={vc_b}")

    # B does local event
    vc_b.increment()
    print(f"    B local event → B={vc_b}")

    # C does local event (concurrent with B)
    vc_c.increment()
    print(f"    C local event → C={vc_c}")

    print(f"\n    B happens-before C? {vc_b.happens_before(vc_c)}")
    print(f"    B concurrent with C? {vc_b.concurrent(vc_c)}")
    print("    → B と C は因果関係なし (concurrent)")

    # --- 2.2 CRDTs ---
    print("\n" + "─" * 60)
    print("2.2 CRDT (Conflict-Free Replicated Data Types)")
    print("─" * 60)

    print("""
    CRDT: ネットワーク分断中でも各レプリカで独立に更新し、
    後からマージしても必ず収束する (Eventual Consistency を保証)
    """)

    # G-Counter (Grow-only Counter)
    class GCounter:
        """各ノードが自分のカウントだけ増やす"""
        def __init__(self, node_id: str, nodes: List[str]):
            self.node_id = node_id
            self.counts = {n: 0 for n in nodes}

        def increment(self, amount: int = 1):
            self.counts[self.node_id] += amount

        def value(self) -> int:
            return sum(self.counts.values())

        def merge(self, other: 'GCounter'):
            for node, count in other.counts.items():
                self.counts[node] = max(self.counts.get(node, 0), count)

    # PN-Counter (Positive-Negative Counter)
    class PNCounter:
        """増減可能なカウンタ: P (正) と N (負) の GCounter"""
        def __init__(self, node_id: str, nodes: List[str]):
            self.p = GCounter(node_id, nodes)
            self.n = GCounter(node_id, nodes)

        def increment(self, amount: int = 1):
            self.p.increment(amount)

        def decrement(self, amount: int = 1):
            self.n.increment(amount)

        def value(self) -> int:
            return self.p.value() - self.n.value()

        def merge(self, other: 'PNCounter'):
            self.p.merge(other.p)
            self.n.merge(other.n)

    # OR-Set (Observed-Remove Set)
    class ORSet:
        """追加と削除が可能な集合 (Observed-Remove)"""
        def __init__(self, node_id: str):
            self.node_id = node_id
            self.elements: Dict[Any, Set[str]] = defaultdict(set)  # value → {unique_tags}

        def add(self, value):
            tag = f"{self.node_id}-{uuid.uuid4().hex[:8]}"
            self.elements[value].add(tag)

        def remove(self, value):
            if value in self.elements:
                self.elements[value].clear()

        def lookup(self, value) -> bool:
            return bool(self.elements.get(value))

        def values(self) -> Set:
            return {v for v, tags in self.elements.items() if tags}

        def merge(self, other: 'ORSet'):
            for value, tags in other.elements.items():
                self.elements[value] |= tags

    # Demo: PN-Counter across 3 replicas
    nodes = ["R1", "R2", "R3"]
    r1 = PNCounter("R1", nodes)
    r2 = PNCounter("R2", nodes)
    r3 = PNCounter("R3", nodes)

    # Independent updates (network partition)
    r1.increment(5)
    r2.increment(3)
    r2.decrement(1)
    r3.increment(2)

    print("\n  PN-Counter (3 replicas, partitioned):")
    print(f"    R1: +5      → value={r1.value()}")
    print(f"    R2: +3, -1  → value={r2.value()}")
    print(f"    R3: +2      → value={r3.value()}")

    # Merge
    r1.merge(r2)
    r1.merge(r3)
    print(f"\n    After merge:  → value={r1.value()} (5+3-1+2=9)")

    # OR-Set demo
    s1 = ORSet("S1")
    s2 = ORSet("S2")

    s1.add("apple")
    s1.add("banana")
    s2.add("cherry")
    s2.remove("apple")  # S2 hasn't seen apple, so this is a no-op

    s1.merge(s2)
    print(f"\n  OR-Set:")
    print(f"    S1: add(apple, banana)")
    print(f"    S2: add(cherry), remove(apple) [not seen]")
    print(f"    Merged: {s1.values()}")
    print("    → apple は S2 の remove 時に S2 が知らなかったので残る")

    print("""
    CRDT 一覧:
    ┌────────────────┬────────────────────────────────┐
    │ Type            │ 用途                            │
    ├────────────────┼────────────────────────────────┤
    │ G-Counter       │ いいね数, PV (増加のみ)          │
    │ PN-Counter      │ 在庫, カート個数 (増減)          │
    │ G-Set           │ タグ追加 (削除不可)              │
    │ OR-Set          │ ショッピングカート (追加/削除)    │
    │ LWW-Register    │ ユーザー名 (最後の書き込み勝ち)  │
    │ MV-Register     │ 競合を保持して後から解決          │
    │ RGA             │ 共同編集テキスト                  │
    └────────────────┴────────────────────────────────┘

    使用例: Redis CRDT, Riak, Automerge, Yjs (共同編集)
    """)


# ============================================================
# Chapter 3: Distributed Transactions
# ============================================================

def chapter3_transactions():
    print("\n" + "=" * 70)
    print("Chapter 3: Distributed Transactions")
    print("  2PC・Saga・Outbox — 複数サービスの整合性")
    print("=" * 70)

    # --- 3.1 Two-Phase Commit ---
    print("\n" + "─" * 60)
    print("3.1 Two-Phase Commit (2PC)")
    print("─" * 60)

    class TwoPhaseCommit:
        def __init__(self, participants: List[str]):
            self.participants = participants
            self.votes: Dict[str, bool] = {}
            self.log: List[str] = []

        def execute(self, will_fail: Optional[str] = None) -> bool:
            self.log.append("=== Phase 1: Prepare ===")

            # Phase 1: Prepare
            for p in self.participants:
                if p == will_fail:
                    self.votes[p] = False
                    self.log.append(f"  {p}: VOTE NO (failure)")
                else:
                    self.votes[p] = True
                    self.log.append(f"  {p}: VOTE YES")

            # Phase 2: Commit or Abort
            all_yes = all(self.votes.values())
            if all_yes:
                self.log.append("=== Phase 2: Commit ===")
                for p in self.participants:
                    self.log.append(f"  {p}: COMMITTED")
                return True
            else:
                self.log.append("=== Phase 2: Abort ===")
                for p in self.participants:
                    if self.votes[p]:
                        self.log.append(f"  {p}: ROLLBACK")
                    else:
                        self.log.append(f"  {p}: already failed")
                return False

    # Success case
    tpc = TwoPhaseCommit(["OrderService", "PaymentService", "InventoryService"])
    result = tpc.execute()
    print("\n  Case 1: All succeed")
    for line in tpc.log:
        print(f"    {line}")
    print(f"    Result: {'COMMITTED' if result else 'ABORTED'}")

    # Failure case
    tpc2 = TwoPhaseCommit(["OrderService", "PaymentService", "InventoryService"])
    result2 = tpc2.execute(will_fail="PaymentService")
    print("\n  Case 2: Payment fails")
    for line in tpc2.log:
        print(f"    {line}")
    print(f"    Result: {'COMMITTED' if result2 else 'ABORTED'}")

    print("""
    2PC の問題:
    1. Blocking: Coordinator 障害で全 Participant がブロック
    2. Single Point of Failure: Coordinator が SPOF
    3. Performance: 2 回の同期通信 → レイテンシ増

    → マイクロサービスでは 2PC は避け、Saga を使う
    """)

    # --- 3.2 Saga Pattern ---
    print("─" * 60)
    print("3.2 Saga Pattern (補償トランザクション)")
    print("─" * 60)

    @dataclass
    class SagaStep:
        name: str
        action: str
        compensation: str

    class SagaOrchestrator:
        def __init__(self, steps: List[SagaStep]):
            self.steps = steps
            self.completed: List[SagaStep] = []
            self.log: List[str] = []

        def execute(self, fail_at: Optional[int] = None) -> bool:
            self.log.append("=== Saga Execution ===")

            for i, step in enumerate(self.steps):
                if i == fail_at:
                    self.log.append(f"  ✗ {step.name}: {step.action} → FAILED")
                    self._compensate()
                    return False

                self.log.append(f"  ✓ {step.name}: {step.action}")
                self.completed.append(step)

            self.log.append("=== Saga COMPLETED ===")
            return True

        def _compensate(self):
            self.log.append("=== Compensation (逆順) ===")
            for step in reversed(self.completed):
                self.log.append(f"  ↩ {step.name}: {step.compensation}")

    saga = SagaOrchestrator([
        SagaStep("Order", "注文を作成", "注文をキャンセル"),
        SagaStep("Inventory", "在庫を予約", "在庫を戻す"),
        SagaStep("Payment", "決済を実行", "返金を実行"),
        SagaStep("Shipping", "配送を手配", "配送をキャンセル"),
    ])

    result = saga.execute(fail_at=2)
    print("\n  EC注文 Saga (Payment で失敗):")
    for line in saga.log:
        print(f"    {line}")

    print("""
    Orchestration vs Choreography:

    Orchestration (中央指揮者):
    ┌────────────┐
    │ Orchestrator│───→ Order ──→ Inventory ──→ Payment
    │             │←── result ←── result    ←── result
    └────────────┘
    ✓ フロー可視化が容易
    ✗ 中央指揮者が SPOF

    Choreography (イベント連鎖):
    Order ──event──→ Inventory ──event──→ Payment
      ↑                                    │
      └──────── compensation event ────────┘
    ✓ 疎結合
    ✗ フロー追跡が困難

    ★ 面接での答え方:
    「3-4 ステップまでなら Choreography、
     5+ ステップや補償ロジックが複雑なら Orchestration。
     大規模では Temporal/Cadence のような Workflow Engine を使う。」
    """)

    # --- 3.3 Outbox Pattern ---
    print("─" * 60)
    print("3.3 Transactional Outbox Pattern")
    print("─" * 60)
    print("""
    問題: DB更新とメッセージ送信のアトミック性

    ✗ 危険なパターン:
    1. UPDATE orders SET status='paid'
    2. kafka.send("order.paid")       ← ここで crash → メッセージ欠損
    3. COMMIT

    ✓ Outbox Pattern:
    BEGIN TRANSACTION
      1. UPDATE orders SET status='paid'
      2. INSERT INTO outbox (event_type, payload) VALUES ('order.paid', ...)
    COMMIT

    別プロセスが outbox テーブルをポーリング or CDC:
    3. SELECT * FROM outbox WHERE sent=false
    4. kafka.send(event)
    5. UPDATE outbox SET sent=true WHERE id=...

    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ Service      │    │ Outbox      │    │ Message     │
    │              │───→│ Table       │───→│ Broker      │
    │ (TRANSACTION)│    │ (same DB)   │    │ (Kafka)     │
    └─────────────┘    └─────────────┘    └─────────────┘
         atomic              CDC/Poll

    CDC (Change Data Capture):
    - Debezium: MySQL/PostgreSQL の binlog/WAL を読む
    - → outbox テーブルの変更を自動的に Kafka に送信
    - → ポーリング不要、リアルタイム

    ★ Exactly-Once を実現する:
    - Producer: Outbox + べき等キー
    - Consumer: べき等処理 (同じイベントを2回処理してもOK)
    """)


# ============================================================
# Chapter 4: Replication & Partitioning
# ============================================================

def chapter4_replication():
    print("\n" + "=" * 70)
    print("Chapter 4: Replication & Partitioning")
    print("  データをどう分散し、どう一貫性を保つか")
    print("=" * 70)

    # --- 4.1 Quorum ---
    print("\n" + "─" * 60)
    print("4.1 Quorum Reads/Writes (Dynamo-style)")
    print("─" * 60)

    class DynamoQuorum:
        """Dynamo-style quorum replication"""
        def __init__(self, n: int, w: int, r: int):
            self.n = n  # Total replicas
            self.w = w  # Write quorum
            self.r = r  # Read quorum
            self.replicas: List[Dict[str, Tuple[Any, int]]] = [
                {} for _ in range(n)
            ]  # key → (value, timestamp)
            self.log: List[str] = []

        def write(self, key: str, value: Any) -> bool:
            ts = int(time.time() * 1000)
            acks = 0
            self.log.append(f"  WRITE {key}={value} (ts={ts})")

            for i in range(self.n):
                # Simulate: some replicas might be slow/down
                if random.random() < 0.9:  # 90% success
                    self.replicas[i][key] = (value, ts)
                    acks += 1
                    self.log.append(f"    Replica {i}: ACK")
                else:
                    self.log.append(f"    Replica {i}: TIMEOUT")

            success = acks >= self.w
            self.log.append(f"    ACKs: {acks}/{self.n}, W={self.w} → {'SUCCESS' if success else 'FAIL'}")
            return success

        def read(self, key: str) -> Optional[Any]:
            responses = []
            self.log.append(f"  READ {key}")

            for i in range(self.n):
                if key in self.replicas[i]:
                    val, ts = self.replicas[i][key]
                    responses.append((val, ts, i))
                    self.log.append(f"    Replica {i}: {val} (ts={ts})")

            if len(responses) < self.r:
                self.log.append(f"    Responses: {len(responses)}/{self.n}, R={self.r} → FAIL")
                return None

            # Return value with highest timestamp
            responses.sort(key=lambda x: x[1], reverse=True)
            latest = responses[0]
            self.log.append(f"    → Latest: {latest[0]} from Replica {latest[2]}")
            return latest[0]

    print("""
    Quorum 条件: R + W > N → 強い一貫性を保証

    ┌──────────┬─────────┬─────────┬──────────────────┐
    │ Config    │ 一貫性   │ 可用性   │ ユースケース       │
    ├──────────┼─────────┼─────────┼──────────────────┤
    │ N=3,W=3,R=1│ 強い     │ Write低 │ 読み取り重視      │
    │ N=3,W=1,R=3│ 強い     │ Read低  │ 書き込み重視      │
    │ N=3,W=2,R=2│ 強い     │ バランス│ 一般的 (推奨)     │
    │ N=3,W=1,R=1│ 結果整合 │ 高い    │ 高可用性優先      │
    └──────────┴─────────┴─────────┴──────────────────┘
    """)

    random.seed(42)
    quorum = DynamoQuorum(n=3, w=2, r=2)
    quorum.write("user:1", "Alice")
    quorum.read("user:1")
    for line in quorum.log:
        print(f"  {line}")

    print("""
    Sloppy Quorum + Hinted Handoff:
    - 本来のレプリカが down → 別ノードに一時保存 (hint)
    - 本来のレプリカ復旧 → hint を転送 (handoff)
    - → 可用性向上、ただし W+R > N でも一貫性保証が弱まる

    Read Repair:
    - Read 時に古いレプリカを発見 → 最新値で上書き
    - → バックグラウンドで一貫性を回復

    Anti-Entropy:
    - Merkle Tree で全レプリカのデータを比較
    - 差分だけを同期 → 帯域効率が良い
    """)

    # --- 4.2 Consistent Hashing (Deep) ---
    print("─" * 60)
    print("4.2 Consistent Hashing (Virtual Nodes)")
    print("─" * 60)

    class ConsistentHash:
        def __init__(self, vnodes_per_node: int = 150):
            self.vnodes = vnodes_per_node
            self.ring: List[Tuple[int, str]] = []  # sorted (hash, node_id)
            self.node_set: Set[str] = set()

        def _hash(self, key: str) -> int:
            return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**32)

        def add_node(self, node_id: str):
            self.node_set.add(node_id)
            for i in range(self.vnodes):
                h = self._hash(f"{node_id}:vnode:{i}")
                self.ring.append((h, node_id))
            self.ring.sort()

        def remove_node(self, node_id: str):
            self.node_set.discard(node_id)
            self.ring = [(h, n) for h, n in self.ring if n != node_id]

        def get_node(self, key: str) -> str:
            if not self.ring:
                raise ValueError("No nodes")
            h = self._hash(key)
            for ring_hash, node_id in self.ring:
                if ring_hash >= h:
                    return node_id
            return self.ring[0][1]  # wrap around

    ch = ConsistentHash(vnodes_per_node=100)
    for node in ["node-A", "node-B", "node-C"]:
        ch.add_node(node)

    # Distribute keys
    dist = defaultdict(int)
    keys = [f"key:{i}" for i in range(1000)]
    for key in keys:
        node = ch.get_node(key)
        dist[node] += 1

    print(f"\n  3 nodes, 100 vnodes each, 1000 keys:")
    for node, count in sorted(dist.items()):
        bar = "█" * (count // 10)
        print(f"    {node}: {count} {bar}")

    # Add node and measure redistribution
    old_mapping = {key: ch.get_node(key) for key in keys}
    ch.add_node("node-D")
    moved = sum(1 for key in keys if ch.get_node(key) != old_mapping[key])
    print(f"\n  After adding node-D: {moved}/{len(keys)} keys moved ({moved/len(keys)*100:.1f}%)")
    print(f"  Ideal: {100/4:.1f}% (1/N of keys)")

    new_dist = defaultdict(int)
    for key in keys:
        new_dist[ch.get_node(key)] += 1
    for node, count in sorted(new_dist.items()):
        bar = "█" * (count // 10)
        print(f"    {node}: {count} {bar}")


# ============================================================
# Chapter 5: Time, Ordering & Failure Detection
# ============================================================

def chapter5_time_and_failure():
    print("\n" + "=" * 70)
    print("Chapter 5: Time, Ordering & Failure Detection")
    print("  分散システムで最も難しい問題: 時間と障害")
    print("=" * 70)

    # --- 5.1 Hybrid Logical Clock ---
    print("\n" + "─" * 60)
    print("5.1 Hybrid Logical Clock (HLC)")
    print("─" * 60)

    class HLC:
        """CockroachDB/Spanner で使われるハイブリッド論理時計"""
        def __init__(self, node_id: str):
            self.node_id = node_id
            self.pt = 0   # physical time component
            self.lc = 0   # logical counter

        def now(self) -> Tuple[int, int]:
            """ローカルイベント"""
            wall = int(time.time() * 1000)
            if wall > self.pt:
                self.pt = wall
                self.lc = 0
            else:
                self.lc += 1
            return (self.pt, self.lc)

        def send(self) -> Tuple[int, int]:
            return self.now()

        def receive(self, msg_pt: int, msg_lc: int) -> Tuple[int, int]:
            wall = int(time.time() * 1000)
            if wall > self.pt and wall > msg_pt:
                self.pt = wall
                self.lc = 0
            elif msg_pt > self.pt:
                self.pt = msg_pt
                self.lc = msg_lc + 1
            elif self.pt > msg_pt:
                self.lc += 1
            else:  # equal
                self.lc = max(self.lc, msg_lc) + 1
            return (self.pt, self.lc)

    print("""
    なぜ物理時計だけではダメか:
    - NTP の精度: 数ms〜数十ms (インターネット経由)
    - クロックスキュー: ノード間で時刻が異なる
    - Leap second: UTC の調整で時計が巻き戻る可能性

    HLC = max(物理時計, 論理時計) で因果順序を保証

    Google TrueTime (Spanner):
    - GPS + 原子時計で ε < 7ms の不確実性
    - TT.now() → [earliest, latest] の区間を返す
    - Commit-wait: 不確実性区間が過ぎるまで待つ
    → 外部一貫性 (External Consistency) を保証
    → 実質的に Linearizability を地理分散で実現
    """)

    # --- 5.2 Snowflake ID ---
    print("─" * 60)
    print("5.2 Snowflake ID (分散ID生成)")
    print("─" * 60)

    class SnowflakeID:
        """Twitter Snowflake: 64-bit unique ID"""
        EPOCH = 1288834974657  # Twitter epoch (2010-11-04)

        def __init__(self, datacenter_id: int, worker_id: int):
            self.datacenter_id = datacenter_id & 0x1F  # 5 bits
            self.worker_id = worker_id & 0x1F           # 5 bits
            self.sequence = 0
            self.last_ts = -1

        def generate(self) -> int:
            ts = int(time.time() * 1000) - self.EPOCH

            if ts == self.last_ts:
                self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits
                if self.sequence == 0:
                    # Wait for next millisecond
                    while ts == self.last_ts:
                        ts = int(time.time() * 1000) - self.EPOCH
            else:
                self.sequence = 0

            self.last_ts = ts

            return (
                (ts << 22) |
                (self.datacenter_id << 17) |
                (self.worker_id << 12) |
                self.sequence
            )

        @staticmethod
        def parse(snowflake_id: int) -> Dict:
            ts = (snowflake_id >> 22) + SnowflakeID.EPOCH
            dc = (snowflake_id >> 17) & 0x1F
            worker = (snowflake_id >> 12) & 0x1F
            seq = snowflake_id & 0xFFF
            return {"timestamp_ms": ts, "datacenter": dc, "worker": worker, "sequence": seq}

    gen = SnowflakeID(datacenter_id=1, worker_id=3)
    ids = [gen.generate() for _ in range(5)]

    print("""
    Snowflake ID 構造 (64 bits):
    ┌─────────────────┬──────┬──────┬────────────┐
    │ Timestamp (41b)  │DC(5b)│WK(5b)│ Sequence(12b)│
    └─────────────────┴──────┴──────┴────────────┘
    - 41 bits: ミリ秒タイムスタンプ (69年分)
    - 5 bits: データセンターID (32 DC)
    - 5 bits: ワーカーID (32 workers/DC)
    - 12 bits: シーケンス (4096/ms/worker)
    → 1ワーカーあたり 毎秒 4,096,000 ID 生成可能
    """)

    print(f"  Generated IDs:")
    for sid in ids:
        parsed = SnowflakeID.parse(sid)
        print(f"    {sid} → dc={parsed['datacenter']}, worker={parsed['worker']}, seq={parsed['sequence']}")

    print("""
    他のID生成方式:
    ┌──────────────┬────────┬──────────┬──────────────┐
    │ Method        │ 順序性  │ 分散対応  │ 用途          │
    ├──────────────┼────────┼──────────┼──────────────┤
    │ UUID v4       │ ✗      │ ✓        │ 汎用          │
    │ UUID v7       │ ✓      │ ✓        │ DB PK (推奨)  │
    │ Snowflake     │ ✓      │ ✓        │ Twitter, Discord│
    │ ULID          │ ✓      │ ✓        │ Snowflake の改良│
    │ DB Auto-Inc   │ ✓      │ ✗        │ 単一DB         │
    │ Leaf (Meituan)│ ✓      │ ✓        │ 中央割当サーバー│
    └──────────────┴────────┴──────────┴──────────────┘

    ★ UUID v4 が B-Tree インデックスに悪い理由:
    - ランダムなので挿入が全ページに分散 → キャッシュ効率↓
    - UUID v7 / ULID / Snowflake はタイムスタンプ先頭 → 順序挿入
    """)

    # --- 5.3 Phi Accrual Failure Detector ---
    print("─" * 60)
    print("5.3 Phi Accrual Failure Detector")
    print("─" * 60)

    class PhiAccrualDetector:
        """Cassandra で使われる適応的障害検出器"""
        def __init__(self, threshold: float = 8.0, window_size: int = 100):
            self.threshold = threshold
            self.window_size = window_size
            self.intervals: List[float] = []
            self.last_heartbeat: Optional[float] = None

        def heartbeat(self, now: float):
            if self.last_heartbeat is not None:
                interval = now - self.last_heartbeat
                self.intervals.append(interval)
                if len(self.intervals) > self.window_size:
                    self.intervals.pop(0)
            self.last_heartbeat = now

        def phi(self, now: float) -> float:
            if not self.intervals or self.last_heartbeat is None:
                return 0.0
            elapsed = now - self.last_heartbeat
            mean = sum(self.intervals) / len(self.intervals)
            if mean == 0:
                return 0.0
            # Exponential distribution approximation
            p = math.exp(-elapsed / mean)
            if p == 0:
                return float('inf')
            return -math.log10(p)

        def is_alive(self, now: float) -> Tuple[bool, float]:
            p = self.phi(now)
            return p < self.threshold, p

    detector = PhiAccrualDetector(threshold=8.0)
    base = 1000.0

    # Normal heartbeats (every ~1.0s with jitter)
    for i in range(20):
        t = base + i * 1.0 + random.uniform(-0.1, 0.1)
        detector.heartbeat(t)

    # Check at various times after last heartbeat
    last = base + 19 * 1.0
    print(f"\n  Normal heartbeat interval: ~1.0s, Threshold: φ={detector.threshold}")
    print(f"\n  {'Elapsed':>8} {'φ':>8} {'Status':>10}")
    print("  " + "-" * 30)
    for delay in [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0]:
        alive, phi_val = detector.is_alive(last + delay)
        status = "ALIVE" if alive else "SUSPECTED"
        print(f"  {delay:>7.1f}s {phi_val:>8.2f} {status:>10}")

    print("""
    従来の Fixed Timeout vs Phi Accrual:
    - Fixed: 3秒で timeout → ネットワーク揺らぎで誤検出
    - Phi: ハートビート間隔の統計分布に基づく
    - φ = -log10(P(遅延がこれ以上続く確率))
    - φ > threshold → suspect
    - Cassandra default: φ threshold = 8

    ★ SWIM Protocol (Scalable Weakly-consistent Infection-style Membership):
    - Gossip + Failure Detection の統合
    - 各ノードがランダムにペアを選んで probe
    - 直接 probe 失敗 → 他ノード経由で間接 probe
    - 間接も失敗 → suspect → 一定時間後 declare dead
    - HashiCorp Serf / Consul で使用
    """)


# ============================================================
# Main
# ============================================================

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  Distributed Systems Deep Dive                                 ║")
    print("║  合意・一貫性・トランザクション・レプリケーション                 ║")
    print("║  DDIA (Designing Data-Intensive Applications) を実装で理解      ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    chapter1_consensus()
    chapter2_consistency()
    chapter3_transactions()
    chapter4_replication()
    chapter5_time_and_failure()

    print("\n" + "=" * 70)
    print("Summary: 分散システムの核心")
    print("=" * 70)
    print("""
    1. 合意 (Consensus): Raft/Paxos — Leader選出 + ログ複製
    2. 一貫性 (Consistency): Linearizability > Sequential > Causal > Eventual
    3. CRDT: 衝突なしで結果整合 — G-Counter, OR-Set
    4. 分散トランザクション: 2PC (強い) vs Saga (柔軟) vs Outbox (信頼性)
    5. レプリケーション: Quorum (R+W>N) + Read Repair + Anti-Entropy
    6. パーティショニング: Consistent Hashing + Virtual Nodes
    7. 時間: HLC / TrueTime, Snowflake ID
    8. 障害検出: Phi Accrual (適応的) > Fixed Timeout

    必読: "Designing Data-Intensive Applications" by Martin Kleppmann
    """)


if __name__ == "__main__":
    main()
