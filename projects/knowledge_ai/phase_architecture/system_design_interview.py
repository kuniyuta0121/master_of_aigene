#!/usr/bin/env python3
"""
phase_architecture/system_design_interview.py
=============================================
FAANG システム設計面接 完全ウォークスルーガイド

「45分で大規模システムを設計せよ」——
FAANG のシニアエンジニア面接で最も配点が高い System Design Round。
このファイルでは、面接の解き方フレームワーク（Step 1-5）を確立し、
頻出10大設計問題を実際に解き、分散システムの Building Blocks を整理する。

実行方法:
    python system_design_interview.py  (標準ライブラリのみ)

考えてほしい疑問:
  Q1. 面接で最初の5分をどう使うかで合否が決まるのはなぜか？
  Q2. 「要件を確認する質問」を投げることが評価に直結する理由は？
  Q3. CAP 定理は実際の設計判断にどう影響するか？
  Q4. Consistent Hashing の仮想ノード数は何を基準に決める？
  Q5. Fan-out on Write と Fan-out on Read のハイブリッド戦略はどう設計する？
  Q6. Rate Limiter を分散環境で動かすとき、Redis 以外の選択肢は？
  Q7. 動画トランスコードの DAG パイプラインで障害が起きたらどうリトライする？
  Q8. 検索オートコンプリートで Trie のメモリが爆発したらどう対処する？
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import random
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple


# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  ── {title} ──")
    print()


def point(text: str) -> None:
    print(f"    > {text}")


def demo(label: str, value: Any) -> None:
    print(f"    {label}: {value}")


def question(text: str) -> None:
    print(f"  [考えてほしい疑問] {text}")
    print()


def diagram(lines: List[str]) -> None:
    """ASCII アートを表示"""
    for line in lines:
        print(f"    {line}")
    print()


# ============================================================
# PART 1: 面接の解き方フレームワーク (Step 1-5)
# ============================================================

def explain_framework():
    section("PART 1: System Design 面接フレームワーク (Step 1-5)")

    # ---- Step 1 ----
    subsection("Step 1: 要件整理 (Requirements Clarification) — 最初の5分")
    point("面接官に質問を投げることが最も重要。黙って設計を始めない。")
    point("Functional Requirements: ユーザーが何をできるか")
    point("Non-Functional Requirements: スケール・可用性・レイテンシ・一貫性")
    point("規模見積もり: DAU → QPS → Storage → Bandwidth")
    print()
    print("    例 (URL Shortener の場合):")
    print("    ┌─────────────────────────────────────────────────┐")
    print("    │ Functional:                                     │")
    print("    │   - 長いURLを短縮URLに変換                        │")
    print("    │   - 短縮URLにアクセスすると元URLにリダイレクト      │")
    print("    │   - カスタムエイリアス (optional)                  │")
    print("    │   - Analytics (optional)                         │")
    print("    │ Non-Functional:                                  │")
    print("    │   - 高可用性 (99.99%)                             │")
    print("    │   - 低レイテンシ (< 100ms リダイレクト)            │")
    print("    │   - 短縮URLは一意で予測不能                       │")
    print("    └─────────────────────────────────────────────────┘")
    print()

    # ---- Step 2 ----
    subsection("Step 2: API 設計 — 次の3分")
    point("REST or GraphQL のエンドポイントを定義")
    point("パラメータ・レスポンスを明示")
    point("Rate Limiting のヘッダーにも言及するとボーナス")
    print()
    print("    POST /api/v1/urls")
    print("      Body: { \"long_url\": \"...\", \"custom_alias\": \"...\", \"expiry\": \"...\" }")
    print("      Response: { \"short_url\": \"https://tny.im/abc123\" }")
    print()
    print("    GET /{short_code}")
    print("      Response: 301 Redirect (永続) or 302 (一時)")
    print()

    # ---- Step 3 ----
    subsection("Step 3: High-Level Design — 10分")
    point("主要コンポーネントをブロック図で描く")
    point("データフロー（書き込み/読み取り）を矢印で示す")
    diagram([
        "┌────────┐    ┌─────────────┐    ┌──────────┐",
        "│ Client │───>│ API Gateway │───>│ App      │",
        "│        │<───│ + LB        │<───│ Server   │",
        "└────────┘    └─────────────┘    └────┬─────┘",
        "                                      │",
        "                          ┌───────────┼───────────┐",
        "                          │           │           │",
        "                     ┌────▼───┐  ┌───▼────┐  ┌───▼───┐",
        "                     │ Cache  │  │  DB    │  │ Queue │",
        "                     │ (Redis)│  │(MySQL) │  │(Kafka)│",
        "                     └────────┘  └────────┘  └───────┘",
    ])

    # ---- Step 4 ----
    subsection("Step 4: Deep Dive — 20分")
    point("ボトルネックを特定して解決策を提示")
    point("スケーリング: 水平分割 (Sharding), レプリケーション, キャッシュ")
    point("データモデル: テーブル設計, インデックス")
    point("障害対策: レプリカ切替, サーキットブレーカー, リトライ")
    print()

    # ---- Step 5 ----
    subsection("Step 5: トレードオフ議論 — 最後の5分")
    point("正解は1つではない。複数案を比較して選択理由を述べる")
    point("CAP 定理のどこに立つか (CP vs AP)")
    point("一貫性 vs レイテンシ, コスト vs 可用性")
    point("「もし時間があれば○○も追加したい」で締めくくる")
    print()
    print("    ┌──────────────────┬──────────────────┬─────────────────┐")
    print("    │     観点         │    Option A      │    Option B     │")
    print("    ├──────────────────┼──────────────────┼─────────────────┤")
    print("    │ 一貫性           │ 強整合 (CP)      │ 結果整合 (AP)   │")
    print("    │ レイテンシ       │ 高 (同期書込)    │ 低 (非同期)     │")
    print("    │ 実装複雑度       │ 低               │ 中〜高          │")
    print("    │ 採用ケース       │ 決済, 在庫       │ SNS, フィード   │")
    print("    └──────────────────┴──────────────────┴─────────────────┘")
    print()


# ============================================================
# PART 2: 規模見積もり計算テンプレート (Back-of-Envelope)
# ============================================================

def estimate_scale(
    dau: int,
    avg_requests_per_user: int,
    data_size_per_request_bytes: int,
    read_write_ratio: float = 10.0,
    cache_hit_ratio: float = 0.8,
    years: int = 5,
    requests_per_server: int = 10_000,
) -> Dict[str, Any]:
    """
    規模見積もりを一括計算する。
    面接中にホワイトボードで素早く概算するための関数。

    Args:
        dau: Daily Active Users
        avg_requests_per_user: 1ユーザーあたりの1日リクエスト数
        data_size_per_request_bytes: 1リクエストで発生するデータ量 (bytes)
        read_write_ratio: 読み取り/書き込み比率 (例: 10 = 読み10:書き1)
        cache_hit_ratio: キャッシュヒット率 (80/20 ルール → 0.8)
        years: ストレージ見積もり期間
        requests_per_server: 1サーバーが捌ける QPS
    """
    # --- QPS ---
    total_daily_requests = dau * avg_requests_per_user
    avg_qps = total_daily_requests / 86400  # 1日 = 86400秒
    peak_qps = avg_qps * 2  # ピーク = 平均の2倍と仮定

    write_qps = avg_qps / (1 + read_write_ratio)
    read_qps = avg_qps - write_qps

    # --- ストレージ (5年分) ---
    daily_storage_bytes = total_daily_requests * data_size_per_request_bytes
    total_storage_bytes = daily_storage_bytes * 365 * years
    total_storage_tb = total_storage_bytes / (1024 ** 4)

    # --- 帯域幅 ---
    bandwidth_bps = avg_qps * data_size_per_request_bytes * 8  # bits per second
    bandwidth_mbps = bandwidth_bps / (10 ** 6)

    # --- キャッシュサイズ (80/20 ルール) ---
    # 1日のリクエストの20%が80%のトラフィックを生む
    # → 上位20%のデータをキャッシュ
    daily_cache_bytes = daily_storage_bytes * 0.2
    daily_cache_gb = daily_cache_bytes / (1024 ** 3)

    # --- サーバー台数 ---
    servers_needed = math.ceil(peak_qps / requests_per_server)

    return {
        "dau": dau,
        "total_daily_requests": total_daily_requests,
        "avg_qps": round(avg_qps, 1),
        "peak_qps": round(peak_qps, 1),
        "write_qps": round(write_qps, 1),
        "read_qps": round(read_qps, 1),
        "daily_storage_gb": round(daily_storage_bytes / (1024 ** 3), 2),
        "total_storage_tb": round(total_storage_tb, 2),
        "bandwidth_mbps": round(bandwidth_mbps, 2),
        "cache_size_gb": round(daily_cache_gb, 2),
        "servers_needed": servers_needed,
    }


def demo_scale_estimation():
    section("PART 2: 規模見積もり計算 (Back-of-Envelope)")

    subsection("計算公式テンプレート")
    print("    ┌──────────────────────────────────────────────────────────┐")
    print("    │ QPS = DAU × avg_requests / 86400                        │")
    print("    │ Peak QPS = QPS × 2 (or ×3 for spiky traffic)            │")
    print("    │ Write QPS = QPS / (1 + R:W ratio)                       │")
    print("    │ Storage (5yr) = daily_data × 365 × 5                    │")
    print("    │ Bandwidth = QPS × data_size × 8 bits                    │")
    print("    │ Cache = daily_data × 0.2 (80/20 rule)                   │")
    print("    │ Servers = Peak QPS / capacity_per_server                 │")
    print("    └──────────────────────────────────────────────────────────┘")
    print()

    # --- 例1: URL Shortener ---
    subsection("例1: URL Shortener (DAU 100M)")
    result = estimate_scale(
        dau=100_000_000,
        avg_requests_per_user=1,
        data_size_per_request_bytes=500,  # URL + メタデータ
        read_write_ratio=100,  # 読み100:書き1
    )
    for k, v in result.items():
        demo(k, f"{v:,}" if isinstance(v, (int, float)) else v)

    # --- 例2: Chat System ---
    subsection("例2: Chat System (DAU 50M)")
    result2 = estimate_scale(
        dau=50_000_000,
        avg_requests_per_user=40,  # 1日40メッセージ
        data_size_per_request_bytes=200,  # メッセージ本文
        read_write_ratio=1,  # 読み書きほぼ同数
    )
    for k, v in result2.items():
        demo(k, f"{v:,}" if isinstance(v, (int, float)) else v)

    # --- 例3: Video Streaming ---
    subsection("例3: Video Streaming (DAU 200M)")
    result3 = estimate_scale(
        dau=200_000_000,
        avg_requests_per_user=5,  # 1日5本視聴
        data_size_per_request_bytes=50_000_000,  # 50MB/動画 (メタデータ含む概算)
        read_write_ratio=200,
        requests_per_server=500,  # CDN 前提でもオリジンサーバー概算
    )
    for k, v in result3.items():
        demo(k, f"{v:,}" if isinstance(v, (int, float)) else v)

    question("見積もりが10倍ずれたらどうなる？許容できるか？")


# ============================================================
# PART 3: 10大設計問題 完全ウォークスルー
# ============================================================

# --------------------------------------------------
# 問題 1: URL Shortener
# --------------------------------------------------

def design_url_shortener():
    subsection("設計問題 1: URL Shortener")

    # Step 1
    print("    [Step 1: 要件]")
    print("    Functional: URL短縮, リダイレクト, Analytics, カスタムエイリアス")
    print("    Non-Functional: 99.99% 可用性, <100ms リダイレクト, 一意性保証")
    print("    規模: DAU 100M, 書込 1K QPS, 読込 100K QPS")
    print()

    # Step 2
    print("    [Step 2: API]")
    print("    POST /api/v1/shorten  → { short_url }")
    print("    GET  /{code}          → 301 Redirect")
    print("    GET  /api/v1/stats/{code} → { clicks, referrers, geo }")
    print()
    print("    301 vs 302:")
    print("      301 (Moved Permanently): ブラウザがキャッシュ → サーバー負荷減")
    print("      302 (Found):             毎回サーバー経由 → Analytics に必須")
    print()

    # Step 3
    print("    [Step 3: High-Level Design]")
    diagram([
        "Client ──> LB ──> Web Server ──> DB (Write Path)",
        "                      │",
        "                      ├──> Cache (Redis)  ──> DB (Read Path)",
        "                      │",
        "                      └──> Analytics Queue ──> Analytics DB",
        "",
        "短縮キー生成:",
        "  方式A: Base62 (MD5ハッシュの先頭7文字 → 62^7 = 3.5兆通り)",
        "  方式B: Auto-increment ID → Base62 変換",
        "  方式C: 事前生成 Key Generation Service (KGS)",
    ])

    # Base62 エンコード実装
    print("    [Base62 エンコード実装]")
    base62_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def base62_encode(num: int) -> str:
        if num == 0:
            return base62_chars[0]
        result = []
        while num > 0:
            result.append(base62_chars[num % 62])
            num //= 62
        return "".join(reversed(result))

    for test_id in [1, 1000, 1_000_000, 3_500_000_000]:
        encoded = base62_encode(test_id)
        demo(f"ID {test_id:>13,}", f"→ {encoded} (長さ {len(encoded)})")
    print()

    # Step 4
    print("    [Step 4: Deep Dive]")
    point("衝突回避: DB に UNIQUE 制約 + リトライ or KGS で事前確保")
    point("キャッシュ: 頻繁アクセスURL を Redis に LRU キャッシュ")
    point("DB: NoSQL (DynamoDB) — Key-Value アクセスパターン")
    point("Sharding: hash(short_code) % N でパーティション")
    print()

    # Step 5
    print("    [Step 5: トレードオフ]")
    print("    ┌─────────────────┬──────────────────┬──────────────────┐")
    print("    │ 方式            │ メリット         │ デメリット       │")
    print("    ├─────────────────┼──────────────────┼──────────────────┤")
    print("    │ Hash + 衝突検知 │ 実装シンプル     │ 衝突時リトライ   │")
    print("    │ Auto-inc + B62  │ 衝突なし         │ 推測可能(連番)   │")
    print("    │ KGS (事前生成)  │ 高速・衝突なし   │ 運用コスト増     │")
    print("    └─────────────────┴──────────────────┴──────────────────┘")
    print()


# --------------------------------------------------
# 問題 2: Rate Limiter
# --------------------------------------------------

def design_rate_limiter():
    subsection("設計問題 2: Rate Limiter")

    print("    [Step 1: 要件]")
    print("    Functional: API ごとにリクエスト数を制限, 超過時 429 返却")
    print("    Non-Functional: 低レイテンシ (<1ms), 分散環境対応, 高精度")
    print()

    print("    [Step 2: API]")
    print("    ミドルウェアとして実装 (API Gateway or Sidecar)")
    print("    Response Headers:")
    print("      X-RateLimit-Limit: 100")
    print("      X-RateLimit-Remaining: 42")
    print("      X-RateLimit-Retry-After: 30")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "Client ──> API Gateway ──> Rate Limiter ──> Backend",
        "                               │",
        "                          ┌────▼────┐",
        "                          │  Redis  │ (カウンター/トークン管理)",
        "                          └─────────┘",
        "                               │",
        "                          ┌────▼────────┐",
        "                          │ Rules Config │ (YAML/DB)",
        "                          └─────────────┘",
    ])

    # Token Bucket 実装
    print("    [Token Bucket アルゴリズム 実装]")

    class TokenBucket:
        """トークンバケット: 一定レートでトークンが補充される"""
        def __init__(self, capacity: int, refill_rate: float):
            self.capacity = capacity
            self.tokens = capacity
            self.refill_rate = refill_rate  # tokens/sec
            self.last_refill = time.time()

        def allow(self) -> bool:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    results = []
    for i in range(8):
        results.append(bucket.allow())
    demo("Token Bucket (cap=5, rate=1/s), 8連続リクエスト", results)
    print()

    # Sliding Window Counter 実装
    print("    [Sliding Window Counter 実装]")

    class SlidingWindowCounter:
        """固定ウィンドウ2つを重み付け合算"""
        def __init__(self, limit: int, window_sec: int = 60):
            self.limit = limit
            self.window_sec = window_sec
            self.current_count = 0
            self.previous_count = 0
            self.current_window_start = int(time.time()) // window_sec * window_sec

        def allow(self) -> bool:
            now = int(time.time())
            window_start = now // self.window_sec * self.window_sec
            if window_start != self.current_window_start:
                self.previous_count = self.current_count
                self.current_count = 0
                self.current_window_start = window_start
            elapsed_ratio = (now - window_start) / self.window_sec
            estimated = self.previous_count * (1 - elapsed_ratio) + self.current_count
            if estimated < self.limit:
                self.current_count += 1
                return True
            return False

    point("Token Bucket: バースト許容, 実装シンプル, メモリ効率良い")
    point("Sliding Window: 精度が高い, メモリ少し多め")
    point("分散環境: Redis INCR + EXPIRE or Lua スクリプトで原子操作")
    print()

    print("    [Step 5: トレードオフ]")
    print("    ┌──────────────────────┬──────────────────┬────────────────┐")
    print("    │ アルゴリズム         │ メリット         │ デメリット     │")
    print("    ├──────────────────────┼──────────────────┼────────────────┤")
    print("    │ Token Bucket         │ バースト可, 省メモリ│ 精度がやや低い│")
    print("    │ Sliding Window Log   │ 高精度           │ メモリ大       │")
    print("    │ Sliding Window Count │ バランス良好     │ 近似値         │")
    print("    │ Fixed Window         │ 最もシンプル     │ 境界でバースト │")
    print("    └──────────────────────┴──────────────────┴────────────────┘")
    print()


# --------------------------------------------------
# 問題 3: Chat System (WhatsApp/Messenger)
# --------------------------------------------------

def design_chat_system():
    subsection("設計問題 3: Chat System")

    print("    [Step 1: 要件]")
    print("    Functional: 1対1チャット, グループチャット, オンライン状態, 既読")
    print("    Non-Functional: リアルタイム (<200ms), メッセージ順序保証, 永続化")
    print("    規模: DAU 50M, 1人40msg/day → 2B msg/day, 23K write QPS")
    print()

    print("    [Step 2: API]")
    print("    WebSocket: wss://chat.example.com/ws (双方向リアルタイム)")
    print("    REST (fallback): POST /api/v1/messages, GET /api/v1/messages?channel_id=")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "┌────────┐  WebSocket  ┌──────────────┐     ┌────────────┐",
        "│User A  │────────────>│ Chat Server  │────>│ Message DB │",
        "└────────┘             │ (Stateful)   │     │ (Cassandra)│",
        "                       └──────┬───────┘     └────────────┘",
        "                              │",
        "                       ┌──────▼───────┐     ┌────────────┐",
        "                       │ Message Queue│────>│ Chat Server│",
        "                       │  (Kafka)     │     │ (User B)   │",
        "                       └──────────────┘     └──────┬─────┘",
        "                                                   │ WebSocket",
        "                                            ┌──────▼─────┐",
        "                                            │   User B   │",
        "                                            └────────────┘",
        "",
        "オンライン状態: Heartbeat (30秒間隔) → Redis に last_seen 記録",
        "グループチャット: Fan-out via Message Queue",
    ])

    print("    [Step 4: Deep Dive]")
    point("メッセージ順序: サーバー側タイムスタンプ + Sequence ID (per channel)")
    point("DB選定: Cassandra / HBase — Write heavy, 時系列データに最適")
    point("パーティションキー: channel_id, クラスタリングキー: message_id (時系列)")
    point("Fan-out on Write (小グループ): 送信時に全員の inbox に書き込み")
    point("Fan-out on Read (大グループ 500+): 受信時にグループから pull")
    point("既読管理: {user_id, channel_id, last_read_msg_id} → Redis")
    print()

    print("    [Step 5: トレードオフ]")
    point("WebSocket vs Long Polling: WS は双方向・低レイテンシだがステートフル")
    point("Push vs Pull: Push は小グループ向き, Pull は大グループ向き")
    point("メッセージ保存期間: 無制限 vs TTL (コスト vs ユーザー体験)")
    print()


# --------------------------------------------------
# 問題 4: News Feed (Twitter/Facebook)
# --------------------------------------------------

def design_news_feed():
    subsection("設計問題 4: News Feed")

    print("    [Step 1: 要件]")
    print("    Functional: 投稿作成, フィード取得 (フォロー中ユーザーの投稿)")
    print("    Non-Functional: フィード生成 <500ms, ランキング/パーソナライズ")
    print("    規模: DAU 300M, フォロー中の平均200人")
    print()

    print("    [Step 2: API]")
    print("    POST /api/v1/feed/posts     → 投稿作成")
    print("    GET  /api/v1/feed?cursor=   → フィード取得 (カーソルページネーション)")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "投稿フロー (Write Path):",
        "  User ──> Post Service ──> Post DB",
        "                │",
        "                ├──> Fan-out Service ──> News Feed Cache (per user)",
        "                └──> Notification Service",
        "",
        "フィード取得 (Read Path):",
        "  User ──> Feed Service ──> News Feed Cache ──> 表示",
        "                │",
        "                └──> (Cache Miss) ──> Fan-out on Read (celebrity)",
    ])

    print("    [Step 4: Deep Dive — Celebrity Problem]")
    point("一般ユーザー (フォロワー < 10K): Fan-out on Write (プリコンピュート)")
    point("Celebrity (フォロワー > 10K): Fan-out on Read (リクエスト時にマージ)")
    point("ハイブリッド: 一般は Push, Celebrity は Pull → フィード取得時にマージ")
    print()

    # ランキングスコア計算
    print("    [ランキングスコア計算の例]")

    def feed_ranking_score(
        likes: int, comments: int, shares: int,
        age_hours: float, is_close_friend: bool
    ) -> float:
        """EdgeRank 風のスコア計算"""
        affinity = 2.0 if is_close_friend else 1.0
        weight = likes * 1.0 + comments * 2.0 + shares * 3.0
        decay = 1.0 / (1.0 + age_hours * 0.1)
        return affinity * weight * decay

    posts = [
        {"likes": 10, "comments": 5, "shares": 1, "age_hours": 1, "close": True},
        {"likes": 100, "comments": 20, "shares": 10, "age_hours": 24, "close": False},
        {"likes": 5, "comments": 1, "shares": 0, "age_hours": 0.5, "close": True},
    ]
    for i, p in enumerate(posts):
        score = feed_ranking_score(p["likes"], p["comments"], p["shares"],
                                   p["age_hours"], p["close"])
        demo(f"Post {i+1} (likes={p['likes']}, age={p['age_hours']}h)",
             f"score = {score:.1f}")
    print()


# --------------------------------------------------
# 問題 5: Notification System
# --------------------------------------------------

def design_notification_system():
    subsection("設計問題 5: Notification System")

    print("    [Step 1: 要件]")
    print("    Functional: Push通知 (iOS/Android), SMS, Email, In-app")
    print("    Non-Functional: ソフトリアルタイム (<30s), 重複排除, 配信保証")
    print("    規模: 10B notifications/day")
    print()

    print("    [Step 2: API]")
    print("    POST /api/v1/notifications")
    print("    Body: { user_id, type, channel, template_id, params, priority }")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "┌──────────┐    ┌──────────┐    ┌────────────────┐",
        "│ Service  │───>│ Notif.   │───>│ Priority Queue │",
        "│ (Caller) │    │ Service  │    │ (Kafka/SQS)    │",
        "└──────────┘    └──────────┘    └───┬───┬───┬────┘",
        "                                    │   │   │",
        "                              ┌─────▼┐ ┌▼──┐ ┌▼────┐",
        "                              │ iOS  │ │SMS│ │Email│",
        "                              │Worker│ │   │ │     │",
        "                              └──────┘ └───┘ └─────┘",
        "                                    │   │   │",
        "                              ┌─────▼───▼───▼────┐",
        "                              │ Delivery Log DB  │",
        "                              │ (Dedup + Status) │",
        "                              └──────────────────┘",
    ])

    print("    [Step 4: Deep Dive]")
    point("Priority Queue: P0 (セキュリティ) > P1 (取引) > P2 (SNS) > P3 (マーケ)")
    point("Rate Limiting: ユーザーあたり通知上限 (1時間に5件 etc)")
    point("Template: 「{user}さんがいいねしました」→ テンプレートDB管理")
    point("重複排除: notification_id で idempotency check (Redis SET NX)")
    point("リトライ: Exponential Backoff + Dead Letter Queue")
    print()

    print("    [Step 5: トレードオフ]")
    point("Push vs Pull: Push はリアルタイム性高いが、サーバー負荷大")
    point("配信保証: At-least-once (重複許容) vs Exactly-once (実装複雑)")
    print()


# --------------------------------------------------
# 問題 6: Web Crawler
# --------------------------------------------------

def design_web_crawler():
    subsection("設計問題 6: Web Crawler")

    print("    [Step 1: 要件]")
    print("    Functional: Webページを再帰的にクロール, コンテンツ保存")
    print("    Non-Functional: Politeness (同一ドメインに過負荷をかけない)")
    print("    規模: 月10億ページ → ~400 pages/sec")
    print()

    print("    [Step 2: API]")
    print("    内部システム (API は管理用)")
    print("    POST /api/v1/crawl  { seed_urls, depth, domain_filter }")
    print("    GET  /api/v1/status { pages_crawled, errors, queue_size }")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "Seed URLs ──> URL Frontier ──> DNS Resolver ──> Fetcher",
        "                  ▲                                │",
        "                  │                          ┌─────▼──────┐",
        "            URL Filter                       │ Content    │",
        "           (Dedup +                          │ Parser     │",
        "            robots.txt)                      └─────┬──────┘",
        "                  ▲                                │",
        "                  │     ┌──────────────────────────┤",
        "                  │     │                          │",
        "            ┌─────┴──┐  │                    ┌────▼─────┐",
        "            │URL Seen│  │                    │ Content  │",
        "            │ (Set)  │  │                    │ Store    │",
        "            └────────┘  │                    └──────────┘",
        "                  ┌─────▼──────┐",
        "                  │ Link       │",
        "                  │ Extractor  │",
        "                  └────────────┘",
    ])

    print("    [Step 4: Deep Dive]")
    point("URL Frontier: 優先度キュー (PageRank) + Politeness キュー (ドメイン別)")
    point("Dedup: URL → MD5 ハッシュ → Bloom Filter (メモリ効率)")
    point("robots.txt: クロール前に必ず確認・キャッシュ")
    point("Trap 回避: URL 深さ制限, 同一ドメイン連続アクセス間隔 1秒以上")

    # Bloom Filter 概念実装
    print()
    print("    [Bloom Filter 簡易実装 (URL重複検知)]")

    class SimpleBloomFilter:
        def __init__(self, size: int = 1000, num_hashes: int = 3):
            self.size = size
            self.bits = [False] * size
            self.num_hashes = num_hashes

        def _hashes(self, item: str) -> List[int]:
            positions = []
            for i in range(self.num_hashes):
                h = hashlib.md5(f"{item}_{i}".encode()).hexdigest()
                positions.append(int(h, 16) % self.size)
            return positions

        def add(self, item: str):
            for pos in self._hashes(item):
                self.bits[pos] = True

        def might_contain(self, item: str) -> bool:
            return all(self.bits[pos] for pos in self._hashes(item))

    bf = SimpleBloomFilter(size=10000)
    urls = ["https://example.com/page1", "https://example.com/page2"]
    for url in urls:
        bf.add(url)
    demo("page1 in filter", bf.might_contain("https://example.com/page1"))
    demo("page3 in filter", bf.might_contain("https://example.com/page3"))
    point("False positive あり, False negative なし → 重複検知に最適")
    print()


# --------------------------------------------------
# 問題 7: Search Autocomplete
# --------------------------------------------------

def design_search_autocomplete():
    subsection("設計問題 7: Search Autocomplete")

    print("    [Step 1: 要件]")
    print("    Functional: 入力文字列に対してTop-K候補をリアルタイム返却")
    print("    Non-Functional: <100ms レイテンシ, 1日のクエリ = 5B")
    print()

    print("    [Step 2: API]")
    print("    GET /api/v1/suggestions?prefix=hel&limit=10")
    print("    Response: [\"hello world\", \"help center\", \"helmet\"]")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "                    ┌─────────────────────┐",
        "  User typing ────> │ Autocomplete Service│",
        "                    │   (Read Path)       │",
        "                    └────────┬────────────┘",
        "                             │",
        "                    ┌────────▼────────────┐",
        "                    │  Trie Cache (Redis)  │",
        "                    └─────────────────────┘",
        "",
        "  Search logs ────> Data Collection ────> Aggregation ────> Trie Build",
        "  (Write Path)      (Kafka)               (Spark/Flink)    (Offline)",
    ])

    # Trie + Top-K 実装
    print("    [Trie + Top-K 実装]")

    class TrieNode:
        def __init__(self):
            self.children: Dict[str, TrieNode] = {}
            self.top_queries: List[Tuple[int, str]] = []  # (count, query)

    class AutocompleteTrie:
        def __init__(self, top_k: int = 5):
            self.root = TrieNode()
            self.top_k = top_k

        def insert(self, query: str, count: int):
            node = self.root
            for char in query:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
                # Top-K をヒープで管理
                self._update_top_k(node, query, count)

        def _update_top_k(self, node: TrieNode, query: str, count: int):
            # 既存エントリを更新
            for i, (c, q) in enumerate(node.top_queries):
                if q == query:
                    node.top_queries[i] = (count, query)
                    node.top_queries.sort(reverse=True)
                    return
            node.top_queries.append((count, query))
            node.top_queries.sort(reverse=True)
            node.top_queries = node.top_queries[:self.top_k]

        def search(self, prefix: str) -> List[Tuple[int, str]]:
            node = self.root
            for char in prefix:
                if char not in node.children:
                    return []
                node = node.children[char]
            return node.top_queries

    trie = AutocompleteTrie(top_k=3)
    queries = [
        ("hello world", 1000), ("help center", 800), ("helmet", 500),
        ("hero", 300), ("health", 200), ("heat", 150),
    ]
    for q, c in queries:
        trie.insert(q, c)

    demo("prefix='hel'", trie.search("hel"))
    demo("prefix='he'", trie.search("he"))
    demo("prefix='her'", trie.search("her"))
    print()

    print("    [Step 4: Deep Dive]")
    point("Trie 更新: オフラインでバッチ再構築 → Trie サーバーにスワップデプロイ")
    point("メモリ削減: 短いプレフィックスのみ保持 (6文字以下)")
    point("多言語: Unicode 対応, 中国語は Pinyin 変換も")
    point("パーソナライズ: ユーザー履歴をマージ (ローカル + グローバル)")
    print()


# --------------------------------------------------
# 問題 8: YouTube / Video Streaming
# --------------------------------------------------

def design_video_streaming():
    subsection("設計問題 8: YouTube / Video Streaming")

    print("    [Step 1: 要件]")
    print("    Functional: 動画アップロード, ストリーミング再生, 検索")
    print("    Non-Functional: 高可用性, 高速再生開始 (<2s), 世界規模CDN")
    print("    規模: DAU 200M, 5本/日視聴, アップロード 500K本/日")
    print()

    print("    [Step 2: API]")
    print("    POST /api/v1/videos/upload (multipart, resumable)")
    print("    GET  /api/v1/videos/{id}/stream?quality=720p")
    print("    GET  /api/v1/search?q=keyword&page=1")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "アップロードフロー:",
        "  User ──> Upload Service ──> Object Store (S3)",
        "                │",
        "                ▼",
        "  Transcode Queue ──> Transcode Workers (DAG)",
        "       │                    │",
        "       │              ┌─────▼──────┐",
        "       │              │ 360p, 480p │",
        "       │              │ 720p,1080p │",
        "       │              │ (parallel) │",
        "       │              └─────┬──────┘",
        "       │                    ▼",
        "       │              CDN に配信",
        "",
        "視聴フロー:",
        "  User ──> CDN Edge ──> (miss) ──> Origin (S3)",
        "             │",
        "             ▼",
        "  Adaptive Bitrate Streaming (HLS/DASH)",
    ])

    print("    [Step 4: Deep Dive]")
    point("Resumable Upload: チャンク分割 + チェックポイント (Google の Resumable API)")
    point("トランスコード DAG: Video → Split → Encode (並列) → Merge → Thumbnail")
    point("Adaptive Bitrate: ネットワーク品質に応じて自動切替 (HLS manifest)")
    point("CDN: 地理的に近いエッジからデリバリー, 人気動画はプリウォーム")
    point("メタデータDB: MySQL (ACID) + ElasticSearch (検索)")
    print()

    # トランスコード DAG 概念
    print("    [トランスコード DAG タスク定義]")

    @dataclass
    class TranscodeTask:
        task_id: str
        input_file: str
        output_resolution: str
        status: str = "pending"  # pending → running → completed → failed

    tasks = [
        TranscodeTask("t1", "video_raw.mp4", "360p"),
        TranscodeTask("t2", "video_raw.mp4", "720p"),
        TranscodeTask("t3", "video_raw.mp4", "1080p"),
    ]
    for t in tasks:
        demo(f"Task {t.task_id}", f"{t.input_file} → {t.output_resolution} [{t.status}]")
    print()


# --------------------------------------------------
# 問題 9: Google Maps
# --------------------------------------------------

def design_google_maps():
    subsection("設計問題 9: Google Maps")

    print("    [Step 1: 要件]")
    print("    Functional: 地図表示, 経路探索 (最短/最速), ETA, ナビゲーション")
    print("    Non-Functional: リアルタイム交通情報反映, 世界規模, <1s 経路計算")
    print()

    print("    [Step 2: API]")
    print("    GET /api/v1/tiles?lat=35.6&lng=139.7&zoom=15")
    print("    GET /api/v1/directions?origin=A&dest=B&mode=driving")
    print("    GET /api/v1/eta?origin=A&dest=B")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "┌────────┐   ┌──────────┐   ┌──────────────┐",
        "│ Client │──>│ API GW   │──>│ Route Planner│",
        "└────────┘   └──────────┘   └──────┬───────┘",
        "     │                             │",
        "     │    ┌────────────┐    ┌──────▼───────┐",
        "     └───>│ Tile Server│    │ Graph Engine │",
        "          │ (CDN+S3)  │    │(Dijkstra/A*) │",
        "          └────────────┘    └──────┬───────┘",
        "                                   │",
        "                     ┌─────────────┼────────────┐",
        "                     │             │            │",
        "               ┌─────▼───┐  ┌─────▼────┐ ┌────▼─────┐",
        "               │Road     │  │Traffic   │ │ETA ML    │",
        "               │Graph DB │  │(Realtime)│ │Model     │",
        "               └─────────┘  └──────────┘ └──────────┘",
    ])

    # Dijkstra 最短経路 (簡易実装)
    print("    [Dijkstra 最短経路 簡易実装]")

    def dijkstra(graph: Dict[str, List[Tuple[str, float]]], start: str, end: str):
        distances = {start: 0.0}
        previous = {}
        pq = [(0.0, start)]

        while pq:
            dist, node = heapq.heappop(pq)
            if node == end:
                # 経路復元
                path = []
                current = end
                while current in previous:
                    path.append(current)
                    current = previous[current]
                path.append(start)
                return dist, list(reversed(path))
            if dist > distances.get(node, float("inf")):
                continue
            for neighbor, weight in graph.get(node, []):
                new_dist = dist + weight
                if new_dist < distances.get(neighbor, float("inf")):
                    distances[neighbor] = new_dist
                    previous[neighbor] = node
                    heapq.heappush(pq, (new_dist, neighbor))
        return float("inf"), []

    # 道路グラフの例
    road_graph = {
        "渋谷": [("新宿", 5.0), ("六本木", 3.0)],
        "新宿": [("池袋", 4.0), ("渋谷", 5.0)],
        "六本木": [("東京", 6.0), ("渋谷", 3.0)],
        "池袋": [("東京", 7.0)],
        "東京": [],
    }
    dist, path = dijkstra(road_graph, "渋谷", "東京")
    demo("渋谷 → 東京 最短距離", f"{dist}km")
    demo("経路", " → ".join(path))
    print()

    print("    [Step 4: Deep Dive]")
    point("グラフ分割: 大規模グラフは領域分割 (Graph Partitioning)")
    point("階層型経路探索: 高速道路ネットワーク → 一般道 (Contraction Hierarchies)")
    point("タイルレンダリング: Zoom レベル別にプリレンダー → CDN キャッシュ")
    point("Geospatial Index: Geohash / S2 Geometry / QuadTree")
    point("ETA: 過去データ + リアルタイム交通 → ML モデル予測")
    print()


# --------------------------------------------------
# 問題 10: Distributed Cache
# --------------------------------------------------

def design_distributed_cache():
    subsection("設計問題 10: Distributed Cache")

    print("    [Step 1: 要件]")
    print("    Functional: Key-Value Put/Get, TTL, Eviction")
    print("    Non-Functional: <1ms レイテンシ, 高スループット, 水平スケール")
    print("    規模: 100TB データ, 1M QPS")
    print()

    print("    [Step 2: API]")
    print("    PUT(key, value, ttl)  → void")
    print("    GET(key)              → value | null")
    print("    DELETE(key)           → void")
    print()

    print("    [Step 3: High-Level Design]")
    diagram([
        "Client ──> Cache Proxy (Consistent Hashing) ──> Cache Node 1",
        "                                             ──> Cache Node 2",
        "                                             ──> Cache Node N",
        "",
        "各ノード: Hash Map + Doubly Linked List (LRU)",
    ])

    # Consistent Hashing 実装
    print("    [Consistent Hashing 実装]")

    class ConsistentHashing:
        def __init__(self, num_virtual_nodes: int = 150):
            self.num_virtual = num_virtual_nodes
            self.ring: List[Tuple[int, str]] = []  # (hash, node_name)
            self.nodes: set = set()

        def _hash(self, key: str) -> int:
            return int(hashlib.md5(key.encode()).hexdigest(), 16)

        def add_node(self, node: str):
            self.nodes.add(node)
            for i in range(self.num_virtual):
                h = self._hash(f"{node}:{i}")
                self.ring.append((h, node))
            self.ring.sort()

        def remove_node(self, node: str):
            self.nodes.discard(node)
            self.ring = [(h, n) for h, n in self.ring if n != node]

        def get_node(self, key: str) -> str:
            if not self.ring:
                raise ValueError("No nodes in ring")
            h = self._hash(key)
            # 二分探索で次のノードを見つける
            idx = self._bisect(h)
            return self.ring[idx % len(self.ring)][1]

        def _bisect(self, target: int) -> int:
            lo, hi = 0, len(self.ring)
            while lo < hi:
                mid = (lo + hi) // 2
                if self.ring[mid][0] < target:
                    lo = mid + 1
                else:
                    hi = mid
            return lo

    ch = ConsistentHashing(num_virtual_nodes=100)
    for node in ["cache-1", "cache-2", "cache-3"]:
        ch.add_node(node)

    # キー分布を確認
    distribution: Dict[str, int] = defaultdict(int)
    for i in range(10000):
        assigned = ch.get_node(f"key_{i}")
        distribution[assigned] += 1
    print("    キー分布 (10,000 keys, 3 nodes):")
    for node, count in sorted(distribution.items()):
        bar = "#" * (count // 50)
        demo(f"{node}", f"{count:,} keys {bar}")

    # ノード追加時の再分配
    ch.add_node("cache-4")
    new_dist: Dict[str, int] = defaultdict(int)
    for i in range(10000):
        assigned = ch.get_node(f"key_{i}")
        new_dist[assigned] += 1
    print("    ノード追加後 (cache-4 追加):")
    for node, count in sorted(new_dist.items()):
        bar = "#" * (count // 50)
        demo(f"{node}", f"{count:,} keys {bar}")
    print()

    # LRU Cache 実装
    print("    [LRU Cache 実装]")

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
                self.cache.popitem(last=False)  # 最も古いエントリを削除

        @property
        def hit_rate(self) -> float:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0

    lru = LRUCache(capacity=3)
    operations = [
        ("put", "a", 1), ("put", "b", 2), ("put", "c", 3),
        ("get", "a", None), ("put", "d", 4),  # b が Evict される
        ("get", "b", None), ("get", "c", None),
    ]
    for op, key, val in operations:
        if op == "put":
            lru.put(key, val)
            demo(f"PUT({key}, {val})", f"cache={list(lru.cache.keys())}")
        else:
            result = lru.get(key)
            demo(f"GET({key})", f"{result}, cache={list(lru.cache.keys())}")
    demo("Hit rate", f"{lru.hit_rate:.1%}")
    print()

    print("    [Step 4: Deep Dive]")
    point("Caching Strategy:")
    print("      Cache-Aside: App が Cache と DB を別々に管理 (最も一般的)")
    print("      Write-Through: Write → Cache → DB (一貫性高いが書込遅い)")
    print("      Write-Behind: Write → Cache → 非同期で DB (高速だがデータロスリスク)")
    print("      Read-Through: Cache が DB を自動 fetch (App はCache のみ参照)")
    print()
    point("Eviction Policy: LRU (最も一般的), LFU (頻度ベース), TTL")
    point("Hot Key 対策: レプリカ分散 or ローカルキャッシュ併用")
    point("Cache Stampede: Mutex Lock or Probabilistic Early Expiration")
    print()


# ============================================================
# PART 4: 分散システム Building Blocks まとめ
# ============================================================

def building_blocks_summary():
    section("PART 4: 分散システム Building Blocks まとめ")

    # --- Load Balancer ---
    subsection("4-1: Load Balancer")
    print("    ┌──────────────────────────────────────────────────────────────┐")
    print("    │ L4 (Transport層)          │ L7 (Application層)              │")
    print("    ├──────────────────────────────────────────────────────────────┤")
    print("    │ TCP/UDP レベルで振り分け   │ HTTP ヘッダ/パスで振り分け      │")
    print("    │ 高速・低オーバーヘッド     │ コンテンツベースルーティング     │")
    print("    │ 例: NLB, HAProxy (TCP)    │ 例: ALB, Nginx, Envoy          │")
    print("    └──────────────────────────────────────────────────────────────┘")
    print()
    point("アルゴリズム: Round Robin, Weighted RR, Least Connections, IP Hash")
    point("ヘルスチェック: Active (定期 ping) vs Passive (失敗カウント)")
    print()

    # --- CDN ---
    subsection("4-2: CDN (Content Delivery Network)")
    print("    Push CDN: コンテンツ更新時にオリジンから CDN へ push")
    print("      → 更新頻度が低い静的コンテンツ向き")
    print("    Pull CDN: 初回リクエスト時に CDN がオリジンから fetch")
    print("      → アクセスパターンが予測しにくい場合に有利")
    print()
    point("Cache Invalidation: TTL, Purge API, バージョン付き URL (?v=2)")
    print()

    # --- Message Queue ---
    subsection("4-3: Message Queue")
    print("    ┌──────────────────────┬────────────────────────────────────┐")
    print("    │ セマンティクス       │ 説明                             │")
    print("    ├──────────────────────┼────────────────────────────────────┤")
    print("    │ At-most-once         │ 失ったら諦める (Fire & Forget)   │")
    print("    │ At-least-once        │ 再送あり, 消費側で冪等性必要     │")
    print("    │ Exactly-once         │ トランザクション + 冪等キー      │")
    print("    └──────────────────────┴────────────────────────────────────┘")
    print()
    point("Kafka: 高スループット, ログベース, パーティション並列")
    point("RabbitMQ: 柔軟なルーティング, 低レイテンシ")
    point("SQS: マネージド, 運用コスト低, FIFO モードあり")
    print()

    # --- DB 選定フローチャート ---
    subsection("4-4: DB 選定フローチャート")
    diagram([
        "データに ACID が必要？",
        "  ├── Yes ──> リレーショナル (MySQL, PostgreSQL)",
        "  │            └── 超大規模？ ──> NewSQL (CockroachDB, TiDB)",
        "  └── No",
        "       ├── Key-Value アクセス？ ──> Redis, DynamoDB",
        "       ├── ドキュメント型？ ──> MongoDB",
        "       ├── Wide-Column (時系列)？ ──> Cassandra, HBase",
        "       ├── グラフ構造？ ──> Neo4j, Neptune",
        "       └── 全文検索？ ──> Elasticsearch",
    ])

    # --- Caching Strategy ---
    subsection("4-5: Caching Strategy")
    diagram([
        "Cache-Aside (Lazy Loading):",
        "  Read: App → Cache (hit?) → DB → Cache に書き込み",
        "  Write: App → DB → Cache を invalidate",
        "",
        "Write-Through:",
        "  Write: App → Cache → DB (同期)",
        "",
        "Write-Behind (Write-Back):",
        "  Write: App → Cache → DB (非同期バッチ)",
        "",
        "Read-Through:",
        "  Read: App → Cache (miss → Cache が DB を fetch)",
    ])

    # --- Sharding ---
    subsection("4-6: Sharding (データ分割)")
    print("    ┌───────────────┬────────────────────┬──────────────────────┐")
    print("    │ 方式          │ メリット           │ デメリット           │")
    print("    ├───────────────┼────────────────────┼──────────────────────┤")
    print("    │ Range-based   │ 範囲クエリ効率的   │ ホットスポット       │")
    print("    │ Hash-based    │ 均一分散           │ 範囲クエリ不可       │")
    print("    │ Directory     │ 柔軟な制御         │ SPOF, ルックアップ   │")
    print("    └───────────────┴────────────────────┴──────────────────────┘")
    print()
    point("Resharding: Consistent Hashing で最小限のデータ移動")
    point("Cross-shard クエリ: Scatter-Gather パターン (レイテンシ注意)")
    print()

    # --- Replication ---
    subsection("4-7: Replication (データ複製)")
    print("    Leader-Follower: 1台の Leader が書込, Follower は読取専用")
    print("      → 読み取りスケール可, Leader が SPOF")
    print("    Multi-Leader: 複数 Leader で書込可")
    print("      → 書込スケール, 衝突解決が複雑 (LWW, CRDT)")
    print("    Leaderless: 全ノードが読み書き (Quorum: W+R > N)")
    print("      → 可用性最大, 一貫性は Quorum 設定次第")
    print()

    # --- ID Generation ---
    subsection("4-8: ID Generation")
    print("    ┌──────────────────┬──────────────────────┬──────────────────┐")
    print("    │ 方式             │ メリット             │ デメリット       │")
    print("    ├──────────────────┼──────────────────────┼──────────────────┤")
    print("    │ UUID v4          │ 分散生成, 衝突ほぼ無 │ 128bit, ソート不可│")
    print("    │ Snowflake        │ 64bit, 時系列ソート可│ Clock依存        │")
    print("    │ DB Auto-inc     │ シンプル, ソート可    │ SPOF, ボトルネック│")
    print("    │ ULID             │ ソート可, UUID互換   │ ライブラリ依存   │")
    print("    └──────────────────┴──────────────────────┴──────────────────┘")
    print()

    # Snowflake ID 実装
    print("    [Snowflake ID 簡易実装]")

    class SnowflakeIDGenerator:
        """Twitter Snowflake 風 ID 生成器
        構造: [1bit unused][41bit timestamp][10bit machine_id][12bit sequence]
        """
        EPOCH = 1609459200000  # 2021-01-01 00:00:00 UTC (ms)

        def __init__(self, machine_id: int):
            self.machine_id = machine_id & 0x3FF  # 10bit
            self.sequence = 0
            self.last_timestamp = -1

        def _current_ms(self) -> int:
            return int(time.time() * 1000)

        def generate(self) -> int:
            timestamp = self._current_ms()
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF  # 12bit
                if self.sequence == 0:
                    # 同一ミリ秒で4096個使い切った → 次のミリ秒を待つ
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_ms()
            else:
                self.sequence = 0
            self.last_timestamp = timestamp

            return (
                ((timestamp - self.EPOCH) << 22)
                | (self.machine_id << 12)
                | self.sequence
            )

    gen = SnowflakeIDGenerator(machine_id=1)
    ids = [gen.generate() for _ in range(5)]
    for sid in ids:
        demo(f"Snowflake ID", f"{sid} (binary length: {sid.bit_length()} bits)")
    point("41bit timestamp → 約69年分, 12bit sequence → 4096 ID/ms/machine")
    print()


# ============================================================
# PART 5: 優先度 (Tier 1-4)
# ============================================================

def priority_tiers():
    section("PART 5: 学習優先度 (Tier 1-4)")

    print("    ┌──────┬────────────────────────────────────────────────────────┐")
    print("    │ Tier │ 内容                                                  │")
    print("    ├──────┼────────────────────────────────────────────────────────┤")
    print("    │  1   │ 面接フレームワーク (Step 1-5) をカラダに染み込ませる    │")
    print("    │      │ 規模見積もり (Back-of-Envelope) を30秒で出せるように   │")
    print("    │      │ Building Blocks (LB, Cache, Queue, DB選定)            │")
    print("    ├──────┼────────────────────────────────────────────────────────┤")
    print("    │  2   │ 必須設計問題: URL Shortener, Rate Limiter, Chat       │")
    print("    │      │ News Feed, Notification — この5問は確実に解けること    │")
    print("    │      │ Consistent Hashing, Sharding, Replication             │")
    print("    ├──────┼────────────────────────────────────────────────────────┤")
    print("    │  3   │ Web Crawler, Search Autocomplete, Video Streaming     │")
    print("    │      │ Google Maps — 問題のバリエーションを広げる            │")
    print("    │      │ ID Generation (Snowflake), Bloom Filter               │")
    print("    ├──────┼────────────────────────────────────────────────────────┤")
    print("    │  4   │ Distributed Cache の深堀り (Cache Stampede, Hot Key)  │")
    print("    │      │ 面接で「もし時間があれば」と言える追加機能の設計       │")
    print("    │      │ 実際の OSS (Redis, Kafka, Cassandra) のアーキ理解     │")
    print("    └──────┴────────────────────────────────────────────────────────┘")
    print()

    point("Tier 1 を完璧にすれば、どんな問題が来ても構造的に解ける")
    point("Tier 2 の5問は暗記ではなく「自力で導出」できるレベルを目指す")
    point("Tier 3-4 は Tier 1-2 の土台があれば応用で対応可能")
    print()

    question("面接本番では完璧を目指さない。")
    point("「この部分は時間があれば深掘りしたい」と言えることが Senior の証。")
    point("面接官は「何を知っているか」よりも「どう考えるか」を見ている。")


# ============================================================
# メイン実行
# ============================================================

def main():
    print()
    print("=" * 72)
    print("  FAANG System Design Interview 完全ウォークスルーガイド")
    print("  ─ 45分で大規模システムを設計する技術 ─")
    print("=" * 72)

    # PART 1: フレームワーク
    explain_framework()

    # PART 2: 規模見積もり
    demo_scale_estimation()

    # PART 3: 10大設計問題
    section("PART 3: 10大設計問題 完全ウォークスルー")

    design_url_shortener()
    design_rate_limiter()
    design_chat_system()
    design_news_feed()
    design_notification_system()
    design_web_crawler()
    design_search_autocomplete()
    design_video_streaming()
    design_google_maps()
    design_distributed_cache()

    # PART 4: Building Blocks
    building_blocks_summary()

    # PART 5: 優先度
    priority_tiers()

    print()
    print("=" * 72)
    print("  ガイド終了。")
    print("  「設計に正解はない。トレードオフを語れることが正解。」")
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
