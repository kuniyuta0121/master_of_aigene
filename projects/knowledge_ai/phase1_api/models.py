"""
models.py - データモデル定義
==============================
Pydantic v2 による入出力スキーマ + SQLAlchemy による DB モデルを分離して定義する。

学習ポイント:
  - なぜ「DBモデル」と「APIスキーマ(Pydantic)」を分けるのか？
    → DBの内部表現をAPIに漏らさないため（例: パスワードhash、内部ID体系）
  - Pydantic の model_validator で複雑なバリデーションを実装する
  - Optional[str] と str | None の違い（Python 3.10+では後者が推奨）
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# --- SQLAlchemy ORM モデル ---

class Base(DeclarativeBase):
    pass


# 多対多の中間テーブル（NoteとTagの関係）
# [考える] 多対多はどんなケースで使うか？他に思いつく例は？
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id"), primary_key=True),
    Column("tag_id",  Integer, ForeignKey("tags.id"),  primary_key=True),
)


class NoteDB(Base):
    """notes テーブルのORM表現"""
    __tablename__ = "notes"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, autoincrement=True)
    title:      Mapped[str]           = mapped_column(String(200), nullable=False)
    content:    Mapped[str]           = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション: Noteは複数のTagを持つ
    tags: Mapped[list["TagDB"]] = relationship("TagDB", secondary=note_tags, back_populates="notes")


class TagDB(Base):
    __tablename__ = "tags"

    id:   Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    notes: Mapped[list["NoteDB"]] = relationship("NoteDB", secondary=note_tags, back_populates="tags")


# --- Pydantic スキーマ (API の入出力) ---

class TagSchema(BaseModel):
    id:   int
    name: str

    model_config = {"from_attributes": True}  # ORM モデルから変換可能にする


class NoteCreate(BaseModel):
    """POST /notes のリクエストボディ"""
    title:      str            = Field(..., min_length=1, max_length=200, description="ノートのタイトル")
    content:    str            = Field(..., min_length=1, description="ノートの本文")
    source_url: Optional[str]  = Field(None, description="参照URL（任意）")
    tag_names:  list[str]      = Field(default_factory=list, description="タグ名のリスト")

    # [実装してみよう] source_url が http/https で始まるかバリデーションを追加する
    @field_validator("source_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("source_url は http:// または https:// で始まる必要があります")
        return v


class NoteUpdate(BaseModel):
    """PATCH /notes/{id} のリクエストボディ（全フィールド任意）"""
    title:      Optional[str]      = Field(None, min_length=1, max_length=200)
    content:    Optional[str]      = Field(None, min_length=1)
    source_url: Optional[str]      = None
    tag_names:  Optional[list[str]] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "NoteUpdate":
        """[考える] PATCH では最低1フィールドが必要。なぜ PUT との違いがあるのか？"""
        if all(v is None for v in [self.title, self.content, self.source_url, self.tag_names]):
            raise ValueError("少なくとも1つのフィールドを指定してください")
        return self


class NoteResponse(BaseModel):
    """GET /notes のレスポンス"""
    id:         int
    title:      str
    content:    str
    source_url: Optional[str]
    tags:       list[TagSchema]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """一覧取得レスポンス（ページネーション情報付き）"""
    items:   list[NoteResponse]
    total:   int
    page:    int
    per_page: int
    # [実装してみよう] has_next, has_prev フィールドを追加する


# 型エイリアスを公開（main.py でのインポートを簡潔にする）
Note     = NoteDB
NoteTag  = TagDB
