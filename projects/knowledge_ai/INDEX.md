# KnowledgeAI - 全体目次 (Table of Contents)

**総ファイル数: 45ファイル / 約56,000行**
**対象: データサイエンティスト → テックリード/PM (Google/Tesla/IBM レベル)**

---

## 推奨学習ルート

```
Phase 1 (基礎固め)        Phase 2 (実装力)          Phase 3 (設計力)          Phase 4 (リーダー)
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ DS0 統計     │    │ Phase1 API   │    │ ARCH 設計    │    │ PM リーダー  │
│ ALGO アルゴ  │ →  │ Phase2 AI    │ →  │ DIST 分散    │ →  │ STAFF+ 戦略  │
│ CS 基盤     │    │ DS1-4 ML     │    │ PERF 性能    │    │ LANG 言語    │
│ PY+ Python  │    │ Phase7 データ │    │ SEC セキュリティ│   │ FRONT フロント│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 1. CS基礎・アルゴリズム (面接突破の土台)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 1 | [statistics_foundations.py](phase_ds0_stats/statistics_foundations.py) | 413 | ベイズの定理・仮説検定・A/Bテスト・信頼区間・因果推論 | Tier1 |
| 2 | [algo_foundations.py](phase_algo/algo_foundations.py) | 749 | Two Pointers・Sliding Window・Binary Search・Heap・Union-Find・DP | Tier1 |
| 3 | [advanced_algo.py](phase_algo/advanced_algo.py) | 905 | Graph(BFS/DFS/Dijkstra)・Trie・Segment Tree・Backtracking・KMP・Bitmask DP | Tier1 |
| 4 | [cs_internals.py](phase_cs_fundamentals/cs_internals.py) | 1,644 | OS(スケジューラ/仮想メモリ/Buddy)・TCP/IP・DB内部(B-Tree/LSM/MVCC)・GC | Tier1 |

| 5 | [networking_deep.py](phase_cs_fundamentals/networking_deep.py) | 1,351 | TCP Sliding Window・HTTP/2-3/QUIC・DNS解決・CDN・WebSocket・gRPC・LB・TLS 1.3 | Tier1 |
| 6 | [concurrency_deep.py](phase_cs_fundamentals/concurrency_deep.py) | 1,418 | メモリモデル・同期プリミティブ全種・Lock-Free・Actor/CSP・デッドロック検出・async vs thread | Tier2 |

**面接での重要度: ★★★★★**
```
Tier 1: Two Pointers, Binary Search, B-Tree, TCP/IP, 仮説検定, HTTP/2, DNS, LB
Tier 2: DP, Trie, MVCC, Producer-Consumer, Mutex/Semaphore, WebSocket, CDN
Tier 3: Segment Tree, LSM-Tree, Lock-Free, 輻輳制御(BBR), gRPC, Actor Model
Tier 4: Bitmask DP, Buddy System, Lexer/Parser, GC実装, Memory Barrier, TLS内部
```

---

## 2. 機械学習・データサイエンス (DS→ML Engineer)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 5 | [ml_from_scratch.py](phase_ds1_ml_foundation/ml_from_scratch.py) | 782 | 線形回帰・ロジスティック回帰・決定木・K-Means・PCA・Naive Bayes (NumPy実装) | Tier1 |
| 6 | [ml_pipeline.py](phase_ds1_ml_foundation/ml_pipeline.py) | 385 | scikit-learn パイプライン・分類/回帰/アンサンブル比較 | Tier1 |
| 7 | [neural_net.py](phase_ds2_deep_learning/neural_net.py) | 425 | PyTorch: SimpleNN・LSTM・Self-Attention 比較 | Tier2 |
| 8 | [transformer_from_scratch.py](phase_ds2_deep_learning/transformer_from_scratch.py) | 724 | NumPyのみでTransformer完全実装 (自動微分/Attention/Multi-Head) | Tier2 |
| 9 | [cv_from_scratch.py](phase_ds4_computer_vision/cv_from_scratch.py) | 656 | CNN・ResNet・ViT スクラッチ実装 + IoU/NMS (物体検出基礎) | Tier2 |
| 10 | [mlops_pipeline.py](phase_ds3_mlops/mlops_pipeline.py) | 503 | 実験管理・モデル本番化・ドリフト検知 (MLflow) | Tier3 |
| 11 | [ml_system_design.py](phase_system_design/ml_system_design.py) | 526 | 推薦システム・Feature Store・Model Serving・面接設計問題 | Tier1 |
| 12 | [llm_engineering.py](phase_ds2_deep_learning/llm_engineering.py) | 1,344 | BPEトークナイザ・Attention/KV-Cache・デコーディング戦略・LoRA/QLoRA・RLHF/DPO・量子化 | Tier1 |

**面接での重要度: ★★★★★**
```
Tier 1: 線形/ロジスティック回帰, 勾配降下法, 推薦システム設計, Attention/Transformer, BPE, LoRA
Tier 2: Transformer実装, CNN/ResNet, 交差検証, バイアス-バリアンス, KV-Cache, RLHF
Tier 3: MLOps, ドリフト検知, Feature Store, A/Bテスト設計, Speculative Decoding
Tier 4: ViT, GAN, 強化学習, 連合学習, INT4量子化
```

---

## 3. API・バックエンド (実装力の証明)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 12 | [api_design_patterns.py](phase1_api/api_design_patterns.py) | 977 | REST・ページネーション・レート制限・冪等性・CQRS・Circuit Breaker | Tier1 |
| 13 | [ai_agents_and_rag.py](phase2_ai/ai_agents_and_rag.py) | 1,407 | Advanced RAG・ReActエージェント・Multi-Agent・HNSW・BM25・LLMOps | Tier1 |

**面接での重要度: ★★★★☆**
```
Tier 1: REST基礎, ページネーション, プロンプトエンジニアリング, RAG
Tier 2: レート制限, 冪等性, ReActエージェント, Hybrid検索
Tier 3: CQRS, GraphQL, Multi-Agent, RAGAS評価
Tier 4: gRPC, HATEOAS, Fine-tuning, 100万ドキュメントRAG
```

---

## 4. インフラ・DevOps・SRE (本番運用力)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 14 | [container_deep_dive.py](phase3_docker/container_deep_dive.py) | 1,129 | namespaces/cgroups・イメージ最適化・K8sアーキテクチャ・HPA・GitOps | Tier1 |
| 15 | [cicd_patterns.py](phase4_cicd/cicd_patterns.py) | 1,173 | テスト戦略・5デプロイ戦略・Progressive Delivery・ML CI/CD | Tier2 |
| 16 | [cloud_architecture.py](phase5_cloud/cloud_architecture.py) | 1,400 | Well-Architected・マルチリージョン・サーバーレス・DR戦略 | Tier1 |
| 17 | [cloud_services_catalog.py](phase5_cloud/cloud_services_catalog.py) | 1,585 | AWS/GCP 100+サービスカタログ・7アーキテクチャパターン | Tier2 |
| 18 | [sre_practices.py](phase6_observability/sre_practices.py) | 1,398 | SLI/SLO/SLA・Error Budget・Burn Rate・カオスエンジニアリング | Tier2 |
| 19 | [devops_hands_on.py](phase_devops/devops_hands_on.py) | 1,930 | Docker実践・K8s Day-2・Terraform・CI/CD・FinOps・クラウドセキュリティ | Tier2 |
| 20 | [command_reference.py](phase_devops/command_reference.py) | 1,143 | UNIX/Docker/K8s/Git/AWS コマンド一覧 (Tier1-4付き) | Tier1 |
| 21 | [production_engineering.py](phase_devops/production_engineering.py) | 1,887 | OODAループ・USE/RED法・ポストモーテム・ランブック・キャパシティプランニング・SLA計算 | Tier1 |

**面接での重要度: ★★★★☆**
```
Tier 1: Dockerfile, docker compose, kubectl基本, Well-Architected, UNIXコマンド, ポストモーテム, OODAループ
Tier 2: マルチステージビルド, Canary Deploy, SLI/SLO, Terraform, USE/RED法, ランブック
Tier 3: K8sアーキテクチャ, カオスエンジニアリング, FinOps, キャパシティプランニング
Tier 4: CNI/CSI/CRI, Operator, GameDay, マルチアカウント戦略
```

---

## 5. データエンジニアリング (データ基盤)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 21 | [data_engineering.py](phase7_data/data_engineering.py) | 1,250 | Star Schema・DAGエグゼキュータ・データ品質・ストリーム処理・レイクハウス | Tier2 |
| 22 | [sql_nosql_deep_dive.py](phase7_data/sql_nosql_deep_dive.py) | 2,168 | Window関数・再帰CTE・DynamoDB設計・MongoDB・Redis・面接SQL | Tier1 |
| 23 | [database_internals.py](phase7_data/database_internals.py) | 1,898 | クエリプランナ・JOIN実装(NL/Hash/Sort-Merge)・B+Tree・WAL/ARIES・MVCC・LSM-Tree・ConnectionPool | Tier1 |

**面接での重要度: ★★★★☆**
```
Tier 1: Window Functions, JOIN, インデックス設計, 基本CTE, EXPLAIN読解, B+Tree, クエリプランナ
Tier 2: DynamoDB Single-Table, Redis Cache-Aside, Star Schema, WAL, JOIN実装比較
Tier 3: MongoDB Aggregation, レイクハウス, ストリーム処理, MVCC, LSM-Tree Compaction
Tier 4: Data Mesh, パーティショニング戦略, SCD Type 2, ARIES Recovery
```

---

## 6. アーキテクチャ・分散システム (設計面接の核心)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 23 | [system_design_patterns.py](phase_architecture/system_design_patterns.py) | 2,729 | マイクロサービス・DDD・Event Sourcing・面接設計問題(URL Shortener等) | Tier1 |
| 24 | [distributed_systems_deep.py](phase_architecture/distributed_systems_deep.py) | 1,041 | Raft合意・CRDT・2PC/Saga・Quorum・Consistent Hashing・HLC・Snowflake ID | Tier2 |
| 25 | [system_design_interview.py](phase_architecture/system_design_interview.py) | 1,365 | 5ステップ面接フレームワーク・スケール見積もり・10設計問題(URL短縮/Rate Limiter/Chat/News Feed等) | Tier1 |

**面接での重要度: ★★★★★**
```
Tier 1: URL Shortener/Rate Limiter設計, API Gateway, Consistent Hashing, 5ステップ面接法, スケール見積もり
Tier 2: Event Sourcing/CQRS, DDD, Raft合意, Saga, Chat/News Feed設計
Tier 3: CRDT, Gossip, Back-pressure, HLC, Web Crawler/Autocomplete設計
Tier 4: Cell-Based Architecture, Phi Accrual, Merkle Tree, Distributed Cache設計
```

---

## 7. プログラミング言語・設計 (コード品質)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 25 | [python_advanced.py](phase_programming/python_advanced.py) | 2,283 | async/await・メタクラス・型システム・テスト技法・Pythonic イディオム | Tier1 |
| 26 | [design_patterns.py](phase_programming/design_patterns.py) | 2,653 | GoF 23パターン・SOLID・並行処理パターン・Repository・DI | Tier1 |
| 27 | [performance_engineering.py](phase_programming/performance_engineering.py) | 894 | CPU cache・Bloom Filter・HyperLogLog・Tail Latency・ベンチマーク | Tier2 |
| 28 | [polyglot_guide.py](phase_programming/polyglot_guide.py) | 1,238 | 5言語比較(Python/TS/Go/Rust/Java)・言語選定フレームワーク | Tier2 |
| 29 | [testing_engineering.py](phase_programming/testing_engineering.py) | 1,296 | テストピラミッド・5種テストダブル・TDD・Property-Based Testing・Mutation Testing・Contract Testing | Tier1 |

**面接での重要度: ★★★★☆**
```
Tier 1: Strategy/Observer/Factory/DI, async/await, 型ヒント, pytest, テストピラミッド, TDD
Tier 2: Decorator/Builder/Command, contextmanager, Bloom Filter, テストダブル(Mock/Stub/Spy)
Tier 3: メタクラス, Chain of Responsibility, HyperLogLog, Property-Based Testing, Mutation Testing
Tier 4: Visitor/Interpreter, match-case, Fan-out amplification, Contract Testing
```

---

## 8. セキュリティ (OWASP + ゼロトラスト)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 29 | [security_deep_dive.py](phase9_security/security_deep_dive.py) | 1,384 | OWASP Top 10・JWT自作・STRIDE・OAuth2/PKCE・ゼロトラスト | Tier2 |

**面接での重要度: ★★★☆☆**
```
Tier 1: OWASP Top 10, JWT/OAuth2, HTTPS/TLS
Tier 2: STRIDE, RBAC/ABAC, シークレット管理
Tier 3: mTLS, ゼロトラスト, PKCE
Tier 4: HSM, FIDO2/WebAuthn, SOC2
```

---

## 9. フロントエンド (フルスタック力)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 30 | [frontend_engineering.py](phase10_frontend/frontend_engineering.py) | 2,079 | Virtual DOM diff・Next.js SSR/SSG/ISR・Core Web Vitals・CSS・状態管理 | Tier3 |

**面接での重要度: ★★☆☆☆ (バックエンド志向の場合)**
```
Tier 1: React基礎, TypeScript型, Flexbox/Grid
Tier 2: Next.js (SSR/SSG), Redux/Zustand, コンポーネント設計
Tier 3: Core Web Vitals, Virtual DOM, アクセシビリティ
Tier 4: Micro Frontends, Web Workers, Service Worker
```

---

## 10. Go並行処理 (クラウドネイティブ)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 31 | [go_concurrency_patterns.go](phase8_go_service/go_concurrency_patterns.go) | 975 | goroutine/channel・Fan-out/Fan-in・select・Circuit Breaker・Graceful Shutdown | Tier3 |

---

## 11. PM・リーダーシップ (Senior → Staff+)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 32 | [tech_pm_leadership.py](phase_pm/tech_pm_leadership.py) | 1,460 | アジャイル・RICE・OKR・STAR面接・ステークホルダー管理・プロダクト戦略 | Tier2 |
| 33 | [staff_plus_leadership.py](phase_pm/staff_plus_leadership.py) | 1,293 | Technology Radar・Build vs Buy・DORA/SPACE・Team Topologies・Staff+面接 | Tier3 |

**面接での重要度: ★★★★☆**
```
Tier 1: アジャイル/スクラム, STAR, OKR, ステークホルダー管理
Tier 2: RICE, ADR, Burndown, Product Sense面接
Tier 3: Technology Radar, DORA, Team Topologies, Build vs Buy
Tier 4: PMF判定, Engineering Levels設計, OKRカスケード
```

---

## 12. 言語別ミニアプリ (ポリグロット実践)

| # | ファイル | 行数 | 言語 | 内容 |
|---|---------|------|------|------|
| 34 | [main.ts](lang_typescript/src/main.ts) | 579 | TypeScript | Branded Types・Discriminated Unions・Generics・satisfies |
| 35 | [main.go](lang_go/main.go) | 604 | Go | goroutine・channel・context・interfaces・error handling |
| 36 | [main.rs](lang_rust/src/main.rs) | 653 | Rust | 所有権・借用・traits・Result/Option・iterators |
| 37 | [Main.java](lang_java/src/main/java/kvstore/Main.java) | 413 | Java 17+ | Records・Sealed Interfaces・Stream API・CompletableFuture |
| 38 | [Main.java (Maven)](lang_java_maven/src/main/java/demo/Main.java) | 609 | Java+Maven | Maven(pom.xml)・Repository パターン・Gson・JUnit 5・DI |

**起動方法:**
```bash
cd lang_typescript && npm install && npx tsx src/main.ts
cd lang_go && go run main.go
cd lang_rust && cargo run
cd lang_java && javac -d out src/main/java/kvstore/Main.java && java -cp out kvstore.Main
cd lang_java_maven && mvn package -q && java -jar target/maven-demo-1.0.0.jar
```

---

## 13. リファレンス

| # | ファイル | 行数 | 内容 |
|---|---------|------|------|
| - | [glossary.py](glossary.py) | 774 | 50+専門用語・カテゴリ別・検索機能付き |
| - | [LEARNING_GUIDE.md](LEARNING_GUIDE.md) | 608 | 各フェーズの詳細説明・実装タスク一覧・面接対応表 |

---

## 全体の優先度マップ

```
【最優先 — 今すぐやる】
  algo_foundations.py → cs_internals.py → ml_from_scratch.py → sql_nosql_deep_dive.py
  → system_design_patterns.py → system_design_interview.py → api_design_patterns.py
  → command_reference.py → testing_engineering.py → database_internals.py

【重要 — 1〜2ヶ月で】
  advanced_algo.py → python_advanced.py → design_patterns.py → cloud_architecture.py
  → container_deep_dive.py → ai_agents_and_rag.py → transformer_from_scratch.py
  → llm_engineering.py → networking_deep.py → production_engineering.py

【上級 — 3〜6ヶ月で】
  distributed_systems_deep.py → concurrency_deep.py → performance_engineering.py
  → security_deep_dive.py → sre_practices.py → devops_hands_on.py
  → data_engineering.py → tech_pm_leadership.py

【専門 — 必要に応じて】
  staff_plus_leadership.py → frontend_engineering.py → polyglot_guide.py
  → cloud_services_catalog.py → mlops_pipeline.py → 言語別ミニアプリ
```

---

## 面接カテゴリ別 クイックリファレンス

| 面接で聞かれたら | 開くファイル |
|----------------|------------|
| 「LeetCode を解け」 | [algo_foundations.py](phase_algo/algo_foundations.py), [advanced_algo.py](phase_algo/advanced_algo.py) |
| 「URL Shortener を設計せよ」 | [system_design_patterns.py](phase_architecture/system_design_patterns.py) |
| 「推薦システムを設計せよ」 | [ml_system_design.py](phase_system_design/ml_system_design.py) |
| 「Raft を説明せよ」 | [distributed_systems_deep.py](phase_architecture/distributed_systems_deep.py) |
| 「B-Tree vs LSM-Tree」 | [cs_internals.py](phase_cs_fundamentals/cs_internals.py) |
| 「OWASP Top 10 は？」 | [security_deep_dive.py](phase9_security/security_deep_dive.py) |
| 「SLO を設計せよ」 | [sre_practices.py](phase6_observability/sre_practices.py) |
| 「Tail Latency の原因は？」 | [performance_engineering.py](phase_programming/performance_engineering.py) |
| 「なぜその言語を選んだ？」 | [polyglot_guide.py](phase_programming/polyglot_guide.py) |
| 「STARで答えよ」 | [tech_pm_leadership.py](phase_pm/tech_pm_leadership.py) |
| 「Staff+ でどう影響を与えた？」 | [staff_plus_leadership.py](phase_pm/staff_plus_leadership.py) |
| 「Docker/K8s で障害対応」 | [command_reference.py](phase_devops/command_reference.py) |
| 「本番障害の対応手順は？」 | [production_engineering.py](phase_devops/production_engineering.py) |
| 「テスト戦略を説明せよ」 | [testing_engineering.py](phase_programming/testing_engineering.py) |
| 「EXPLAIN の読み方は？」 | [database_internals.py](phase7_data/database_internals.py) |
| 「LLMの仕組みを説明せよ」 | [llm_engineering.py](phase_ds2_deep_learning/llm_engineering.py) |
| 「Chat システムを設計せよ」 | [system_design_interview.py](phase_architecture/system_design_interview.py) |
| 「TCP の仕組みを説明せよ」 | [networking_deep.py](phase_cs_fundamentals/networking_deep.py) |
| 「デッドロックの検出方法は？」 | [concurrency_deep.py](phase_cs_fundamentals/concurrency_deep.py) |
| 「RAG を設計せよ」 | [ai_agents_and_rag.py](phase2_ai/ai_agents_and_rag.py) |
| 「Window Function で解け」 | [sql_nosql_deep_dive.py](phase7_data/sql_nosql_deep_dive.py) |
| 「デザインパターンを適用せよ」 | [design_patterns.py](phase_programming/design_patterns.py) |
| 「Well-Architected の柱は？」 | [cloud_architecture.py](phase5_cloud/cloud_architecture.py) |
