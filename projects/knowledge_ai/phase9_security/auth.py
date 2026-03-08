"""
Phase 9: セキュリティ強化 - JWT認証 + OWASP対策
=================================================
学習目標:
  - JWT（JSON Web Token）の仕組みを実装して理解する
  - OAuth2 Password Flow を FastAPI で実装する
  - OWASP Top 10 の具体的な対策コードを書く

考えてほしい疑問:
  Q1. JWT をサーバーサイドで保存しないのはなぜか？（ステートレス認証の意味）
  Q2. access_token の有効期限を短く（15分）する理由は？refresh_token との組み合わせは？
  Q3. パスワードを平文でDBに保存してはいけない理由は？bcryptの強みは？
  Q4. このコードで防げていない攻撃は何か？（ブルートフォース対策？）

main.py への追加:
  from phase9_security.auth import auth_router, get_current_user
  app.include_router(auth_router)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import Session

from database import get_db
from models import Base

# JWT 設定
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production-use-256bit-random")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # 短め（セキュリティのため）
REFRESH_TOKEN_EXPIRE_DAYS = 7

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# --- ユーザーモデル ---

class UserDB(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    email         = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class UserCreate(BaseModel):
    email:    EmailStr  # メールアドレスの自動バリデーション
    password: str


class Token(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


# --- パスワードハッシュ ---

def hash_password(password: str) -> str:
    """
    bcrypt でパスワードをハッシュ化する。
    なぜ bcrypt か:
    - ソルト自動付与（レインボーテーブル攻撃への対策）
    - コスト因数（計算時間調整）でブルートフォースを遅くできる
    - SHA256等より安全なパスワード専用アルゴリズム
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- JWT 操作 ---

def create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無効なトークンです")


# --- 依存性注入: 認証済みユーザーを取得 ---

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> UserDB:
    """
    JWTトークンを検証して現在のユーザーを返す。
    FastAPI の Depends() で各エンドポイントに注入する。

    使い方:
      @router.get("/notes")
      async def list_notes(current_user: UserDB = Depends(get_current_user)):
          ...
    """
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="不正なトークン")

    user = db.query(UserDB).filter(UserDB.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")

    return user


# --- エンドポイント ---

@auth_router.post("/register", status_code=201)
async def register(body: UserCreate, db: Session = Depends(get_db)):
    """
    ユーザー登録。

    OWASP対策:
    - パスワードはbcryptでハッシュ化（平文保存禁止）
    - メールアドレスはPydanticのEmailStrで検証
    - [実装してみよう] パスワード強度チェック（8文字以上・大小文字・記号）を追加
    """
    existing = db.query(UserDB).filter(UserDB.email == body.email).first()
    if existing:
        # [考える] なぜ「このメールは登録済み」と正確に教えてはいけないのか？
        # （ユーザー列挙攻撃の防止）
        raise HTTPException(status_code=400, detail="登録に失敗しました")

    user = UserDB(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"message": "登録完了"}


@auth_router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    ログイン → JWT発行。

    [実装してみよう]
    - 5回連続失敗したらアカウントを一時ロック（Redis で試行回数を管理）
    - これが「ブルートフォース攻撃対策」
    """
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()

    # [考える] ユーザーが存在しない場合とパスワード不一致の場合で
    # エラーメッセージを変えてはいけない理由は？（ユーザー列挙攻撃の防止）
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが誤っています")

    access_token = create_token(
        {"sub": str(user.id), "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_token(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return Token(access_token=access_token, refresh_token=refresh_token)
