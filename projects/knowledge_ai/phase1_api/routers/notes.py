"""
routers/notes.py - ノートCRUDエンドポイント
=============================================
学習ポイント:
  - RESTful API の URL設計（動詞を使わない、リソースで表現する）
  - HTTP ステータスコードの正しい使い分け
  - 依存性注入(Depends)によるDB・認証の注入
  - クエリパラメータによるフィルタリングとページネーション

RESTful 設計ルール（ここで体感する）:
  GET    /notes          → 一覧取得
  POST   /notes          → 新規作成    → 201 Created
  GET    /notes/{id}     → 1件取得
  PATCH  /notes/{id}     → 部分更新
  DELETE /notes/{id}     → 削除        → 204 No Content
  GET    /notes/{id}/tags → 関連タグ取得（ネストリソース）

考えてほしい疑問:
  Q1. search を GET /notes?q=keyword にした理由は？ POST /notes/search にしなかった理由は？
  Q2. 削除APIで 200 と 204 のどちらを返すべきか？その基準は？
  Q3. ページネーションで offset/limit とカーソルベースの違いと使い分けは？
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import NoteCreate, NoteDB, NoteListResponse, NoteResponse, NoteUpdate, TagDB

router = APIRouter(prefix="/notes", tags=["Notes"])


def _get_note_or_404(note_id: int, db: Session) -> NoteDB:
    """共通ヘルパー: ノートを取得するか404を返す"""
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note id={note_id} が見つかりません",
        )
    return note


def _resolve_tags(tag_names: list[str], db: Session) -> list[TagDB]:
    """タグ名リストをDBのTagオブジェクトに変換（なければ作成）"""
    tags = []
    for name in set(tag_names):  # 重複排除
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(TagDB).filter(TagDB.name == name).first()
        if not tag:
            tag = TagDB(name=name)
            db.add(tag)
        tags.append(tag)
    return tags


@router.get("", response_model=NoteListResponse)
async def list_notes(
    q:       str | None = Query(None, description="タイトル・本文の全文検索キーワード"),
    tag:     str | None = Query(None, description="タグ名でフィルタ"),
    page:    int        = Query(1, ge=1, description="ページ番号（1始まり）"),
    per_page: int       = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    db: Session = Depends(get_db),
):
    """
    ノート一覧取得。キーワード検索・タグフィルタ・ページネーション対応。

    [実装してみよう]
    - created_at で並び替えるパラメータ（sort_by, order）を追加する
    - 複数タグでの AND/OR フィルタを実装する
    """
    query = db.query(NoteDB)

    # キーワード検索（LIKE検索 - 本番ではFull Text Searchを使うべき）
    # [考える] なぜ本番でLIKE検索はスケールしないのか？代替は何か？
    if q:
        query = query.filter(
            NoteDB.title.contains(q) | NoteDB.content.contains(q)
        )

    # タグフィルタ
    if tag:
        query = query.join(NoteDB.tags).filter(TagDB.name == tag.lower())

    total = query.count()
    offset = (page - 1) * per_page
    notes = query.order_by(NoteDB.created_at.desc()).offset(offset).limit(per_page).all()

    return NoteListResponse(
        items=notes,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(body: NoteCreate, db: Session = Depends(get_db)):
    """
    ノート新規作成。

    [考える] なぜ POST の成功レスポンスは 200 ではなく 201 なのか？
    """
    tags = _resolve_tags(body.tag_names, db)

    note = NoteDB(
        title=body.title,
        content=body.content,
        source_url=body.source_url,
        tags=tags,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    return _get_note_or_404(note_id, db)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, body: NoteUpdate, db: Session = Depends(get_db)):
    """
    部分更新 (PATCH)。送られたフィールドだけ更新する。

    [考える] PUT（全フィールド更新）との設計上の違いと使い分けは？
    """
    note = _get_note_or_404(note_id, db)

    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    if body.source_url is not None:
        note.source_url = body.source_url
    if body.tag_names is not None:
        note.tags = _resolve_tags(body.tag_names, db)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    ノート削除。

    [実装してみよう] 論理削除（deleted_at カラムを追加）に変更する。
    物理削除と論理削除の使い分けはどう考えるか？
    """
    note = _get_note_or_404(note_id, db)
    db.delete(note)
    db.commit()
    # 204 No Content なのでボディを返さない
