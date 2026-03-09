# KnowledgeAI - 学習ガイド

## アプリの全体像

「AIナレッジ管理システム」を段階的に育てる。
**データサイエンティスト → テックリード/PM** を目指す構成。

```
■ FAANG通過に必要な基礎（★最優先）
  Phase DS0: 統計・確率の基礎       → ベイズ定理・仮説検定・A/Bテスト・因果推論・情報理論
  Phase ALGO: アルゴリズム&DS       → Two Pointers・DP・Graph・Trie・Segment Tree・Bitmask DP

■ データサイエンス基盤（スクラッチ実装 + フレームワーク）
  Phase DS1: ML Foundation          → ML from scratch (NumPy) + scikit-learn パイプライン
  Phase DS2: Deep Learning          → Transformer from scratch (NumPy autograd) + PyTorch
  Phase DS3: MLOps                  → 実験管理・モデル本番化・ドリフト検知 (MLflow)
  Phase DS4: Computer Vision        → CNN・ResNet・ViT from scratch + 物体検出 (IoU/NMS)
  Phase SYS: ML System Design       → 推薦システム・Feature Store・Model Serving・面接対策

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
DS0 → ALGO → DS1 → DS2 → DS4 → DS3 → SYS → Phase 1 → Phase 2 → Phase 7 → Phase 3〜10
 ↑      ↑      ↑     ↑     ↑     ↑     ↑
統計   面接   ML   DL   CV   本番  設計
基礎   突破   作る  作る  作る  運用  面接
```

### Google/Tesla/IBM 面接で何が問われるか

| 面接種別 | 問われること | 対応フェーズ |
|---------|------------|-------------|
| コーディング | LeetCode Medium/Hard | ALGO |
| ML理論 | ベイズ・過学習・損失関数の数学的根拠 | DS0, DS1, DS2 |
| ML実装力 | 勾配降下法・逆伝播・Transformerをスクラッチ実装 | DS1(from_scratch), DS2(transformer) |
| CV/NLP | CNN・ResNet・ViT・Attention の原理と実装 | DS4, DS2 |
| システム設計 | 億ユーザースケールのML基盤・推薦システム | SYS, DS3, Phase 1,7 |
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
python algo_foundations.py   # 基礎: Two Pointers, Sliding Window, Binary Search, Heap, Union-Find, DP
python advanced_algo.py      # 上級: Graph(BFS/DFS/TopSort/WordLadder), Trie, Segment Tree
                             #       Backtracking(N-Queens/Permutations), KMP, Monotonic Stack
                             #       Bitmask DP (TSP), Matrix Chain Multiplication
# 標準ライブラリのみ、追加インストール不要
# 練習: https://leetcode.com/study-plan/  目標: 3ヶ月でMedium100問+Hard30問
```

### Phase DS1 - ML基礎（scikit-learn + スクラッチ実装）
```bash
cd phase_ds1_ml_foundation
pip install -r requirements.txt
python ml_pipeline.py          # scikit-learn: 分類・回帰・アンサンブル比較
python ml_from_scratch.py      # ★NumPyのみで6アルゴリズムを実装:
                               #   Linear Regression (正規方程式 + 勾配降下法)
                               #   Logistic Regression (シグモイド + 交差エントロピー + L2正則化)
                               #   Decision Tree (エントロピー/ジニ + 再帰分割)
                               #   K-Means (K-Means++ 初期化 + エルボー法)
                               #   PCA (SVD分解 + 累積寄与率)
                               #   Naive Bayes (ラプラス平滑化 + 対数空間計算)
```

### Phase DS2 - 深層学習（PyTorch + Transformer スクラッチ）
```bash
cd phase_ds2_deep_learning
pip install torch
python neural_net.py               # PyTorch: SimpleNN / LSTM / Self-Attention 比較
python transformer_from_scratch.py  # ★NumPyのみでTransformerを完全実装:
                                    #   Tensor クラス（自動微分エンジン: forward/backward）
                                    #   Positional Encoding (sin/cos)
                                    #   Scaled Dot-Product Attention (QK^T/√d_k + マスキング)
                                    #   Multi-Head Attention (ヘッド分割 + W_Q/W_K/W_V/W_O)
                                    #   Layer Normalization, Position-wise FFN
                                    #   Transformer Encoder (残差接続 + 正規化)
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

### Phase DS4 - Computer Vision（CNN・ResNet・ViT）
```bash
cd phase_ds4_computer_vision
pip install -r requirements.txt  # torch, torchvision, matplotlib, numpy
python cv_from_scratch.py
# → 2D畳み込みをNumPyでスクラッチ実装
# → SimpleCNN (LeNet + BatchNorm) / MiniResNet (残差接続) / MiniViT (パッチ埋め込み)
# → 物体検出の基礎: IoU (Intersection over Union), NMS (Non-Max Suppression)
# → MNIST で CNN vs ResNet vs ViT を性能比較
```

### Phase SYS - MLシステム設計（面接の最重要フェーズ）
```bash
cd phase_system_design
python ml_system_design.py  # 標準ライブラリのみ
# → 推薦システム設計 (2段階: 候補生成 + ランキング)
# → Feature Store アーキテクチャ (バッチ/リアルタイム/静的特徴量)
# → Model Serving パターン (同期/非同期/ストリーム/エッジ)
# → 設計問題3題: 不正検知(Google Pay), 画像検索(Google Lens), 自動運転(Tesla)
# → 面接 Deep Dive: コールドスタート, レイテンシSLA, 100K QPS スケーリング
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
| DS4 | YOLOv8 で物体検出を実装して mAP を計測 | ★★★ |
| DS4 | Grad-CAM で CNN の判断根拠を可視化 | ★★☆ |
| DS4 | Data Augmentation を追加して精度向上を検証 | ★★☆ |
| SYS | FAISS で 100万ベクトルの ANN 検索を実装 | ★★★ |
| SYS | Feast で Feature Store をローカル構築 | ★★★ |
| SYS | BentoML でモデルを本番サービングする | ★★☆ |

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
