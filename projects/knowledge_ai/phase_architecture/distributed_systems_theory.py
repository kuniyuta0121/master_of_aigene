#!/usr/bin/env python3
"""
Distributed Systems Theory — FLP不可能性・Paxos・一貫性モデル・BFT・レプリケーション・時間と順序

DDIA (Designing Data-Intensive Applications) + Distributed Algorithms レベル。
理論を「動く Python コード」で体験する。

実行: python distributed_systems_theory.py
依存: Python 3.9+ 標準ライブラリのみ
"""

import hashlib
import random
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================
# Chapter 1: FLP Impossibility (Fischer-Lynch-Paterson, 1985)
# ============================================================

def chapter1_flp_impossibility():
    print("=" * 70)
    print("Chapter 1: FLP Impossibility Theorem")
    print("  非同期システムでは1ノード障害でも合意が保証できない")
    print("=" * 70)

    # --- 1.1 FLP の本質 ---
    print("\n" + "-" * 60)
    print("1.1 FLP不可能性定理とは何か")
    print("-" * 60)
    print("""
    FLP定理 (Fischer, Lynch, Paterson 1985):
    ──────────────────────────────────────
    「完全非同期システムにおいて、たとえ1つのプロセスがクラッシュする
     可能性があるだけで、決定的な合意プロトコルは存在しない」

    前提条件:
      1. 非同期モデル: メッセージ遅延に上限なし
      2. 決定的プロセス: ランダム性を使わない
      3. 信頼性のあるネットワーク: メッセージは必ず届く (遅延は不定)
      4. クラッシュ障害: 最大1ノードがクラッシュしうる

    結論:
      上記条件下で Agreement + Validity + Termination を
      同時に満たすプロトコルは存在しない。

    重要: FLPは「不可能」を証明するが「実用不可能」を意味しない。
           Paxos/Raft は確率的終了性で回避する。
    """)

    # --- 1.2 合意の3条件 ---
    print("-" * 60)
    print("1.2 合意の3条件 (Consensus Properties)")
    print("-" * 60)

    @dataclass
    class ConsensusProperties:
        agreement: str = "全ての正常プロセスは同じ値を決定する"
        validity: str = "決定される値はいずれかのプロセスが提案した値"
        termination: str = "全ての正常プロセスは最終的に決定する"

    props = ConsensusProperties()
    print(f"  Agreement  : {props.agreement}")
    print(f"  Validity   : {props.validity}")
    print(f"  Termination: {props.termination}")
    print()
    print("  FLPが示すのは: Termination を保証できない (永遠に決定しないケースが存在)")
    print("  Agreement + Validity は保証可能だが、終了性を犠牲にする")

    # --- 1.3 FLP不可能性のシミュレーション ---
    print("\n" + "-" * 60)
    print("1.3 FLP Impossibility — シミュレーション")
    print("-" * 60)

    class AsyncProcess:
        """非同期プロセス。内部状態と入力バッファを持つ"""
        def __init__(self, pid: int, initial_value: int):
            self.pid = pid
            self.initial_value = initial_value
            self.decided: Optional[int] = None
            self.inbox: List[Tuple[int, int]] = []  # (from_pid, value)
            self.alive = True

        def receive(self, from_pid: int, value: int):
            if self.alive:
                self.inbox.append((from_pid, value))

        def __repr__(self):
            status = "CRASHED" if not self.alive else (
                f"decided={self.decided}" if self.decided is not None else "undecided"
            )
            return f"P{self.pid}(v={self.initial_value}, {status})"

    class FLPDemonstration:
        """FLPの核心: adversary が1つのメッセージ遅延を制御するだけで合意を妨害"""
        def __init__(self, n: int = 3):
            self.processes = [AsyncProcess(i, i % 2) for i in range(n)]
            self.round = 0
            self.log: List[str] = []

        def adversarial_schedule(self, max_rounds: int = 10) -> bool:
            """敵対的スケジューラ: 常に 'bivalent' 状態を維持しようとする"""
            self.log.append("  [Adversary] メッセージ配送順序を操作して合意を妨害する")

            for r in range(max_rounds):
                self.round = r + 1
                alive_procs = [p for p in self.processes if p.alive]

                if len(alive_procs) < 2:
                    self.log.append(f"  Round {self.round}: 正常プロセスが不足 — 合意不可能")
                    return False

                # 各プロセスが自分の値をブロードキャスト
                for p in alive_procs:
                    for q in alive_procs:
                        if p.pid != q.pid:
                            q.receive(p.pid, p.initial_value)

                # Adversary: 重要なメッセージを「遅延」させて
                # 過半数の合意形成を妨害する
                target = alive_procs[0]
                delayed_msgs = target.inbox[:1]  # 最初のメッセージを遅延
                target.inbox = target.inbox[1:]

                # 合意チェック: 多数決で decide しようとする
                for p in alive_procs:
                    if p.decided is None and len(p.inbox) >= len(alive_procs) - 1:
                        votes = defaultdict(int)
                        votes[p.initial_value] += 1
                        for (_, v) in p.inbox:
                            votes[v] += 1
                        majority = max(votes.items(), key=lambda x: x[1])
                        if majority[1] > len(self.processes) // 2:
                            p.decided = majority[0]

                # Adversary: decided 直前のプロセスを crash させる
                about_to_decide = [p for p in alive_procs if p.decided is not None]
                if about_to_decide and r < max_rounds - 1:
                    victim = about_to_decide[0]
                    victim.alive = False
                    victim.decided = None
                    self.log.append(
                        f"  Round {self.round}: P{victim.pid} が decide 直前に crash! "
                        f"→ bivalent 状態維持"
                    )
                else:
                    decided = [p for p in alive_procs if p.decided is not None]
                    self.log.append(
                        f"  Round {self.round}: alive={len(alive_procs)}, "
                        f"decided={len(decided)}"
                    )

                # 遅延メッセージを戻す
                target.inbox.extend(delayed_msgs)

            all_decided = all(
                p.decided is not None for p in self.processes if p.alive
            )
            return all_decided

    demo = FLPDemonstration(n=5)
    result = demo.adversarial_schedule(max_rounds=8)
    for line in demo.log:
        print(line)
    print(f"\n  合意達成: {result}")
    print("  → Adversary がメッセージ遅延+クラッシュタイミングを制御すると合意不可能")

    # --- 1.4 実用的な回避策 ---
    print("\n" + "-" * 60)
    print("1.4 FLPの実用的回避策")
    print("-" * 60)
    print("""
    FLPを回避する方法:
    ┌─────────────────┬───────────────────────────────────────────┐
    │ 方法            │ 説明                                      │
    ├─────────────────┼───────────────────────────────────────────┤
    │ タイムアウト     │ 部分同期モデル (eventually synchronous)    │
    │                 │ → Paxos, Raft が採用                      │
    ├─────────────────┼───────────────────────────────────────────┤
    │ ランダム化       │ 確率的終了性 (w.p.1 で終了)               │
    │                 │ → Ben-Or Protocol, Randomized Consensus   │
    ├─────────────────┼───────────────────────────────────────────┤
    │ 障害検出器       │ ◇P (eventually perfect failure detector) │
    │                 │ → Chandra-Toueg Consensus                 │
    ├─────────────────┼───────────────────────────────────────────┤
    │ 弱い一貫性      │ 合意を諦めて結果整合性                     │
    │                 │ → Dynamo, CRDTs                           │
    └─────────────────┴───────────────────────────────────────────┘

    Paxos/Raft の戦略:
      「非同期だが、十分長い安定期間があれば progress する」
      → Safety は常に保証、Liveness は安定期間中のみ保証
    """)


# ============================================================
# Chapter 2: Paxos
# ============================================================

def chapter2_paxos():
    print("\n" + "=" * 70)
    print("Chapter 2: Paxos — Lamport's Consensus Algorithm")
    print("  Single-decree Paxos の完全実装 + Multi-Paxos")
    print("=" * 70)

    # --- 2.1 Single-Decree Paxos ---
    print("\n" + "-" * 60)
    print("2.1 Single-Decree Paxos (Synod Protocol)")
    print("-" * 60)
    print("""
    役割:
      Proposer  — 値を提案する
      Acceptor  — 提案を受け入れる/拒否する
      Learner   — 決定された値を学習する

    Phase 1: Prepare / Promise
      Proposer → Acceptor: Prepare(n)
      Acceptor → Proposer: Promise(n, accepted_n, accepted_v)
        条件: n > max_promised ならば promise する

    Phase 2: Accept / Accepted
      Proposer → Acceptor: Accept(n, v)
      Acceptor → Proposer: Accepted(n, v)
        条件: n >= max_promised ならば accept する

    不変条件 (Safety):
      - 最大1つの値のみが決定される
      - 決定された値は必ず提案された値のいずれか
    """)

    @dataclass
    class PaxosMessage:
        msg_type: str  # prepare, promise, accept, accepted, nack
        proposal_num: int
        value: Optional[Any] = None
        accepted_num: Optional[int] = None
        accepted_val: Optional[Any] = None
        from_id: str = ""
        to_id: str = ""

    class PaxosAcceptor:
        def __init__(self, aid: str):
            self.aid = aid
            self.max_promised: int = -1
            self.accepted_num: Optional[int] = None
            self.accepted_val: Optional[Any] = None

        def handle_prepare(self, msg: PaxosMessage) -> PaxosMessage:
            if msg.proposal_num > self.max_promised:
                self.max_promised = msg.proposal_num
                return PaxosMessage(
                    msg_type="promise",
                    proposal_num=msg.proposal_num,
                    accepted_num=self.accepted_num,
                    accepted_val=self.accepted_val,
                    from_id=self.aid,
                    to_id=msg.from_id,
                )
            return PaxosMessage(
                msg_type="nack", proposal_num=msg.proposal_num,
                from_id=self.aid, to_id=msg.from_id,
            )

        def handle_accept(self, msg: PaxosMessage) -> PaxosMessage:
            if msg.proposal_num >= self.max_promised:
                self.max_promised = msg.proposal_num
                self.accepted_num = msg.proposal_num
                self.accepted_val = msg.value
                return PaxosMessage(
                    msg_type="accepted",
                    proposal_num=msg.proposal_num,
                    value=msg.value,
                    from_id=self.aid,
                    to_id=msg.from_id,
                )
            return PaxosMessage(
                msg_type="nack", proposal_num=msg.proposal_num,
                from_id=self.aid, to_id=msg.from_id,
            )

    class PaxosProposer:
        def __init__(self, pid: str, acceptors: List[PaxosAcceptor]):
            self.pid = pid
            self.acceptors = acceptors
            self.majority = len(acceptors) // 2 + 1
            self.proposal_counter = 0

        def next_proposal_num(self, base: int = 0) -> int:
            """ユニークな proposal number を生成"""
            self.proposal_counter += 1
            # proposer ID をエンコード: counter * 100 + hash(pid) % 100
            return self.proposal_counter * 100 + hash(self.pid) % 100

        def propose(self, value: Any, log: List[str]) -> Optional[Any]:
            """Single-decree Paxos の実行"""
            n = self.next_proposal_num()
            log.append(f"  [{self.pid}] Phase 1: Prepare(n={n})")

            # Phase 1: Send Prepare, collect Promises
            prepare_msg = PaxosMessage(
                msg_type="prepare", proposal_num=n, from_id=self.pid
            )
            promises = []
            for acc in self.acceptors:
                resp = acc.handle_prepare(prepare_msg)
                if resp.msg_type == "promise":
                    promises.append(resp)
                    log.append(
                        f"    {acc.aid} → Promise(n={n}, "
                        f"accepted=({resp.accepted_num}, {resp.accepted_val}))"
                    )
                else:
                    log.append(f"    {acc.aid} → NACK (already promised higher)")

            if len(promises) < self.majority:
                log.append(f"  [{self.pid}] Promise 不足 ({len(promises)}/{self.majority}) — 失敗")
                return None

            # Phase 1b の制約: 既に accept された値があればそれを使う
            prev_accepted = [
                p for p in promises if p.accepted_num is not None
            ]
            if prev_accepted:
                highest = max(prev_accepted, key=lambda p: p.accepted_num)
                value = highest.accepted_val
                log.append(
                    f"  [{self.pid}] 既存 accepted 値を採用: {value} "
                    f"(from proposal {highest.accepted_num})"
                )

            # Phase 2: Send Accept
            log.append(f"  [{self.pid}] Phase 2: Accept(n={n}, v={value})")
            accept_msg = PaxosMessage(
                msg_type="accept", proposal_num=n,
                value=value, from_id=self.pid,
            )
            accepted_count = 0
            for acc in self.acceptors:
                resp = acc.handle_accept(accept_msg)
                if resp.msg_type == "accepted":
                    accepted_count += 1
                    log.append(f"    {acc.aid} → Accepted(n={n}, v={value})")
                else:
                    log.append(f"    {acc.aid} → NACK")

            if accepted_count >= self.majority:
                log.append(f"  [{self.pid}] DECIDED: {value} (n={n})")
                return value
            else:
                log.append(f"  [{self.pid}] Accept 不足 — 失敗")
                return None

    # --- Paxos 実行 ---
    print("  --- Single-Decree Paxos シミュレーション ---\n")

    acceptors = [PaxosAcceptor(f"A{i}") for i in range(5)]
    p1 = PaxosProposer("P1", acceptors)
    p2 = PaxosProposer("P2", acceptors)

    log: List[str] = []

    # シナリオ: P1 が提案
    log.append("=== Scenario 1: 単一 Proposer ===")
    result = p1.propose("value_X", log)

    # シナリオ: P2 が競合提案 (Acceptor は既に P1 の値を accepted)
    log.append("\n=== Scenario 2: 競合 Proposer (P2 は P1 の accepted 値を尊重) ===")
    result2 = p2.propose("value_Y", log)

    for line in log:
        print(line)

    print(f"\n  Safety 検証: 両 Proposer の結果 = {result}, {result2}")
    if result == result2:
        print("  → 同じ値に合意! Paxos の Safety 保証が機能")

    # --- 2.2 Multi-Paxos ---
    print("\n" + "-" * 60)
    print("2.2 Multi-Paxos & Leader 最適化")
    print("-" * 60)
    print("""
    Multi-Paxos の核心:
      Single-decree Paxos をログの各スロットに適用する。

    Leader 最適化:
      1. 安定したリーダーが Phase 1 を1回だけ実行
      2. 以降は Phase 2 のみ (1 RTT で commit)
      3. リーダー障害時のみ Phase 1 が再実行される

    ┌────────────────────────────────────────────────┐
    │ Log Slot:  [1]    [2]    [3]    [4]    [5]     │
    │            v=A    v=B    v=C    v=D    ...     │
    │            ↑ Single-decree Paxos per slot      │
    │                                                │
    │ Multi-Paxos Leader: Phase 1 は slot 1 で1回   │
    │  以降 slot 2,3,4... は Phase 2 のみ (高速)    │
    └────────────────────────────────────────────────┘

    現実のシステム:
      Google Chubby  → Multi-Paxos
      Apache ZooKeeper → Zab (Paxos variant)
      etcd / Consul  → Raft (Paxos の理解しやすい版)
    """)

    # --- 2.3 Paxos vs Raft 比較 ---
    print("-" * 60)
    print("2.3 Paxos vs Raft 比較")
    print("-" * 60)
    print("""
    ┌──────────────┬──────────────────────┬──────────────────────┐
    │              │ Paxos                │ Raft                 │
    ├──────────────┼──────────────────────┼──────────────────────┤
    │ 論文発表     │ 1989 (Lamport)       │ 2014 (Ongaro)        │
    │ 設計思想     │ 数学的に最小限       │ 理解しやすさ重視     │
    │ リーダー     │ 必須ではない         │ 強リーダー必須       │
    │ ログ穴       │ 許容 (gap)           │ 不許容 (連続)        │
    │ メンバ変更   │ 未定義 (拡張が必要)  │ Joint Consensus      │
    │ 実装難度     │ 非常に高い           │ 比較的低い           │
    │ 正当性証明   │ Lamport の TLA+      │ TLA+ spec 付き       │
    │ 性能         │ 理論的に同等         │ 理論的に同等         │
    │ 採用例       │ Chubby, Spanner      │ etcd, CockroachDB    │
    └──────────────┴──────────────────────┴──────────────────────┘

    Raft が Paxos を「制限」した点:
      1. リーダーのログが最も進んでいることを保証
      2. ログの gap を禁止 → リプレイが単純
      3. リーダー選出に制約 (最新ログを持つノードのみ)
    """)


# ============================================================
# Chapter 3: Consistency Models
# ============================================================

def chapter3_consistency_models():
    print("\n" + "=" * 70)
    print("Chapter 3: Consistency Models — 一貫性モデルの実装と検証")
    print("=" * 70)

    # --- 3.1 一貫性モデルの階層 ---
    print("\n" + "-" * 60)
    print("3.1 一貫性モデルの強さ階層")
    print("-" * 60)
    print("""
    強い ──────────────────────────────── 弱い
    Linearizable > Sequential > Causal > Eventual

    Linearizable (線形化可能性):
      - 全操作にリアルタイムの順序付けが存在
      - 操作は「瞬間的に」効果を持つように見える
      - コスト: 高レイテンシ (CAP の C)

    Sequential Consistency (逐次一貫性):
      - 全操作にグローバル順序が存在
      - 各プロセスのローカル順序は保持
      - リアルタイム順序は不要

    Causal Consistency (因果一貫性):
      - 因果関係のある操作の順序は全ノードで一致
      - 並行操作は異なる順序で見えてよい

    Eventual Consistency (結果整合性):
      - 更新が停止すれば最終的に全ノードが一致
      - 途中は異なる値を返してよい
    """)

    # --- 3.2 操作履歴と一貫性チェッカー ---
    print("-" * 60)
    print("3.2 Jepsen-style 一貫性チェッカー")
    print("-" * 60)

    @dataclass
    class Operation:
        """分散ストアへの操作を記録"""
        process: int      # プロセスID
        op_type: str      # "write" or "read"
        key: str
        value: Any
        start_time: float   # 操作開始時刻
        end_time: float     # 操作完了時刻

        def __repr__(self):
            return f"P{self.process}:{self.op_type}({self.key}={self.value})@[{self.start_time:.1f},{self.end_time:.1f}]"

    class ConsistencyChecker:
        """操作履歴から一貫性モデル違反を検出"""

        def __init__(self, history: List[Operation]):
            self.history = sorted(history, key=lambda op: op.start_time)
            self.writes = [op for op in self.history if op.op_type == "write"]
            self.reads = [op for op in self.history if op.op_type == "read"]

        def check_linearizability(self) -> Tuple[bool, List[str]]:
            """
            Linearizability チェック (簡易版):
            各 read は、リアルタイム順序で「最後に完了した write」の値を返すべき。

            正確には NP-complete (Wing & Gong) だが、ここでは single-key の
            簡易版を実装。
            """
            violations = []
            for read_op in self.reads:
                # この read の start_time より前に end した write を探す
                preceding_writes = [
                    w for w in self.writes
                    if w.key == read_op.key and w.end_time <= read_op.start_time
                ]
                # この read の end_time より後に start した write は「後」
                # concurrent な write は許容する

                if preceding_writes:
                    latest_write = max(preceding_writes, key=lambda w: w.end_time)
                    if read_op.value != latest_write.value:
                        # concurrent write がないか確認
                        concurrent_writes = [
                            w for w in self.writes
                            if w.key == read_op.key
                            and w.start_time <= read_op.end_time
                            and w.end_time >= read_op.start_time
                        ]
                        concurrent_values = {w.value for w in concurrent_writes}
                        if read_op.value not in concurrent_values:
                            violations.append(
                                f"  VIOLATION: {read_op} read {read_op.value}, "
                                f"but latest write was {latest_write.value}"
                            )
            is_valid = len(violations) == 0
            return is_valid, violations

        def check_sequential_consistency(self) -> Tuple[bool, List[str]]:
            """
            Sequential Consistency チェック:
            各プロセスのローカル順序を保持する全順序が存在するか。
            (リアルタイム制約なし)
            """
            violations = []
            # プロセスごとの操作順序を取得
            per_process: Dict[int, List[Operation]] = defaultdict(list)
            for op in self.history:
                per_process[op.process].append(op)

            # 各プロセス内で、write 後の read が古い値を返していないか
            for pid, ops in per_process.items():
                last_written: Dict[str, Any] = {}
                for op in ops:
                    if op.op_type == "write":
                        last_written[op.key] = op.value
                    elif op.op_type == "read" and op.key in last_written:
                        # "read your own writes" の違反チェック
                        pass  # Sequential consistency では他プロセスの write は見えなくてよい

            # 簡易チェック: read が全く書かれていない値を返していないか
            all_written_values: Dict[str, Set] = defaultdict(set)
            for w in self.writes:
                all_written_values[w.key].add(w.value)

            for r in self.reads:
                if r.value is not None and r.value not in all_written_values.get(r.key, set()):
                    # 初期値 None でなく、かつ write されていない値
                    if r.value != "init":
                        violations.append(
                            f"  VIOLATION: {r} read value '{r.value}' "
                            f"that was never written"
                        )

            return len(violations) == 0, violations

        def check_causal_consistency(self) -> Tuple[bool, List[str]]:
            """
            Causal Consistency チェック:
            因果関係 (happens-before) のある操作は全プロセスで同じ順序で観測される。
            """
            violations = []

            # 因果関係の構築: write → read (同一 key, 同一 value)
            # = read が write に依存する
            causal_deps: List[Tuple[Operation, Operation]] = []
            for r in self.reads:
                for w in self.writes:
                    if w.key == r.key and w.value == r.value and w.end_time <= r.start_time:
                        causal_deps.append((w, r))
                        break

            # 同一プロセスの操作は因果関係がある (program order)
            per_process: Dict[int, List[Operation]] = defaultdict(list)
            for op in self.history:
                per_process[op.process].append(op)

            for pid, ops in per_process.items():
                for i in range(len(ops) - 1):
                    causal_deps.append((ops[i], ops[i + 1]))

            # 因果順序の cycle チェック (cycle があれば違反)
            # 簡易版: 推移閉包で cycle 検出
            op_to_idx = {id(op): i for i, op in enumerate(self.history)}
            n = len(self.history)
            reachable = [[False] * n for _ in range(n)]
            for (a, b) in causal_deps:
                ai, bi = op_to_idx.get(id(a)), op_to_idx.get(id(b))
                if ai is not None and bi is not None:
                    reachable[ai][bi] = True

            # Floyd-Warshall (小規模なので OK)
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        if reachable[i][k] and reachable[k][j]:
                            reachable[i][j] = True

            for i in range(n):
                if reachable[i][i]:
                    violations.append(f"  VIOLATION: Causal cycle involving {self.history[i]}")
                    break

            return len(violations) == 0, violations

    # --- テスト用の操作履歴 ---
    print("\n  --- Linearizable な履歴 ---")
    linear_history = [
        Operation(1, "write", "x", "a", 0.0, 1.0),
        Operation(2, "read",  "x", "a", 1.5, 2.0),  # write 完了後に read → OK
        Operation(1, "write", "x", "b", 2.5, 3.0),
        Operation(2, "read",  "x", "b", 3.5, 4.0),  # 最新値 → OK
    ]
    checker = ConsistencyChecker(linear_history)
    ok, viols = checker.check_linearizability()
    print(f"  Linearizable: {ok}")

    print("\n  --- Non-linearizable な履歴 (stale read) ---")
    non_linear_history = [
        Operation(1, "write", "x", "a", 0.0, 1.0),
        Operation(1, "write", "x", "b", 1.5, 2.5),
        Operation(2, "read",  "x", "a", 3.0, 3.5),  # write "b" 完了後に "a" を read → NG
    ]
    checker2 = ConsistencyChecker(non_linear_history)
    ok2, viols2 = checker2.check_linearizability()
    print(f"  Linearizable: {ok2}")
    for v in viols2:
        print(v)

    # --- 3.3 Session Guarantees ---
    print("\n" + "-" * 60)
    print("3.3 Session Guarantees")
    print("-" * 60)
    print("""
    クライアントセッション内の保証 (Bayou, 1994):

    1. Read Your Writes (RYW):
       自分が書いた値は必ず読める
       → Dynamo: sticky session / read from write quorum

    2. Monotonic Reads (MR):
       一度読んだ値より古い値は読まない
       → バージョンベクタで実装

    3. Monotonic Writes (MW):
       write は発行順に全レプリカに適用される
       → 因果順序付けで保証

    4. Writes Follow Reads (WFR):
       read の結果に依存する write は因果順序で適用
       → read で得た causal context を write に付与

    実装パターン:
      per-session version vector を追跡
      read 時: session_vv <= replica_vv なレプリカから読む
      write 時: session_vv を write に付与
    """)

    class SessionStore:
        """Session guarantees を提供するキーバリューストア"""
        def __init__(self, replicas: int = 3):
            self.stores: List[Dict[str, Tuple[Any, int]]] = [
                {} for _ in range(replicas)
            ]
            self.version = 0

        def write(self, key: str, value: Any, replica: int = 0):
            self.version += 1
            self.stores[replica][key] = (value, self.version)
            return self.version

        def replicate(self, from_r: int, to_r: int, key: str):
            if key in self.stores[from_r]:
                val, ver = self.stores[from_r][key]
                existing = self.stores[to_r].get(key)
                if existing is None or existing[1] < ver:
                    self.stores[to_r][key] = (val, ver)

        def read_with_ryw(self, key: str, session_write_version: int) -> Tuple[Any, int]:
            """Read Your Writes: session で書いた version 以上のレプリカから読む"""
            for store in self.stores:
                if key in store:
                    val, ver = store[key]
                    if ver >= session_write_version:
                        return val, ver
            return None, 0

    store = SessionStore(3)
    wv = store.write("user:1", {"name": "Alice"}, replica=0)
    print(f"  Write to replica 0: version={wv}")

    # RYW なし: replica 1 からは読めない可能性
    val, ver = store.stores[1].get("user:1", (None, 0))
    print(f"  Read from replica 1 (no RYW): value={val}")

    # RYW あり: write した version 以上を要求
    val, ver = store.read_with_ryw("user:1", wv)
    print(f"  Read with RYW (session_wv={wv}): value={val}")

    # レプリケーション後
    store.replicate(0, 1, "user:1")
    val, ver = store.stores[1].get("user:1", (None, 0))
    print(f"  Read from replica 1 (after replication): value={val}")


# ============================================================
# Chapter 4: Byzantine Fault Tolerance
# ============================================================

def chapter4_byzantine_bft():
    print("\n" + "=" * 70)
    print("Chapter 4: Byzantine Fault Tolerance")
    print("  悪意あるノードが存在する環境での合意")
    print("=" * 70)

    # --- 4.1 Byzantine Generals Problem ---
    print("\n" + "-" * 60)
    print("4.1 ビザンチン将軍問題")
    print("-" * 60)
    print("""
    問題設定 (Lamport, Shostak, Pease 1982):
      n 人の将軍が攻撃/撤退を合意する。
      最大 f 人の裏切り者(任意の振る舞い)がいる。

    定理: n >= 3f + 1 が必要
      f=1 なら n>=4, f=2 なら n>=7

    なぜ 3f+1 か:
      - f 個のノードがクラッシュ → 応答なし
      - f 個のノードが嘘をつく → 誤った応答
      - 正直ノード f+1 個で多数決に勝つ必要
      → 合計 f + f + (f+1) = 3f + 1
    """)

    # --- 4.2 なぜ 3f+1 が必要か: シミュレーション ---
    print("-" * 60)
    print("4.2 Byzantine Generals — シミュレーション")
    print("-" * 60)

    class ByzantineGeneral:
        def __init__(self, gid: int, is_traitor: bool = False):
            self.gid = gid
            self.is_traitor = is_traitor
            self.received_values: List[Tuple[int, str]] = []
            self.decision: Optional[str] = None

        def send_value(self, actual_value: str, to_gid: int) -> str:
            """裏切り者は相手によって異なる値を送る"""
            if self.is_traitor:
                # 偶数 ID には ATTACK, 奇数には RETREAT を送る
                return "ATTACK" if to_gid % 2 == 0 else "RETREAT"
            return actual_value

        def receive(self, from_gid: int, value: str):
            self.received_values.append((from_gid, value))

        def decide(self) -> str:
            """多数決で決定"""
            votes = defaultdict(int)
            for _, v in self.received_values:
                votes[v] += 1
            self.decision = max(votes, key=votes.get) if votes else "UNKNOWN"
            return self.decision

    def run_byzantine_simulation(n: int, f: int, commander_value: str):
        """ビザンチン将軍のシミュレーション"""
        generals = []
        traitor_ids = set(random.sample(range(n), f))
        for i in range(n):
            generals.append(ByzantineGeneral(i, is_traitor=(i in traitor_ids)))

        print(f"\n  n={n}, f={f}, traitors={traitor_ids}")
        print(f"  Commander (G0) value: {commander_value}")
        print(f"  3f+1 = {3*f+1}, n >= 3f+1: {n >= 3*f+1}")

        # Commander (G0) sends value to all
        commander = generals[0]
        for g in generals[1:]:
            val = commander.send_value(commander_value, g.gid)
            g.receive(commander.gid, val)

        # Lieutenants relay to each other
        for g in generals[1:]:
            received_val = dict(g.received_values).get(0, commander_value)
            for other in generals[1:]:
                if other.gid != g.gid:
                    relayed = g.send_value(received_val, other.gid)
                    other.receive(g.gid, relayed)

        # Each lieutenant decides
        decisions = {}
        for g in generals[1:]:
            if not g.is_traitor:
                d = g.decide()
                decisions[g.gid] = d
                print(f"  G{g.gid} (honest): decided {d}")

        honest_decisions = set(decisions.values())
        agreement = len(honest_decisions) <= 1
        print(f"  Agreement among honest generals: {agreement}")
        return agreement

    # n=4, f=1: 3f+1=4 → OK
    run_byzantine_simulation(n=4, f=1, commander_value="ATTACK")
    # n=3, f=1: 3f+1=4 > 3 → NG (合意不可能なケースあり)
    random.seed(42)
    run_byzantine_simulation(n=3, f=1, commander_value="ATTACK")

    # --- 4.3 PBFT (Practical Byzantine Fault Tolerance) ---
    print("\n" + "-" * 60)
    print("4.3 PBFT — Practical Byzantine Fault Tolerance")
    print("-" * 60)
    print("""
    PBFT (Castro & Liskov, 1999):
      ネットワークが部分同期であれば BFT 合意可能。

    3-phase protocol:
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │ PRE-PREPARE  │→  │   PREPARE    │→  │    COMMIT    │
    │ Leader→All   │   │ All→All      │   │ All→All      │
    │ <request,v,n>│   │ 2f+1 prepare │   │ 2f+1 commit  │
    └──────────────┘   └──────────────┘   └──────────────┘

    Phase 1 (Pre-prepare): Leader が request に sequence number を割り当て
    Phase 2 (Prepare): 各 replica が pre-prepare を検証、prepare を broadcast
      → 2f+1 の prepare 受信で "prepared" 状態 (= agreement on order)
    Phase 3 (Commit): prepared な replica が commit を broadcast
      → 2f+1 の commit 受信で実行・返信
    """)

    class PBFTNode:
        """簡略化 PBFT ノード"""
        def __init__(self, nid: int, n_total: int, is_byzantine: bool = False):
            self.nid = nid
            self.n_total = n_total
            self.f = (n_total - 1) // 3
            self.is_byzantine = is_byzantine
            self.prepares: Dict[int, Set[int]] = defaultdict(set)    # seq -> set of nids
            self.commits: Dict[int, Set[int]] = defaultdict(set)
            self.executed: List[int] = []

        def receive_prepare(self, seq: int, from_nid: int):
            self.prepares[seq].add(from_nid)

        def is_prepared(self, seq: int) -> bool:
            return len(self.prepares[seq]) >= 2 * self.f + 1

        def receive_commit(self, seq: int, from_nid: int):
            self.commits[seq].add(from_nid)

        def is_committed(self, seq: int) -> bool:
            return len(self.commits[seq]) >= 2 * self.f + 1

    # PBFT シミュレーション
    n_nodes = 4
    f_max = 1
    nodes = [PBFTNode(i, n_nodes, is_byzantine=(i == 3)) for i in range(n_nodes)]

    seq_num = 1
    print(f"\n  PBFT Simulation: n={n_nodes}, f={f_max}")
    print(f"  Byzantine node: N3")

    # Pre-prepare: leader (N0) assigns seq
    print(f"  Phase 1: Leader N0 sends Pre-prepare(seq={seq_num})")

    # Prepare: each node broadcasts prepare
    print(f"  Phase 2: Prepare broadcast")
    for sender in nodes:
        if sender.is_byzantine:
            # Byzantine node might not send or send wrong data
            print(f"    N{sender.nid} (byzantine): skips prepare")
            continue
        for receiver in nodes:
            if sender.nid != receiver.nid:
                receiver.receive_prepare(seq_num, sender.nid)

    for node in nodes:
        if not node.is_byzantine:
            prepared = node.is_prepared(seq_num)
            print(f"    N{node.nid}: prepares={len(node.prepares[seq_num])}, "
                  f"prepared={prepared}")

    # Commit: prepared nodes broadcast commit
    print(f"  Phase 3: Commit broadcast")
    for sender in nodes:
        if sender.is_byzantine or not sender.is_prepared(seq_num):
            continue
        for receiver in nodes:
            if sender.nid != receiver.nid:
                receiver.receive_commit(seq_num, sender.nid)

    for node in nodes:
        if not node.is_byzantine:
            committed = node.is_committed(seq_num)
            print(f"    N{node.nid}: commits={len(node.commits[seq_num])}, "
                  f"committed={committed}")
            if committed:
                node.executed.append(seq_num)

    # --- 4.4 Tendermint ---
    print("\n" + "-" * 60)
    print("4.4 Tendermint (BFT for Blockchain)")
    print("-" * 60)
    print("""
    Tendermint (Cosmos SDK):
      PBFT の改良版、ブロックチェーン向け。

    特徴:
      1. Propose → Prevote → Precommit (3-phase)
      2. Round ごとに Proposer をローテーション
      3. Locking mechanism: 一度 precommit したら戻れない
      4. 2/3+ の stake-weight で合意 (PoS + BFT)

    PBFT との違い:
      - PBFT: permissioned (固定メンバー)
      - Tendermint: permissionless-ish (validator set は変動)
      - Tendermint: optimistic responsiveness なし
        → 固定タイムアウトに依存

    Cosmos / CometBFT で使用。
    Ethereum 2.0 の Casper FFG も BFT ベース。
    """)


# ============================================================
# Chapter 5: Replication Deep Dive
# ============================================================

def chapter5_replication_deep():
    print("\n" + "=" * 70)
    print("Chapter 5: Replication Deep Dive")
    print("  Single-leader / Multi-leader / Leaderless の詳細")
    print("=" * 70)

    # --- 5.1 Single-Leader Replication ---
    print("\n" + "-" * 60)
    print("5.1 Single-Leader Replication")
    print("-" * 60)

    class SingleLeaderCluster:
        """Single-leader レプリケーションの実装"""
        def __init__(self, n_replicas: int = 3):
            self.leader_id = 0
            self.replicas: List[Dict[str, Tuple[Any, int]]] = [
                {} for _ in range(n_replicas)
            ]
            self.replication_log: List[Tuple[str, Any, int]] = []
            self.version = 0
            self.sync_replicas: Set[int] = {1}  # replica 1 は同期レプリカ
            self.fenced_leader: Optional[int] = None

        def write(self, key: str, value: Any, mode: str = "async") -> bool:
            """leader に write"""
            self.version += 1
            self.replicas[self.leader_id][key] = (value, self.version)
            self.replication_log.append((key, value, self.version))

            if mode == "sync":
                # 同期レプリカへの書き込みも完了してからACK
                for rid in self.sync_replicas:
                    self.replicas[rid][key] = (value, self.version)
                return True
            elif mode == "semi-sync":
                # 少なくとも1つの同期レプリカに書き込み
                for rid in list(self.sync_replicas)[:1]:
                    self.replicas[rid][key] = (value, self.version)
                return True
            else:  # async
                return True

        def async_replicate(self, replica_id: int):
            """非同期レプリケーション"""
            for key, value, ver in self.replication_log:
                existing = self.replicas[replica_id].get(key)
                if existing is None or existing[1] < ver:
                    self.replicas[replica_id][key] = (value, ver)

        def failover(self, new_leader: int):
            """リーダー障害時のフェイルオーバー"""
            old_leader = self.leader_id
            self.fenced_leader = old_leader  # 旧リーダーを fence
            self.leader_id = new_leader
            return old_leader

    cluster = SingleLeaderCluster(3)

    # 同期 vs 非同期
    cluster.write("user:1", "Alice", mode="sync")
    cluster.write("user:2", "Bob", mode="async")

    print("  Sync write: leader + sync replicas に書き込み完了後ACK")
    print(f"    Replica 0 (leader): {cluster.replicas[0]}")
    print(f"    Replica 1 (sync):   {cluster.replicas[1]}")
    print(f"    Replica 2 (async):  {cluster.replicas[2]}  ← まだ未反映")

    cluster.async_replicate(2)
    print(f"    Replica 2 (after async repl): {cluster.replicas[2]}")

    print("""
    Split-Brain Fencing (脳分裂防止):
    ┌─────────────────────────────────────────────────────────┐
    │ 問題: ネットワーク分断で旧リーダーがまだ write を受付  │
    │                                                         │
    │ 解決策:                                                 │
    │  1. Epoch/Fence Token: 新リーダーが epoch を increment  │
    │     古い epoch の write は拒否される                     │
    │  2. STONITH: 旧リーダーを強制シャットダウン             │
    │  3. Lease: リーダーは定期的にリース更新が必要           │
    │     リース失効 → 自動的にリーダー権限喪失              │
    └─────────────────────────────────────────────────────────┘
    """)

    # --- 5.2 Multi-Leader Replication ---
    print("-" * 60)
    print("5.2 Multi-Leader Replication")
    print("-" * 60)

    class MultiLeaderStore:
        """Multi-leader レプリケーション + 競合解決"""
        def __init__(self, n_leaders: int = 3):
            self.leaders: List[Dict[str, List[Tuple[Any, float, int]]]] = [
                {} for _ in range(n_leaders)
            ]
            # 各キーに対して (value, timestamp, leader_id) のリスト

        def write(self, leader_id: int, key: str, value: Any):
            ts = time.time() + random.uniform(0, 0.001)
            if key not in self.leaders[leader_id]:
                self.leaders[leader_id][key] = []
            self.leaders[leader_id][key].append((value, ts, leader_id))

        def replicate_and_resolve(self, strategy: str = "lww"):
            """全リーダー間でレプリケーション + 競合解決"""
            # 全 write を収集
            all_writes: Dict[str, List[Tuple[Any, float, int]]] = defaultdict(list)
            for lid, store in enumerate(self.leaders):
                for key, writes in store.items():
                    all_writes[key].extend(writes)

            # 競合解決
            resolved: Dict[str, Any] = {}
            for key, writes in all_writes.items():
                if strategy == "lww":
                    # Last-Writer-Wins: 最新 timestamp が勝つ
                    winner = max(writes, key=lambda w: w[1])
                    resolved[key] = winner[0]
                elif strategy == "merge":
                    # 全 value をマージ (set union)
                    resolved[key] = list({w[0] for w in writes})

            return resolved

    ml_store = MultiLeaderStore(3)
    ml_store.write(0, "doc:1", "version_A")
    ml_store.write(1, "doc:1", "version_B")
    ml_store.write(2, "doc:1", "version_C")

    lww_result = ml_store.replicate_and_resolve("lww")
    merge_result = ml_store.replicate_and_resolve("merge")
    print(f"  LWW 解決: doc:1 = {lww_result.get('doc:1')}")
    print(f"  Merge 解決: doc:1 = {merge_result.get('doc:1')}")

    print("""
    Multi-Leader の競合解決戦略:
    ┌───────────────────┬────────────────────────────────────┐
    │ LWW               │ 最新タイムスタンプが勝つ(データロス)│
    │ Merge             │ 全バージョンを保持 (CRDT 的)       │
    │ Custom logic      │ アプリケーション固有のマージ関数    │
    │ Conflict-free     │ CRDT で設計上競合を排除             │
    │ Operational Transform │ Google Docs 方式               │
    └───────────────────┴────────────────────────────────────┘
    """)

    # --- 5.3 Leaderless Replication ---
    print("-" * 60)
    print("5.3 Leaderless Replication (Dynamo-style)")
    print("-" * 60)

    class LeaderlessStore:
        """Dynamo-style leaderless ストア"""
        def __init__(self, n: int = 5, w: int = 3, r: int = 3):
            self.n = n
            self.w = w
            self.r = r
            self.nodes: List[Dict[str, Tuple[Any, int]]] = [{} for _ in range(n)]
            self.hints: Dict[int, List[Tuple[str, Any, int]]] = defaultdict(list)  # hinted handoff

        def write(self, key: str, value: Any, version: int,
                  unavailable: Set[int] = None) -> bool:
            """W ノードに write。unavailable ノードには hinted handoff"""
            unavailable = unavailable or set()
            written = 0
            hint_targets: List[int] = []

            for nid in range(self.n):
                if nid in unavailable:
                    hint_targets.append(nid)
                    continue
                self.nodes[nid][key] = (value, version)
                written += 1
                if written >= self.w:
                    break

            # Sloppy quorum: hint を別ノードに保存
            for target_nid in hint_targets:
                # 生存ノードに hint を保存
                for nid in range(self.n):
                    if nid not in unavailable:
                        self.hints[target_nid].append((key, value, version))
                        break

            return written >= self.w

        def read(self, key: str, unavailable: Set[int] = None) -> Optional[Any]:
            """R ノードから read。read repair を実行"""
            unavailable = unavailable or set()
            responses: List[Tuple[int, Any, int]] = []

            for nid in range(self.n):
                if nid in unavailable:
                    continue
                if key in self.nodes[nid]:
                    val, ver = self.nodes[nid][key]
                    responses.append((nid, val, ver))
                if len(responses) >= self.r:
                    break

            if not responses:
                return None

            # 最新バージョンを選択
            latest = max(responses, key=lambda x: x[2])

            # Read repair: 古いレプリカを更新
            for nid, val, ver in responses:
                if ver < latest[2]:
                    self.nodes[nid][key] = (latest[1], latest[2])

            return latest[1]

        def hinted_handoff(self, recovered_nid: int):
            """復旧ノードに hint を配送"""
            hints = self.hints.pop(recovered_nid, [])
            for key, value, version in hints:
                existing = self.nodes[recovered_nid].get(key)
                if existing is None or existing[1] < version:
                    self.nodes[recovered_nid][key] = (value, version)
            return len(hints)

        def anti_entropy(self):
            """全ノード間で Merkle tree ベースの同期 (簡易版)"""
            synced = 0
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    all_keys = set(self.nodes[i].keys()) | set(self.nodes[j].keys())
                    for key in all_keys:
                        vi = self.nodes[i].get(key, (None, -1))
                        vj = self.nodes[j].get(key, (None, -1))
                        if vi[1] > vj[1]:
                            self.nodes[j][key] = vi
                            synced += 1
                        elif vj[1] > vi[1]:
                            self.nodes[i][key] = vj
                            synced += 1
            return synced

    store = LeaderlessStore(n=5, w=3, r=3)

    # Normal write
    ok = store.write("key1", "valueA", version=1)
    print(f"  Write(key1, v=1): success={ok}, W={store.w}")

    # Write with node failure + hinted handoff
    ok = store.write("key2", "valueB", version=1, unavailable={3, 4})
    print(f"  Write(key2, v=1, nodes 3,4 down): success={ok}")
    print(f"    Hints pending for node 3: {len(store.hints.get(3, []))}")

    # Hinted handoff when node recovers
    delivered = store.hinted_handoff(3)
    print(f"    Hinted handoff to node 3: {delivered} hints delivered")

    # Read with read repair
    val = store.read("key1")
    print(f"  Read(key1): {val}")

    # Anti-entropy
    synced = store.anti_entropy()
    print(f"  Anti-entropy sync: {synced} keys synced")

    print("""
    Quorum Math: W + R > N → 少なくとも1つの最新レプリカから読める

    BUT: W+R>N は Linearizable を保証しない!
    ┌──────────────────────────────────────────────────────────┐
    │ 理由:                                                    │
    │  1. Sloppy quorum: 本来のノード以外に write → 重複なし  │
    │  2. Concurrent writes: LWW で片方が消える               │
    │  3. Write と read が部分的に重なる → stale read 可能    │
    │  4. 障害復旧中の read repair タイミング                  │
    │                                                          │
    │ Linearizable にするには:                                 │
    │  - Read 時に追加の write-back が必要 (ABD algorithm)     │
    │  - または Paxos/Raft で合意を取る                        │
    └──────────────────────────────────────────────────────────┘
    """)


# ============================================================
# Chapter 6: Time & Ordering
# ============================================================

def chapter6_time_and_ordering():
    print("\n" + "=" * 70)
    print("Chapter 6: Time & Ordering in Distributed Systems")
    print("  Lamport Clock / Vector Clock / HLC / TrueTime")
    print("=" * 70)

    # --- 6.1 Lamport Timestamps ---
    print("\n" + "-" * 60)
    print("6.1 Lamport Timestamps (Logical Clock)")
    print("-" * 60)
    print("""
    Lamport Clock (1978):
      ルール:
        1. イベント発生時: counter++
        2. メッセージ送信時: (counter, msg) を送る
        3. メッセージ受信時: counter = max(local, received) + 1

      性質:
        a → b ならば L(a) < L(b)        (因果順序を反映)
        L(a) < L(b) でも a → b とは限らない (逆は不成立)
    """)

    class LamportClock:
        def __init__(self, pid: str):
            self.pid = pid
            self.counter: int = 0
            self.log: List[str] = []

        def tick(self, event: str) -> int:
            self.counter += 1
            self.log.append(f"  {self.pid}: {event} @ L={self.counter}")
            return self.counter

        def send(self, event: str) -> Tuple[int, str]:
            ts = self.tick(f"send({event})")
            return ts, event

        def receive(self, sender_ts: int, event: str):
            self.counter = max(self.counter, sender_ts) + 1
            self.log.append(f"  {self.pid}: recv({event}) @ L={self.counter}")

    c1 = LamportClock("P1")
    c2 = LamportClock("P2")

    c1.tick("local_event")
    ts, msg = c1.send("hello")
    c2.tick("local_event")
    c2.tick("local_event")
    c2.receive(ts, msg)
    ts2, msg2 = c2.send("reply")
    c1.receive(ts2, msg2)

    for line in c1.log + c2.log:
        print(line)
    print(f"\n  Total order: P1={c1.counter}, P2={c2.counter}")

    # --- 6.2 Vector Clocks ---
    print("\n" + "-" * 60)
    print("6.2 Vector Clocks — 因果関係の完全な追跡")
    print("-" * 60)
    print("""
    Vector Clock: 各プロセスが全プロセスの counter を維持

    VC(a) < VC(b):  a → b (因果関係あり)
    VC(a) || VC(b): a と b は並行 (concurrent)

    Lamport Clock との違い:
      Lamport: 因果関係の一方向のみ (a→b ⇒ L(a)<L(b))
      Vector:  双方向 (a→b ⟺ VC(a)<VC(b))
    """)

    class VectorClock:
        def __init__(self, pid: str, all_pids: List[str]):
            self.pid = pid
            self.clock: Dict[str, int] = {p: 0 for p in all_pids}

        def tick(self):
            self.clock[self.pid] += 1

        def send(self) -> Dict[str, int]:
            self.tick()
            return dict(self.clock)

        def receive(self, sender_clock: Dict[str, int]):
            for p, ts in sender_clock.items():
                self.clock[p] = max(self.clock.get(p, 0), ts)
            self.tick()

        @staticmethod
        def compare(vc_a: Dict[str, int], vc_b: Dict[str, int]) -> str:
            """Compare two vector clocks"""
            all_keys = set(vc_a.keys()) | set(vc_b.keys())
            a_leq_b = all(vc_a.get(k, 0) <= vc_b.get(k, 0) for k in all_keys)
            b_leq_a = all(vc_b.get(k, 0) <= vc_a.get(k, 0) for k in all_keys)
            if a_leq_b and b_leq_a:
                return "EQUAL"
            elif a_leq_b:
                return "BEFORE"   # a → b
            elif b_leq_a:
                return "AFTER"    # b → a
            else:
                return "CONCURRENT"

        def __repr__(self):
            return f"VC({self.pid}: {dict(self.clock)})"

    pids = ["A", "B", "C"]
    clocks = {p: VectorClock(p, pids) for p in pids}

    # A does event, sends to B
    ts_a = clocks["A"].send()
    print(f"  A send: {ts_a}")
    clocks["B"].receive(ts_a)
    print(f"  B recv from A: {clocks['B'].clock}")

    # C does independent event
    clocks["C"].tick()
    print(f"  C independent: {clocks['C'].clock}")

    # Compare
    rel = VectorClock.compare(clocks["B"].clock, clocks["C"].clock)
    print(f"  B vs C: {rel}")  # Should be CONCURRENT

    # B sends to C
    ts_b = clocks["B"].send()
    clocks["C"].receive(ts_b)
    rel2 = VectorClock.compare(clocks["B"].clock, clocks["C"].clock)
    print(f"  After B→C: B vs C = {rel2}")  # B BEFORE C

    # --- 6.3 Hybrid Logical Clock (HLC) ---
    print("\n" + "-" * 60)
    print("6.3 Hybrid Logical Clock (HLC)")
    print("-" * 60)
    print("""
    HLC (Kulkarni et al. 2014):
      物理時計 + 論理カウンタの組合せ

    HLC = (physical_ts, logical_counter)
      - physical_ts: NTP 同期された物理時計
      - logical_counter: 同一 physical_ts 内の順序付け

    利点:
      - Vector Clock のような O(n) ストレージ不要
      - Lamport Clock より豊富な情報 (物理時刻に近い)
      - CockroachDB, YugabyteDB で採用
    """)

    class HybridLogicalClock:
        def __init__(self, pid: str):
            self.pid = pid
            self.l: int = 0   # physical component (ms)
            self.c: int = 0   # logical counter

        def _physical_time_ms(self) -> int:
            return int(time.time() * 1000)

        def tick(self) -> Tuple[int, int]:
            pt = self._physical_time_ms()
            if pt > self.l:
                self.l = pt
                self.c = 0
            else:
                self.c += 1
            return (self.l, self.c)

        def send(self) -> Tuple[int, int]:
            return self.tick()

        def receive(self, sender_l: int, sender_c: int) -> Tuple[int, int]:
            pt = self._physical_time_ms()
            if pt > self.l and pt > sender_l:
                self.l = pt
                self.c = 0
            elif self.l == sender_l:
                self.c = max(self.c, sender_c) + 1
            elif sender_l > self.l:
                self.l = sender_l
                self.c = sender_c + 1
            else:
                self.c += 1
            return (self.l, self.c)

        def __repr__(self):
            return f"HLC({self.pid}: l={self.l}, c={self.c})"

    hlc1 = HybridLogicalClock("N1")
    hlc2 = HybridLogicalClock("N2")

    ts1 = hlc1.send()
    print(f"  N1 send: HLC=({ts1[0]}, {ts1[1]})")
    ts2 = hlc2.receive(ts1[0], ts1[1])
    print(f"  N2 recv: HLC=({ts2[0]}, {ts2[1]})")
    ts3 = hlc2.send()
    print(f"  N2 send: HLC=({ts3[0]}, {ts3[1]})")

    # --- 6.4 TrueTime (Google Spanner) ---
    print("\n" + "-" * 60)
    print("6.4 TrueTime — Google Spanner のタイムスタンプ")
    print("-" * 60)
    print("""
    TrueTime API:
      tt.now() → [earliest, latest]  (区間を返す)

    不確実性区間 ε (通常 1-7ms):
      - GPS + 原子時計で ε を最小化
      - Spanner: commit 時に ε だけ待つ (commit-wait)
        → 外部一貫性 (external consistency) を保証

    ┌───────────────────────────────────────────────────────┐
    │ Commit-Wait Protocol:                                 │
    │  1. Acquire locks                                     │
    │  2. Choose commit timestamp s = TT.now().latest       │
    │  3. Wait until TT.now().earliest > s (commit-wait)    │
    │  4. Release locks and apply                           │
    │                                                       │
    │  これにより: T1.commit < T2.start ⇒ s1 < s2         │
    │  = 外部一貫性 (linearizability と同等)                │
    └───────────────────────────────────────────────────────┘
    """)

    class TrueTime:
        """TrueTime の概念実装"""
        def __init__(self, epsilon_ms: float = 5.0):
            self.epsilon = epsilon_ms / 1000.0

        def now(self) -> Tuple[float, float]:
            t = time.time()
            return (t - self.epsilon, t + self.epsilon)

        def after(self, timestamp: float) -> bool:
            earliest, _ = self.now()
            return earliest > timestamp

        def before(self, timestamp: float) -> bool:
            _, latest = self.now()
            return latest < timestamp

    class TimestampOracle:
        """Timestamp Oracle (TiDB/Percolator style)"""
        def __init__(self):
            self.current_ts: int = 0
            self._physical_base = int(time.time() * 1000)

        def get_timestamp(self) -> int:
            self.current_ts += 1
            return self._physical_base + self.current_ts

        def get_batch(self, n: int) -> List[int]:
            result = []
            for _ in range(n):
                result.append(self.get_timestamp())
            return result

    tso = TimestampOracle()
    batch = tso.get_batch(5)
    print(f"  TSO batch: {[ts - batch[0] for ts in batch]} (relative)")
    print("  → 厳密に単調増加するタイムスタンプを中央集権的に発行")
    print("  → TiDB/TiKV で採用。single-point-of-failure リスクあり")


# ============================================================
# Chapter 7: Formal Verification & Testing
# ============================================================

def chapter7_formal_verification():
    print("\n" + "=" * 70)
    print("Chapter 7: Formal Verification & Chaos Testing")
    print("  TLA+, Safety vs Liveness, Jepsen")
    print("=" * 70)

    # --- 7.1 TLA+ Concepts ---
    print("\n" + "-" * 60)
    print("7.1 TLA+ (Temporal Logic of Actions)")
    print("-" * 60)
    print("""
    TLA+ (Lamport):
      分散システムの仕様記述と検証のための形式言語。

    基本概念:
      State Machine: システムは状態の集合と遷移関数
      Invariant:     全到達可能状態で true な述語
      Safety:        「悪いことは起きない」(invariant)
      Liveness:      「良いことがいつか起きる」(progress)

    TLA+ spec の構造:
      INIT     : 初期状態の定義
      Next     : 状態遷移の定義
      Spec     : Init ∧ □[Next]_vars ∧ Liveness
      Invariant: □(Safety_Property)
    """)

    # --- 7.2 Safety vs Liveness ---
    print("-" * 60)
    print("7.2 Safety vs Liveness in Practice")
    print("-" * 60)
    print("""
    Safety (安全性):
      "Something bad never happens"
      例: 2つのノードが異なる値に decide しない
      検証: 到達可能な全状態を探索 (model checking)

    Liveness (活性):
      "Something good eventually happens"
      例: 全正常ノードがいつか decide する
      検証: 公平性条件 (fairness) が必要
        Weak fairness: 常に有効なアクションはいつか実行される
        Strong fairness: 無限に頻繁に有効なアクションはいつか実行される
    """)

    class SimpleModelChecker:
        """
        TLA+ 的な不変条件チェッカーの簡易実装。
        状態空間を BFS で探索し、invariant 違反を検出。
        """
        def __init__(self):
            self.states_explored = 0
            self.violations: List[str] = []

        def check_invariant(
            self,
            init_state: Any,
            next_states_fn,  # state -> List[state]
            invariant_fn,    # state -> bool
            max_states: int = 10000,
        ) -> bool:
            visited = set()
            queue = [init_state]

            while queue and self.states_explored < max_states:
                state = queue.pop(0)
                state_key = str(state)
                if state_key in visited:
                    continue
                visited.add(state_key)
                self.states_explored += 1

                if not invariant_fn(state):
                    self.violations.append(f"  INVARIANT VIOLATION at state: {state}")
                    return False

                for next_s in next_states_fn(state):
                    if str(next_s) not in visited:
                        queue.append(next_s)

            return True

    # 例: 2-process mutex の検証
    # state = (pc1, pc2, lock)  pc in {"idle", "trying", "critical"}
    def mutex_next(state):
        pc1, pc2, lock = state
        next_states = []
        # Process 1 transitions
        if pc1 == "idle":
            next_states.append(("trying", pc2, lock))
        if pc1 == "trying" and not lock:
            next_states.append(("critical", pc2, True))
        if pc1 == "critical":
            next_states.append(("idle", pc2, False))
        # Process 2 transitions
        if pc2 == "idle":
            next_states.append((pc1, "trying", lock))
        if pc2 == "trying" and not lock:
            next_states.append((pc1, "critical", True))
        if pc2 == "critical":
            next_states.append((pc1, "idle", False))
        return next_states

    def mutex_safety(state):
        pc1, pc2, _ = state
        # Safety: 同時に critical section に入らない
        return not (pc1 == "critical" and pc2 == "critical")

    checker = SimpleModelChecker()
    safe = checker.check_invariant(
        init_state=("idle", "idle", False),
        next_states_fn=mutex_next,
        invariant_fn=mutex_safety,
    )
    print(f"  Mutex safety check: {'PASS' if safe else 'FAIL'}")
    print(f"  States explored: {checker.states_explored}")
    for v in checker.violations:
        print(v)

    # --- 7.3 Jepsen & Chaos Testing ---
    print("\n" + "-" * 60)
    print("7.3 Jepsen / Chaos Testing")
    print("-" * 60)
    print("""
    Jepsen (Kyle Kingsbury):
      分散データベースの一貫性を検証するフレームワーク。

    テスト手法:
      1. クラスタを構築
      2. クライアントから並行操作を発行
      3. 障害を注入 (ネットワーク分断, ノードクラッシュ, clock skew)
      4. 操作履歴を収集
      5. 一貫性モデルに対して検証

    発見された有名なバグ:
      - MongoDB: stale reads during network partition
      - Elasticsearch: split-brain data loss
      - CockroachDB: serializable violation (修正済)
      - etcd: watch notification loss
      - Redis Cluster: data loss on failover

    Chaos Engineering (Netflix):
      - Chaos Monkey: ランダムにインスタンスを kill
      - Chaos Kong: リージョン全体を停止
      - Latency Monkey: レイテンシ注入
      - FIT (Failure Injection Testing): 依存サービス障害

    原則:
      1. 定常状態の仮説を立てる
      2. 実験群と対照群で比較
      3. 本番環境で実行 (blast radius を制限)
      4. 自動化して継続的に実行
    """)


# ============================================================
# Chapter 8: Tier 1-4 Learning Priority
# ============================================================

def chapter8_tier_priority():
    print("\n" + "=" * 70)
    print("Chapter 8: 分散システム理論 — 学習優先度")
    print("=" * 70)
    print("""
    ┌──────┬────────────────────────┬──────────────────────────────────┐
    │ Tier │ トピック               │ 理由                             │
    ├──────┼────────────────────────┼──────────────────────────────────┤
    │  1   │ CAP/PACELC            │ 面接の第一声で聞かれる           │
    │  1   │ Replication (Ch5)     │ 全 DB の基礎。障害時の動作理解   │
    │  1   │ Consensus (Raft)      │ etcd/ZooKeeper の原理。必須      │
    │  1   │ Consistency Models    │ 「linearizable ですか?」即答必要 │
    ├──────┼────────────────────────┼──────────────────────────────────┤
    │  2   │ Paxos (理論)          │ Raft の元ネタ。Staff+ で差別化   │
    │  2   │ Vector Clock / HLC    │ 因果一貫性の実装。DynamoDB 系    │
    │  2   │ Quorum Math           │ W+R>N の限界を説明できるか       │
    │  2   │ Jepsen 概念           │ 「テストどうする?」への回答      │
    ├──────┼────────────────────────┼──────────────────────────────────┤
    │  3   │ FLP Impossibility     │ 「なぜ timeout?」の根本理由      │
    │  3   │ PBFT / Byzantine      │ ブロックチェーン系で必須         │
    │  3   │ TrueTime / Spanner    │ Google 系面接で頻出              │
    │  3   │ Formal Verification   │ TLA+ を読める = 設計力の証明     │
    ├──────┼────────────────────────┼──────────────────────────────────┤
    │  4   │ Ben-Or Protocol       │ Randomized consensus 理論        │
    │  4   │ Failure Detectors     │ Chandra-Toueg 理論               │
    │  4   │ Tendermint 詳細       │ Blockchain 特化                  │
    │  4   │ ABD Algorithm         │ Quorum + linearizable 証明       │
    └──────┴────────────────────────┴──────────────────────────────────┘

    学習パス:
      Week 1-2: Tier 1 — DDIA Ch5-9 を精読
      Week 3-4: Tier 2 — 実装しながら理解
      Week 5-6: Tier 3 — 論文を読む (FLP, Paxos Made Simple)
      Week 7+:  Tier 4 — 興味に応じて深掘り

    推薦図書:
      1. DDIA (Kleppmann) — バイブル。Ch5-9 が核心
      2. "Paxos Made Simple" (Lamport) — 9ページの名論文
      3. "In Search of an Understandable Consensus Algorithm" — Raft 論文
      4. "Time, Clocks, and the Ordering of Events" (Lamport 1978) — 原典
      5. Jepsen analyses — https://jepsen.io/analyses

    面接での使い方:
      「Dynamo-style leaderless store を設計してください」
      → Quorum, Vector Clock, Read Repair, Anti-Entropy を説明
      → 「ただし W+R>N でも linearizable ではない」まで言及
      → Sloppy Quorum と Hinted Handoff の tradeoff を議論
    """)


# ============================================================
# Main
# ============================================================

def main():
    print("*" * 70)
    print("  Distributed Systems Theory")
    print("  FLP Impossibility / Paxos / Consistency / BFT / Replication / Time")
    print("  DDIA + Distributed Algorithms Level")
    print("*" * 70)

    chapter1_flp_impossibility()
    chapter2_paxos()
    chapter3_consistency_models()
    chapter4_byzantine_bft()
    chapter5_replication_deep()
    chapter6_time_and_ordering()
    chapter7_formal_verification()
    chapter8_tier_priority()

    print("\n" + "=" * 70)
    print("  Complete! 分散システム理論の全7章 + 学習優先度を実行しました。")
    print("=" * 70)


if __name__ == "__main__":
    main()
