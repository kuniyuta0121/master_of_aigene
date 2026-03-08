"""
ai_router.py - AI機能のAPIエンドポイント
==========================================
Phase 1 の FastAPI アプリに追加するルーター。

main.py に以下を追加:
    from phase2_ai.ai_router import router as ai_router
    app.include_router(ai_router, prefix="/api/v1")

考えてほしい疑問:
  Q1. RAGの回答を非同期(async)にしているが、LLM呼び出しが遅い場合どう対処するか？
      （ストリーミングレスポンス・WebSocket・バックグラウンドタスク）
  Q2. APIキーをコードに書かない（環境変数で管理する）重要性は？
  Q3. レート制限（Rate Limit）をAPIに実装するとしたらどこに追加するか？
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import NoteDB
from rag_service import RAGService

router = APIRouter(prefix="/ai", tags=["AI"])
rag_service = RAGService()


class QuestionRequest(BaseModel):
    question: str
    score_threshold: float = 0.3


class IndexRequest(BaseModel):
    note_id: int


@router.post("/ask")
async def ask_question(body: QuestionRequest):
    """
    RAGで質問に答える。

    [実装してみよう] StreamingResponse を使って回答をストリーミングする。
    LLMの応答をリアルタイムで表示する体験が大きく変わる。
    """
    result = rag_service.answer(body.question, body.score_threshold)
    return result


@router.post("/index/{note_id}")
async def index_note(
    note_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    ノートをベクターDBに登録する（バックグラウンドで処理）。

    BackgroundTasks を使う理由:
    - Embeddingの計算は少し時間がかかる
    - APIレスポンスを即座に返しつつ、インデックス化はバックグラウンドで実行

    [考える] BackgroundTasks の代わりにCelery + Redisを使うのはいつか？
    （バックグラウンドタスクが失敗したとき、BackgroundTasksはリトライできない）
    """
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} が見つかりません")

    def _index():
        rag_service.vector_store.add_note(note.id, note.title, note.content)

    background_tasks.add_task(_index)

    return {"message": f"Note {note_id} のインデックス化を開始しました（バックグラウンド処理）"}


@router.delete("/index/{note_id}")
async def delete_index(note_id: int):
    """ノート削除時にベクターDBからも削除する"""
    rag_service.vector_store.delete_note(note_id)
    return {"message": f"Note {note_id} のインデックスを削除しました"}


@router.post("/index/all")
async def index_all_notes(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    全ノートを一括インデックス化する。

    [実装してみよう]
    - 進捗をSSE（Server-Sent Events）でリアルタイム通知する
    - すでにインデックス済みのノートはスキップする
    """
    notes = db.query(NoteDB).all()

    def _index_all():
        for note in notes:
            rag_service.vector_store.add_note(note.id, note.title, note.content)

    background_tasks.add_task(_index_all)
    return {"message": f"{len(notes)}件のノートのインデックス化を開始しました"}
