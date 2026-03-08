"""
test_notes.py - APIのテストコード
===================================
学習ポイント:
  - pytest + httpx でFastAPIのエンドポイントをテストする
  - テストDBを本番DBと分離する方法（インメモリSQLite）
  - テストの「Arrange / Act / Assert」パターン

考えてほしい疑問:
  Q1. テストで本番DBを使わない理由は何か？
  Q2. fixture とは何か？なぜ使うのか？
  Q3. このテストで何がテストできていないか（テスト漏れ）？

実行方法:
  pytest test_notes.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from models import Base

# テスト用インメモリDBを使う（本番DBに影響しない）
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用のDBセッションで上書きする（DIの活用）"""
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """各テスト前にDBをリセットする"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- テストケース ---

def test_create_note(client):
    """ノート作成の正常系テスト"""
    # Arrange（準備）
    payload = {"title": "FastAPIの学習", "content": "依存性注入が面白い", "tag_names": ["python", "fastapi"]}

    # Act（実行）
    response = client.post("/api/v1/notes", json=payload)

    # Assert（検証）
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "FastAPIの学習"
    assert len(data["tags"]) == 2
    assert data["id"] is not None


def test_create_note_invalid_url(client):
    """不正なURLでバリデーションエラーになるか"""
    payload = {"title": "テスト", "content": "内容", "source_url": "not-a-url"}
    response = client.post("/api/v1/notes", json=payload)
    assert response.status_code == 422  # Unprocessable Entity


def test_get_note_not_found(client):
    """存在しないノートは404になるか"""
    response = client.get("/api/v1/notes/999")
    assert response.status_code == 404


def test_list_notes_with_search(client):
    """キーワード検索が機能するか"""
    client.post("/api/v1/notes", json={"title": "Pythonの非同期処理", "content": "asyncio について"})
    client.post("/api/v1/notes", json={"title": "Docker入門", "content": "コンテナとは何か"})

    response = client.get("/api/v1/notes?q=Python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Pythonの非同期処理"


def test_update_note(client):
    """PATCH で部分更新できるか"""
    create_res = client.post("/api/v1/notes", json={"title": "元のタイトル", "content": "内容"})
    note_id = create_res.json()["id"]

    update_res = client.patch(f"/api/v1/notes/{note_id}", json={"title": "更新後のタイトル"})
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "更新後のタイトル"
    assert update_res.json()["content"] == "内容"  # 未変更フィールドは保持される


def test_delete_note(client):
    """削除後に404になるか"""
    create_res = client.post("/api/v1/notes", json={"title": "削除するノート", "content": "内容"})
    note_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/notes/{note_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/v1/notes/{note_id}")
    assert get_res.status_code == 404


# [実装してみよう]
# 1. ページネーションのテスト（20件以上作ってpage=2をテスト）
# 2. タグフィルタのテスト
# 3. 空のタイトルで422になるかテスト
