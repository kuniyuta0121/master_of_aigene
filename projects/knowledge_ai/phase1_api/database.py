"""
database.py - データベース接続とセッション管理
=================================================
学習ポイント:
  - SQLAlchemy の SessionLocal と依存性注入（Dependency Injection）パターン
  - なぜ「1リクエスト = 1セッション」が基本なのか？
  - connection pool の役割と設定

考えてほしい疑問:
  Q1. SQLite から PostgreSQL に切り替えるとき、どこを変えるだけでよいか？
  Q2. connect_args={"check_same_thread": False} はなぜ必要か？（SQLite特有の問題）
  Q3. 本番環境でのコネクションプール設定（pool_size, max_overflow）はどう決めるか？
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 環境変数から接続先を切り替えられるようにする
# [実装してみよう] .env ファイルから読み込むよう python-dotenv を使って修正する
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./knowledge_ai.db")

# SQLite の場合は check_same_thread=False が必要（マルチスレッド対応）
# PostgreSQL の場合はこの設定は不要
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # [実装してみよう] PostgreSQL に切り替えたら pool_size=5, max_overflow=10 を設定する
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # デバッグ用: SQLをログ出力
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    """アプリ起動時にテーブルを作成する"""
    from models import Base
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI の Depends() で使う DB セッションジェネレーター。

    try/finally で必ずセッションをクローズする。
    これが「依存性注入（DI）」の実例。

    [考える] なぜ yield を使うのか？return との違いは？
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
