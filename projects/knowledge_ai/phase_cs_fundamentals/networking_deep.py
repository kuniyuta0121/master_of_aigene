"""
============================================================
ネットワーク & プロトコル 完全ガイド
============================================================
TCP内部動作、HTTP進化、DNS、CDN、WebSocket、gRPC、
ロードバランシング、TLS/SSL を網羅的に実装・解説する。

Python標準ライブラリのみ使用。
"""

import time
import random
import hashlib
import struct
import enum
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# ============================================================
# 1. TCP Deep Internals
# ============================================================

class TCPFlag(enum.IntFlag):
    """TCPフラグビット"""
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20

@dataclass
class TCPSegment:
    """TCPセグメント構造"""
    src_port: int
    dst_port: int
    seq_num: int
    ack_num: int
    flags: TCPFlag
    window_size: int = 65535
    data: bytes = b""

    def __str__(self):
        flag_names = [f.name for f in TCPFlag if f in self.flags]
        return (f"[{','.join(flag_names)}] seq={self.seq_num} "
                f"ack={self.ack_num} win={self.window_size} "
                f"data={len(self.data)}B")


def simulate_three_way_handshake():
    """3-Way Handshake シミュレーション

    クライアント              サーバー
       |--- SYN (seq=x) ------->|
       |<-- SYN-ACK (seq=y, ack=x+1) ---|
       |--- ACK (seq=x+1, ack=y+1) ---->|
       |      接続確立 (ESTABLISHED)      |
    """
    print("=== TCP 3-Way Handshake ===")
    client_isn = random.randint(1000, 9999)  # Initial Sequence Number
    server_isn = random.randint(1000, 9999)

    # Step 1: クライアント → SYN
    syn = TCPSegment(
        src_port=49152, dst_port=80,
        seq_num=client_isn, ack_num=0,
        flags=TCPFlag.SYN
    )
    print(f"  Client → Server: {syn}")

    # Step 2: サーバー → SYN-ACK
    syn_ack = TCPSegment(
        src_port=80, dst_port=49152,
        seq_num=server_isn, ack_num=client_isn + 1,
        flags=TCPFlag.SYN | TCPFlag.ACK
    )
    print(f"  Server → Client: {syn_ack}")

    # Step 3: クライアント → ACK
    ack = TCPSegment(
        src_port=49152, dst_port=80,
        seq_num=client_isn + 1, ack_num=server_isn + 1,
        flags=TCPFlag.ACK
    )
    print(f"  Client → Server: {ack}")
    print("  → ESTABLISHED (接続確立)\n")

    # なぜ3-wayなのか
    print("  【なぜ3-wayか】")
    print("  - 2-way: サーバーがクライアントの到達性を確認できない")
    print("  - 古いSYNの重複接続問題を防止 (ISNの検証)")
    print("  - 双方向の通信路確立を保証")


class SlidingWindowProtocol:
    """スライディングウィンドウプロトコル実装

    送信側ウィンドウ:
    [送信済&ACK済 | 送信済&未ACK | 送信可能 | 送信不可]

    受信側ウィンドウ:
    [受信済&配送済 | 受信可能 | 受信不可]
    """
    def __init__(self, window_size: int = 4):
        self.window_size = window_size
        self.base = 0           # 最も古い未ACKパケット
        self.next_seq = 0       # 次に送信するシーケンス番号
        self.acked = set()      # ACK済みセット
        self.buffer: Dict[int, str] = {}

    def send(self, data_list: List[str]):
        """ウィンドウ制御付き送信シミュレーション"""
        total = len(data_list)
        print(f"=== Sliding Window (size={self.window_size}) ===")
        round_num = 0

        while self.base < total:
            round_num += 1
            print(f"\n  --- Round {round_num} ---")

            # ウィンドウ内で送信可能なパケットを送信
            while (self.next_seq < self.base + self.window_size
                   and self.next_seq < total):
                print(f"  送信: seq={self.next_seq} data='{data_list[self.next_seq]}'")
                self.buffer[self.next_seq] = data_list[self.next_seq]
                self.next_seq += 1

            # ACK受信シミュレーション (ランダムにパケロスあり)
            for seq in range(self.base, self.next_seq):
                if seq not in self.acked:
                    if random.random() > 0.2:  # 80%の確率で到達
                        self.acked.add(seq)
                        print(f"  ACK受信: seq={seq}")
                    else:
                        print(f"  ✗ パケットロス: seq={seq}")

            # ウィンドウスライド (連続ACK済みまでbaseを進める)
            while self.base in self.acked:
                self.base += 1

            window_view = []
            for i in range(total):
                if i < self.base:
                    window_view.append(f"[{i}:済]")
                elif i < self.next_seq:
                    status = "ACK" if i in self.acked else "未ACK"
                    window_view.append(f"[{i}:{status}]")
                elif i < self.base + self.window_size:
                    window_view.append(f"[{i}:送信可]")
                else:
                    window_view.append(f"[{i}:待機]")
            print(f"  Window: {' '.join(window_view)}")

        print(f"\n  全パケット送信完了 ({round_num} rounds)")


class CongestionControl:
    """TCP輻輳制御シミュレーション

    フェーズ:
    1. Slow Start: cwnd を指数的に増加 (1→2→4→8...)
    2. Congestion Avoidance: cwnd を線形に増加 (ssthresh以降)
    3. Fast Recovery: 3重複ACKで cwnd を半減 (Reno)
    """
    def __init__(self):
        self.cwnd = 1.0          # Congestion Window (MSS単位)
        self.ssthresh = 16.0     # Slow Start Threshold
        self.phase = "slow_start"
        self.history: List[Tuple[int, float, str]] = []

    def simulate(self, rounds: int = 25):
        print("=== TCP Congestion Control (Reno) ===")
        print(f"  初期 cwnd={self.cwnd}, ssthresh={self.ssthresh}\n")

        for rtt in range(1, rounds + 1):
            # パケットロスシミュレーション (cwndが大きいと起きやすい)
            loss = random.random() < (self.cwnd / 50.0)

            if loss:
                # Fast Recovery: ssthreshを半分に、cwndをssthreshに
                self.ssthresh = max(self.cwnd / 2, 2)
                self.cwnd = self.ssthresh  # Reno: ssthreshから再開
                self.phase = "congestion_avoidance"
                event = "LOSS"
            elif self.phase == "slow_start":
                # Slow Start: 1 ACKあたり cwnd += 1 MSS (指数増加)
                self.cwnd += 1
                if self.cwnd >= self.ssthresh:
                    self.phase = "congestion_avoidance"
                event = "SS"
            else:
                # Congestion Avoidance: 1 RTTあたり cwnd += 1/cwnd (線形増加)
                self.cwnd += 1.0 / self.cwnd
                event = "CA"

            self.history.append((rtt, self.cwnd, event))
            bar = "#" * int(self.cwnd)
            print(f"  RTT {rtt:2d}: cwnd={self.cwnd:6.1f} "
                  f"ssth={self.ssthresh:5.1f} [{self.phase:22s}] "
                  f"{'!! LOSS' if loss else ''} {bar}")

    @staticmethod
    def print_comparison():
        """TCP vs UDP トレードオフ表"""
        print("\n=== TCP vs UDP 比較表 ===")
        rows = [
            ("接続",         "コネクション型 (3-way HS)",  "コネクションレス"),
            ("信頼性",       "保証 (再送・順序制御)",       "保証なし"),
            ("フロー制御",   "あり (Sliding Window)",      "なし"),
            ("輻輳制御",     "あり (Slow Start等)",        "なし"),
            ("オーバーヘッド","大 (20Bヘッダ)",             "小 (8Bヘッダ)"),
            ("遅延",         "高い (HS + ACK待ち)",        "低い"),
            ("用途",         "HTTP, SSH, DB接続",          "DNS, VoIP, ゲーム, 動画"),
            ("Head-of-Line", "あり (1パケロスで全停止)",    "なし"),
        ]
        print(f"  {'項目':14s} | {'TCP':28s} | {'UDP':28s}")
        print(f"  {'-'*14}-+-{'-'*28}-+-{'-'*28}")
        for item, tcp, udp in rows:
            print(f"  {item:14s} | {tcp:28s} | {udp:28s}")

    @staticmethod
    def explain_nagle_delayed_ack():
        """Nagle アルゴリズムと Delayed ACK の問題"""
        print("\n=== Nagle's Algorithm & Delayed ACK 問題 ===")
        print("""
  【Nagle's Algorithm】
  - 小さなパケットの大量送信を防ぐ
  - ルール: 未ACKデータがある場合、小データはバッファして送らない
  - 効果: ネットワーク効率向上 (Silly Window Syndrome 防止)

  【Delayed ACK】
  - ACKを即座に返さず、最大200ms待って他データとまとめて返す
  - 効果: ACKパケット数削減

  【組み合わせ問題】
  - Nagle: 「ACK来るまで次を送らない」
  - Delayed ACK: 「ACKを遅らせる」
  → 結果: 最大200msの不要な遅延が発生 (Write-Write-Read パターン)

  【対策】
  - TCP_NODELAY: Nagle無効化 (低レイテンシ要求時)
  - TCP_QUICKACK: Delayed ACK無効化 (Linux)
  - アプリ側でバッファリングしてまとめて送信
""")


# ============================================================
# 2. HTTP プロトコル進化
# ============================================================

class HTTPEvolution:
    """HTTP/1.1 → HTTP/2 → HTTP/3 の進化を解説"""

    @staticmethod
    def http11_simulation():
        """HTTP/1.1 の動作シミュレーション"""
        print("=== HTTP/1.1 ===")
        print("""
  【Keep-Alive】
  - HTTP/1.0: リクエストごとにTCP接続 (遅い)
  - HTTP/1.1: Connection: keep-alive でTCP再利用
  - 同一接続で複数リクエスト/レスポンスを順次処理

  【Pipelining】
  - 複数リクエストをACK待たずに連続送信
  - ただしレスポンスは順番通りに返す必要あり
  - → Head-of-Line Blocking が発生

  【Head-of-Line Blocking 問題】
  Request 1 ──→ [処理中...遅い] → Response 1
  Request 2 ──→              待機 → Response 2  ← 1が終わるまで待つ
  Request 3 ──→              待機 → Response 3
""")
        # Keep-Alive vs 毎回接続のシミュレーション
        tcp_setup = 50   # ms
        request_time = 10  # ms
        n_requests = 6

        # 毎回接続
        no_keepalive = n_requests * (tcp_setup + request_time)
        # Keep-Alive (初回のみTCP接続)
        keepalive = tcp_setup + n_requests * request_time
        print(f"  {n_requests}リクエスト送信:")
        print(f"    毎回接続:  {no_keepalive}ms (TCP接続 x {n_requests})")
        print(f"    Keep-Alive: {keepalive}ms (TCP接続 x 1)")
        print(f"    → {no_keepalive - keepalive}ms 短縮\n")

    @staticmethod
    def http2_simulation():
        """HTTP/2 の主要機能シミュレーション"""
        print("=== HTTP/2 ===")

        # Binary Framing
        print("  【Binary Framing Layer】")
        print("  HTTP/1.1: テキストベース (改行区切り)")
        print("  HTTP/2:   バイナリフレーム (効率的パース)")
        frame_header = struct.pack(">I", 0x00_00_1A)[:3]  # 26バイトのペイロード長
        frame_type = b'\x01'     # HEADERS frame
        frame_flags = b'\x05'    # END_STREAM | END_HEADERS
        stream_id = struct.pack(">I", 1)
        print(f"  フレーム例: length={len(frame_header)}B type=HEADERS "
              f"flags=0x05 stream_id=1\n")

        # Multiplexing
        print("  【Multiplexing (多重化)】")
        print("  1つのTCP接続で複数ストリームを並行処理")
        streams = [
            (1, "index.html",  30),
            (3, "style.css",   15),
            (5, "app.js",      45),
            (7, "image.png",   80),
        ]
        print(f"  {'Stream':8s} | {'リソース':14s} | {'時間(ms)':8s}")
        print(f"  {'-'*8}-+-{'-'*14}-+-{'-'*8}")
        for sid, resource, ms in streams:
            print(f"  {sid:<8d} | {resource:14s} | {ms:8d}")

        # HTTP/1.1: 直列 → HTTP/2: 並列
        serial = sum(ms for _, _, ms in streams)
        parallel = max(ms for _, _, ms in streams)
        print(f"\n  HTTP/1.1 (直列): {serial}ms")
        print(f"  HTTP/2 (並列):   {parallel}ms  → {serial - parallel}ms短縮\n")

        # HPACK Header Compression
        print("  【HPACK ヘッダ圧縮】")
        headers_raw = {
            ":method": "GET",
            ":path": "/api/users",
            ":scheme": "https",
            ":authority": "example.com",
            "accept": "application/json",
            "authorization": "Bearer eyJhbGciOiJSUz...",
        }
        raw_size = sum(len(k) + len(v) for k, v in headers_raw.items())

        # 静的テーブル: よく使うヘッダはインデックスで表現
        static_table = {":method GET": 2, ":scheme https": 7}
        compressed_items = []
        for k, v in headers_raw.items():
            key = f"{k} {v}"
            if key in static_table:
                compressed_items.append(f"  index={static_table[key]}")
            else:
                compressed_items.append(f"  {k}: {v[:20]}...")
        compressed_size = int(raw_size * 0.4)  # 約60%削減
        print(f"  元サイズ: {raw_size}B → 圧縮後: ~{compressed_size}B "
              f"({100 - int(compressed_size/raw_size*100)}%削減)\n")

        # Stream Priority
        print("  【Stream Priority】")
        print("  CSS/JS を画像より優先 → レンダリング高速化")
        print("  依存関係ツリーで制御 (weight: 1-256)")

    @staticmethod
    def http3_quic():
        """HTTP/3 (QUIC) の解説"""
        print("=== HTTP/3 (QUIC) ===")
        print("""
  【UDP上のHTTP】
  - TCP + TLS の代わりに QUIC (UDP上に構築)
  - カーネル空間でなくユーザー空間で実装 → 高速イテレーション

  【0-RTT 接続確立】
  TCP+TLS 1.3: 2-RTT (TCP HS + TLS HS)
  QUIC:        1-RTT (初回) / 0-RTT (再接続)

  接続時間比較:
    TCP+TLS 1.3: SYN → SYN-ACK → ACK+ClientHello → ServerHello → データ
                 |---------- 2 RTT ---------|
    QUIC:        Initial → Handshake → データ
                 |--- 1 RTT ---|
    QUIC 0-RTT:  Initial(+データ) → レスポンス
                 |-- 0 RTT --|

  【Connection Migration】
  - 接続IDベース (IPアドレス非依存)
  - WiFi → 4G 切替時もコネクション維持
  - モバイル環境で大きなメリット

  【Stream Independence (ストリーム独立性)】
  HTTP/2 問題: 1パケットロスで全ストリーム停止 (TCP HoL Blocking)
  HTTP/3 解決: ストリームごとに独立 → 影響が局所化
""")

    @staticmethod
    def performance_comparison():
        """HTTP バージョン間パフォーマンス比較シミュレーション"""
        print("=== HTTP パフォーマンス比較 ===")
        rtt = 50  # ms
        resources = 20
        connections_11 = 6  # ブラウザの並列接続上限

        # HTTP/1.1: 6並列接続で直列処理
        rounds_11 = (resources + connections_11 - 1) // connections_11
        time_11 = rounds_11 * rtt * 2  # 往復
        # HTTP/2: 1接続で全並列
        time_2 = rtt * 2 + rtt  # 接続 + 全リソース並列
        # HTTP/3: 0-RTT可能
        time_3 = rtt  # 0-RTT再接続時

        print(f"  条件: RTT={rtt}ms, リソース数={resources}")
        print(f"  HTTP/1.1: ~{time_11}ms (6並列TCP, {rounds_11}ラウンド)")
        print(f"  HTTP/2:   ~{time_2}ms (1TCP, 全多重化)")
        print(f"  HTTP/3:   ~{time_3}ms (0-RTT再接続時)")


# ============================================================
# 3. DNS 完全解説
# ============================================================

@dataclass
class DNSRecord:
    """DNSレコード"""
    name: str
    record_type: str    # A, AAAA, CNAME, MX, TXT, SRV, NS, SOA
    value: str
    ttl: int = 300      # Time To Live (秒)
    priority: int = 0   # MX, SRV用
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl

    def remaining_ttl(self) -> int:
        return max(0, int(self.ttl - (time.time() - self.created_at)))


class DNSResolver:
    """DNS リゾルバ シミュレーション (キャッシュ + 再帰/反復クエリ)"""

    # レコードタイプ解説
    RECORD_TYPES = {
        "A":     "IPv4アドレス (例: 93.184.216.34)",
        "AAAA":  "IPv6アドレス (例: 2606:2800:220:1::)",
        "CNAME": "正規名 (エイリアス → 実ホスト名)",
        "MX":    "メールサーバー (優先度付き)",
        "TXT":   "テキスト情報 (SPF, DKIM, ドメイン認証)",
        "SRV":   "サービスロケーション (ポート・重み付き)",
        "NS":    "権威ネームサーバー",
        "SOA":   "ゾーン管理情報 (シリアル番号, リフレッシュ間隔)",
    }

    def __init__(self):
        # キャッシュ: {(name, type): DNSRecord}
        self.cache: Dict[Tuple[str, str], DNSRecord] = {}
        self.query_count = 0

        # 模擬権威サーバーのゾーンデータ
        self.zone_data: Dict[str, List[DNSRecord]] = {
            "example.com": [
                DNSRecord("example.com", "A", "93.184.216.34", ttl=3600),
                DNSRecord("example.com", "AAAA", "2606:2800:220:1::", ttl=3600),
                DNSRecord("example.com", "NS", "ns1.example.com", ttl=86400),
                DNSRecord("example.com", "MX", "mail.example.com", ttl=3600, priority=10),
                DNSRecord("example.com", "TXT", "v=spf1 include:_spf.google.com ~all", ttl=300),
                DNSRecord("example.com", "SOA",
                          "ns1.example.com admin.example.com 2024010101 3600 900 604800 86400",
                          ttl=86400),
            ],
            "www.example.com": [
                DNSRecord("www.example.com", "CNAME", "example.com", ttl=300),
            ],
            "api.example.com": [
                DNSRecord("api.example.com", "A", "93.184.216.35", ttl=60),
                DNSRecord("api.example.com", "A", "93.184.216.36", ttl=60),
                DNSRecord("api.example.com", "A", "93.184.216.37", ttl=60),
            ],
        }

    def resolve(self, name: str, record_type: str = "A") -> List[DNSRecord]:
        """DNS名前解決 (キャッシュ付き)"""
        self.query_count += 1
        cache_key = (name, record_type)

        # キャッシュチェック
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if not cached.is_expired():
                print(f"    [CACHE HIT] {name} {record_type} → {cached.value} "
                      f"(TTL残: {cached.remaining_ttl()}s)")
                return [cached]
            else:
                print(f"    [CACHE EXPIRED] {name} {record_type}")
                del self.cache[cache_key]

        # 反復クエリシミュレーション
        print(f"    [QUERY] {name} {record_type}")
        results = self._iterative_query(name, record_type)

        # キャッシュ保存
        for record in results:
            self.cache[(record.name, record.record_type)] = record

        return results

    def _iterative_query(self, name: str, record_type: str) -> List[DNSRecord]:
        """反復的クエリ シミュレーション

        クライアント → ローカルリゾルバ → ルートDNS → TLD DNS → 権威DNS
        """
        print(f"      1. ルートDNS (.): '{name}' → .com TLDサーバーへ")
        print(f"      2. TLD DNS (.com): '{name}' → 権威DNSサーバーへ")

        # ゾーンデータ検索
        if name in self.zone_data:
            records = [r for r in self.zone_data[name] if r.record_type == record_type]
            if records:
                # CNAME解決
                if records[0].record_type == "CNAME" and record_type == "A":
                    print(f"      3. 権威DNS: CNAME → {records[0].value}")
                    return self.resolve(records[0].value, "A")
                print(f"      3. 権威DNS: {name} → {[r.value for r in records]}")
                return records

        print(f"      3. 権威DNS: NXDOMAIN (見つからない)")
        return []

    def simulate_dns_queries(self):
        """DNSクエリのデモ"""
        print("=== DNS 名前解決 シミュレーション ===\n")

        # レコードタイプ一覧
        print("  DNSレコードタイプ:")
        for rt, desc in self.RECORD_TYPES.items():
            print(f"    {rt:6s}: {desc}")
        print()

        # 各種クエリ
        print("  --- Aレコード解決 ---")
        self.resolve("example.com", "A")
        print()

        print("  --- CNAME経由の解決 ---")
        self.resolve("www.example.com", "A")
        print()

        print("  --- キャッシュヒット ---")
        self.resolve("example.com", "A")
        print()

        print("  --- MXレコード ---")
        self.resolve("example.com", "MX")
        print()

        print(f"  総クエリ数: {self.query_count}")


class DNSLoadBalancer:
    """DNSベース ロードバランシング"""

    def __init__(self):
        self.servers = [
            {"ip": "10.0.1.1", "weight": 5, "region": "ap-northeast-1"},
            {"ip": "10.0.1.2", "weight": 3, "region": "ap-northeast-1"},
            {"ip": "10.0.2.1", "weight": 4, "region": "us-east-1"},
            {"ip": "10.0.3.1", "weight": 2, "region": "eu-west-1"},
        ]
        self.rr_index = 0

    def round_robin(self) -> str:
        """ラウンドロビンDNS"""
        ip = self.servers[self.rr_index % len(self.servers)]["ip"]
        self.rr_index += 1
        return ip

    def weighted(self) -> str:
        """重み付きDNS"""
        total = sum(s["weight"] for s in self.servers)
        r = random.randint(1, total)
        cumulative = 0
        for s in self.servers:
            cumulative += s["weight"]
            if r <= cumulative:
                return s["ip"]
        return self.servers[-1]["ip"]

    def geolocation(self, client_region: str) -> str:
        """地理的DNS (最寄りリージョン)"""
        # 同リージョン優先
        same_region = [s for s in self.servers if s["region"] == client_region]
        if same_region:
            return random.choice(same_region)["ip"]
        return self.round_robin()

    def demo(self):
        print("=== DNS ロードバランシング ===\n")
        print("  Round Robin:")
        for i in range(6):
            print(f"    Request {i+1} → {self.round_robin()}")

        print("\n  Weighted (5:3:4:2):")
        counts = defaultdict(int)
        for _ in range(1000):
            counts[self.weighted()] += 1
        for ip, count in sorted(counts.items()):
            bar = "#" * (count // 20)
            print(f"    {ip}: {count:4d} ({count/10:.1f}%) {bar}")

        print("\n  Geolocation:")
        for region in ["ap-northeast-1", "us-east-1", "eu-west-1", "sa-east-1"]:
            ip = self.geolocation(region)
            print(f"    Client@{region:16s} → {ip}")

    @staticmethod
    def explain_dns_security():
        """DNSセキュリティ解説"""
        print("\n=== DNS Security ===")
        print("""
  【DNSSEC (DNS Security Extensions)】
  - DNS応答にデジタル署名を付与
  - レコード改ざん検出 (DNS Spoofing対策)
  - 信頼の連鎖: ルート → TLD → 権威サーバー
  - RRSIG, DNSKEY, DS レコードを使用

  【DNS over HTTPS (DoH)】
  - DNS クエリを HTTPS で暗号化
  - ポート443 (通常のHTTPSと同じ → ブロック困難)
  - プライバシー保護 (ISPによる監視防止)

  【DNS over TLS (DoT)】
  - DNS クエリを TLS で暗号化
  - ポート853 (専用ポート → ファイアウォールで制御可能)

  【攻撃と対策】
  - DNS Cache Poisoning → DNSSEC
  - DNS Amplification DDoS → Response Rate Limiting
  - DNS Tunneling → クエリ監視・異常検知
""")


# ============================================================
# 4. CDN (Content Delivery Network)
# ============================================================

class CDNSimulator:
    """CDN動作シミュレーション"""

    def __init__(self):
        self.edge_cache: Dict[str, Dict] = {}  # エッジキャッシュ
        self.origin_shield_cache: Dict[str, Dict] = {}  # Origin Shield
        self.origin_requests = 0
        self.shield_requests = 0
        self.edge_requests = 0

    def request(self, url: str, edge_location: str = "tokyo") -> str:
        """CDNリクエスト処理フロー"""
        self.edge_requests += 1
        cache_key = f"{edge_location}:{url}"

        # 1. エッジキャッシュチェック
        if cache_key in self.edge_cache:
            entry = self.edge_cache[cache_key]
            if entry["expires"] > time.time():
                return f"EDGE HIT ({edge_location})"

        # 2. Origin Shield チェック
        self.shield_requests += 1
        if url in self.origin_shield_cache:
            entry = self.origin_shield_cache[url]
            if entry["expires"] > time.time():
                # エッジに伝搬
                self.edge_cache[cache_key] = {
                    "content": entry["content"],
                    "expires": time.time() + 60
                }
                return f"SHIELD HIT → edge cached"

        # 3. オリジンサーバーへ
        self.origin_requests += 1
        content = f"content_of_{url}"
        now = time.time()
        self.origin_shield_cache[url] = {"content": content, "expires": now + 300}
        self.edge_cache[cache_key] = {"content": content, "expires": now + 60}
        return "ORIGIN FETCH → shield + edge cached"

    def demo(self):
        print("=== CDN シミュレーション ===\n")

        # Push vs Pull
        print("  【Push CDN vs Pull CDN】")
        print("  Push: コンテンツ更新時にオリジンからエッジに配信 (静的サイト向き)")
        print("  Pull: 初回リクエスト時にオリジンからフェッチ (動的コンテンツ向き)\n")

        # リクエストシミュレーション
        urls = ["/index.html", "/api/data", "/images/logo.png", "/index.html"]
        locations = ["tokyo", "tokyo", "osaka", "tokyo"]

        for url, loc in zip(urls, locations):
            result = self.request(url, loc)
            print(f"  {loc:6s} GET {url:20s} → {result}")

        print(f"\n  統計: Edge={self.edge_requests} "
              f"Shield={self.shield_requests} Origin={self.origin_requests}")

        # Cache Invalidation
        print("\n  【Cache Invalidation 戦略】")
        strategies = [
            ("TTL-based",       "一定時間後に自動失効 (Cache-Control: max-age=3600)",
             "シンプル / 更新反映が遅い"),
            ("Purge",           "APIで明示的にキャッシュ削除 (POST /purge)",
             "即時反映 / 全エッジに伝搬必要"),
            ("Versioned URL",   "/app.abc123.js (ハッシュ付きURL)",
             "確実 / ビルドパイプライン必要"),
            ("Stale-While-Rev", "古いキャッシュを返しつつバックグラウンド更新",
             "高速 / 一瞬古いデータ"),
        ]
        print(f"  {'戦略':18s} | {'説明':44s} | {'特徴'}")
        print(f"  {'-'*18}-+-{'-'*44}-+-{'-'*30}")
        for name, desc, note in strategies:
            print(f"  {name:18s} | {desc:44s} | {note}")

        # Origin Shield
        print("\n  【Origin Shield パターン】")
        print("  Client → Edge POP → Origin Shield → Origin Server")
        print("  - 複数エッジからの同一リクエストをShieldが集約")
        print("  - オリジンへの負荷を大幅削減 (Thunder Herd 防止)")

        # CDN選定
        print("\n  【CDN選定 比較】")
        cdns = [
            ("CloudFront", "AWS統合, Lambda@Edge, S3連携",        "AWS利用者"),
            ("Cloudflare", "無料プランあり, Workers, DDoS防御",    "汎用・コスパ重視"),
            ("Fastly",     "リアルタイムPurge, VCL/Wasm, 高速",   "動的コンテンツ"),
        ]
        for name, features, fit in cdns:
            print(f"  {name:12s}: {features:42s} 適: {fit}")

        # Edge Computing
        print("\n  【Edge Computing】")
        print("  CDNエッジでロジック実行 (API応答, A/Bテスト, 認証)")
        print("  例: Cloudflare Workers, Lambda@Edge, Fastly Compute")


# ============================================================
# 5. WebSocket & リアルタイム通信
# ============================================================

class WebSocketSimulator:
    """WebSocket プロトコル シミュレーション"""

    @staticmethod
    def handshake_demo():
        """WebSocket ハンドシェイク (HTTP Upgrade)"""
        print("=== WebSocket Handshake ===\n")

        # クライアントリクエスト
        ws_key = "dGhlIHNhbXBsZSBub25jZQ=="  # Base64エンコードされた16Bランダム値
        print("  Client → Server:")
        print(f"    GET /chat HTTP/1.1")
        print(f"    Host: example.com")
        print(f"    Upgrade: websocket")
        print(f"    Connection: Upgrade")
        print(f"    Sec-WebSocket-Key: {ws_key}")
        print(f"    Sec-WebSocket-Version: 13\n")

        # サーバーレスポンス (101 Switching Protocols)
        magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        accept = hashlib.sha1((ws_key + magic).encode()).digest()
        import base64
        accept_b64 = base64.b64encode(accept).decode()
        print("  Server → Client:")
        print(f"    HTTP/1.1 101 Switching Protocols")
        print(f"    Upgrade: websocket")
        print(f"    Connection: Upgrade")
        print(f"    Sec-WebSocket-Accept: {accept_b64}\n")
        print("  → WebSocket接続確立 (以降はフレームベース通信)")

    @staticmethod
    def frame_format():
        """WebSocket フレームフォーマット"""
        print("\n=== WebSocket Frame Format ===")
        print("""
   0                   1                   2                   3
   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
  |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
  |N|V|V|V|       |S|             |   (if payload len==126/127)   |
  | |1|2|3|       |K|             |                               |
  +-+-+-+-+-------+-+-------------+-------------------------------+
  |     Masking-key (if MASK=1)   |          Payload Data         |
  +-------------------------------+-------------------------------+

  Opcode: 0x1=Text, 0x2=Binary, 0x8=Close, 0x9=Ping, 0xA=Pong
  MASK:   クライアント→サーバーは必須 (プロキシキャッシュ汚染防止)
  FIN:    最終フレームフラグ (大きなメッセージは分割送信)
""")

    @staticmethod
    def compare_realtime():
        """リアルタイム通信方式の比較"""
        print("=== リアルタイム通信方式 比較 ===")
        rows = [
            ("項目",         "Long Polling",          "SSE",                   "WebSocket"),
            ("プロトコル",   "HTTP",                  "HTTP",                  "WS (HTTP Upgrade)"),
            ("方向",         "擬似双方向",            "サーバー→クライアント", "全二重双方向"),
            ("接続",         "繰り返しHTTPリクエスト", "1つの持続接続",         "1つの持続接続"),
            ("オーバーヘッド","高い(毎回ヘッダ)",      "中(HTTPヘッダ1回)",      "低い(2-14Bフレーム)"),
            ("ブラウザ対応", "全て",                  "IE以外",                "全モダンブラウザ"),
            ("再接続",       "自動(次のリクエスト)",   "EventSource自動再接続", "手動実装必要"),
            ("適用例",       "チャット(レガシー)",     "通知・フィード",        "ゲーム・チャット・取引"),
        ]
        widths = [14, 24, 24, 24]
        for row in rows:
            print("  " + " | ".join(f"{v:{w}s}" for v, w in zip(row, widths)))
            if row == rows[0]:
                print("  " + "-+-".join("-" * w for w in widths))


class PubSubWebSocket:
    """WebSocket上のPub/Subパターン シミュレーション"""

    def __init__(self):
        self.topics: Dict[str, List[str]] = defaultdict(list)  # topic → [client_ids]
        self.messages: List[Dict] = []

    def subscribe(self, client_id: str, topic: str):
        self.topics[topic].append(client_id)
        print(f"  [{client_id}] subscribed to '{topic}'")

    def publish(self, topic: str, message: str, sender: str = "server"):
        subscribers = self.topics.get(topic, [])
        print(f"  [{sender}] publish to '{topic}': {message}")
        for client_id in subscribers:
            print(f"    → delivered to [{client_id}]")
        self.messages.append({"topic": topic, "message": message, "to": subscribers})

    def demo(self):
        print("\n=== Pub/Sub on WebSocket ===\n")
        self.subscribe("user-1", "chat/room-1")
        self.subscribe("user-2", "chat/room-1")
        self.subscribe("user-1", "notifications")
        self.subscribe("user-3", "notifications")
        print()
        self.publish("chat/room-1", "Hello everyone!", "user-1")
        self.publish("notifications", "New update available", "system")


# ============================================================
# 6. gRPC & Protocol Buffers
# ============================================================

class GRPCSimulator:
    """gRPC & Protocol Buffers の概念とシミュレーション"""

    @staticmethod
    def protobuf_encoding():
        """Protobuf エンコーディング解説"""
        print("=== Protocol Buffers エンコーディング ===\n")

        # Varint エンコーディング
        print("  【Varint (可変長整数)】")
        values = [1, 127, 128, 300, 16384]
        for v in values:
            encoded = GRPCSimulator._encode_varint(v)
            print(f"    {v:6d} → {' '.join(f'{b:08b}' for b in encoded)} "
                  f"({len(encoded)} bytes)")

        # フィールドタグ
        print("\n  【Field Tag = (field_number << 3) | wire_type】")
        wire_types = {
            0: "Varint (int32, bool, enum)",
            1: "64-bit (double, fixed64)",
            2: "Length-delimited (string, bytes, embedded msg)",
            5: "32-bit (float, fixed32)",
        }
        for wt, desc in wire_types.items():
            print(f"    wire_type={wt}: {desc}")

        # JSON vs Protobuf サイズ比較
        print("\n  【JSON vs Protobuf サイズ比較】")
        json_example = '{"id":12345,"name":"Alice","email":"alice@example.com","age":30}'
        json_size = len(json_example)
        proto_size = 2 + 2 + 2 + 5 + 2 + 17 + 2 + 1  # 概算
        print(f"    JSON:     {json_size} bytes  '{json_example}'")
        print(f"    Protobuf: ~{proto_size} bytes  (バイナリ)")
        print(f"    → {int((1 - proto_size/json_size) * 100)}% サイズ削減")

    @staticmethod
    def _encode_varint(value: int) -> bytes:
        """Varint エンコード"""
        result = []
        while value > 127:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)

    @staticmethod
    def communication_patterns():
        """gRPC の4通信パターン"""
        print("\n=== gRPC 通信パターン ===\n")
        patterns = [
            ("1. Unary RPC",
             "Client --req--> Server --res--> Client",
             "通常のリクエスト/レスポンス (REST相当)",
             "GetUser(UserRequest) returns (User)"),
            ("2. Server Streaming",
             "Client --req--> Server ==res==> Client (複数)",
             "サーバーが複数レスポンスをストリーム送信",
             "ListUsers(Filter) returns (stream User)"),
            ("3. Client Streaming",
             "Client ==req==> Server (複数) --res--> Client",
             "クライアントが複数リクエストをストリーム送信",
             "UploadChunks(stream Chunk) returns (Status)"),
            ("4. Bidirectional Streaming",
             "Client <=====req/res=====> Server",
             "双方向で同時にストリーム通信",
             "Chat(stream Msg) returns (stream Msg)"),
        ]
        for name, diagram, desc, proto in patterns:
            print(f"  {name}")
            print(f"    {diagram}")
            print(f"    説明: {desc}")
            print(f"    Proto: rpc {proto}")
            print()

    @staticmethod
    def grpc_vs_rest():
        """gRPC vs REST 比較表"""
        print("=== gRPC vs REST 比較 ===")
        rows = [
            ("プロトコル",   "HTTP/2",               "HTTP/1.1 or HTTP/2"),
            ("データ形式",   "Protocol Buffers",     "JSON (テキスト)"),
            ("スキーマ",     ".proto (厳密型)",       "OpenAPI (任意)"),
            ("コード生成",   "自動 (多言語対応)",     "手動 or ツール"),
            ("ストリーミング","4パターン対応",         "限定的 (SSE等)"),
            ("ブラウザ",     "gRPC-Web必要",          "ネイティブ対応"),
            ("デバッグ",     "難 (バイナリ)",         "容易 (テキスト)"),
            ("パフォーマンス","高速 (小サイズ, 多重化)","中速"),
            ("適用場面",     "マイクロサービス間通信", "公開API・Web/モバイル"),
        ]
        print(f"  {'項目':16s} | {'gRPC':24s} | {'REST':24s}")
        print(f"  {'-'*16}-+-{'-'*24}-+-{'-'*24}")
        for item, grpc, rest in rows:
            print(f"  {item:16s} | {grpc:24s} | {rest:24s}")

        print("\n  【gRPC-Web】")
        print("  ブラウザから直接gRPCを呼べない → gRPC-Webプロキシ経由")
        print("  Envoy, grpc-web (npm) で対応")
        print("\n  【gRPC Gateway】")
        print("  gRPCサービスにRESTful APIエンドポイントを自動生成")
        print("  .protoにHTTPアノテーション追加 → REST→gRPC変換プロキシ")


# ============================================================
# 7. ロードバランシング詳細
# ============================================================

@dataclass
class Server:
    """バックエンドサーバー"""
    address: str
    weight: int = 1
    connections: int = 0
    healthy: bool = True


class LoadBalancer:
    """ロードバランサー実装 (複数アルゴリズム)"""

    def __init__(self, servers: List[Server]):
        self.servers = servers
        self.rr_index = 0
        self.wrr_index = 0
        self.wrr_current_weight = 0
        # Consistent Hashing
        self.ring: List[Tuple[int, str]] = []
        self._build_ring(replicas=100)

    def _healthy_servers(self) -> List[Server]:
        return [s for s in self.servers if s.healthy]

    # --- Round Robin ---
    def round_robin(self) -> Optional[str]:
        healthy = self._healthy_servers()
        if not healthy:
            return None
        server = healthy[self.rr_index % len(healthy)]
        self.rr_index += 1
        return server.address

    # --- Weighted Round Robin ---
    def weighted_round_robin(self) -> Optional[str]:
        healthy = self._healthy_servers()
        if not healthy:
            return None
        total = sum(s.weight for s in healthy)
        self.wrr_current_weight += 1
        if self.wrr_current_weight > total:
            self.wrr_current_weight = 1
        cumulative = 0
        for s in healthy:
            cumulative += s.weight
            if self.wrr_current_weight <= cumulative:
                return s.address
        return healthy[-1].address

    # --- Least Connections ---
    def least_connections(self) -> Optional[str]:
        healthy = self._healthy_servers()
        if not healthy:
            return None
        server = min(healthy, key=lambda s: s.connections)
        server.connections += 1
        return server.address

    # --- IP Hash ---
    def ip_hash(self, client_ip: str) -> Optional[str]:
        healthy = self._healthy_servers()
        if not healthy:
            return None
        h = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        return healthy[h % len(healthy)].address

    # --- Consistent Hashing ---
    def _build_ring(self, replicas: int = 100):
        """コンシステントハッシュリング構築"""
        self.ring = []
        for server in self.servers:
            for i in range(replicas):
                key = f"{server.address}:{i}"
                h = int(hashlib.md5(key.encode()).hexdigest(), 16)
                self.ring.append((h, server.address))
        self.ring.sort(key=lambda x: x[0])

    def consistent_hash(self, key: str) -> Optional[str]:
        """コンシステントハッシュでサーバー選択"""
        if not self.ring:
            return None
        h = int(hashlib.md5(key.encode()).hexdigest(), 16)
        # 時計回りで最初に見つかるノード
        for ring_hash, address in self.ring:
            if ring_hash >= h:
                server = next((s for s in self.servers
                               if s.address == address and s.healthy), None)
                if server:
                    return server.address
        # ラップアラウンド
        return self.ring[0][1]

    def demo(self):
        print("=== ロードバランシング アルゴリズム ===\n")

        # L4 vs L7
        print("  【L4 (Transport) vs L7 (Application) ロードバランサー】")
        print(f"  {'':4s}{'L4 (TCP/UDP)':30s} {'L7 (HTTP/HTTPS)':30s}")
        print(f"  {'':4s}{'-'*30} {'-'*30}")
        l4l7 = [
            ("判断基準", "IP, ポート, TCP情報",      "URL, ヘッダ, Cookie, Body"),
            ("速度",     "高速 (パケット転送のみ)",   "中速 (HTTPパース必要)"),
            ("機能",     "シンプルな振り分け",        "パスルーティング, SSL終端"),
            ("例",       "NLB, HAProxy (TCP)",       "ALB, Nginx, Envoy"),
        ]
        for item, l4, l7 in l4l7:
            print(f"  {'':4s}{item:10s} {l4:30s} {l7:30s}")

        # 各アルゴリズムのデモ
        print("\n  --- Round Robin ---")
        for i in range(6):
            print(f"    Request {i+1} → {self.round_robin()}")

        print("\n  --- Least Connections ---")
        # コネクション数をリセット
        for s in self.servers:
            s.connections = random.randint(0, 5)
        print(f"    現在の接続数: {[(s.address, s.connections) for s in self.servers]}")
        for i in range(4):
            addr = self.least_connections()
            print(f"    Request {i+1} → {addr}")

        print("\n  --- IP Hash (セッション維持) ---")
        client_ips = ["192.168.1.1", "192.168.1.2", "192.168.1.1", "10.0.0.1"]
        for ip in client_ips:
            print(f"    {ip} → {self.ip_hash(ip)}")

        print("\n  --- Consistent Hashing ---")
        keys = ["user:1001", "user:1002", "user:1003", "session:abc"]
        for key in keys:
            print(f"    {key} → {self.consistent_hash(key)}")
        # サーバー障害時の影響範囲
        print("    [サーバーB障害発生]")
        self.servers[1].healthy = False
        self._build_ring()
        for key in keys:
            print(f"    {key} → {self.consistent_hash(key)} "
                  f"{'(再配置)' if 'B' in key else ''}")
        self.servers[1].healthy = True
        self._build_ring()

        # Health Check
        print("\n  【Health Check】")
        print("  Active: LBがサーバーに定期的にプローブ送信 (HTTP GET /health)")
        print("  Passive: 実トラフィックの応答を監視 (5xx連続 → unhealthy)")
        print("  → 両方組み合わせが推奨")

        # Connection Draining
        print("\n  【Connection Draining (Graceful Shutdown)】")
        print("  1. サーバーをunhealthyにマーク (新規リクエスト停止)")
        print("  2. 既存接続の完了を待つ (タイムアウト付き)")
        print("  3. 全接続完了後にサーバー停止")
        print("  → デプロイ/スケールイン時のリクエスト断を防止")

        # Service Discovery
        print("\n  【Service Discovery】")
        print("  Client-side: クライアントがレジストリ問合せ → 直接接続")
        print("    例: Netflix Eureka, Consul (クライアントライブラリ)")
        print("  Server-side: LB/プロキシがレジストリ問合せ → 転送")
        print("    例: AWS ALB + ECS, Kubernetes Service")


# ============================================================
# 8. TLS/SSL Deep Dive
# ============================================================

class TLSExplainer:
    """TLS/SSL 詳細解説"""

    @staticmethod
    def tls13_handshake():
        """TLS 1.3 ハンドシェイク"""
        print("=== TLS 1.3 Handshake ===\n")
        print("""
  【1-RTT Handshake (初回接続)】
  Client                              Server
    |                                    |
    |--- ClientHello ------------------->|  鍵共有パラメータ含む
    |    (Supported Ciphers,             |  (TLS 1.2は2-RTT必要だった)
    |     Key Share,                     |
    |     Supported Groups)              |
    |                                    |
    |<-- ServerHello + EncryptedExt -----|  以降は暗号化
    |    Certificate                     |
    |    CertificateVerify               |
    |    Finished                        |
    |                                    |
    |--- Finished --------------------->|
    |                                    |
    |<========= 暗号化通信 ==========>|
    |            (1 RTT)                 |

  【0-RTT (再接続 / Early Data)】
  - 前回のセッション鍵 (PSK) を使って即データ送信
  - リスク: リプレイ攻撃の可能性 (冪等なリクエストのみ推奨)

  【TLS 1.3 の改善点】
  - 暗号スイート簡素化 (安全でないもの除去: RC4, SHA-1, CBC等)
  - 前方秘匿性 (Forward Secrecy) 必須: ECDHE のみ
  - ハンドシェイク暗号化 (Certificate を暗号化して送信)
  - 0-RTT 再接続サポート
""")

    @staticmethod
    def certificate_chain():
        """証明書チェーン検証"""
        print("=== Certificate Chain 検証 ===\n")
        chain = [
            ("サーバー証明書",       "example.com",               "中間CA発行"),
            ("中間CA証明書",         "DigiCert SHA2 Secure CA",   "ルートCA発行"),
            ("ルートCA証明書",       "DigiCert Global Root G2",   "自己署名 (信頼ストア)"),
        ]
        for i, (cert_type, cn, issuer) in enumerate(chain):
            indent = "  " * (i + 1)
            arrow = "└─" if i > 0 else "──"
            print(f"{indent}{arrow} [{cert_type}]")
            print(f"{indent}   CN: {cn}")
            print(f"{indent}   発行者: {issuer}")

        print("""
  検証プロセス:
  1. サーバー証明書の署名を中間CAの公開鍵で検証
  2. 中間CA証明書の署名をルートCAの公開鍵で検証
  3. ルートCA証明書がOSの信頼ストアに存在するか確認
  4. 有効期限・失効状態 (OCSP/CRL) チェック
  5. ドメイン名一致確認 (CN or SAN)
""")

    @staticmethod
    def mtls():
        """相互TLS (mTLS) 解説"""
        print("=== mTLS (相互TLS認証) ===")
        print("""
  通常のTLS: サーバーのみ証明書を提示
  mTLS:      サーバー + クライアントの双方が証明書を提示

  Client                              Server
    |--- ClientHello ------------------>|
    |<-- ServerHello + Certificate -----|
    |<-- CertificateRequest ------------|  ← サーバーがクライアント証明書を要求
    |--- Certificate (client) --------->|  ← クライアントも証明書を提示
    |--- CertificateVerify ------------>|
    |--- Finished --------------------->|
    |<-- Finished ----------------------|

  【用途】
  - マイクロサービス間認証 (Service Mesh: Istio, Linkerd)
  - ゼロトラストアーキテクチャ
  - IoTデバイス認証
  - API認証 (クライアント証明書ベース)

  【Certificate Pinning】
  - 特定の証明書/公開鍵のみを信頼する
  - CA侵害時の中間者攻撃を防止
  - リスク: 証明書ローテーション時の更新が必要
  - 方式: 公開鍵ピン留め (HPKP, アプリ内埋め込み)
""")


# ============================================================
# 9. 優先度 (Tier)
# ============================================================

def print_priority_tiers():
    """学習優先度ガイド"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          ネットワーク & プロトコル 学習優先度                   ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                ║
║  【Tier 1: 必須 (全エンジニア)】                               ║
║  ・TCP/UDP の基礎 (3-Way HS, 信頼性, フロー制御)              ║
║  ・HTTP/1.1 → HTTP/2 の違い (Keep-Alive, 多重化)             ║
║  ・DNS の仕組み (名前解決, レコードタイプ)                     ║
║  ・TLS/SSL の基礎 (HTTPS, 証明書チェーン)                     ║
║  ・ロードバランシング基礎 (L4/L7, Round Robin)                ║
║                                                                ║
║  【Tier 2: 重要 (バックエンド/インフラ)】                      ║
║  ・TCP 輻輳制御 (Slow Start, Congestion Avoidance)            ║
║  ・CDN (キャッシュ戦略, Origin Shield)                        ║
║  ・WebSocket (リアルタイム通信)                                ║
║  ・ロードバランシング応用 (Consistent Hashing, Health Check)  ║
║  ・TLS 1.3 ハンドシェイク詳細                                  ║
║                                                                ║
║  【Tier 3: 実践的 (アーキテクト/SRE)】                        ║
║  ・HTTP/3 (QUIC) の利点と採用判断                              ║
║  ・gRPC & Protocol Buffers                                     ║
║  ・mTLS (ゼロトラスト, Service Mesh)                           ║
║  ・DNS セキュリティ (DNSSEC, DoH/DoT)                         ║
║  ・Connection Draining, Service Discovery                      ║
║                                                                ║
║  【Tier 4: 専門知識 (ネットワークスペシャリスト)】             ║
║  ・TCP 内部実装 (Nagle, Delayed ACK, Sliding Window詳細)      ║
║  ・Protobuf エンコーディング (Varint, Wire Type)              ║
║  ・Certificate Pinning                                         ║
║  ・Edge Computing 詳細                                         ║
║  ・QUIC プロトコル内部構造                                     ║
║                                                                ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ============================================================
# メイン実行
# ============================================================

def main():
    print("=" * 64)
    print("  ネットワーク & プロトコル 完全ガイド")
    print("  TCP, HTTP, DNS, CDN, WebSocket, gRPC, LB, TLS")
    print("=" * 64)

    # --- 1. TCP Deep Internals ---
    print("\n" + "=" * 64)
    print("  SECTION 1: TCP Deep Internals")
    print("=" * 64)
    simulate_three_way_handshake()

    sw = SlidingWindowProtocol(window_size=4)
    sw.send(["A", "B", "C", "D", "E", "F", "G", "H"])

    cc = CongestionControl()
    cc.simulate(rounds=20)
    CongestionControl.print_comparison()
    CongestionControl.explain_nagle_delayed_ack()

    # --- 2. HTTP Evolution ---
    print("\n" + "=" * 64)
    print("  SECTION 2: HTTP プロトコル進化")
    print("=" * 64)
    HTTPEvolution.http11_simulation()
    HTTPEvolution.http2_simulation()
    HTTPEvolution.http3_quic()
    HTTPEvolution.performance_comparison()

    # --- 3. DNS ---
    print("\n" + "=" * 64)
    print("  SECTION 3: DNS 完全解説")
    print("=" * 64)
    resolver = DNSResolver()
    resolver.simulate_dns_queries()

    dns_lb = DNSLoadBalancer()
    dns_lb.demo()
    DNSLoadBalancer.explain_dns_security()

    # --- 4. CDN ---
    print("\n" + "=" * 64)
    print("  SECTION 4: CDN")
    print("=" * 64)
    cdn = CDNSimulator()
    cdn.demo()

    # --- 5. WebSocket ---
    print("\n" + "=" * 64)
    print("  SECTION 5: WebSocket & リアルタイム通信")
    print("=" * 64)
    WebSocketSimulator.handshake_demo()
    WebSocketSimulator.frame_format()
    WebSocketSimulator.compare_realtime()
    pubsub = PubSubWebSocket()
    pubsub.demo()

    # --- 6. gRPC ---
    print("\n" + "=" * 64)
    print("  SECTION 6: gRPC & Protocol Buffers")
    print("=" * 64)
    GRPCSimulator.protobuf_encoding()
    GRPCSimulator.communication_patterns()
    GRPCSimulator.grpc_vs_rest()

    # --- 7. Load Balancing ---
    print("\n" + "=" * 64)
    print("  SECTION 7: ロードバランシング詳細")
    print("=" * 64)
    servers = [
        Server("server-A", weight=5),
        Server("server-B", weight=3),
        Server("server-C", weight=2),
    ]
    lb = LoadBalancer(servers)
    lb.demo()

    # --- 8. TLS/SSL ---
    print("\n" + "=" * 64)
    print("  SECTION 8: TLS/SSL Deep Dive")
    print("=" * 64)
    TLSExplainer.tls13_handshake()
    TLSExplainer.certificate_chain()
    TLSExplainer.mtls()

    # --- 9. Priority ---
    print_priority_tiers()

    print("\n完了: 全セクション実行済み")


if __name__ == "__main__":
    main()
