"""
===============================================================================
 OS & ハードウェア ディープガイド
 ― CSAPP/OSTEP レベル: CPU パイプラインから NUMA まで ―
===============================================================================
Python 標準ライブラリのみ使用 / そのまま実行可能

目次:
  1. CPU パイプライン (5段, ハザード, 分岐予測)
  2. キャッシュシミュレータ (セットアソシアティブ, MESI, AMAT)
  3. 仮想メモリ (4レベルページテーブル, TLB, CoW)
  4. プロセス & スケジューリング (CFS, Work-Stealing)
  5. I/O モデル (Reactor, Proactor, select/poll/epoll)
  6. 割り込み & NUMA (Top-half/Bottom-half, DMA)
  7. 優先度マップ (Tier 1-4)
"""

import time
import random
import heapq
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Tuple, Set


# ============================================================================
# 1. CPU パイプライン (5段パイプライン, ハザード検出, 分岐予測)
# ============================================================================

def section_cpu_pipeline():
    """
    ■ 5段パイプライン (クラシック RISC)
      IF (Instruction Fetch) → ID (Decode) → EX (Execute)
      → MEM (Memory Access) → WB (Write Back)

    ■ パイプラインハザード
      (1) データハザード (RAW: Read After Write)
          - 前の命令の結果を後の命令が使う → ストール or フォワーディング
      (2) 制御ハザード (分岐)
          - 分岐結果が確定するまで次の命令が不明 → 分岐予測
      (3) 構造ハザード
          - 同じリソースを同時に使おうとする → 別ポートで回避

    ■ 分岐予測 (2-bit Saturating Counter)
      状態: Strongly Not Taken(00) → Weakly Not Taken(01)
           → Weakly Taken(10) → Strongly Taken(11)
      予測ミスペナルティ = パイプライン深さに比例
    """
    print("=== CPU パイプライン シミュレーション ===\n")

    # --- 命令の定義 ---
    @dataclass
    class Instruction:
        opcode: str          # ADD, SUB, MUL, LOAD, STORE, BEQ, NOP
        rd: Optional[str]    # destination register
        rs1: Optional[str]   # source register 1
        rs2: Optional[str]   # source register 2
        imm: int = 0         # immediate value
        label: str = ""      # branch target label

        def __repr__(self):
            if self.opcode == "NOP":
                return "NOP"
            parts = [self.opcode]
            if self.rd:
                parts.append(self.rd)
            if self.rs1:
                parts.append(self.rs1)
            if self.rs2:
                parts.append(self.rs2)
            if self.imm:
                parts.append(f"#{self.imm}")
            return " ".join(parts)

    # --- 2-bit 飽和カウンタ分岐予測器 ---
    class BranchPredictor:
        """
        2-bit Saturating Counter:
          0 = Strongly Not Taken, 1 = Weakly Not Taken,
          2 = Weakly Taken,       3 = Strongly Taken
        予測: counter >= 2 → Taken
        """
        def __init__(self):
            self.table: Dict[int, int] = defaultdict(lambda: 1)  # 初期: Weakly Not Taken
            self.hits = 0
            self.misses = 0

        def predict(self, pc: int) -> bool:
            return self.table[pc] >= 2

        def update(self, pc: int, actually_taken: bool):
            old = self.table[pc]
            if actually_taken:
                self.table[pc] = min(3, old + 1)
            else:
                self.table[pc] = max(0, old - 1)

            predicted = old >= 2
            if predicted == actually_taken:
                self.hits += 1
            else:
                self.misses += 1

        def accuracy(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0

    # --- パイプラインステージ ---
    class PipelineStage(Enum):
        IF = "IF"
        ID = "ID"
        EX = "EX"
        MEM = "MEM"
        WB = "WB"

    # --- 5段パイプラインシミュレータ ---
    class PipelineSimulator:
        def __init__(self, instructions: List[Instruction]):
            self.instructions = instructions
            self.registers: Dict[str, int] = defaultdict(int)
            self.bp = BranchPredictor()
            self.cycle = 0
            self.completed = 0
            self.stalls = 0
            self.forwards = 0
            # パイプラインレジスタ: 各ステージの命令 (None = バブル)
            self.pipeline: Dict[str, Optional[Tuple[int, Instruction]]] = {
                "IF": None, "ID": None, "EX": None, "MEM": None, "WB": None
            }
            self.pc = 0
            # フォワーディングパス: (reg, value) をEX/MEMから供給
            self.forward_ex: Dict[str, int] = {}
            self.forward_mem: Dict[str, int] = {}

        def detect_raw_hazard(self, inst: Instruction) -> Optional[str]:
            """RAW ハザード検出: ID段の命令が EX/MEM段の結果を必要とするか"""
            sources = [inst.rs1, inst.rs2]
            # EX段の命令の書き込み先をチェック
            if self.pipeline["EX"]:
                ex_inst = self.pipeline["EX"][1]
                if ex_inst.rd and ex_inst.rd in sources:
                    if ex_inst.opcode == "LOAD":
                        # LOAD-USE: フォワーディングでも1サイクルストール必要
                        return f"LOAD-USE hazard: {ex_inst.rd}"
            return None  # フォワーディングで解決可能 or ハザードなし

        def check_forwarding(self, inst: Instruction) -> List[str]:
            """フォワーディングパスで解決できるハザードを検出"""
            forwarded = []
            sources = [inst.rs1, inst.rs2]
            for src in sources:
                if src and src in self.forward_ex:
                    forwarded.append(f"  Forward EX→ID: {src}={self.forward_ex[src]}")
                    self.registers[src] = self.forward_ex[src]
                elif src and src in self.forward_mem:
                    forwarded.append(f"  Forward MEM→ID: {src}={self.forward_mem[src]}")
                    self.registers[src] = self.forward_mem[src]
            return forwarded

        def run(self, verbose: bool = True) -> Dict:
            max_cycles = len(self.instructions) * 5 + 20
            stages_order = ["WB", "MEM", "EX", "ID", "IF"]

            while self.cycle < max_cycles:
                self.cycle += 1
                stall_this_cycle = False
                self.forward_ex = {}
                self.forward_mem = {}

                # --- WB ---
                if self.pipeline["WB"]:
                    _, wb_inst = self.pipeline["WB"]
                    if wb_inst.rd and wb_inst.opcode != "STORE":
                        pass  # レジスタ書き込み完了
                    self.completed += 1

                # --- MEM: フォワーディング値を設定 ---
                if self.pipeline["MEM"]:
                    _, mem_inst = self.pipeline["MEM"]
                    if mem_inst.rd:
                        val = self.registers.get(mem_inst.rd, 0)
                        self.forward_mem[mem_inst.rd] = val

                # --- EX: 演算実行 + フォワーディング値を設定 ---
                if self.pipeline["EX"]:
                    _, ex_inst = self.pipeline["EX"]
                    if ex_inst.opcode in ("ADD", "SUB", "MUL"):
                        a = self.registers.get(ex_inst.rs1, 0)
                        b = self.registers.get(ex_inst.rs2, 0) if ex_inst.rs2 else ex_inst.imm
                        if ex_inst.opcode == "ADD":
                            self.registers[ex_inst.rd] = a + b
                        elif ex_inst.opcode == "SUB":
                            self.registers[ex_inst.rd] = a - b
                        elif ex_inst.opcode == "MUL":
                            self.registers[ex_inst.rd] = a * b
                    if ex_inst.rd:
                        self.forward_ex[ex_inst.rd] = self.registers.get(ex_inst.rd, 0)

                # --- ID: ハザード検出 ---
                if self.pipeline["ID"]:
                    _, id_inst = self.pipeline["ID"]
                    hazard = self.detect_raw_hazard(id_inst)
                    if hazard:
                        stall_this_cycle = True
                        self.stalls += 1
                        if verbose:
                            print(f"  Cycle {self.cycle}: STALL - {hazard}")
                    else:
                        fwd = self.check_forwarding(id_inst)
                        if fwd:
                            self.forwards += 1
                            if verbose:
                                for f in fwd:
                                    print(f"  Cycle {self.cycle}: {f}")

                # --- ステージ遷移 ---
                if stall_this_cycle:
                    self.pipeline["WB"] = self.pipeline["MEM"]
                    self.pipeline["MEM"] = self.pipeline["EX"]
                    self.pipeline["EX"] = None  # バブル挿入
                    # ID, IF はストール (進まない)
                else:
                    self.pipeline["WB"] = self.pipeline["MEM"]
                    self.pipeline["MEM"] = self.pipeline["EX"]
                    self.pipeline["EX"] = self.pipeline["ID"]
                    self.pipeline["ID"] = self.pipeline["IF"]
                    # 次の命令をフェッチ
                    if self.pc < len(self.instructions):
                        self.pipeline["IF"] = (self.pc, self.instructions[self.pc])
                        self.pc += 1
                    else:
                        self.pipeline["IF"] = None

                # 全ステージ空なら終了
                if all(v is None for v in self.pipeline.values()) and self.pc >= len(self.instructions):
                    break

            cpi = self.cycle / max(self.completed, 1)
            stats = {
                "cycles": self.cycle,
                "completed": self.completed,
                "stalls": self.stalls,
                "forwards": self.forwards,
                "CPI": round(cpi, 2),
                "branch_accuracy": round(self.bp.accuracy() * 100, 1),
            }
            return stats

    # --- デモ実行 ---
    program = [
        Instruction("ADD", "R1", "R0", None, imm=10),   # R1 = R0 + 10
        Instruction("ADD", "R2", "R0", None, imm=20),   # R2 = R0 + 20
        Instruction("ADD", "R3", "R1", "R2"),            # R3 = R1 + R2 (RAW: R1, R2)
        Instruction("SUB", "R4", "R3", None, imm=5),    # R4 = R3 - 5 (RAW: R3)
        Instruction("MUL", "R5", "R4", "R1"),            # R5 = R4 * R1 (RAW: R4)
        Instruction("LOAD", "R6", "R5", None),           # R6 = Mem[R5]
        Instruction("ADD", "R7", "R6", "R5"),            # R7 = R6 + R5 (LOAD-USE!)
        Instruction("ADD", "R8", "R7", None, imm=1),    # R8 = R7 + 1
    ]

    print("プログラム:")
    for i, inst in enumerate(program):
        print(f"  [{i}] {inst}")
    print()

    sim = PipelineSimulator(program)
    stats = sim.run(verbose=True)
    print(f"\n--- パイプライン統計 ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    # --- 分岐予測デモ ---
    print("\n--- 2-bit 分岐予測器デモ ---")
    bp = BranchPredictor()
    # 典型的なループ: TTTTTTTTTN (9回taken, 1回not taken)
    pattern = [True] * 9 + [False]
    print(f"パターン: {''.join('T' if t else 'N' for t in pattern)} × 5ループ")
    for loop in range(5):
        for i, taken in enumerate(pattern):
            pred = bp.predict(0)
            bp.update(0, taken)
    print(f"  予測精度: {bp.accuracy()*100:.1f}%")
    print(f"  ヒット: {bp.hits}, ミス: {bp.misses}")

    print(f"""
■ CPI (Cycles Per Instruction) の目安:
  理想パイプライン: CPI = 1.0
  ストールあり:     CPI = 1.0 + ストール率
  スーパースカラ:   CPI < 1.0 (IPC > 1)
  現代CPU (Zen4):   IPC ≈ 5-6 (理論上)

■ 分岐予測ミスのコスト:
  パイプライン深さが深いほど大きい
  Intel Alder Lake: ~15-20 サイクル penalty
  TAGE予測器: 精度 97%+ (複雑な履歴パターンを学習)
""")


# ============================================================================
# 2. キャッシュシミュレータ (セットアソシアティブ, MESI, AMAT)
# ============================================================================

def section_cache_simulator():
    """
    ■ キャッシュ階層 (典型的な現代CPU)
      L1D: 32-48KB, 4-5 cycle,  8-12way
      L1I: 32-48KB, 4-5 cycle,  8way
      L2:  256KB-1MB, 12-14 cycle, 8-16way
      L3:  16-96MB, 30-50 cycle, 16way (共有)
      Main: 8-64GB, 100+ cycle

    ■ AMAT (Average Memory Access Time)
      AMAT = Hit Time + Miss Rate × Miss Penalty
      多層: AMAT = L1 Hit Time + L1 Miss Rate × (L2 Hit Time + L2 Miss Rate × ...)

    ■ MESI プロトコル (キャッシュコヒーレンシ)
      M (Modified):  自分だけが持ち、メモリと不一致
      E (Exclusive): 自分だけが持ち、メモリと一致
      S (Shared):    複数コアが持ち、メモリと一致
      I (Invalid):   無効
    """
    print("=== キャッシュシミュレータ ===\n")

    # --- キャッシュライン ---
    @dataclass
    class CacheLine:
        valid: bool = False
        tag: int = 0
        data: int = 0
        dirty: bool = False
        # LRU
        last_access: int = 0
        # Clock
        reference_bit: bool = False

    # --- セットアソシアティブキャッシュ ---
    class SetAssociativeCache:
        def __init__(self, total_size: int = 256, line_size: int = 64,
                     associativity: int = 4, replacement: str = "LRU"):
            self.line_size = line_size
            self.associativity = associativity
            self.num_sets = total_size // (line_size * associativity)
            self.replacement = replacement  # "LRU" or "Clock"
            self.sets: List[List[CacheLine]] = [
                [CacheLine() for _ in range(associativity)]
                for _ in range(self.num_sets)
            ]
            self.clock_hands: Dict[int, int] = defaultdict(int)
            self.access_count = 0
            self.hits = 0
            self.misses = 0
            self.evictions = 0

        def _get_set_tag(self, address: int) -> Tuple[int, int]:
            block_addr = address // self.line_size
            set_index = block_addr % self.num_sets
            tag = block_addr // self.num_sets
            return set_index, tag

        def access(self, address: int, write: bool = False) -> bool:
            self.access_count += 1
            set_idx, tag = self._get_set_tag(address)
            cache_set = self.sets[set_idx]

            # ヒット判定
            for line in cache_set:
                if line.valid and line.tag == tag:
                    self.hits += 1
                    line.last_access = self.access_count
                    line.reference_bit = True
                    if write:
                        line.dirty = True
                    return True

            # ミス → 置換
            self.misses += 1
            victim = self._find_victim(set_idx)
            if victim.valid:
                self.evictions += 1
            victim.valid = True
            victim.tag = tag
            victim.dirty = write
            victim.last_access = self.access_count
            victim.reference_bit = True
            return False

        def _find_victim(self, set_idx: int) -> CacheLine:
            cache_set = self.sets[set_idx]
            # 空きラインがあればそれを使う
            for line in cache_set:
                if not line.valid:
                    return line

            if self.replacement == "LRU":
                return min(cache_set, key=lambda l: l.last_access)
            elif self.replacement == "Clock":
                return self._clock_replace(set_idx)
            return cache_set[0]

        def _clock_replace(self, set_idx: int) -> CacheLine:
            cache_set = self.sets[set_idx]
            hand = self.clock_hands[set_idx]
            while True:
                line = cache_set[hand % self.associativity]
                if not line.reference_bit:
                    self.clock_hands[set_idx] = (hand + 1) % self.associativity
                    return line
                line.reference_bit = False
                hand = (hand + 1) % self.associativity

        def miss_rate(self) -> float:
            return self.misses / self.access_count if self.access_count else 0.0

        def stats(self) -> Dict:
            return {
                "accesses": self.access_count,
                "hits": self.hits,
                "misses": self.misses,
                "miss_rate": f"{self.miss_rate()*100:.2f}%",
                "evictions": self.evictions,
            }

    # --- MESI プロトコルシミュレータ ---
    class MESIState(Enum):
        MODIFIED = "M"
        EXCLUSIVE = "E"
        SHARED = "S"
        INVALID = "I"

    class MESIProtocol:
        """4コアのキャッシュコヒーレンシを MESI でシミュレーション"""
        def __init__(self, num_cores: int = 4):
            self.num_cores = num_cores
            # core_id -> {address -> state}
            self.cache_states: List[Dict[int, MESIState]] = [
                {} for _ in range(num_cores)
            ]
            self.transitions: List[str] = []

        def read(self, core_id: int, addr: int) -> MESIState:
            current = self.cache_states[core_id].get(addr, MESIState.INVALID)

            if current in (MESIState.MODIFIED, MESIState.EXCLUSIVE, MESIState.SHARED):
                return current  # ヒット

            # INVALID → バスでスヌープ
            others_have = False
            for i in range(self.num_cores):
                if i == core_id:
                    continue
                other_state = self.cache_states[i].get(addr, MESIState.INVALID)
                if other_state == MESIState.MODIFIED:
                    # Modified → 書き戻し + Shared に遷移
                    self.cache_states[i][addr] = MESIState.SHARED
                    self.transitions.append(
                        f"Core{i} {addr:#06x}: M→S (snoop flush)")
                    others_have = True
                elif other_state == MESIState.EXCLUSIVE:
                    self.cache_states[i][addr] = MESIState.SHARED
                    self.transitions.append(
                        f"Core{i} {addr:#06x}: E→S (snoop)")
                    others_have = True
                elif other_state == MESIState.SHARED:
                    others_have = True

            new_state = MESIState.SHARED if others_have else MESIState.EXCLUSIVE
            self.cache_states[core_id][addr] = new_state
            self.transitions.append(
                f"Core{core_id} {addr:#06x}: I→{new_state.value} (read)")
            return new_state

        def write(self, core_id: int, addr: int) -> MESIState:
            current = self.cache_states[core_id].get(addr, MESIState.INVALID)

            if current == MESIState.MODIFIED:
                return current  # すでに独占 & dirty

            # 他のコアを Invalidate
            for i in range(self.num_cores):
                if i == core_id:
                    continue
                other_state = self.cache_states[i].get(addr, MESIState.INVALID)
                if other_state != MESIState.INVALID:
                    self.cache_states[i][addr] = MESIState.INVALID
                    self.transitions.append(
                        f"Core{i} {addr:#06x}: {other_state.value}→I (invalidate)")

            old_str = current.value
            self.cache_states[core_id][addr] = MESIState.MODIFIED
            self.transitions.append(
                f"Core{core_id} {addr:#06x}: {old_str}→M (write)")
            return MESIState.MODIFIED

    # --- デモ実行 ---
    print("--- セットアソシアティブキャッシュ (LRU vs Clock) ---")
    random.seed(42)
    # 局所性のあるアクセスパターン
    addresses = []
    for _ in range(200):
        base = random.choice([0x1000, 0x2000, 0x3000])  # 3つのホットスポット
        offset = random.randint(0, 255)
        addresses.append(base + offset)
    # たまにコールドアクセス
    for _ in range(50):
        addresses.append(random.randint(0x8000, 0xFFFF))
    random.shuffle(addresses)

    for policy in ["LRU", "Clock"]:
        cache = SetAssociativeCache(
            total_size=256, line_size=64, associativity=4, replacement=policy)
        for addr in addresses:
            cache.access(addr)
        print(f"\n  {policy} 置換:")
        for k, v in cache.stats().items():
            print(f"    {k}: {v}")

    # AMAT 計算
    print("\n--- AMAT 計算 ---")
    l1_hit_time = 4    # cycles
    l1_miss_rate = 0.05
    l2_hit_time = 12
    l2_miss_rate = 0.20
    mem_access = 100

    amat = l1_hit_time + l1_miss_rate * (l2_hit_time + l2_miss_rate * mem_access)
    print(f"  L1 Hit Time: {l1_hit_time} cycles, Miss Rate: {l1_miss_rate*100}%")
    print(f"  L2 Hit Time: {l2_hit_time} cycles, Miss Rate: {l2_miss_rate*100}%")
    print(f"  Memory Access: {mem_access} cycles")
    print(f"  AMAT = {l1_hit_time} + {l1_miss_rate} × ({l2_hit_time} + {l2_miss_rate} × {mem_access})")
    print(f"       = {amat:.1f} cycles")

    # MESI デモ
    print("\n--- MESI プロトコル デモ ---")
    mesi = MESIProtocol(num_cores=4)
    print("  操作シーケンス:")
    ops = [
        (0, "read", 0x1000),   # Core0 が排他的に取得
        (1, "read", 0x1000),   # Core1 が読む → 両方 Shared
        (0, "write", 0x1000),  # Core0 が書く → Core1 を Invalidate
        (2, "read", 0x1000),   # Core2 が読む → Core0 は flush
        (3, "write", 0x1000),  # Core3 が書く → 全員 Invalidate
    ]
    for core, op, addr in ops:
        print(f"    Core{core} {op} {addr:#06x}")
        if op == "read":
            mesi.read(core, addr)
        else:
            mesi.write(core, addr)
    print("\n  状態遷移ログ:")
    for t in mesi.transitions:
        print(f"    {t}")

    # False Sharing デモ
    print(f"""
--- False Sharing ---
  同じキャッシュラインに複数コアが異なる変数で書き込むと
  MESI Invalidation が頻発し性能が大幅に劣化する。

  例: struct {{ int core0_counter; int core1_counter; }}
  → 64B ライン内に両方の変数 → 書くたびに相手の I→S→I の往復

  対策:
    - パディング: __attribute__((aligned(64))) で変数をラインに分離
    - Java: @Contended アノテーション
    - Linux: __cacheline_aligned_in_smp マクロ
""")


# ============================================================================
# 3. 仮想メモリ (4レベルページテーブル, TLB, CoW)
# ============================================================================

def section_virtual_memory():
    """
    ■ x86-64 仮想アドレス (48-bit)
      [PML4:9bit][PDPT:9bit][PD:9bit][PT:9bit][Offset:12bit]
      4KB ページ × 4レベル = 256TB の仮想空間

    ■ TLB (Translation Lookaside Buffer)
      仮想→物理アドレス変換のキャッシュ。ミスすると page walk (4回メモリアクセス)。
      TLB shootdown: 他コアの TLB を無効化する IPI (高コスト)。

    ■ ページ置換アルゴリズム
      - LRU: 最も長く使われてないページを追い出す (実装コスト高)
      - Clock (Second Chance): 参照ビットで近似LRU
      - 2Q: Active/Inactive リストで「一度だけ」のページを早く追い出す

    ■ Copy-on-Write (CoW)
      fork() 時にページをコピーせず、書き込み時に初めてコピー。
    """
    print("=== 仮想メモリ シミュレーション ===\n")

    # --- 4レベルページテーブル ---
    class PageTableEntry:
        def __init__(self):
            self.present: bool = False
            self.frame: int = 0
            self.dirty: bool = False
            self.accessed: bool = False
            self.writable: bool = True
            self.user: bool = True
            self.cow: bool = False  # Copy-on-Write フラグ
            self.next_level: Optional[Dict[int, 'PageTableEntry']] = None

    class MultiLevelPageTable:
        """x86-64 スタイルの4レベルページテーブル"""
        LEVELS = 4
        INDEX_BITS = 9  # 各レベル 9bit (512エントリ)
        OFFSET_BITS = 12  # 4KB ページ

        def __init__(self):
            self.root: Dict[int, PageTableEntry] = {}
            self.next_frame = 1
            self.page_faults = 0
            self.walks = 0

        def _extract_indices(self, virtual_addr: int) -> List[int]:
            """仮想アドレスを4レベルのインデックスに分解"""
            indices = []
            addr = virtual_addr >> self.OFFSET_BITS
            for _ in range(self.LEVELS):
                indices.append(addr & ((1 << self.INDEX_BITS) - 1))
                addr >>= self.INDEX_BITS
            return list(reversed(indices))

        def translate(self, virtual_addr: int) -> Tuple[int, bool]:
            """仮想→物理アドレス変換。ページフォルトなら割り当て。"""
            self.walks += 1
            indices = self._extract_indices(virtual_addr)
            offset = virtual_addr & ((1 << self.OFFSET_BITS) - 1)

            current_table = self.root
            for level in range(self.LEVELS):
                idx = indices[level]
                if idx not in current_table:
                    # ページフォルト → デマンドページング
                    self.page_faults += 1
                    entry = PageTableEntry()
                    if level < self.LEVELS - 1:
                        entry.next_level = {}
                        entry.present = True
                    else:
                        entry.present = True
                        entry.frame = self.next_frame
                        self.next_frame += 1
                    current_table[idx] = entry

                entry = current_table[idx]
                entry.accessed = True
                if level < self.LEVELS - 1:
                    if entry.next_level is None:
                        entry.next_level = {}
                    current_table = entry.next_level
                else:
                    physical = (entry.frame << self.OFFSET_BITS) | offset
                    return physical, True
            return 0, False  # 到達しない

    # --- TLB ---
    class TLB:
        def __init__(self, size: int = 64):
            self.size = size
            self.entries: OrderedDict[int, int] = OrderedDict()  # vpn → ppn
            self.hits = 0
            self.misses = 0

        def lookup(self, vpn: int) -> Optional[int]:
            if vpn in self.entries:
                self.hits += 1
                self.entries.move_to_end(vpn)
                return self.entries[vpn]
            self.misses += 1
            return None

        def insert(self, vpn: int, ppn: int):
            if vpn in self.entries:
                self.entries.move_to_end(vpn)
            else:
                if len(self.entries) >= self.size:
                    self.entries.popitem(last=False)
                self.entries[vpn] = ppn

        def invalidate(self, vpn: int):
            self.entries.pop(vpn, None)

        def flush(self):
            """TLB shootdown: 全エントリ無効化"""
            count = len(self.entries)
            self.entries.clear()
            return count

        def hit_rate(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total else 0.0

    # --- ページ置換アルゴリズム ---
    class PageReplacer:
        """LRU, Clock, 2Q の3つのページ置換を比較"""

        @staticmethod
        def lru_simulate(pages: List[int], num_frames: int) -> Dict:
            frames: OrderedDict[int, bool] = OrderedDict()
            faults = 0
            for page in pages:
                if page in frames:
                    frames.move_to_end(page)
                else:
                    faults += 1
                    if len(frames) >= num_frames:
                        frames.popitem(last=False)
                    frames[page] = True
            return {"algorithm": "LRU", "faults": faults,
                    "fault_rate": f"{faults/len(pages)*100:.1f}%"}

        @staticmethod
        def clock_simulate(pages: List[int], num_frames: int) -> Dict:
            frames: List[Optional[int]] = [None] * num_frames
            ref_bits: List[bool] = [False] * num_frames
            hand = 0
            faults = 0
            page_to_frame: Dict[int, int] = {}

            for page in pages:
                if page in page_to_frame:
                    ref_bits[page_to_frame[page]] = True
                else:
                    faults += 1
                    while ref_bits[hand]:
                        ref_bits[hand] = False
                        hand = (hand + 1) % num_frames
                    # 追い出し
                    old = frames[hand]
                    if old is not None:
                        del page_to_frame[old]
                    frames[hand] = page
                    ref_bits[hand] = True
                    page_to_frame[page] = hand
                    hand = (hand + 1) % num_frames
            return {"algorithm": "Clock", "faults": faults,
                    "fault_rate": f"{faults/len(pages)*100:.1f}%"}

        @staticmethod
        def two_q_simulate(pages: List[int], num_frames: int) -> Dict:
            """
            2Q: FIFO (A1in) と LRU (Am) の2つのキュー。
            初回アクセスは A1in に入り、再アクセスで Am に昇格。
            A1in は全体の 1/3、Am は 2/3。
            """
            a1_size = max(1, num_frames // 3)
            am_size = num_frames - a1_size
            a1in: deque = deque()  # FIFO
            am: OrderedDict = OrderedDict()  # LRU
            a1out: deque = deque()  # 最近 A1in から出たページを記憶
            a1out_max = a1_size * 2
            faults = 0
            in_cache: Set[int] = set()

            for page in pages:
                if page in in_cache:
                    # ヒット
                    if page in am:
                        am.move_to_end(page)
                    else:
                        # A1in にある → Am に昇格
                        a1_list = list(a1in)
                        if page in a1_list:
                            a1in.remove(page)
                            if len(am) >= am_size:
                                old, _ = am.popitem(last=False)
                                in_cache.discard(old)
                            am[page] = True
                else:
                    faults += 1
                    if page in list(a1out):
                        # A1out にある → Am に入れる (再アクセスされた重要ページ)
                        if len(am) >= am_size:
                            old, _ = am.popitem(last=False)
                            in_cache.discard(old)
                        am[page] = True
                    else:
                        # 完全に新規 → A1in へ
                        if len(a1in) >= a1_size:
                            old = a1in.popleft()
                            in_cache.discard(old)
                            a1out.append(old)
                            if len(a1out) > a1out_max:
                                a1out.popleft()
                        a1in.append(page)
                    in_cache.add(page)

            return {"algorithm": "2Q", "faults": faults,
                    "fault_rate": f"{faults/len(pages)*100:.1f}%"}

    # --- Copy-on-Write ---
    class CoWMemory:
        """Copy-on-Write fork のシミュレーション"""
        def __init__(self):
            self.pages: Dict[int, List[int]] = {}  # page_id → data
            self.ref_count: Dict[int, int] = defaultdict(int)
            self.copies_made = 0

        def allocate(self, page_id: int, data: List[int]):
            self.pages[page_id] = data
            self.ref_count[page_id] = 1

        def fork(self) -> 'CoWMemory':
            """子プロセスを作成 (ページは共有、書き込み時にコピー)"""
            child = CoWMemory()
            child.pages = self.pages  # 同じ辞書を共有
            child.ref_count = self.ref_count
            for pid in self.pages:
                self.ref_count[pid] += 1
            child.copies_made = 0
            return child

        def write(self, page_id: int, new_data: List[int]):
            if self.ref_count.get(page_id, 0) > 1:
                # CoW: コピーしてから書き込み
                self.pages = dict(self.pages)  # 辞書も分離
                self.pages[page_id] = list(new_data)
                self.ref_count[page_id] -= 1
                self.ref_count = dict(self.ref_count)
                self.copies_made += 1
            else:
                self.pages[page_id] = new_data

    # --- デモ実行 ---
    print("--- 4レベルページテーブル (x86-64) ---")
    pt = MultiLevelPageTable()
    tlb = TLB(size=64)

    test_addrs = [
        0x0000_0040_0000,  # .text
        0x0000_0040_1000,
        0x0000_0060_0000,  # .data
        0x7FFF_FFFF_E000,  # stack
        0x7FFF_FFFF_F000,
        0x0000_0040_0000,  # 再アクセス (TLB hit)
    ]

    for va in test_addrs:
        vpn = va >> 12
        ppn = tlb.lookup(vpn)
        if ppn is not None:
            print(f"  VA {va:#018x} → TLB HIT → PA {(ppn << 12) | (va & 0xFFF):#018x}")
        else:
            pa, ok = pt.translate(va)
            ppn = pa >> 12
            tlb.insert(vpn, ppn)
            print(f"  VA {va:#018x} → TLB MISS → page walk → PA {pa:#018x}")

    print(f"\n  TLB ヒット率: {tlb.hit_rate()*100:.1f}%")
    print(f"  ページフォルト: {pt.page_faults}")
    print(f"  ページウォーク: {pt.walks}")

    # TLB shootdown デモ
    flushed = tlb.flush()
    print(f"\n  TLB Shootdown: {flushed} エントリ無効化")
    print("  → コンテキストスイッチ/mmap変更時に発生。IPIで全コアに通知。")

    # ページ置換比較
    print("\n--- ページ置換アルゴリズム比較 ---")
    random.seed(42)
    # ワークロード: 局所性あり + たまにスキャン
    page_refs = []
    for _ in range(500):
        page_refs.append(random.choice(range(10)))     # ホットセット
    for i in range(50):
        page_refs.append(i + 100)                       # シーケンシャルスキャン
    for _ in range(500):
        page_refs.append(random.choice(range(10)))     # ホットセットに戻る
    num_frames = 8

    for result in [
        PageReplacer.lru_simulate(page_refs, num_frames),
        PageReplacer.clock_simulate(page_refs, num_frames),
        PageReplacer.two_q_simulate(page_refs, num_frames),
    ]:
        print(f"  {result['algorithm']}: "
              f"faults={result['faults']}, rate={result['fault_rate']}")

    print("  → 2Q はシーケンシャルスキャンに強い (スキャン耐性)")

    # Copy-on-Write デモ
    print("\n--- Copy-on-Write fork ---")
    parent = CoWMemory()
    for i in range(5):
        parent.allocate(i, [i * 10, i * 10 + 1])
    print(f"  Parent: 5ページ割り当て済み")

    child = parent.fork()
    print(f"  fork() → 子プロセス作成 (0ページコピー、参照カウント+1)")

    child.write(2, [99, 100])
    print(f"  子がページ2に書き込み → CoWコピー発生: {child.copies_made}回")
    child.write(3, [77, 78])
    print(f"  子がページ3に書き込み → CoWコピー累計: {child.copies_made}回")
    print("  → fork+exec パターンでは大部分のページは exec でまるごと置換されるため CoW は非常に効率的")


# ============================================================================
# 4. プロセス & スケジューリング (CFS, Work-Stealing)
# ============================================================================

def section_process_scheduling():
    """
    ■ プロセス状態遷移
      New → Ready → Running → (Blocked) → Ready → ... → Terminated
      - Running → Blocked: I/O待ち, mutex待ち
      - Running → Ready: タイムスライス切れ (preemption)
      - Blocked → Ready: I/O完了割り込み

    ■ CFS (Completely Fair Scheduler) - Linux
      - 各タスクの vruntime (仮想実行時間) を追跡
      - vruntime が最小のタスクを次に実行
      - 優先度 (nice) で vruntime の進む速度を変える
      - Red-Black Tree で O(log N) の最小値取得

    ■ Work-Stealing
      - 各ワーカーが自分のキュー (deque) を持つ
      - 自分のキューが空 → 他のワーカーからタスクを steal
      - Golang goroutine, Java ForkJoinPool で使用
    """
    print("=== プロセス & スケジューリング ===\n")

    # --- プロセス状態マシン ---
    class ProcessState(Enum):
        NEW = auto()
        READY = auto()
        RUNNING = auto()
        BLOCKED = auto()
        TERMINATED = auto()

    @dataclass
    class Process:
        pid: int
        name: str
        state: ProcessState = ProcessState.NEW
        priority: int = 0      # nice値 (-20〜19)
        vruntime: float = 0.0  # CFS用
        burst_remaining: int = 0
        total_wait: int = 0
        total_run: int = 0

        def __lt__(self, other):
            return self.vruntime < other.vruntime

    class ProcessStateMachine:
        """プロセス状態遷移のデモ"""
        VALID_TRANSITIONS = {
            ProcessState.NEW: [ProcessState.READY],
            ProcessState.READY: [ProcessState.RUNNING],
            ProcessState.RUNNING: [ProcessState.READY, ProcessState.BLOCKED,
                                   ProcessState.TERMINATED],
            ProcessState.BLOCKED: [ProcessState.READY],
            ProcessState.TERMINATED: [],
        }

        @staticmethod
        def transition(proc: Process, new_state: ProcessState) -> bool:
            if new_state in ProcessStateMachine.VALID_TRANSITIONS.get(
                    proc.state, []):
                old = proc.state
                proc.state = new_state
                return True
            return False

    # --- CFS スケジューラ ---
    class CFSScheduler:
        """
        Completely Fair Scheduler:
        vruntime = 実際の実行時間 × (weight_nice0 / weight_process)
        nice 0 の weight = 1024
        nice が1上がると weight が約 1.25 倍減少
        """
        WEIGHT_NICE0 = 1024
        NICE_TO_WEIGHT = {
            -20: 88761, -10: 9548, -5: 3121, 0: 1024,
            5: 335, 10: 110, 15: 36, 19: 15
        }

        def __init__(self, min_granularity: int = 1):
            self.run_queue: List[Process] = []  # min-heap by vruntime
            self.min_granularity = min_granularity
            self.clock = 0
            self.log: List[str] = []

        def add_process(self, proc: Process):
            proc.state = ProcessState.READY
            # 新プロセスは現在の最小 vruntime から開始
            if self.run_queue:
                proc.vruntime = self.run_queue[0].vruntime
            heapq.heappush(self.run_queue, proc)

        def _get_weight(self, nice: int) -> int:
            # 近い値に丸める
            closest = min(self.NICE_TO_WEIGHT.keys(), key=lambda k: abs(k - nice))
            return self.NICE_TO_WEIGHT[closest]

        def schedule_tick(self) -> Optional[Process]:
            if not self.run_queue:
                return None
            current = heapq.heappop(self.run_queue)
            current.state = ProcessState.RUNNING

            # 実行 (1 tick)
            weight = self._get_weight(current.priority)
            delta_vruntime = self.WEIGHT_NICE0 / weight
            current.vruntime += delta_vruntime
            current.burst_remaining -= 1
            current.total_run += 1
            self.clock += 1

            self.log.append(
                f"  tick={self.clock:3d}: {current.name:8s} "
                f"(nice={current.priority:+3d}, vruntime={current.vruntime:8.1f})")

            if current.burst_remaining <= 0:
                current.state = ProcessState.TERMINATED
            else:
                current.state = ProcessState.READY
                heapq.heappush(self.run_queue, current)
            return current

        def run_all(self) -> List[str]:
            while self.run_queue:
                self.schedule_tick()
            return self.log

    # --- Work-Stealing スケジューラ ---
    class WorkStealingScheduler:
        def __init__(self, num_workers: int = 4):
            self.num_workers = num_workers
            self.queues: List[deque] = [deque() for _ in range(num_workers)]
            self.completed: List[Tuple[int, str]] = []  # (worker_id, task)
            self.steals = 0

        def submit(self, task: str, worker_id: int = -1):
            if worker_id < 0:
                # ラウンドロビンで振り分け
                worker_id = hash(task) % self.num_workers
            self.queues[worker_id].append(task)

        def _steal_from(self, thief: int) -> Optional[str]:
            """他のワーカーのキューの末尾からスティール"""
            for victim in range(self.num_workers):
                if victim == thief:
                    continue
                if self.queues[victim]:
                    self.steals += 1
                    return self.queues[victim].pop()  # 末尾から取る
            return None

        def run_all(self) -> Dict:
            rounds = 0
            while any(self.queues[i] for i in range(self.num_workers)):
                rounds += 1
                for w in range(self.num_workers):
                    if self.queues[w]:
                        task = self.queues[w].popleft()
                        self.completed.append((w, task))
                    else:
                        stolen = self._steal_from(w)
                        if stolen:
                            self.completed.append((w, f"{stolen}(stolen)"))
            return {
                "total_tasks": len(self.completed),
                "steals": self.steals,
                "rounds": rounds,
                "per_worker": {w: sum(1 for wid, _ in self.completed if wid == w)
                               for w in range(self.num_workers)},
            }

    # --- デモ実行 ---
    print("--- プロセス状態遷移 ---")
    p = Process(1, "init")
    transitions = [
        (ProcessState.READY, "admit"),
        (ProcessState.RUNNING, "dispatch"),
        (ProcessState.BLOCKED, "I/O request"),
        (ProcessState.READY, "I/O complete"),
        (ProcessState.RUNNING, "dispatch"),
        (ProcessState.TERMINATED, "exit"),
    ]
    print(f"  {p.state.name}", end="")
    for new_state, reason in transitions:
        ok = ProcessStateMachine.transition(p, new_state)
        print(f" --[{reason}]--> {p.state.name}", end="")
    print()

    # CFS
    print("\n--- CFS スケジューラ ---")
    cfs = CFSScheduler()
    cfs.add_process(Process(1, "nginx", priority=0, burst_remaining=5))
    cfs.add_process(Process(2, "compile", priority=10, burst_remaining=8))
    cfs.add_process(Process(3, "realtime", priority=-10, burst_remaining=3))

    logs = cfs.run_all()
    print(f"  プロセス: nginx(nice=0), compile(nice=+10), realtime(nice=-10)")
    for line in logs[:10]:
        print(line)
    if len(logs) > 10:
        print(f"  ... (残り {len(logs)-10} tick)")
    print(f"\n  → nice が低い (優先度が高い) ほど vruntime がゆっくり進む")
    print(f"    → より多くの CPU 時間を得る")

    # Work-Stealing
    print("\n--- Work-Stealing スケジューラ ---")
    ws = WorkStealingScheduler(num_workers=4)
    # 偏った負荷
    for i in range(10):
        ws.submit(f"task_{i}", worker_id=0)  # Worker0 に集中
    for i in range(2):
        ws.submit(f"task_{10+i}", worker_id=1)
    # Worker2, Worker3 は空 → steal する

    result = ws.run_all()
    print(f"  タスク総数: {result['total_tasks']}")
    print(f"  スティール回数: {result['steals']}")
    print(f"  ワーカー別処理数: {result['per_worker']}")
    print(f"""
■ IPC (Inter-Process Communication) 比較:
  パイプ:         最も単純。親子プロセス間。一方向。
  名前付きパイプ: 無関係なプロセス間でも使える。
  共有メモリ:     最速。同期が必要 (semaphore/mutex)。
  メッセージキュー: 構造化メッセージ。カーネルがバッファ管理。
  ソケット:       ネットワーク越しも可。最も汎用的。
  シグナル:       非同期通知。データ量は最小 (シグナル番号のみ)。

  スループット: 共有メモリ >> パイプ > ソケット > メッセージキュー
  レイテンシ:   共有メモリ < パイプ < ソケット < メッセージキュー
""")


# ============================================================================
# 5. I/O モデル (Reactor, Proactor, select/poll/epoll)
# ============================================================================

def section_io_models():
    """
    ■ 5つの I/O モデル (Stevens)
      1. Blocking I/O:      read() でブロック。最も単純。
      2. Non-blocking I/O:  EAGAIN で即座に返る。ポーリングが必要。
      3. I/O Multiplexing:  select/poll/epoll で複数FDを監視。
      4. Signal-driven I/O: SIGIO で通知。
      5. Async I/O (AIO):   カーネルが完了まで処理。io_uring。

    ■ Reactor パターン (Node.js, Redis, Nginx)
      - 単一スレッドのイベントループ
      - I/O multiplexing でイベント待ち → コールバック実行
      - CPU-bound タスクはブロックするので注意

    ■ Proactor パターン (Windows IOCP, io_uring)
      - OS がI/O完了まで処理 → 完了通知だけ受け取る
      - Reactor との違い: 「準備完了」vs「完了」通知

    ■ select vs poll vs epoll:
      select: FD上限1024, 毎回全FDをカーネルにコピー, O(N)
      poll:   FD上限なし, 毎回全FDをカーネルにコピー, O(N)
      epoll:  FD上限なし, カーネルが状態管理, O(1) per event
    """
    print("=== I/O モデル & Reactor パターン ===\n")

    # --- I/O モデル比較シミュレーション ---
    class IOModelSimulator:
        """5つの I/O モデルの動作を擬似的にシミュレーション"""

        @staticmethod
        def blocking_io(tasks: List[Tuple[str, int]]) -> Dict:
            """Blocking I/O: 1タスクずつ順番に処理"""
            total_time = 0
            results = []
            for name, io_time in tasks:
                total_time += io_time
                results.append((name, total_time))
            return {"model": "Blocking I/O", "total_time": total_time,
                    "completed": results}

        @staticmethod
        def nonblocking_poll(tasks: List[Tuple[str, int]]) -> Dict:
            """Non-blocking I/O: ポーリング (CPU時間を浪費)"""
            remaining = {name: io_time for name, io_time in tasks}
            total_time = 0
            poll_count = 0
            completed = []
            while remaining:
                total_time += 1
                done = []
                for name in remaining:
                    remaining[name] -= 1
                    poll_count += 1
                    if remaining[name] <= 0:
                        done.append(name)
                        completed.append((name, total_time))
                for d in done:
                    del remaining[d]
            return {"model": "Non-blocking Poll", "total_time": total_time,
                    "poll_count": poll_count, "completed": completed}

        @staticmethod
        def io_multiplexing(tasks: List[Tuple[str, int]]) -> Dict:
            """I/O Multiplexing: epoll風 (全FDを一括監視)"""
            remaining = {name: io_time for name, io_time in tasks}
            total_time = 0
            events = 0
            completed = []
            while remaining:
                # 最も早く完了するものを見つける
                min_time = min(remaining.values())
                total_time += min_time
                events += 1  # epoll_wait 1回
                done = []
                for name in remaining:
                    remaining[name] -= min_time
                    if remaining[name] <= 0:
                        done.append(name)
                        completed.append((name, total_time))
                for d in done:
                    del remaining[d]
            return {"model": "I/O Multiplexing", "total_time": total_time,
                    "epoll_events": events, "completed": completed}

        @staticmethod
        def async_io(tasks: List[Tuple[str, int]]) -> Dict:
            """Async I/O: カーネルが全部やって完了通知"""
            max_time = max(io_time for _, io_time in tasks)
            completed = [(name, io_time) for name, io_time in tasks]
            return {"model": "Async I/O", "total_time": max_time,
                    "completions": len(tasks), "completed": completed}

    # --- Reactor パターン (シングルスレッド イベントループ) ---
    class ReactorEventLoop:
        """
        Redis/Node.js 風の Reactor パターン:
        1. epoll_wait でイベント待ち
        2. イベント発生 → 登録済みハンドラを実行
        3. 1に戻る

        重要: ハンドラ内で長時間ブロックすると全体が止まる
        """
        def __init__(self):
            self.handlers: Dict[str, callable] = {}
            self.timers: List[Tuple[float, str, callable]] = []  # (deadline, name, cb)
            self.pending_io: List[Tuple[str, int, callable]] = []
            self.event_log: List[str] = []
            self.current_time = 0.0

        def register_handler(self, event_type: str, handler: callable):
            self.handlers[event_type] = handler

        def add_timer(self, delay: float, name: str, callback: callable):
            heapq.heappush(self.timers, (self.current_time + delay, name, callback))

        def submit_io(self, name: str, duration: int, callback: callable):
            self.pending_io.append((name, self.current_time + duration, callback))

        def run(self, max_ticks: int = 50) -> List[str]:
            for tick in range(max_ticks):
                self.current_time = tick
                events_this_tick = []

                # タイマー処理
                while self.timers and self.timers[0][0] <= self.current_time:
                    _, name, cb = heapq.heappop(self.timers)
                    result = cb()
                    events_this_tick.append(f"timer:{name}={result}")

                # I/O 完了処理
                completed_io = []
                remaining_io = []
                for name, deadline, cb in self.pending_io:
                    if deadline <= self.current_time:
                        result = cb()
                        events_this_tick.append(f"io:{name}={result}")
                        completed_io.append(name)
                    else:
                        remaining_io.append((name, deadline, cb))
                self.pending_io = remaining_io

                if events_this_tick:
                    self.event_log.append(
                        f"  tick={tick:3d}: {', '.join(events_this_tick)}")

                if not self.timers and not self.pending_io:
                    break

            return self.event_log

    # --- select/poll/epoll 比較 ---
    class MultiplexerBenchmark:
        """select, poll, epoll の性能特性をシミュレーション"""

        @staticmethod
        def simulate(num_fds: int, active_ratio: float = 0.01) -> Dict:
            active_fds = max(1, int(num_fds * active_ratio))

            # select: 全FDをビットマップでコピー + スキャン
            select_copy_cost = num_fds  # FD_SET コピー
            select_scan_cost = num_fds  # 全FDスキャン
            select_total = select_copy_cost + select_scan_cost
            select_limited = min(num_fds, 1024)  # FD_SETSIZE 制限

            # poll: 全FDを pollfd 配列でコピー + スキャン
            poll_copy_cost = num_fds * 8  # struct pollfd (8 bytes)
            poll_scan_cost = num_fds
            poll_total = poll_copy_cost + poll_scan_cost

            # epoll: 登録済みFDのイベントのみ返す
            epoll_wait_cost = 1           # O(1) wait
            epoll_event_cost = active_fds  # アクティブFDだけ処理
            epoll_total = epoll_wait_cost + epoll_event_cost

            return {
                "num_fds": num_fds,
                "active_fds": active_fds,
                "select": {"cost": select_total, "max_fd": select_limited,
                           "complexity": "O(N)"},
                "poll": {"cost": poll_total, "max_fd": "unlimited",
                         "complexity": "O(N)"},
                "epoll": {"cost": epoll_total, "max_fd": "unlimited",
                          "complexity": "O(active)"},
            }

    # --- デモ実行 ---
    print("--- 5つの I/O モデル比較 ---")
    tasks = [("DB_query", 5), ("API_call", 8), ("File_read", 3), ("DNS", 2)]
    print(f"  タスク: {tasks}\n")

    sim = IOModelSimulator()
    for result in [
        sim.blocking_io(tasks),
        sim.nonblocking_poll(tasks),
        sim.io_multiplexing(tasks),
        sim.async_io(tasks),
    ]:
        extras = ""
        if "poll_count" in result:
            extras = f", polls={result['poll_count']}"
        if "epoll_events" in result:
            extras = f", epoll_waits={result['epoll_events']}"
        print(f"  {result['model']:25s}: total_time={result['total_time']}{extras}")

    # Reactor パターン
    print("\n--- Reactor パターン (イベントループ) ---")
    reactor = ReactorEventLoop()
    request_count = [0]

    def handle_request():
        request_count[0] += 1
        return f"req#{request_count[0]}"

    def handle_timeout():
        return "cleanup"

    # リクエストを登録
    reactor.submit_io("client_A", 3, handle_request)
    reactor.submit_io("client_B", 5, handle_request)
    reactor.submit_io("client_C", 3, handle_request)
    reactor.add_timer(7.0, "cleanup", handle_timeout)
    reactor.add_timer(2.0, "heartbeat", lambda: "ping")

    logs = reactor.run()
    for line in logs:
        print(line)

    print(f"""
  Reactor の特徴:
    ✓ シングルスレッドで数万接続を処理 (C10K problem 解決)
    ✓ コンテキストスイッチなし
    ✗ CPU-bound 処理が入ると全体がブロック
    → Node.js: Worker Thread で対処
    → Redis: 基本的にCPU-boundにならない設計
""")

    # select/poll/epoll 比較
    print("--- select / poll / epoll 比較 ---")
    for num_fds in [100, 1000, 10000, 100000]:
        result = MultiplexerBenchmark.simulate(num_fds)
        print(f"  FD数={num_fds:>6d}: "
              f"select={result['select']['cost']:>8d}, "
              f"poll={result['poll']['cost']:>8d}, "
              f"epoll={result['epoll']['cost']:>5d}")

    print(f"""
  → FD数が増えるほど epoll の O(active) が圧倒的に有利
  → 10万接続で1%アクティブ: epoll は select の 200倍効率的

■ Proactor パターン (Windows IOCP / Linux io_uring):
  Reactor: 「準備完了」通知 → アプリが read() → 処理
  Proactor: カーネルが read() 完了 → 「完了」通知 → 処理

  io_uring (Linux 5.1+):
    - Submission Queue (SQ) と Completion Queue (CQ) をリング構造で共有
    - システムコールなしで I/O リクエストを投入可能
    - カーネルとユーザー空間のメモリコピーゼロ
""")


# ============================================================================
# 6. 割り込み & NUMA (Top-half/Bottom-half, DMA)
# ============================================================================

def section_interrupts_numa():
    """
    ■ 割り込み処理
      Top-half (Hard IRQ): 最小限の処理。割り込み無効化中。
      Bottom-half (Soft IRQ / Tasklet / Workqueue): 遅延実行。

    ■ DMA (Direct Memory Access)
      CPU を介さずデバイスがメモリに直接アクセス。
      CPU は DMA コントローラにアドレスとサイズを指示するだけ。

    ■ NUMA (Non-Uniform Memory Access)
      各 CPU ソケットにローカルメモリ。
      リモートメモリアクセスはローカルの 1.5-3倍 遅い。
    """
    print("=== 割り込み & NUMA ===\n")

    # --- 割り込みハンドリング ---
    class InterruptController:
        """割り込み処理のシミュレーション (Top-half / Bottom-half)"""

        def __init__(self):
            self.irq_handlers: Dict[int, callable] = {}
            self.bottom_half_queue: deque = deque()
            self.log: List[str] = []
            self.irq_count = 0
            self.softirq_count = 0

        def register_irq(self, irq_num: int, handler: callable):
            self.irq_handlers[irq_num] = handler

        def raise_irq(self, irq_num: int, data: str = ""):
            """Top-half: 割り込み発生 → 最小限の処理"""
            self.irq_count += 1
            self.log.append(
                f"  [IRQ] #{irq_num} Top-half: ack + save '{data}'")
            # Bottom-half をスケジュール
            handler = self.irq_handlers.get(irq_num)
            if handler:
                self.bottom_half_queue.append((irq_num, handler, data))

        def process_bottom_half(self):
            """Bottom-half: 遅延処理 (割り込み有効状態で実行)"""
            while self.bottom_half_queue:
                irq_num, handler, data = self.bottom_half_queue.popleft()
                self.softirq_count += 1
                result = handler(data)
                self.log.append(
                    f"  [SoftIRQ] #{irq_num} Bottom-half: {result}")

    # --- DMA ---
    class DMAController:
        """DMA 転送のシミュレーション"""
        def __init__(self):
            self.transfers: List[Dict] = []

        def initiate_transfer(self, device: str, src_addr: int,
                              dst_addr: int, size: int) -> Dict:
            # CPU は設定するだけ (数サイクル)
            cpu_cycles = 5
            # DMA が転送 (CPU は他の仕事ができる)
            dma_cycles = size // 8  # 8 bytes/cycle
            transfer = {
                "device": device,
                "src": f"{src_addr:#010x}",
                "dst": f"{dst_addr:#010x}",
                "size": f"{size} bytes",
                "cpu_cost": f"{cpu_cycles} cycles (setup only)",
                "dma_cost": f"{dma_cycles} cycles (CPU free)",
                "without_dma": f"{size} cycles (CPU busy)",
            }
            self.transfers.append(transfer)
            return transfer

    # --- NUMA トポロジ ---
    class NUMATopology:
        """NUMA ノード間のメモリアクセスコストをシミュレーション"""

        def __init__(self, num_nodes: int = 4):
            self.num_nodes = num_nodes
            # ノード間の相対コスト (1.0 = ローカル)
            self.cost_matrix: List[List[float]] = []
            for i in range(num_nodes):
                row = []
                for j in range(num_nodes):
                    if i == j:
                        row.append(1.0)
                    elif abs(i - j) == 1:
                        row.append(1.7)   # 隣接ノード
                    else:
                        row.append(2.5)   # 遠いノード
                self.cost_matrix.append(row)

            # 各ノードのメモリ (page_id → data)
            self.node_memory: List[Dict[int, str]] = [
                {} for _ in range(num_nodes)
            ]

        def access_memory(self, cpu_node: int, page_id: int) -> Tuple[float, str]:
            """メモリアクセス: ローカル or リモート"""
            for node_id, mem in enumerate(self.node_memory):
                if page_id in mem:
                    cost = self.cost_matrix[cpu_node][node_id]
                    locality = "LOCAL" if cpu_node == node_id else f"REMOTE(node{node_id})"
                    return cost, locality
            return 0, "PAGE_FAULT"

        def allocate(self, node_id: int, page_id: int, data: str):
            self.node_memory[node_id][page_id] = data

        def print_topology(self):
            print("  NUMA 距離行列 (相対コスト):")
            header = "       " + "  ".join(f"Node{j}" for j in range(self.num_nodes))
            print(f"  {header}")
            for i in range(self.num_nodes):
                row = f"  Node{i}  " + "   ".join(
                    f"{self.cost_matrix[i][j]:.1f}" for j in range(self.num_nodes))
                print(row)

    # --- デモ実行 ---
    print("--- 割り込み処理 (Top-half / Bottom-half) ---")
    ic = InterruptController()
    ic.register_irq(1, lambda data: f"NIC: process packet '{data}'")
    ic.register_irq(14, lambda data: f"Disk: complete I/O '{data}'")
    ic.register_irq(0, lambda data: f"Timer: tick '{data}'")

    # 割り込み発生
    ic.raise_irq(1, "TCP SYN from 10.0.0.1")
    ic.raise_irq(14, "read sector 42")
    ic.raise_irq(0, "100ms")
    ic.raise_irq(1, "TCP ACK from 10.0.0.1")

    print("  -- Top-half (即時) --")
    for line in ic.log:
        print(line)
    ic.log.clear()

    print("\n  -- Bottom-half (遅延処理) --")
    ic.process_bottom_half()
    for line in ic.log:
        print(line)
    print(f"\n  IRQ: {ic.irq_count}, SoftIRQ: {ic.softirq_count}")

    # DMA
    print("\n--- DMA (Direct Memory Access) ---")
    dma = DMAController()
    t = dma.initiate_transfer("NVMe SSD", 0xFE00_0000, 0x0010_0000, 4096)
    print(f"  デバイス: {t['device']}")
    print(f"  転送: {t['src']} → {t['dst']} ({t['size']})")
    print(f"  CPU コスト: {t['cpu_cost']}")
    print(f"  DMA コスト: {t['dma_cost']}")
    print(f"  DMA なし:   {t['without_dma']}")
    print("  → CPU は DMA 中に他の仕事ができる (効率 100倍以上)")

    # NUMA
    print("\n--- NUMA トポロジ ---")
    numa = NUMATopology(num_nodes=4)
    numa.print_topology()

    # メモリ割り当て & アクセス
    numa.allocate(0, 100, "data_A")
    numa.allocate(2, 200, "data_B")

    print("\n  メモリアクセスパターン:")
    test_accesses = [
        (0, 100, "CPU0 → page100"),
        (0, 200, "CPU0 → page200"),
        (2, 200, "CPU2 → page200"),
        (3, 100, "CPU3 → page100"),
    ]
    for cpu, page, desc in test_accesses:
        cost, locality = numa.access_memory(cpu, page)
        print(f"  {desc}: cost={cost:.1f}x ({locality})")

    print(f"""
■ NUMA 最適化の原則:
  1. メモリはそれを使うCPUのローカルノードに割り当てる
  2. numactl --membind / --cpunodebind でプロセスを固定
  3. Linux: /proc/sys/vm/zone_reclaim_mode で回収ポリシー制御
  4. 大規模DB (PostgreSQL/MySQL): NUMA-aware な設定が性能に直結

■ 割り込みの種類:
  ハードウェア割り込み: NIC, ディスク, タイマー, キーボード
  ソフトウェア割り込み: システムコール (int 0x80 / syscall)
  例外: ページフォルト, ゼロ除算, 一般保護違反 (GPF)
  NMI: Non-Maskable Interrupt (ハードウェア故障, ウォッチドッグ)
""")


# ============================================================================
# 7. 優先度マップ (Tier 1-4)
# ============================================================================

def section_priority_map():
    print("=== OS & ハードウェア 優先度マップ ===\n")
    tiers = {
        "Tier 1 (最優先 - 全エンジニア必須)": [
            "プロセスvsスレッド, コンテキストスイッチの仕組み",
            "仮想メモリ, ページフォルト, malloc の裏側",
            "ファイルディスクリプタ, I/O多重化 (epoll)",
            "キャッシュ階層 (L1/L2/L3) と局所性の原則",
        ],
        "Tier 2 (重要 - バックエンド/インフラ)": [
            "CPU パイプライン, 分岐予測, IPC",
            "スケジューラ (CFS), nice, cgroup",
            "MESI プロトコル, キャッシュコヒーレンシ",
            "Reactor パターン, select/poll/epoll の違い",
            "DMA, 割り込みの Top-half/Bottom-half",
        ],
        "Tier 3 (差別化 - SRE/パフォーマンス)": [
            "NUMA トポロジとメモリ配置最適化",
            "ページ置換 (LRU/Clock/2Q)",
            "TLB shootdown, Huge Pages",
            "io_uring, Proactor パターン",
            "False Sharing 検出と回避",
        ],
        "Tier 4 (専門 - カーネル/組込み)": [
            "ページテーブルの多段構造の実装詳細",
            "Work-Stealing スケジューラの実装",
            "割り込みコントローラ (APIC) の詳細",
            "CPU マイクロアーキテクチャ (OoO実行, ROB)",
        ],
    }
    for tier, items in tiers.items():
        print(f"  {tier}:")
        for item in items:
            print(f"    - {item}")
        print()


# ============================================================================
# メイン
# ============================================================================

def main():
    print("=" * 72)
    print(" OS & ハードウェア ディープガイド")
    print(" CSAPP/OSTEP レベル: CPU パイプラインから NUMA まで")
    print("=" * 72)
    print()

    section_cpu_pipeline()
    print("\n" + "=" * 72 + "\n")

    section_cache_simulator()
    print("\n" + "=" * 72 + "\n")

    section_virtual_memory()
    print("\n" + "=" * 72 + "\n")

    section_process_scheduling()
    print("\n" + "=" * 72 + "\n")

    section_io_models()
    print("\n" + "=" * 72 + "\n")

    section_interrupts_numa()
    print("\n" + "=" * 72 + "\n")

    section_priority_map()

    print("=" * 72)
    print(" 完了: 全セクション実行済み")
    print("=" * 72)


if __name__ == "__main__":
    main()
