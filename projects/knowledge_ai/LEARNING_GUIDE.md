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
  Phase 1: FastAPI + API設計パターン  → CRUD + ページネーション・レート制限・CQRS・冪等性・Circuit Breaker
  Phase 2: LLM + RAG 統合           → LLMを使う側・RAG・ベクターDB

■ インフラ・DevOps
  Phase 3: Docker + K8s 深掘り       → namespaces/cgroups・K8sアーキテクチャ・HPA/KEDA・GPU・GitOps
  Phase 4: CI/CD パターン            → テスト戦略・5デプロイ戦略・Progressive Delivery・ML CI/CD
  Phase 5: クラウドアーキテクチャ      → Well-Architected・DR4戦略・サーバーレス・AWS/GCP対応表
  Phase 6: SRE + 可観測性            → SLI/SLO/SLA・Burn Rate・インシデント対応・カオスエンジニアリング

■ データエンジニアリング
  Phase 7: データエンジニアリング      → Star Schema・DAG実装・データ品質・ストリーム処理・レイクハウス

■ プログラミング言語（ポリグロット）
  Phase LANG: 言語比較 + 選定        → Python弱点・TS/Go/Rust/Java比較・PM選定フレームワーク
  Phase LANG-TS: TypeScript Backend  → Hono REST API・型システム・Generics・Discriminated Unions
  Phase LANG-RS: Rust 基礎           → 所有権・パターンマッチ・trait・並行処理・HTTP自作

■ 応用・専門領域
  Phase 8: Go 並行処理パターン       → goroutine/channel・Worker Pool・Circuit Breaker・Graceful Shutdown
  Phase 9: セキュリティ工学           → OWASP Top10・JWT自作・STRIDE・ゼロトラスト・暗号学
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
| システム設計 | 億ユーザースケールのML基盤・推薦システム | SYS, DS3, Phase 1,5,7 |
| インフラ設計 | K8s・CI/CD・DR戦略・SRE | Phase 3,4,5,6 |
| セキュリティ | OWASP・認証認可・脅威モデリング | Phase 9 |
| データ基盤 | バッチ/ストリーム・データ品質・パイプライン設計 | Phase 7 |
| 言語選定 | 「なぜその言語を選んだ？」技術的トレードオフ | LANG |
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

### Phase 1 - API設計（CRUD + 上級パターン）
```bash
cd phase1_api
pip install -r requirements.txt
uvicorn main:app --reload         # CRUD API → http://localhost:8000/docs
python api_design_patterns.py     # ★上級API設計パターン:
                                  #   Richardson Maturity Model (Level 0-3)
                                  #   ページネーション（Offset vs Cursor 実装）
                                  #   レート制限（Token Bucket / Sliding Window 実装）
                                  #   冪等性（Idempotency Key パターン）
                                  #   CQRS / API Gateway / Circuit Breaker
```

### Phase 2（LLM + RAG）
```bash
export ANTHROPIC_API_KEY="your-key"
pip install langchain langchain-anthropic langchain-community chromadb
# phase2_ai/rag_service.py を読んで RAGService を使ってみる
```

### Phase 3 - Docker/K8s（コンテナ技術の全体像）
```bash
cd phase3_docker
python container_deep_dive.py     # ★コンテナ/K8s の全体像:
                                  #   コンテナの仕組み (namespaces, cgroups, UnionFS)
                                  #   イメージ最適化 (マルチステージ, distroless)
                                  #   K8s アーキテクチャ (Control Plane / Data Plane)
                                  #   リソース設計 (Deployment/StatefulSet/DaemonSet)
                                  #   スケーリング (HPA/VPA/KEDA), Helm, GitOps
                                  #   GPU ワークロード (ML推論 on K8s)
```

### Phase 4 - CI/CD（デプロイ戦略とテスト戦略）
```bash
cd phase4_cicd
python cicd_patterns.py           # ★CI/CDパターン:
                                  #   テスト戦略 (Pyramid, Mock/Stub/Fake 実装)
                                  #   5つのデプロイ戦略 (Rolling/BlueGreen/Canary/FeatureFlag/Shadow)
                                  #   DB マイグレーション (expand-and-contract)
                                  #   シークレット管理 (Vault, rotation)
                                  #   Progressive Delivery, ML CI/CD
```

### Phase 5 - クラウドアーキテクチャ（AWS/GCP 設計）
```bash
cd phase5_cloud
python cloud_architecture.py      # ★クラウドアーキテクチャ:
                                  #   AWS Well-Architected 6本柱
                                  #   マルチAZ/マルチリージョン設計
                                  #   サーバーレス (Lambda + DynamoDB + Step Functions)
                                  #   DB選択 (RDS/Aurora/DynamoDB/ElastiCache/Neptune)
                                  #   災害復旧4戦略 (Backup→Multi-Site)
                                  #   AWS vs GCP サービス対応表 (35+サービス)
                                  #   面接: 100K QPS ML推論基盤の設計
```

### Phase 6 - SRE/可観測性（本番運用の技術）
```bash
cd phase6_observability
python sre_practices.py           # ★SRE実践:
                                  #   SLI/SLO/SLA 定義と Error Budget 計算
                                  #   アラート設計 (Multi-Window Burn Rate)
                                  #   インシデント対応 (Severity分類, Postmortem)
                                  #   カオスエンジニアリング (GameDay計画)
                                  #   PromQL クエリビルダー実装
                                  #   分散トレーシング (W3C TraceContext)
```

### Phase 7 - データエンジニアリング（パイプライン設計）
```bash
cd phase7_data
python data_engineering.py        # ★データエンジニアリング:
                                  #   Star Schema / Data Vault 2.0 (実装付き)
                                  #   バッチ vs ストリーム (Lambda/Kappa Architecture)
                                  #   DAG エグゼキュータ (トポロジカルソートで実装)
                                  #   データ品質チェッカー (6種のチェック実装)
                                  #   レイクハウス (Delta Lake / Iceberg / Hudi)
                                  #   ストリーム処理 (Tumbling/Sliding/Session Window 実装)
                                  #   面接: ライドシェアの1M events/sec パイプライン設計
```

### Phase 8 - Go（並行処理 + マイクロサービス）
```bash
cd phase8_go_service
go run main.go                    # 転置インデックス検索サービス
go run go_concurrency_patterns.go # ★Go並行処理パターン:
                                  #   Fan-out/Fan-in, select, context.Context
                                  #   sync (Mutex/RWMutex/WaitGroup/Once/Pool)
                                  #   Worker Pool, Pipeline パターン
                                  #   Rate Limiter (Token Bucket)
                                  #   Circuit Breaker (状態遷移: Closed→Open→Half-Open)
                                  #   Graceful Shutdown (SIGTERM/SIGINT)
```

### Phase 9 - セキュリティ（OWASP + 暗号 + ゼロトラスト）
```bash
cd phase9_security
python security_deep_dive.py      # ★セキュリティ工学:
                                  #   OWASP Top 10 (脆弱 vs 安全コード比較)
                                  #   暗号学基礎 (HMAC API認証 実装)
                                  #   JWT をスクラッチ実装 + 4つの攻撃デモ
                                  #   OAuth2/OIDC (PKCE 実装)
                                  #   脅威モデリング (STRIDE 分析ツール実装)
                                  #   ゼロトラスト (BeyondCorp, mTLS)
                                  #   面接: マルチテナントSaaSの認証認可設計
```

### Phase LANG - ポリグロットプログラミング（言語選定力）
```bash
cd phase_programming
python polyglot_guide.py              # ★5言語比較ガイド (stdlib のみ):
                                      #   Pythonの弱点 (GIL, 速度, 型安全性, デプロイサイズ)
                                      #   TypeScript: フルスタック・型安全・npm エコシステム
                                      #   Go: goroutine・シングルバイナリ・クラウドネイティブ
                                      #   Rust: 所有権・ゼロコスト抽象化・WebAssembly
                                      #   Java/Kotlin: JVM・Spring Boot・Android
                                      #   同じ TODO API を5言語で比較
                                      #   PM/テックリード向け言語選定フレームワーク
cd ts_backend && npm install && npm run dev  # TypeScript バックエンド (Hono):
                                      #   interface vs type, Generics, Discriminated Unions
                                      #   strictNullChecks, ミドルウェアパターン
cd ../rust_basics && cargo run        # Rust 基礎 (std のみ):
                                      #   所有権 (move/borrow/lifetime)
                                      #   Option<T> / Result<T,E> (null/例外を排除)
                                      #   trait (Pythonの Protocol/ABC の上位互換)
                                      #   fearless concurrency (GILなし並列処理)
                                      #   HTTP サーバーを std のみで自作
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
| Phase 1 | GraphQL API を FastAPI + Strawberry で実装 | ★★★ |
| Phase 1 | Redis でレート制限ミドルウェアを実装 | ★★☆ |
| Phase 3 | minikube でアプリをデプロイして HPA を設定 | ★★★ |
| Phase 3 | Trivy でイメージスキャンを CI に組み込む | ★★☆ |
| Phase 4 | GitHub Actions で Canary デプロイを実装 | ★★★ |
| Phase 5 | Terraform で VPC + ECS Fargate を構築 | ★★★ |
| Phase 5 | Lambda + API Gateway のサーバーレスAPIを構築 | ★★☆ |
| Phase 6 | Prometheus + Grafana でダッシュボードを作成 | ★★☆ |
| Phase 6 | SLO ベースのアラートルールを設計 | ★★★ |
| Phase 7 | dbt で Star Schema のモデルを実装 | ★★☆ |
| Phase 7 | Kafka + Flink で簡易ストリーム処理を構築 | ★★★ |
| Phase 8 | gRPC サーバーを Go で実装 | ★★★ |
| Phase 8 | Go で REST API テストを table-driven で書く | ★★☆ |
| Phase 9 | OWASP ZAP でアプリのセキュリティスキャン | ★★☆ |
| Phase 9 | mTLS でサービス間認証を実装 | ★★★ |
| LANG | TypeScript で Zod バリデーション付き API を実装 | ★★☆ |
| LANG | Rust で Axum フレームワークを使った API を実装 | ★★★ |
| LANG | Go + Rust + Python で同じ処理のベンチマーク比較 | ★★☆ |
| LANG | Kotlin で Spring Boot REST API を実装 | ★★★ |

## 言語・技術選定の理由

| 技術 | 選定理由 | Pythonにない強み |
|---|---|---|
| Python / FastAPI | ML/DSの標準言語・既存スキル活用 | ― (基軸言語) |
| Python / PyTorch | 研究〜本番まで使われるDLフレームワーク | ― |
| TypeScript / Hono | フルスタック・フロントはJSのみ | コンパイル時型安全・Discriminated Unions |
| Go | クラウドネイティブのデファクト | goroutine 並行処理・10MBバイナリ |
| Rust | システムプログラミング・ML基盤 (Ruff, Polars) | 所有権でGCなしメモリ安全・C並速度 |
| Java / Kotlin | エンタープライズ・Android | JVM 20年の最適化・大規模リファクタリング |
| Terraform | AWS/GCPをまたいで使えるデファクトIaCツール | ― |
| Docker / Kubernetes | コンテナ技術の基礎から運用まで | ― |
