#!/usr/bin/env python3
"""
Cloud Services Catalog - AWS / GCP マネージドサービス完全ガイド
=============================================================

「どの場面でどのサービスを使うべきか」を体系的に整理した実行可能リファレンス。

実行: python3 cloud_services_catalog.py
"""

import textwrap
from dataclasses import dataclass, field
from typing import Optional

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ユーティリティ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SEP = "━" * 60
THIN = "─" * 60


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title: str) -> None:
    print(f"\n{THIN}")
    print(f"  {title}")
    print(THIN)


def svc(name: str, what: str, when: str, not_when: str,
        pricing: str, alt: str) -> None:
    print(f"\n  ▶ {name}")
    print(f"    何: {what}")
    print(f"    いつ使う: {when}")
    print(f"    いつ使わない: {not_when}")
    print(f"    料金: {pricing}")
    print(f"    代替: {alt}")


def question(text: str) -> None:
    print(f"\n  🤔 考えてほしい疑問: {text}")


def task(text: str) -> None:
    print(f"\n  [実装してみよう] {text}")


def diagram(lines: list) -> None:
    print()
    for line in lines:
        print(f"    {line}")
    print()


def table(headers: list, rows: list) -> None:
    """簡易テーブル表示"""
    widths = [max(len(str(r[i])) for r in [headers] + rows)
              for i in range(len(headers))]
    fmt = " | ".join(f"{{:<{w}}}" for w in widths)
    print(f"    {fmt.format(*headers)}")
    print(f"    {'-+-'.join('-' * w for w in widths)}")
    for row in rows:
        print(f"    {fmt.format(*row)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print(SEP)
    print("  Cloud Services Catalog")
    print("  AWS / GCP マネージドサービス完全ガイド")
    print(SEP)
    print("""
  このカタログの使い方:
  1. カテゴリ別にサービスを網羅的に解説
  2. 各サービスに「いつ使う/使わない」を明記
  3. Decision Tree で選択を体系化
  4. 設計パターン別のサービス組み合わせ例
  5. 面接問題で実践力チェック
    """)

    # ================================================================
    # 1. コンピュート
    # ================================================================
    section("1. コンピュート (Compute)")

    print("""
  コンピュートの選択は「抽象度」で考える:

    低い ← 抽象度 → 高い
    EC2 → ECS/EKS → Fargate → App Runner → Lambda

  抽象度が高いほど運用は楽だが、制御は減る。
    """)

    subsection("AWS コンピュート")

    svc("Amazon EC2",
        "仮想サーバー (IaaS)。OS・ミドルウェアを自由に構成",
        "GPU が必要 / 特殊カーネル設定 / 長時間バッチ / レガシーアプリ移行",
        "単純な Web API → Fargate や Lambda のほうが運用コスト低",
        "オンデマンド時間課金。Reserved/Spot で最大90%割引",
        "GCP: Compute Engine / OSS: 自前サーバー")

    svc("AWS Lambda",
        "イベント駆動のサーバーレス関数。最大15分実行",
        "API のバックエンド / S3イベント処理 / cron的ジョブ / Glue起動トリガー",
        "15分超の処理 / 大量メモリ(10GB超) / WebSocket長時間接続",
        "リクエスト数 + 実行時間(ms) × メモリ。無料枠100万req/月",
        "GCP: Cloud Functions / OSS: OpenFaaS, Knative")

    svc("AWS Fargate",
        "コンテナ用サーバーレスエンジン。EC2管理不要で ECS/EKS と組合せ",
        "コンテナ化された Web API / マイクロサービス / 常時起動が必要",
        "GPU が必要(EC2起動タイプを使う) / 極端なコスト最適化",
        "vCPU + メモリの秒課金",
        "GCP: Cloud Run / OSS: K8s + 自前クラスタ")

    svc("Amazon ECS",
        "AWS 独自のコンテナオーケストレーション。タスク定義でコンテナ管理",
        "AWS に寄せた設計でシンプルにコンテナ運用したい / K8s は過剰",
        "マルチクラウド / K8s エコシステムの活用が必要",
        "ECS 自体は無料。裏の EC2 or Fargate に課金",
        "GCP: Cloud Run / OSS: Docker Compose, Nomad")

    svc("Amazon EKS",
        "マネージド Kubernetes。K8s API 完全互換",
        "K8s エコシステム活用 / マルチクラウド移植性 / Istio 等が必要",
        "小規模チーム(ECS のほうが楽) / サーバーレスで済む場合",
        "クラスタ $0.10/h + ワーカーノード(EC2/Fargate)費用",
        "GCP: GKE / OSS: 自前 K8s, k3s")

    svc("AWS App Runner",
        "コンテナ/ソースコードから自動デプロイ。PaaS 的な体験",
        "シンプルな Web API を最速でデプロイ / プロトタイプ",
        "複雑なネットワーク構成 / VPC 内リソースへの接続(制限あり)",
        "vCPU + メモリの秒課金。アクティブ時とアイドル時で異なる",
        "GCP: App Engine, Cloud Run / OSS: Heroku")

    svc("AWS Batch",
        "大規模バッチジョブのスケジューリングと実行",
        "数千ジョブの並列実行 / ゲノム解析 / レンダリング / ML学習",
        "リアルタイム処理 / 単発の小さなジョブ(Lambda で十分)",
        "Batch 自体は無料。裏の EC2/Fargate に課金",
        "GCP: Batch / OSS: Apache Airflow + K8s")

    svc("Amazon Lightsail",
        "簡易 VPS。月額固定料金で予測しやすい",
        "小規模 Web サイト / WordPress / 個人プロジェクト",
        "本格的な本番環境 / スケールが必要",
        "月額固定(例: $3.50/月〜)",
        "GCP: なし(Compute Engine小規模) / OSS: VPS各社")

    subsection("GCP コンピュート")

    svc("Google Compute Engine (GCE)",
        "仮想サーバー。EC2 相当",
        "カスタム VM / GPU / 長時間処理",
        "コンテナ化できる場合 → Cloud Run のほうが楽",
        "時間課金。Preemptible VM で最大80%割引",
        "AWS: EC2")

    svc("Cloud Functions",
        "イベント駆動サーバーレス関数。第2世代は Cloud Run ベース",
        "Pub/Sub トリガー / GCS イベント / 軽量 API",
        "長時間処理 / 大量メモリ / コンテナが必要",
        "呼び出し数 + 実行時間 + メモリ",
        "AWS: Lambda")

    svc("Cloud Run",
        "コンテナをサーバーレスで実行。HTTP/gRPC 対応",
        "コンテナ化された API / Web アプリ / バッチジョブ",
        "GPU 必須 / 極端な低レイテンシ要件",
        "リクエスト数 + vCPU秒 + メモリ秒。ゼロスケール可",
        "AWS: Fargate + ALB, App Runner")

    svc("GKE (Google Kubernetes Engine)",
        "マネージド K8s。Autopilot モードで完全マネージド化可能",
        "大規模マイクロサービス / K8s エコシステム活用",
        "小規模アプリ → Cloud Run のほうが楽",
        "クラスタ管理費 + ノード費用。Autopilot は Pod 単位課金",
        "AWS: EKS")

    svc("App Engine",
        "PaaS。Standard(サーバーレス的) と Flexible(コンテナベース)がある",
        "レガシー GCP アプリ / シンプルな Web アプリ",
        "新規なら Cloud Run のほうが柔軟。App Engine は制約多め",
        "インスタンス時間課金",
        "AWS: Elastic Beanstalk, App Runner")

    question("Lambda vs Fargate の分岐点は何秒の処理時間？ → 15分が上限だが、"
             "コールドスタートや同時実行数制限も考慮が必要")

    print("""
  ■ コンピュート Decision Tree:

    処理時間15分以内？
    ├─ Yes → ステートレス？
    │   ├─ Yes → イベント駆動？
    │   │   ├─ Yes → Lambda / Cloud Functions
    │   │   └─ No  → App Runner / Cloud Run
    │   └─ No  → Fargate / Cloud Run (常時起動)
    └─ No  → コンテナ化できる？
        ├─ Yes → ECS+Fargate or EKS / GKE
        └─ No  → EC2 / GCE
    """)

    task("Lambda で S3 にファイルがアップロードされたら "
         "サムネイルを生成する関数を書いてみよう (boto3 + Pillow)")

    # ================================================================
    # 2. ストレージ
    # ================================================================
    section("2. ストレージ (Storage)")

    subsection("AWS ストレージ")

    svc("Amazon S3",
        "オブジェクトストレージ。無制限容量。99.999999999% 耐久性",
        "静的ファイル配信 / データレイク / バックアップ / ログ保存",
        "ファイルシステムとしてマウントしたい → EFS / POSIX アクセス要件",
        "GB単価 + リクエスト数 + 転送量。ストレージクラスで大幅削減",
        "GCP: Cloud Storage / OSS: MinIO")

    print("""
    S3 ストレージクラス一覧:
    ┌──────────────────────┬───────────┬──────────────────────┐
    │ クラス               │ GB/月単価  │ ユースケース          │
    ├──────────────────────┼───────────┼──────────────────────┤
    │ S3 Standard          │ $0.023    │ 頻繁アクセス          │
    │ S3 Intelligent-Tier  │ 自動最適化 │ アクセスパターン不明   │
    │ S3 Standard-IA       │ $0.0125   │ 低頻度だが即時取得    │
    │ S3 One Zone-IA       │ $0.010    │ 再生成可能な低頻度    │
    │ S3 Glacier Instant   │ $0.004    │ 四半期1回, 即時取得   │
    │ S3 Glacier Flexible  │ $0.0036   │ 年1-2回, 数分〜数時間 │
    │ S3 Glacier Deep Arch │ $0.00099  │ 7年保存義務等, 12h取得│
    └──────────────────────┴───────────┴──────────────────────┘
    """)

    svc("Amazon EBS (Elastic Block Store)",
        "EC2 にアタッチするブロックストレージ。SSD(gp3/io2)/HDD(st1/sc1)",
        "EC2 のルートボリューム / DB のストレージ / 高 IOPS が必要",
        "複数 EC2 から同時読み書き → EFS / 大量アーカイブ → S3",
        "GB/月 + IOPS(io2の場合)。gp3: $0.08/GB/月",
        "GCP: Persistent Disk")

    svc("Amazon EFS (Elastic File System)",
        "マネージド NFS。複数 EC2/Fargate から同時マウント可",
        "共有ファイルシステム / CMS の共有メディア / ML 学習データ共有",
        "単一 EC2 だけのストレージ → EBS のほうが安い",
        "GB/月。Standard: $0.30/GB/月, IA: $0.025/GB/月",
        "GCP: Filestore / OSS: NFS サーバー")

    svc("Amazon FSx",
        "マネージドファイルシステム (Lustre, Windows, NetApp, OpenZFS)",
        "HPC (Lustre) / Windows ファイルサーバー移行 / 高性能共有ストレージ",
        "Linux の共有ストレージだけなら EFS で十分",
        "ストレージ容量 + スループット",
        "GCP: Filestore (NetApp CVS)")

    subsection("GCP ストレージ")

    svc("Cloud Storage (GCS)",
        "オブジェクトストレージ。S3 相当。BigQuery と直接連携",
        "データレイク / 静的ホスティング / バックアップ",
        "ブロックストレージが必要 → Persistent Disk",
        "GB/月 + オペレーション数 + 転送量",
        "AWS: S3")

    svc("Persistent Disk",
        "GCE にアタッチするブロックストレージ。スナップショット可",
        "VM のブートディスク / DB ストレージ",
        "共有ファイルシステム → Filestore",
        "GB/月。Standard: $0.04/GB, SSD: $0.17/GB",
        "AWS: EBS")

    svc("Filestore",
        "マネージド NFS。GKE や GCE からマウント",
        "共有ファイルシステム / K8s の ReadWriteMany PV",
        "小さなファイル共有 → GCS で十分な場合が多い",
        "容量 + ティア(Basic/Enterprise)",
        "AWS: EFS")

    question("S3 Intelligent-Tiering は万能に見えるが、128KB未満の"
             "小さなファイルが大量にある場合は Standard のほうが安くなる。なぜ？"
             " → モニタリング料金が 1,000オブジェクトあたり$0.0025 かかるため")

    task("boto3 で S3 バケットを作成し、ライフサイクルルールを設定して "
         "30日後に IA、90日後に Glacier へ自動移行するスクリプトを書こう")

    # ================================================================
    # 3. データベース
    # ================================================================
    section("3. データベース (Database)")

    print("""
  DB 選択の大原則:
    1. まずデータモデル(リレーショナル or NoSQL)を決める
    2. 次にアクセスパターン(OLTP or OLAP)を決める
    3. スケール要件(読み書きの量、レイテンシ)で絞る
    4. 最後にマネージド度(フルマネージド or セルフマネージド)を選ぶ
    """)

    subsection("AWS リレーショナル DB")

    svc("Amazon RDS",
        "マネージド RDBMS。MySQL, PostgreSQL, MariaDB, Oracle, SQL Server 対応",
        "一般的な OLTP / 既存 DB のマネージド化 / マルチ AZ で高可用性",
        "グローバル分散が必要 → Aurora Global / 超大規模 → Aurora or Spanner",
        "インスタンス時間 + ストレージ + I/O(Aurora の場合)",
        "GCP: Cloud SQL / OSS: セルフホスト MySQL/PostgreSQL")

    svc("Amazon Aurora",
        "AWS 独自の MySQL/PostgreSQL 互換 DB。RDS の3〜5倍高速",
        "高性能 OLTP / リードレプリカ15台 / Global Database / Serverless v2",
        "MySQL/PostgreSQL 以外のエンジンが必要 / 予算が厳しい小規模案件",
        "インスタンス時間 + ストレージ + I/O。Serverless v2 は ACU 課金",
        "GCP: AlloyDB / OSS: CockroachDB, TiDB")

    svc("Amazon Aurora Serverless v2",
        "Aurora の自動スケーリング版。0.5〜128 ACU で瞬時にスケール",
        "アクセスが不規則なワークロード / 開発環境 / 夜間トラフィック減少",
        "常時高負荷 → プロビジョンドのほうがコスパ良い",
        "ACU (Aurora Capacity Unit) の時間課金",
        "GCP: AlloyDB / Cloud SQL")

    subsection("AWS NoSQL")

    svc("Amazon DynamoDB",
        "フルマネージド Key-Value / ドキュメント DB。無限スケール、1桁ms レイテンシ",
        "セッション管理 / ユーザープロファイル / IoT データ / ゲームスコア / "
        "アクセスパターンが事前に明確な場合",
        "複雑なクエリ(JOIN多用) → RDS / アドホック分析 → 不向き",
        "オンデマンド: 読み書きリクエスト単位, プロビジョンド: RCU/WCU 予約",
        "GCP: Firestore, Bigtable / OSS: Cassandra, ScyllaDB")

    print("""
    ★ DynamoDB の重要概念:
    ┌────────────────────────────────────────────────────────┐
    │ ● パーティションキー: データ分散の軸                      │
    │ ● ソートキー: パーティション内の順序付け                  │
    │ ● GSI (Global Secondary Index): 別のキーでクエリ         │
    │ ● LSI (Local Secondary Index): 同パーティション別ソート  │
    │ ● DynamoDB Streams: 変更データキャプチャ (CDC)            │
    │ ● TTL: 自動データ削除 (セッション等に便利)                │
    │ ● DAX: インメモリキャッシュ (マイクロ秒レイテンシ)         │
    └────────────────────────────────────────────────────────┘
    """)

    svc("Amazon DynamoDB Streams ★",
        "DynamoDB テーブルの変更をリアルタイムにキャプチャ (CDC)",
        "変更通知 → Lambda でリアクティブ処理 / データ同期 / 集計更新 / "
        "検索インデックス (OpenSearch) の自動同期",
        "高スループットストリーミング → Kinesis のほうが適切",
        "読み取りリクエスト単位課金。24時間保持",
        "GCP: Firestore リアルタイムリスナー / OSS: Debezium (CDC)")

    svc("Amazon ElastiCache",
        "マネージド Redis / Memcached。インメモリキャッシュ/データストア",
        "DB クエリキャッシュ / セッション管理 / リーダーボード / Pub/Sub",
        "永続データの一次保存 → DB を使う / Serverless が必要 → MemoryDB",
        "ノードタイプ × 時間課金",
        "GCP: Memorystore / OSS: Redis, Memcached")

    svc("Amazon MemoryDB for Redis",
        "Redis 互換の耐久性あるインメモリ DB。マルチ AZ 自動フェイルオーバー",
        "Redis をプライマリ DB として使いたい / 耐久性 + 低レイテンシの両立",
        "一時的なキャッシュだけなら ElastiCache で十分(安い)",
        "ノード時間 + データストレージ",
        "GCP: Memorystore / OSS: Redis + AOF 永続化")

    svc("Amazon Neptune",
        "マネージドグラフ DB (Gremlin / SPARQL / openCypher)",
        "SNS のフレンド関係 / レコメンデーション / 不正検出 / ナレッジグラフ",
        "単純なリレーション → RDS の JOIN で十分",
        "インスタンス時間 + ストレージ + I/O",
        "GCP: なし (JanusGraph on Bigtable) / OSS: Neo4j, JanusGraph")

    svc("Amazon Timestream",
        "時系列 DB。IoT センサーデータ / メトリクス保存",
        "IoT データ / アプリメトリクス / 時系列分析",
        "汎用クエリ / リレーショナルデータ",
        "書き込み量 + クエリスキャン量 + ストレージ",
        "GCP: Bigtable (時系列用途) / OSS: InfluxDB, TimescaleDB")

    svc("Amazon DocumentDB",
        "MongoDB 互換のドキュメント DB",
        "既存 MongoDB アプリの移行 / MongoDB API が必要",
        "新規なら DynamoDB のほうがフルマネージドで楽",
        "インスタンス時間 + ストレージ + I/O",
        "GCP: Firestore / OSS: MongoDB")

    svc("Amazon Keyspaces",
        "Apache Cassandra 互換のワイドカラム DB",
        "既存 Cassandra アプリの移行 / 大規模書き込み",
        "新規ならDynamoDB のほうが機能豊富",
        "読み書きスループット + ストレージ",
        "GCP: Bigtable / OSS: Apache Cassandra, ScyllaDB")

    subsection("GCP データベース")

    svc("Cloud SQL",
        "マネージド RDBMS (MySQL, PostgreSQL, SQL Server)",
        "一般的 OLTP / RDS 相当の用途",
        "グローバル分散 → Spanner / NoSQL → Firestore",
        "インスタンス時間 + ストレージ",
        "AWS: RDS")

    svc("Cloud Spanner",
        "グローバル分散リレーショナル DB。強整合性 + 水平スケール",
        "グローバル金融システム / 大規模ゲームバックエンド / "
        "リレーショナル + 無限スケールが必要",
        "小規模アプリ → 高価すぎる(最低ノード費用が高い)",
        "ノード時間($0.90/h〜) + ストレージ",
        "AWS: Aurora Global (近いが完全同等ではない) / OSS: CockroachDB")

    svc("Firestore",
        "サーバーレス ドキュメント DB。リアルタイム同期対応",
        "モバイル/Web のバックエンド / リアルタイムチャット / オフライン同期",
        "複雑なクエリ → Cloud SQL / 高書き込みスループット → Bigtable",
        "読み書きオペレーション + ストレージ",
        "AWS: DynamoDB / OSS: MongoDB, CouchDB")

    svc("Bigtable",
        "ワイドカラム NoSQL。ペタバイト規模・低レイテンシ",
        "IoT 時系列 / アドテク / 金融ティックデータ / 大規模分析用ストレージ",
        "小規模データ → Firestore で十分。複雑クエリ → Cloud SQL",
        "ノード時間($0.65/h) + ストレージ",
        "AWS: Keyspaces, DynamoDB / OSS: HBase, Cassandra")

    svc("AlloyDB",
        "PostgreSQL 互換の高性能 DB。Aurora 対抗",
        "高性能 OLTP + 分析の混在ワークロード",
        "MySQL が必要 → Cloud SQL / 小規模 → Cloud SQL で十分",
        "インスタンス時間 + ストレージ",
        "AWS: Aurora PostgreSQL")

    print("""
  ■ データベース Decision Tree:

    リレーショナル(SQL)が必要？
    ├─ Yes → グローバル分散が必要？
    │   ├─ Yes → Spanner / Aurora Global
    │   └─ No  → 高性能が必要？
    │       ├─ Yes → Aurora / AlloyDB
    │       └─ No  → RDS / Cloud SQL
    └─ No  → どんなデータモデル？
        ├─ Key-Value / Document → DynamoDB / Firestore
        ├─ ワイドカラム(大規模書き込み) → Bigtable / Keyspaces
        ├─ グラフ → Neptune / Neo4j
        ├─ 時系列 → Timestream / InfluxDB
        └─ インメモリ → ElastiCache / MemoryDB / Memorystore
    """)

    question("DynamoDB と RDS の使い分けで最も重要な判断基準は？"
             " → アクセスパターンが事前に決まっているかどうか。"
             "DynamoDB はパーティションキーベースの限定的クエリは超速いが、"
             "アドホックな JOIN は不可能")

    task("DynamoDB テーブルを設計し、GSI を使って"
         "「ユーザーIDで取得」と「日付で範囲検索」の両方を実現してみよう")

    # ================================================================
    # 4. メッセージング・ストリーミング ★重点セクション
    # ================================================================
    section("4. メッセージング・ストリーミング (Messaging & Streaming) ★")

    print("""
  ★ ユーザーが最も知りたいセクション ★

  メッセージングは「通信パターン」で分類する:

  1. Queue (1対1, 非同期):  SQS / Cloud Tasks
  2. Pub/Sub (1対多, ファンアウト): SNS / Pub/Sub
  3. Event Bus (ルーティング): EventBridge
  4. Stream (時系列, リプレイ可): Kinesis / Kafka / Pub/Sub
  5. Delivery Stream (ストリーム→蓄積): Firehose / Dataflow
    """)

    subsection("AWS メッセージング")

    svc("Amazon SQS (Simple Queue Service)",
        "フルマネージドメッセージキュー。Producer → Queue → Consumer の1対1通信",
        "マイクロサービス間の非同期通信 / ワーカーへのジョブ配信 / "
        "バーストトラフィックの平準化 / 処理失敗時のリトライ(DLQ)",
        "1つのメッセージを複数Consumerに配信 → SNS / "
        "メッセージの順序保証 + 重複排除が不要なら Standard で十分",
        "リクエスト数($0.40/100万req)。メッセージサイズ最大256KB",
        "GCP: Cloud Tasks (タスクキュー) / OSS: RabbitMQ, Redis Queue")

    print("""
    SQS Standard vs FIFO:
    ┌─────────────┬─────────────────┬──────────────────────┐
    │             │ Standard        │ FIFO                 │
    ├─────────────┼─────────────────┼──────────────────────┤
    │ 順序        │ ベストエフォート │ 厳密な FIFO           │
    │ 配信        │ 最低1回(重複有) │ 正確に1回             │
    │ スループット │ ほぼ無制限      │ 300 msg/s (バッチ3000)│
    │ ユースケース │ 大量ジョブ配信  │ 決済処理、注文処理     │
    └─────────────┴─────────────────┴──────────────────────┘
    """)

    svc("Amazon SNS (Simple Notification Service)",
        "Pub/Sub メッセージング。1つのメッセージを複数サブスクライバーに配信",
        "ファンアウト(1→多) / SQS + SNS でファンアウトキュー / "
        "メール・SMS 通知 / Lambda トリガー",
        "1対1のキュー → SQS / 複雑なルーティング → EventBridge",
        "パブリッシュ数 + 配信数。SNS→SQS は無料",
        "GCP: Pub/Sub / OSS: Redis Pub/Sub, NATS")

    svc("Amazon EventBridge",
        "サーバーレスイベントバス。ルールベースでイベントをルーティング",
        "SaaS 連携(Shopify,Zendesk等) / AWS サービス間イベント / "
        "イベント内容によるフィルタリング / Schema Registry",
        "超高スループット → Kinesis / シンプルなファンアウト → SNS で十分",
        "イベント数 ($1/100万イベント)",
        "GCP: Eventarc / OSS: なし (独自性が高い)")

    print("""
    ★ SNS vs EventBridge:
    - SNS: シンプルなファンアウト。フィルタリングは属性ベースのみ
    - EventBridge: イベントの中身(JSON)でルーティング可能
    - 例: {"status": "FAILED"} のときだけ Lambda を起動 → EventBridge
    - 例: 全注文を3つの SQS に配信 → SNS
    """)

    svc("Amazon Kinesis Data Streams",
        "リアルタイムストリーミング。順序保証あり・複数Consumer・リプレイ可能",
        "リアルタイムログ集約 / クリックストリーム分析 / IoT センサーデータ / "
        "リアルタイムダッシュボード / 機械学習の特徴量計算",
        "非同期ジョブキュー → SQS / 単純な通知 → SNS",
        "シャード時間($0.015/h) + PUT レコード数。オンデマンドモードあり",
        "GCP: Pub/Sub / OSS: Apache Kafka")

    svc("Amazon Data Firehose (旧 Kinesis Data Firehose) ★",
        "ストリーミングデータを S3, Redshift, OpenSearch 等に自動配信。"
        "バッファリング・変換・圧縮を自動実行",
        "ログを S3 に集約 / ストリーミングデータの ETL / "
        "Kinesis Data Streams → S3 への橋渡し / リアルタイムデータの永続化",
        "データの Consumer を自分で書きたい → Kinesis Data Streams / "
        "複雑な変換 → Glue or Lambda で処理してから配信",
        "取り込みデータ量 (GB単位: $0.029/GB)",
        "GCP: Pub/Sub → Dataflow → GCS / OSS: Kafka Connect + S3 Sink")

    print("""
    ★ Kinesis Data Streams vs Data Firehose:
    ┌──────────────────┬──────────────────┬──────────────────┐
    │                  │ Data Streams     │ Data Firehose    │
    ├──────────────────┼──────────────────┼──────────────────┤
    │ 目的             │ リアルタイム処理  │ データ配信(蓄積)  │
    │ Consumer         │ 自分で書く       │ 自動(S3/Redshift)│
    │ レイテンシ       │ 200ms〜          │ 60秒〜(バッファ)  │
    │ リプレイ         │ 可(最大365日)    │ 不可             │
    │ 変換             │ Consumer 側      │ Lambda で可      │
    │ スケーリング     │ シャード管理     │ 自動             │
    │ 典型的利用法     │ リアルタイム分析  │ ログ → S3 集約   │
    └──────────────────┴──────────────────┴──────────────────┘

    よくある組み合わせ:
    Kinesis Data Streams → Firehose → S3 (リアルタイム処理 + 永続化)
    """)

    svc("Amazon MSK (Managed Streaming for Apache Kafka)",
        "マネージド Apache Kafka。Kafka API 完全互換",
        "既存 Kafka アプリの移行 / Kafka Connect エコシステム活用 / "
        "超高スループット / マルチ Consumer の複雑なストリーム処理",
        "Kafka の運用知識がない → Kinesis のほうが楽 / "
        "シンプルなストリーミング → Kinesis で十分",
        "ブローカー時間 + ストレージ。MSK Serverless もあり",
        "GCP: Pub/Sub (Kafka互換ではない) / OSS: Apache Kafka")

    svc("Amazon MQ",
        "マネージド ActiveMQ / RabbitMQ。JMS/AMQP/MQTT 等の標準プロトコル",
        "既存 MQ アプリの移行 / JMS 互換が必須 / MQTT (IoT)",
        "新規なら SQS + SNS のほうが安くてスケーラブル",
        "ブローカー時間 + ストレージ",
        "GCP: なし / OSS: RabbitMQ, ActiveMQ")

    subsection("AWS イベント系サービス")

    svc("S3 Event Notifications",
        "S3 バケットの操作(PUT/DELETE等)をトリガーにイベント発火",
        "ファイルアップロード → Lambda で処理 / 画像アップ → サムネイル生成",
        "複雑なイベントルーティング → EventBridge + S3 の組合せ",
        "S3 Event 自体は無料。送信先(Lambda/SQS/SNS)の料金のみ",
        "GCP: GCS Notifications (Pub/Sub 経由)")

    svc("EventBridge Pipes",
        "ソース→フィルタ→変換→ターゲットのパイプラインを宣言的に構築",
        "DynamoDB Streams → 変換 → SQS / Kinesis → フィルタ → Lambda",
        "複雑なオーケストレーション → Step Functions",
        "呼び出し回数課金",
        "GCP: なし")

    svc("EventBridge Scheduler",
        "cron/rate 式でイベントを定期実行。200万以上のスケジュール対応",
        "定期バッチ起動 / 将来の予約実行 / Lambda の定期呼び出し",
        "CloudWatch Events (旧) でも可能だが Scheduler のほうが高機能",
        "スケジュール呼び出し数課金",
        "GCP: Cloud Scheduler")

    subsection("GCP メッセージング")

    svc("Cloud Pub/Sub",
        "フルマネージド Pub/Sub + ストリーミング。AWS の SNS+SQS+Kinesis を兼ねる",
        "イベント配信 / ストリーミング / マイクロサービス間通信 / "
        "BigQuery への直接ストリーミング挿入",
        "厳密な FIFO が必要 → ordering key を使うがスループット制限あり",
        "メッセージ量(最初の10GB/月無料) + 配信数",
        "AWS: SNS + SQS (ファンアウト) / Kinesis (ストリーミング)")

    svc("Cloud Tasks",
        "HTTP ターゲットへの非同期タスクキュー。リトライ・レート制限付き",
        "Cloud Run / App Engine へのジョブ配信 / 外部 API 呼び出しのレート制限",
        "Pub/Sub 的なファンアウト → Pub/Sub を使う",
        "オペレーション数($0.40/100万)",
        "AWS: SQS + Lambda")

    svc("Dataflow",
        "Apache Beam ベースのストリーム/バッチデータ処理",
        "ETL パイプライン / リアルタイムストリーム処理 / Pub/Sub → BigQuery",
        "シンプルな配信だけなら Pub/Sub の BigQuery サブスクリプションで十分",
        "ワーカーの vCPU/メモリ/ストレージ時間課金",
        "AWS: Kinesis Data Analytics, Glue Streaming / OSS: Apache Beam, Flink")

    print("""
  ★★★ メッセージングサービス比較表 ★★★

    ┌──────────────┬────────┬─────────┬────────┬────────┬────────┐
    │              │ SQS    │ SNS     │ EventBr│ Kinesis│ Kafka  │
    ├──────────────┼────────┼─────────┼────────┼────────┼────────┤
    │ パターン     │ Queue  │ Pub/Sub │ Bus    │ Stream │ Stream │
    │ 1対1 / 1対多 │ 1対1   │ 1対多   │ 1対多  │ 1対多  │ 1対多  │
    │ 順序保証     │ FIFO可 │ FIFO可  │ なし   │ シャード│ パーティ│
    │ リプレイ     │ 不可   │ 不可    │ アーカイ│ 可     │ 可     │
    │ レイテンシ   │ ms     │ ms      │ ms     │ 200ms  │ ms     │
    │ スループット │ 高     │ 高      │ 中     │ シャード│ 超高   │
    │ 運用コスト   │ 低     │ 低      │ 低     │ 中     │ 高     │
    │ 消費後削除   │ Yes    │ N/A     │ N/A    │ No     │ No     │
    └──────────────┴────────┴─────────┴────────┴────────┴────────┘
    """)

    print("""
  ■ メッセージング Decision Tree:

    何がしたい？
    ├─ ジョブを1つのWorkerに配信したい
    │   └→ SQS / Cloud Tasks
    ├─ 1つのイベントを複数サービスに配信したい
    │   ├─ 内容ベースのフィルタリングが必要？
    │   │   ├─ Yes → EventBridge
    │   │   └─ No  → SNS (+ SQS でファンアウトキュー)
    │   └─ GCP なら → Pub/Sub
    ├─ ストリーミングデータをリアルタイム処理したい
    │   ├─ 自分で Consumer を書く？
    │   │   ├─ Yes → Kinesis Data Streams / Kafka / Pub/Sub
    │   │   └─ No  → Data Firehose (自動で S3/Redshift へ)
    │   └─ Kafka エコシステムが必要？
    │       ├─ Yes → MSK
    │       └─ No  → Kinesis (運用が楽)
    ├─ DB の変更を検知して処理したい
    │   └→ DynamoDB Streams / Debezium (RDS) / Firestore リスナー
    └─ ファイルアップロードをトリガーにしたい
        └→ S3 Event Notifications / GCS → Pub/Sub
    """)

    question("SQS + SNS のファンアウトパターンはなぜ EventBridge より"
             "よく使われるのか？ → 歴史が長くスループットが高い、"
             "EventBridge は比較的新しく上限が低い場合がある")

    task("SQS キューと Lambda を接続し、メッセージ処理失敗時に "
         "DLQ (Dead Letter Queue) にメッセージを退避するシステムを構築してみよう")

    # ================================================================
    # 5. データ分析・ETL
    # ================================================================
    section("5. データ分析・ETL (Analytics)")

    subsection("AWS データ分析")

    svc("AWS Glue",
        "サーバーレス ETL + データカタログ。Spark ベースの変換処理",
        "S3 上のデータの ETL / データカタログ(テーブル定義管理) / "
        "Athena や Redshift のメタデータ管理 / クロール自動スキーマ検出",
        "シンプルな変換 → Athena の CTAS で十分 / リアルタイム → Kinesis",
        "DPU 時間($0.44/DPU/h)。Crawler 実行時間",
        "GCP: Dataflow + Data Catalog / OSS: Apache Spark, dbt")

    svc("Amazon Athena",
        "S3 上のデータに SQL クエリ。サーバーレス・スキャン量課金",
        "アドホック分析 / ログ解析 / データレイクの SQL インターフェース / "
        "Glue Data Catalog と連携してスキーマ管理",
        "低レイテンシが必要な OLTP → RDS / 大量定常クエリ → Redshift のほうが安い",
        "スキャンデータ量($5/TB)。Parquet/ORC で圧縮すれば大幅削減",
        "GCP: BigQuery / OSS: Presto, Trino")

    svc("Amazon Redshift",
        "マネージドデータウェアハウス。列指向圧縮・MPP アーキテクチャ",
        "大規模 BI / 定常的な集計クエリ / ペタバイト規模の分析",
        "アドホックな小規模分析 → Athena のほうが安い / リアルタイム → 不向き",
        "ノード時間(dc2/ra3)。Serverless は RPU 課金",
        "GCP: BigQuery / OSS: ClickHouse, Apache Druid")

    svc("Amazon EMR",
        "マネージド Hadoop/Spark/Hive/Presto クラスタ",
        "大規模データ処理(Spark) / 既存 Hadoop ワークロード移行 / ML 学習",
        "サーバーレスで済む → Athena or Glue / 小規模データ",
        "EC2 インスタンス時間 + EMR 料金。EMR Serverless もあり",
        "GCP: Dataproc / OSS: Apache Spark (自前クラスタ)")

    svc("AWS Lake Formation",
        "データレイクの構築・管理・アクセス制御を一元化",
        "データレイクの権限管理 / 列レベル・行レベルのアクセス制御 / "
        "Glue + S3 + Athena を統合管理",
        "単純な S3 アクセス制御 → IAM ポリシーで十分",
        "Lake Formation 自体は無料。裏のサービスに課金",
        "GCP: Dataplex / OSS: Apache Ranger")

    svc("Amazon OpenSearch Service (旧 Elasticsearch Service)",
        "マネージド OpenSearch/Elasticsearch。全文検索 + ログ分析",
        "アプリケーション検索 / ログ分析 (ELK スタック) / SIEM",
        "単純なログ保存 → S3 + Athena / RDB の検索 → PostgreSQL全文検索",
        "インスタンス時間 + ストレージ。Serverless もあり",
        "GCP: なし (Elastic Cloud) / OSS: OpenSearch, Elasticsearch")

    svc("Amazon QuickSight",
        "マネージド BI ツール。ダッシュボード作成・共有",
        "社内ダッシュボード / 埋め込み分析 / ML 予測(QuickSight Q)",
        "高度なカスタム可視化 → Grafana, Tableau",
        "ユーザー数 × 月額($9〜24/user/月)",
        "GCP: Looker / OSS: Grafana, Metabase, Superset")

    subsection("GCP データ分析")

    svc("BigQuery",
        "サーバーレス DWH + データレイク。スキャン量課金。ML/地理空間も統合",
        "大規模分析 / アドホッククエリ / BI / ML (BigQuery ML) / "
        "ストリーミング挿入(Pub/Sub 直接連携)",
        "低レイテンシ OLTP → Cloud SQL / 小規模なら Sheets で十分",
        "スキャン量($5/TB) or スロット予約(定額)。ストレージ $0.02/GB/月",
        "AWS: Athena + Redshift / OSS: ClickHouse, DuckDB")

    svc("Dataproc",
        "マネージド Spark/Hadoop。EMR 相当",
        "大規模 Spark ジョブ / 既存 Hadoop 移行",
        "サーバーレスで済む → BigQuery or Dataflow",
        "VM 時間 + Dataproc プレミアム",
        "AWS: EMR")

    svc("Looker",
        "BI プラットフォーム。LookML でデータモデリング",
        "エンタープライズ BI / データガバナンス / 埋め込み分析",
        "簡易ダッシュボード → Looker Studio(無料)で十分",
        "ユーザー数ベースのライセンス",
        "AWS: QuickSight / OSS: Metabase, Superset")

    print("""
  ■ データ分析 Decision Tree:

    何がしたい？
    ├─ S3/GCS 上のデータにアドホック SQL
    │   └→ Athena / BigQuery
    ├─ 定常的な大規模集計・BI ダッシュボード
    │   └→ Redshift / BigQuery (スロット予約)
    ├─ ETL (データ変換パイプライン)
    │   ├─ バッチ → Glue / Dataflow (batch) / dbt
    │   └─ ストリーム → Glue Streaming / Dataflow (streaming)
    ├─ 全文検索 / ログ分析
    │   └→ OpenSearch / Elastic Cloud
    ├─ データカタログ(メタデータ管理)
    │   └→ Glue Data Catalog / Data Catalog
    └─ BI ダッシュボード
        └→ QuickSight / Looker / Grafana
    """)

    task("Athena で S3 上の CSV ファイルに SQL クエリを投げるハンズオンを"
         "やってみよう。Parquet 変換前後でスキャン量の差を確認すると面白い")

    # ================================================================
    # 6. AI/ML サービス
    # ================================================================
    section("6. AI/ML サービス")

    subsection("AWS AI/ML")

    svc("Amazon SageMaker",
        "ML のフルライフサイクルプラットフォーム。学習・推論・MLOps 統合",
        "カスタムモデルの学習 / モデルデプロイ(エンドポイント) / "
        "Feature Store / Pipelines / Ground Truth (アノテーション)",
        "既成 AI サービスで済む → Rekognition 等 / LLM を使うだけ → Bedrock",
        "インスタンス時間(学習/推論) + ストレージ + 各機能の個別課金",
        "GCP: Vertex AI / OSS: MLflow, Kubeflow")

    svc("Amazon Bedrock",
        "Foundation Model (Claude, Titan, Llama 等) の API サービス",
        "LLM アプリ開発 / RAG / テキスト生成 / 画像生成 / エンベディング",
        "カスタムモデル学習 → SageMaker / 画像分類 → Rekognition",
        "入出力トークン数課金。モデルにより異なる",
        "GCP: Vertex AI (Gemini API) / OSS: Ollama, vLLM")

    svc("Amazon Rekognition",
        "画像・動画の AI 分析。顔検出、物体検出、テキスト検出",
        "顔認証 / コンテンツモデレーション / 車のナンバープレート認識",
        "カスタム画像分類 → SageMaker or Rekognition Custom Labels",
        "処理画像数/動画時間課金",
        "GCP: Vision AI / OSS: OpenCV + カスタムモデル")

    svc("Amazon Textract",
        "ドキュメントからのテキスト・テーブル・フォーム抽出 (OCR+)",
        "請求書処理 / 身分証明書読み取り / PDF からのデータ抽出",
        "単純 OCR → Tesseract で十分 / 手書き文字多い → 精度要確認",
        "ページ数課金",
        "GCP: Document AI / OSS: Tesseract OCR")

    svc("Amazon Comprehend",
        "自然言語処理。感情分析、エンティティ抽出、トピック分類",
        "カスタマーレビューの感情分析 / PII 検出 / 文書分類",
        "LLM で柔軟に処理可能な場合 → Bedrock のほうが汎用的",
        "処理文字数課金",
        "GCP: Natural Language AI / OSS: spaCy, Hugging Face")

    svc("Amazon Kendra",
        "AI 搭載のエンタープライズ検索。社内ドキュメント検索",
        "社内ナレッジベース検索 / RAG のリトリーバー",
        "シンプルなキーワード検索 → OpenSearch / 公開 Web 検索 → 不向き",
        "インデックス時間 + クエリ数",
        "GCP: Vertex AI Search / OSS: Elasticsearch + ベクトル検索")

    print("""
  ■ AI/ML Decision Tree:

    何がしたい？
    ├─ LLM を使いたい (テキスト生成/チャット/要約)
    │   └→ Bedrock / Vertex AI (Gemini)
    ├─ カスタムモデルを学習したい
    │   └→ SageMaker / Vertex AI
    ├─ 画像/動画分析
    │   ├─ 汎用(顔/物体検出) → Rekognition / Vision AI
    │   └─ カスタム分類 → SageMaker / AutoML
    ├─ ドキュメント処理 (OCR)
    │   └→ Textract / Document AI
    ├─ 自然言語処理
    │   └→ Comprehend / Natural Language AI (or LLM で代替)
    └─ 社内検索
        └→ Kendra / Vertex AI Search
    """)

    subsection("GCP AI/ML")

    svc("Vertex AI",
        "ML プラットフォーム。AutoML + カスタム学習 + Gemini API 統合",
        "カスタムモデル学習 / Gemini API / AutoML / Feature Store",
        "シンプルな推論 API だけなら Cloud Functions + OSS モデルで十分",
        "学習/推論のコンピュート時間 + API 呼び出し",
        "AWS: SageMaker + Bedrock")

    # ================================================================
    # 7. ネットワーク
    # ================================================================
    section("7. ネットワーク (Networking)")

    subsection("AWS ネットワーク")

    svc("Amazon VPC",
        "仮想プライベートネットワーク。サブネット、ルートテーブル、NAT GW 等",
        "全ての AWS リソースのネットワーク基盤。VPC は必須の基礎知識",
        "サーバーレスのみの構成でも VPC は意識が必要(Lambda VPC 接続等)",
        "VPC 自体は無料。NAT GW($0.045/h + $0.045/GB)が高額注意",
        "GCP: VPC")

    svc("Elastic Load Balancing (ALB/NLB/GLB)",
        "ロードバランサー。ALB(L7/HTTP), NLB(L4/TCP), GLB(L3/IP)",
        "ALB: Web API の負荷分散 / NLB: 超低レイテンシ・TCP / GLB: ファイアウォール連携",
        "単一インスタンスなら不要 / CloudFront で済む静的サイト",
        "LCU(ALB) or NLCU(NLB) 時間 + データ処理量",
        "GCP: Cloud Load Balancing")

    svc("Amazon CloudFront",
        "グローバル CDN。S3/ALB/API GW のエッジキャッシュ",
        "静的サイト配信 / API レスポンスキャッシュ / 動画配信 / Lambda@Edge",
        "社内システムのみ → 不要 / キャッシュ不可なデータ",
        "データ転送量 + リクエスト数。無料枠1TB/月",
        "GCP: Cloud CDN / OSS: Cloudflare, nginx")

    svc("Amazon Route 53",
        "マネージド DNS + ヘルスチェック + ルーティングポリシー",
        "ドメイン管理 / フェイルオーバールーティング / 地理的ルーティング",
        "シンプルな DNS → 他のレジストラでも可",
        "ホストゾーン($0.50/月) + クエリ数",
        "GCP: Cloud DNS / OSS: BIND, Cloudflare DNS")

    svc("Amazon API Gateway",
        "マネージド API 管理。REST API / HTTP API / WebSocket API",
        "Lambda の HTTP エンドポイント / API キー管理 / レート制限 / "
        "WebSocket リアルタイム通信",
        "ALB + Fargate で十分な場合(API GW は単価が高い) / "
        "高スループット API → HTTP API (REST API より安い)",
        "REST: $3.50/100万req, HTTP: $1.00/100万req, WebSocket: 接続+メッセージ",
        "GCP: API Gateway, Cloud Endpoints / OSS: Kong, NGINX")

    print("""
    API Gateway REST vs HTTP API:
    ┌────────────────┬───────────────┬──────────────────┐
    │                │ REST API      │ HTTP API         │
    ├────────────────┼───────────────┼──────────────────┤
    │ 料金           │ $3.50/100万   │ $1.00/100万      │
    │ WebSocket      │ 別 (WS API)   │ 非対応           │
    │ キャッシュ     │ あり          │ なし             │
    │ WAF 統合       │ あり          │ なし             │
    │ 使用場面       │ エンプラ API  │ シンプルな API   │
    └────────────────┴───────────────┴──────────────────┘
    → 多くの場合 HTTP API で十分。3.5倍安い。
    """)

    svc("AWS PrivateLink",
        "VPC 内から AWS サービスや他 VPC のサービスにプライベート接続",
        "S3/DynamoDB 等への接続をインターネット経由にしたくない / "
        "SaaS をプライベート接続で利用",
        "パブリックアクセスで問題ない場合",
        "VPC エンドポイント時間 + データ処理量",
        "GCP: Private Service Connect")

    svc("AWS Transit Gateway",
        "複数 VPC とオンプレを中央ハブで接続",
        "数十〜数百の VPC を管理 / マルチアカウント構成",
        "VPC 2-3個なら VPC Peering で十分",
        "アタッチメント時間 + データ処理量",
        "GCP: Network Connectivity Center")

    svc("AWS Global Accelerator",
        "AWS グローバルネットワーク経由でトラフィックを最適ルーティング",
        "グローバルユーザーへの低レイテンシ提供 / TCP/UDP の高速化",
        "HTTP のみなら CloudFront で十分",
        "固定 IP × 時間 + データ転送量プレミアム",
        "GCP: Premium Tier ネットワーク")

    svc("AWS Direct Connect",
        "オンプレミスと AWS を専用線接続",
        "大量データ転送 / レイテンシ要件 / セキュリティ要件",
        "VPN で十分な場合 / コスト的に見合わない小規模",
        "ポート時間 + データ転送量(安い)",
        "GCP: Cloud Interconnect")

    # ================================================================
    # 8. セキュリティ・ID
    # ================================================================
    section("8. セキュリティ・ID (Security & Identity)")

    subsection("AWS セキュリティ")

    svc("AWS IAM",
        "ユーザー・ロール・ポリシーによるアクセス制御。AWS の基盤",
        "全ての AWS 利用で必須。最小権限の原則を徹底",
        "エンドユーザー認証 → Cognito / 外部 IdP → IAM Identity Center",
        "無料",
        "GCP: IAM")

    svc("Amazon Cognito",
        "エンドユーザー認証・認可。User Pool(認証) + Identity Pool(AWS 認可)",
        "Web/モバイルアプリのサインアップ・サインイン / ソーシャルログイン / MFA",
        "社内ユーザー管理 → IAM Identity Center / 単純な API キー認証",
        "MAU 課金(最初50,000 MAU 無料)",
        "GCP: Identity Platform, Firebase Auth / OSS: Keycloak, Auth0")

    svc("AWS Secrets Manager",
        "シークレット(DB パスワード、API キー等)の管理と自動ローテーション",
        "DB パスワード管理 / API キー管理 / 自動ローテーション",
        "暗号化キー管理 → KMS / 設定値(非機密) → Parameter Store(無料)",
        "$0.40/シークレット/月 + API コール数",
        "GCP: Secret Manager / OSS: HashiCorp Vault")

    svc("AWS KMS (Key Management Service)",
        "暗号化キーの作成・管理。S3, EBS, RDS 等の暗号化に使用",
        "保存データの暗号化 / エンベロープ暗号化 / キーローテーション",
        "単純なシークレット保存 → Secrets Manager",
        "キー保管($1/月) + API コール数",
        "GCP: Cloud KMS")

    svc("AWS WAF",
        "Web Application Firewall。SQL Injection, XSS 等を防御",
        "ALB, CloudFront, API Gateway の前段に配置 / Bot 対策 / レート制限",
        "L3/L4 の DDoS 防御 → Shield / ネットワークファイアウォール → Network FW",
        "Web ACL($5/月) + ルール数 + リクエスト数",
        "GCP: Cloud Armor / OSS: ModSecurity")

    svc("Amazon GuardDuty",
        "脅威検出サービス。ML ベースで異常なアクティビティを検出",
        "不正アクセス検出 / マルウェア検知 / 異常な API コール検出",
        "詳細なコンプライアンス管理 → Security Hub と連携",
        "分析データ量課金",
        "GCP: Security Command Center")

    svc("AWS CloudTrail",
        "AWS API コールのログ記録。誰が何をしたかの監査証跡",
        "セキュリティ監査 / コンプライアンス / インシデント調査",
        "管理イベントの90日履歴は無料。それ以上は Trail 設定が必要",
        "管理イベント無料 / データイベント($0.10/10万イベント)",
        "GCP: Cloud Audit Logs")

    svc("AWS Security Hub",
        "セキュリティ状態の一元管理。GuardDuty, Inspector 等を統合",
        "セキュリティ全体のダッシュボード / CIS ベンチマーク自動チェック",
        "小規模で個別サービスの監視で十分な場合",
        "セキュリティチェック数課金",
        "GCP: Security Command Center")

    svc("Amazon Inspector",
        "EC2, Lambda, ECR イメージの脆弱性スキャン",
        "OS/パッケージの CVE スキャン / コンテナイメージスキャン",
        "アプリケーションレベルの脆弱性 → DAST ツール(OWASP ZAP等)",
        "スキャン対象数課金",
        "GCP: Artifact Analysis / OSS: Trivy, Grype")

    svc("Amazon Macie",
        "S3 内の機密データ(PII等)を ML で自動検出",
        "個人情報の検出 / GDPR 対応 / データ分類",
        "構造化データの PII → Comprehend PII 検出のほうが安い場合",
        "S3 バケット評価 + データスキャン量",
        "GCP: DLP (Data Loss Prevention)")

    # ================================================================
    # 9. 監視・運用
    # ================================================================
    section("9. 監視・運用 (Monitoring & Operations)")

    subsection("AWS 監視・運用")

    svc("Amazon CloudWatch",
        "AWS の統合モニタリング。Metrics, Logs, Alarms, Dashboards, Synthetics",
        "全 AWS リソースのメトリクス監視 / ログ集約 / アラート通知 / "
        "カスタムメトリクス / Synthetics(外形監視)",
        "高度なログ分析 → OpenSearch / 分散トレーシング → X-Ray",
        "メトリクス数 + ログ取り込み($0.50/GB) + Alarm 数 + Dashboard",
        "GCP: Cloud Monitoring + Cloud Logging / OSS: Prometheus + Grafana")

    svc("AWS X-Ray",
        "分散トレーシング。マイクロサービスのリクエストフローを可視化",
        "マイクロサービスのボトルネック特定 / エラー原因追跡 / レイテンシ分析",
        "単純なメトリクス → CloudWatch / ログ分析 → CloudWatch Logs Insights",
        "トレース記録数 + スキャン数",
        "GCP: Cloud Trace / OSS: Jaeger, Zipkin, OpenTelemetry")

    svc("AWS Systems Manager",
        "EC2 インスタンスの運用管理。パッチ適用, Run Command, Parameter Store",
        "EC2 フリートの一括管理 / SSM Session Manager(SSH不要接続) / "
        "Parameter Store(設定値管理, 無料枠あり)",
        "コンテナ/サーバーレスのみの環境ではほぼ不要",
        "一部無料。Advanced Parameter Store, OpsCenter 等は有料",
        "GCP: OS Config / OSS: Ansible, Chef")

    svc("AWS CloudFormation",
        "AWS の IaC (Infrastructure as Code)。YAML/JSON でリソース定義",
        "AWS リソースのコード管理 / スタック単位のデプロイ/ロールバック",
        "マルチクラウド → Terraform / プログラマブルに書きたい → CDK",
        "無料(管理するリソースに課金)",
        "GCP: Deployment Manager / OSS: Terraform, Pulumi")

    svc("AWS CDK (Cloud Development Kit)",
        "TypeScript/Python/Java 等でインフラをコード定義。CloudFormation 生成",
        "プログラマブルにインフラを定義したい / 再利用可能なコンストラクト",
        "既存チームが Terraform 運用している場合 → 移行コストを考慮",
        "無料(CloudFormation + リソースに課金)",
        "GCP: Pulumi / OSS: Terraform CDK, Pulumi")

    svc("AWS Config",
        "AWS リソースの設定変更履歴と準拠ルールの評価",
        "コンプライアンス監査 / 設定変更の追跡 / 自動修復",
        "単純な変更ログ → CloudTrail で十分",
        "記録項目数 + ルール評価数",
        "GCP: Cloud Asset Inventory")

    subsection("GCP 監視・運用")

    svc("Cloud Monitoring",
        "GCP の統合モニタリング。メトリクス, ダッシュボード, アラート",
        "GCP リソース監視 / カスタムメトリクス / アラートポリシー",
        "ログ分析 → Cloud Logging / トレーシング → Cloud Trace",
        "カスタムメトリクス数 + API コール",
        "AWS: CloudWatch")

    svc("Cloud Logging",
        "ログ管理。ルーティング, フィルタリング, BigQuery エクスポート",
        "GCP リソースのログ集約 / 監査ログ / ログベースメトリクス",
        "長期保存分析 → BigQuery へエクスポート",
        "取り込み量(最初50GB/月無料) + 保持期間",
        "AWS: CloudWatch Logs")

    # ================================================================
    # 10. コンテナ・サーバーレス補助
    # ================================================================
    section("10. コンテナ・サーバーレス補助")

    svc("Amazon ECR (Elastic Container Registry)",
        "マネージド Docker コンテナレジストリ",
        "ECS/EKS/Lambda のコンテナイメージ保管 / 脆弱性スキャン",
        "パブリックイメージの配信 → Docker Hub / GitHub Container Registry",
        "ストレージ($0.10/GB/月) + データ転送量",
        "GCP: Artifact Registry / OSS: Harbor")

    svc("AWS Step Functions",
        "サーバーレスワークフローオーケストレーション。ステートマシンで定義",
        "複数 Lambda の連携 / 承認フロー / エラーハンドリング付きパイプライン / "
        "並列実行 / 条件分岐 / Saga パターン",
        "単純な Lambda チェーン → Lambda 内で直接呼び出し / "
        "大量データ処理 → Glue or EMR",
        "Standard: 状態遷移数($0.025/1000), Express: 実行数+時間",
        "GCP: Cloud Workflows / OSS: Apache Airflow, Temporal")

    print("""
    Step Functions Standard vs Express:
    ┌────────────────┬───────────────┬──────────────────┐
    │                │ Standard      │ Express          │
    ├────────────────┼───────────────┼──────────────────┤
    │ 実行時間上限   │ 1年           │ 5分              │
    │ 実行保証       │ 正確に1回     │ 最低1回          │
    │ 料金           │ 状態遷移課金  │ 実行数+時間      │
    │ ユースケース   │ 長時間ワークフ │ 高頻度短時間処理 │
    └────────────────┴───────────────┴──────────────────┘
    """)

    svc("AWS App Mesh",
        "マネージド Envoy ベースのサービスメッシュ",
        "ECS/EKS のサービス間通信制御 / mTLS / トラフィック制御",
        "小規模 → 不要。サービスメッシュはオーバーヘッド大きい",
        "無料(Envoy の EC2/Fargate リソースに課金)",
        "GCP: Anthos Service Mesh / OSS: Istio, Linkerd")

    svc("AWS Cloud Map",
        "サービスディスカバリ。ECS/EKS のサービス登録と DNS 検出",
        "マイクロサービスのサービス検出 / ECS Service Connect の裏側",
        "K8s の Service で十分な場合 / 単純な ALB ルーティング",
        "リソース登録数 + DNS クエリ数",
        "GCP: Service Directory")

    svc("GCP Cloud Workflows",
        "サーバーレスワークフロー。YAML で定義。Step Functions 相当",
        "Cloud Functions/Run の連携 / API コール連鎖 / 条件分岐",
        "大規模データ処理 → Dataflow / 複雑な ML パイプライン → Vertex AI Pipelines",
        "ステップ数課金",
        "AWS: Step Functions")

    svc("GCP Artifact Registry",
        "コンテナイメージ + 言語パッケージ(Maven, npm, Python)のレジストリ",
        "GKE/Cloud Run のイメージ保管 / npm/Python パッケージの社内レジストリ",
        "パブリック配信 → Docker Hub",
        "ストレージ + データ転送量",
        "AWS: ECR / OSS: Harbor, Nexus")

    # ================================================================
    # 11. 設計パターン別サービス組み合わせ ★最重要
    # ================================================================
    section("11. 設計パターン別サービス組み合わせ ★最重要セクション")

    print("""
  実際のシステムは複数のサービスを組み合わせて構築する。
  ここでは頻出パターンを ASCII アーキテクチャ図付きで解説する。
    """)

    # Pattern 1: Web API
    subsection("Pattern 1: Web API (コンテナベース)")

    diagram([
        "Client",
        "  │",
        "  ▼",
        "Route53 (DNS)",
        "  │",
        "  ▼",
        "CloudFront (CDN/WAF)",
        "  │",
        "  ▼",
        "ALB (Load Balancer)",
        "  │",
        "  ├──▶ ECS/Fargate (API サーバー) ─┬──▶ Aurora (OLTP)",
        "  ├──▶ ECS/Fargate (API サーバー) ─┤",
        "  └──▶ ECS/Fargate (API サーバー) ─┘──▶ ElastiCache (キャッシュ)",
    ])

    print("""
    サービス選定理由:
    - ALB: HTTP/HTTPS の負荷分散。パスベースルーティング可能
    - ECS + Fargate: EC2 管理不要。オートスケーリング
    - Aurora: RDS より高性能。リードレプリカで読み取りスケール
    - ElastiCache: DB 負荷軽減。セッション管理にも使用
    - CloudFront: 静的アセットのキャッシュ + WAF 統合
    - GCP 版: Cloud Run + Cloud SQL + Memorystore + Cloud CDN
    """)

    # Pattern 2: イベント駆動
    subsection("Pattern 2: イベント駆動 (サーバーレス)")

    diagram([
        "Client",
        "  │",
        "  ▼",
        "API Gateway (HTTP API)",
        "  │",
        "  ▼",
        "Lambda (受付処理)",
        "  │",
        "  ├──▶ SQS (注文キュー) ──▶ Lambda (処理Worker)",
        "  │                              │",
        "  │                              ├──▶ DynamoDB (注文データ)",
        "  │                              └──▶ SNS (通知)",
        "  │                                    │",
        "  │                                    ├──▶ SQS (メール通知)",
        "  │                                    ├──▶ SQS (Push通知)",
        "  │                                    └──▶ Lambda (在庫更新)",
        "  │",
        "  └──▶ DynamoDB (べき等性チェック用)",
    ])

    print("""
    サービス選定理由:
    - API Gateway HTTP API: REST API より安い。Lambda 統合が簡単
    - SQS: ジョブキューでバーストを平準化。DLQ で失敗処理を保証
    - SNS → SQS: ファンアウトパターン。注文完了を複数サービスに通知
    - DynamoDB: 高速な Key-Value アクセス。TTL でべき等性キーを自動削除
    - GCP 版: Cloud Run + Pub/Sub + Firestore
    """)

    # Pattern 3: リアルタイムストリーミング
    subsection("Pattern 3: リアルタイムストリーミング")

    diagram([
        "IoT デバイス / アプリ",
        "  │",
        "  ▼",
        "Kinesis Data Streams (リアルタイム取り込み)",
        "  │",
        "  ├──▶ Lambda (リアルタイムアラート)",
        "  │      └──▶ SNS → メール/Slack通知",
        "  │",
        "  ├──▶ Kinesis Data Analytics (ストリーム集計)",
        "  │      └──▶ DynamoDB (リアルタイムダッシュボード用)",
        "  │",
        "  └──▶ Data Firehose ★",
        "         │",
        "         ├──▶ S3 (データレイク, Parquet 変換)",
        "         │     └──▶ Athena (アドホック分析)",
        "         │",
        "         └──▶ OpenSearch (ログ検索/可視化)",
    ])

    print("""
    サービス選定理由:
    - Kinesis Data Streams: 順序保証ありのストリーム。リプレイ可能
    - Data Firehose ★: Consumer を書かずに S3 へ自動配信。バッファリング・
      圧縮・Parquet 変換も自動。運用負荷が最も低い
    - Lambda: シャードごとに Consumer を自動実行
    - OpenSearch: Kibana でログの可視化・検索
    - GCP 版: Pub/Sub → Dataflow → BigQuery + GCS
    """)

    question("Firehose のバッファリング間隔(60秒〜900秒)を短くすると"
             "何が起きる？ → S3 に小さなファイルが大量に生成される。"
             "後続の Athena クエリが遅くなるため、適切なバッファサイズが重要")

    # Pattern 4: ML パイプライン
    subsection("Pattern 4: ML パイプライン")

    diagram([
        "データソース",
        "  │",
        "  ▼",
        "S3 (Raw Data)",
        "  │",
        "  ▼",
        "Glue ETL (前処理・特徴量エンジニアリング)",
        "  │",
        "  ▼",
        "SageMaker",
        "  ├──▶ Processing Job (データ加工)",
        "  ├──▶ Training Job (モデル学習)",
        "  ├──▶ Model Registry (モデル管理)",
        "  └──▶ Endpoint (推論 API)",
        "         │",
        "         ▼",
        "API Gateway → Lambda → SageMaker Endpoint",
        "                          │",
        "                          ▼",
        "                       Client",
    ])

    print("""
    サービス選定理由:
    - S3: 学習データの一元管理。バージョニングでデータ管理
    - Glue: サーバーレス ETL。Spark ベースで大規模データ処理
    - SageMaker: 学習→デプロイの一気通貫。A/B テストも可能
    - API Gateway + Lambda: 推論 API のサーバーレス公開
    - GCP 版: GCS → Dataflow → Vertex AI → Cloud Run
    """)

    # Pattern 5: マイクロサービス
    subsection("Pattern 5: マイクロサービス")

    diagram([
        "Client",
        "  │",
        "  ▼",
        "API Gateway",
        "  │",
        "  ▼",
        "EKS (Kubernetes)",
        "  ├──▶ User Service ─────▶ Aurora (users)",
        "  ├──▶ Order Service ────▶ DynamoDB (orders)",
        "  ├──▶ Payment Service ──▶ Aurora (payments)",
        "  └──▶ Notification Svc ─▶ SES (email)",
        "         │",
        "    EventBridge (イベントバス)",
        "    ┌────┼──────────┐",
        "    ▼    ▼          ▼",
        "  Order  Payment  Inventory",
        "  SQS    SQS      SQS",
    ])

    print("""
    サービス選定理由:
    - EKS: マイクロサービスのデプロイ・スケーリング。Istio でサービスメッシュ
    - EventBridge: サービス間の疎結合イベント通信。内容ベースルーティング
    - SQS: 各サービスの入力キュー。バックプレッシャー + DLQ
    - 各 DB をサービスごとに分離: Database per Service パターン
    - GCP 版: GKE + Pub/Sub + 各種 DB
    """)

    # Pattern 6: データレイク
    subsection("Pattern 6: データレイク")

    diagram([
        "データソース",
        "  ├──▶ アプリ DB (RDS) ──▶ DMS ──┐",
        "  ├──▶ ログ (CloudWatch) ────────┤",
        "  ├──▶ IoT (Kinesis → Firehose) ─┤",
        "  └──▶ SaaS (API → Lambda) ──────┘",
        "                                   │",
        "                                   ▼",
        "                          S3 (Data Lake)",
        "                      ┌────┼────────────┐",
        "                      │    │             │",
        "                Raw Zone  Curated Zone  Aggregated",
        "                      │    │             │",
        "                      ▼    ▼             ▼",
        "              Glue Crawler  Glue ETL     Redshift",
        "                      │    │             │",
        "                      ▼    ▼             ▼",
        "              Glue Data Catalog     QuickSight",
        "                      │",
        "                      ▼",
        "               Athena (SQL)",
        "                      │",
        "                 Lake Formation (権限管理)",
    ])

    print("""
    サービス選定理由:
    - S3: データレイクのストレージ基盤。ゾーン分け(Raw/Curated/Aggregated)
    - Glue: ETL + メタデータ管理(Data Catalog)。Crawler で自動スキーマ検出
    - Athena: S3 上のデータに直接 SQL。Parquet 形式で高速化
    - Lake Formation: 列/行レベルのアクセス制御。データガバナンス
    - Redshift: 大量定常クエリ用の DWH
    - GCP 版: GCS + Dataflow + BigQuery + Data Catalog + Looker
    """)

    # Pattern 7: サーバーレス Web
    subsection("Pattern 7: サーバーレス Web アプリ")

    diagram([
        "Browser",
        "  │",
        "  ▼",
        "CloudFront (CDN)",
        "  ├──▶ S3 (React SPA: HTML/JS/CSS)",
        "  │",
        "  └──▶ API Gateway (HTTP API)",
        "         │",
        "         ├──▶ Lambda (CRUD API)",
        "         │      └──▶ DynamoDB",
        "         │",
        "         └──▶ Lambda (認証)",
        "                └──▶ Cognito User Pool",
        "",
        "  + CloudWatch (ログ・メトリクス)",
        "  + WAF (セキュリティ)",
        "  + Route53 (カスタムドメイン)",
        "  + ACM (SSL証明書, 無料)",
    ])

    print("""
    サービス選定理由:
    - CloudFront + S3: SPA の静的ホスティング。グローバル配信
    - API Gateway HTTP API: Lambda との統合が最も安い
    - Lambda: API サーバー不要。コールドスタートは Provisioned Concurrency で対策
    - DynamoDB: サーバーレスと相性抜群。オンデマンド課金でゼロスケール
    - Cognito: 認証機能をフルマネージド化。JWT トークン発行
    - 月額: 小規模なら数ドル〜。アクセス増加に応じて線形スケール
    - GCP 版: Cloud CDN + GCS + Cloud Run + Firestore + Identity Platform
    """)

    task("Pattern 7 のサーバーレス Web アプリを AWS CDK (TypeScript) で "
         "デプロイしてみよう。CloudFront + S3 + API Gateway + Lambda + DynamoDB を "
         "1つのスタックで構築できる")

    # ================================================================
    # 12. 面接問題
    # ================================================================
    section("12. 面接問題 (System Design Interview)")

    subsection("問題1: 1000万ユーザー向けリアルタイム通知システム")

    print("""
  ■ 要件:
    - 1000万ユーザーにリアルタイム通知(プッシュ、メール、アプリ内)
    - 通知の優先度(即時 / バッチ)
    - 配信保証(少なくとも1回)
    - 通知の既読管理

  ■ 推奨アーキテクチャ:
    """)

    diagram([
        "イベントソース (注文完了, メンション等)",
        "  │",
        "  ▼",
        "EventBridge (ルーティング)",
        "  │",
        "  ├─[即時]──▶ SNS → SQS (優先度別キュー)",
        "  │              │",
        "  │              ├──▶ Lambda (Push通知) ──▶ SNS Mobile Push / FCM",
        "  │              ├──▶ Lambda (メール)   ──▶ SES",
        "  │              └──▶ Lambda (アプリ内) ──▶ DynamoDB + WebSocket",
        "  │",
        "  └─[バッチ]──▶ SQS (バッチキュー)",
        "                  └──▶ Lambda (まとめ通知) ──▶ SES",
        "",
        "  WebSocket接続管理:",
        "  API Gateway WebSocket ──▶ Lambda ──▶ DynamoDB (接続ID管理)",
    ])

    print("""
    サービス選定理由:
    - EventBridge: 通知タイプごとにルーティング。ルールで優先度判定
    - SNS → SQS: ファンアウトで配信チャネル(Push/メール/アプリ内)に分散
    - SQS: DLQ で配信失敗を保証。バックプレッシャーで過負荷防止
    - DynamoDB: 通知の永続化 + 既読管理。TTL で古い通知を自動削除
    - API Gateway WebSocket: リアルタイムのアプリ内通知配信
    - SES: 大量メール配信。バウンス管理

    スケーラビリティのポイント:
    - SQS のキューを優先度別に分けて処理速度を制御
    - Lambda の同時実行数を Reserved Concurrency で制御
    - DynamoDB のオンデマンドモードでスパイクに対応
    - CloudFront + S3 で通知画像等の配信をオフロード
    """)

    subsection("問題2: ペタバイト規模のデータレイク分析基盤")

    print("""
  ■ 要件:
    - 複数のデータソース(RDS, ログ, API, IoT)を統合
    - ペタバイト規模のデータ保存
    - BI ダッシュボード + アドホック分析
    - データガバナンス(アクセス制御、データ品質)
    - コスト最適化

  ■ 推奨アーキテクチャ:
    """)

    diagram([
        "━━━ データ取り込み ━━━",
        "RDS ──▶ DMS (CDC) ──────────────┐",
        "ログ ──▶ Firehose ─────────────┤",
        "API ──▶ Lambda → Step Functions ┤",
        "IoT ──▶ Kinesis Data Streams ──┤",
        "                                │",
        "━━━ ストレージ ━━━              ▼",
        "              S3 Data Lake (ゾーン分け)",
        "         ┌────────┼────────────┐",
        "      Raw Zone  Curated Zone  Gold Zone",
        "      (JSON/CSV) (Parquet)    (集計済み)",
        "         │          │            │",
        "━━━ 処理 ━━━       │            │",
        "  Glue ETL ────────┘            │",
        "  EMR (Spark) ──────────────────┘",
        "",
        "━━━ 分析 ━━━",
        "  Athena (アドホック SQL) ──┐",
        "  Redshift (定常 BI) ──────┤──▶ QuickSight",
        "  SageMaker (ML) ──────────┘",
        "",
        "━━━ ガバナンス ━━━",
        "  Lake Formation (権限) + Glue Data Catalog (メタデータ)",
        "  + Macie (PII検出) + CloudTrail (監査)",
    ])

    print("""
    サービス選定理由:
    - DMS: RDS からの CDC (変更データキャプチャ) で差分取り込み
    - Firehose: ログのバッファリング → S3 配信を自動化
    - S3 ゾーン分け: Raw → Curated → Gold で段階的にデータ品質向上
    - Glue ETL: Spark ベースの変換。Data Catalog でメタデータ一元管理
    - Athena: アドホック分析。Parquet + パーティション分割でコスト削減
    - Redshift: 定常的な BI クエリ。RA3 ノードで S3 ストレージ分離
    - Lake Formation: テーブル/列/行レベルの細かいアクセス制御

    コスト最適化のポイント:
    - S3 Intelligent-Tiering で自動的にストレージクラス最適化
    - Athena: Parquet 変換で90%以上スキャン量削減
    - Redshift Serverless: 使わない時間は課金ゼロ
    - EMR Spot インスタンスで学習コスト削減
    - Firehose で Parquet 直接出力 → ETL ステップ削減
    """)

    question("データレイクで Raw Zone を残す理由は？ → データの再処理が可能。"
             "ETL ロジックにバグがあった場合、Raw から再変換できる。"
             "GDPR の Right to Erasure 対応にも Raw Zone の管理が必要")

    # ================================================================
    # まとめ
    # ================================================================
    section("まとめ: サービス選択の判断フレームワーク")

    print("""
  ■ サービス選択の5つの軸:

    1. マネージド度: フルマネージド → サーバーレス → コンテナ → VM
       ・運用チームの規模に応じて選択
       ・小さいチーム → フルマネージド寄り

    2. スケーラビリティ: 自動スケール vs 手動プロビジョニング
       ・DynamoDB オンデマンド、Lambda → 自動
       ・RDS, ElastiCache → 手動(リードレプリカ追加等)

    3. コストモデル: 従量課金 vs 予約 vs 固定
       ・初期は従量課金で始め、安定したら予約に切り替え
       ・Lambda は小規模なら安いが大規模だと Fargate のほうが安い

    4. ロックイン度: AWS 固有 vs OSS 互換 vs マルチクラウド
       ・DynamoDB: AWS 固有(ロックイン高)
       ・EKS: K8s 互換(移植性高)
       ・MSK: Kafka 互換(移植性高)

    5. 運用成熟度: チームの運用スキルに合わせる
       ・K8s 未経験 → ECS + Fargate から始める
       ・Kafka 未経験 → Kinesis から始める

  ■ よくある落とし穴:

    × NAT Gateway の転送量課金を見落とす($0.045/GB 往復で$0.09/GB)
    × CloudWatch Logs の取り込み量が爆発($0.50/GB)
    × API Gateway REST API の高コスト(HTTP API なら1/3.5)
    × DynamoDB のスキャン操作(全件取得)で RCU 爆発
    × S3 の小さなファイル大量問題(Athena/Spark の性能劣化)
    × Lambda のコールドスタート(VPC 内だと特に遅い→ SnapStart/Provisioned)
    × Glue ETL の DPU 最小値(2 DPU = $0.88/h〜)
    × Redshift のアイドル時課金(Serverless にするか停止設定)

  ■ 最初に覚えるべきサービス(優先度順):

    Tier 1 (必須): S3, IAM, VPC, Lambda, DynamoDB, API Gateway,
                   CloudWatch, SQS, SNS, RDS/Aurora
    Tier 2 (重要): ECS/Fargate, CloudFront, Route53, Kinesis,
                   EventBridge, Glue, Athena, Cognito, Step Functions
    Tier 3 (応用): EKS, Redshift, SageMaker, Bedrock, MSK,
                   OpenSearch, Lake Formation, EMR
    """)

    task("AWS Free Tier を使って Pattern 7 (サーバーレス Web) を実際に構築し、"
         "CloudWatch でコストをモニタリングしてみよう。"
         "月額 $0〜$5 で本番相当のアーキテクチャを体験できる")

    print(f"\n{SEP}")
    print("  以上、Cloud Services Catalog でした。")
    print("  このファイルを辞書的に使い、設計判断の際に参照してください。")
    print(SEP)


if __name__ == "__main__":
    main()
