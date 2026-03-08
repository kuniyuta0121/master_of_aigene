"""
Phase 1: FastAPI + SQLite によるナレッジ管理API
=================================================
学習目標:
  - Pythonの型ヒント・Pydantic・async/await を実践する
  - RESTful API 設計原則（リソース設計・ステータスコード・エラーハンドリング）を体感する
  - SQLAlchemy ORM によるデータベース操作を習得する

考えてほしい疑問:
  Q1. なぜ同期(def)ではなく非同期(async def)でエンドポイントを定義するのか？
  Q2. NoteCreateとNoteResponseを別々のPydanticモデルにした理由は？
  Q3. HTTP 404 と 422 の違いは何か？いつどちらを返すべきか？
  Q4. ページネーションを加えるとしたら、どう設計するか？（クエリパラメータ? カーソル?）

実行方法:
  pip install fastapi uvicorn sqlalchemy
  uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import uvicorn
from database import create_tables, get_db
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from models import Note, NoteCreate, NoteResponse, NoteUpdate
from routers import notes, tags
from sqlalchemy.orm import Session


# --- アプリケーションのライフサイクル管理 ---
# [考える] startup/shutdownで何を初期化・クリーンアップすべきか？
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時: テーブル作成・接続プール初期化
    create_tables()
    print("✓ Database initialized")
    yield
    # 終了時: リソース解放
    print("✓ Shutdown complete")


app = FastAPI(
    title="KnowledgeAI API",
    description="AI搭載ナレッジ管理システム - Phase 1: Core CRUD",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: フロントエンド(Phase 10)が別ポートからアクセスするために必要
# [考える] 本番環境では allow_origins=["*"] にしていいか？なぜダメか？
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js の開発サーバー
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント - Phase 6で監視ツールが叩く"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
