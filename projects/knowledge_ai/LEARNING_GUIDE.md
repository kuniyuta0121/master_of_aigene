# KnowledgeAI - 学習ガイド

## アプリの全体像

「AIナレッジ管理システム」を段階的に育てる。
**データサイエンティスト → テックリード/PM** を目指す構成。

```
■ FAANG通過に必要な基礎（★最優先）
  Phase DS0: 統計・確率の基礎       → ベイズ定理・仮説検定・A/Bテスト・因果推論
  Phase ALGO: アルゴリズム&DS       → Two Pointers・DP・Graph・LeetCode Hard

■ データサイエンス基盤
  Phase DS1: ML Foundation          → 機械学習・アンサンブル学習 (scikit-learn)
  Phase DS2: Deep Learning          → 深層学習・Attention・転移学習 (PyTorch)
  Phase DS3: MLOps                  → 実験管理・モデル本番化・ドリフト検知 (MLflow)

■ API・バックエンド
  Phase 1: FastAPI CRUD API          → Python上級・API設計
  Phase 2: LLM + RAG 統合           → LLMを使う側・RAG・ベクターDB

■ インフラ・DevOps
  Phase 3: Docker コンテナ化         → Docker・コンテナ化
  Phase 4: GitHub Actions CI/CD      → CI/CD
  Phase 5: Terraform + AWS           → IaC・クラウドアーキテクチャ
  Phase 6: Prometheus + OpenTelemetry → 可観測性

■ データエンジニアリング
  Phase 7: Airflow + dbt             → データパイプライン設計

■ 応用・専門領域
  Phase 8: Go マイクロサービス        → Go言語・並行処理
  Phase 9: JWT認証 + セキュリティ     → セキュリティ
  Phase 10: Next.js フロントエンド    → TypeScript・React・Next.js
```

## 推奨学習順序（Google/Tesla/IBM レベル志向）

```
DS0 → ALGO → DS1 → DS2 → DS3 → Phase 1 → Phase 2 → Phase 7 → Phase 3〜10
 ↑      ↑      ↑                    ↑
統計   面接   ML作る              MLをAPIに
基礎   突破
```

### Google/Tesla/IBM 面接で何が問われるか

| 面接種別 | 問われること | 対応フェーズ |
|---------|------------|-------------|
| コーディング | LeetCode Medium/Hard | ALGO |
| ML理論 | ベイズ・過学習・損失関数の数学的根拠 | DS0, DS1 |
| システム設計 | 億ユーザースケールのML基盤 | DS3, Phase 1,7 |
| 行動面接 | 技術的意思決定・チームリード | techcorp_sim シナリオ5 |

## 各フェーズの始め方

### Phase DS0 - 統計・確率（最初に入れる土台）
```bash
cd phase_ds0_stats
pip install -r requirements.txt
python statistics_foundations.py
# → ベイズの定理、信頼区間、仮説検定、A/Bテスト設計、因果推論
# → 「p値とは何か」を統計学的に正確に説明できるようになる
```

### Phase ALGO - アルゴリズム（面接突破の必須条件）
```bash
cd phase_algo
python algo_foundations.py  # 標準ライブラリのみ、追加インストール不要
# → Two Pointers, Sliding Window, Binary Search
# → Heap, Union-Find, Dynamic Programming
# → LeetCode Hard レベルの問題を解説付きで実装
# 練習: https://leetcode.com/study-plan/  目標: 3ヶ月でMedium100問+Hard30問
```

### Phase DS1 - ML基礎
```bash
cd phase_ds1_ml_foundation
pip install -r requirements.txt
python ml_pipeline.py
# → タグ自動付与（分類）と閲覧数予測（回帰）を実装
# → Random Forest / Gradient Boosting / Voting のアンサンブル比較
```

### Phase DS2 - 深層学習
```bash
cd phase_ds2_deep_learning
pip install torch
python neural_net.py
# → SimpleNN / LSTM / Self-Attention の3アーキテクチャを比較
# → Apple Silicon は MPS、NVIDIA は CUDA が自動選択される
```

### Phase DS3 - MLOps
```bash
cd phase_ds3_mlops
pip install -r requirements.txt
python mlops_pipeline.py
# MLflow UI で実験を可視化（オプション）
pip install mlflow
mlflow ui  # → http://localhost:5000
```

### Phase 1（API設計）
```bash
cd phase1_api
pip install -r requirements.txt
uvicorn main:app --reload
# http://localhost:8000/docs でSwagger UIが開く
```

### Phase 2（LLM + RAG）
```bash
export ANTHROPIC_API_KEY="your-key"
pip install langchain langchain-anthropic langchain-community chromadb
# phase2_ai/rag_service.py を読んで RAGService を使ってみる
# ※ Phase DS2 で学んだ Embedding が RAG の核心
```

### Phase 8（Go サービス）
```bash
cd phase8_go_service
go mod init knowledge-ai-search
go run main.go
curl "http://localhost:8001/search?q=Python"
```

### Phase 10（フロントエンド）
```bash
cd phase10_frontend
npm install
npm run dev
# http://localhost:3000 でUIが開く
```

## 学習の進め方

1. **コードを読む** → コメントの「考えてほしい疑問」を声に出す
2. **動かす** → 実際にAPIを叩いてレスポンスを確認する
3. **壊す** → わざとエラーを起こして挙動を学ぶ
4. **改造する** → `[実装してみよう]` のタスクを実装する
5. **調べる** → 疑問が生まれたら深掘りする（書籍・ドキュメント）

## 全フェーズの「実装してみよう」一覧

| フェーズ | タスク | 難易度 |
|---------|-------|--------|
| DS0 | statsmodels でA/Bテストのサンプルサイズを計算 | ★★☆ |
| DS0 | PyMC でベイズ線形回帰を実装 | ★★★ |
| ALGO | Trie, Segment Tree, Topological Sort を追加実装 | ★★★ |
| ALGO | LeetCode 75問セットを時間計測で解く | ★★★ |
| DS1 | LightGBM を pip install して RF/GBM と比較 | ★★☆ |
| DS1 | SHAP で特徴量の影響を可視化 | ★★☆ |
| DS2 | GRU に置き換えて LSTM と比較 | ★★★ |
| DS2 | sentence-transformers で埋め込み取得 | ★★☆ |
| DS3 | evidently でドリフト検知レポートを生成 | ★★★ |
| DS3 | モデルを FastAPI でサーブして /predict を叩く | ★★☆ |

## 言語・技術選定の理由

| 技術 | 選定理由 |
|---|---|
| Python / scikit-learn | ML の事実上の標準ライブラリ |
| Python / PyTorch | Meta 発・研究〜本番まで使われるDLフレームワーク |
| MLflow | OSS の実験管理・モデルレジストリのデファクト |
| Python / FastAPI | 既存スキルの延長・AI/MLの主要言語 |
| TypeScript / Next.js | フロントエンド経験を型安全に発展させる |
| Go | クラウドネイティブのデファクト・並行処理学習 |
| Terraform | AWS/GCPをまたいで使えるデファクトIaCツール |
| Docker / Kubernetes | コンテナ技術の基礎から運用まで |
