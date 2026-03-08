# TechCorp Simulator - 本番環境シミュレーター

テックリード・PM志望者のための実務レベルシミュレーター。
本番環境に潜む10個の問題を発見・修正・判断せよ。

## クイックスタート

```bash
cd projects/techcorp_sim

# 1. サービスを起動（初回は5〜10分かかる）
docker compose up --build -d

# 2. 全サービスの起動を確認
docker compose ps

# 3. シミュレーターを起動
pip install httpx rich
python sim_runner.py
```

## アーキテクチャ

```
[Client] → [API Gateway :8000]
                ├── note_service   :8001  (FastAPI + PostgreSQL)
                ├── search_service :8002  (Go)
                └── analytics_service :8003 (FastAPI + Scheduler)

[Prometheus :9090] ← scrapes all services
[Grafana :3001]    ← visualizes Prometheus data
```

## 埋め込まれた本番バグ一覧

| # | サービス | バグ種別 | 関連スキル |
|---|---------|---------|----------|
| BUG-01 | note_service | N+1クエリ | SQL最適化 |
| BUG-02 | note_service | SQLインジェクション | セキュリティ |
| BUG-03 | note_service | SQL_ECHO本番残存 | 設定管理 |
| BUG-04 | api_gateway | レート制限なし | セキュリティ |
| BUG-05 | api_gateway | JWTシークレットハードコード | Secrets管理 |
| BUG-06 | api_gateway | /searchが未認証 | 認証・認可 |
| BUG-07 | search_service | レースコンディション | 並行処理 |
| BUG-08 | search_service | インメモリのみ（永続化なし） | データ設計 |
| BUG-09 | analytics_service | サイレント例外 | 可観測性 |
| BUG-10 | analytics_service | スケジューラー未実装 | データパイプライン |
| BUG-11 | analytics_service | コネクションリーク | リソース管理 |

## シナリオ

| # | タイトル | 主なスキル | 配点 |
|---|---------|----------|------|
| 1 | 本番パフォーマンス障害 | SQL・DB最適化・可観測性 | 300pt |
| 2 | セキュリティ監査 | SQLi・JWT・認証 | 400pt |
| 3 | データパイプライン障害 | サイレント障害・スケジューリング・PM判断 | 350pt |
| 4 | トラフィックスパイク | スケールアウト・Redis・レート制限 | 350pt |
| 5 | Q3計画会議 | OKR設計・ステークホルダー管理 | 300pt |

## 負荷テスト（シナリオ4用）

```bash
# k6 負荷テストを実行
docker compose --profile load-test up load_generator

# または k6 インストール済みなら直接実行
k6 run --env API_URL=http://localhost:8000 scenarios/load_test.js
```

## 可観測性ダッシュボード

- **Grafana**: http://localhost:3001 (admin/admin)
  - TechCorp Production Dashboard が自動プロビジョニングされる
- **Prometheus**: http://localhost:9090
- **API Docs**: http://localhost:8000/docs

## グレード判定

| グレード | スコア | 評価 |
|---------|------|------|
| S | 1400+ | テックリード・CTOレベル |
| A | 1000-1399 | シニアエンジニア・PM レベル |
| B | 600-999 | ミドルエンジニア |
| C | 0-599 | 要学習 |
