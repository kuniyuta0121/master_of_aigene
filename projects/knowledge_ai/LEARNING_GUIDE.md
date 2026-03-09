# KnowledgeAI - 学習ガイド

## アプリの全体像

「AIナレッジ管理システム」を段階的に育てる。
**データサイエンティスト → テックリード/PM** を目指す構成。

```
■ FAANG通過に必要な基礎（★最優先）
  Phase DS0: 統計・確率の基礎       → ベイズ定理・仮説検定・A/Bテスト・因果推論・情報理論
  Phase ALGO: アルゴリズム&DS       → Two Pointers・DP・Graph・Trie・Segment Tree・Bitmask DP
  Phase CS: CS基盤                  → OS(スケジューラ/仮想メモリ)・TCP/IP・DB内部(B-Tree/LSM/MVCC)・GC・並行処理

■ データサイエンス基盤（スクラッチ実装 + フレームワーク）
  Phase DS1: ML Foundation          → ML from scratch (NumPy) + scikit-learn パイプライン
  Phase DS2: Deep Learning          → Transformer from scratch (NumPy autograd) + PyTorch
  Phase DS3: MLOps                  → 実験管理・モデル本番化・ドリフト検知 (MLflow)
  Phase DS4: Computer Vision        → CNN・ResNet・ViT from scratch + 物体検出 (IoU/NMS)
  Phase SYS: ML System Design       → 推薦システム・Feature Store・Model Serving・面接対策

■ API・バックエンド
  Phase 1: FastAPI + API設計パターン  → CRUD + ページネーション・レート制限・CQRS・冪等性・Circuit Breaker
  Phase 2: LLM + RAG 統合           → Advanced RAG・AIエージェント・プロンプトエンジニアリング・ベクターDB

■ インフラ・DevOps
  Phase 3: Docker + K8s 深掘り       → namespaces/cgroups・K8sアーキテクチャ・HPA/KEDA・GPU・GitOps
  Phase 4: CI/CD パターン            → テスト戦略・5デプロイ戦略・Progressive Delivery・ML CI/CD
  Phase 5: クラウドアーキテクチャ      → Well-Architected・DR4戦略・サーバーレス・AWS/GCP対応表
  Phase 6: SRE + 可観測性            → SLI/SLO/SLA・Burn Rate・インシデント対応・カオスエンジニアリング
  Phase DEVOPS: DevOpsハンズオン      → Docker実践・K8s Day-2・Terraform・CI/CD・FinOps・クラウドセキュリティ

■ データエンジニアリング
  Phase 7: データエンジニアリング      → Star Schema・DAG実装・データ品質・ストリーム処理・レイクハウス
  Phase 7+: SQL上級 + NoSQL          → Window関数・CTE・インデックス・DynamoDB/MongoDB/Redis設計

■ アーキテクチャ設計
  Phase ARCH: システム設計パターン     → マイクロサービス・DDD・Event Sourcing・分散システム・面接設計問題
  Phase DIST: 分散システム深掘り       → Raft合意・CRDT・2PC/Saga・Quorum・HLC・Snowflake ID・Phi Accrual

■ プログラミング言語（ポリグロット）
  Phase LANG: 言語比較 + 選定        → Python弱点・TS/Go/Rust/Java比較・PM選定フレームワーク
  Phase LANG-TS: TypeScript Backend  → Hono REST API・型システム・Generics・Discriminated Unions
  Phase LANG-RS: Rust 基礎           → 所有権・パターンマッチ・trait・並行処理・HTTP自作
  Phase PY+: Python上級              → async/await・メタクラス・型システム・パフォーマンス・テスト技法
  Phase PATTERN: デザインパターン      → GoF 23パターン・SOLID・並行処理パターン・アンチパターン
  Phase PERF: パフォーマンス工学       → CPU cache・Bloom Filter・HyperLogLog・Tail Latency・ベンチマーク

■ PM・リーダーシップ
  Phase PM: テクニカルPM             → アジャイル・OKR・RICE・ADR・ステークホルダー・戦略・面接対応
  Phase STAFF+: Staff+リーダーシップ   → 技術戦略・組織設計・DORA/SPACE・Staff+面接・Build vs Buy

■ 応用・専門領域
  Phase 8: Go 並行処理パターン       → goroutine/channel・Worker Pool・Circuit Breaker・Graceful Shutdown
  Phase 9: セキュリティ工学           → OWASP Top10・JWT自作・STRIDE・ゼロトラスト・暗号学
  Phase 10: Next.js フロントエンド    → TypeScript・React・Next.js
  Phase FRONT: フロントエンド工学      → Virtual DOM・Next.js SSR/SSG/ISR・Core Web Vitals・CSS・状態管理・テスト

■ リファレンス
  用語集 (glossary.py)               → 50+専門用語・カテゴリ別・検索機能付き
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
| データ基盤 | バッチ/ストリーム・データ品質・パイプライン設計 | Phase 7, 7+ |
| SQL/NoSQL | Window関数・DynamoDB設計・「なぜこのDBを選んだ」 | Phase 7+ |
| 汎用システム設計 | URL Shortener, Chat, News Feed, Rate Limiter | ARCH |
| マイクロサービス | Saga, Event Sourcing, CQRS, DDD | ARCH |
| デザインパターン | GoF, SOLID, 「このシステムにどのパターンを適用するか」 | PATTERN |
| 言語選定 | 「なぜその言語を選んだ？」技術的トレードオフ | LANG |
| AI/LLM | RAGアーキテクチャ・エージェント設計・プロンプト | Phase 2 |
| PM面接 | Product Sense, Execution, メトリクス | PM |
| 行動面接 | STAR, 技術的意思決定・チームリード | PM, techcorp_sim |
| CS基盤 | OS, ネットワーク, DB内部, GC の「なぜ」 | CS |
| 分散システム | Raft, CRDT, Saga, Quorum の設計と実装 | DIST |
| パフォーマンス | ボトルネック特定, Tail Latency, 計測手法 | PERF |
| Staff+設計 | プラットフォーム設計, 移行計画, 組織影響 | STAFF+ |
| Staff+行動 | Influence without authority, 曖昧さの対処 | STAFF+ |

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

### Phase 2 - AI/LLM（エージェント + Advanced RAG）
```bash
cd phase2_ai
python ai_agents_and_rag.py          # ★AI エージェント & RAG (stdlib のみ):
                                      #   プロンプトエンジニアリング (テンプレートエンジン実装)
                                      #   チャンキング戦略 (Fixed/Recursive/Semantic)
                                      #   BM25 検索エンジン実装
                                      #   Hybrid Retrieval (BM25 + Vector)
                                      #   RAGAS 評価指標 (Faithfulness/Relevancy/Precision)
                                      #   ReAct エージェント (Thought→Action→Observation)
                                      #   Multi-Agent (Supervisor/Debate/Swarm)
                                      #   HNSW ベクトル検索アルゴリズム実装
                                      #   LLMOps (コスト追跡, トレーシング)
                                      #   面接: 100万ドキュメントRAG設計
# RAG を実際の LLM で動かす場合:
export ANTHROPIC_API_KEY="your-key"
pip install langchain langchain-anthropic chromadb
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
python cloud_services_catalog.py  # ★クラウドサービスカタログ (100+サービス):
                                  #   10カテゴリ別 AWS/GCP サービス一覧
                                  #   各サービス: 用途・使うべき場面・使うべきでない場面・料金・代替
                                  #   メッセージング比較: SQS vs SNS vs EventBridge vs Kinesis vs Kafka
                                  #   DynamoDB Streams / Kinesis Data Firehose 詳細解説
                                  #   7つのアーキテクチャパターン (ASCII図付き)
                                  #   面接: ECサイト設計 / リアルタイム不正検知設計
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
python sql_nosql_deep_dive.py    # ★SQL上級 + NoSQL (sqlite3):
                                  #   Window Functions (ROW_NUMBER/RANK/LAG/LEAD)
                                  #   CTE (再帰CTE でツリー構造走査)
                                  #   インデックス戦略 (B-Tree, 複合, カバリング)
                                  #   DynamoDB Single-Table Design (GSI設計)
                                  #   MongoDB Aggregation Pipeline シミュレーション
                                  #   Redis パターン (Cache-Aside, Sorted Set, Pub/Sub)
                                  #   面接SQL: 連続ログイン日数, 中央値, ファネル分析
```

### Phase ARCH - アーキテクチャ設計（システム設計面接の核心）
```bash
cd phase_architecture
python system_design_patterns.py # ★システム設計パターン:
                                  #   マイクロサービス (Saga, Circuit Breaker, API Gateway)
                                  #   DDD (Aggregate, Value Object, Bounded Context)
                                  #   Event Sourcing + CQRS (実装付き)
                                  #   分散システム (Consistent Hashing, Vector Clock, Gossip)
                                  #   面接設計問題 (URL Shortener, Rate Limiter, Chat, News Feed)
                                  #   スケーラビリティ (Sharding, Cache戦略, Back-pressure)
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
python python_advanced.py            # ★Python上級 (stdlib のみ):
                                      #   async/await (イベントループ, Semaphore, async generator)
                                      #   メタプログラミング (@retry/@cache, メタクラス, descriptor)
                                      #   型システム (TypeVar, Generic, Protocol, overload, mypy)
                                      #   パフォーマンス (__slots__, generator, lru_cache, struct)
                                      #   テスト技法 (Mock, patch, Stub/Fake/Spy, Property-based)
                                      #   Pythonic イディオム (walrus, match-case, EAFP)
python design_patterns.py            # ★デザインパターン (stdlib のみ):
                                      #   生成 (Singleton, Factory, Builder, Prototype)
                                      #   構造 (Adapter, Decorator, Proxy, Facade, Composite)
                                      #   振る舞い (Strategy, Observer, Command, State, Chain of Resp.)
                                      #   モダン (Repository, Unit of Work, DI, Specification)
                                      #   並行処理 (Producer-Consumer, Thread Pool, Actor Model)
                                      #   SOLID原則とパターンの対応マッピング
```

### Phase PM - テクニカルPM・リーダーシップ
```bash
cd phase_pm
python tech_pm_leadership.py         # ★PM/Tech Lead 完全ガイド:
                                      #   アジャイル (Sprint計画, Burndown, WIPシミュレーション)
                                      #   プロダクトディスカバリー (RICE, Impact Mapping, JTBD)
                                      #   OKR・メトリクス (AARRR, LTV/CAC, Retention Curve)
                                      #   ステークホルダー (RACI, Power/Interest Grid, SBI)
                                      #   テクニカルPM (ADR, Tech Debt, トレードオフ分析)
                                      #   プロダクト戦略 (TAM/SAM/SOM, Porter, PMF, Chasm)
                                      #   リーダーシップ (1:1, Health Check, スキルマトリクス)
                                      #   面接 (STAR, Product Sense, Execution問題)
```

### Phase CS - CS基盤（Staff+面接の必須知識）
```bash
cd phase_cs_fundamentals
python cs_internals.py              # ★CS基盤 (stdlib のみ):
                                      #   OS: プロセススケジューラ (Round Robin 実装)
                                      #   OS: 仮想メモリ (ページテーブル + TLB + LRU 実装)
                                      #   OS: Buddy System メモリアロケータ実装
                                      #   OS: I/Oモデル5種比較, デッドロック検出
                                      #   Net: TCP ステートマシン + 輻輳制御シミュレーション
                                      #   Net: HTTP/1.1 vs 2 vs 3, DNS解決, ロードバランシング
                                      #   DB: B-Tree 実装 (挿入・検索・分割)
                                      #   DB: LSM-Tree 実装 (MemTable→SSTable→Compaction)
                                      #   DB: MVCC + Snapshot Isolation 実装
                                      #   Concurrency: Lock-Free Stack (CAS), Work Stealing
                                      #   Runtime: Lexer→Parser→AST→評価器, Mark-Sweep GC
```

### Phase DIST - 分散システム深掘り（DDIA の実装版）
```bash
cd phase_architecture
python distributed_systems_deep.py  # ★分散システム (stdlib のみ):
                                      #   Raft 合意: Leader選出 + ログ複製 + 障害回復
                                      #   Vector Clock: 因果関係追跡
                                      #   CRDT: G-Counter, PN-Counter, OR-Set (収束保証)
                                      #   2PC: Prepare→Commit/Abort
                                      #   Saga: Orchestration + 補償トランザクション
                                      #   Outbox Pattern: DB+メッセージのアトミック性
                                      #   Quorum: R+W>N, Sloppy Quorum, Read Repair
                                      #   Consistent Hashing: Virtual Nodes + 再分散計測
                                      #   HLC: ハイブリッド論理時計
                                      #   Snowflake ID: 64-bit 分散ID生成
                                      #   Phi Accrual: 適応的障害検出
```

### Phase PERF - パフォーマンス工学（計測→最適化→検証）
```bash
cd phase_programming
python performance_engineering.py   # ★パフォーマンス工学 (stdlib のみ):
                                      #   CPU cache: Row-major vs Column-major ベンチマーク
                                      #   メモリ: Python オブジェクトサイズ, __slots__
                                      #   Bloom Filter: 確率的メンバーシップテスト実装
                                      #   Count-Min Sketch: ストリーム頻度推定実装
                                      #   HyperLogLog: カーディナリティ推定実装
                                      #   キャッシュ: LRU vs LFU 比較, Cache Stampede 対策
                                      #   N+1 問題: デモ + バッチ解決
                                      #   Rate Limiting: Token Bucket, Sliding Window
                                      #   ベンチマークハーネス: warmup, P95/P99, stddev
                                      #   Tail Latency: Fan-out amplification シミュレーション
                                      #   Apdex Score: SLO設計の基礎
```

### Phase STAFF+ - Staff+リーダーシップ（Senior→Staffの壁を越える）
```bash
cd phase_pm
python staff_plus_leadership.py     # ★Staff+リーダーシップ (stdlib のみ):
                                      #   Technology Radar (Adopt/Trial/Assess/Hold)
                                      #   Build vs Buy フレームワーク + TCO計算
                                      #   Technical Vision ドキュメントテンプレート
                                      #   Team Topologies + 認知負荷アセスメント
                                      #   Engineering Levels (IC3→IC7) + Senior→Staff差
                                      #   DACI 意思決定, Pre-mortem 分析
                                      #   技術的負債四象限, 投資配分 (70-20-10)
                                      #   DORA メトリクス (Elite/High/Medium/Low)
                                      #   SPACE Framework, OKR カスケード
                                      #   技術→ビジネスインパクト変換
                                      #   BLUF, RFC テンプレート, Pyramid Principle
                                      #   Staff+ 面接: プラットフォーム設計, Behavioral
```

### Phase DEVOPS - DevOpsハンズオン（実践的インフラスキル）
```bash
cd phase_devops
python devops_hands_on.py           # ★DevOps実践ガイド (stdlib のみ):
                                      #   Docker パターン (マルチステージ, Compose, セキュリティ)
                                      #   K8s Day-2 (Pod lifecycle, デプロイ戦略, RBAC, トラブルシュート)
                                      #   Terraform IaC (HCL, State管理, モジュール, ライフサイクル)
                                      #   CI/CD パイプライン (GitHub Actions, キャッシュ, GitOps)
                                      #   FinOps (コストモデル, Right-sizing, コスト配賦)
                                      #   クラウドセキュリティ (共有責任, IAM, VPC, 暗号化, コンプライアンス)
```

### Phase FRONT - フロントエンド工学（React/Next.js/パフォーマンス）
```bash
cd phase10_frontend
python frontend_engineering.py      # ★フロントエンド工学 (stdlib のみ):
                                      #   React (Virtual DOM diff実装, Hooks, Reconciliation)
                                      #   Next.js (SSR/SSG/ISR シミュレーション, App Router)
                                      #   Web Performance (Core Web Vitals, Bundle最適化, Lighthouse)
                                      #   CSS (Specificity計算機, Flexbox/Grid, CSS-in-JS比較)
                                      #   状態管理 (Redux実装, Context API, Zustand/Jotai)
                                      #   テスト (Testing Trophy, E2E, アクセシビリティ)
                                      #   セキュリティ (XSS, CSRF, CSP, CORS)
```

### Phase 10（フロントエンド - Next.js実装）
```bash
cd phase10_frontend
npm install
npm run dev
# http://localhost:3000 でUIが開く
```

### 用語集（専門用語リファレンス）
```bash
python glossary.py                   # 全用語一覧表示
python glossary.py search Sidecar    # 用語を検索
python glossary.py category ARCH     # カテゴリ別表示
# → 50+用語: Sidecar, Ambassador, Saga, CQRS, Gossip Protocol 等
# → 各用語: 日本語名・一行説明・詳細・関連ファイル・関連用語
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
| Phase 5 | AWS Free Tier でサーバーレス Web パターンを構築しコスト監視 | ★★☆ |
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
| Phase 2 | LangChain で Hybrid RAG パイプラインを構築 | ★★★ |
| Phase 2 | ReAct エージェントに Web 検索ツールを追加 | ★★☆ |
| Phase 2 | RAGAS で RAG パイプラインの品質を定量評価 | ★★★ |
| Phase 7+ | LeetCode Database 問題を30問解く | ★★☆ |
| Phase 7+ | DynamoDB Single-Table Design で自分のアプリを設計 | ★★★ |
| ARCH | Saga パターンで注文→在庫→決済の連携を実装 | ★★★ |
| ARCH | Event Sourcing + CQRS でブログシステムを実装 | ★★★ |
| ARCH | Consistent Hashing でキャッシュ分散を実装 | ★★☆ |
| PATTERN | 自分のプロジェクトに適用可能なパターンを3つ特定する | ★★☆ |
| PATTERN | Command パターンで Undo/Redo 付きエディタを作る | ★★★ |
| PY+ | asyncio で並行 HTTP クライアントを実装 | ★★☆ |
| PY+ | mypy --strict で既存コードを型チェックする | ★★☆ |
| PM | 自分のプロジェクトの RICE スコアリングを実施 | ★★☆ |
| PM | ADR を1つ書いて技術選定の理由を記録する | ★★☆ |
| PM | STAR メソッドで面接回答を3つ準備する | ★★★ |
| DEVOPS | LocalStack で Terraform apply → plan → destroy を実践 | ★★☆ |
| DEVOPS | minikube で Rolling Update → Canary デプロイを実行 | ★★★ |
| DEVOPS | GitHub Actions で Docker build + test + push パイプラインを構築 | ★★☆ |
| DEVOPS | AWS Cost Explorer で月次コストレポートを自動生成 | ★★☆ |
| FRONT | React で Virtual DOM diff の可視化ツールを作る | ★★★ |
| FRONT | Lighthouse CI を GitHub Actions に組み込む | ★★☆ |
| FRONT | Next.js App Router で ISR ブログを実装 | ★★☆ |
| FRONT | Playwright で E2E テストを書いて CI に組み込む | ★★★ |
| CS | プロセススケジューラに MLFQ を追加実装 | ★★★ |
| CS | B+ Tree (リーフ連結リスト付き) を実装 | ★★★ |
| CS | epoll のイベントループを Python で実装 | ★★☆ |
| DIST | Raft に membership change を追加実装 | ★★★ |
| DIST | CRDT で共同編集テキスト (RGA) を実装 | ★★★ |
| DIST | Merkle Tree で2レプリカの差分同期を実装 | ★★☆ |
| PERF | cProfile + snakeviz で既存コードをプロファイリング | ★★☆ |
| PERF | Redis で Bloom Filter + Count-Min Sketch を実践 | ★★☆ |
| PERF | locust で負荷テストを実施し Tail Latency を計測 | ★★★ |
| STAFF+ | 自分のプロジェクトの Technical Vision を書く | ★★★ |
| STAFF+ | DORA メトリクスを計測して改善計画を立てる | ★★☆ |
| STAFF+ | RFC を1つ書いて技術提案する | ★★★ |

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
