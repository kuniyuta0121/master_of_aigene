# KnowledgeAI - 全体目次 (Table of Contents)

**総ファイル数: 67ファイル / 約91,500行**
**対象: データサイエンティスト → テックリード/PM (Google/Tesla/IBM レベル)**

---

## 統合ストーリー (まずここから)

| ファイル | 行数 | 内容 |
|---------|------|------|
| [unified_system_story.py](unified_system_story.py) | 3,612 | 「TechPulse」構築物語 - 全知識を1つのシステムで串刺し (13 Chapter) |

> 全体像を掴みたいなら、まずこのファイルを読んでから各詳細ファイルに進むのがおすすめ。

## 深掘り解説シリーズ (用語定義・なぜ・アナロジー・面接対策)

| ファイル | 行数 | 内容 |
|---------|------|------|
| [unified_system_story_explained.py](unified_system_story_explained.py) | 2,727 | TechPulse全13章の深掘り解説 |
| [compiler_runtime_explained.py](compiler_runtime_explained.py) | 1,244 | Lexer/Parser/AST・型推論・IR最適化・GC全種・JIT・バイトコード |
| [concurrency_explained.py](concurrency_explained.py) | 955 | メモリモデル・同期プリミティブ・Lock-Free・デッドロック・async/await・Go/Actor・分散並行 |
| [data_engineering_explained.py](data_engineering_explained.py) | 1,015 | 正規化・SQL深掘り・NoSQL・DB内部・Airflow/dbt・Kafka/Flink・レイクハウス |
| [data_science_explained.py](data_science_explained.py) | 1,435 | 統計・ML/DL基礎・Transformer・LLM・RAG・エージェント・MLOps・評価・ガードレール |
| [programming_practices_explained.py](programming_practices_explained.py) | 2,513 | テスト戦略・パフォーマンス・Python高度・GoF全23パターン・SOLID・Go/TS比較 |
| [frontend_explained.py](frontend_explained.py) | 1,673 | ブラウザレンダリング・V8・React/Next.js・状態管理・TypeScript・Web API・ビルドツール |
| [leadership_explained.py](leadership_explained.py) | 1,280 | Staff+・チームトポロジー・SPACE・アジャイル・PM・組織設計・ADR・ビジネス思考 |
| [security_explained.py](security_explained.py) | 938 | 暗号学・PKI/TLS・OWASP・OAuth/JWT・ゼロトラスト・クラウド/コンテナセキュリティ |
| [system_design_explained.py](system_design_explained.py) | 1,213 | 面接フレームワーク・設計問題9選・概算・DB選定・マイクロサービス |
| [qa_engineering_explained.py](qa_engineering_explained.py) | 989 | ISO 25010・IEEE 829・テスト設計技法・テスト自動化・性能テスト・品質メトリクス・CMMI・JSTQB |
| [pmo_portfolio_explained.py](pmo_portfolio_explained.py) | 1,047 | PMO 3類型・PMBOK 7th・CPM/PERT/CCPM・EVM・リスク管理・ポートフォリオ・ガバナンス・RFP/契約 |
| [itil_itsm_explained.py](itil_itsm_explained.py) | 934 | ITIL 4・インシデント/問題/変更管理・サービスデスク・CMDB・社内SE実務・ITSM+DevOps融合 |
| [network_engineering_explained.py](network_engineering_explained.py) | 945 | OSI L1-L3・IPアドレス/サブネット・VLAN/STP・OSPF/BGP・Firewall/ACL・VPN/SD-WAN・無線LAN・監視 |

> 各ファイルは全用語を初出で定義し、「なぜ」を必ず説明。⚠誤解と【面接向けまとめ】付き。

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
| 7 | [os_hardware_deep.py](phase_cs_fundamentals/os_hardware_deep.py) | 1,670 | CPUパイプライン・MESI・仮想記憶ページテーブル・CFS・epoll/Reactor・NUMA・DMA | Tier1 |
| 8 | [storage_engine_internals.py](phase_cs_fundamentals/storage_engine_internals.py) | 2,547 | SSD/FTL・ファイルシステムinode・バッファプール・B+Tree on disk・LSM Compaction・RAID | Tier1 |
| 9 | [compiler_runtime.py](phase_cs_fundamentals/compiler_runtime.py) | 2,310 | Lexer/Parser/AST・型推論(HM)・SSA最適化・レジスタ割当・GC全種(Mark-Sweep〜ZGC)・JIT | Tier2 |

**面接での重要度: ★★★★★**
```
Tier 1: Two Pointers, Binary Search, B-Tree, TCP/IP, 仮説検定, CPUパイプライン, キャッシュMESI, 仮想記憶, SSD/WAF
Tier 2: DP, Trie, MVCC, epoll/Reactor, CFS, バッファプール, B+Tree on disk, GC(世代別)
Tier 3: Segment Tree, LSM-Tree, Lock-Free, RAID, Lexer/Parser, 型推論, レジスタ割当
Tier 4: Bitmask DP, NUMA, DMA, JIT/OSR, ZGC, FTL内部, コンパイラ最適化
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
| 13b | [llm_eval_and_guardrails.py](phase2_ai/llm_eval_and_guardrails.py) | 2,181 | RAGAS全メトリクス・DeepEval・Agent評価6軸・NeMo Guardrails・Presidio PII・Prompt Injection多層防御 | Tier1 |

**面接での重要度: ★★★★☆**
```
Tier 1: REST基礎, ページネーション, プロンプトエンジニアリング, RAG, RAGAS評価, ガードレール設計
Tier 2: レート制限, 冪等性, ReActエージェント, Hybrid検索, PII マスキング, Prompt Injection対策
Tier 3: CQRS, GraphQL, Multi-Agent, DeepEval, LLM-as-Judge バイアス
Tier 4: gRPC, HATEOAS, Fine-tuning, 100万ドキュメントRAG, Agent評価ベンチマーク
```

---

## 4. インフラ・DevOps・SRE (本番運用力)

| # | ファイル | 行数 | 内容 | 優先度 |
|---|---------|------|------|--------|
| 14 | [container_deep_dive.py](phase3_docker/container_deep_dive.py) | 1,129 | namespaces/cgroups・イメージ最適化・K8sアーキテクチャ・HPA・GitOps | Tier1 |
| 15 | [cicd_patterns.py](phase4_cicd/cicd_patterns.py) | 1,173 | テスト戦略・5デプロイ戦略・Progressive Delivery・ML CI/CD | Tier2 |
| 16 | [cloud_architecture.py](phase5_cloud/cloud_architecture.py) | 1,400 | Well-Architected・マルチリージョン・サーバーレス・DR戦略 | Tier1 |
| 17 | [cloud_services_catalog.py](phase5_cloud/cloud_services_catalog.py) | 1,585 | AWS/GCP 100+サービスカタログ・7アーキテクチャパターン | Tier2 |
| 17b | [azure_services_catalog.py](phase5_cloud/azure_services_catalog.py) | 1,492 | Azure 全サービスカタログ・Cosmos DB整合性・3クラウド比較・認定ロードマップ | Tier2 |
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
| 26 | [reliability_math.py](phase_architecture/reliability_math.py) | 2,403 | M/M/1待ち行列・Little's Law・テールレイテンシ数学・Amdahl/USL・可用性マルコフ連鎖・負荷試験統計 | Tier1 |
| 27 | [distributed_systems_theory.py](phase_architecture/distributed_systems_theory.py) | 1,727 | FLP不可能性・Paxos・線形化可能性・ビザンチンBFT・レプリケーション理論・TLA+概念 | Tier2 |

**面接での重要度: ★★★★★**
```
Tier 1: URL Shortener/Rate Limiter設計, Consistent Hashing, Little's Law, M/M/1, Amdahl's Law, 可用性計算
Tier 2: Event Sourcing/CQRS, DDD, Raft/Paxos, Saga, テールレイテンシ, USL, 線形化可能性
Tier 3: CRDT, Gossip, HLC, FLP不可能性, ビザンチンBFT, 負荷試験統計
Tier 4: Cell-Based Architecture, Phi Accrual, Merkle Tree, TLA+, 形式検証
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
| 30 | [cryptography_fundamentals.py](phase9_security/cryptography_fundamentals.py) | 1,514 | RSA数学証明・AES/Feistel・SHA-256・ECDSA・DH鍵交換・TLS 1.3・PKI | Tier2 |

**面接での重要度: ★★★☆☆**
```
Tier 1: OWASP Top 10, JWT/OAuth2, HTTPS/TLS, RSA/AES概念
Tier 2: STRIDE, RBAC/ABAC, シークレット管理, DH鍵交換, ECDSA, ハッシュ関数
Tier 3: mTLS, ゼロトラスト, PKCE, PKI/証明書チェーン, TLS 1.3内部
Tier 4: HSM, FIDO2/WebAuthn, SOC2, 楕円曲線数学, ゼロ知識証明
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
  algo_foundations.py → cs_internals.py → os_hardware_deep.py → ml_from_scratch.py
  → sql_nosql_deep_dive.py → system_design_patterns.py → system_design_interview.py
  → reliability_math.py → api_design_patterns.py → testing_engineering.py

【重要 — 1〜2ヶ月で】
  advanced_algo.py → storage_engine_internals.py → python_advanced.py → design_patterns.py
  → cloud_architecture.py → container_deep_dive.py → database_internals.py
  → llm_engineering.py → networking_deep.py → production_engineering.py → command_reference.py

【上級 — 3〜6ヶ月で】
  distributed_systems_theory.py → distributed_systems_deep.py → concurrency_deep.py
  → compiler_runtime.py → cryptography_fundamentals.py → performance_engineering.py
  → security_deep_dive.py → sre_practices.py → ai_agents_and_rag.py
  → data_engineering.py → tech_pm_leadership.py

【専門 — 必要に応じて】
  staff_plus_leadership.py → frontend_engineering.py → polyglot_guide.py
  → cloud_services_catalog.py → mlops_pipeline.py → 言語別ミニアプリ
```

---

## 推薦図書 (カテゴリ別・厳選)

> 各カテゴリ1〜3冊に厳選。日本語書籍を優先し、定番の洋書は邦訳があれば邦題も併記。

### CS基礎・OS・ネットワーク

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『プログラムはなぜ動くのか 第3版』 | 矢沢久雄 | CPU・メモリ・OS の仕組みを図解。CS基礎の入門に最適 |
| 『ネットワークはなぜつながるのか 第2版』 | 戸根 勤 | URL入力→サーバ到達の全過程を1冊で。物理層〜アプリ層 |
| 『マスタリングTCP/IP 入門編 第6版』 | 竹下・村山・荒井・苅田 | ネットワーク定番教科書。OSI〜TCP/IPを網羅 |
| 『コンピュータの構成と設計 (パタヘネ) 第6版』 | Patterson, Hennessy | CPUパイプライン・キャッシュ・仮想記憶の教科書 |

### アルゴリズム・データ構造

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『問題解決力を鍛える! アルゴリズムとデータ構造』 | 大槻 兼資 | 競プロ由来の実践的アルゴ本。Python/C++例付き |
| 『プログラミングコンテストチャレンジブック 第2版』 | 秋葉・岩田・北川 | 通称「蟻本」。DP・グラフ・数学を深掘り |

### データベース・データエンジニアリング

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『データ指向アプリケーションデザイン (DDIA)』 | Martin Kleppmann | DB・分散・ストリーム処理の理論と実践。全エンジニア必読 |
| 『達人に学ぶDB設計 徹底指南書 第2版』 | ミック | 正規化・インデックス・パフォーマンスを日本語で体系解説 |
| 『SQL実践入門 — パフォーマンスを最適化する思考法』 | ミック | EXPLAIN・実行計画・Window関数を実例で学ぶ |
| 『Fundamentals of Data Engineering』 | Joe Reis, Matt Housley | データエンジニアリングのライフサイクル全体を俯瞰。ETL/dbt/レイクハウス |
| 『Streaming Systems』 | Tyler Akidau 他 | Watermark・Window・Trigger の決定版。Kafka/Flink理論背景 |

### ストレージエンジン・DB内部

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『Database Internals』 | Alex Petrov | B-Tree/LSM-Tree・レプリケーション・分散ストレージの内部構造 |
| 『詳解 システム・パフォーマンス 第2版』 | Brendan Gregg | ファイルシステム・ディスクI/O・SSD特性・RAID・カーネルI/Oスタック |

### システム設計・分散システム

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『System Design Interview Vol.1 & Vol.2』 | Alex Xu | 設計面接の定番。URL短縮〜決済システムまで20+問題 |
| 『Building Microservices 第2版』邦訳:『マイクロサービスアーキテクチャ 第2版』 | Sam Newman | Saga・Circuit Breaker・Service Mesh の実践 |

### API・バックエンド設計

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『Web API: The Good Parts』 | 水野 貴明 | REST API設計の日本語決定版。URI/ページネーション/バージョニング/エラー設計 |
| 『マイクロサービスパターン』 | Chris Richardson | CQRS・Event Sourcing・Saga・Circuit Breaker を実装パターンで解説 |

### AI・機械学習・LLM

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『ゼロから作る Deep Learning』シリーズ (全5巻) | 斎藤 康毅 | NumPyでCNN〜Transformer実装。DL理解の最短ルート |
| 『Hands-On Machine Learning 第3版』邦訳:『scikit-learn、Keras、TensorFlowによる実践機械学習 第3版』 | Aurélien Géron | ML/DL全般を実践的に。scikit-learn+TF/Keras |
| 『Build a Large Language Model (From Scratch)』 | Sebastian Raschka | GPTをPyTorchでゼロ実装。LLM内部理解に最適 (2024刊) |
| 『パターン認識と機械学習 (PRML)』 | C.M. Bishop | ML理論の決定版。数学寄りだが深い理解には不可欠 |

### セキュリティ・暗号

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『暗号技術入門 第3版 — 秘密の国のアリス』 | 結城 浩 | AES/RSA/TLS を物語形式で解説。数学苦手でもOK |
| 『体系的に学ぶ 安全なWebアプリケーションの作り方 第2版』 | 徳丸 浩 | 通称「徳丸本」。OWASP Top 10 を手を動かして理解 |
| 『Zero Trust Networks 2nd Ed.』 | Gilman, Barth | ゼロトラスト理論と実装。BeyondCorp・mTLS・SPIFFE |

### インフラ・DevOps・SRE・クラウド

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『Docker/Kubernetes 実践コンテナ開発入門 改訂新版』 | 山田明憲 | Docker〜K8sを日本語で段階的に。ハンズオン豊富 |
| 『Googleのソフトウェアエンジニアリング』 | Titus Winters 他 | テスト/CI-CD/レビュー/技術的負債。大規模開発の知見 |
| 『SRE サイトリライアビリティエンジニアリング』 | Google SRE チーム | SLI/SLO/Error Budget/ポストモーテムの原典 |

### プログラミング実践・設計

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『リファクタリング 第2版』 | Martin Fowler | コード改善の決定版。JS例で読みやすい |
| 『テスト駆動開発』 | Kent Beck | TDDの原典。薄く1日で読める |
| 『Head First デザインパターン 第2版』 | Freeman, Robson | GoF 23パターンをストーリー形式で解説 |
| 『Fluent Python 第2版』邦訳あり | Luciano Ramalho | Python上級者向け。メタクラス・async・型ヒント |

### フロントエンド

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『プロを目指す人のための TypeScript 入門』 | 鈴木 僚太 | TS型システムを体系解説。日本語TS本の決定版 |
| 『Learning React 2nd Ed.』 | Banks, Porcello | React Hooks/Context/Suspense を基礎から。入門に最適 |
| 『Web Performance in Action』 | Jeremy Wagner | Core Web Vitals・Code Splitting・画像最適化をハンズオン |
| 『ハイパフォーマンス ブラウザ ネットワーキング』 | Ilya Grigorik | ブラウザ通信層を深掘り。無料Web版あり |

### PM・リーダーシップ

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『INSPIRED 熱狂させる製品を生み出すプロダクトマネジメント』 | Marty Cagan | PM必読。プロダクトディスカバリー・ロードマップ |
| 『Staff Engineer』 | Will Larson | Staff+の4アーキタイプ・Technical Vision・影響力行使 |
| 『チームトポロジー』 | Skelton, Pais | 4チーム型・認知負荷ベースの組織設計 |
| 『アジャイルサムライ』 | Jonathan Rasmusson | アジャイル/スクラムの入門書。日本語で読みやすい |

### コンパイラ・並行処理 (上級)

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『Crafting Interpreters』 | Robert Nystrom | Lexer→VM→GCをハンズオン実装。無料Web版あり |
| 『Engineering a Compiler 3rd Ed.』 | Cooper, Torczon | 大学コンパイラ講義の教科書。SSA・レジスタ割当 |
| 『The Garbage Collection Handbook 2nd Ed.』 | Jones, Hosking, Moss | GCアルゴリズム決定版。Mark-Sweep〜ZGCまで |
| 『Go言語による並行処理』 | Katherine Cox-Buday | goroutine/channel/contextを体系的に。邦訳あり |
| 『Java Concurrency in Practice』 | Brian Goetz 他 | 並行プログラミングの本質。Java以外にも応用可 |
| 『Is Parallel Programming Hard, And, If So, What Can You Do About It?』 | Paul McKenney | Linuxカーネル開発者の実践書。**無料PDF公開** |

### QA・品質保証

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『ソフトウェアテストの教科書』 | 石原一宏・田中英和 | テスト設計技法の入門書。JSTQB対策にも |
| 『Lessons Learned in Software Testing』 | Kaner, Bach, Pettichord | 293のテスト教訓集。実践的洞察が満載。中級以上 |
| 『Agile Testing』 | Lisa Crispin, Janet Gregory | アジャイルチームのQA実践ガイド。四象限モデル |

### PMO・プロジェクトマネジメント

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『プロジェクトマネジメントの基本』 | 好川 哲人 | PMBOKを日本の文脈で噛み砕いた入門書 |
| 『PMBOK ガイド 第7版』 | PMI | PM の聖典。12原則ベースに転換 |
| 『The Standard for Portfolio Management 4th Ed.』 | PMI | ポートフォリオ管理の国際標準。戦略整合・投資最適化 |

### ITIL・ITSM

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『ITIL 4 ファンデーション』公式テキスト | Axelos | ITIL資格入門。SVS・SVC・34プラクティスを体系学習 |
| 『The Phoenix Project』 | Gene Kim 他 | DevOps小説。ITIL→DevOps変革を物語で理解 |
| 『情報処理教科書 ITサービスマネージャ』 | 翔泳社 | ITIL+日本の情シス実務をカバー |

### クラウドサービス

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『AWS認定ソリューションアーキテクト[アソシエイト]教科書』 | NRIネットコム | AWS主要サービスを体系的に。認定対策にも最適 |
| 『Google Cloudではじめる実践データエンジニアリング入門』 | 下田倫大 他 | GCPサービスをデータ基盤構築で実践的に学ぶ |
| 『Azure定番システム設計・実装・運用ガイド 改訂新版』 | 日本マイクロソフト | Azureの主要サービスを設計パターンで解説 |

### ネットワーク実務

| 書籍 | 著者 | ひとこと |
|------|------|---------|
| 『CCNA完全合格テキスト&問題集』 | — | Cisco資格定番。資格を取らなくてもリファレンスとして有用 |

---

## 読書ロードマップ（並行2〜3冊 × 6フェーズで全網羅）

> 異なる分野を並行して読み、飽きずに幅広くカバーする戦略。
> ★ = 通読必須　☆ = 辞書引き/必要章のみ

### Phase 1: 土台固め（CS + DB + アルゴ）── 目安 2〜3ヶ月

| Track A (CS基礎) | Track B (DB) | Track C (アルゴ) |
|-------------------|--------------|-------------------|
| ★ プログラムはなぜ動くのか 第3版 | ★ 達人に学ぶDB設計 第2版 | ★ 問題解決力を鍛える! アルゴリズムとデータ構造 |
| ★ ネットワークはなぜつながるのか 第2版 | ★ SQL実践入門 | |

- カバー: Cat 1 (アルゴ), 2 (OS), 3 (NW), 7 (DB基礎)
- 並行サイト: AtCoder ABC + SQLZOO

### Phase 2: 設計力 + AI深化（設計 + ML + セキュリティ）── 2〜3ヶ月

| Track A (システム設計) | Track B (AI/ML) | Track C (セキュリティ) |
|------------------------|-----------------|------------------------|
| ★ System Design Interview Vol.1 | ★ ゼロから作るDL 1巻→2巻 | ★ 暗号技術入門 第3版 (結城浩) |
| ☆ SDI Vol.2 (興味ある問題だけ) | ★ Build a LLM From Scratch | ★ 徳丸本 |

- カバー: Cat 9 (AI/ML), 10 (設計面接), 12 (セキュリティ)
- 並行サイト: NeetCode 150 + LeetCode

### Phase 3: 実装力 + インフラ（コード品質 + DevOps + API）── 2〜3ヶ月

| Track A (プログラミング) | Track B (インフラ) | Track C (API/バックエンド) |
|--------------------------|---------------------|----------------------------|
| ★ テスト駆動開発 (Kent Beck) | ★ Docker/K8s 実践コンテナ開発入門 | ★ Web API: The Good Parts |
| ★ Head First デザインパターン | ☆ SRE サイトリライアビリティエンジニアリング | ★ DDIA (データ指向アプリケーションデザイン) |

- カバー: Cat 4 (ストレージ), 7 (DB深化), 8 (API), 11 (インフラ), 13 (プログラミング)
- 並行サイト: AWS Skill Builder + Play with Docker
- **DDIA は全書籍中で最重要。Phase 1 の DB知識の上に積むためこの位置がベスト**

### Phase 4: 上級 + PM（分散 + リーダーシップ + フロントエンド）── 2〜3ヶ月

| Track A (分散/アーキ) | Track B (PM/リーダー) | Track C (フロントエンド) |
|-----------------------|-----------------------|--------------------------|
| ★ Building Microservices 第2版 | ★ INSPIRED (Cagan) | ★ プロを目指す人のための TS入門 |
| ★ マイクロサービスパターン | ★ アジャイルサムライ | ☆ Learning React 2nd Ed. |

- カバー: Cat 8 (CQRS/Saga), 10 (マイクロサービス), 14 (フロントエンド), 15 (PM)
- 並行サイト: React公式(ja) + Scrum Guide

### Phase 5: 専門深化（クラウド + QA/PMO + ネットワーク）── 2〜3ヶ月

| Track A (クラウド) | Track B (QA/PMO/ITIL) | Track C (ネットワーク) |
|--------------------|------------------------|-----------------------|
| ★ AWS認定SAA教科書 | ★ ソフトウェアテストの教科書 | ★ マスタリングTCP/IP 入門編 第6版 |
| ☆ GCP or Azure本 (必要な方) | ★ PMの基本 (好川) | |
| | ☆ Phoenix Project | |

- カバー: Cat 16 (クラウド), 17 (QA), 18 (PMO), 19 (ITIL), 20 (NW実務)
- 並行サイト: AWS Skill Builder + IPA過去問 + 3分間ネットワーキング

### Phase 6: 仕上げ — キャリア方向に応じて選択

| 方向性 | 書籍 | カテゴリ |
|--------|------|----------|
| Python上級者 | ★ Fluent Python 第2版 | Cat 13 |
| ML理論深化 | ☆ PRML / Hands-On ML | Cat 9 |
| Staff+目指す | ★ Staff Engineer + チームトポロジー | Cat 15 |
| コンパイラ興味 | ★ Crafting Interpreters (無料Web版) | Cat 5 |
| 並行処理を極める | ★ Go言語による並行処理 or JCiP | Cat 6 |
| ストレージ内部 | ★ Database Internals | Cat 4 |
| データ基盤構築 | ★ Fundamentals of Data Engineering | Cat 7 |
| Web性能 | ☆ Web Performance in Action | Cat 14 |
| PM認定 | ☆ PMBOK 第7版 | Cat 18 |

### フェーズ別サマリ

```
Phase  期間目安     冊数   カバーカテゴリ
─────  ──────────  ─────  ────────────────────────────────────
  1    2〜3ヶ月    5冊    Cat 1, 2, 3, 7(基礎)
  2    2〜3ヶ月    5冊    Cat 9, 10, 12
  3    2〜3ヶ月    6冊    Cat 4, 7(深化), 8, 11, 13
  4    2〜3ヶ月    5冊    Cat 8(残), 10(残), 14, 15
  5    2〜3ヶ月    5冊    Cat 16, 17, 18, 19, 20
  6    随時        選択    Cat 5, 6 + 各カテゴリ深化
─────  ──────────  ─────  ────────────────────────────────────
合計   10〜15ヶ月  26冊(必須) + 選択で全20カテゴリ網羅
```

---

## 無料学習サイト・リソース

> 書籍と併用すると効果的。日本語リソースを優先。

### アルゴリズム・コーディング
| サイト | 言語 | 内容 |
|--------|------|------|
| AtCoder (atcoder.jp) | 日本語 | 競プロ。ABC(初級)→ARC(中級)→AGC(上級) |
| AtCoder Problems (kenkoooo.com) | 日本語 | AtCoder過去問の難易度別一覧・進捗管理 |
| LeetCode (leetcode.com) | 英語 | FAANG面接対策の定番。NeetCode 150 から |
| NeetCode (neetcode.io) | 英語 | LeetCode厳選150問+動画解説。ロードマップ付き |
| アルゴ式 (algo-method.com) | 日本語 | アルゴリズムを段階的に学べる日本語サイト |
| AOJ (judge.u-aizu.ac.jp) | 日本語 | 会津大のオンラインジャッジ。教育向け問題が豊富 |

### CS基礎・OS・コンピュータサイエンス
| サイト | 言語 | 内容 |
|--------|------|------|
| CS50 (cs50.harvard.edu) | 英語(字幕あり) | ハーバードCS入門。C→Python→Web。無料 |
| MIT OCW 6.824 Distributed Systems | 英語 | MIT分散システム講義。Raft実装の演習付き |
| teachyourselfcs.com | 英語 | CS独学カリキュラム。9科目の推薦教材一覧 |
| Nand2Tetris (nand2tetris.org) | 英語 | NANDゲートからOS・コンパイラまで自作 |
| Crafting Interpreters (craftinginterpreters.com) | 英語 | コンパイラ実装を無料で段階学習。書籍版と同一 |

### AI・機械学習・LLM
| サイト | 言語 | 内容 |
|--------|------|------|
| 東大 松尾研 Deep Learning基礎講座 | 日本語 | 東大の無料DL講座。スライド+演習 |
| Coursera: Machine Learning (Andrew Ng) | 英語(字幕あり) | ML入門の金字塔。リニューアル版はPython |
| fast.ai (course.fast.ai) | 英語 | 実践ファーストのDL講座。PyTorch/fastai |
| Hugging Face NLP Course | 英語 | Transformers/RAG/ファインチューニング実践 |
| Google Machine Learning Crash Course | 英語(日本語版あり) | TensorFlow ベースのML速習。演習付き |
| Kaggle Learn (kaggle.com/learn) | 英語 | Python/ML/SQL/DLの短期コース。ブラウザ完結 |
| LLM University by Cohere (docs.cohere.com/docs/llmu) | 英語 | LLM/RAG/Embeddingを体系的に学ぶ無料コース |

### データベース・SQL
| サイト | 言語 | 内容 |
|--------|------|------|
| SQLZOO (sqlzoo.net) | 英語 | SQL練習問題。ブラウザで即実行 |
| Mode SQL Tutorial (mode.com/sql-tutorial) | 英語 | 分析SQL(Window関数含む)を段階学習 |
| PostgreSQL公式チュートリアル (postgresql.org/docs) | 英語 | 公式ドキュメント。実行計画の読み方も |
| DBやろうぜ (qiita.com/mochizuki875) | 日本語 | DB内部構造・インデックス設計のQiita連載 |

### インフラ・DevOps・クラウド
| サイト | 言語 | 内容 |
|--------|------|------|
| AWS Skill Builder (explore.skillbuilder.aws) | 日本語あり | AWS公式の無料学習。SAA対策含む |
| Google Cloud Skills Boost (cloudskillsboost.google) | 日本語あり | GCP公式ハンズオンラボ。Qwiklabs |
| Microsoft Learn (learn.microsoft.com) | 日本語 | Azure全サービスの学習パス。認定対策にも |
| KodeKloud (kodekloud.com) | 英語 | Docker/K8s/Terraformのハンズオン。一部無料 |
| Play with Docker (labs.play-with-docker.com) | 英語 | ブラウザでDockerを試せる無料環境 |
| Kubernetes公式チュートリアル (kubernetes.io/ja/docs) | 日本語 | K8s公式の日本語ドキュメント |

### セキュリティ
| サイト | 言語 | 内容 |
|--------|------|------|
| IPA 安全なウェブサイトの作り方 (ipa.go.jp) | 日本語 | 日本政府公式のWebセキュリティガイド。無料PDF |
| PortSwigger Web Security Academy (portswigger.net) | 英語 | OWASP Top 10 を実際に攻撃して学ぶ。無料 |
| OWASP Juice Shop (owasp.org) | 英語 | 脆弱なWebアプリで攻撃を体験。CTF形式 |
| CryptoHack (cryptohack.org) | 英語 | 暗号学をパズル形式で学ぶ。AES/RSA/ECC |

### システム設計
| サイト | 言語 | 内容 |
|--------|------|------|
| System Design Primer (github.com/donnemartin) | 英語 | GitHubスター25万+。設計面接の総まとめ |
| ByteByteGo (blog.bytebytego.com) | 英語 | Alex Xu のブログ。設計図解が秀逸。一部無料 |
| Grokking System Design (educative.io) | 英語 | インタラクティブな設計面接コース。一部無料 |
| highscalability.com | 英語 | 実企業のアーキテクチャ事例集 |

### フロントエンド・TypeScript
| サイト | 言語 | 内容 |
|--------|------|------|
| TypeScript Deep Dive (basarat.gitbook.io) | 英語 | TS深掘り無料書籍。型システム詳細 |
| React公式ドキュメント (ja.react.dev) | 日本語 | React 最新の公式チュートリアル |
| web.dev (web.dev) | 英語(日本語一部) | Google公式。Core Web Vitals・パフォーマンス |
| JavaScript.info (javascript.info) | 英語(日本語版あり) | JS/TS基礎〜上級を網羅した無料教材 |

### PM・アジャイル・リーダーシップ
| サイト | 言語 | 内容 |
|--------|------|------|
| Scrum Guide 公式 (scrumguides.org) | 日本語 | スクラムガイド日本語版。13ページの必読文書 |
| IPA ITSS+ (ipa.go.jp/jinzai) | 日本語 | IT人材のスキル標準。キャリアパス参考 |
| Atlassian Agile Coach (atlassian.com/agile) | 英語 | アジャイル/スクラム/カンバンの解説。図解豊富 |
| re:Work by Google (rework.withgoogle.com) | 英語 | Googleの人材/チーム研究。心理的安全性など |

### ネットワーク・CCNA
| サイト | 言語 | 内容 |
|--------|------|------|
| 3分間ネットワーキング (3min-networking.com) | 日本語 | ネットワーク基礎を3分単位で解説 |
| ネットワークエンジニアとして (infraexpert.com) | 日本語 | CCNA/CCNP対策の定番サイト。図解豊富 |
| Packet Tracer (netacad.com) | 英語 | Cisco公式のネットワークシミュレータ。無料 |

### ITIL・ITSM
| サイト | 言語 | 内容 |
|--------|------|------|
| ITIL 4 Foundation Study Guide (各種) | 英語 | Axelos公式の学習リソース |
| IPA ITサービスマネージャ試験 過去問 (ipa.go.jp) | 日本語 | 過去問+解答が無料公開。ITSM知識の力試し |

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
| 「CPUパイプラインを説明せよ」 | [os_hardware_deep.py](phase_cs_fundamentals/os_hardware_deep.py) |
| 「SSD vs HDD の内部構造は？」 | [storage_engine_internals.py](phase_cs_fundamentals/storage_engine_internals.py) |
| 「GCアルゴリズムの違いは？」 | [compiler_runtime.py](phase_cs_fundamentals/compiler_runtime.py) |
| 「RSAの仕組みを数学的に」 | [cryptography_fundamentals.py](phase9_security/cryptography_fundamentals.py) |
| 「Little's Law を適用せよ」 | [reliability_math.py](phase_architecture/reliability_math.py) |
| 「Paxos vs Raft の違いは？」 | [distributed_systems_theory.py](phase_architecture/distributed_systems_theory.py) |
| 「Cosmos DB の整合性レベルは？」 | [azure_services_catalog.py](phase5_cloud/azure_services_catalog.py) |
| 「RAGの品質をどう評価する？」 | [llm_eval_and_guardrails.py](phase2_ai/llm_eval_and_guardrails.py) |
| 「Prompt Injectionの多層防御は？」 | [llm_eval_and_guardrails.py](phase2_ai/llm_eval_and_guardrails.py) |
| 「品質保証の指標は？」 | [qa_engineering_explained.py](qa_engineering_explained.py) |
| 「テスト設計技法を説明せよ」 | [qa_engineering_explained.py](qa_engineering_explained.py) |
| 「PMBOK 7thの変更点は？」 | [pmo_portfolio_explained.py](pmo_portfolio_explained.py) |
| 「EVMでプロジェクト状況を報告せよ」 | [pmo_portfolio_explained.py](pmo_portfolio_explained.py) |
| 「ITILのインシデント管理は？」 | [itil_itsm_explained.py](itil_itsm_explained.py) |
| 「変更管理のプロセスは？」 | [itil_itsm_explained.py](itil_itsm_explained.py) |
| 「VLANの設計方針は？」 | [network_engineering_explained.py](network_engineering_explained.py) |
| 「OSPF vs BGP の違いは？」 | [network_engineering_explained.py](network_engineering_explained.py) |

---

## 学習チェックリスト (全400+ トピック)

> 学んだらチェックを入れよう。Tier 1 → 4 の順に進めるのが効率的。

### 1. アルゴリズム・データ構造
- [ ] Big-O 計算量分析
- [ ] Two Pointers (Two Sum, 3Sum, Container)
- [ ] Sliding Window (最大部分和, 最長部分文字列)
- [ ] Binary Search (回転ソート配列, Koko)
- [ ] Heap / Priority Queue (K最大, K個ソート済リスト統合)
- [ ] Union-Find (島の数)
- [ ] DP (LCS, コイン問題, 編集距離)
- [ ] Dijkstra 最短経路
- [ ] LRU Cache 設計
- [ ] BFS / DFS
- [ ] トポロジカルソート
- [ ] Trie (挿入/検索/オートコンプリート)
- [ ] セグメント木
- [ ] バックトラッキング (順列, 部分集合, N-Queen)
- [ ] KMP 文字列マッチング
- [ ] Rolling Hash (Rabin-Karp)
- [ ] 単調スタック (次に大きい要素, 最大長方形)
- [ ] Bitmask DP (巡回セールスマン)

### 2. OS・ハードウェア
- [ ] CPUパイプライン (5段)
- [ ] パイプラインハザード & 分岐予測
- [ ] CPUキャッシュ & MESI プロトコル
- [ ] キャッシュシミュレータ (L1/L2/L3, 連想度, 追出し)
- [ ] 仮想メモリ (ページテーブル, TLB, ページフォルト)
- [ ] プロセススケジューリング (FIFO, SJF, RR, MLFQ, CFS)
- [ ] I/Oモデル (ブロッキング, ノンブロッキング, 多重化, 非同期)
- [ ] 割り込み & NUMA

### 3. ネットワーク
- [ ] TCP 3-way ハンドシェイク
- [ ] スライディングウィンドウ
- [ ] TCP 輻輳制御 (cwnd, Slow Start, CUBIC, BBR)
- [ ] Nagle アルゴリズム & Delayed ACK
- [ ] HTTP/1.1 (Head-of-Line Blocking)
- [ ] HTTP/2 (Multiplexing, Server Push)
- [ ] HTTP/3 & QUIC
- [ ] DNS (階層構造, キャッシュ, DNSSEC, レコード種別)
- [ ] CDN (キャッシュ, エッジロケーション)
- [ ] WebSocket
- [ ] Protocol Buffers / gRPC
- [ ] ロードバランシング (RR, 重み付き, Least Conn, Consistent Hash)
- [ ] TLS 1.3 ハンドシェイク
- [ ] 証明書チェーン & mTLS

### 4. ストレージエンジン
- [ ] HDD メカニクス (シーク時間, 回転遅延, IOPS)
- [ ] SSD / FTL (ウェアレベリング, Write Amplification)
- [ ] ファイルシステム (inode, ブロック割当, ジャーナリング)
- [ ] Copy-on-Write ファイルシステム
- [ ] バッファプール管理 (LRU, Clock, LRU-K)
- [ ] B+Tree (挿入, 分割, 範囲スキャン)
- [ ] Skip List
- [ ] Bloom Filter
- [ ] LSM-Tree (MemTable, SSTable, Compaction戦略)
- [ ] WAL (先行書き込みログ, ARIES リカバリ)
- [ ] RAID レベル (0, 1, 5, 6, 10)
- [ ] Merkle Tree (データ整合性検証)

### 5. コンパイラ・ランタイム
- [ ] レキサー / 字句解析 (正規表現, DFA/NFA)
- [ ] パーサー / 構文解析 (BNF, 再帰下降, Pratt)
- [ ] LL(k) vs LR(k) 比較
- [ ] AST (抽象構文木)
- [ ] 型推論 (Hindley-Milner, 単一化)
- [ ] 中間表現 (Three Address Code, SSA)
- [ ] 最適化パス (定数畳み込み, DCE, インライン展開)
- [ ] レジスタ割り当て (グラフ彩色, 線形スキャン)
- [ ] GC: Mark-Sweep / Copying / Generational
- [ ] GC: G1 / ZGC / Shenandoah / 参照カウント
- [ ] JIT (ティアードコンパイル, トレーシングJIT)
- [ ] ウォームアップ & 脱最適化
- [ ] バイトコード (JVM / CPython / WASM)
- [ ] メモリレイアウト (スタックフレーム, vtable, エスケープ解析)

### 6. 並行・並列処理
- [ ] 並行 vs 並列 (Rob Pike の定義)
- [ ] プロセス vs スレッド vs コンテキストスイッチ
- [ ] メモリモデル (happens-before, SC, TSO, JMM)
- [ ] Mutex / Semaphore / RWLock / Condition Variable
- [ ] CAS (Compare-And-Swap) & ABA問題
- [ ] Lock-Free vs Wait-Free
- [ ] デッドロック (Coffman 4条件, 検出/予防/回避)
- [ ] ライブロック & スターベーション
- [ ] C10K問題 & イベントループ (epoll/kqueue)
- [ ] async/await & コルーチン
- [ ] Python GIL (内部構造, PEP 703)
- [ ] goroutine & CSP & channel
- [ ] Actor モデル (Erlang, Supervision Tree)
- [ ] 2PC / Saga / Raft (分散並行)

### 7. データベース・データエンジニアリング
- [ ] 正規化 (1NF〜BCNF)
- [ ] スター/スノーフレークスキーマ
- [ ] Data Vault 2.0
- [ ] ウィンドウ関数 (ROW_NUMBER, RANK, LAG)
- [ ] CTE & 再帰CTE
- [ ] EXPLAIN 実行計画の読み方
- [ ] インデックス戦略 (B-Tree / Hash / GIN / GiST / BRIN)
- [ ] NoSQL 4分類 (KV / Document / Wide-column / Graph)
- [ ] CAP定理 & Dynamo論文
- [ ] WAL & MVCC (PostgreSQL vs MySQL)
- [ ] B+Tree & LSM-Tree (DB内部)
- [ ] ETL vs ELT
- [ ] Airflow DAG 設計
- [ ] dbt (ref / incremental / snapshot / test)
- [ ] Kafka (Partition, Consumer Group, ISR, 配信保証)
- [ ] Flink (Window, Watermark, State, Checkpoint)
- [ ] レイクハウス (Delta Lake / Iceberg / Hudi)
- [ ] ACID on Data Lake & Time Travel
- [ ] データ品質 (Great Expectations, データ契約)
- [ ] データガバナンス (リネージ, カタログ)
- [ ] OLAP比較 (BigQuery / Redshift / Snowflake / ClickHouse)

### 8. API・バックエンド
- [ ] REST 原則 & Richardson Maturity Model
- [ ] REST vs GraphQL vs gRPC
- [ ] ページネーション (Cursor vs Offset)
- [ ] レート制限 (Token Bucket, Sliding Window)
- [ ] 冪等性
- [ ] CQRS & Event Sourcing
- [ ] Circuit Breaker

### 9. AI・機械学習
- [ ] 確率分布 (正規, ポアソン, ベルヌーイ)
- [ ] ベイズ定理 & 中心極限定理
- [ ] 仮説検定 (p値, 信頼区間) & A/Bテスト
- [ ] 教師あり / 教師なし / 強化学習
- [ ] バイアス-バリアンストレードオフ
- [ ] 交差検証 (K-Fold)
- [ ] 線形回帰 / ロジスティック回帰
- [ ] 決定木 / Random Forest / XGBoost
- [ ] SVM / k-means / PCA
- [ ] パーセプトロン & 活性化関数
- [ ] 勾配降下法 & バックプロパゲーション
- [ ] CNN (畳み込み, プーリング, 特徴マップ)
- [ ] RNN / LSTM
- [ ] Attention 機構 & Transformer
- [ ] GPT アーキテクチャ
- [ ] トークナイゼーション (BPE)
- [ ] ファインチューニング (LoRA / QLoRA)
- [ ] RLHF & DPO
- [ ] プロンプトエンジニアリング
- [ ] RAG (ベクトル検索, Embedding, チャンキング)
- [ ] AI エージェント (ReAct, Tool Use, Multi-Agent)
- [ ] MLOps (MLflow, Feature Store, モデル監視)
- [ ] 物体検出 (YOLO) & セグメンテーション
- [ ] 拡散モデル (画像生成)
- [ ] RAGAS & DeepEval (RAG/LLM評価)
- [ ] ガードレール (NeMo, Presidio, Prompt Injection防御)

### 10. アーキテクチャ・分散システム
- [ ] システム設計面接 5ステップ
- [ ] Back-of-Envelope 概算 (QPS, ストレージ, 帯域)
- [ ] ロードバランサー (L4/L7, アルゴリズム)
- [ ] キャッシュ (Cache-Aside / Write-Through / Write-Back)
- [ ] DB スケーリング (シャーディング, レプリケーション)
- [ ] メッセージキュー (Kafka vs RabbitMQ vs SQS)
- [ ] CDN (Push vs Pull)
- [ ] 設計問題: URL短縮
- [ ] 設計問題: Twitter タイムライン (Fan-out)
- [ ] 設計問題: チャットシステム (WebSocket)
- [ ] 設計問題: Rate Limiter
- [ ] 設計問題: 分散KVストア (Consistent Hashing)
- [ ] 設計問題: 検索オートコンプリート (Trie)
- [ ] 設計問題: Web Crawler
- [ ] 設計問題: 通知システム
- [ ] 設計問題: 動画配信 (トランスコード, ABR)
- [ ] マイクロサービス (API Gateway, Saga, Circuit Breaker)
- [ ] Consistent Hashing & Vector Clock
- [ ] Raft 合意アルゴリズム
- [ ] Paxos & FLP不可能性定理
- [ ] 線形化可能性 & 因果一貫性
- [ ] ビザンチンBFT
- [ ] CRDT (Conflict-Free Replicated Data Types)
- [ ] Lamport Clock / Vector Clock / HLC
- [ ] Little's Law & Amdahl's Law
- [ ] M/M/1 待ち行列理論
- [ ] USL (Universal Scalability Law)
- [ ] テールレイテンシ (P99, Hedged Requests)
- [ ] 可用性計算 (直列/並列, MTBF/MTTR)

### 11. インフラ・DevOps・SRE
- [ ] Docker (Namespace, cgroups, OverlayFS)
- [ ] Dockerfile 最適化 (マルチステージビルド)
- [ ] Docker Compose
- [ ] K8s アーキテクチャ (Control Plane, etcd)
- [ ] K8s リソース (Deployment, StatefulSet, DaemonSet)
- [ ] K8s ネットワーキング (Service, Ingress, Service Mesh)
- [ ] K8s スケーリング (HPA, VPA, KEDA)
- [ ] Helm & GitOps (ArgoCD)
- [ ] CI/CD パイプライン
- [ ] 5 デプロイ戦略 (Recreate/Rolling/Blue-Green/Canary/Progressive)
- [ ] Feature Flag
- [ ] IaC (Terraform: plan/apply/drift)
- [ ] DB マイグレーション安全チェック
- [ ] シークレット管理 (Vault)
- [ ] Well-Architected Framework (6 柱)
- [ ] マルチリージョン & DR戦略
- [ ] サーバーレス (Cold Start, コスト見積)
- [ ] FinOps
- [ ] SLI / SLO / SLA & Error Budget
- [ ] Burn Rate アラート
- [ ] 可観測性3本柱 (Metrics, Logs, Traces)
- [ ] インシデント対応 (OODA, 重大度分類)
- [ ] カオスエンジニアリング
- [ ] ポストモーテム
- [ ] ランブック
- [ ] USE/RED メソッド
- [ ] キャパシティプランニング

### 12. セキュリティ・暗号
- [ ] 対称鍵暗号 (AES: ECB/CBC/GCM)
- [ ] 非対称鍵暗号 (RSA, ECC)
- [ ] DH鍵交換 & Forward Secrecy
- [ ] ハッシュ (SHA-256, HMAC)
- [ ] パスワードハッシュ (bcrypt / Argon2)
- [ ] PKI (証明書チェーン, CA, CSR)
- [ ] TLS 1.3 (0-RTT, cipher suite)
- [ ] OWASP Top 10 (Injection, XSS, SSRF, Broken Access)
- [ ] OAuth 2.0 (Authorization Code, PKCE, Client Credentials)
- [ ] OpenID Connect & JWT (ヘッダ/ペイロード/署名)
- [ ] SAML
- [ ] ゼロトラスト (BeyondCorp, mTLS, SPIFFE/SPIRE)
- [ ] クラウドセキュリティ (IAM, 最小権限, KMS)
- [ ] コンテナセキュリティ (Trivy, OPA, Pod Security)
- [ ] 脅威モデリング (STRIDE)
- [ ] インシデント対応 (NIST IR, フォレンジック, SIEM/SOAR)

### 13. プログラミング実践
- [ ] テストピラミッド (Unit 70% / Integration 20% / E2E 10%)
- [ ] TDD (Red-Green-Refactor)
- [ ] テストダブル 5種 (Dummy, Stub, Spy, Mock, Fake)
- [ ] Property-based Testing (Hypothesis)
- [ ] Mutation Testing
- [ ] Fuzzing (AFL, OSS-Fuzz)
- [ ] Contract Testing (Pact)
- [ ] Big-O 分析 & プロファイリング (cProfile, perf)
- [ ] メモリリーク検出 (tracemalloc)
- [ ] キャッシュ戦略 (LRU/LFU, Cache-Aside)
- [ ] 接続プール (Little's Law)
- [ ] Python: メタクラス & デスクリプタ
- [ ] Python: GIL 内部 & asyncio 内部
- [ ] Python: 型ヒント高度 (Protocol, TypeVar, ParamSpec)
- [ ] GoF 23 デザインパターン (生成5/構造7/振舞11)
- [ ] SOLID 原則 (SRP/OCP/LSP/ISP/DIP)
- [ ] リファクタリング & コードスメル
- [ ] 技術的負債 (4象限モデル)
- [ ] 多言語比較 (Python/TS/Go/Rust/Java)

### 14. フロントエンド
- [ ] ブラウザレンダリング (DOM/CSSOM, CRP, Layout/Paint/Composite)
- [ ] V8 エンジン (Ignition/TurboFan)
- [ ] イベントループ (マイクロ/マクロタスク)
- [ ] クロージャ & プロトタイプチェーン
- [ ] React (仮想DOM, Fiber, Hooks内部)
- [ ] React レンダリング最適化 (memo, useMemo, useCallback)
- [ ] Suspense & Streaming
- [ ] Next.js (SSR/SSG/ISR/RSC, App Router, Server Actions)
- [ ] 状態管理 (Redux / Zustand / Jotai / React Query / SWR)
- [ ] TypeScript 高度 (Generics, Conditional/Mapped/Template Literal Types, infer)
- [ ] Core Web Vitals (LCP, INP, CLS)
- [ ] Code Splitting & Tree Shaking
- [ ] Service Worker
- [ ] CSS 設計 (CSS-in-JS vs Tailwind vs CSS Modules, Flexbox/Grid)
- [ ] フロントエンドテスト (Jest/Vitest, RTL, Playwright, MSW)
- [ ] アクセシビリティ (WCAG, WAI-ARIA, セマンティックHTML)
- [ ] Web API (WebSocket, WebRTC, Web Workers, IndexedDB)
- [ ] ビルドツール (Webpack / Vite / Turbopack, HMR, Module Federation)

### 15. PM・リーダーシップ
- [ ] Staff+ エンジニア (4アーキタイプ, Technical Vision)
- [ ] IC vs Manager トラック
- [ ] チームトポロジー (4チーム型, 認知負荷, Team API)
- [ ] SPACE フレームワーク (5軸)
- [ ] DORA メトリクス (4+1指標)
- [ ] Scrum / Kanban / SAFe
- [ ] 見積もり (ストーリーポイント, Planning Poker)
- [ ] レトロスペクティブ
- [ ] プロダクトディスカバリー (4リスク)
- [ ] RICE スコアリング
- [ ] OKR (Objectives & Key Results)
- [ ] ロードマップ (Now/Next/Later)
- [ ] PMF (Product-Market Fit)
- [ ] コンウェイの法則 & 逆コンウェイ戦略
- [ ] Two-Pizza Team & Spotify Model
- [ ] ADR (Architecture Decision Record) & RFC
- [ ] 技術面接設計 (構造化面接, STAR形式)
- [ ] メンタリング vs スポンサーシップ
- [ ] ユニットエコノミクス (CAC/LTV/Churn)
- [ ] テクニカルライティング & BLUF
- [ ] ステークホルダー管理
- [ ] Disagree and Commit

### 16. クラウドサービス
- [ ] AWS サービスカタログ (主要サービス)
- [ ] GCP サービスカタログ
- [ ] Azure サービスカタログ (57サービス)
- [ ] Cosmos DB 整合性レベル (5段階)
- [ ] 3クラウド比較マッピング
- [ ] 認定ロードマップ

### 17. QA・品質保証
- [ ] ISO 25010 品質モデル (8特性)
- [ ] IEEE 829 テスト計画書
- [ ] テスト設計技法 (同値分割, 境界値, デシジョンテーブル, 状態遷移, ペアワイズ)
- [ ] テストレベル (単体/結合/システム/受入)
- [ ] テスト自動化 (テストピラミッド, Selenium/Playwright, CI統合)
- [ ] 性能テスト (負荷/ストレス/耐久, JMeter/k6/Locust)
- [ ] 品質メトリクス (DDP, バグ密度, テストカバレッジ)
- [ ] CMMI 成熟度レベル (1-5)
- [ ] ISO 9001 品質マネジメント
- [ ] JSTQB / ISTQB (テスト技術者資格)
- [ ] 探索的テスト (セッションベース)
- [ ] シフトレフトテスト

### 18. PMO・ポートフォリオ管理
- [ ] PMO 3類型 (支援型/管理型/指揮型)
- [ ] PMBOK 第7版 (12原則, 8パフォーマンス領域)
- [ ] WBS (Work Breakdown Structure)
- [ ] CPM (クリティカルパス法) & PERT
- [ ] CCPM (クリティカルチェーン)
- [ ] EVM (PV/EV/AC, SPI/CPI, EAC/ETC)
- [ ] リスク管理 (定性/定量分析, EMV, モンテカルロ)
- [ ] ステークホルダー分析 (権力/関心マトリクス)
- [ ] ポートフォリオ管理 (優先順位付け, バブルチャート)
- [ ] ガバナンス (ステージゲート, フェーズゲート)
- [ ] RFP / 提案書評価 / 契約形態 (FP/T&M/CR)
- [ ] プロジェクト憲章 & キックオフ

### 19. ITIL / ITSM
- [ ] ITIL 4 フレームワーク (SVS, SVC)
- [ ] ITIL 7つの基本原則
- [ ] インシデント管理 (分類, エスカレーション, 重大インシデント)
- [ ] 問題管理 (根本原因分析, 既知のエラー, KEDB)
- [ ] 変更管理 (標準/通常/緊急変更, CAB)
- [ ] サービスデスク (SPOC, オムニチャネル)
- [ ] CMDB (構成管理データベース, CI, 関係モデル)
- [ ] SLA管理 & サービスカタログ
- [ ] ITSM + DevOps 融合
- [ ] 社内SE 実務 (ヘルプデスク, IT資産管理, BCP)
- [ ] サービスレベル管理 (SLA/OLA/UC)

### 20. ネットワーク実務
- [ ] OSI 参照モデル (L1-L7)
- [ ] IP アドレス & サブネット計算 (CIDR, VLSM)
- [ ] VLAN (タグ/アクセスポート, トランク, Inter-VLAN)
- [ ] STP (スパニングツリー, RSTP, ループ防止)
- [ ] ルーティング (スタティック, OSPF, BGP)
- [ ] OSPF (エリア設計, LSA, SPFアルゴリズム)
- [ ] BGP (AS, eBGP/iBGP, 経路制御)
- [ ] Firewall & ACL (ステートフル/ステートレス)
- [ ] VPN (IPsec, SSL-VPN, WireGuard)
- [ ] SD-WAN (MPLS代替, ZTP, アプリケーション認識)
- [ ] 無線LAN (802.11ax/Wi-Fi 6, チャネル設計, WPA3)
- [ ] ネットワーク監視 (SNMP, syslog, NetFlow, Zabbix/PRTG)
- [ ] トラブルシューティング (ping, traceroute, tcpdump, Wireshark)
