"""
API Gateway - 認証・レート制限・ルーティング
=============================================
[BUG-04] レート制限が実装されていない → DDoSで全サービスが落ちる
[BUG-05] JWTシークレットが環境変数だが、デフォルト値がハードコード
[BUG-06] 全エンドポイントに認証が必要なのに /notes/search は public
"""

import os
import time
from functools import wraps

import httpx
import jwt
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

NOTE_SERVICE    = os.environ.get("NOTE_SERVICE_URL",   "http://note_service:8001")
SEARCH_SERVICE  = os.environ.get("SEARCH_SERVICE_URL", "http://search_service:8002")
ANALYTICS_URL   = os.environ.get("ANALYTICS_SERVICE_URL", "http://analytics_service:8003")

# [BUG-05] デフォルト値がハードコード → 本番でも同じシークレットが使われる危険
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-do-not-use-in-prod")
ALGORITHM  = "HS256"

app = FastAPI(title="TechCorp API Gateway", version="1.0.0")

# メトリクス
GW_REQUESTS = Counter("gateway_requests_total", "Gateway requests", ["method", "path", "status"])
GW_DURATION = Histogram("gateway_duration_seconds", "Gateway request duration", ["path"])
UPSTREAM_ERRORS = Counter("gateway_upstream_errors_total", "Upstream errors", ["service"])

# ─── 認証 ───────────────────────────────────────────────

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_auth_header(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return None


# ─── レート制限（★ 未実装 - BUG-04 ★）────────────────────
# TODO: Redis を使ったスライディングウィンドウ方式のレート制限を実装する
# 現状: 無制限にリクエストを受け付けるため、スパイク時に全サービスがダウンする
#
# 実装すべきコード（ヒント）:
# async def rate_limit(request: Request):
#     key = f"rate:{request.client.host}"
#     count = await redis.incr(key)
#     if count == 1:
#         await redis.expire(key, 60)
#     if count > 100:  # 1分間に100リクエストまで
#         raise HTTPException(status_code=429, detail="Too Many Requests")

# ─── ヘルスチェック ──────────────────────────────────────

@app.get("/health")
async def health():
    services = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, url in [("note", NOTE_SERVICE), ("search", SEARCH_SERVICE), ("analytics", ANALYTICS_URL)]:
            try:
                r = await client.get(f"{url}/health")
                services[name] = "healthy" if r.status_code == 200 else "unhealthy"
            except Exception:
                services[name] = "unreachable"
    overall = "healthy" if all(v == "healthy" for v in services.values()) else "degraded"
    return {"status": overall, "services": services}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ─── ノートAPI プロキシ ──────────────────────────────────

@app.get("/api/notes")
async def list_notes(request: Request, limit: int = 20, offset: int = 0):
    # [BUG-06] 認証チェックしているが、/api/notes/search は認証なしで通過できる
    token = get_auth_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    verify_token(token)

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{NOTE_SERVICE}/notes", params={"limit": limit, "offset": offset})
        GW_REQUESTS.labels(request.method, "/api/notes", r.status_code).inc()
        GW_DURATION.labels("/api/notes").observe(time.time() - start)
        return r.json()
    except httpx.TimeoutException:
        UPSTREAM_ERRORS.labels("note_service").inc()
        raise HTTPException(status_code=504, detail="Note service timeout")
    except Exception as e:
        UPSTREAM_ERRORS.labels("note_service").inc()
        raise HTTPException(status_code=502, detail=f"Note service error: {e}")


@app.get("/api/notes/search")
async def search_notes(request: Request, q: str = ""):
    """
    ★ [BUG-06] 認証なしでアクセス可能 ★
    これにより未認証のユーザーがコンテンツを検索・取得できる。
    さらに note_service 側に SQLインジェクション脆弱性があるため、
    認証なし + SQLインジェクション = 深刻なセキュリティホール
    """
    # 認証チェックがない！
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{NOTE_SERVICE}/notes/search", params={"q": q})
    return r.json()


@app.post("/api/notes")
async def create_note(request: Request):
    token = get_auth_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    payload = verify_token(token)

    body = await request.json()
    body["user_id"] = payload.get("user_id", 1)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"{NOTE_SERVICE}/notes", json=body)
    return JSONResponse(content=r.json(), status_code=r.status_code)


@app.get("/api/notes/{note_id}")
async def get_note(note_id: int, request: Request):
    token = get_auth_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    verify_token(token)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{NOTE_SERVICE}/notes/{note_id}")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Note not found")
    return r.json()


# ─── 検索API プロキシ ─────────────────────────────────────

@app.post("/api/search/index")
async def index_note(request: Request):
    token = get_auth_header(request)
    if not token:
        raise HTTPException(status_code=401)
    verify_token(token)
    body = await request.json()
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.post(f"{SEARCH_SERVICE}/index", json=body)
    return r.json()


@app.get("/api/search")
async def full_text_search(q: str, request: Request):
    token = get_auth_header(request)
    if not token:
        raise HTTPException(status_code=401)
    verify_token(token)
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(f"{SEARCH_SERVICE}/search", params={"q": q})
    return r.json()


# ─── 認証API ──────────────────────────────────────────────

@app.post("/auth/token")
async def get_token(request: Request):
    """開発用: 簡易JWT発行（本番ではOAuth2/OIDC を使うこと）"""
    from datetime import datetime, timedelta, timezone
    body = await request.json()

    # [本番禁止] ユーザー認証を省略している
    payload = {
        "user_id": 1,
        "email": body.get("email", "demo@techcorp.com"),
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
