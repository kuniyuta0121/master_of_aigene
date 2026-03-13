#!/usr/bin/env python3
"""
Applied Cryptography Fundamentals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
暗号技術を数学的基礎から TLS 1.3 まで、動くコードで体系的に学ぶ

実行: python cryptography_fundamentals.py
依存: 標準ライブラリのみ (hashlib, hmac, secrets, struct, os, time)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
import hmac
import secrets
import struct
import os
import time
import random
import math
from typing import List, Tuple, Optional, Dict

SEP = "━" * 60
THIN = "─" * 50


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title: str) -> None:
    print(f"\n{THIN}")
    print(f"  {title}")
    print(THIN)


def demo(label: str) -> None:
    print(f"\n  ▶ {label}")


# ============================================================
# 第1章: 数学的基礎 (Math Foundations)
# ============================================================
def chapter1_math_foundations():
    section("第1章: 暗号の数学的基礎")
    print("""
    暗号技術はすべて数論の上に成り立つ。ここでは RSA や DH を
    理解するのに必要な数学を、実装しながら身につける。
    """)

    # --- GCD & Extended Euclidean ---
    demo("GCD (ユークリッドの互除法)")

    def gcd(a: int, b: int) -> int:
        """最大公約数"""
        while b:
            a, b = b, a % b
        return a

    print(f"    gcd(252, 105) = {gcd(252, 105)}")  # 21
    print(f"    gcd(17, 13)   = {gcd(17, 13)}")    # 1 (互いに素)

    demo("拡張ユークリッドの互除法 (Extended Euclidean)")
    print("""
    ax + by = gcd(a, b) を満たす x, y を求める。
    モジュラー逆元の計算に不可欠。
    """)

    def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
        """拡張ユークリッド: (gcd, x, y) where ax + by = gcd"""
        if a == 0:
            return b, 0, 1
        g, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return g, x, y

    g, x, y = extended_gcd(35, 15)
    print(f"    extended_gcd(35, 15) = gcd={g}, x={x}, y={y}")
    print(f"    検証: 35*{x} + 15*{y} = {35*x + 15*y}")

    # --- Modular Inverse ---
    demo("モジュラー逆元 (Modular Inverse)")
    print("""
    a^(-1) mod m : a * a^(-1) ≡ 1 (mod m)
    RSA で d = e^(-1) mod φ(n) を計算するのに使う。
    条件: gcd(a, m) = 1 (互いに素であること)
    """)

    def mod_inverse(a: int, m: int) -> int:
        """モジュラー逆元を拡張ユークリッドで計算"""
        g, x, _ = extended_gcd(a % m, m)
        if g != 1:
            raise ValueError(f"{a} has no inverse mod {m}")
        return x % m

    inv = mod_inverse(3, 26)
    print(f"    3^(-1) mod 26 = {inv}")
    print(f"    検証: 3 * {inv} mod 26 = {(3 * inv) % 26}")

    inv_rsa = mod_inverse(65537, 3120)
    print(f"    65537^(-1) mod 3120 = {inv_rsa}  (RSA で頻出)")
    print(f"    検証: 65537 * {inv_rsa} mod 3120 = {(65537 * inv_rsa) % 3120}")

    # --- Fast Exponentiation ---
    demo("高速べき乗 (Fast Modular Exponentiation)")
    print("""
    a^b mod m を O(log b) で計算。RSA 暗号化/復号の核心。
    二進展開法 (square-and-multiply) を使う。
    """)

    def fast_pow(base: int, exp: int, mod: int) -> int:
        """反復二乗法による高速べき乗"""
        result = 1
        base %= mod
        while exp > 0:
            if exp & 1:
                result = (result * base) % mod
            exp >>= 1
            base = (base * base) % mod
        return result

    print(f"    2^10 mod 1000   = {fast_pow(2, 10, 1000)}")
    print(f"    3^200 mod 50    = {fast_pow(3, 200, 50)}")
    print(f"    Python built-in = {pow(3, 200, 50)}")

    # --- Euler's Totient ---
    demo("オイラーのトーシェント関数 φ(n)")
    print("""
    φ(n) = n 以下で n と互いに素な正整数の個数
    - p が素数: φ(p) = p - 1
    - p, q が素数: φ(p*q) = (p-1)(q-1)  ← RSA の鍵生成で使用
    - オイラーの定理: a^φ(n) ≡ 1 (mod n)  (gcd(a,n)=1)
    """)

    def euler_totient(n: int) -> int:
        """オイラーのトーシェント関数"""
        result = n
        p = 2
        temp = n
        while p * p <= temp:
            if temp % p == 0:
                while temp % p == 0:
                    temp //= p
                result -= result // p
            p += 1
        if temp > 1:
            result -= result // temp
        return result

    print(f"    φ(7)   = {euler_totient(7)}   (素数 → 6)")
    print(f"    φ(12)  = {euler_totient(12)}  (1,5,7,11)")
    print(f"    φ(35)  = {euler_totient(35)}  = φ(5*7) = 4*6 = 24")

    # --- Miller-Rabin Primality ---
    demo("ミラー・ラビン素数判定")
    print("""
    確率的素数判定アルゴリズム。RSA の鍵生成で大きな素数を見つける。
    n-1 = 2^s * d と分解し、a^d mod n を繰り返し二乗して判定。
    k 回のテストで合成数を見逃す確率 ≤ 4^(-k)
    """)

    def is_prime_miller_rabin(n: int, k: int = 10) -> bool:
        """ミラー・ラビン素数判定"""
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0:
            return False

        # n-1 = 2^s * d
        s, d = 0, n - 1
        while d % 2 == 0:
            d //= 2
            s += 1

        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                continue
            for _ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    break
            else:
                return False
        return True

    test_nums = [2, 17, 561, 1009, 1000000007, 1000000009]
    for n in test_nums:
        result = is_prime_miller_rabin(n)
        print(f"    {n:>12} → {'素数' if result else '合成数'}")

    demo("素数生成 (RSA 鍵生成のコア)")

    def generate_prime(bits: int) -> int:
        """指定ビット数の素数を生成"""
        while True:
            n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
            if is_prime_miller_rabin(n, 20):
                return n

    p = generate_prime(32)
    print(f"    32ビット素数の例: {p}")
    print(f"    検証 (Miller-Rabin): {is_prime_miller_rabin(p)}")

    print("""
    [面接で聞かれるポイント]
    Q: なぜ Miller-Rabin であって決定的判定ではないのか?
    A: AKS は多項式時間だが定数が大きい。Miller-Rabin は k=40 で
       2^(-80) 以下の誤り確率を達成でき、実用的に十分。
       FIPS 186-5 でも推奨されている。
    """)


# ============================================================
# 第2章: 共通鍵暗号 (Symmetric Cryptography)
# ============================================================
def chapter2_symmetric_crypto():
    section("第2章: 共通鍵暗号 (Symmetric Cryptography)")
    print("""
    同じ鍵で暗号化・復号を行う。AES-256-GCM が現代の標準。
    ブロック暗号 + 暗号利用モードの組み合わせで理解する。
    """)

    # --- XOR / One-Time Pad ---
    demo("XOR と ワンタイムパッド (OTP)")

    def xor_bytes(a: bytes, b: bytes) -> bytes:
        return bytes(x ^ y for x, y in zip(a, b))

    plaintext = b"HELLO"
    key = os.urandom(len(plaintext))
    ciphertext = xor_bytes(plaintext, key)
    decrypted = xor_bytes(ciphertext, key)

    print(f"    平文:   {plaintext}")
    print(f"    鍵:     {key.hex()}")
    print(f"    暗号文: {ciphertext.hex()}")
    print(f"    復号:   {decrypted}")
    print("""
    OTP は情報理論的に安全 (Shannon 1949) だが:
    - 鍵が平文と同じ長さ → 鍵配送問題
    - 鍵の再利用は致命的 (XOR で平文同士が漏洩)
    """)

    # --- Feistel Network ---
    demo("Feistel ネットワーク (DES の構造)")
    print("""
    平文を L, R に分割し、ラウンド関数 F で繰り返し変換。
    Li+1 = Ri,  Ri+1 = Li ⊕ F(Ri, Ki)
    復号は同じ構造で鍵を逆順に適用するだけ。
    """)

    def feistel_round_func(data: int, subkey: int) -> int:
        """簡略化したラウンド関数"""
        return ((data * 31 + subkey) ^ (data >> 3)) & 0xFFFF

    def feistel_encrypt(plain: int, subkeys: List[int]) -> int:
        """32ビットの Feistel 暗号 (16ビット x 2)"""
        left = (plain >> 16) & 0xFFFF
        right = plain & 0xFFFF
        for sk in subkeys:
            left, right = right, left ^ feistel_round_func(right, sk)
        return (left << 16) | right

    def feistel_decrypt(cipher: int, subkeys: List[int]) -> int:
        """復号: サブキーを逆順にするだけ"""
        return feistel_encrypt(cipher, subkeys[::-1])

    subkeys = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
    original = 0xDEADBEEF
    encrypted = feistel_encrypt(original, subkeys)
    restored = feistel_decrypt(encrypted, subkeys)
    print(f"    平文:   0x{original:08X}")
    print(f"    暗号文: 0x{encrypted:08X}")
    print(f"    復号:   0x{restored:08X}")
    print(f"    一致:   {original == restored}")

    # --- Simplified AES Round ---
    demo("AES ラウンドの簡略シミュレーション")
    print("""
    AES-128: 10 ラウンド、各ラウンドで 4 つの変換
    1. SubBytes  - S-Box による非線形置換 (confusion)
    2. ShiftRows - 行のシフト (diffusion)
    3. MixColumns - 列の線形混合 (diffusion)
    4. AddRoundKey - ラウンド鍵との XOR

    ここでは 4x4 の状態行列で概念を示す。
    """)

    # Mini S-Box (4-bit, 教育用)
    SBOX = [0x6, 0x4, 0xC, 0x5, 0x0, 0x7, 0x2, 0xE,
            0x1, 0xF, 0x3, 0xD, 0x8, 0xA, 0x9, 0xB]
    INV_SBOX = [0] * 16
    for i, v in enumerate(SBOX):
        INV_SBOX[v] = i

    def mini_sub_bytes(state: List[int]) -> List[int]:
        return [SBOX[b & 0xF] for b in state]

    def mini_inv_sub_bytes(state: List[int]) -> List[int]:
        return [INV_SBOX[b & 0xF] for b in state]

    state = [0x3, 0xA, 0x7, 0x1]
    substituted = mini_sub_bytes(state)
    restored_s = mini_inv_sub_bytes(substituted)
    print(f"    元の状態:     {[hex(x) for x in state]}")
    print(f"    SubBytes後:   {[hex(x) for x in substituted]}")
    print(f"    InvSubBytes:  {[hex(x) for x in restored_s]}")

    # --- Block Cipher Modes ---
    demo("ブロック暗号利用モード")
    print("""
    ┌──────────┬───────────────────────────────────────────┐
    │ モード   │ 特徴                                     │
    ├──────────┼───────────────────────────────────────────┤
    │ ECB      │ 各ブロック独立暗号化 → パターン漏洩！    │
    │ CBC      │ 前の暗号文ブロックと XOR → IV 必要       │
    │ CTR      │ カウンタを暗号化して XOR → 並列処理可能  │
    │ GCM      │ CTR + GHASH 認証タグ → AEAD の標準       │
    └──────────┴───────────────────────────────────────────┘
    """)

    def simple_block_encrypt(block: bytes, key: bytes) -> bytes:
        """教育用の簡易ブロック暗号 (XOR ベース)"""
        return bytes(b ^ k for b, k in zip(block, key))

    def simple_block_decrypt(block: bytes, key: bytes) -> bytes:
        return simple_block_encrypt(block, key)  # XOR は自己逆

    BLOCK_SIZE = 8
    key = b"SECRETKY"

    # ECB Mode
    demo("ECB モード (危険な例)")

    def ecb_encrypt(plaintext: bytes, key: bytes) -> bytes:
        ct = b""
        for i in range(0, len(plaintext), BLOCK_SIZE):
            block = plaintext[i:i + BLOCK_SIZE]
            ct += simple_block_encrypt(block, key)
        return ct

    # ECB Penguin Problem
    msg_ecb = b"AAAABBBBAAAABBBB"  # 繰り返しパターン
    ct_ecb = ecb_encrypt(msg_ecb, key)
    print(f"    平文: {msg_ecb}")
    print(f"    ECB:  {ct_ecb.hex()}")
    blk1 = ct_ecb[:BLOCK_SIZE].hex()
    blk2 = ct_ecb[BLOCK_SIZE:].hex()
    print(f"    ブロック1: {blk1}")
    print(f"    ブロック2: {blk2}")
    print(f"    同一パターン漏洩: {blk1 == blk2}")

    # CBC Mode
    demo("CBC モード")

    def cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
        ct = b""
        prev = iv
        for i in range(0, len(plaintext), BLOCK_SIZE):
            block = plaintext[i:i + BLOCK_SIZE]
            xored = xor_bytes(block, prev)
            encrypted = simple_block_encrypt(xored, key)
            ct += encrypted
            prev = encrypted
        return ct

    def cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
        pt = b""
        prev = iv
        for i in range(0, len(ciphertext), BLOCK_SIZE):
            block = ciphertext[i:i + BLOCK_SIZE]
            decrypted = simple_block_decrypt(block, key)
            pt += xor_bytes(decrypted, prev)
            prev = block
        return pt

    iv = os.urandom(BLOCK_SIZE)
    ct_cbc = cbc_encrypt(msg_ecb, key, iv)
    pt_cbc = cbc_decrypt(ct_cbc, key, iv)
    print(f"    CBC暗号文: {ct_cbc.hex()}")
    print(f"    CBC復号:   {pt_cbc}")
    print(f"    同一ブロックでもCBC暗号文は異なる: "
          f"{ct_cbc[:BLOCK_SIZE].hex() != ct_cbc[BLOCK_SIZE:].hex()}")

    # CTR Mode
    demo("CTR モード")

    def ctr_encrypt(plaintext: bytes, key: bytes, nonce: bytes) -> bytes:
        ct = b""
        for i in range(0, len(plaintext), BLOCK_SIZE):
            counter = nonce[:4] + struct.pack(">I", i // BLOCK_SIZE)
            keystream = simple_block_encrypt(counter, key)
            block = plaintext[i:i + BLOCK_SIZE]
            ct += xor_bytes(block, keystream[:len(block)])
        return ct

    nonce = os.urandom(4)
    ct_ctr = ctr_encrypt(msg_ecb, key, nonce)
    pt_ctr = ctr_encrypt(ct_ctr, key, nonce)  # CTR は暗復号同じ
    print(f"    CTR暗号文: {ct_ctr.hex()}")
    print(f"    CTR復号:   {pt_ctr}")

    # --- PKCS7 Padding ---
    demo("PKCS#7 パディング")

    def pkcs7_pad(data: bytes, block_size: int) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    def pkcs7_unpad(data: bytes) -> bytes:
        pad_len = data[-1]
        if pad_len == 0 or pad_len > len(data):
            raise ValueError("Invalid padding")
        if data[-pad_len:] != bytes([pad_len] * pad_len):
            raise ValueError("Invalid padding")
        return data[:-pad_len]

    original = b"Hello!"
    padded = pkcs7_pad(original, 8)
    unpadded = pkcs7_unpad(padded)
    print(f"    元データ ({len(original)}B): {original}")
    print(f"    パディング後 ({len(padded)}B): {padded.hex()}")
    print(f"    パディング除去: {unpadded}")

    # --- AEAD Concept ---
    demo("AEAD (Authenticated Encryption with Associated Data)")
    print("""
    暗号化 + 認証を同時に行う。GCM が事実上の標準。

    ┌─────────────────────────────────────────────────┐
    │  AEAD = Encrypt(key, nonce, plaintext, aad)     │
    │  → (ciphertext, tag)                            │
    │                                                 │
    │  AAD (Associated Data): 暗号化しないが認証する  │
    │  例: HTTPヘッダ、IPアドレス                     │
    │  tag: 改竄検知用の認証タグ (128bit)             │
    └─────────────────────────────────────────────────┘

    AES-256-GCM: 現代の標準 (TLS 1.3, AWS KMS, etc.)
    ChaCha20-Poly1305: モバイル/IoT 向け (ソフトウェア実装が高速)
    """)


# ============================================================
# 第3章: ハッシュ関数 (Hash Functions)
# ============================================================
def chapter3_hash_functions():
    section("第3章: ハッシュ関数")
    print("""
    任意長の入力を固定長の出力に変換する一方向関数。
    3つの安全性要件:
    1. 原像耐性: H(x) = h から x を求められない
    2. 第二原像耐性: H(x1) = H(x2) となる x2 を見つけられない
    3. 衝突耐性: H(x1) = H(x2) となる (x1, x2) の組を見つけられない
    """)

    # --- Merkle-Damgård Construction ---
    demo("Merkle-Damgård 構造")
    print("""
    SHA-1/SHA-256 の基本構造:

      メッセージ → [パディング] → [ブロック分割]
                                      ↓
      IV → [f] → [f] → [f] → ... → ハッシュ値
            ↑      ↑      ↑
           M1     M2     M3

    - 各ステップで圧縮関数 f(H_i-1, M_i) を適用
    - 長さ拡張攻撃 (length extension) に脆弱
      → SHA-3 (スポンジ構造) で解決
    """)

    # --- Simplified SHA-256 style ---
    demo("SHA-256 の動作確認")

    test_inputs = [b"hello", b"hello!", b"Hello"]
    for inp in test_inputs:
        h = hashlib.sha256(inp).hexdigest()
        print(f"    SHA-256('{inp.decode()}') = {h[:32]}...")

    print("\n    雪崩効果 (Avalanche Effect):")
    h1 = hashlib.sha256(b"test1").digest()
    h2 = hashlib.sha256(b"test2").digest()
    diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(h1, h2))
    print(f"    'test1' vs 'test2': {diff_bits}/256 ビットが異なる "
          f"({diff_bits/256*100:.1f}%)")

    # --- Birthday Paradox ---
    demo("誕生日のパラドックスと衝突攻撃")
    print("""
    n ビットハッシュの衝突を見つけるのに必要な試行回数:
    - ブルートフォース (原像攻撃):  O(2^n)
    - 誕生日攻撃 (衝突攻撃):       O(2^(n/2))

    ┌──────────┬──────────┬──────────────┐
    │ アルゴリズム │ 出力長  │ 衝突攻撃強度  │
    ├──────────┼──────────┼──────────────┤
    │ MD5      │ 128 bit  │ 2^64 (破られた) │
    │ SHA-1    │ 160 bit  │ 2^80 (破られた) │
    │ SHA-256  │ 256 bit  │ 2^128 (安全)    │
    │ SHA-3    │ 256 bit  │ 2^128 (安全)    │
    └──────────┴──────────┴──────────────┘
    """)

    # Birthday paradox simulation with small hash
    demo("誕生日攻撃シミュレーション (16ビットハッシュ)")

    def small_hash(data: bytes) -> int:
        """16ビットハッシュ (教育用)"""
        return int(hashlib.sha256(data).hexdigest()[:4], 16)

    seen: Dict[int, bytes] = {}
    attempts = 0
    collision_found = False
    for i in range(100000):
        data = struct.pack(">I", i)
        h = small_hash(data)
        attempts += 1
        if h in seen and seen[h] != data:
            print(f"    衝突発見! 試行回数: {attempts}")
            print(f"    入力1: {seen[h].hex()} → hash: 0x{h:04X}")
            print(f"    入力2: {data.hex()} → hash: 0x{h:04X}")
            collision_found = True
            break
        seen[h] = data

    if collision_found:
        expected = int(math.sqrt(2 * 65536))
        print(f"    理論的期待値: ~{expected} (√(2 * 2^16))")

    # --- HMAC ---
    demo("HMAC (Hash-based Message Authentication Code)")
    print("""
    HMAC-SHA256(key, msg) = SHA256((key ⊕ opad) || SHA256((key ⊕ ipad) || msg))

    用途: メッセージ認証 (API 署名, JWT, Webhook 検証)
    """)

    secret = b"my-secret-key"
    message = b"important-data"
    tag = hmac.new(secret, message, hashlib.sha256).hexdigest()
    print(f"    HMAC-SHA256: {tag[:40]}...")

    # Verify
    received_tag = tag
    is_valid = hmac.compare_digest(
        hmac.new(secret, message, hashlib.sha256).hexdigest(),
        received_tag
    )
    print(f"    検証結果: {is_valid}")
    print("""
    重要: hmac.compare_digest() を使うこと!
    通常の == 比較はタイミング攻撃に脆弱。
    """)

    # --- Password Hashing ---
    demo("パスワードハッシュ (bcrypt / scrypt / Argon2)")
    print("""
    パスワード保存には専用のハッシュ関数を使う:

    ┌──────────┬──────────────────────────────────────────┐
    │ 関数     │ 特徴                                     │
    ├──────────┼──────────────────────────────────────────┤
    │ bcrypt   │ Blowfish ベース。cost factor で速度調整  │
    │ scrypt   │ メモリハード。GPU 攻撃に強い             │
    │ Argon2id │ 最新推奨。メモリ + CPU ハード             │
    └──────────┴──────────────────────────────────────────┘

    なぜ SHA-256 ではダメか:
    - 高速すぎる → GPU で毎秒数十億回ハッシュ可能
    - ソルトなし → レインボーテーブル攻撃
    - ストレッチングなし → ブルートフォースが容易
    """)

    # PBKDF2 demo (標準ライブラリで利用可能)
    password = b"my-secure-password"
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password, salt, 100000)
    print(f"    PBKDF2-SHA256 (100000 iterations):")
    print(f"    Salt:   {salt.hex()}")
    print(f"    Hash:   {dk.hex()[:40]}...")


# ============================================================
# 第4章: RSA 暗号
# ============================================================
def chapter4_rsa():
    section("第4章: RSA 暗号")
    print("""
    1977年 Rivest, Shamir, Adleman が発明。
    大きな整数の素因数分解の困難性に基づく公開鍵暗号。
    """)

    # --- Key Generation ---
    demo("RSA 鍵生成 (スクラッチ実装)")

    def generate_prime_simple(bits: int) -> int:
        """素数生成 (教育用の小さなビット数)"""
        while True:
            n = random.getrandbits(bits) | (1 << (bits - 1)) | 1
            if all(n % p != 0 for p in [2, 3, 5, 7, 11, 13, 17, 19, 23]):
                if pow(2, n - 1, n) == 1:  # Fermat test
                    return n

    def extended_gcd_local(a: int, b: int) -> Tuple[int, int, int]:
        if a == 0:
            return b, 0, 1
        g, x1, y1 = extended_gcd_local(b % a, a)
        return g, y1 - (b // a) * x1, x1

    def mod_inverse_local(e: int, phi: int) -> int:
        g, x, _ = extended_gcd_local(e % phi, phi)
        if g != 1:
            raise ValueError("No inverse")
        return x % phi

    # Generate keys
    KEY_BITS = 32  # 教育用。実際は 2048 以上
    p = generate_prime_simple(KEY_BITS // 2)
    q = generate_prime_simple(KEY_BITS // 2)
    while p == q:
        q = generate_prime_simple(KEY_BITS // 2)

    n = p * q
    phi_n = (p - 1) * (q - 1)
    e = 65537  # 標準的な公開指数
    # e と phi_n が互いに素であることを確認
    while math.gcd(e, phi_n) != 1:
        p = generate_prime_simple(KEY_BITS // 2)
        q = generate_prime_simple(KEY_BITS // 2)
        n = p * q
        phi_n = (p - 1) * (q - 1)

    d = mod_inverse_local(e, phi_n)

    print(f"    p = {p}")
    print(f"    q = {q}")
    print(f"    n = p * q = {n}")
    print(f"    φ(n) = (p-1)(q-1) = {phi_n}")
    print(f"    e = {e}  (公開指数)")
    print(f"    d = {d}  (秘密指数)")
    print(f"    公開鍵: (n={n}, e={e})")
    print(f"    秘密鍵: (n={n}, d={d})")

    # --- Encrypt / Decrypt ---
    demo("RSA 暗号化・復号")
    print("""
    暗号化: c = m^e mod n
    復号:   m = c^d mod n
    """)

    message = 42
    ciphertext = pow(message, e, n)
    decrypted = pow(ciphertext, d, n)
    print(f"    平文 m = {message}")
    print(f"    暗号文 c = m^e mod n = {ciphertext}")
    print(f"    復号   m' = c^d mod n = {decrypted}")
    print(f"    m == m': {message == decrypted}")

    # --- Why RSA Works ---
    demo("なぜ RSA が動くのか (オイラーの定理)")
    print("""
    証明の骨子:
    ─────────────
    e * d ≡ 1 (mod φ(n))
    → e * d = 1 + k * φ(n)   (ある整数 k)

    復号: c^d = (m^e)^d = m^(e*d) = m^(1 + k*φ(n))
         = m * (m^φ(n))^k
         ≡ m * 1^k  (mod n)   ← オイラーの定理: m^φ(n) ≡ 1 (mod n)
         ≡ m (mod n)

    条件: gcd(m, n) = 1 (m が n の倍数でないこと)
    """)

    # Verify Euler's theorem
    test_m = 7
    euler_result = pow(test_m, phi_n, n)
    print(f"    検証: {test_m}^φ({n}) mod {n} = {euler_result} (≡ 1)")

    # --- Digital Signature ---
    demo("RSA デジタル署名")
    print("""
    署名:   sig = hash(msg)^d mod n  (秘密鍵で署名)
    検証:   hash(msg) == sig^e mod n  (公開鍵で検証)
    """)

    msg = b"This is an important document"
    msg_hash = int(hashlib.sha256(msg).hexdigest(), 16) % n
    signature = pow(msg_hash, d, n)
    verified_hash = pow(signature, e, n)
    print(f"    メッセージハッシュ (mod n): {msg_hash}")
    print(f"    署名:                      {signature}")
    print(f"    検証ハッシュ:              {verified_hash}")
    print(f"    署名有効: {msg_hash == verified_hash}")

    # --- OAEP Padding ---
    demo("OAEP パディングの重要性")
    print("""
    教科書 RSA (Textbook RSA) の問題:
    1. 決定的 → 同じ平文 = 同じ暗号文 (CPA 非安全)
    2. 乗法準同型 → E(m1) * E(m2) = E(m1*m2) (改竄可能)
    3. 小さな平文 → e 乗根で解ける (e=3, m^3 < n の場合)

    RSAES-OAEP (PKCS#1 v2.2):
    ┌───────────────────────────────────┐
    │  m → [パディング + ランダム性]   │
    │  → MGF (Mask Generation Func)    │
    │  → RSA 暗号化                    │
    └───────────────────────────────────┘
    - ランダムパディングで確率的暗号化
    - IND-CCA2 安全 (最強のモデル)
    - 実務では必ず OAEP を使うこと
    """)


# ============================================================
# 第5章: Diffie-Hellman & 楕円曲線暗号
# ============================================================
def chapter5_dh_and_ecc():
    section("第5章: Diffie-Hellman & 楕円曲線暗号 (ECC)")

    # --- Diffie-Hellman ---
    demo("Diffie-Hellman 鍵交換")
    print("""
    1976年 Diffie & Hellman。公開チャネルで共有秘密を確立。
    離散対数問題の困難性に基づく。

    プロトコル:
      公開: 素数 p, 生成元 g
      Alice: a (秘密) → A = g^a mod p を送信
      Bob:   b (秘密) → B = g^b mod p を送信
      共有秘密: Alice: B^a mod p = Bob: A^b mod p = g^(ab) mod p
    """)

    # Small DH demo
    p = 23  # 小さな素数 (教育用)
    g = 5   # 生成元

    # Alice
    a_private = random.randint(2, p - 2)
    A_public = pow(g, a_private, p)

    # Bob
    b_private = random.randint(2, p - 2)
    B_public = pow(g, b_private, p)

    # Shared secret
    alice_secret = pow(B_public, a_private, p)
    bob_secret = pow(A_public, b_private, p)

    print(f"    公開パラメータ: p={p}, g={g}")
    print(f"    Alice: 秘密鍵 a={a_private}, 公開値 A=g^a mod p = {A_public}")
    print(f"    Bob:   秘密鍵 b={b_private}, 公開値 B=g^b mod p = {B_public}")
    print(f"    Alice の共有秘密: B^a mod p = {alice_secret}")
    print(f"    Bob   の共有秘密: A^b mod p = {bob_secret}")
    print(f"    一致: {alice_secret == bob_secret}")

    # --- MITM Attack ---
    demo("中間者攻撃 (MITM) のデモ")
    print("""
    DH 単体では認証がない → MITM に脆弱。

    Alice ←→ [Mallory] ←→ Bob
    Mallory は Alice, Bob それぞれと別の鍵を共有し、
    中継時に平文を盗み見・改竄できる。
    """)

    # Mallory の攻撃
    m_private = random.randint(2, p - 2)
    M_public = pow(g, m_private, p)

    # Alice thinks she's talking to Bob, but gets Mallory's public key
    alice_shared_with_mallory = pow(M_public, a_private, p)
    mallory_shared_with_alice = pow(A_public, m_private, p)

    # Bob thinks he's talking to Alice, but gets Mallory's public key
    bob_shared_with_mallory = pow(M_public, b_private, p)
    mallory_shared_with_bob = pow(B_public, m_private, p)

    print(f"    Alice-Mallory 共有鍵: {alice_shared_with_mallory} == "
          f"{mallory_shared_with_alice}: "
          f"{alice_shared_with_mallory == mallory_shared_with_alice}")
    print(f"    Mallory-Bob   共有鍵: {mallory_shared_with_bob} == "
          f"{bob_shared_with_mallory}: "
          f"{mallory_shared_with_bob == bob_shared_with_mallory}")
    print("""
    対策: 認証付き DH が必要 → TLS ではサーバー証明書で認証
    """)

    # --- Elliptic Curve ---
    demo("楕円曲線暗号 (ECC) の基礎")
    print("""
    楕円曲線: y² = x³ + ax + b  (有限体 F_p 上)

    利点: RSA 2048bit ≒ ECC 256bit (同等セキュリティ)
    → 鍵サイズが小さい → モバイル・IoT に最適

    主要な曲線:
    ┌──────────────┬───────────────────────────────┐
    │ 曲線名       │ 用途                          │
    ├──────────────┼───────────────────────────────┤
    │ P-256        │ NIST 標準。TLS, AWS で広く使用│
    │ P-384        │ より高い安全性が必要な場合     │
    │ Curve25519   │ Daniel Bernstein 設計。高速    │
    │ secp256k1    │ Bitcoin で使用                 │
    │ Ed25519      │ 署名用。SSH, Signal で使用     │
    └──────────────┴───────────────────────────────┘
    """)

    # --- EC Point Addition over Finite Field ---
    demo("有限体上の楕円曲線点加算")
    print("""
    y² ≡ x³ + ax + b (mod p) 上の演算
    """)

    class ECPoint:
        """楕円曲線上の点"""
        def __init__(self, x: Optional[int], y: Optional[int],
                     a: int, b: int, p: int):
            self.x = x
            self.y = y
            self.a = a
            self.b = b
            self.p = p

        def is_infinity(self) -> bool:
            return self.x is None and self.y is None

        def __eq__(self, other) -> bool:
            return (self.x == other.x and self.y == other.y and
                    self.a == other.a and self.p == other.p)

        def __repr__(self) -> str:
            if self.is_infinity():
                return "O (infinity)"
            return f"({self.x}, {self.y})"

    def ec_add(P: ECPoint, Q: ECPoint) -> ECPoint:
        """楕円曲線上の点加算"""
        a, b, p = P.a, P.b, P.p

        if P.is_infinity():
            return Q
        if Q.is_infinity():
            return P

        if P.x == Q.x and P.y != Q.y:
            return ECPoint(None, None, a, b, p)  # 無限遠点

        if P == Q:
            # 接線の傾き
            lam = ((3 * P.x * P.x + a) * pow(2 * P.y, -1, p)) % p
        else:
            # 割線の傾き
            lam = ((Q.y - P.y) * pow(Q.x - P.x, -1, p)) % p

        x_r = (lam * lam - P.x - Q.x) % p
        y_r = (lam * (P.x - x_r) - P.y) % p
        return ECPoint(x_r, y_r, a, b, p)

    def ec_multiply(k: int, P: ECPoint) -> ECPoint:
        """スカラー倍算 (double-and-add)"""
        result = ECPoint(None, None, P.a, P.b, P.p)
        addend = P
        while k > 0:
            if k & 1:
                result = ec_add(result, addend)
            addend = ec_add(addend, addend)
            k >>= 1
        return result

    # 小さな曲線 y² = x³ + 2x + 3 mod 97
    a_ec, b_ec, p_ec = 2, 3, 97
    G = ECPoint(3, 6, a_ec, b_ec, p_ec)

    # Verify G is on the curve
    lhs = (G.y * G.y) % p_ec
    rhs = (G.x ** 3 + a_ec * G.x + b_ec) % p_ec
    print(f"    曲線: y² = x³ + {a_ec}x + {b_ec} mod {p_ec}")
    print(f"    基点 G = {G}")
    print(f"    曲線上の点か検証: {lhs} == {rhs}: {lhs == rhs}")

    P2 = ec_add(G, G)
    P3 = ec_add(P2, G)
    print(f"    2G = {P2}")
    print(f"    3G = {P3}")

    # ECDH
    demo("ECDH 鍵交換")

    alice_sk = random.randint(1, p_ec - 1)
    alice_pk = ec_multiply(alice_sk, G)

    bob_sk = random.randint(1, p_ec - 1)
    bob_pk = ec_multiply(bob_sk, G)

    alice_shared = ec_multiply(alice_sk, bob_pk)
    bob_shared = ec_multiply(bob_sk, alice_pk)

    print(f"    Alice: sk={alice_sk}, pk={alice_pk}")
    print(f"    Bob:   sk={bob_sk}, pk={bob_pk}")
    print(f"    Alice の共有秘密: {alice_shared}")
    print(f"    Bob   の共有秘密: {bob_shared}")
    print(f"    一致: {alice_shared == bob_shared}")

    # --- ECDSA Concept ---
    demo("ECDSA (楕円曲線デジタル署名)")
    print("""
    署名生成:
      1. ランダムな k を選び、R = kG を計算
      2. r = R.x mod n
      3. s = k^(-1) * (hash(msg) + r * privateKey) mod n
      4. 署名 = (r, s)

    署名検証:
      1. u1 = hash(msg) * s^(-1) mod n
      2. u2 = r * s^(-1) mod n
      3. P = u1*G + u2*publicKey
      4. P.x == r なら有効

    利点:
    - RSA 署名より鍵が短い (256bit vs 2048bit)
    - 署名生成が高速
    - TLS 1.3, SSH, Bitcoin, JWT (ES256) で使用
    """)


# ============================================================
# 第6章: PKI と証明書
# ============================================================
def chapter6_pki_certificates():
    section("第6章: PKI (公開鍵基盤) と証明書")

    demo("X.509 証明書の構造")
    print("""
    X.509 v3 証明書の主要フィールド:

    ┌─────────────────────────────────────────────────┐
    │ Version: v3                                     │
    │ Serial Number: (CA が一意に付与)                │
    │ Signature Algorithm: SHA256withRSA / ECDSA      │
    │ Issuer: CN=Let's Encrypt Authority X3           │
    │ Validity:                                       │
    │   Not Before: 2024-01-01 00:00:00 UTC           │
    │   Not After:  2024-03-31 23:59:59 UTC           │
    │ Subject: CN=example.com                         │
    │ Subject Public Key Info:                        │
    │   Algorithm: EC (P-256)                         │
    │   Public Key: 04:AB:CD:...                      │
    │ Extensions:                                     │
    │   Subject Alt Names: example.com, *.example.com │
    │   Key Usage: Digital Signature                  │
    │   Basic Constraints: CA:FALSE                   │
    │   Authority Key Identifier: ...                 │
    │   CRL Distribution Points: http://...           │
    │   Authority Info Access: OCSP: http://...       │
    │ Signature: (CA の秘密鍵で署名)                  │
    └─────────────────────────────────────────────────┘
    """)

    demo("証明書チェーン検証")
    print("""
    検証プロセス (ブラウザ / TLS クライアント):

    Root CA (自己署名, OS/ブラウザに組み込み)
      │  ↓ 署名
    Intermediate CA
      │  ↓ 署名
    Server Certificate (example.com)

    1. サーバー証明書の署名を中間CA公開鍵で検証
    2. 中間CA証明書の署名をルートCA公開鍵で検証
    3. ルートCA証明書がトラストストアに存在するか確認
    4. 有効期限チェック
    5. 失効チェック (CRL / OCSP)
    6. ドメイン名の一致確認
    """)

    # Simulated certificate chain
    class SimpleCert:
        def __init__(self, subject: str, issuer: str,
                     pub_key: int, is_ca: bool):
            self.subject = subject
            self.issuer = issuer
            self.pub_key = pub_key
            self.is_ca = is_ca
            self.signature_hash = hashlib.sha256(
                f"{subject}:{issuer}:{pub_key}".encode()
            ).hexdigest()[:16]

        def __repr__(self):
            kind = "CA" if self.is_ca else "End Entity"
            return f"[{kind}] {self.subject} (issued by: {self.issuer})"

    root = SimpleCert("Root CA", "Root CA", 1001, True)
    intermediate = SimpleCert("Intermediate CA", "Root CA", 2002, True)
    server = SimpleCert("example.com", "Intermediate CA", 3003, False)

    chain = [server, intermediate, root]
    trust_store = {"Root CA"}

    print("    証明書チェーン:")
    for i, cert in enumerate(chain):
        indent = "    " + "  " * i
        print(f"{indent}└─ {cert}")

    # Validate chain
    print("\n    チェーン検証シミュレーション:")
    valid = True
    for i in range(len(chain) - 1):
        cert = chain[i]
        issuer_cert = chain[i + 1]
        match = cert.issuer == issuer_cert.subject
        print(f"    {cert.subject} の発行者 '{cert.issuer}' == "
              f"'{issuer_cert.subject}': {'OK' if match else 'NG'}")
        valid = valid and match

    root_trusted = chain[-1].subject in trust_store
    print(f"    ルートCA '{chain[-1].subject}' がトラストストアに存在: "
          f"{'OK' if root_trusted else 'NG'}")
    valid = valid and root_trusted
    print(f"    チェーン検証結果: {'有効' if valid else '無効'}")

    # --- Certificate Transparency ---
    demo("Certificate Transparency (CT)")
    print("""
    CA が不正な証明書を発行した場合の検知機構。

    仕組み:
    1. CA は証明書を CT ログサーバーに登録
    2. CT ログは Merkle Tree で証明書を管理
    3. SCT (Signed Certificate Timestamp) を証明書に含める
    4. ブラウザは SCT を検証 → CT ログに登録されていない証明書を拒否

    実例:
    - 2011 DigiNotar 事件: 不正な *.google.com 証明書
    - 2015 Symantec 事件: Google 向け不正証明書
    → CT があれば即座に検知できた
    """)

    # --- Certificate Pinning ---
    demo("証明書ピンニング")
    print("""
    期待する証明書/公開鍵のハッシュをアプリに埋め込む。

    種類:
    1. 公開鍵ピンニング: 公開鍵の SHA-256 をピン留め
    2. 証明書ピンニング: 証明書全体をピン留め

    ┌──────────────────────────────────────────────┐
    │  pin-sha256 = Base64(SHA-256(公開鍵の DER))  │
    └──────────────────────────────────────────────┘

    注意:
    - バックアップピンを必ず設定 (証明書更新時の障害防止)
    - HPKP (HTTP Public Key Pinning) は非推奨化 (Chrome 72)
    - 現在はモバイルアプリ内ピンニングが主流
    """)


# ============================================================
# 第7章: TLS 1.3
# ============================================================
def chapter7_tls13():
    section("第7章: TLS 1.3 ハンドシェイク")

    demo("TLS 1.3 フルハンドシェイク (1-RTT)")
    print("""
    TLS 1.2 は 2-RTT だったが、TLS 1.3 は 1-RTT に短縮。
    不要な暗号スイートの排除で大幅に簡素化。

    Client                                    Server
      │                                          │
      │ ── ClientHello ──────────────────────────→│  ┐
      │    supported_versions: TLS 1.3            │  │
      │    cipher_suites: [AES_256_GCM_SHA384,    │  │
      │                    CHACHA20_POLY1305]      │  │
      │    key_share: ECDHE(X25519) 公開値         │  │
      │    signature_algorithms: [ECDSA_P256,     │  │
      │                           RSA_PSS_SHA256] │  │
      │                                          │  │ 1-RTT
      │ ←────────── ServerHello ──────────────── │  │
      │    selected_cipher: AES_256_GCM_SHA384    │  │
      │    key_share: ECDHE(X25519) 公開値         │  │
      │ ←── {EncryptedExtensions} ───────────── │  │
      │ ←── {Certificate} ──────────────────── │  │
      │ ←── {CertificateVerify} ─────────────── │  │
      │ ←── {Finished} ─────────────────────── │  │
      │                                          │  │
      │ ── {Finished} ──────────────────────────→│  ┘
      │                                          │
      │ ══ Application Data (encrypted) ════════│
    """)

    # TLS 1.3 Handshake Simulation
    demo("ハンドシェイクシミュレーション")

    class TLS13Handshake:
        def __init__(self):
            self.transcript: List[str] = []
            self.client_random = os.urandom(32)
            self.server_random = os.urandom(32)

        def client_hello(self) -> dict:
            msg = {
                "type": "ClientHello",
                "version": "TLS 1.3",
                "random": self.client_random.hex()[:16] + "...",
                "cipher_suites": [
                    "TLS_AES_256_GCM_SHA384",
                    "TLS_CHACHA20_POLY1305_SHA256",
                ],
                "key_share": "X25519 ephemeral public key",
                "signature_algorithms": ["ecdsa_secp256r1_sha256"],
            }
            self.transcript.append("ClientHello")
            return msg

        def server_hello(self) -> dict:
            msg = {
                "type": "ServerHello",
                "version": "TLS 1.3",
                "random": self.server_random.hex()[:16] + "...",
                "selected_cipher": "TLS_AES_256_GCM_SHA384",
                "key_share": "X25519 ephemeral public key",
            }
            self.transcript.append("ServerHello")
            return msg

        def derive_keys(self) -> dict:
            """HKDF ベースの鍵スケジュール (簡略版)"""
            # 実際は ECDHE 共有秘密から導出
            shared_secret = hashlib.sha256(
                self.client_random + self.server_random
            ).digest()

            # HKDF-Extract
            early_secret = hmac.new(
                b"\x00" * 32, b"\x00" * 32, hashlib.sha256
            ).digest()

            # Handshake Secret
            hs_secret = hmac.new(
                early_secret, shared_secret, hashlib.sha256
            ).digest()

            # Traffic keys
            client_key = hmac.new(
                hs_secret, b"client_traffic", hashlib.sha256
            ).digest()
            server_key = hmac.new(
                hs_secret, b"server_traffic", hashlib.sha256
            ).digest()

            return {
                "handshake_secret": hs_secret.hex()[:24] + "...",
                "client_traffic_key": client_key.hex()[:24] + "...",
                "server_traffic_key": server_key.hex()[:24] + "...",
            }

    tls = TLS13Handshake()
    ch = tls.client_hello()
    sh = tls.server_hello()
    keys = tls.derive_keys()

    print(f"    ClientHello: cipher_suites={ch['cipher_suites']}")
    print(f"    ServerHello: selected={sh['selected_cipher']}")
    print(f"    鍵導出:")
    for k, v in keys.items():
        print(f"      {k}: {v}")

    # --- HKDF Key Schedule ---
    demo("HKDF 鍵スケジュール")
    print("""
    TLS 1.3 は HKDF (HMAC-based KDF) で全鍵を導出:

    PSK ─→ HKDF-Extract ─→ Early Secret
                              │
    ECDHE ─→ HKDF-Extract ─→ Handshake Secret
                              │
                 HKDF-Extract ─→ Master Secret
                              │
                 HKDF-Expand ──→ client_traffic_key
                              ├──→ server_traffic_key
                              ├──→ client_traffic_iv
                              └──→ server_traffic_iv

    HKDF-Extract(salt, IKM) → PRK (疑似ランダム鍵)
    HKDF-Expand(PRK, info, L) → OKM (出力鍵材料)
    """)

    # --- 0-RTT ---
    demo("0-RTT (Early Data)")
    print("""
    再接続時に 0-RTT でデータ送信可能 (PSK ベース):

    Client                        Server
      │ ── ClientHello ──────────→│
      │    + early_data            │  ← 0-RTT!
      │    + pre_shared_key        │
      │                            │
      │ ←── ServerHello ─────── │
      │ ←── {Finished} ─────── │

    リスク: リプレイ攻撃に脆弱
    → 0-RTT データは冪等な操作のみに使用すべき
       (GET は OK、POST での決済は NG)
    """)

    # --- PFS ---
    demo("Perfect Forward Secrecy (PFS)")
    print("""
    エフェメラル ECDHE により PFS を実現:

    - 各セッションで新しい DH 鍵ペアを生成
    - サーバーの長期秘密鍵が漏洩しても、
      過去のセッション鍵は安全

    TLS 1.2 の問題:
    - RSA 鍵交換 → PFS なし (サーバー鍵漏洩で全セッション復号)
    - DHE/ECDHE → PFS あり (オプション)

    TLS 1.3 の改善:
    - RSA 鍵交換を廃止 → 全セッションで PFS を強制
    - ECDHE が必須
    """)

    # --- TLS 1.2 vs 1.3 ---
    demo("TLS 1.2 vs TLS 1.3 比較")
    print("""
    ┌────────────────┬─────────────────┬─────────────────┐
    │ 項目           │ TLS 1.2         │ TLS 1.3         │
    ├────────────────┼─────────────────┼─────────────────┤
    │ RTT            │ 2-RTT           │ 1-RTT (0-RTT)   │
    │ 鍵交換         │ RSA/DHE/ECDHE   │ ECDHE のみ      │
    │ PFS            │ オプション       │ 必須             │
    │ 暗号スイート   │ ~37 種類        │ 5 種類           │
    │ ハッシュ       │ MD5/SHA-1 可    │ SHA-256/384 のみ │
    │ AEAD           │ オプション       │ 必須             │
    │ 圧縮           │ あり (CRIME)    │ 廃止             │
    │ 再ネゴ         │ あり            │ 廃止             │
    │ ServerHello後  │ 平文            │ 暗号化           │
    └────────────────┴─────────────────┴─────────────────┘

    TLS 1.3 で廃止されたもの:
    - RC4, DES, 3DES, AES-CBC
    - RSA 鍵交換
    - SHA-1 署名
    - 圧縮 (CRIME 攻撃対策)
    - 再ネゴシエーション (Triple Handshake 攻撃対策)
    """)


# ============================================================
# 第8章: 応用パターン (Applied Patterns)
# ============================================================
def chapter8_applied_patterns():
    section("第8章: 暗号の応用パターン")

    # --- CSPRNG ---
    demo("CSPRNG (暗号学的に安全な疑似乱数生成器)")
    print("""
    暗号用途には os.urandom() / secrets モジュールを使う。
    random モジュールは Mersenne Twister → 予測可能で危険。

    Python での正しい使い方:
    """)

    token = secrets.token_hex(32)
    url_token = secrets.token_urlsafe(32)
    api_key = secrets.token_hex(16)
    print(f"    secrets.token_hex(32):     {token[:32]}...")
    print(f"    secrets.token_urlsafe(32): {url_token[:32]}...")
    print(f"    API Key 例:                {api_key}")
    print("""
    NG: random.randint()  → 暗号用途に使ってはいけない
    OK: secrets.randbelow(), secrets.token_bytes()
    """)

    # --- KDF ---
    demo("KDF (鍵導出関数)")
    print("""
    パスワードや共有秘密から暗号鍵を導出する。

    ┌──────────┬───────────────────────────────────────┐
    │ 関数     │ 用途                                  │
    ├──────────┼───────────────────────────────────────┤
    │ HKDF     │ 暗号学的に強い入力からの鍵導出        │
    │ PBKDF2   │ パスワードからの鍵導出 (ストレッチ)   │
    │ scrypt   │ メモリハードな鍵導出                  │
    │ Argon2   │ 最新推奨のパスワードハッシュ/KDF      │
    └──────────┴───────────────────────────────────────┘
    """)

    # HKDF-like using hmac
    def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
        return hmac.new(salt, ikm, hashlib.sha256).digest()

    def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
        """HKDF-Expand (RFC 5869)"""
        blocks = []
        prev = b""
        i = 1
        while len(b"".join(blocks)) < length:
            prev = hmac.new(
                prk, prev + info + bytes([i]), hashlib.sha256
            ).digest()
            blocks.append(prev)
            i += 1
        return b"".join(blocks)[:length]

    salt = os.urandom(32)
    ikm = os.urandom(32)  # Input Key Material
    prk = hkdf_extract(salt, ikm)
    okm = hkdf_expand(prk, b"encryption-key", 32)

    print(f"    HKDF-Extract PRK: {prk.hex()[:32]}...")
    print(f"    HKDF-Expand OKM:  {okm.hex()[:32]}...")

    # --- Envelope Encryption ---
    demo("エンベロープ暗号化 (AWS KMS パターン)")
    print("""
    大量データの暗号化に使う 2 層構造:

    ┌───────────────────────────────────────────────┐
    │  1. KMS で Master Key (CMK) を管理            │
    │  2. GenerateDataKey API で Data Key を取得    │
    │     - 平文の Data Key (暗号化に使用後破棄)    │
    │     - 暗号化された Data Key (データと一緒に保存)│
    │  3. Data Key でデータを AES-256-GCM 暗号化   │
    │  4. 復号時: KMS で暗号化 Data Key を復号      │
    │            → 平文 Data Key でデータ復号       │
    └───────────────────────────────────────────────┘

    利点:
    - Master Key は KMS 外に出ない (HSM 内)
    - 大量データを KMS に送る必要がない
    - Data Key のローテーションが容易
    """)

    class SimpleKMS:
        """エンベロープ暗号化の概念デモ"""
        def __init__(self):
            self.master_key = os.urandom(32)

        def generate_data_key(self) -> Tuple[bytes, bytes]:
            """(平文DataKey, 暗号化DataKey)"""
            data_key = os.urandom(32)
            # Master Key で Data Key を暗号化 (簡略版)
            encrypted_dk = bytes(
                a ^ b for a, b in zip(data_key, self.master_key)
            )
            return data_key, encrypted_dk

        def decrypt_data_key(self, encrypted_dk: bytes) -> bytes:
            return bytes(
                a ^ b for a, b in zip(encrypted_dk, self.master_key)
            )

    kms = SimpleKMS()
    plaintext_dk, encrypted_dk = kms.generate_data_key()

    # Encrypt data with data key
    data = b"Sensitive customer data here!!!"
    ct = bytes(a ^ b for a, b in zip(
        data, (plaintext_dk * 2)[:len(data)]
    ))

    # Decrypt
    recovered_dk = kms.decrypt_data_key(encrypted_dk)
    recovered_data = bytes(a ^ b for a, b in zip(
        ct, (recovered_dk * 2)[:len(ct)]
    ))

    print(f"    平文 Data Key:   {plaintext_dk.hex()[:24]}...")
    print(f"    暗号化 Data Key: {encrypted_dk.hex()[:24]}...")
    print(f"    暗号化データ:    {ct.hex()[:24]}...")
    print(f"    復号データ:      {recovered_data}")
    print(f"    一致: {data == recovered_data}")

    # --- Zero-Knowledge Proof (Schnorr) ---
    demo("ゼロ知識証明 (Schnorr プロトコル 簡略版)")
    print("""
    「秘密を知っている」ことを、秘密自体を明かさずに証明する。

    Schnorr 識別プロトコル:
    - 公開: 素数 p, 生成元 g, 公開鍵 y = g^x mod p
    - 証明者は秘密鍵 x を知っていることを証明

    1. 証明者: ランダムな r を選び、t = g^r mod p を送信
    2. 検証者: ランダムなチャレンジ c を送信
    3. 証明者: s = r + c*x mod (p-1) を送信
    4. 検証者: g^s ≡ t * y^c (mod p) を確認
    """)

    p_zk = 23
    g_zk = 5
    x_secret = 7  # 秘密鍵
    y_public = pow(g_zk, x_secret, p_zk)  # 公開鍵

    # Protocol execution
    r = random.randint(1, p_zk - 2)
    t = pow(g_zk, r, p_zk)              # Commitment
    c = random.randint(1, p_zk - 2)     # Challenge
    s = (r + c * x_secret) % (p_zk - 1) # Response

    # Verification
    lhs = pow(g_zk, s, p_zk)
    rhs = (t * pow(y_public, c, p_zk)) % p_zk

    print(f"    公開パラメータ: p={p_zk}, g={g_zk}")
    print(f"    公開鍵 y = g^x mod p = {y_public}")
    print(f"    1. Commitment t = g^r mod p = {t}")
    print(f"    2. Challenge c = {c}")
    print(f"    3. Response  s = r + c*x mod (p-1) = {s}")
    print(f"    4. 検証: g^s = {lhs}, t*y^c = {rhs}")
    print(f"    結果: {'証明成功 (秘密を明かさずに知識を証明)' if lhs == rhs else '証明失敗'}")
    print("""
    応用例:
    - パスワードレス認証
    - ブロックチェーンのプライバシー (Zcash: zk-SNARKs)
    - 年齢確認 (「18歳以上」を生年月日を明かさずに証明)
    """)


# ============================================================
# 第9章: 学習優先度 (Tier 1-4)
# ============================================================
def chapter9_priority():
    section("第9章: 暗号技術の学習優先度")
    print("""
    ┌────────────────────────────────────────────────────────┐
    │  Tier 1 (必須 - 面接で必ず聞かれる)                   │
    ├────────────────────────────────────────────────────────┤
    │  ・対称鍵 vs 公開鍵の違いと使い分け                   │
    │  ・AES-256-GCM (AEAD の標準)                          │
    │  ・TLS 1.3 ハンドシェイクの流れ                       │
    │  ・ハッシュ関数の性質 (SHA-256, HMAC)                 │
    │  ・証明書チェーン検証                                 │
    │  ・パスワードハッシュ (bcrypt/Argon2)                 │
    └────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │  Tier 2 (重要 - システム設計面接で差がつく)           │
    ├────────────────────────────────────────────────────────┤
    │  ・RSA の仕組み (鍵生成, 暗号化, 署名)               │
    │  ・ECDHE / PFS の概念                                │
    │  ・エンベロープ暗号化 (KMS パターン)                  │
    │  ・CSPRNG の重要性                                    │
    │  ・PKI / CA の信頼モデル                              │
    └────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │  Tier 3 (発展 - セキュリティ専門職向け)               │
    ├────────────────────────────────────────────────────────┤
    │  ・楕円曲線暗号の数学的背景                           │
    │  ・ブロック暗号モードの詳細 (CBC, CTR)                │
    │  ・HKDF 鍵スケジュール                               │
    │  ・Certificate Transparency                          │
    │  ・0-RTT のリプレイ攻撃リスク                        │
    └────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────┐
    │  Tier 4 (専門研究 - 暗号研究者/プロトコル設計者)      │
    ├────────────────────────────────────────────────────────┤
    │  ・AES の内部構造 (SubBytes, MixColumns)              │
    │  ・Feistel ネットワークの安全性証明                   │
    │  ・ゼロ知識証明 (zk-SNARKs/STARKs)                   │
    │  ・ポスト量子暗号 (CRYSTALS-Kyber, Dilithium)        │
    │  ・形式検証 (ProVerif, Tamarin)                       │
    └────────────────────────────────────────────────────────┘

    [面接 Tips]
    ・「TLS ハンドシェイクを説明してください」→ 1-RTT の図を描ける
    ・「HTTPS はなぜ安全か」→ 証明書チェーン + ECDHE + AEAD
    ・「パスワードの保存方法」→ Argon2id + ソルト + ペッパー
    ・「暗号化と署名の違い」→ 公開鍵/秘密鍵の使い方が逆
    """)


# ============================================================
# メイン
# ============================================================
def main():
    print(f"\n{'━' * 60}")
    print("  Applied Cryptography Fundamentals")
    print("  暗号技術の基礎から TLS 1.3 まで")
    print(f"{'━' * 60}")

    chapter1_math_foundations()
    chapter2_symmetric_crypto()
    chapter3_hash_functions()
    chapter4_rsa()
    chapter5_dh_and_ecc()
    chapter6_pki_certificates()
    chapter7_tls13()
    chapter8_applied_patterns()
    chapter9_priority()

    print(f"\n{SEP}")
    print("  学習完了!")
    print("  次のステップ: security_deep_dive.py で攻撃手法を学ぶ")
    print(SEP)


if __name__ == "__main__":
    main()
