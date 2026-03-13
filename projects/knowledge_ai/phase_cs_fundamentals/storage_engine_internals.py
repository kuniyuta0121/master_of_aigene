#!/usr/bin/env python3
"""
Storage Engine Internals — From Physics to Data Structures
==========================================================

Textbook-level coverage based on:
  - "Database Internals" by Alex Petrov
  - "Operating Systems: Three Easy Pieces" (OSTEP)
  - PostgreSQL, RocksDB, ext4, ZFS source-level concepts

Target audience: Python-experienced data scientist → senior/staff engineer

Run: python storage_engine_internals.py
"""

from __future__ import annotations
import math
import random
import struct
import hashlib
import time
import bisect
from typing import (
    Any, Dict, List, Optional, Tuple, Set, Iterator, Callable
)
from collections import OrderedDict, defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod

# ============================================================================
# SECTION 1: STORAGE MEDIA PHYSICS  (~200 lines)
# ============================================================================
#
#  ┌──────────────────────────────────────────────────────────┐
#  │  Storage Hierarchy (latency, not to scale)               │
#  │                                                          │
#  │  CPU Registers  ─  < 1 ns                                │
#  │  L1 Cache       ─  ~1 ns                                 │
#  │  L2 Cache       ─  ~4 ns                                 │
#  │  L3 Cache       ─  ~10 ns                                │
#  │  DRAM           ─  ~100 ns                               │
#  │  Optane (PMEM)  ─  ~300 ns                               │
#  │  NVMe SSD       ─  ~10-20 μs                             │
#  │  SATA SSD       ─  ~50-100 μs                            │
#  │  HDD            ─  ~5-10 ms                              │
#  │  Network (DC)   ─  ~0.5 ms                               │
#  └──────────────────────────────────────────────────────────┘


@dataclass
class HDDSpec:
    """Hard Disk Drive physical parameters."""
    rpm: int = 7200                # rotations per minute
    sectors_per_track: int = 500
    bytes_per_sector: int = 512
    tracks: int = 50000           # total tracks (cylinders)
    avg_seek_ms: float = 8.0      # average seek time in ms
    track_to_track_ms: float = 1.0

    @property
    def rotational_latency_ms(self) -> float:
        """Average rotational latency = half rotation time."""
        rotation_time_ms = 60_000.0 / self.rpm
        return rotation_time_ms / 2.0

    @property
    def transfer_rate_mb_s(self) -> float:
        """Sustained sequential transfer rate."""
        bytes_per_rotation = self.sectors_per_track * self.bytes_per_sector
        rotations_per_sec = self.rpm / 60.0
        return (bytes_per_rotation * rotations_per_sec) / (1024 * 1024)


class HDDSimulator:
    """
    Simulates HDD I/O with realistic latency model.

    Total I/O time = Seek Time + Rotational Latency + Transfer Time

    For random reads:
      - Seek: arm moves across platters (~4-10ms average)
      - Rotation: wait for sector to rotate under head (~4.17ms @ 7200 RPM)
      - Transfer: read the data off the platter

    For sequential reads, seek ≈ 0 and rotational latency ≈ 0.
    """

    def __init__(self, spec: HDDSpec = HDDSpec()):
        self.spec = spec
        self.current_track = 0

    def seek_time_ms(self, from_track: int, to_track: int) -> float:
        distance = abs(to_track - from_track)
        if distance == 0:
            return 0.0
        if distance == 1:
            return self.spec.track_to_track_ms
        # Seek time ≈ a + b * sqrt(distance)  (common model)
        a = self.spec.track_to_track_ms
        b = (self.spec.avg_seek_ms - a) / math.sqrt(self.spec.tracks / 3)
        return a + b * math.sqrt(distance)

    def read_latency_ms(self, track: int, num_sectors: int = 1) -> float:
        seek = self.seek_time_ms(self.current_track, track)
        rotation = self.spec.rotational_latency_ms
        transfer_time = (num_sectors * self.spec.bytes_per_sector /
                         (self.spec.transfer_rate_mb_s * 1024 * 1024)) * 1000
        self.current_track = track
        return seek + rotation + transfer_time

    def random_read_iops(self) -> float:
        avg_latency_ms = self.spec.avg_seek_ms + self.spec.rotational_latency_ms
        return 1000.0 / avg_latency_ms

    def sequential_throughput_mb_s(self) -> float:
        return self.spec.transfer_rate_mb_s


@dataclass
class NANDBlock:
    """
    NAND Flash Block — the unit of erasure.

    ┌────────────────────────────────────────┐
    │  NAND Block (e.g., 256 pages)          │
    │  ┌──────┐ ┌──────┐ ┌──────┐           │
    │  │Page 0│ │Page 1│ │Page 2│ ...        │
    │  │ 4 KB │ │ 4 KB │ │ 4 KB │           │
    │  └──────┘ └──────┘ └──────┘           │
    │                                        │
    │  States: FREE → VALID → INVALID        │
    │  Erase: entire block at once           │
    │  Write: page-at-a-time, sequentially   │
    └────────────────────────────────────────┘
    """
    block_id: int
    pages_per_block: int = 256
    page_size: int = 4096
    erase_count: int = 0
    max_erase_cycles: int = 3000  # TLC NAND typical
    page_states: List[str] = field(default_factory=list)  # FREE/VALID/INVALID

    def __post_init__(self):
        if not self.page_states:
            self.page_states = ["FREE"] * self.pages_per_block

    def erase(self):
        self.erase_count += 1
        self.page_states = ["FREE"] * self.pages_per_block

    def is_worn_out(self) -> bool:
        return self.erase_count >= self.max_erase_cycles


class FlashTranslationLayer:
    """
    FTL: Maps logical page addresses → physical (block, page) locations.

    Why FTL exists:
      1. NAND cannot overwrite — must erase entire block first
      2. Erase granularity (block) ≠ write granularity (page)
      3. Wear leveling — spread erases evenly across blocks

    ┌─────────────────┐       ┌─────────────────────┐
    │  Logical Page N  │──FTL──▶ Physical (Block, Page)│
    └─────────────────┘       └─────────────────────┘
    """

    def __init__(self, num_blocks: int = 64, pages_per_block: int = 256):
        self.pages_per_block = pages_per_block
        self.blocks = [NANDBlock(i, pages_per_block) for i in range(num_blocks)]
        # Logical → Physical mapping
        self.l2p: Dict[int, Tuple[int, int]] = {}  # logical → (block_id, page_offset)
        self.p2l: Dict[Tuple[int, int], int] = {}  # reverse mapping
        self.write_pointer_block = 0
        self.write_pointer_page = 0
        self.total_writes = 0
        self.total_physical_writes = 0

    def _advance_write_pointer(self):
        self.write_pointer_page += 1
        if self.write_pointer_page >= self.pages_per_block:
            self.write_pointer_page = 0
            self.write_pointer_block = (self.write_pointer_block + 1) % len(self.blocks)
            # Skip non-free blocks (simplified — real FTL is more complex)
            attempts = 0
            while (self.blocks[self.write_pointer_block]
                   .page_states[self.write_pointer_page] != "FREE"):
                self.write_pointer_block = ((self.write_pointer_block + 1)
                                            % len(self.blocks))
                attempts += 1
                if attempts >= len(self.blocks):
                    self._garbage_collect()
                    break

    def write(self, logical_page: int):
        """Write a logical page — invalidate old location, write to new."""
        self.total_writes += 1

        # Invalidate old mapping
        if logical_page in self.l2p:
            old_block, old_page = self.l2p[logical_page]
            self.blocks[old_block].page_states[old_page] = "INVALID"
            del self.p2l[(old_block, old_page)]

        # Find free page
        blk = self.blocks[self.write_pointer_block]
        if blk.page_states[self.write_pointer_page] != "FREE":
            self._garbage_collect()
            blk = self.blocks[self.write_pointer_block]

        # Write to physical location
        blk.page_states[self.write_pointer_page] = "VALID"
        self.l2p[logical_page] = (self.write_pointer_block, self.write_pointer_page)
        self.p2l[(self.write_pointer_block, self.write_pointer_page)] = logical_page
        self.total_physical_writes += 1
        self._advance_write_pointer()

    def read(self, logical_page: int) -> Optional[Tuple[int, int]]:
        return self.l2p.get(logical_page)

    def trim(self, logical_page: int):
        """TRIM: OS tells SSD that logical page is no longer needed."""
        if logical_page in self.l2p:
            block_id, page_off = self.l2p[logical_page]
            self.blocks[block_id].page_states[page_off] = "INVALID"
            del self.p2l[(block_id, page_off)]
            del self.l2p[logical_page]

    def _garbage_collect(self):
        """Pick block with most invalid pages, copy valid pages, erase."""
        # Greedy policy: pick block with most garbage
        best_block = max(
            range(len(self.blocks)),
            key=lambda i: self.blocks[i].page_states.count("INVALID")
        )
        blk = self.blocks[best_block]
        # Copy valid pages to write frontier
        for page_off in range(self.pages_per_block):
            if blk.page_states[page_off] == "VALID":
                logical = self.p2l.get((best_block, page_off))
                if logical is not None:
                    # Write valid page elsewhere (simplified)
                    self.total_physical_writes += 1
                    del self.p2l[(best_block, page_off)]
        blk.erase()
        self.write_pointer_block = best_block
        self.write_pointer_page = 0

    def write_amplification_factor(self) -> float:
        """WAF = Physical Writes / Logical Writes."""
        if self.total_writes == 0:
            return 0.0
        return self.total_physical_writes / self.total_writes

    def wear_report(self) -> Dict[str, Any]:
        erases = [b.erase_count for b in self.blocks]
        return {
            "min_erase": min(erases),
            "max_erase": max(erases),
            "avg_erase": sum(erases) / len(erases),
            "std_erase": (sum((e - sum(erases)/len(erases))**2
                              for e in erases) / len(erases)) ** 0.5,
            "worn_out_blocks": sum(1 for b in self.blocks if b.is_worn_out()),
            "waf": self.write_amplification_factor(),
        }


def storage_media_comparison():
    """Throughput & IOPS comparison across storage tiers."""
    media = {
        "HDD 7200RPM":  {"seq_read_mb": 150,  "seq_write_mb": 140,
                          "rand_read_iops": 100, "rand_write_iops": 100,
                          "latency_us": 8000},
        "SATA SSD":     {"seq_read_mb": 550,  "seq_write_mb": 520,
                          "rand_read_iops": 90_000, "rand_write_iops": 30_000,
                          "latency_us": 80},
        "NVMe SSD":     {"seq_read_mb": 3500, "seq_write_mb": 3000,
                          "rand_read_iops": 500_000, "rand_write_iops": 100_000,
                          "latency_us": 15},
        "Intel Optane":  {"seq_read_mb": 2500, "seq_write_mb": 2200,
                          "rand_read_iops": 550_000, "rand_write_iops": 500_000,
                          "latency_us": 7},
    }
    print("\n=== Storage Media Comparison ===")
    header = f"{'Media':<18} {'SeqR MB/s':>10} {'SeqW MB/s':>10} {'RandR IOPS':>12} {'RandW IOPS':>12} {'Latency':>10}"
    print(header)
    print("-" * len(header))
    for name, s in media.items():
        print(f"{name:<18} {s['seq_read_mb']:>10,} {s['seq_write_mb']:>10,} "
              f"{s['rand_read_iops']:>12,} {s['rand_write_iops']:>12,} "
              f"{s['latency_us']:>8,} μs")


# ============================================================================
# SECTION 2: FILE SYSTEM INTERNALS  (~350 lines)
# ============================================================================
#
#  ext4 Disk Layout (simplified):
#  ┌──────────┬───────────────────────────────────────────────┐
#  │Superblock│ Block Group 0  │ Block Group 1  │ ...         │
#  └──────────┴───────────────────────────────────────────────┘
#
#  Each Block Group:
#  ┌──────────┬────────────┬────────────┬────────┬───────────┐
#  │ GD Table │ Block Bmap │ Inode Bmap │ Inodes │ Data Blks │
#  └──────────┴────────────┴────────────┴────────┴───────────┘


@dataclass
class Inode:
    """
    Inode: metadata for a file (no filename — that's in the directory).

    Direct block pointers:     12 pointers → 12 × 4KB = 48 KB
    Single indirect:           1 pointer → 1024 ptrs → 4 MB
    Double indirect:           1 pointer → 1024 × 1024 → 4 GB
    Triple indirect:           1 pointer → 1024^3 → 4 TB

    ┌──────────────────────────┐
    │  Inode                   │
    │  mode, uid, size, times  │
    │  ┌──────────────────┐    │
    │  │ direct[0..11]    │────▶ data blocks
    │  │ single_indirect  │────▶ [ptr block] → data
    │  │ double_indirect  │────▶ [ptr] → [ptr] → data
    │  │ triple_indirect  │────▶ [ptr]→[ptr]→[ptr]→data
    │  └──────────────────┘    │
    └──────────────────────────┘
    """
    ino: int
    mode: str = "regular"  # regular, directory, symlink
    uid: int = 0
    size: int = 0
    created: float = 0.0
    modified: float = 0.0
    link_count: int = 1
    direct_blocks: List[int] = field(default_factory=lambda: [0]*12)
    single_indirect: int = 0
    double_indirect: int = 0
    triple_indirect: int = 0


BLOCK_SIZE = 4096
PTRS_PER_BLOCK = BLOCK_SIZE // 4  # 1024 pointers per indirect block


def inode_max_file_size() -> int:
    """Calculate max file size addressable by inode pointer structure."""
    direct = 12 * BLOCK_SIZE
    single = PTRS_PER_BLOCK * BLOCK_SIZE
    double = (PTRS_PER_BLOCK ** 2) * BLOCK_SIZE
    triple = (PTRS_PER_BLOCK ** 3) * BLOCK_SIZE
    return direct + single + double + triple


def resolve_block_index(block_index: int) -> str:
    """
    Given a logical block index within a file, determine which pointer
    level of the inode is used to reach it.
    """
    if block_index < 12:
        return f"direct[{block_index}]"
    block_index -= 12
    if block_index < PTRS_PER_BLOCK:
        return f"single_indirect → slot[{block_index}]"
    block_index -= PTRS_PER_BLOCK
    if block_index < PTRS_PER_BLOCK ** 2:
        lvl1 = block_index // PTRS_PER_BLOCK
        lvl2 = block_index % PTRS_PER_BLOCK
        return f"double_indirect → [{lvl1}] → [{lvl2}]"
    block_index -= PTRS_PER_BLOCK ** 2
    lvl1 = block_index // (PTRS_PER_BLOCK ** 2)
    rem = block_index % (PTRS_PER_BLOCK ** 2)
    lvl2 = rem // PTRS_PER_BLOCK
    lvl3 = rem % PTRS_PER_BLOCK
    return f"triple_indirect → [{lvl1}] → [{lvl2}] → [{lvl3}]"


@dataclass
class DirEntry:
    name: str
    inode_num: int


class Ext4Simulator:
    """
    Simplified ext4 file system simulator.

    Tracks: superblock, block bitmap, inode table, directory entries.
    Supports: create file, create directory, path resolution, allocate blocks.
    """

    def __init__(self, total_blocks: int = 4096, total_inodes: int = 512):
        self.total_blocks = total_blocks
        self.total_inodes = total_inodes
        self.block_bitmap = [False] * total_blocks  # True = allocated
        self.inode_bitmap = [False] * total_inodes
        self.inodes: Dict[int, Inode] = {}
        self.block_data: Dict[int, bytes] = {}
        self.directories: Dict[int, List[DirEntry]] = {}

        # Reserve blocks 0-9 for superblock, group descriptors, bitmaps
        for i in range(10):
            self.block_bitmap[i] = True

        # Create root directory (inode 2, as in ext4)
        self._alloc_inode(2, mode="directory")
        self.directories[2] = [
            DirEntry(".", 2),
            DirEntry("..", 2),
        ]

    def _alloc_inode(self, ino: int = -1, mode: str = "regular") -> Inode:
        if ino < 0:
            for i in range(len(self.inode_bitmap)):
                if not self.inode_bitmap[i]:
                    ino = i
                    break
            else:
                raise OSError("No free inodes")
        self.inode_bitmap[ino] = True
        inode = Inode(ino=ino, mode=mode, created=time.time(),
                      modified=time.time())
        self.inodes[ino] = inode
        return inode

    def _alloc_block(self) -> int:
        for i in range(len(self.block_bitmap)):
            if not self.block_bitmap[i]:
                self.block_bitmap[i] = True
                return i
        raise OSError("No free blocks")

    def resolve_path(self, path: str) -> Optional[int]:
        """
        Walk the inode tree to resolve a path → inode number.

        /home/user/file.txt
           ↓ lookup "home" in root dir → inode 5
           ↓ lookup "user" in inode 5's dir → inode 12
           ↓ lookup "file.txt" in inode 12's dir → inode 37
        """
        parts = [p for p in path.split("/") if p]
        current_ino = 2  # root
        for part in parts:
            if current_ino not in self.directories:
                return None
            found = False
            for entry in self.directories[current_ino]:
                if entry.name == part:
                    current_ino = entry.inode_num
                    found = True
                    break
            if not found:
                return None
        return current_ino

    def create_file(self, parent_ino: int, name: str, size: int = 0) -> Inode:
        inode = self._alloc_inode(mode="regular")
        inode.size = size
        # Allocate blocks for file data
        blocks_needed = math.ceil(size / BLOCK_SIZE) if size > 0 else 0
        for i in range(min(blocks_needed, 12)):
            blk = self._alloc_block()
            inode.direct_blocks[i] = blk
        if parent_ino in self.directories:
            self.directories[parent_ino].append(DirEntry(name, inode.ino))
        return inode

    def create_directory(self, parent_ino: int, name: str) -> Inode:
        inode = self._alloc_inode(mode="directory")
        self.directories[inode.ino] = [
            DirEntry(".", inode.ino),
            DirEntry("..", parent_ino),
        ]
        if parent_ino in self.directories:
            self.directories[parent_ino].append(DirEntry(name, inode.ino))
        return inode

    def stat(self, ino: int) -> Optional[Dict]:
        if ino not in self.inodes:
            return None
        nd = self.inodes[ino]
        used_blocks = sum(1 for b in nd.direct_blocks if b != 0)
        return {
            "ino": nd.ino, "mode": nd.mode, "size": nd.size,
            "blocks": used_blocks, "links": nd.link_count,
        }

    def free_space(self) -> Dict[str, int]:
        free_blocks = self.block_bitmap.count(False)
        free_inodes = self.inode_bitmap.count(False)
        return {
            "free_blocks": free_blocks,
            "free_bytes": free_blocks * BLOCK_SIZE,
            "free_inodes": free_inodes,
        }


class JournalMode(Enum):
    JOURNAL = auto()    # Both metadata + data journaled
    ORDERED = auto()    # Data written before metadata journal
    WRITEBACK = auto()  # No ordering guarantee


@dataclass
class JournalEntry:
    txn_id: int
    operation: str
    inode: int
    data_committed: bool = False
    metadata_committed: bool = False


class JournalingFS:
    """
    Journaling simulator showing crash recovery modes.

    Journal mode comparison:
    ┌───────────┬──────────────┬───────────────┬────────────┐
    │  Mode     │ Performance  │ Data Safety   │ Use Case   │
    ├───────────┼──────────────┼───────────────┼────────────┤
    │ journal   │ Slowest      │ Full          │ Critical   │
    │ ordered   │ Medium       │ Good (default)│ General    │
    │ writeback │ Fastest      │ Metadata only │ Speed      │
    └───────────┴──────────────┴───────────────┴────────────┘
    """

    def __init__(self, mode: JournalMode = JournalMode.ORDERED):
        self.mode = mode
        self.journal: List[JournalEntry] = []
        self.committed_data: Dict[int, bytes] = {}
        self.committed_metadata: Dict[int, dict] = {}
        self.txn_counter = 0

    def write_file(self, inode: int, data: bytes, metadata: dict) -> int:
        self.txn_counter += 1
        txn_id = self.txn_counter
        entry = JournalEntry(txn_id=txn_id, operation="write", inode=inode)

        if self.mode == JournalMode.JOURNAL:
            # Step 1: Write data + metadata to journal
            entry.data_committed = True
            entry.metadata_committed = True
            self.journal.append(entry)
            # Step 2: Write to actual location
            self.committed_data[inode] = data
            self.committed_metadata[inode] = metadata

        elif self.mode == JournalMode.ORDERED:
            # Step 1: Write DATA to final location first
            self.committed_data[inode] = data
            entry.data_committed = True
            # Step 2: Then write metadata to journal
            entry.metadata_committed = True
            self.journal.append(entry)
            self.committed_metadata[inode] = metadata

        elif self.mode == JournalMode.WRITEBACK:
            # Write metadata to journal (data order not guaranteed)
            entry.metadata_committed = True
            self.journal.append(entry)
            self.committed_metadata[inode] = metadata
            self.committed_data[inode] = data

        return txn_id

    def simulate_crash_recovery(self) -> List[str]:
        """Replay journal to recover consistent state."""
        actions = []
        for entry in self.journal:
            if entry.metadata_committed and not entry.data_committed:
                if self.mode == JournalMode.WRITEBACK:
                    actions.append(
                        f"TXN {entry.txn_id}: metadata OK but data may be "
                        f"stale (writeback mode risk)")
                else:
                    actions.append(
                        f"TXN {entry.txn_id}: redo metadata from journal")
            elif entry.metadata_committed and entry.data_committed:
                actions.append(
                    f"TXN {entry.txn_id}: fully committed, no action needed")
        return actions


class CopyOnWriteFS:
    """
    CoW filesystem concepts (ZFS / btrfs style).

    On write: allocate NEW block, write data there, update parent pointer.
    Old block remains untouched → instant snapshots.

    Before write:                After CoW write to Block B:
    ┌──────┐                    ┌──────┐
    │ Root │──▶ A               │Root' │──▶ A
    │      │──▶ B               │      │──▶ B' (new copy)
    │      │──▶ C               │      │──▶ C
    └──────┘                    └──────┘
                                Old Root still points to A, B, C → snapshot!
    """

    def __init__(self):
        self.block_store: Dict[int, bytes] = {}
        self.next_block_id = 0
        self.current_root: Dict[str, int] = {}  # filename → block_id
        self.snapshots: Dict[str, Dict[str, int]] = {}

    def _alloc_block(self, data: bytes) -> int:
        bid = self.next_block_id
        self.next_block_id += 1
        self.block_store[bid] = data
        return bid

    def write(self, filename: str, data: bytes):
        """CoW write: always allocate new block."""
        new_bid = self._alloc_block(data)
        self.current_root[filename] = new_bid

    def read(self, filename: str, snapshot: str = None) -> Optional[bytes]:
        root = self.snapshots.get(snapshot, self.current_root) if snapshot else self.current_root
        bid = root.get(filename)
        return self.block_store.get(bid) if bid is not None else None

    def create_snapshot(self, name: str):
        """Instant snapshot — just copy the root pointer dict."""
        self.snapshots[name] = dict(self.current_root)

    def list_snapshots(self) -> List[str]:
        return list(self.snapshots.keys())


class MerkleChecksumTree:
    """
    ZFS-style Merkle tree for data integrity.

    Each data block has a checksum stored in its PARENT pointer block.
    Corruption at any level is detectable.

    ┌──────────────────────────────────────────┐
    │             Uberblock (root hash)         │
    │                    │                      │
    │         ┌──────────┴──────────┐           │
    │     hash(L)              hash(R)          │
    │      │                     │              │
    │   ┌──┴──┐              ┌──┴──┐           │
    │  h(d0) h(d1)          h(d2) h(d3)        │
    │   │     │               │     │           │
    │  d0    d1              d2    d3           │
    └──────────────────────────────────────────┘
    """

    def __init__(self):
        self.data_blocks: List[bytes] = []
        self.tree: List[List[str]] = []

    def build(self, blocks: List[bytes]):
        self.data_blocks = blocks
        # Level 0: hash of each data block
        level = [hashlib.sha256(b).hexdigest()[:16] for b in blocks]
        self.tree = [level]
        # Build up
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i+1] if i+1 < len(level) else left
                combined = hashlib.sha256(
                    (left + right).encode()).hexdigest()[:16]
                next_level.append(combined)
            self.tree.append(next_level)
            level = next_level

    def root_hash(self) -> str:
        return self.tree[-1][0] if self.tree else ""

    def verify(self, block_index: int, data: bytes) -> bool:
        computed = hashlib.sha256(data).hexdigest()[:16]
        return computed == self.tree[0][block_index]


# ============================================================================
# SECTION 3: BUFFER POOL & PAGE CACHE  (~250 lines)
# ============================================================================
#
#  Buffer Pool Architecture (PostgreSQL-style):
#  ┌────────────────────────────────────────────────────────┐
#  │  Page Table (hash: page_id → frame_id)                 │
#  │                                                        │
#  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
#  │  │Frame 0 │ │Frame 1 │ │Frame 2 │ │Frame 3 │ ...      │
#  │  │pg=5    │ │pg=12   │ │pg=NULL │ │pg=3    │          │
#  │  │dirty=T │ │dirty=F │ │free    │ │dirty=F │          │
#  │  │pin=2   │ │pin=0   │ │pin=0   │ │pin=1   │          │
#  │  └────────┘ └────────┘ └────────┘ └────────┘          │
#  │                                                        │
#  │  Disk Manager: read_page(id) / write_page(id, data)   │
#  └────────────────────────────────────────────────────────┘


@dataclass
class BufferFrame:
    frame_id: int
    page_id: Optional[int] = None
    data: Optional[bytes] = None
    is_dirty: bool = False
    pin_count: int = 0
    ref_bit: bool = False    # for Clock-Sweep
    last_access: float = 0.0
    access_count: int = 0


class ReplacementPolicy(ABC):
    @abstractmethod
    def victim(self, frames: List[BufferFrame]) -> Optional[int]:
        """Return frame_id of victim to evict, or None."""

    @abstractmethod
    def access(self, frame: BufferFrame):
        """Record access to a frame."""


class LRUPolicy(ReplacementPolicy):
    """
    LRU: evict the Least Recently Used unpinned page.
    Simple but suffers from sequential flood problem.
    """
    def victim(self, frames: List[BufferFrame]) -> Optional[int]:
        unpinned = [f for f in frames if f.pin_count == 0 and f.page_id is not None]
        if not unpinned:
            return None
        return min(unpinned, key=lambda f: f.last_access).frame_id

    def access(self, frame: BufferFrame):
        frame.last_access = time.monotonic()


class ClockSweepPolicy(ReplacementPolicy):
    """
    Clock-Sweep (PostgreSQL's buffer replacement policy).

    A clock hand sweeps through frames:
      - If ref_bit=1: clear it, move on
      - If ref_bit=0 and unpinned: evict

    More efficient than LRU — O(1) amortized with no list maintenance.
    """

    def __init__(self):
        self.hand = 0

    def victim(self, frames: List[BufferFrame]) -> Optional[int]:
        n = len(frames)
        for _ in range(2 * n):  # at most 2 full sweeps
            frame = frames[self.hand]
            if frame.pin_count == 0 and frame.page_id is not None:
                if frame.ref_bit:
                    frame.ref_bit = False
                else:
                    victim_id = frame.frame_id
                    self.hand = (self.hand + 1) % n
                    return victim_id
            self.hand = (self.hand + 1) % n
        return None

    def access(self, frame: BufferFrame):
        frame.ref_bit = True


class LRUKPolicy(ReplacementPolicy):
    """
    LRU-K: Evict page whose K-th most recent access is oldest.

    K=2 (LRU-2) is common. Resists sequential scan pollution because
    a page scanned once won't have a second access timestamp.
    """

    def __init__(self, k: int = 2):
        self.k = k
        self.history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=k))

    def victim(self, frames: List[BufferFrame]) -> Optional[int]:
        unpinned = [f for f in frames if f.pin_count == 0 and f.page_id is not None]
        if not unpinned:
            return None

        def kth_access(f: BufferFrame) -> float:
            hist = self.history.get(f.frame_id, deque())
            if len(hist) < self.k:
                return 0.0  # not accessed K times → evict first
            return hist[0]

        return min(unpinned, key=kth_access).frame_id

    def access(self, frame: BufferFrame):
        self.history[frame.frame_id].append(time.monotonic())


class BufferPool:
    """
    Buffer Pool Manager — the heart of any database storage engine.

    Manages fixed-size frames in memory that cache disk pages.
    """

    def __init__(self, pool_size: int = 16,
                 policy: ReplacementPolicy = None):
        self.pool_size = pool_size
        self.frames = [BufferFrame(frame_id=i) for i in range(pool_size)]
        self.page_table: Dict[int, int] = {}  # page_id → frame_id
        self.policy = policy or ClockSweepPolicy()
        # Simulated disk
        self.disk: Dict[int, bytes] = {}
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "flushes": 0}

    def _flush_frame(self, frame: BufferFrame):
        if frame.is_dirty and frame.page_id is not None:
            self.disk[frame.page_id] = frame.data
            frame.is_dirty = False
            self.stats["flushes"] += 1

    def fetch_page(self, page_id: int) -> BufferFrame:
        """Fetch a page into the buffer pool, evicting if necessary."""
        # Hit
        if page_id in self.page_table:
            self.stats["hits"] += 1
            frame = self.frames[self.page_table[page_id]]
            frame.pin_count += 1
            self.policy.access(frame)
            return frame

        # Miss
        self.stats["misses"] += 1

        # Find free frame
        free_frame = None
        for f in self.frames:
            if f.page_id is None:
                free_frame = f
                break

        if free_frame is None:
            # Evict
            victim_id = self.policy.victim(self.frames)
            if victim_id is None:
                raise RuntimeError("All buffer pool frames are pinned!")
            free_frame = self.frames[victim_id]
            self._flush_frame(free_frame)
            del self.page_table[free_frame.page_id]
            self.stats["evictions"] += 1

        # Load page from disk
        free_frame.page_id = page_id
        free_frame.data = self.disk.get(page_id, b'\x00' * BLOCK_SIZE)
        free_frame.is_dirty = False
        free_frame.pin_count = 1
        self.page_table[page_id] = free_frame.frame_id
        self.policy.access(free_frame)
        return free_frame

    def unpin_page(self, page_id: int, is_dirty: bool = False):
        if page_id in self.page_table:
            frame = self.frames[self.page_table[page_id]]
            frame.pin_count = max(0, frame.pin_count - 1)
            if is_dirty:
                frame.is_dirty = True

    def flush_all(self):
        for f in self.frames:
            self._flush_frame(f)

    def hit_rate(self) -> float:
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total > 0 else 0.0


class PrefetchStrategy(Enum):
    NONE = auto()
    SEQUENTIAL = auto()
    STRIDE = auto()


class PrefetchingBufferPool(BufferPool):
    """Buffer pool with prefetching heuristics."""

    def __init__(self, pool_size: int = 32, prefetch_window: int = 4,
                 strategy: PrefetchStrategy = PrefetchStrategy.SEQUENTIAL):
        super().__init__(pool_size)
        self.prefetch_window = prefetch_window
        self.strategy = strategy
        self.access_history: List[int] = []

    def fetch_page(self, page_id: int) -> BufferFrame:
        frame = super().fetch_page(page_id)
        self.access_history.append(page_id)

        if self.strategy == PrefetchStrategy.SEQUENTIAL:
            for offset in range(1, self.prefetch_window + 1):
                next_page = page_id + offset
                if next_page not in self.page_table:
                    try:
                        pf = super().fetch_page(next_page)
                        pf.pin_count = max(0, pf.pin_count - 1)  # unpin prefetch
                    except RuntimeError:
                        break

        elif self.strategy == PrefetchStrategy.STRIDE:
            if len(self.access_history) >= 3:
                stride = (self.access_history[-1] - self.access_history[-2])
                prev_stride = (self.access_history[-2] - self.access_history[-3])
                if stride == prev_stride and stride != 0:
                    for i in range(1, self.prefetch_window + 1):
                        next_page = page_id + stride * i
                        if next_page not in self.page_table and next_page >= 0:
                            try:
                                pf = super().fetch_page(next_page)
                                pf.pin_count = max(0, pf.pin_count - 1)
                            except RuntimeError:
                                break
        return frame


# ============================================================================
# SECTION 4: B-TREE ON-DISK IMPLEMENTATION  (~300 lines)
# ============================================================================
#
#  B+Tree on Disk (page-oriented):
#
#  ┌─────────────────────────────────────────────────┐
#  │  Internal Node (Page)                            │
#  │  ┌──────┬──────┬──────┬──────┬──────┐           │
#  │  │ ptr0 │ key1 │ ptr1 │ key2 │ ptr2 │           │
#  │  └──┬───┴──────┴──┬───┴──────┴──┬───┘           │
#  │     ▼             ▼             ▼                │
#  │  ┌──────┐     ┌──────┐     ┌──────┐             │
#  │  │Leaf  │────▶│Leaf  │────▶│Leaf  │             │
#  │  │k1:v1 │     │k3:v3 │     │k5:v5 │             │
#  │  │k2:v2 │     │k4:v4 │     │k6:v6 │             │
#  │  └──────┘     └──────┘     └──────┘             │
#  │           Leaf nodes linked for range scans      │
#  └─────────────────────────────────────────────────┘

PAGE_SIZE = 4096

# Page layout:
#   [4 bytes: node_type] [4 bytes: num_keys] [4 bytes: parent_page]
#   [4 bytes: next_leaf (leaf only)]
#   For leaf:   [key(8B), value(8B)] * num_keys
#   For internal: [child_ptr(4B), key(8B)] * num_keys + [child_ptr(4B)]
HEADER_SIZE = 16
KEY_SIZE = 8
VALUE_SIZE = 8
PTR_SIZE = 4
LEAF_ENTRY_SIZE = KEY_SIZE + VALUE_SIZE
INTERNAL_ENTRY_SIZE = PTR_SIZE + KEY_SIZE
MAX_LEAF_KEYS = (PAGE_SIZE - HEADER_SIZE) // LEAF_ENTRY_SIZE  # ~254
MAX_INTERNAL_KEYS = (PAGE_SIZE - HEADER_SIZE - PTR_SIZE) // INTERNAL_ENTRY_SIZE  # ~339


class BPlusTreeNodeType(Enum):
    INTERNAL = 1
    LEAF = 2


@dataclass
class BPlusTreeNode:
    page_id: int
    node_type: BPlusTreeNodeType
    keys: List[int] = field(default_factory=list)
    values: List[int] = field(default_factory=list)      # leaf only
    children: List[int] = field(default_factory=list)     # internal only (page_ids)
    parent_page: int = -1
    next_leaf: int = -1  # leaf only — linked list pointer

    def is_leaf(self) -> bool:
        return self.node_type == BPlusTreeNodeType.LEAF

    def is_full(self) -> bool:
        max_k = MAX_LEAF_KEYS if self.is_leaf() else MAX_INTERNAL_KEYS
        # Use smaller limit for demo clarity
        return len(self.keys) >= min(max_k, 4)

    def serialize(self) -> bytes:
        """Serialize node to a fixed-size page."""
        buf = bytearray(PAGE_SIZE)
        struct.pack_into('!I', buf, 0, self.node_type.value)
        struct.pack_into('!I', buf, 4, len(self.keys))
        struct.pack_into('!i', buf, 8, self.parent_page)
        struct.pack_into('!i', buf, 12, self.next_leaf)
        offset = HEADER_SIZE
        if self.is_leaf():
            for i, k in enumerate(self.keys):
                struct.pack_into('!q', buf, offset, k)
                offset += KEY_SIZE
                struct.pack_into('!q', buf, offset,
                                 self.values[i] if i < len(self.values) else 0)
                offset += VALUE_SIZE
        else:
            for i in range(len(self.children)):
                struct.pack_into('!i', buf, offset, self.children[i])
                offset += PTR_SIZE
                if i < len(self.keys):
                    struct.pack_into('!q', buf, offset, self.keys[i])
                    offset += KEY_SIZE
        return bytes(buf)

    @staticmethod
    def deserialize(page_id: int, data: bytes) -> 'BPlusTreeNode':
        node_type_val = struct.unpack_from('!I', data, 0)[0]
        num_keys = struct.unpack_from('!I', data, 4)[0]
        parent = struct.unpack_from('!i', data, 8)[0]
        next_leaf = struct.unpack_from('!i', data, 12)[0]
        node_type = BPlusTreeNodeType(node_type_val)
        node = BPlusTreeNode(page_id=page_id, node_type=node_type,
                              parent_page=parent, next_leaf=next_leaf)
        offset = HEADER_SIZE
        if node.is_leaf():
            for _ in range(num_keys):
                k = struct.unpack_from('!q', data, offset)[0]; offset += KEY_SIZE
                v = struct.unpack_from('!q', data, offset)[0]; offset += VALUE_SIZE
                node.keys.append(k)
                node.values.append(v)
        else:
            for i in range(num_keys + 1):
                c = struct.unpack_from('!i', data, offset)[0]; offset += PTR_SIZE
                node.children.append(c)
                if i < num_keys:
                    k = struct.unpack_from('!q', data, offset)[0]; offset += KEY_SIZE
                    node.keys.append(k)
        return node


class BPlusTree:
    """
    Page-oriented B+Tree with split/merge and serialization.

    Uses small order for demo (max 4 keys per node).
    In production, each node = one 4KB/8KB/16KB disk page.
    """

    def __init__(self):
        self.pages: Dict[int, BPlusTreeNode] = {}
        self.next_page_id = 0
        self.root_page_id = self._new_leaf().page_id
        self.height = 1

    def _new_leaf(self) -> BPlusTreeNode:
        pid = self.next_page_id
        self.next_page_id += 1
        node = BPlusTreeNode(page_id=pid, node_type=BPlusTreeNodeType.LEAF)
        self.pages[pid] = node
        return node

    def _new_internal(self) -> BPlusTreeNode:
        pid = self.next_page_id
        self.next_page_id += 1
        node = BPlusTreeNode(page_id=pid, node_type=BPlusTreeNodeType.INTERNAL)
        self.pages[pid] = node
        return node

    def _find_leaf(self, key: int) -> BPlusTreeNode:
        node = self.pages[self.root_page_id]
        while not node.is_leaf():
            idx = bisect.bisect_right(node.keys, key)
            node = self.pages[node.children[idx]]
        return node

    def search(self, key: int) -> Optional[int]:
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            return leaf.values[idx]
        return None

    def range_scan(self, lo: int, hi: int) -> List[Tuple[int, int]]:
        """Range scan using leaf linked list — O(log n + result_size)."""
        leaf = self._find_leaf(lo)
        results = []
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                if k > hi:
                    return results
                if k >= lo:
                    results.append((k, leaf.values[i]))
            if leaf.next_leaf >= 0:
                leaf = self.pages[leaf.next_leaf]
            else:
                break
        return results

    def insert(self, key: int, value: int):
        leaf = self._find_leaf(key)
        idx = bisect.bisect_left(leaf.keys, key)
        # Update if exists
        if idx < len(leaf.keys) and leaf.keys[idx] == key:
            leaf.values[idx] = value
            return
        leaf.keys.insert(idx, key)
        leaf.values.insert(idx, value)
        if leaf.is_full():
            self._split_leaf(leaf)

    def _split_leaf(self, leaf: BPlusTreeNode):
        """Split a full leaf node, push middle key up to parent."""
        mid = len(leaf.keys) // 2
        new_leaf = self._new_leaf()
        new_leaf.keys = leaf.keys[mid:]
        new_leaf.values = leaf.values[mid:]
        new_leaf.next_leaf = leaf.next_leaf
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        leaf.next_leaf = new_leaf.page_id
        push_up_key = new_leaf.keys[0]
        self._insert_into_parent(leaf, push_up_key, new_leaf)

    def _insert_into_parent(self, left: BPlusTreeNode, key: int,
                            right: BPlusTreeNode):
        if left.parent_page < 0:
            # Create new root
            new_root = self._new_internal()
            new_root.keys = [key]
            new_root.children = [left.page_id, right.page_id]
            left.parent_page = new_root.page_id
            right.parent_page = new_root.page_id
            self.root_page_id = new_root.page_id
            self.height += 1
            return

        parent = self.pages[left.parent_page]
        idx = bisect.bisect_right(parent.keys, key)
        parent.keys.insert(idx, key)
        parent.children.insert(idx + 1, right.page_id)
        right.parent_page = parent.page_id

        if parent.is_full():
            self._split_internal(parent)

    def _split_internal(self, node: BPlusTreeNode):
        mid = len(node.keys) // 2
        push_up_key = node.keys[mid]
        new_node = self._new_internal()
        new_node.keys = node.keys[mid+1:]
        new_node.children = node.children[mid+1:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid+1]
        for child_pid in new_node.children:
            self.pages[child_pid].parent_page = new_node.page_id
        self._insert_into_parent(node, push_up_key, new_node)

    @staticmethod
    def bulk_load(sorted_pairs: List[Tuple[int, int]]) -> 'BPlusTree':
        """
        Bottom-up bulk loading — much faster than repeated inserts.

        1. Create leaf nodes from sorted data
        2. Build internal levels bottom-up
        """
        tree = BPlusTree()
        tree.pages.clear()
        tree.next_page_id = 0
        if not sorted_pairs:
            tree.root_page_id = tree._new_leaf().page_id
            return tree

        max_keys = 4  # demo order
        # Create leaves
        leaves = []
        for i in range(0, len(sorted_pairs), max_keys):
            leaf = tree._new_leaf()
            chunk = sorted_pairs[i:i+max_keys]
            leaf.keys = [p[0] for p in chunk]
            leaf.values = [p[1] for p in chunk]
            leaves.append(leaf)

        # Link leaves
        for i in range(len(leaves) - 1):
            leaves[i].next_leaf = leaves[i+1].page_id

        if len(leaves) == 1:
            tree.root_page_id = leaves[0].page_id
            tree.height = 1
            return tree

        # Build internal levels
        current_level = leaves
        tree.height = 1
        while len(current_level) > 1:
            tree.height += 1
            next_level = []
            for i in range(0, len(current_level), max_keys + 1):
                group = current_level[i:i+max_keys+1]
                internal = tree._new_internal()
                internal.children = [n.page_id for n in group]
                internal.keys = [group[j].keys[0]
                                 for j in range(1, len(group))]
                for n in group:
                    n.parent_page = internal.page_id
                next_level.append(internal)
            current_level = next_level

        tree.root_page_id = current_level[0].page_id
        return tree

    def print_tree(self):
        """Print tree structure level by level."""
        from collections import deque as dq
        q = dq([(self.root_page_id, 0)])
        current_level = 0
        print(f"\n  B+Tree (height={self.height}):")
        level_str = "  "
        while q:
            pid, lvl = q.popleft()
            if lvl > current_level:
                print(level_str)
                level_str = "  "
                current_level = lvl
            node = self.pages[pid]
            if node.is_leaf():
                pairs = list(zip(node.keys, node.values))
                level_str += f"[Leaf p{pid}: {pairs}] "
            else:
                level_str += f"[Int p{pid}: keys={node.keys}] "
                for c in node.children:
                    q.append((c, lvl + 1))
        print(level_str)


def btree_comparison():
    """
    B-Tree vs B+Tree vs B*Tree comparison.

    ┌──────────┬───────────────────┬──────────────────┬──────────────────┐
    │ Property │     B-Tree        │     B+Tree       │     B*Tree       │
    ├──────────┼───────────────────┼──────────────────┼──────────────────┤
    │ Values   │ Internal + Leaf   │ Leaf only        │ Leaf only        │
    │ Leaf Link│ No                │ Yes (linked list)│ Yes              │
    │ Min Fill │ 50%               │ 50%              │ 66%              │
    │ Split    │ 1 → 2             │ 1 → 2            │ 2 → 3            │
    │ Range    │ Slow (tree walk)  │ Fast (leaf scan) │ Fast             │
    │ Use Case │ General           │ Databases (InnoDB│ File systems     │
    │          │                   │  PostgreSQL)     │                  │
    └──────────┴───────────────────┴──────────────────┴──────────────────┘
    """
    print("\n=== B-Tree Family Comparison ===")
    rows = [
        ("Values in",    "Internal+Leaf", "Leaf only",      "Leaf only"),
        ("Leaf linked",  "No",            "Yes",            "Yes"),
        ("Min fill",     "50%",           "50%",            "66%"),
        ("Split",        "1->2",          "1->2",           "2->3 (delay)"),
        ("Range scan",   "Tree walk",     "Leaf chain",     "Leaf chain"),
        ("Used by",      "General",       "InnoDB/PG/SQLite","Some FS"),
    ]
    print(f"  {'Property':<14} {'B-Tree':<18} {'B+Tree':<18} {'B*Tree':<18}")
    print("  " + "-" * 68)
    for prop, bt, bpt, bst in rows:
        print(f"  {prop:<14} {bt:<18} {bpt:<18} {bst:<18}")


# ============================================================================
# SECTION 5: LSM-TREE DEEP DIVE  (~300 lines)
# ============================================================================
#
#  LSM-Tree Architecture:
#
#  Write path:
#   PUT(k,v) → WAL (disk) → MemTable (RAM, sorted)
#                              ↓ flush when full
#                          Immutable MemTable
#                              ↓ write to disk
#                          SSTable (L0)
#                              ↓ compaction
#                          SSTable (L1, L2, ...)
#
#  Read path:
#   GET(k) → MemTable → L0 SSTables → L1 → L2 → ...
#            (check Bloom filter before reading each SSTable)


class SkipListNode:
    """Node in a skip list (used as MemTable in LSM)."""
    def __init__(self, key: int = -1, value: Any = None, level: int = 0):
        self.key = key
        self.value = value
        self.forward: List[Optional[SkipListNode]] = [None] * (level + 1)


class SkipList:
    """
    Skip List — probabilistic balanced search structure.

    Used as MemTable in RocksDB, LevelDB, etc.
    O(log n) insert/search/delete on average.

    Level 3:  HEAD ─────────────────────────────▶ 50 ──▶ NIL
    Level 2:  HEAD ──▶ 10 ─────────▶ 30 ──────▶ 50 ──▶ NIL
    Level 1:  HEAD ──▶ 10 ──▶ 20 ──▶ 30 ──▶ 40 ▶ 50 ──▶ NIL
    Level 0:  HEAD ──▶ 10 ──▶ 20 ──▶ 30 ──▶ 40 ▶ 50 ──▶ NIL
    """

    MAX_LEVEL = 16
    P = 0.5

    def __init__(self):
        self.header = SkipListNode(level=self.MAX_LEVEL)
        self.level = 0
        self.size = 0

    def _random_level(self) -> int:
        lvl = 0
        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl

    def insert(self, key: int, value: Any):
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current

        current = current.forward[0]
        if current and current.key == key:
            current.value = value
            return

        new_level = self._random_level()
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level

        new_node = SkipListNode(key, value, new_level)
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        self.size += 1

    def search(self, key: int) -> Optional[Any]:
        current = self.header
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None

    def items(self) -> List[Tuple[int, Any]]:
        result = []
        current = self.header.forward[0]
        while current:
            result.append((current.key, current.value))
            current = current.forward[0]
        return result


class BloomFilter:
    """
    Bloom Filter — space-efficient probabilistic set membership.

    Used per SSTable to avoid unnecessary disk reads.

    False positive rate ≈ (1 - e^(-kn/m))^k
      m = number of bits
      n = number of elements
      k = number of hash functions
    """

    def __init__(self, expected_items: int, fp_rate: float = 0.01):
        self.size = self._optimal_size(expected_items, fp_rate)
        self.num_hashes = self._optimal_hashes(self.size, expected_items)
        self.bits = [False] * self.size
        self.items_added = 0

    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        """m = -(n * ln(p)) / (ln(2)^2)"""
        if n <= 0:
            return 64
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return max(64, int(m))

    @staticmethod
    def _optimal_hashes(m: int, n: int) -> int:
        """k = (m/n) * ln(2)"""
        if n <= 0:
            return 1
        k = (m / n) * math.log(2)
        return max(1, int(k))

    def _hashes(self, key: int) -> List[int]:
        h1 = hash(key) & 0xFFFFFFFF
        h2 = hash(key * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative
        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

    def add(self, key: int):
        for pos in self._hashes(key):
            self.bits[pos] = True
        self.items_added += 1

    def might_contain(self, key: int) -> bool:
        return all(self.bits[pos] for pos in self._hashes(key))

    def false_positive_rate(self) -> float:
        if self.items_added == 0:
            return 0.0
        k, n, m = self.num_hashes, self.items_added, self.size
        return (1 - math.exp(-k * n / m)) ** k

    def bits_per_key(self) -> float:
        return self.size / max(1, self.items_added)


@dataclass
class SSTable:
    """
    Sorted String Table — immutable on-disk sorted key-value file.

    Layout:
    ┌────────────────────────────────────────────┐
    │  Data Blocks (sorted key-value pairs)       │
    │  ┌─────────┐┌─────────┐┌─────────┐         │
    │  │Block 0  ││Block 1  ││Block 2  │ ...     │
    │  └─────────┘└─────────┘└─────────┘         │
    ├────────────────────────────────────────────┤
    │  Index Block (fence pointers / sparse idx) │
    │  first_key_of_block → block_offset         │
    ├────────────────────────────────────────────┤
    │  Bloom Filter                              │
    ├────────────────────────────────────────────┤
    │  Footer (offsets, metadata)                │
    └────────────────────────────────────────────┘
    """
    level: int
    run_id: int
    entries: List[Tuple[int, Any]]  # sorted by key
    bloom: BloomFilter = field(default=None)
    # Fence pointers: sampled keys for binary search without full scan
    fence_pointers: List[Tuple[int, int]] = field(default_factory=list)
    size_bytes: int = 0

    def __post_init__(self):
        if self.bloom is None:
            self.bloom = BloomFilter(max(1, len(self.entries)))
            for k, _ in self.entries:
                self.bloom.add(k)
        # Build fence pointers (every 16 entries)
        self.fence_pointers = []
        for i in range(0, len(self.entries), 16):
            self.fence_pointers.append((self.entries[i][0], i))
        self.size_bytes = len(self.entries) * 24  # rough estimate

    @property
    def min_key(self) -> int:
        return self.entries[0][0] if self.entries else 0

    @property
    def max_key(self) -> int:
        return self.entries[-1][0] if self.entries else 0

    def get(self, key: int) -> Optional[Any]:
        if not self.bloom.might_contain(key):
            return None  # definitely not here
        # Use fence pointers for coarse search
        block_start = 0
        for fence_key, offset in reversed(self.fence_pointers):
            if key >= fence_key:
                block_start = offset
                break
        # Binary search in block
        lo, hi = block_start, min(block_start + 16, len(self.entries))
        idx = bisect.bisect_left(self.entries, (key,), lo, hi)
        if idx < len(self.entries) and self.entries[idx][0] == key:
            return self.entries[idx][1]
        return None


class CompactionStrategy(Enum):
    SIZE_TIERED = auto()   # Cassandra default
    LEVELED = auto()       # RocksDB default
    FIFO = auto()          # TTL-based, simplest


class LSMTree:
    """
    Full LSM-Tree implementation.

    Write path:  key,value → WAL → MemTable → flush → SSTable
    Read path:   MemTable → L0 SSTables → L1 → L2 → ...

    Compaction reduces read amplification by merging overlapping SSTables.
    """

    def __init__(self, memtable_size: int = 64,
                 strategy: CompactionStrategy = CompactionStrategy.LEVELED,
                 level_ratio: int = 10):
        self.memtable = SkipList()
        self.memtable_size = memtable_size
        self.immutable_memtable: Optional[SkipList] = None
        self.levels: List[List[SSTable]] = [[] for _ in range(7)]  # L0..L6
        self.strategy = strategy
        self.level_ratio = level_ratio
        self.next_run_id = 0
        # Stats
        self.total_writes = 0
        self.total_bytes_written = 0
        self.total_compaction_bytes = 0

    def put(self, key: int, value: Any):
        self.memtable.insert(key, value)
        self.total_writes += 1
        if self.memtable.size >= self.memtable_size:
            self._flush()

    def get(self, key: int) -> Optional[Any]:
        """Read path: MemTable → Immutable → L0 → L1 → ..."""
        # 1. Check active MemTable
        result = self.memtable.search(key)
        if result is not None:
            return result

        # 2. Check immutable MemTable
        if self.immutable_memtable:
            result = self.immutable_memtable.search(key)
            if result is not None:
                return result

        # 3. Check SSTables level by level
        for level_tables in self.levels:
            for sst in reversed(level_tables):  # newest first
                result = sst.get(key)
                if result is not None:
                    return result
        return None

    def _flush(self):
        """Flush MemTable to L0 SSTable."""
        entries = self.memtable.items()
        if not entries:
            return
        sst = SSTable(level=0, run_id=self.next_run_id, entries=entries)
        self.next_run_id += 1
        self.levels[0].append(sst)
        self.total_bytes_written += sst.size_bytes

        self.memtable = SkipList()

        # Trigger compaction if L0 has too many tables
        if len(self.levels[0]) >= 4:
            self._compact(0)

    def _compact(self, level: int):
        """Merge SSTables from level to level+1."""
        if level >= len(self.levels) - 1:
            return

        if self.strategy == CompactionStrategy.LEVELED:
            self._leveled_compaction(level)
        elif self.strategy == CompactionStrategy.SIZE_TIERED:
            self._size_tiered_compaction(level)

    def _leveled_compaction(self, level: int):
        """
        Leveled Compaction (RocksDB style):
        - L0: merge ALL L0 tables with overlapping L1 tables
        - L1+: pick one table, merge with overlapping tables in L(n+1)

        Each level (except L0) has non-overlapping key ranges.
        Level size grows by level_ratio (default 10x).

        Write amplification ≈ level_ratio * num_levels
        Read amplification = 1 per level (due to non-overlapping)
        Space amplification ≈ 1.1x (low)
        """
        tables_to_merge = list(self.levels[level])
        self.levels[level] = []

        # Find overlapping tables in next level
        if tables_to_merge:
            min_k = min(t.min_key for t in tables_to_merge)
            max_k = max(t.max_key for t in tables_to_merge)
            overlapping = [
                t for t in self.levels[level + 1]
                if t.max_key >= min_k and t.min_key <= max_k
            ]
            remaining = [t for t in self.levels[level + 1]
                         if t not in overlapping]
            tables_to_merge.extend(overlapping)

            # Merge all entries
            merged = self._merge_entries(tables_to_merge)
            compaction_bytes = sum(t.size_bytes for t in tables_to_merge)
            self.total_compaction_bytes += compaction_bytes

            # Split into new SSTables (target size = memtable_size entries)
            target_size = self.memtable_size * 2
            new_tables = []
            for i in range(0, len(merged), target_size):
                chunk = merged[i:i+target_size]
                sst = SSTable(level=level + 1, run_id=self.next_run_id,
                              entries=chunk)
                self.next_run_id += 1
                new_tables.append(sst)

            self.levels[level + 1] = remaining + new_tables

            # Cascade if next level is too full
            max_tables = self.level_ratio ** (level + 1)
            if len(self.levels[level + 1]) > max_tables:
                self._compact(level + 1)

    def _size_tiered_compaction(self, level: int):
        """
        Size-Tiered Compaction (Cassandra style):
        - Group similarly-sized SSTables
        - Merge groups together

        Write amplification ≈ O(log n) — lower than leveled
        Read amplification ≈ O(num_tables) — higher
        Space amplification ≈ 2x (higher, needs space for merge)
        """
        tables = self.levels[level]
        if len(tables) < 4:
            return

        # Merge all tables on this level into one on next level
        merged = self._merge_entries(tables)
        self.total_compaction_bytes += sum(t.size_bytes for t in tables)
        self.levels[level] = []

        sst = SSTable(level=level + 1, run_id=self.next_run_id,
                      entries=merged)
        self.next_run_id += 1
        self.levels[level + 1].append(sst)

        if len(self.levels[level + 1]) >= 4:
            self._compact(level + 1)

    @staticmethod
    def _merge_entries(tables: List[SSTable]) -> List[Tuple[int, Any]]:
        """Merge sorted entries from multiple SSTables, newer wins."""
        all_entries: Dict[int, Any] = {}
        for table in tables:
            for k, v in table.entries:
                all_entries[k] = v  # later table overwrites
        return sorted(all_entries.items())

    def write_amplification(self) -> float:
        """WAF = total bytes written to disk / total user bytes written."""
        user_bytes = self.total_writes * 24
        if user_bytes == 0:
            return 0.0
        return (self.total_bytes_written + self.total_compaction_bytes) / user_bytes

    def space_amplification(self) -> float:
        """Ratio of disk space used to actual data size."""
        unique_keys: Set[int] = set()
        total_entries = 0
        for level_tables in self.levels:
            for sst in level_tables:
                total_entries += len(sst.entries)
                for k, _ in sst.entries:
                    unique_keys.add(k)
        if not unique_keys:
            return 1.0
        return total_entries / len(unique_keys)

    def stats(self) -> Dict[str, Any]:
        table_counts = [len(lvl) for lvl in self.levels]
        entry_counts = [sum(len(t.entries) for t in lvl) for lvl in self.levels]
        return {
            "memtable_size": self.memtable.size,
            "tables_per_level": table_counts,
            "entries_per_level": entry_counts,
            "write_amp": round(self.write_amplification(), 2),
            "space_amp": round(self.space_amplification(), 2),
            "strategy": self.strategy.name,
        }


# ============================================================================
# SECTION 6: WRITE-AHEAD LOG (WAL) DEEP  (~200 lines)
# ============================================================================
#
#  WAL guarantees durability: write log BEFORE modifying data pages.
#
#  ┌──────────────────────────────────────────────┐
#  │  WAL Record Layout                           │
#  │  ┌─────┬──────┬───────┬──────┬─────────────┐ │
#  │  │ LSN │ TxnID│ Type  │ PgID │ Before/After│ │
#  │  └─────┴──────┴───────┴──────┴─────────────┘ │
#  │                                              │
#  │  LSN = Log Sequence Number (monotonic)       │
#  │  Types: BEGIN, UPDATE, COMMIT, ABORT, CLR,   │
#  │         CHECKPOINT                           │
#  └──────────────────────────────────────────────┘


class WALRecordType(Enum):
    BEGIN = auto()
    UPDATE = auto()
    COMMIT = auto()
    ABORT = auto()
    COMPENSATION = auto()  # CLR for undo
    CHECKPOINT = auto()


@dataclass
class WALRecord:
    lsn: int
    txn_id: int
    record_type: WALRecordType
    page_id: int = -1
    before_image: Optional[Any] = None  # for undo
    after_image: Optional[Any] = None   # for redo
    prev_lsn: int = -1  # previous LSN for this transaction
    undo_next_lsn: int = -1  # for CLR records


class WriteAheadLog:
    """
    WAL with ARIES-style recovery.

    ARIES Recovery Algorithm (3 phases):

    1. ANALYSIS: Scan log forward from last checkpoint
       - Rebuild Active Transaction Table (ATT)
       - Rebuild Dirty Page Table (DPT)
       - Determine redo start point

    2. REDO: Scan forward from earliest LSN in DPT
       - Reapply ALL logged changes (even for aborted txns)
       - Ensures durability of committed data

    3. UNDO: Scan backward
       - Undo changes of transactions that were active at crash
       - Write CLR (Compensation Log Records) during undo
    """

    def __init__(self):
        self.log: List[WALRecord] = []
        self.next_lsn = 1
        self.txn_last_lsn: Dict[int, int] = {}
        # Simulated database pages
        self.pages: Dict[int, Any] = {}
        self.flushed_lsn = 0  # WAL records flushed to disk up to this LSN
        # Group commit buffer
        self.commit_buffer: List[WALRecord] = []
        self.group_commit_size = 4

    def _append(self, record: WALRecord) -> int:
        record.lsn = self.next_lsn
        record.prev_lsn = self.txn_last_lsn.get(record.txn_id, -1)
        self.next_lsn += 1
        self.log.append(record)
        self.txn_last_lsn[record.txn_id] = record.lsn
        return record.lsn

    def begin(self, txn_id: int) -> int:
        return self._append(WALRecord(
            lsn=0, txn_id=txn_id, record_type=WALRecordType.BEGIN))

    def update(self, txn_id: int, page_id: int,
               before: Any, after: Any) -> int:
        lsn = self._append(WALRecord(
            lsn=0, txn_id=txn_id, record_type=WALRecordType.UPDATE,
            page_id=page_id, before_image=before, after_image=after))
        self.pages[page_id] = after
        return lsn

    def commit(self, txn_id: int) -> int:
        record = WALRecord(lsn=0, txn_id=txn_id,
                           record_type=WALRecordType.COMMIT)
        lsn = self._append(record)
        self.commit_buffer.append(record)
        if len(self.commit_buffer) >= self.group_commit_size:
            self._flush_group_commit()
        return lsn

    def _flush_group_commit(self):
        """
        Group commit: batch multiple commit records into one fsync.
        Reduces I/O by amortizing fsync cost across transactions.
        """
        if self.commit_buffer:
            max_lsn = max(r.lsn for r in self.commit_buffer)
            self.flushed_lsn = max(self.flushed_lsn, max_lsn)
            self.commit_buffer.clear()

    def checkpoint(self, checkpoint_type: str = "fuzzy") -> int:
        """
        Checkpoint types:
        - Sharp: stop all transactions, flush all dirty pages, write checkpoint
        - Fuzzy: record ATT + DPT without stopping transactions
          (used by PostgreSQL, InnoDB)
        """
        active_txns = {}
        committed = set()
        for rec in self.log:
            if rec.record_type == WALRecordType.BEGIN:
                active_txns[rec.txn_id] = rec.lsn
            elif rec.record_type in (WALRecordType.COMMIT, WALRecordType.ABORT):
                active_txns.pop(rec.txn_id, None)
                if rec.record_type == WALRecordType.COMMIT:
                    committed.add(rec.txn_id)

        lsn = self._append(WALRecord(
            lsn=0, txn_id=-1, record_type=WALRecordType.CHECKPOINT,
            before_image={"active_txns": dict(active_txns),
                          "type": checkpoint_type}))
        if checkpoint_type == "sharp":
            self.flushed_lsn = lsn
        return lsn

    def crash_and_recover(self) -> Dict[str, Any]:
        """
        ARIES recovery simulation.

        Returns a report of what each phase did.
        """
        report = {"analysis": [], "redo": [], "undo": []}

        # === PHASE 1: ANALYSIS ===
        # Find last checkpoint
        checkpoint_lsn = -1
        active_txns: Dict[int, int] = {}
        for rec in self.log:
            if rec.record_type == WALRecordType.CHECKPOINT:
                checkpoint_lsn = rec.lsn
                if rec.before_image:
                    active_txns = dict(rec.before_image.get("active_txns", {}))

        # Scan forward from checkpoint to rebuild state
        committed_txns: Set[int] = set()
        dirty_pages: Set[int] = set()
        start_idx = 0
        if checkpoint_lsn > 0:
            start_idx = next(
                (i for i, r in enumerate(self.log)
                 if r.lsn >= checkpoint_lsn), 0)

        for rec in self.log[start_idx:]:
            if rec.record_type == WALRecordType.BEGIN:
                active_txns[rec.txn_id] = rec.lsn
            elif rec.record_type == WALRecordType.COMMIT:
                committed_txns.add(rec.txn_id)
                active_txns.pop(rec.txn_id, None)
            elif rec.record_type == WALRecordType.ABORT:
                active_txns.pop(rec.txn_id, None)
            elif rec.record_type == WALRecordType.UPDATE:
                dirty_pages.add(rec.page_id)

        losers = set(active_txns.keys()) - committed_txns
        report["analysis"] = [
            f"Checkpoint at LSN {checkpoint_lsn}",
            f"Active txns at crash: {active_txns}",
            f"Committed txns: {committed_txns}",
            f"Loser txns (need undo): {losers}",
            f"Dirty pages: {dirty_pages}",
        ]

        # === PHASE 2: REDO ===
        redo_count = 0
        for rec in self.log:
            if rec.record_type == WALRecordType.UPDATE:
                self.pages[rec.page_id] = rec.after_image
                redo_count += 1
        report["redo"].append(f"Redid {redo_count} updates")

        # === PHASE 3: UNDO ===
        undo_count = 0
        for rec in reversed(self.log):
            if (rec.record_type == WALRecordType.UPDATE
                    and rec.txn_id in losers):
                self.pages[rec.page_id] = rec.before_image
                # Write CLR
                self._append(WALRecord(
                    lsn=0, txn_id=rec.txn_id,
                    record_type=WALRecordType.COMPENSATION,
                    page_id=rec.page_id,
                    after_image=rec.before_image,
                    undo_next_lsn=rec.prev_lsn))
                undo_count += 1
        report["undo"].append(f"Undid {undo_count} updates from loser txns")

        return report


# ============================================================================
# SECTION 7: RAID SYSTEMS  (~200 lines)
# ============================================================================
#
#  RAID Levels Overview:
#  ┌───────┬──────────┬──────────┬──────────┬──────────────┐
#  │ Level │ Min Disks│ Usable % │ Fault Tol│ Description  │
#  ├───────┼──────────┼──────────┼──────────┼──────────────┤
#  │ 0     │ 2        │ 100%     │ 0        │ Striping     │
#  │ 1     │ 2        │ 50%      │ 1        │ Mirroring    │
#  │ 5     │ 3        │ (N-1)/N  │ 1        │ Parity       │
#  │ 6     │ 4        │ (N-2)/N  │ 2        │ Dual parity  │
#  │ 10    │ 4        │ 50%      │ 1 per mir│ Stripe+Mirror│
#  └───────┴──────────┴──────────┴──────────┴──────────────┘


class RAIDLevel(Enum):
    RAID0 = 0
    RAID1 = 1
    RAID5 = 5
    RAID6 = 6
    RAID10 = 10


class RAIDArray:
    """
    RAID simulator with data layout, parity, and rebuild.
    """

    def __init__(self, level: RAIDLevel, num_disks: int,
                 disk_size_blocks: int = 100):
        self.level = level
        self.num_disks = num_disks
        self.disk_size = disk_size_blocks
        # Each disk is a list of data blocks (integers for simplicity)
        self.disks: List[List[Optional[int]]] = [
            [None] * disk_size_blocks for _ in range(num_disks)
        ]
        self.failed_disks: Set[int] = set()
        self.hot_spare: Optional[int] = None

    def usable_capacity(self) -> int:
        n = self.num_disks
        if self.level == RAIDLevel.RAID0:
            return n * self.disk_size
        elif self.level == RAIDLevel.RAID1:
            return (n // 2) * self.disk_size
        elif self.level == RAIDLevel.RAID5:
            return (n - 1) * self.disk_size
        elif self.level == RAIDLevel.RAID6:
            return (n - 2) * self.disk_size
        elif self.level == RAIDLevel.RAID10:
            return (n // 2) * self.disk_size
        return 0

    def write_raid0(self, logical_block: int, data: int):
        """RAID 0: stripe across all disks."""
        disk_idx = logical_block % self.num_disks
        block_idx = logical_block // self.num_disks
        self.disks[disk_idx][block_idx] = data

    def read_raid0(self, logical_block: int) -> Optional[int]:
        disk_idx = logical_block % self.num_disks
        block_idx = logical_block // self.num_disks
        if disk_idx in self.failed_disks:
            return None  # data lost
        return self.disks[disk_idx][block_idx]

    def write_raid1(self, logical_block: int, data: int):
        """RAID 1: mirror — write to both disks in pair."""
        pair = (logical_block // self.disk_size) * 2
        offset = logical_block % self.disk_size
        if pair < self.num_disks:
            self.disks[pair][offset] = data
        if pair + 1 < self.num_disks:
            self.disks[pair + 1][offset] = data

    def read_raid1(self, logical_block: int) -> Optional[int]:
        pair = (logical_block // self.disk_size) * 2
        offset = logical_block % self.disk_size
        if pair not in self.failed_disks:
            return self.disks[pair][offset]
        if pair + 1 not in self.failed_disks:
            return self.disks[pair + 1][offset]
        return None

    def _xor_parity(self, values: List[int]) -> int:
        """XOR parity for RAID 5/6."""
        result = 0
        for v in values:
            if v is not None:
                result ^= v
        return result

    def write_raid5(self, stripe: int, data_values: List[int]):
        """
        RAID 5: rotating parity.

        Stripe 0: D D D P
        Stripe 1: D D P D
        Stripe 2: D P D D
        Stripe 3: P D D D
        """
        data_disks = self.num_disks - 1
        parity_disk = (self.num_disks - 1) - (stripe % self.num_disks)
        parity = self._xor_parity(data_values)

        data_idx = 0
        for d in range(self.num_disks):
            if d == parity_disk:
                self.disks[d][stripe] = parity
            else:
                if data_idx < len(data_values):
                    self.disks[d][stripe] = data_values[data_idx]
                    data_idx += 1

    def read_raid5(self, stripe: int) -> List[Optional[int]]:
        """Read a stripe, reconstructing from parity if one disk failed."""
        parity_disk = (self.num_disks - 1) - (stripe % self.num_disks)
        data = []
        for d in range(self.num_disks):
            if d == parity_disk:
                continue
            if d in self.failed_disks:
                # Reconstruct from XOR of all other disks
                others = [
                    self.disks[od][stripe]
                    for od in range(self.num_disks)
                    if od != d and od not in self.failed_disks
                ]
                data.append(self._xor_parity(others))
            else:
                data.append(self.disks[d][stripe])
        return data

    def fail_disk(self, disk_idx: int):
        self.failed_disks.add(disk_idx)

    def rebuild(self, failed_disk: int, target_disk: int = None):
        """
        Rebuild a failed disk from redundancy.

        Rebuild time estimation:
          T_rebuild = disk_capacity / (rebuild_rate - active_io_rate)
          Typical: 1TB disk at 50MB/s ≈ 5.5 hours
        """
        if target_disk is None:
            target_disk = failed_disk

        rebuild_ops = 0
        if self.level in (RAIDLevel.RAID5, RAIDLevel.RAID6):
            for stripe in range(self.disk_size):
                others = [
                    self.disks[d][stripe]
                    for d in range(self.num_disks)
                    if d != failed_disk and d not in self.failed_disks
                ]
                self.disks[target_disk][stripe] = self._xor_parity(others)
                rebuild_ops += 1
        elif self.level == RAIDLevel.RAID1:
            mirror = failed_disk ^ 1  # partner disk
            if mirror not in self.failed_disks:
                for b in range(self.disk_size):
                    self.disks[target_disk][b] = self.disks[mirror][b]
                    rebuild_ops += 1

        self.failed_disks.discard(failed_disk)
        return rebuild_ops

    def rebuild_time_estimate(self, disk_capacity_tb: float = 1.0,
                              rebuild_rate_mb_s: float = 50.0) -> float:
        """Estimate rebuild time in hours."""
        capacity_mb = disk_capacity_tb * 1024 * 1024
        return capacity_mb / rebuild_rate_mb_s / 3600

    def write_hole_risk(self) -> str:
        """
        RAID Write Hole: if power fails between writing data and parity,
        the stripe becomes inconsistent.

        Solutions:
        - Battery-Backed Write Cache (BBWC)
        - Write-intent bitmap (mdadm)
        - ZFS: no write hole due to CoW + checksums
        """
        if self.level in (RAIDLevel.RAID5, RAIDLevel.RAID6):
            return ("RAID write hole risk EXISTS. If crash occurs between "
                    "data write and parity update, stripe is inconsistent. "
                    "Mitigations: BBWC, write-intent bitmap, or use ZFS/btrfs.")
        return "No write hole risk for this RAID level."


# ============================================================================
# SECTION 8: TIER 1-4 PRIORITY REFERENCE
# ============================================================================
#
#  Tier 1 (Must Know for Any Backend Role):
#    - Buffer pool, B+Tree, WAL fundamentals
#    - HDD vs SSD tradeoffs
#    - RAID basics (0/1/5/10)
#
#  Tier 2 (Senior Engineer):
#    - LSM-Tree and compaction strategies
#    - Bloom filters, fence pointers
#    - ARIES recovery algorithm
#    - File system journaling
#
#  Tier 3 (Staff Engineer):
#    - Write amplification analysis
#    - FTL and wear leveling
#    - CoW filesystems, Merkle trees
#    - Concurrent B-Tree (latch crabbing)
#    - Group commit, fuzzy checkpoints
#
#  Tier 4 (Architect / Distinguished):
#    - Storage hardware physics
#    - Custom compaction strategies
#    - RAID write hole and solutions
#    - Cross-engine comparisons (InnoDB vs RocksDB vs WiredTiger)


# ============================================================================
# DEMONSTRATIONS
# ============================================================================

def demo_storage_media():
    print("=" * 72)
    print("  SECTION 1: STORAGE MEDIA PHYSICS")
    print("=" * 72)

    hdd = HDDSimulator()
    print(f"\n  HDD Simulator (7200 RPM):")
    print(f"    Rotational latency:  {hdd.spec.rotational_latency_ms:.2f} ms")
    print(f"    Random read IOPS:    {hdd.random_read_iops():.0f}")
    print(f"    Sequential MB/s:     {hdd.sequential_throughput_mb_s():.0f}")
    print(f"    Random read (track 0→25000): "
          f"{hdd.read_latency_ms(25000):.2f} ms")
    print(f"    Sequential read (next track): "
          f"{hdd.read_latency_ms(25001):.2f} ms")

    print(f"\n  SSD Flash Translation Layer:")
    ftl = FlashTranslationLayer(num_blocks=32, pages_per_block=64)
    random.seed(42)
    for i in range(500):
        ftl.write(random.randint(0, 200))
    for i in range(50):
        ftl.trim(i)
    report = ftl.wear_report()
    print(f"    Write Amplification Factor: {report['waf']:.2f}")
    print(f"    Erase counts — min: {report['min_erase']}, "
          f"max: {report['max_erase']}, avg: {report['avg_erase']:.1f}")
    print(f"    Worn-out blocks: {report['worn_out_blocks']}")

    storage_media_comparison()


def demo_filesystem():
    print("\n" + "=" * 72)
    print("  SECTION 2: FILE SYSTEM INTERNALS")
    print("=" * 72)

    # Inode addressing
    max_size = inode_max_file_size()
    print(f"\n  Inode max file size: {max_size / (1024**4):.1f} TB")
    for blk_idx in [0, 5, 11, 12, 1035, 1048587]:
        print(f"    Block {blk_idx:>10,}: {resolve_block_index(blk_idx)}")

    # ext4 simulator
    print(f"\n  ext4 Simulator:")
    fs = Ext4Simulator(total_blocks=1024, total_inodes=128)
    home = fs.create_directory(2, "home")
    user = fs.create_directory(home.ino, "user")
    f1 = fs.create_file(user.ino, "data.csv", size=16000)
    f2 = fs.create_file(user.ino, "model.pkl", size=8000)

    ino = fs.resolve_path("/home/user/data.csv")
    print(f"    resolve('/home/user/data.csv') → inode {ino}")
    print(f"    stat: {fs.stat(ino)}")
    print(f"    free space: {fs.free_space()}")

    # Journaling
    print(f"\n  Journaling Modes:")
    for mode in JournalMode:
        jfs = JournalingFS(mode)
        jfs.write_file(1, b"hello", {"size": 5})
        jfs.write_file(2, b"world", {"size": 5})
        recovery = jfs.simulate_crash_recovery()
        print(f"    {mode.name:>10}: {recovery[0]}")

    # CoW filesystem
    print(f"\n  Copy-on-Write Filesystem:")
    cow = CopyOnWriteFS()
    cow.write("file1.txt", b"version1")
    cow.create_snapshot("snap1")
    cow.write("file1.txt", b"version2")
    print(f"    Current file1.txt: {cow.read('file1.txt')}")
    print(f"    Snap1   file1.txt: {cow.read('file1.txt', 'snap1')}")
    print(f"    Blocks allocated:  {cow.next_block_id} "
          f"(old block preserved for snapshot)")

    # Merkle tree
    blocks = [f"block{i}".encode() for i in range(8)]
    merkle = MerkleChecksumTree()
    merkle.build(blocks)
    print(f"\n  Merkle Checksum Tree:")
    print(f"    Root hash: {merkle.root_hash()}")
    print(f"    Verify block 3 (valid): {merkle.verify(3, blocks[3])}")
    print(f"    Verify block 3 (corrupt): {merkle.verify(3, b'bad')}")


def demo_buffer_pool():
    print("\n" + "=" * 72)
    print("  SECTION 3: BUFFER POOL & PAGE CACHE")
    print("=" * 72)

    policies = [
        ("LRU", LRUPolicy()),
        ("Clock-Sweep", ClockSweepPolicy()),
        ("LRU-2", LRUKPolicy(k=2)),
    ]

    for name, policy in policies:
        bp = BufferPool(pool_size=8, policy=policy)
        # Simulate workload: hot pages (0-3) + sequential scan (100-115)
        random.seed(42)
        # Phase 1: establish hot pages
        for _ in range(50):
            pg = random.choice([0, 1, 2, 3])
            f = bp.fetch_page(pg)
            bp.unpin_page(pg)
        # Phase 2: sequential scan (should not evict hot pages ideally)
        for pg in range(100, 116):
            f = bp.fetch_page(pg)
            bp.unpin_page(pg)
        # Phase 3: access hot pages again
        hot_hits = 0
        for pg in [0, 1, 2, 3]:
            f = bp.fetch_page(pg)
            if bp.stats["hits"] > 0:  # simplified check
                hot_hits += 1
            bp.unpin_page(pg)

        print(f"\n  {name} Policy:")
        print(f"    Hit rate: {bp.hit_rate():.1%}")
        print(f"    Stats: hits={bp.stats['hits']}, "
              f"misses={bp.stats['misses']}, "
              f"evictions={bp.stats['evictions']}")

    # Prefetching demo
    print(f"\n  Prefetching (sequential):")
    pbp = PrefetchingBufferPool(pool_size=32, prefetch_window=4,
                                strategy=PrefetchStrategy.SEQUENTIAL)
    for pg in range(0, 20):
        f = pbp.fetch_page(pg)
        pbp.unpin_page(pg)
    print(f"    After sequential scan of 20 pages:")
    print(f"    Hit rate: {pbp.hit_rate():.1%} "
          f"(prefetching turns misses into hits)")


def demo_btree():
    print("\n" + "=" * 72)
    print("  SECTION 4: B+TREE ON-DISK IMPLEMENTATION")
    print("=" * 72)

    # Insert-based construction
    tree = BPlusTree()
    keys = [15, 25, 35, 45, 5, 10, 20, 30, 40, 50, 55, 60]
    for k in keys:
        tree.insert(k, k * 100)
    tree.print_tree()

    print(f"\n  Point lookups:")
    for k in [25, 42, 55]:
        v = tree.search(k)
        print(f"    search({k}) = {v}")

    print(f"\n  Range scan [20, 45]:")
    results = tree.range_scan(20, 45)
    print(f"    {results}")

    # Serialization round-trip
    node = tree.pages[tree.root_page_id]
    serialized = node.serialize()
    deserialized = BPlusTreeNode.deserialize(node.page_id, serialized)
    print(f"\n  Serialization round-trip:")
    print(f"    Original keys:      {node.keys}")
    print(f"    Deserialized keys:  {deserialized.keys}")
    print(f"    Page size:          {len(serialized)} bytes")

    # Bulk load
    print(f"\n  Bulk Loading (bottom-up):")
    sorted_data = [(i, i * 10) for i in range(0, 100, 5)]
    bulk_tree = BPlusTree.bulk_load(sorted_data)
    bulk_tree.print_tree()
    print(f"    Height: {bulk_tree.height}, "
          f"Pages: {len(bulk_tree.pages)}")

    btree_comparison()


def demo_lsm():
    print("\n" + "=" * 72)
    print("  SECTION 5: LSM-TREE DEEP DIVE")
    print("=" * 72)

    # Bloom filter demo
    print(f"\n  Bloom Filter:")
    bf = BloomFilter(expected_items=1000, fp_rate=0.01)
    for i in range(1000):
        bf.add(i)
    false_positives = sum(1 for i in range(1000, 2000) if bf.might_contain(i))
    print(f"    Size: {bf.size} bits ({bf.bits_per_key():.1f} bits/key)")
    print(f"    Hash functions: {bf.num_hashes}")
    print(f"    Theoretical FP rate: {bf.false_positive_rate():.4f}")
    print(f"    Empirical FP rate:   {false_positives / 1000:.4f}")

    # Skip list (MemTable)
    print(f"\n  Skip List (MemTable):")
    sl = SkipList()
    random.seed(42)
    for i in random.sample(range(100), 20):
        sl.insert(i, f"val_{i}")
    items = sl.items()
    print(f"    Inserted 20 random keys, sorted output: "
          f"{[k for k, v in items[:10]]}...")
    print(f"    search(42) = {sl.search(42)}")

    # LSM Tree — Leveled vs Size-Tiered
    for strategy in [CompactionStrategy.LEVELED, CompactionStrategy.SIZE_TIERED]:
        print(f"\n  LSM-Tree ({strategy.name}):")
        lsm = LSMTree(memtable_size=32, strategy=strategy)
        random.seed(42)
        for i in range(500):
            lsm.put(random.randint(0, 200), f"v{i}")

        # Read verification
        found = sum(1 for k in range(200) if lsm.get(k) is not None)
        stats = lsm.stats()
        print(f"    Tables per level: {stats['tables_per_level']}")
        print(f"    Entries per level: {stats['entries_per_level']}")
        print(f"    Write amplification: {stats['write_amp']}x")
        print(f"    Space amplification: {stats['space_amp']}x")
        print(f"    Keys found: {found}/200")

    # Compaction strategy comparison
    print(f"""
  Compaction Strategy Comparison:
  ┌──────────────┬──────────────┬──────────────┬──────────────┐
  │  Metric      │ Size-Tiered  │  Leveled     │  FIFO        │
  ├──────────────┼──────────────┼──────────────┼──────────────┤
  │ Write Amp    │ O(log N)     │ O(L × ratio) │ O(1)         │
  │ Read Amp     │ O(N tables)  │ O(1/level)   │ O(N tables)  │
  │ Space Amp    │ ~2x          │ ~1.1x        │ ~1x          │
  │ Write Speed  │ Fast         │ Medium       │ Fastest      │
  │ Read Speed   │ Slow         │ Fast         │ Slow         │
  │ Used By      │ Cassandra    │ RocksDB      │ TTL data     │
  └──────────────┴──────────────┴──────────────┴──────────────┘""")


def demo_wal():
    print("\n" + "=" * 72)
    print("  SECTION 6: WRITE-AHEAD LOG (WAL)")
    print("=" * 72)

    wal = WriteAheadLog()

    # Transaction 1: commits
    wal.begin(1)
    wal.update(1, page_id=10, before="old_A", after="new_A")
    wal.update(1, page_id=20, before="old_B", after="new_B")
    wal.commit(1)

    # Transaction 2: active at crash (will be undone)
    wal.begin(2)
    wal.update(2, page_id=30, before="old_C", after="new_C")
    wal.update(2, page_id=40, before="old_D", after="new_D")
    # NO COMMIT — simulating crash

    # Transaction 3: commits
    wal.begin(3)
    wal.update(3, page_id=50, before="old_E", after="new_E")
    wal.commit(3)

    # Checkpoint
    wal.checkpoint("fuzzy")

    print(f"\n  WAL Log ({len(wal.log)} records):")
    for rec in wal.log:
        extra = ""
        if rec.record_type == WALRecordType.UPDATE:
            extra = f" page={rec.page_id} [{rec.before_image}→{rec.after_image}]"
        print(f"    LSN={rec.lsn:>3} Txn={rec.txn_id:>2} "
              f"{rec.record_type.name:<13}{extra}")

    # Simulate crash and recovery
    print(f"\n  ARIES Recovery (crash with Txn 2 uncommitted):")
    report = wal.crash_and_recover()
    for phase in ["analysis", "redo", "undo"]:
        print(f"    {phase.upper()}:")
        for line in report[phase]:
            print(f"      {line}")

    print(f"\n  Pages after recovery:")
    for pid in sorted(wal.pages.keys()):
        print(f"    Page {pid}: {wal.pages[pid]}")
    print(f"    (Pages 30,40 reverted to old_C,old_D — Txn 2 undone)")

    # Group commit explanation
    print(f"""
  Group Commit Optimization:
  ┌─────────────────────────────────────────────────┐
  │  Without group commit:                          │
  │    Txn1 commit → fsync → Txn2 commit → fsync   │
  │    Each fsync ≈ 5-10ms (HDD) or 50μs (SSD)     │
  │    Max commits/sec = 1/fsync_time               │
  │                                                 │
  │  With group commit (batch size=4):              │
  │    Txn1,2,3,4 commit → single fsync             │
  │    4x throughput improvement                    │
  │    PostgreSQL: commit_delay + commit_siblings   │
  └─────────────────────────────────────────────────┘""")


def demo_raid():
    print("\n" + "=" * 72)
    print("  SECTION 7: RAID SYSTEMS")
    print("=" * 72)

    # RAID 5 demo
    print(f"\n  RAID 5 (4 disks):")
    raid5 = RAIDArray(RAIDLevel.RAID5, num_disks=4, disk_size_blocks=20)
    print(f"    Usable capacity: {raid5.usable_capacity()} blocks "
          f"({raid5.usable_capacity() * 100 // (4 * 20)}%)")

    # Write stripes
    for stripe in range(5):
        data = [stripe * 10 + d for d in range(3)]
        raid5.write_raid5(stripe, data)
        parity = raid5._xor_parity(data)
        print(f"    Stripe {stripe}: data={data}, parity={parity}")

    # Fail disk and read
    print(f"\n  Failing disk 2...")
    raid5.fail_disk(2)
    for stripe in range(3):
        recovered = raid5.read_raid5(stripe)
        print(f"    Stripe {stripe} (degraded read): {recovered}")

    # Rebuild
    ops = raid5.rebuild(2)
    print(f"    Rebuild complete: {ops} blocks reconstructed")
    for stripe in range(3):
        data = raid5.read_raid5(stripe)
        print(f"    Stripe {stripe} (after rebuild): {data}")

    # Rebuild time estimate
    for size_tb in [1, 4, 12]:
        hours = raid5.rebuild_time_estimate(disk_capacity_tb=size_tb)
        print(f"    Rebuild {size_tb}TB disk @ 50MB/s: {hours:.1f} hours")

    # RAID comparison
    print(f"\n  RAID Level Comparison:")
    for level, ndisks in [(RAIDLevel.RAID0, 4), (RAIDLevel.RAID1, 4),
                           (RAIDLevel.RAID5, 4), (RAIDLevel.RAID6, 4),
                           (RAIDLevel.RAID10, 4)]:
        arr = RAIDArray(level, ndisks, 100)
        cap = arr.usable_capacity()
        pct = cap * 100 // (ndisks * 100)
        print(f"    RAID {level.value:>2}: {ndisks} disks × 100 blocks = "
              f"{cap} usable ({pct}%)")

    # Write hole
    print(f"\n  RAID Write Hole:")
    print(f"    {raid5.write_hole_risk()}")


def demo_cross_engine_comparison():
    """Tier 4: Cross-engine architecture comparison."""
    print(f"""
  ┌─────────────────────────────────────────────────────────────────┐
  │         Storage Engine Architecture Comparison                  │
  ├────────────┬───────────┬───────────┬───────────┬───────────────┤
  │ Feature    │ InnoDB    │ RocksDB   │WiredTiger │ PostgreSQL    │
  ├────────────┼───────────┼───────────┼───────────┼───────────────┤
  │ Structure  │ B+Tree    │ LSM-Tree  │ B-Tree+   │ Heap+B-Tree   │
  │            │           │           │ LSM hybrid│               │
  │ Buffer Mgr │ LRU       │ Block     │ WT cache  │ Clock-Sweep   │
  │            │           │ cache     │           │               │
  │ WAL        │ Redo log  │ WAL       │ Journal   │ WAL           │
  │ Recovery   │ ARIES-like│ Replay    │ Checkpoint│ ARIES         │
  │ MVCC       │ Undo log  │ Sequence# │ Timestamps│ Tuple version │
  │ Compaction │ N/A       │ Leveled/  │ Background│ VACUUM        │
  │            │           │ Universal │ merge     │               │
  │ Best For   │ OLTP      │ Write-    │ Mixed     │ General       │
  │            │ balanced  │ heavy     │ workloads │ purpose       │
  │ Used By    │ MySQL     │ CockroachDB│ MongoDB  │ PostgreSQL    │
  │            │           │ TiKV      │           │               │
  └────────────┴───────────┴───────────┴───────────┴───────────────┘""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("╔" + "═" * 70 + "╗")
    print("║  Storage Engine Internals — From Physics to Data Structures       ║")
    print("║  Based on: Database Internals (Petrov) + OSTEP                    ║")
    print("╚" + "═" * 70 + "╝")

    demo_storage_media()
    demo_filesystem()
    demo_buffer_pool()
    demo_btree()
    demo_lsm()
    demo_wal()
    demo_raid()
    demo_cross_engine_comparison()

    print("\n" + "=" * 72)
    print("  KEY FORMULAS REFERENCE")
    print("=" * 72)
    print(f"""
  HDD Random I/O Latency:
    T = T_seek + T_rotation + T_transfer
    IOPS = 1000 / (T_seek_ms + T_rotation_ms)

  SSD Write Amplification:
    WAF = Physical Writes / Logical Writes
    Ideal WAF = 1.0, typical 2-10x depending on workload

  B+Tree Height:
    h = ceil(log_B(N)) where B = branching factor, N = num keys
    4KB page, 8B keys → B ≈ 254 → 254^3 ≈ 16M keys in 3 levels

  LSM Write Amplification:
    Leveled: WAF ≈ size_ratio × num_levels
    Size-tiered: WAF ≈ num_levels

  Bloom Filter:
    Bits needed: m = -(n × ln(p)) / (ln2)^2
    Optimal hashes: k = (m/n) × ln2
    10 bits/key → ~1% FP rate

  RAID 5 Usable Capacity:
    C = (N-1) × disk_size   (1 disk worth of parity)

  RAID Rebuild Time:
    T = disk_capacity / (rebuild_rate - active_io_rate)
""")

    print("  [All demos completed successfully]")


if __name__ == "__main__":
    main()
