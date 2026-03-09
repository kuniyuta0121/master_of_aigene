"""
セキュリティエンジニアリング Deep Dive
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAANG レベルのセキュリティ知識を体系的に学ぶ

実行: python security_deep_dive.py
依存: 標準ライブラリのみ (hashlib, hmac, secrets, base64, json, time)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
import hmac
import secrets
import base64
import json
import time
import re
import struct
from typing import Dict, List, Optional, Tuple
from enum import Enum

SEP = "━" * 60


# ============================================================
# 第1章: OWASP Top 10 (2021)
# ============================================================
def chapter1_owasp_top10():
    print(f"\n{SEP}")
    print("第1章: OWASP Top 10 (2021)")
    print(f"{SEP}")
    print("""
OWASP Top 10 はWebアプリケーションの最も重大なセキュリティリスクを
定義するグローバル標準。FAANG面接では具体的なコード例で説明できることが必須。
""")

    # --- A01: Broken Access Control ---
    print(f"\n{'─' * 40}")
    print("A01: Broken Access Control（アクセス制御の不備）")
    print(f"{'─' * 40}")
    print("""
最も多い脆弱性。IDOR (Insecure Direct Object Reference) が典型例。
""")

    # 脆弱なコード
    print("[脆弱なコード] IDOR の例:")
    print("""
    # GET /api/users/123/profile
    def get_profile_vulnerable(user_id_from_url):
        # URLのIDをそのまま使う → 他人のプロフィールが見れる！
        return db.query(f"SELECT * FROM users WHERE id = {user_id_from_url}")
    """)

    # 安全なコード
    print("[安全なコード] 適切なアクセス制御:")
    print("""
    def get_profile_secure(user_id_from_url, authenticated_user):
        # 認証済みユーザーのIDと一致するか検証
        if user_id_from_url != authenticated_user.id:
            if not authenticated_user.has_role('ADMIN'):
                raise PermissionError("アクセス権限がありません")
        return db.query("SELECT * FROM users WHERE id = %s", (user_id_from_url,))
    """)

    # 権限昇格の例
    print("[脆弱なコード] Privilege Escalation:")
    print("""
    # POST /api/users  body: {"name": "Eve", "role": "admin"}
    def create_user_vulnerable(request_body):
        # リクエストボディをそのまま保存 → role: admin を注入可能！
        db.insert("users", request_body)
    """)
    print("[安全なコード] ホワイトリスト方式:")
    print("""
    def create_user_secure(request_body, authenticated_user):
        allowed_fields = ['name', 'email']  # roleは含めない
        safe_data = {k: v for k, v in request_body.items() if k in allowed_fields}
        safe_data['role'] = 'user'  # デフォルトロールを強制
        db.insert("users", safe_data)
    """)

    # --- A02: Cryptographic Failures ---
    print(f"\n{'─' * 40}")
    print("A02: Cryptographic Failures（暗号化の失敗）")
    print(f"{'─' * 40}")

    print("[脆弱なコード] MD5でパスワードハッシュ:")
    weak_hash = hashlib.md5(b"password123").hexdigest()
    print(f"  MD5('password123') = {weak_hash}")
    print("  → レインボーテーブルで即座に復元される")

    print("\n[安全なコード] ソルト付きSHA-256（本番はbcrypt/argon2推奨）:")
    salt = secrets.token_hex(16)
    strong_hash = hashlib.sha256((salt + "password123").encode()).hexdigest()
    print(f"  salt = {salt}")
    print(f"  SHA-256(salt + password) = {strong_hash}")
    print("  → ソルトがあるためレインボーテーブル攻撃は無効")

    # --- A03: Injection ---
    print(f"\n{'─' * 40}")
    print("A03: Injection（インジェクション）")
    print(f"{'─' * 40}")

    print("[脆弱なコード] SQL Injection:")
    print("""
    def login_vulnerable(username, password):
        query = f"SELECT * FROM users WHERE name='{username}' AND pass='{password}'"
        # 入力: username = "admin' OR '1'='1' --"
        # 実行されるSQL: SELECT * FROM users WHERE name='admin' OR '1'='1' --' AND pass=''
        # → 全ユーザーが返される
    """)

    print("[安全なコード] パラメータ化クエリ:")
    print("""
    def login_secure(username, password):
        query = "SELECT * FROM users WHERE name = %s AND pass = %s"
        cursor.execute(query, (username, password))
        # → SQLインジェクション不可能
    """)

    print("[脆弱なコード] Command Injection:")
    print("""
    import os
    def ping_vulnerable(host):
        os.system(f"ping -c 1 {host}")
        # 入力: host = "8.8.8.8; rm -rf /"  → 致命的！
    """)

    print("[安全なコード] subprocess + シェル無効化:")
    print("""
    import subprocess, shlex
    def ping_secure(host):
        if not re.match(r'^[a-zA-Z0-9.\\-]+$', host):
            raise ValueError("不正なホスト名")
        subprocess.run(["ping", "-c", "1", host], shell=False)
    """)

    # --- A07: Authentication Failures ---
    print(f"\n{'─' * 40}")
    print("A07: Identification and Authentication Failures")
    print(f"{'─' * 40}")
    print("""
    [脆弱なパターン]
    - パスワード最小長なし / 複雑性要件なし
    - ブルートフォース対策なし (レート制限なし)
    - セッション固定攻撃に脆弱
    - パスワードリセットトークンが推測可能

    [安全なパターン]
    - パスワードポリシー強制 + bcrypt/argon2
    - アカウントロックアウト + レート制限
    - ログイン成功時にセッションID再生成
    - cryptographically random なリセットトークン
    - 多要素認証 (MFA) 必須化
    """)

    # --- A09: Security Logging & Monitoring ---
    print(f"\n{'─' * 40}")
    print("A09: Security Logging and Monitoring Failures")
    print(f"{'─' * 40}")

    print("[実装例] セキュリティイベントログ:")

    class SecurityLogger:
        """セキュリティイベントを構造化ログとして記録"""
        def __init__(self):
            self.logs: List[dict] = []

        def log_event(self, event_type: str, user: str, detail: str,
                      severity: str = "INFO"):
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "event_type": event_type,
                "user": user,
                "detail": detail,
                "severity": severity,
            }
            self.logs.append(entry)
            return entry

        def detect_brute_force(self, user: str, window_sec: int = 300,
                               threshold: int = 5) -> bool:
            """一定期間内のログイン失敗回数で検知"""
            now = time.time()
            failures = [
                log for log in self.logs
                if log["event_type"] == "LOGIN_FAILURE"
                and log["user"] == user
            ]
            return len(failures) >= threshold

    logger = SecurityLogger()
    logger.log_event("LOGIN_FAILURE", "eve", "Invalid password", "WARNING")
    logger.log_event("LOGIN_FAILURE", "eve", "Invalid password", "WARNING")
    logger.log_event("LOGIN_SUCCESS", "alice", "Login from 10.0.0.1")
    logger.log_event("PRIVILEGE_ESCALATION", "eve", "Attempted admin access", "CRITICAL")

    print(f"  ログエントリ数: {len(logger.logs)}")
    for log in logger.logs:
        print(f"  [{log['severity']}] {log['event_type']}: {log['user']} - {log['detail']}")

    print("""
    考えてほしい疑問:
    「なぜログにパスワード自体を記録してはいけないのか？」
    「ログの改ざんを防ぐにはどうすればよいか？」
    → 答え: 平文パスワードがログから漏洩する。ログはappend-onlyストレージ
      (例: S3 Object Lock) に保存し、HMACで完全性を保証する。
    """)


# ============================================================
# 第2章: 暗号学の基礎
# ============================================================
def chapter2_cryptography():
    print(f"\n{SEP}")
    print("第2章: 暗号学の基礎")
    print(f"{SEP}")

    # --- ハッシュ関数 ---
    print(f"\n{'─' * 40}")
    print("2.1 ハッシュ関数")
    print(f"{'─' * 40}")

    message = "Hello, Security!"
    sha256 = hashlib.sha256(message.encode()).hexdigest()
    sha512 = hashlib.sha512(message.encode()).hexdigest()
    print(f"  SHA-256('{message}') = {sha256}")
    print(f"  SHA-512('{message}') = {sha512[:64]}...")

    print("\n  [アバランシェ効果] 1bit変えるだけで出力が大きく変わる:")
    h1 = hashlib.sha256(b"test1").hexdigest()
    h2 = hashlib.sha256(b"test2").hexdigest()
    diff_bits = bin(int(h1, 16) ^ int(h2, 16)).count('1')
    print(f"  SHA-256('test1') = {h1[:32]}...")
    print(f"  SHA-256('test2') = {h2[:32]}...")
    print(f"  異なるビット数: {diff_bits}/256 ({diff_bits/256*100:.1f}%)")

    print("\n  [bcryptの仕組み - 概念説明]")
    print("""
    bcryptはwork factorを持つ適応型ハッシュ:
    - cost=10: 2^10 = 1024回の反復 → 約100ms
    - cost=12: 2^12 = 4096回の反復 → 約400ms
    - cost=14: 2^14 = 16384回の反復 → 約1.6s
    → GPUのムーアの法則に対抗してcostを上げていく
    → Argon2はメモリハードでGPU/ASIC攻撃により強い
    """)

    # work factor シミュレーション
    print("  [Work Factor シミュレーション]")
    for rounds in [1000, 10000, 100000]:
        start = time.time()
        h = b"password"
        for _ in range(rounds):
            h = hashlib.sha256(h).digest()
        elapsed = time.time() - start
        print(f"  SHA-256 x {rounds:>6}: {elapsed*1000:.1f}ms")

    # --- HMAC ---
    print(f"\n{'─' * 40}")
    print("2.2 HMAC（メッセージ認証コード）")
    print(f"{'─' * 40}")

    secret_key = secrets.token_bytes(32)
    message = b"amount=10000&to=alice"
    mac = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
    print(f"  メッセージ: {message.decode()}")
    print(f"  HMAC-SHA256: {mac}")

    # 改ざん検知
    tampered = b"amount=99999&to=eve"
    tampered_mac = hmac.new(secret_key, tampered, hashlib.sha256).hexdigest()
    print(f"\n  改ざんメッセージ: {tampered.decode()}")
    print(f"  改ざんMAC: {tampered_mac}")
    print(f"  一致するか: {hmac.compare_digest(mac, tampered_mac)} → 改ざん検知！")

    print("""
    重要: hmac.compare_digest() はタイミング攻撃を防ぐ定数時間比較。
    通常の == 比較は文字列の先頭から比較し、不一致の位置で処理時間が変わる。
    攻撃者はレスポンス時間の差から正しいMACを推測できる。
    """)

    # --- 対称暗号（概念） ---
    print(f"\n{'─' * 40}")
    print("2.3 対称暗号の概念")
    print(f"{'─' * 40}")
    print("""
    AES (Advanced Encryption Standard):
    ┌─────────────┐     鍵     ┌─────────────┐
    │  平文ブロック │ ─────────→ │  暗号文ブロック │
    │  (128bit)    │   AES暗号化  │  (128bit)    │
    └─────────────┘            └─────────────┘

    [ECBモードが危険な理由]
    同じ平文ブロック → 同じ暗号文ブロック → パターンが見える！
    例: 画像をECBで暗号化すると元の輪郭が見えてしまう（有名なペンギン問題）

    [CBCモード] 前のブロックの暗号文とXORしてからAES暗号化
    → 同じ平文でも異なる暗号文になる
    → ただしIV (Initialization Vector) は予測不能でなければならない

    [GCMモード (推奨)] AES-GCM = 暗号化 + 認証 を同時に提供
    → 改ざん検知付き暗号化（Authenticated Encryption）
    """)

    # XOR暗号のデモ（概念理解用）
    print("  [XOR暗号デモ - 概念理解用]")
    plaintext = b"HELLO"
    key_byte = 0x42
    encrypted = bytes([b ^ key_byte for b in plaintext])
    decrypted = bytes([b ^ key_byte for b in encrypted])
    print(f"  平文: {plaintext}")
    print(f"  暗号文: {encrypted.hex()}")
    print(f"  復号: {decrypted}")

    # --- 非対称暗号（概念） ---
    print(f"\n{'─' * 40}")
    print("2.4 非対称暗号とデジタル署名（概念）")
    print(f"{'─' * 40}")
    print("""
    RSA の仕組み (簡略化):
    1. 大きな素数 p, q を選ぶ
    2. n = p × q, φ(n) = (p-1)(q-1)
    3. e を選ぶ (通常 65537)
    4. d = e^(-1) mod φ(n)
    → 公開鍵: (n, e), 秘密鍵: (n, d)
    → 暗号化: c = m^e mod n
    → 復号: m = c^d mod n
    → 安全性の根拠: 大きな n の素因数分解は計算量的に困難

    デジタル署名:
    1. メッセージのハッシュを計算: h = SHA-256(message)
    2. 秘密鍵で署名: sig = h^d mod n
    3. 公開鍵で検証: h' = sig^e mod n, h == h' なら正当
    → 否認不可性: 秘密鍵の持ち主のみが署名可能
    """)

    # --- HMAC API認証の実装 ---
    print(f"\n{'─' * 40}")
    print("2.5 HMAC ベース API認証（実装）")
    print(f"{'─' * 40}")

    class HMACApiAuth:
        """AWS Signature V4 に似たHMACベースAPI認証"""

        def __init__(self):
            self.api_keys: Dict[str, bytes] = {}

        def register_client(self, client_id: str) -> str:
            """クライアントにAPIキーを発行"""
            secret = secrets.token_bytes(32)
            self.api_keys[client_id] = secret
            return base64.b64encode(secret).decode()

        def sign_request(self, client_id: str, secret_b64: str,
                         method: str, path: str, body: str,
                         timestamp: str) -> str:
            """リクエストに署名"""
            secret = base64.b64decode(secret_b64)
            # 正規化された署名対象文字列
            string_to_sign = f"{method}\n{path}\n{timestamp}\n{body}"
            signature = hmac.new(
                secret, string_to_sign.encode(), hashlib.sha256
            ).hexdigest()
            return signature

        def verify_request(self, client_id: str, method: str, path: str,
                           body: str, timestamp: str, signature: str,
                           max_age_sec: int = 300) -> Tuple[bool, str]:
            """リクエストの署名を検証"""
            # クライアント存在チェック
            if client_id not in self.api_keys:
                return False, "Unknown client_id"

            # タイムスタンプ検証（リプレイ攻撃防止）
            try:
                req_time = float(timestamp)
                if abs(time.time() - req_time) > max_age_sec:
                    return False, "Request expired (replay attack?)"
            except ValueError:
                return False, "Invalid timestamp"

            # 署名検証
            secret = self.api_keys[client_id]
            string_to_sign = f"{method}\n{path}\n{timestamp}\n{body}"
            expected = hmac.new(
                secret, string_to_sign.encode(), hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(expected, signature):
                return True, "Valid"
            return False, "Invalid signature"

    auth = HMACApiAuth()
    client_id = "service-a"
    secret_b64 = auth.register_client(client_id)
    print(f"  クライアント: {client_id}")
    print(f"  シークレット: {secret_b64[:20]}...")

    ts = str(time.time())
    sig = auth.sign_request(client_id, secret_b64, "POST", "/api/transfer",
                            '{"amount":100}', ts)
    print(f"  署名: {sig[:32]}...")

    valid, msg = auth.verify_request(client_id, "POST", "/api/transfer",
                                     '{"amount":100}', ts, sig)
    print(f"  検証結果: {valid} ({msg})")

    # 改ざんテスト
    valid2, msg2 = auth.verify_request(client_id, "POST", "/api/transfer",
                                       '{"amount":99999}', ts, sig)
    print(f"  改ざんテスト: {valid2} ({msg2})")

    print("""
    考えてほしい疑問:
    「なぜタイムスタンプを署名に含めるのか？」
    → リプレイ攻撃を防ぐため。署名付きリクエストを傍受して
      再送されても、タイムスタンプの有効期限が切れていれば拒否。
    """)


# ============================================================
# 第3章: JWT セキュリティ
# ============================================================
def chapter3_jwt():
    print(f"\n{SEP}")
    print("第3章: JWT セキュリティ")
    print(f"{SEP}")

    class SimpleJWT:
        """JWTをゼロから実装（HMAC-SHA256）"""

        @staticmethod
        def _b64url_encode(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

        @staticmethod
        def _b64url_decode(s: str) -> bytes:
            padding = 4 - len(s) % 4
            if padding != 4:
                s += '=' * padding
            return base64.urlsafe_b64decode(s)

        @classmethod
        def create(cls, payload: dict, secret: str,
                   algorithm: str = "HS256") -> str:
            """JWTトークンを生成"""
            header = {"alg": algorithm, "typ": "JWT"}
            header_b64 = cls._b64url_encode(json.dumps(header).encode())
            payload_b64 = cls._b64url_encode(json.dumps(payload).encode())

            signing_input = f"{header_b64}.{payload_b64}"

            if algorithm == "HS256":
                sig = hmac.new(
                    secret.encode(), signing_input.encode(), hashlib.sha256
                ).digest()
            elif algorithm == "none":
                sig = b""
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            sig_b64 = cls._b64url_encode(sig)
            return f"{header_b64}.{payload_b64}.{sig_b64}"

        @classmethod
        def verify(cls, token: str, secret: str,
                   require_exp: bool = True) -> Tuple[bool, dict, str]:
            """JWTトークンを検証 (安全な実装)"""
            parts = token.split('.')
            if len(parts) != 3:
                return False, {}, "Invalid token format"

            header_b64, payload_b64, sig_b64 = parts

            # ヘッダーデコード
            try:
                header = json.loads(cls._b64url_decode(header_b64))
            except Exception:
                return False, {}, "Invalid header"

            # 【重要】 alg: none 攻撃を防ぐ
            if header.get("alg") != "HS256":
                return False, {}, f"Unsupported algorithm: {header.get('alg')}"

            # 署名検証
            signing_input = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                secret.encode(), signing_input.encode(), hashlib.sha256
            ).digest()
            actual_sig = cls._b64url_decode(sig_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return False, {}, "Invalid signature"

            # ペイロードデコード
            try:
                payload = json.loads(cls._b64url_decode(payload_b64))
            except Exception:
                return False, {}, "Invalid payload"

            # 有効期限チェック
            if require_exp:
                if "exp" not in payload:
                    return False, {}, "Missing expiration"
                if time.time() > payload["exp"]:
                    return False, {}, "Token expired"

            return True, payload, "Valid"

    jwt = SimpleJWT()
    secret = "super-secret-key-at-least-256-bits!"

    # 正常なトークン生成
    payload = {
        "sub": "user-123",
        "name": "Alice",
        "role": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1時間後に有効期限
    }
    token = jwt.create(payload, secret)
    print(f"  JWTトークン:")
    parts = token.split('.')
    print(f"    Header:  {parts[0][:40]}...")
    print(f"    Payload: {parts[1][:40]}...")
    print(f"    Sig:     {parts[2][:40]}...")

    # 検証
    valid, decoded, msg = jwt.verify(token, secret)
    print(f"\n  検証結果: {valid} ({msg})")
    if valid:
        print(f"  デコード: sub={decoded['sub']}, role={decoded['role']}")

    # --- 攻撃デモ ---
    print(f"\n{'─' * 40}")
    print("JWT への攻撃パターン")
    print(f"{'─' * 40}")

    # 攻撃1: alg: none
    print("\n  [攻撃1] alg: none 攻撃:")
    none_token = jwt.create({"sub": "attacker", "role": "admin"}, "", "none")
    valid, _, msg = jwt.verify(none_token, secret)
    print(f"    結果: {valid} ({msg})")
    print("    → 安全な実装はHS256以外を拒否する")

    # 攻撃2: 弱い秘密鍵
    print("\n  [攻撃2] 弱い秘密鍵:")
    weak_secret = "secret"
    weak_token = jwt.create(payload, weak_secret)
    print(f"    秘密鍵 'secret' は辞書攻撃で数秒で破られる")
    print("    → 最低256bit (32バイト) 以上のランダムな鍵を使用")
    strong_secret = secrets.token_hex(32)
    print(f"    推奨: {strong_secret[:32]}...")

    # 攻撃3: 有効期限なし
    print("\n  [攻撃3] 有効期限なしトークン:")
    no_exp_token = jwt.create({"sub": "user-123", "role": "admin"}, secret)
    valid, _, msg = jwt.verify(no_exp_token, secret, require_exp=True)
    print(f"    結果: {valid} ({msg})")
    print("    → require_exp=True で有効期限必須を強制")

    # 攻撃4: 署名改ざん
    print("\n  [攻撃4] ペイロード改ざん:")
    tampered_payload = jwt._b64url_encode(
        json.dumps({"sub": "user-123", "role": "superadmin",
                     "exp": int(time.time()) + 99999}).encode()
    )
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
    valid, _, msg = jwt.verify(tampered_token, secret)
    print(f"    結果: {valid} ({msg})")
    print("    → 署名が一致しないため改ざんを検知")

    print("""
    [実装してみよう]
    1. リフレッシュトークンの仕組みを追加せよ
       - アクセストークン: 15分, リフレッシュトークン: 7日
       - リフレッシュ時に古いトークンを無効化 (ブラックリスト方式)
    2. JWTにスコープ (permissions) を追加し、エンドポイント別に認可チェックせよ
    """)


# ============================================================
# 第4章: OAuth2 / OIDC
# ============================================================
def chapter4_oauth2():
    print(f"\n{SEP}")
    print("第4章: OAuth2 / OIDC")
    print(f"{SEP}")

    print("""
    OAuth2 Authorization Code Flow with PKCE:

    ┌──────┐                    ┌────────────┐                ┌──────────┐
    │Client│                    │Auth Server │                │Resource  │
    │(SPA) │                    │(IdP)       │                │Server    │
    └──┬───┘                    └─────┬──────┘                └────┬─────┘
       │  1. code_verifier = random()│                             │
       │  2. code_challenge =        │                             │
       │     SHA256(code_verifier)   │                             │
       │                             │                             │
       │  3. /authorize?             │                             │
       │     response_type=code&     │                             │
       │     code_challenge=...&     │                             │
       │     code_challenge_method=  │                             │
       │     S256                    │                             │
       │ ───────────────────────────→│                             │
       │                             │ 4. ユーザー認証             │
       │  5. redirect_uri?code=xyz   │                             │
       │ ←───────────────────────────│                             │
       │                             │                             │
       │  6. POST /token             │                             │
       │     code=xyz&               │                             │
       │     code_verifier=...       │                             │
       │ ───────────────────────────→│                             │
       │                             │ 7. SHA256(code_verifier)    │
       │                             │    == code_challenge?       │
       │  8. access_token + id_token │                             │
       │ ←───────────────────────────│                             │
       │                             │                             │
       │  9. GET /api/resource       │                             │
       │     Authorization: Bearer ..│                             │
       │ ────────────────────────────┼────────────────────────────→│
       │  10. Resource data          │                             │
       │ ←───────────────────────────┼─────────────────────────────│
    """)

    # PKCE 実装デモ
    print("  [PKCE 実装デモ]")
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()

    print(f"  code_verifier:  {code_verifier[:32]}...")
    print(f"  code_challenge: {code_challenge}")
    print(f"  SHA256(verifier) == challenge: ", end="")

    verify_check = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    print(f"{verify_check == code_challenge}")

    print("""
    トークンの種類:
    ┌───────────────┬───────────────────────────────────────────┐
    │ Access Token  │ APIアクセス用。短寿命 (15分〜1時間)        │
    │ Refresh Token │ アクセストークン更新用。長寿命 (7日〜90日)  │
    │ ID Token      │ ユーザー情報 (OIDC)。JWTでクレーム含む     │
    └───────────────┴───────────────────────────────────────────┘

    スコープ設計のベストプラクティス:
    - read:users / write:users のようにリソース:アクション形式
    - 最小権限の原則: 必要最小限のスコープのみリクエスト
    - オフラインアクセス: offline_access スコープでリフレッシュトークン取得
    """)

    print("""
    考えてほしい疑問:
    「なぜ Authorization Code Flow で直接アクセストークンを返さずに
     一度認可コードを経由するのか？」
    → フロントチャネル (ブラウザURL) にトークンを露出させないため。
      認可コードは短寿命で一度しか使えず、バックチャネル (サーバー間)
      でトークンと交換する。PKCEにより認可コード傍受攻撃も防ぐ。
    """)


# ============================================================
# 第5章: 脅威モデリング (STRIDE)
# ============================================================
def chapter5_threat_modeling():
    print(f"\n{SEP}")
    print("第5章: 脅威モデリング (STRIDE)")
    print(f"{SEP}")

    class ThreatCategory(Enum):
        SPOOFING = "なりすまし"
        TAMPERING = "改ざん"
        REPUDIATION = "否認"
        INFORMATION_DISCLOSURE = "情報漏洩"
        DENIAL_OF_SERVICE = "サービス妨害"
        ELEVATION_OF_PRIVILEGE = "権限昇格"

    class STRIDEAnalyzer:
        """STRIDE脅威モデリングツール"""

        # 各カテゴリの対策マッピング
        MITIGATIONS = {
            ThreatCategory.SPOOFING: [
                "多要素認証 (MFA)",
                "証明書ベース認証 (mTLS)",
                "IPホワイトリスト",
            ],
            ThreatCategory.TAMPERING: [
                "デジタル署名",
                "HMAC検証",
                "入力バリデーション",
                "Immutable infrastructure",
            ],
            ThreatCategory.REPUDIATION: [
                "監査ログ (tamper-proof)",
                "デジタル署名",
                "タイムスタンプ認証局",
            ],
            ThreatCategory.INFORMATION_DISCLOSURE: [
                "暗号化 (at-rest / in-transit)",
                "アクセス制御",
                "データマスキング",
                "DLP (Data Loss Prevention)",
            ],
            ThreatCategory.DENIAL_OF_SERVICE: [
                "レート制限",
                "WAF / DDoS保護",
                "オートスケーリング",
                "サーキットブレーカー",
            ],
            ThreatCategory.ELEVATION_OF_PRIVILEGE: [
                "最小権限の原則",
                "RBAC / ABAC",
                "入力バリデーション",
                "サンドボックス化",
            ],
        }

        def __init__(self, system_name: str):
            self.system_name = system_name
            self.components: List[dict] = []
            self.data_flows: List[dict] = []
            self.threats: List[dict] = []

        def add_component(self, name: str, comp_type: str,
                          trust_level: str) -> None:
            self.components.append({
                "name": name,
                "type": comp_type,
                "trust_level": trust_level,
            })

        def add_data_flow(self, source: str, dest: str,
                          data_type: str, protocol: str) -> None:
            self.data_flows.append({
                "source": source,
                "dest": dest,
                "data_type": data_type,
                "protocol": protocol,
            })

        def analyze(self) -> List[dict]:
            """全コンポーネントとデータフローに対してSTRIDE分析"""
            self.threats = []
            for comp in self.components:
                for cat in ThreatCategory:
                    risk = self._assess_risk(comp, cat)
                    if risk > 0:
                        self.threats.append({
                            "component": comp["name"],
                            "category": cat,
                            "risk_score": risk,
                            "mitigations": self.MITIGATIONS[cat],
                        })

            for flow in self.data_flows:
                if flow["protocol"] == "HTTP":
                    self.threats.append({
                        "component": f"{flow['source']}→{flow['dest']}",
                        "category": ThreatCategory.INFORMATION_DISCLOSURE,
                        "risk_score": 9,
                        "mitigations": ["HTTPSへ移行", "mTLS導入"],
                    })
                if flow["data_type"] in ["credentials", "PII"]:
                    self.threats.append({
                        "component": f"{flow['source']}→{flow['dest']}",
                        "category": ThreatCategory.TAMPERING,
                        "risk_score": 8,
                        "mitigations": ["署名付きペイロード", "TLS 1.3"],
                    })

            self.threats.sort(key=lambda t: t["risk_score"], reverse=True)
            return self.threats

        def _assess_risk(self, component: dict,
                         category: ThreatCategory) -> int:
            """リスクスコア算出 (簡易版, 0-10)"""
            score = 5  # ベーススコア
            if component["trust_level"] == "untrusted":
                score += 3
            if component["type"] == "external_api":
                score += 2
            if component["type"] == "database":
                if category == ThreatCategory.INFORMATION_DISCLOSURE:
                    score += 3
            if component["type"] == "web_frontend":
                if category in (ThreatCategory.SPOOFING,
                                ThreatCategory.ELEVATION_OF_PRIVILEGE):
                    score += 2
            return min(score, 10)

        def report(self) -> str:
            lines = [f"\n  脅威モデリングレポート: {self.system_name}",
                     f"  {'=' * 50}"]
            lines.append(f"  コンポーネント数: {len(self.components)}")
            lines.append(f"  データフロー数: {len(self.data_flows)}")
            lines.append(f"  検出された脅威数: {len(self.threats)}")
            lines.append(f"\n  {'─' * 50}")
            lines.append("  脅威一覧 (リスクスコア降順):")
            for t in self.threats:
                cat_name = t['category'].value
                lines.append(
                    f"  [{t['risk_score']:>2}/10] {t['component']}"
                    f" - {cat_name}"
                )
                for m in t['mitigations'][:2]:
                    lines.append(f"         対策: {m}")
            return "\n".join(lines)

    # 実行デモ: ECサイトの脅威分析
    analyzer = STRIDEAnalyzer("EC サイト")
    analyzer.add_component("Webフロントエンド", "web_frontend", "untrusted")
    analyzer.add_component("APIサーバー", "api_server", "trusted")
    analyzer.add_component("データベース", "database", "trusted")
    analyzer.add_component("決済API", "external_api", "untrusted")

    analyzer.add_data_flow("Webフロントエンド", "APIサーバー", "credentials", "HTTPS")
    analyzer.add_data_flow("APIサーバー", "データベース", "PII", "TCP")
    analyzer.add_data_flow("APIサーバー", "決済API", "payment_data", "HTTPS")

    threats = analyzer.analyze()
    print(analyzer.report())

    print("""
    考えてほしい疑問:
    「脅威モデリングはいつ行うべきか？」
    → 設計フェーズ (Shift Left)。コードを書く前にアーキテクチャレベルで
      脅威を洗い出す。CIパイプラインでも自動脅威分析ツール (例: OWASP
      Threat Dragon) を組み込む。
    """)


# ============================================================
# 第6章: サプライチェーンセキュリティ
# ============================================================
def chapter6_supply_chain():
    print(f"\n{SEP}")
    print("第6章: サプライチェーンセキュリティ")
    print(f"{SEP}")
    print("""
    近年のメジャーインシデント:
    - SolarWinds (2020): ビルドパイプラインにバックドア注入
    - Log4Shell (2021): 広く使われるOSSの重大脆弱性
    - Codecov (2021): CIツールのBashスクリプト改ざん
    - xz utils (2024): メンテナによるバックドア挿入

    ┌─────────────────────────────────────────────────────────┐
    │                  攻撃ベクトル                             │
    ├──────────────────┬──────────────────────────────────────┤
    │ Dependency        │ 正規パッケージに悪意コードを注入       │
    │ Confusion         │ (内部パッケージ名と同名の公開パッケージ)│
    ├──────────────────┼──────────────────────────────────────┤
    │ Typosquatting     │ 類似名パッケージ (例: reqeusts)       │
    ├──────────────────┼──────────────────────────────────────┤
    │ Compromised       │ メンテナアカウントの乗っ取り           │
    │ Maintainer        │                                      │
    ├──────────────────┼──────────────────────────────────────┤
    │ Build Pipeline    │ CI/CDパイプラインへの不正アクセス      │
    │ Compromise        │                                      │
    └──────────────────┴──────────────────────────────────────┘

    対策:
    1. SBOM (Software Bill of Materials)
       - CycloneDX / SPDX 形式で依存関係を記録
       - 脆弱性発見時に影響範囲を即座に特定

    2. Sigstore / cosign
       - コンテナイメージや成果物に署名
       - Keyless signing (OIDC連携)
       - 透明性ログ (Rekor) で署名を公開検証可能

    3. SLSA (Supply-chain Levels for Software Artifacts)
       - Level 1: ビルドプロセスの文書化
       - Level 2: ビルドサービス使用 + 署名付きProvenance
       - Level 3: 改ざん防止されたビルド環境
       - Level 4: 2人レビュー + Hermetic build

    4. Reproducible Builds
       - 同じソースから同じバイナリを再現
       - ビルド環境の決定論的固定
       - Nix / Bazel の hermetic build

    [実装してみよう]
    1. requirements.txt のパッケージをハッシュ固定する仕組みを実装せよ
       pip install --require-hashes -r requirements.txt
    2. Dependabot / Renovate のようなバージョン自動更新ボットの
       アーキテクチャを設計せよ
    """)


# ============================================================
# 第7章: クラウドセキュリティ
# ============================================================
def chapter7_cloud_security():
    print(f"\n{SEP}")
    print("第7章: クラウドセキュリティ")
    print(f"{SEP}")
    print("""
    IAM 最小権限の原則:
    ┌──────────────────────────────────────────────────────┐
    │ 悪い例:                                               │
    │   "Effect": "Allow",                                 │
    │   "Action": "*",                                     │
    │   "Resource": "*"                                    │
    │ → 全リソースに全操作可能 = 侵害時に壊滅的               │
    │                                                      │
    │ 良い例:                                               │
    │   "Effect": "Allow",                                 │
    │   "Action": [                                        │
    │     "s3:GetObject",                                  │
    │     "s3:PutObject"                                   │
    │   ],                                                 │
    │   "Resource": "arn:aws:s3:::my-bucket/uploads/*",    │
    │   "Condition": {                                     │
    │     "StringEquals": {                                │
    │       "aws:PrincipalTag/team": "data-eng"           │
    │     }                                                │
    │   }                                                  │
    │ → 特定バケット・特定パスのみ、タグベースの条件付き       │
    └──────────────────────────────────────────────────────┘

    S3 バケットセキュリティ:
    - バケットポリシーでパブリックアクセスをブロック
    - S3 Block Public Access (アカウントレベル)
    - サーバーサイド暗号化 (SSE-S3 / SSE-KMS)
    - VPCエンドポイント経由のアクセスに限定
    - アクセスログ有効化 (CloudTrail + S3 Server Access Log)

    VPC セキュリティグループ:
    ┌────────────────────────────────────────────────────┐
    │ Web層:                                              │
    │   Inbound: 443 (HTTPS) from 0.0.0.0/0             │
    │   Outbound: 3306 to App-SG only                    │
    │                                                    │
    │ App層:                                              │
    │   Inbound: 8080 from Web-SG only                   │
    │   Outbound: 3306 to DB-SG only                     │
    │                                                    │
    │ DB層:                                               │
    │   Inbound: 3306 from App-SG only                   │
    │   Outbound: なし                                    │
    └────────────────────────────────────────────────────┘
    → セキュリティグループをチェーンしてマイクロセグメンテーション

    AWS セキュリティサービス:
    - GuardDuty: 脅威検知 (異常API呼び出し, C&C通信, 暗号マイニング)
    - Security Hub: セキュリティ態勢の統合ダッシュボード
    - Config: リソース設定の変更追跡 + コンプライアンスルール
    - Macie: S3内の機密データ (PII) 自動検出
    - Inspector: EC2/ECRの脆弱性スキャン
    - KMS: 鍵管理 + エンベロープ暗号化

    考えてほしい疑問:
    「EC2インスタンスにIAMアクセスキーをハードコードするのと
     IAMロールをアタッチするのでは何が違うか？」
    → アクセスキーは永続的で漏洩リスクが高い。IAMロールはSTSから
      一時的なクレデンシャルを自動取得し、自動ローテーションされる。
    """)


# ============================================================
# 第8章: ゼロトラストアーキテクチャ
# ============================================================
def chapter8_zero_trust():
    print(f"\n{SEP}")
    print("第8章: ゼロトラストアーキテクチャ")
    print(f"{SEP}")
    print("""
    従来のネットワークモデル vs ゼロトラスト:

    従来 (Castle & Moat):
    ┌──────────────────────────────────────────────┐
    │ 企業ネットワーク (信頼ゾーン)                    │
    │  ┌────┐  ┌────┐  ┌────┐                      │
    │  │App1│──│App2│──│ DB │  ← 内部は自由通信    │
    │  └────┘  └────┘  └────┘                      │
    │                         ファイアウォール        │
    └──────────────────────────────────────────────┘
    → VPN突破 = 全リソースにアクセス可能

    ゼロトラスト (BeyondCorp):
    ┌──────────────────────────────────────────────┐
    │ すべてのアクセスを「信頼しない、必ず検証する」     │
    │                                              │
    │  User → Identity-Aware Proxy → Policy Engine │
    │         ↓                        ↓           │
    │    デバイス信頼度チェック    コンテキスト評価      │
    │    mTLS証明書検証          リスクスコア算出       │
    │         ↓                        ↓           │
    │    アクセス許可/拒否 (リクエスト単位)              │
    └──────────────────────────────────────────────┘

    ゼロトラストの原則:
    1. ネットワーク位置で信頼しない
    2. 常に認証・認可する (すべてのリクエスト)
    3. 最小権限アクセス
    4. すべてのトラフィックを暗号化
    5. 継続的なモニタリングとポリシー適応

    mTLS (相互TLS認証):
    ┌────────┐           ┌────────┐
    │Service │  mTLS     │Service │
    │   A    │ ←──────→  │   B    │
    └────────┘           └────────┘
    - 通常のTLS: サーバーのみ証明書提示
    - mTLS: クライアントもサーバーも証明書提示
    → サービス間の認証に利用 (Istio, Linkerd)

    Service Mesh Security (Istio 例):
    - Sidecar Proxy (Envoy) が全通信を仲介
    - 自動mTLS (PeerAuthentication)
    - AuthorizationPolicy でL7レベルのアクセス制御
    - 例: サービスAからBへのGETのみ許可、POSTは拒否

    [実装してみよう]
    1. IPベースの信頼ではなく、トークン+デバイスコンテキストで
       アクセス制御する認可エンジンを設計せよ
    2. mTLSのハンドシェイクフローを図示せよ
    """)


# ============================================================
# 第9章: セキュリティテスト
# ============================================================
def chapter9_security_testing():
    print(f"\n{SEP}")
    print("第9章: セキュリティテスト")
    print(f"{SEP}")
    print("""
    セキュリティテストの種類と CI/CD への組み込み:

    ┌──────────┬─────────────────────────────────────────────┐
    │ SAST     │ Static Application Security Testing         │
    │          │ ソースコードを解析して脆弱性を検出            │
    │          │ ツール: Semgrep, CodeQL, SonarQube           │
    │          │ CI: PR作成時に自動実行                        │
    ├──────────┼─────────────────────────────────────────────┤
    │ DAST     │ Dynamic Application Security Testing        │
    │          │ 実行中のアプリケーションに攻撃を実行          │
    │          │ ツール: OWASP ZAP, Burp Suite               │
    │          │ CI: ステージング環境にデプロイ後に実行         │
    ├──────────┼─────────────────────────────────────────────┤
    │ SCA      │ Software Composition Analysis               │
    │          │ 依存関係の既知脆弱性を検出                    │
    │          │ ツール: Dependabot, Snyk, Trivy             │
    │          │ CI: 毎日スケジュール実行 + PR時                │
    ├──────────┼─────────────────────────────────────────────┤
    │ Secret   │ シークレット検出                              │
    │ Scanning │ ハードコードされた認証情報を検出               │
    │          │ ツール: GitLeaks, TruffleHog                 │
    │          │ CI: pre-commit hook + PR時                   │
    └──────────┴─────────────────────────────────────────────┘

    Semgrep ルール例:
    ```yaml
    rules:
      - id: sql-injection
        patterns:
          - pattern: |
              cursor.execute(f"... {$VAR} ...")
        message: "SQLインジェクションの可能性"
        severity: ERROR
    ```

    ペネトレーションテスト方法論:
    1. 偵察 (Reconnaissance): OSINT, DNS列挙, ポートスキャン
    2. 列挙 (Enumeration): サービス検出, バナーグラブ
    3. 脆弱性分析: 既知CVEの確認, カスタム脆弱性探索
    4. エクスプロイト: 実際の攻撃実行 (許可された範囲内)
    5. ポストエクスプロイト: 権限昇格, ラテラルムーブメント
    6. レポート: 発見事項, 影響度, 修正推奨

    Bug Bounty プログラム:
    - HackerOne / Bugcrowd 等のプラットフォーム
    - スコープ定義が重要 (対象ドメイン、許可する攻撃手法)
    - 報酬設計: Critical ($5K-$50K+), High ($1K-$10K), Medium ($500-$2K)
    """)


# ============================================================
# 第10章: パスワード強度チェッカー（実装）
# ============================================================
def chapter10_password_checker():
    print(f"\n{SEP}")
    print("実装: パスワード強度チェッカー")
    print(f"{SEP}")

    class PasswordStrengthChecker:
        """NIST SP 800-63B ガイドラインに基づくチェッカー"""

        COMMON_PASSWORDS = {
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "monkey", "dragon", "master", "abc123",
            "password123", "iloveyou", "trustno1", "sunshine",
        }

        @classmethod
        def check(cls, password: str) -> dict:
            result = {
                "password": password[:2] + "*" * (len(password) - 2),
                "score": 0,
                "max_score": 100,
                "issues": [],
                "strength": "",
            }

            # 長さチェック (最重要)
            length = len(password)
            if length < 8:
                result["issues"].append("8文字以上必要")
            elif length < 12:
                result["score"] += 20
            elif length < 16:
                result["score"] += 35
            else:
                result["score"] += 45

            # 文字種チェック
            has_lower = bool(re.search(r'[a-z]', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_digit = bool(re.search(r'\d', password))
            has_special = bool(re.search(r'[^a-zA-Z0-9]', password))

            char_types = sum([has_lower, has_upper, has_digit, has_special])
            result["score"] += char_types * 10

            if char_types < 2:
                result["issues"].append("複数の文字種を使用してください")

            # 共通パスワードチェック
            if password.lower() in cls.COMMON_PASSWORDS:
                result["score"] = max(0, result["score"] - 50)
                result["issues"].append("よく使われるパスワードです")

            # 連続文字チェック
            for i in range(len(password) - 2):
                if password[i] == password[i+1] == password[i+2]:
                    result["score"] = max(0, result["score"] - 10)
                    result["issues"].append("同じ文字の3連続は避けてください")
                    break

            # キーボードパターンチェック
            patterns = ["qwerty", "asdf", "1234", "abcd"]
            for p in patterns:
                if p in password.lower():
                    result["score"] = max(0, result["score"] - 15)
                    result["issues"].append(f"キーボードパターン '{p}' を含んでいます")
                    break

            # エントロピー概算
            charset_size = 0
            if has_lower: charset_size += 26
            if has_upper: charset_size += 26
            if has_digit: charset_size += 10
            if has_special: charset_size += 32
            if charset_size > 0:
                import math
                entropy = length * math.log2(charset_size)
                result["entropy_bits"] = round(entropy, 1)
                if entropy >= 60:
                    result["score"] += 15

            # 強度判定
            score = result["score"]
            if score >= 80:
                result["strength"] = "非常に強い"
            elif score >= 60:
                result["strength"] = "強い"
            elif score >= 40:
                result["strength"] = "普通"
            elif score >= 20:
                result["strength"] = "弱い"
            else:
                result["strength"] = "非常に弱い"

            result["score"] = min(100, result["score"])
            return result

    checker = PasswordStrengthChecker()
    test_passwords = [
        "password",
        "P@ssw0rd",
        "correct-horse-battery-staple",
        "Tr0ub4dor&3",
        "aB3$" + secrets.token_urlsafe(12),
        "aaaa1111",
    ]

    print()
    for pw in test_passwords:
        result = checker.check(pw)
        bar_len = result["score"] // 5
        bar = "█" * bar_len + "░" * (20 - bar_len)
        entropy = result.get("entropy_bits", 0)
        print(f"  {result['password']:<30} [{bar}] "
              f"{result['score']:>3}/100 {result['strength']}"
              f"  ({entropy:.0f}bit)")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"    ⚠ {issue}")
        print()


# ============================================================
# 面接問題
# ============================================================
def interview_question():
    print(f"\n{SEP}")
    print("面接問題: マルチテナントSaaSの認証・認可システムを設計せよ")
    print(f"{SEP}")
    print("""
    要件:
    - 100社以上のテナント、各テナント1000ユーザー
    - テナント間の完全なデータ分離
    - 各テナントが独自のSSO (SAML/OIDC) を設定可能
    - ロールベースアクセス制御 (RBAC) + カスタムロール
    - APIアクセスの認証
    - 監査ログ

    模範回答の構成:

    1. 認証アーキテクチャ:
    ┌─────────┐    ┌──────────────┐    ┌──────────────┐
    │ ユーザー │───→│  API Gateway │───→│  Auth Service│
    │          │    │ (Rate Limit) │    │  (IdP連携)   │
    └─────────┘    └──────────────┘    └──────┬───────┘
                                              │
                    ┌─────────────────────────┼────────────┐
                    │                         │            │
              ┌─────┴─────┐  ┌───────────┐  ┌┴──────────┐
              │ Local Auth │  │ SAML IdP  │  │ OIDC IdP  │
              │ (bcrypt)   │  │ (Okta等)  │  │ (Google等)│
              └───────────┘  └───────────┘  └───────────┘

    2. テナント分離戦略:
       - DB: tenant_id カラム + Row Level Security (PostgreSQL RLS)
       - 全クエリに tenant_id を自動注入 (ミドルウェア)
       - JWTにtenant_idを含め、APIレイヤーで検証

    3. 認可モデル (RBAC):
       tenant_roles テーブル:
       | tenant_id | role_name | permissions (JSON)               |
       |-----------|-----------|----------------------------------|
       | t-001     | admin     | ["*"]                            |
       | t-001     | editor    | ["read:*", "write:docs"]         |
       | t-001     | viewer    | ["read:docs", "read:dashboard"]  |

       APIミドルウェアで permission チェック:
       @require_permission("write:docs")
       def create_document(request):
           ...

    4. APIキー管理:
       - テナント管理者がAPIキーを発行
       - キーはbcryptでハッシュ化して保存
       - プレフィックス (例: sk_live_) で識別
       - スコープ制限 + 有効期限

    5. セキュリティ考慮事項:
       - セッション固定攻撃対策: ログイン成功時にセッション再生成
       - CSRF: SameSite Cookie + CSRFトークン
       - XSS: Content-Security-Policy ヘッダー
       - レート制限: テナント単位 + ユーザー単位

    6. 監査ログ:
       - 全認証イベント (成功/失敗) を記録
       - 権限変更の追跡
       - Immutable storage (S3 Object Lock)
       - テナント管理者向け監査ログUI

    スケーラビリティ:
    - Auth ServiceはステートレスでHorizontal Scaling
    - セッション管理はRedis Cluster
    - JWTで分散検証 (Auth Serviceへの問い合わせ不要)
    - 公開鍵はJWKSエンドポイントで配布

    考えてほしい疑問:
    「テナントAの管理者がテナントBのデータにアクセスする脆弱性
     (テナントエスケープ) をどう防ぐか？」
    → 全レイヤーでtenant_idを検証。DB (RLS)、API (ミドルウェア)、
      フロントエンド (コンテキスト) の多層防御。
      侵入テストでテナントエスケープを重点的にテスト。
    """)

    print(f"\n{SEP}")
    print("総合演習")
    print(f"{SEP}")
    print("""
    [実装してみよう]

    1. OWASP Top 10 チェックリストを自分のプロジェクトに適用し、
       各項目の対策状況を○/×で一覧表にせよ

    2. 上記のJWT実装にリフレッシュトークンローテーションを追加:
       - リフレッシュ時に古いトークンを失効させる
       - トークン再利用検知 (盗まれたリフレッシュトークンの検出)

    3. Semgrep カスタムルールを3つ以上書き、自分のコードベースで実行せよ:
       - SQLインジェクション検出
       - ハードコードされた秘密鍵検出
       - 不適切なエラーハンドリング検出

    4. 面接問題のシステム設計をコードで実装:
       - FastAPI / Flask でAuth Service のプロトタイプ
       - RBAC ミドルウェア
       - 監査ログ記録
    """)


# ============================================================
# メイン実行
# ============================================================
def main():
    print(f"\n{'━' * 60}")
    print("  セキュリティエンジニアリング Deep Dive")
    print("  FAANG レベルのセキュリティ知識体系")
    print(f"{'━' * 60}")
    print("""
  対象: セキュリティの基礎は知っているが、体系的に深く学びたいエンジニア
  目標: OWASP Top 10、暗号学、認証・認可、脅威モデリング、
        クラウドセキュリティ、ゼロトラストを実装レベルで理解する
    """)

    chapter1_owasp_top10()
    chapter2_cryptography()
    chapter3_jwt()
    chapter4_oauth2()
    chapter5_threat_modeling()
    chapter6_supply_chain()
    chapter7_cloud_security()
    chapter8_zero_trust()
    chapter9_security_testing()
    chapter10_password_checker()
    interview_question()

    print(f"\n{SEP}")
    print("学習完了！")
    print(f"{SEP}")
    print("""
  セキュリティは「完璧」は存在しない。多層防御 (Defense in Depth) で
  リスクを許容可能なレベルまで低減するのが目標。

  次のステップ:
  1. OWASP WebGoat で実際に脆弱性を体験する
  2. CTF (Capture The Flag) に参加する
  3. 自分のプロジェクトで脅威モデリングを実施する
  4. AWS Security Specialty 認定を取得する
    """)


if __name__ == "__main__":
    main()
