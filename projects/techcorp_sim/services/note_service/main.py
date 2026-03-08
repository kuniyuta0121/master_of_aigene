"""
Note Service - コアCRUDサービス
================================
このサービスには意図的な問題が3つ埋め込まれている。
シミュレーターが教える前に自分で発見できるか？

[BUG-01] N+1クエリ問題 → list_notes でノートごとに別クエリが走る
[BUG-02] SQLインジェクション → search エンドポイントで文字列結合
[BUG-03] SQL_ECHO=true で機密データがログに出力される
"""

import os
import time
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./notes.db")
engine = create_engine(DATABASE_URL, echo=os.environ.get("SQL_ECHO", "false").lower() == "true")
Session = sessionmaker(bind=engine)

app = FastAPI(title="Note Service", version="1.0.0")

# Prometheus メトリクス
REQUEST_COUNT    = Counter("note_service_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_DURATION = Histogram("note_service_request_duration_seconds", "Request duration", ["endpoint"])
DB_QUERY_DURATION = Histogram("note_service_db_query_duration_seconds", "DB query duration", ["query_type"])


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: list[str] = []
    user_id: int = 1


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: list[str]
    view_count: int
    created_at: str
    user_email: Optional[str] = None  # N+1の原因：ノートごとにユーザーを取得する


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(request.method, request.url.path, response.status_code).inc()
    REQUEST_DURATION.labels(request.url.path).observe(duration)
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": "note_service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/notes")
def list_notes(limit: int = Query(20, ge=1, le=100), offset: int = 0):
    """
    ノート一覧取得。

    ★ [BUG-01] N+1クエリ問題がここに存在する ★
    ノートを取得した後、各ノートのユーザー情報を個別クエリで取得している。
    500件のノートがあると = 1(ノート一覧) + 500(ユーザー) = 501クエリ！

    修正方法: JOIN を使って1クエリで取得する
      SELECT n.*, u.email FROM notes n
      LEFT JOIN users u ON n.user_id = u.id
      ORDER BY n.created_at DESC
      LIMIT :limit OFFSET :offset
    """
    db = Session()
    try:
        with DB_QUERY_DURATION.labels("list_notes").time():
            # ノート一覧を取得（1クエリ）
            notes = db.execute(
                text("SELECT * FROM notes ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset}
            ).fetchall()

        results = []
        for note in notes:
            note_dict = dict(note._mapping)

            # ★ N+1の問題箇所: ノートごとに別クエリでユーザーを取得 ★
            # ループの中でクエリを実行 → ノート数 × 1 の追加クエリが発生
            user = db.execute(
                text("SELECT email FROM users WHERE id = :uid"),
                {"uid": note_dict["user_id"]}
            ).fetchone()

            note_dict["user_email"] = user.email if user else None
            note_dict["tags"] = note_dict.get("tags") or []
            note_dict["created_at"] = str(note_dict.get("created_at", ""))
            results.append(note_dict)

        return {"items": results, "total": len(results)}
    finally:
        db.close()


@app.get("/notes/search")
def search_notes(q: str = Query(...)):
    """
    ノード検索。

    ★ [BUG-02] SQLインジェクション脆弱性がここに存在する ★
    ユーザー入力を文字列結合でSQLに組み込んでいる！

    攻撃例:
      q=' OR '1'='1  → 全件取得
      q=' UNION SELECT email,password_hash,1,1,1,1,1 FROM users--

    修正方法: パラメータ化クエリを使う
      text("... WHERE title ILIKE :q"), {"q": f"%{q}%"}
    """
    db = Session()
    try:
        # ★ 絶対にやってはいけないSQLの書き方 ★
        unsafe_sql = f"SELECT id, title, content FROM notes WHERE title ILIKE '%{q}%' OR content ILIKE '%{q}%' LIMIT 20"
        results = db.execute(text(unsafe_sql)).fetchall()
        return {"items": [dict(r._mapping) for r in results], "query": q}
    finally:
        db.close()


@app.post("/notes", status_code=201)
def create_note(body: NoteCreate):
    db = Session()
    try:
        import json
        result = db.execute(
            text("""INSERT INTO notes (user_id, title, content, tags)
                    VALUES (:uid, :title, :content, :tags::jsonb)
                    RETURNING id, title, created_at"""),
            {"uid": body.user_id, "title": body.title,
             "content": body.content, "tags": json.dumps(body.tags)}
        ).fetchone()
        db.commit()
        return {"id": result.id, "title": result.title, "created_at": str(result.created_at)}
    finally:
        db.close()


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    db = Session()
    try:
        note = db.execute(
            text("SELECT * FROM notes WHERE id = :id"),
            {"id": note_id}
        ).fetchone()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        # 閲覧数を更新
        db.execute(text("UPDATE notes SET view_count = view_count + 1 WHERE id = :id"), {"id": note_id})
        db.commit()
        result = dict(note._mapping)
        result["created_at"] = str(result.get("created_at", ""))
        return result
    finally:
        db.close()


@app.get("/stats")
def get_stats():
    """サービス統計（アナリティクスサービスが参照する）"""
    db = Session()
    try:
        stats = db.execute(text("""
            SELECT
                COUNT(*) as total_notes,
                SUM(view_count) as total_views,
                AVG(LENGTH(content)) as avg_content_length
            FROM notes
        """)).fetchone()
        return dict(stats._mapping)
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
