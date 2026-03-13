#!/usr/bin/env python3
"""
Azure Services Catalog - Azure マネージドサービス完全ガイド
==========================================================

「どの場面でどの Azure サービスを使うべきか」を体系的に整理した実行可能リファレンス。
AWS/GCP との対応関係も全サービスに記載。

実行: python3 azure_services_catalog.py
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
    print(f"\n  考えてほしい疑問: {text}")


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
    print("  Azure Services Catalog")
    print("  Azure マネージドサービス完全ガイド")
    print(SEP)
    print("""
  このカタログの使い方:
  1. カテゴリ別に Azure サービスを網羅的に解説
  2. 各サービスに「いつ使う/使わない」を明記
  3. 全サービスに AWS / GCP の代替を記載
  4. 設計パターン別のサービス組み合わせ例
  5. Cosmos DB 整合性レベルの徹底解説
  6. 面接問題で実践力チェック
    """)

    # ================================================================
    # 1. コンピュート
    # ================================================================
    section("1. コンピュート (Compute)")

    print("""
  Azure のコンピュートは「抽象度」と「制御の粒度」で選ぶ:

    低い ← 抽象度 → 高い
    VM → AKS → Container Instances → App Service → Functions

  Azure 固有の特徴:
  - Windows ワークロードとの親和性が最も高い
  - Azure Arc でハイブリッド/マルチクラウドの統合管理
  - App Service は PaaS として最も成熟したサービスの一つ
    """)

    svc("Azure Virtual Machines (VM)",
        "IaaS 仮想マシン。Windows/Linux 対応。カスタムイメージ対応",
        "GPU が必要 / 特殊 OS 構成 / レガシーアプリ移行 / Windows Server ワークロード",
        "単純な Web API → App Service or Functions のほうが運用コスト低",
        "オンデマンド秒課金。Reserved VM (1/3年) で最大72%割引。Spot VM で最大90%割引",
        "AWS: EC2 / GCP: Compute Engine")

    svc("Azure Functions",
        "イベント駆動サーバーレス関数。C#, Python, Java, JS, PowerShell 対応",
        "API バックエンド / Blob イベント処理 / タイマートリガー / Event Hub 消費",
        "長時間処理(Consumption プランは10分制限) / 大量メモリ / ステートフル処理(→Durable Functions検討)",
        "Consumption: 実行数 + GB-秒。無料枠100万実行/月 + 40万GB-秒。Premium: 予約インスタンスで常時ウォーム",
        "AWS: Lambda / GCP: Cloud Functions")

    svc("Azure Container Instances (ACI)",
        "サーバーレスコンテナ実行。VM プロビジョニング不要で単発コンテナ実行",
        "バッチジョブ / CI/CD のビルドエージェント / 短命タスク / AKS の仮想ノード(バースト)",
        "長期稼働 Web サービス(→App Service or AKS) / 複雑なオーケストレーション",
        "vCPU + メモリの秒課金。Linux: ~$0.000012/秒(1vCPU), メモリ ~$0.0000013/秒/GB",
        "AWS: Fargate (ECS) / GCP: Cloud Run Jobs")

    svc("Azure Kubernetes Service (AKS)",
        "マネージド Kubernetes。コントロールプレーン無料。KEDA 統合によるイベント駆動スケーリング",
        "K8s エコシステム活用 / マイクロサービス / Istio/Linkerd 等サービスメッシュ / マルチクラウド移植性",
        "小規模チーム(App Service のほうが楽) / シンプルな Web API",
        "コントロールプレーン無料(Uptime SLA 有料)。ワーカーノード VM に課金",
        "AWS: EKS / GCP: GKE")

    svc("Azure App Service",
        "フルマネージド PaaS。Web Apps, API Apps, Mobile Apps。デプロイスロットでブルーグリーンデプロイ",
        "Web アプリ / REST API / 継続的デプロイ / .NET, Java, Node, Python, PHP 対応",
        "コンテナオーケストレーション / GPU 処理 / 超大規模トラフィック(→AKS)",
        "App Service Plan 単位。Free/Shared/Basic/Standard/Premium/Isolated。Standard S1: ~$73/月",
        "AWS: Elastic Beanstalk, App Runner / GCP: App Engine")

    svc("Azure Batch",
        "大規模並列バッチコンピューティング。数千ノードの自動スケーリング",
        "HPC / レンダリング / ゲノム解析 / 大規模シミュレーション / ML 学習",
        "リアルタイム処理 / 少量バッチ(Functions で十分)",
        "Batch 管理自体は無料。使用した VM + ストレージに課金。Low-Priority VM で大幅割引",
        "AWS: AWS Batch / GCP: Batch")

    svc("Azure Spring Apps",
        "Spring Boot / Spring Cloud アプリのフルマネージド PaaS。VMware Tanzu 基盤",
        "Java Spring Boot マイクロサービス / Eureka, Config Server 統合 / エンタープライズ Java",
        "Spring 以外のフレームワーク / 非 Java ワークロード",
        "Basic: vCPU + メモリ課金。Standard/Enterprise: アプリインスタンス課金 + vCPU/メモリ",
        "AWS: Elastic Beanstalk (Java) / GCP: Cloud Run")

    question("Azure Functions の Consumption プランと Premium プランをどう使い分ける？"
             "コールドスタートが許容できるか、VNet 統合が必要かが判断基準。")

    # ================================================================
    # 2. ストレージ
    # ================================================================
    section("2. ストレージ (Storage)")

    print("""
  Azure Storage は「ストレージアカウント」単位で管理する。
  1つのストレージアカウント内に Blob, Files, Queue, Table が共存可能。

  Blob のアクセス層:
    Hot  → 頻繁アクセス。保存安い、取得安い
    Cool → 30日以上保持前提。保存安い、取得やや高い
    Cold → 90日以上保持前提。保存さらに安い、取得高い
    Archive → 180日以上保持前提。保存最安、取得に数時間(リハイドレーション)
    """)

    svc("Azure Blob Storage",
        "オブジェクトストレージ。Block Blob, Append Blob, Page Blob の3タイプ",
        "画像/動画/ログ保存 / データレイク基盤 / 静的 Web ホスティング / バックアップ",
        "POSIX ファイルシステムが必要(→Data Lake Storage Gen2) / 共有ファイルシステム(→Azure Files)",
        "Hot: ~$0.018/GB/月(LRS)。Cool: ~$0.01/GB。Archive: ~$0.00099/GB。操作単位課金あり",
        "AWS: S3 / GCP: Cloud Storage")

    svc("Azure Files",
        "フルマネージド SMB/NFS ファイル共有。Windows/Linux VM からマウント可能",
        "レガシーアプリのファイル共有移行 / VM 間共有ストレージ / コンテナの永続ボリューム",
        "オブジェクトストレージ用途(→Blob) / 高スループット分析(→Data Lake Storage Gen2)",
        "Premium(SSD): ~$0.16/GiB/月。Transaction Optimized: ~$0.06/GiB。Hot/Cool もあり",
        "AWS: EFS (NFS), FSx (SMB) / GCP: Filestore")

    svc("Azure Data Lake Storage Gen2",
        "Blob Storage + 階層型名前空間(HNS)。ビッグデータ分析に最適化。ABFS ドライバー対応",
        "データレイク基盤 / Spark/Databricks のストレージ / 大規模 ETL / ACL ベースのアクセス制御",
        "単純なファイル保存(→Blob) / SMB 共有(→Azure Files)",
        "Blob Storage と同等 + 名前空間操作の追加課金。Hot: ~$0.021/GB/月(LRS)",
        "AWS: S3 + Lake Formation / GCP: Cloud Storage + BigLake")

    svc("Azure Managed Disks",
        "VM 用ブロックストレージ。Ultra, Premium SSD v2, Premium SSD, Standard SSD, Standard HDD",
        "VM のルート/データディスク / 高 IOPS データベース / SAP HANA",
        "共有ファイル(→Azure Files) / オブジェクト保存(→Blob)",
        "Ultra SSD: IOPS/スループット課金。Premium SSD P30(1TiB): ~$122/月。スナップショット別課金",
        "AWS: EBS / GCP: Persistent Disk")

    svc("Azure Queue Storage",
        "シンプルな HTTP ベースメッセージキュー。ストレージアカウント内で利用",
        "簡易的な非同期処理 / 低コストキューイング / Functions トリガー",
        "順序保証が必要 / 複雑なルーティング / 重複排除(→Service Bus Queue)",
        "操作単位: ~$0.00036/10,000操作。保存: ~$0.045/GB/月。極めて安価",
        "AWS: SQS / GCP: Cloud Tasks")

    question("Blob Storage のアクセス層自動化(ライフサイクル管理ポリシー)で、"
             "30日後に Cool, 90日後に Archive に自動移行するルールを設計してみよう。")

    # ================================================================
    # 3. データベース
    # ================================================================
    section("3. データベース (Database)")

    print("""
  Azure DB 選択フローチャート:

    リレーショナル?
    ├─ Yes → SQL Server 互換? → Azure SQL Database
    │        PostgreSQL? → Azure Database for PostgreSQL
    │        MySQL? → Azure Database for MySQL
    └─ No  → グローバル分散必要? → Cosmos DB
             キャッシュ? → Azure Cache for Redis
             Key-Value シンプル? → Table Storage
    """)

    svc("Azure SQL Database",
        "フルマネージド SQL Server。単一 DB / エラスティックプール / Managed Instance の3形態",
        "SQL Server ワークロード / .NET アプリ / エンタープライズ OLTP / 自動チューニング",
        "OSS DB を使いたい(→PostgreSQL Flexible) / NoSQL(→Cosmos DB) / 超大規模分析(→Synapse)",
        "DTU モデル: Basic 5DTU ~$5/月。vCore モデル: GP 2vCores ~$370/月。サーバーレス(自動スケール)あり",
        "AWS: RDS for SQL Server / GCP: Cloud SQL for SQL Server")

    svc("Azure Cosmos DB",
        "グローバル分散マルチモデル DB。5つの整合性レベル。5つの API(NoSQL, MongoDB, Cassandra, Gremlin, Table)",
        "グローバル低レイテンシ(1桁ms SLA) / マルチリージョン書込 / 柔軟なスキーマ / IoT 大量データ",
        "単一リージョンの単純 CRUD(→SQL Database のほうが安い) / 複雑な JOIN(→RDB)",
        "プロビジョンド: 100 RU/s ~$5.84/月。サーバーレス: 100万RU ~$0.25。ストレージ: ~$0.25/GB",
        "AWS: DynamoDB / GCP: Cloud Spanner, Firestore")

    subsection("Cosmos DB 整合性レベル詳細解説")

    print("""
  Cosmos DB は5段階の整合性レベルを提供する(上ほど強い):

  ┌─────────────────────────────────────────────────────────────┐
  │  Strong (強い整合性)                                        │
  │  ────────────────────────────────────────────────────────── │
  │  - 全リージョンで最新の書込結果を即座に読取可能              │
  │  - 線形化可能性(Linearizability)を保証                      │
  │  - レイテンシが最も高い(書込時に全レプリカの確認待ち)        │
  │  - 使用例: 金融取引、在庫管理、選挙システム                  │
  │  - 制約: マルチリージョン書込と併用不可                      │
  │  - RU コスト: 最大(読取も2倍のRU消費)                       │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  Bounded Staleness (有界キャラク)                            │
  │  ────────────────────────────────────────────────────────── │
  │  - K回の書込 or T秒以内の遅延を許容                         │
  │  - 「Strong だが少しだけ古くてもよい」場合に最適             │
  │  - 単一リージョン内では Strong と同等                        │
  │  - 使用例: リーダーボード、分析ダッシュボード                │
  │  - 設定例: K=100,000操作 or T=300秒(5分)                    │
  │  - グローバル分散でコスト/パフォーマンスと整合性のバランス    │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  Session (セッション整合性) ← デフォルト                     │
  │  ────────────────────────────────────────────────────────── │
  │  - 同一セッション内では自分の書込を必ず読取可能              │
  │  - Read-your-own-writes, Monotonic reads を保証             │
  │  - 他のクライアントからは Eventual に見える場合がある        │
  │  - 使用例: ユーザープロファイル、ショッピングカート          │
  │  - 最も人気のある選択肢(~70%のワークロード)                 │
  │  - RU コスト: 中程度                                        │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  Consistent Prefix (整合プレフィックス)                      │
  │  ────────────────────────────────────────────────────────── │
  │  - 書込順序が保証される(順序逆転なし)                       │
  │  - 遅延はあるが、データの因果関係は保持                      │
  │  - 使用例: SNS タイムライン、チャット履歴                    │
  │  - Eventual より強いが Session より弱い                      │
  │  - RU コスト: 低め                                          │
  └─────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────┐
  │  Eventual (結果整合性)                                       │
  │  ────────────────────────────────────────────────────────── │
  │  - 順序保証なし。最終的に全レプリカが収束                    │
  │  - レイテンシ最低、スループット最高                          │
  │  - 使用例: いいね数、閲覧数カウンター、レコメンド            │
  │  - 古いデータを一時的に読む可能性がある                      │
  │  - RU コスト: 最低                                          │
  └─────────────────────────────────────────────────────────────┘

  整合性レベルと性能のトレードオフ:
    Strong ←→ Eventual
    整合性:   高い ←──→ 低い
    レイテンシ: 高い ←──→ 低い
    可用性:   低い ←──→ 高い
    RUコスト:  高い ←──→ 低い
    """)

    question("ECサイトの在庫管理に Session 整合性を使うと何が起きる？"
             "2人が同時に残り1個の商品を購入できてしまう問題をどう解決する？")

    subsection("Cosmos DB パーティション戦略")

    print("""
  パーティションキーの選択は Cosmos DB 設計の最重要事項:

  ▶ 良いパーティションキーの条件:
    1. カーディナリティが高い(値の種類が多い)
    2. 読取/書込が均等に分散される
    3. 頻繁なクエリの WHERE 句に含まれる

  ▶ パーティションキーの例:

    ┌────────────────┬──────────────┬──────────────────────────┐
    │ ユースケース    │ 良い例        │ 悪い例                   │
    ├────────────────┼──────────────┼──────────────────────────┤
    │ EC 注文         │ /customerId  │ /orderDate (ホットパーティション)│
    │ IoT テレメトリ  │ /deviceId    │ /timestamp (書込集中)    │
    │ マルチテナント  │ /tenantId    │ /region (偏り大)         │
    │ ソーシャル投稿  │ /userId      │ /category (偏り大)       │
    └────────────────┴──────────────┴──────────────────────────┘

  ▶ 論理パーティション vs 物理パーティション:
    - 論理パーティション: 同じパーティションキー値を持つアイテムの集合
    - 物理パーティション: 1つ以上の論理パーティションを格納(最大50GB, 10,000 RU/s)
    - 物理パーティションは自動分割される(ユーザー操作不要)

  ▶ クロスパーティションクエリの回避:
    - パーティションキーを WHERE に含まないクエリはファンアウト(全パーティション走査)
    - RU コストが大幅に増加 → 設計段階でアクセスパターンを洗い出すことが重要

  ▶ 階層パーティションキー (Hierarchical Partition Keys):
    - 最大3レベルのキーを指定可能(例: /tenantId, /userId, /sessionId)
    - マルチテナントで tenant 内のデータ量に偏りがある場合に有効
    """)

    subsection("Azure SQL Database デプロイモデル比較")

    table(
        ["項目", "単一DB", "エラスティックプール", "Managed Instance"],
        [
            ["概要", "独立したDB", "複数DBでリソース共有", "SQL Serverインスタンス互換"],
            ["ユースケース", "予測可能な負荷", "負荷が変動する複数DB", "オンプレSQL Server移行"],
            ["互換性", "DB レベル", "DB レベル", "インスタンスレベル(CLR,Agent等)"],
            ["VNet統合", "Private Endpoint", "Private Endpoint", "VNet 内デプロイ(専用サブネット)"],
            ["最大サイズ", "100TB(Hyperscale)", "エラスティックプール制限", "16TB"],
            ["リンクサーバー", "不可", "不可", "対応"],
            ["料金例", "GP 2vCores ~$370/月", "GP 2vCores ~$370/月(共有)", "GP 4vCores ~$730/月"],
        ]
    )

    print("""
  ▶ Hyperscale サービスティア:
    - 最大100TB / 読取スケールアウト(最大4レプリカ) / 瞬時バックアップ
    - ページサーバーアーキテクチャ: コンピュートとストレージの分離
    - 料金: GP の約1.5倍だが、大規模 DB では最もコスト効率が良い
    """)

    svc("Azure Database for PostgreSQL - Flexible Server",
        "フルマネージド PostgreSQL。HA, 自動バックアップ, 読取レプリカ対応",
        "OSS DB を使いたい / PostGIS 空間データ / 既存 PostgreSQL 移行",
        "SQL Server 機能が必要(→Azure SQL) / グローバル分散(→Cosmos DB)",
        "Burstable B1ms: ~$12/月。GP D2s_v3: ~$125/月。ストレージ: ~$0.115/GB/月",
        "AWS: RDS/Aurora for PostgreSQL / GCP: Cloud SQL for PostgreSQL, AlloyDB")

    svc("Azure Database for MySQL - Flexible Server",
        "フルマネージド MySQL。HA, 同一ゾーン/ゾーン冗長構成選択可能",
        "既存 MySQL ワークロード移行 / WordPress / PHP アプリ",
        "PostgreSQL の高度な機能が必要 / NoSQL(→Cosmos DB)",
        "Burstable B1ms: ~$12/月。GP D2as_v5: ~$100/月。ストレージ: ~$0.115/GB/月",
        "AWS: RDS/Aurora for MySQL / GCP: Cloud SQL for MySQL")

    svc("Azure Cache for Redis",
        "フルマネージド Redis キャッシュ。クラスタリング, Geo レプリケーション対応",
        "セッションストア / API レスポンスキャッシュ / リーダーボード / Pub/Sub",
        "永続的データストア(→Cosmos DB) / 複雑なクエリ(→SQL Database)",
        "Basic C0(250MB): ~$16/月。Standard C1(1GB): ~$41/月。Premium P1(6GB): ~$215/月",
        "AWS: ElastiCache for Redis / GCP: Memorystore for Redis")

    svc("Azure Table Storage",
        "NoSQL Key-Value ストア。ストレージアカウント内で利用。低コスト",
        "シンプルな Key-Value / 構造化データの安価な保存 / IoT テレメトリログ",
        "複雑なクエリ / セカンダリインデックス / グローバル分散(→Cosmos DB Table API)",
        "~$0.045/GB/月 + 操作単位課金。極めて安価",
        "AWS: DynamoDB (低スループット設定) / GCP: Bigtable (大規模向け)")

    # ================================================================
    # 4. メッセージング・ストリーミング
    # ================================================================
    section("4. メッセージング・ストリーミング (Messaging & Streaming)")

    print("""
  Azure メッセージングの選択基準:

    シンプル非同期 → Queue Storage (最安)
    エンタープライズ統合 → Service Bus (FIFO, トランザクション)
    大量イベントストリーミング → Event Hubs (Kafka 互換)
    イベント通知(Pub/Sub) → Event Grid (リアクティブ)
    """)

    svc("Azure Service Bus",
        "エンタープライズメッセージブローカー。Queue と Topic/Subscription。AMQP 1.0 対応",
        "FIFO 保証 / トランザクション / 重複検出 / デッドレター / セッション(順序制御)",
        "単純な非同期(→Queue Storage のほうが安い) / 大量ストリーミング(→Event Hubs)",
        "Basic: ~$0.05/100万操作。Standard: ~$10/月 + 操作課金。Premium: 1 MU ~$668/月(専用リソース)",
        "AWS: SQS + SNS / GCP: Cloud Pub/Sub")

    svc("Azure Event Hubs",
        "大規模イベントストリーミング。Apache Kafka 互換プロトコル対応。毎秒数百万イベント",
        "IoT テレメトリ / ログ集約 / リアルタイムパイプライン / Kafka 移行",
        "メッセージ単位の確認応答(→Service Bus) / 小規模イベント(→Event Grid)",
        "Basic: 1 TU ~$11/月。Standard: 1 TU ~$22/月。Premium: 1 PU ~$863/月。Capture(→Storage/Data Lake)追加課金",
        "AWS: Kinesis Data Streams, MSK / GCP: Cloud Pub/Sub, Confluent on GCP")

    svc("Azure Event Grid",
        "イベントルーティングサービス。Azure リソースイベントを Pub/Sub で配信",
        "Blob 作成通知 / リソース変更通知 / カスタムイベント / サーバーレスアーキテクチャのグルー",
        "大量データストリーミング(→Event Hubs) / メッセージキューイング(→Service Bus)",
        "操作単位: ~$0.60/100万操作。最初の10万操作/月無料",
        "AWS: EventBridge / GCP: Eventarc")

    subsection("Queue Storage vs Service Bus Queue 比較")

    table(
        ["項目", "Queue Storage", "Service Bus Queue"],
        [
            ["プロトコル", "HTTP/HTTPS REST", "AMQP 1.0 / HTTP"],
            ["最大メッセージ", "64KB", "256KB(Standard) / 100MB(Premium)"],
            ["FIFO保証", "なし", "あり(Session)"],
            ["重複検出", "なし", "あり"],
            ["トランザクション", "なし", "あり"],
            ["デッドレター", "なし(TTL超過で消失)", "あり(DLQ)"],
            ["最大キューサイズ", "500TB", "1-80GB"],
            ["コスト", "極めて安い", "中程度"],
            ["ユースケース", "シンプル非同期", "エンタープライズ統合"],
        ]
    )

    question("マイクロサービス間通信で Event Grid, Service Bus, Event Hubs のどれを使うか？"
             "ヒント: コマンド(1:1)は Service Bus Queue, イベント通知(1:N)は Event Grid or Service Bus Topic。")

    # ================================================================
    # 5. データ分析・ETL
    # ================================================================
    section("5. データ分析・ETL (Analytics)")

    print("""
  Azure のデータ分析スタック:

    取込          → Data Factory / Event Hubs
    保存          → Data Lake Storage Gen2
    加工(ETL)     → Data Factory / Databricks / Synapse Spark
    DWH/分析      → Synapse Analytics (SQL Pool)
    リアルタイム   → Stream Analytics
    ガバナンス     → Microsoft Purview
    可視化        → Power BI
    """)

    svc("Azure Synapse Analytics",
        "統合分析プラットフォーム。専用 SQL プール(旧 SQL DW) + サーバーレス SQL + Spark プール",
        "エンタープライズ DWH / データレイク分析 / SQL + Spark の統合 / Power BI 連携",
        "OLTP ワークロード(→SQL Database) / 小規模分析(→サーバーレス SQL で十分)",
        "専用 SQL: DW100c ~$1.20/h。サーバーレス SQL: ~$5/TB スキャン。Spark: ノード課金",
        "AWS: Redshift + Athena + EMR / GCP: BigQuery + Dataproc")

    svc("Azure Data Factory (ADF)",
        "クラウドスケール ETL/ELT。90+ コネクタ。GUI パイプラインデザイナー。Mapping Data Flow",
        "データ統合 / ETL パイプライン / オンプレ→クラウドデータ移行 / スケジュール実行",
        "リアルタイム処理(→Stream Analytics) / 複雑な変換ロジック(→Databricks)",
        "パイプライン実行: ~$1/1,000回。Data Flow: ~$0.274/vCore-h。DIU 課金あり",
        "AWS: Glue / GCP: Dataflow, Cloud Data Fusion")

    svc("Azure Databricks",
        "Apache Spark ベースの統合分析プラットフォーム。Unity Catalog, Delta Lake, MLflow 統合",
        "大規模 ETL / ML ワークロード / Delta Lake / リアルタイム + バッチ統合(Lakehouse)",
        "シンプルな SQL 分析(→Synapse サーバーレス SQL) / 小規模データ(→Data Factory のみ)",
        "DBU (Databricks Unit) + VM 費用。Standard: ~$0.07/DBU(ジョブ), ~$0.22/DBU(対話型)",
        "AWS: EMR, Databricks on AWS / GCP: Dataproc, Databricks on GCP")

    svc("Azure Stream Analytics",
        "フルマネージドリアルタイムストリーム処理。SQL ライクなクエリ言語",
        "IoT リアルタイムダッシュボード / 異常検知 / ストリーム ETL / Event Hubs → DB/DWH",
        "複雑な ML 推論(→Databricks Structured Streaming) / バッチ処理(→Data Factory)",
        "Streaming Unit (SU) 課金: 1 SU ~$0.11/h (~$80/月)",
        "AWS: Kinesis Data Analytics / GCP: Dataflow (Streaming)")

    svc("Azure HDInsight",
        "マネージド OSS 分析クラスタ。Hadoop, Spark, Hive, HBase, Kafka, Storm 対応",
        "既存 Hadoop ワークロード移行 / HBase が必要 / OSS エコシステムそのまま使いたい",
        "新規プロジェクト(→Synapse or Databricks のほうが生産性高い)",
        "ヘッドノード + ワーカーノード VM 課金。D3 v2: ~$0.35/h per node",
        "AWS: EMR / GCP: Dataproc")

    svc("Microsoft Purview (旧 Azure Purview)",
        "データガバナンス・データカタログ。自動スキャンでメタデータ収集・血統追跡",
        "データカタログ / 分類・ラベリング / データリネージ / コンプライアンス",
        "単純なデータ保存(ガバナンス不要な段階)",
        "Data Map: vCore 課金 ~$0.41/h。Data Estate Insights: 追加課金",
        "AWS: Glue Data Catalog + Lake Formation / GCP: Dataplex, Data Catalog")

    task("Azure Data Factory で Blob Storage → Synapse Analytics (専用 SQL プール) の"
         "ETL パイプラインを構築し、日次スケジュールで実行する設計を書いてみよう。")

    # ================================================================
    # 6. AI/ML サービス
    # ================================================================
    section("6. AI/ML サービス")

    print("""
  Azure AI の差別化要因:
  - Azure OpenAI Service: GPT-4, GPT-4o, o1 を Azure のセキュリティで利用可能
  - Cognitive Services が Azure AI Services に統合(2023年リブランド)
  - Responsible AI ツールキットが充実
    """)

    svc("Azure Machine Learning",
        "エンドツーエンド ML プラットフォーム。AutoML, Designer(GUI), SDK(コード), MLOps パイプライン",
        "カスタムモデル学習 / MLOps / 実験管理 / モデルレジストリ / マネージドエンドポイント",
        "既製 AI API で済む場合(→Cognitive Services) / LLM 活用のみ(→Azure OpenAI)",
        "コンピュートインスタンス/クラスタ VM 課金。マネージドエンドポイント: VM + 推論課金",
        "AWS: SageMaker / GCP: Vertex AI")

    svc("Azure OpenAI Service",
        "OpenAI モデル(GPT-4, GPT-4o, o1, DALL-E, Whisper)を Azure 上でセキュアに利用",
        "エンタープライズ LLM 活用 / RAG 構築 / チャットボット / コンテンツ生成 / コード生成",
        "カスタムモデル学習(→Azure ML) / 画像認識特化(→Azure AI Vision)",
        "トークン課金。GPT-4o: 入力 ~$2.50/100万トークン, 出力 ~$10.00/100万トークン。PTU(プロビジョンドスループット)あり",
        "AWS: Bedrock (Anthropic Claude, etc.) / GCP: Vertex AI (Gemini)")

    svc("Azure AI Services (旧 Cognitive Services)",
        "事前構築済み AI API 群。Vision, Speech, Language, Decision カテゴリ",
        "画像分類・OCR / 音声認識・合成 / 感情分析 / テキスト翻訳 / ドキュメント解析",
        "カスタムモデルが必要(→Azure ML) / 高度な生成 AI(→Azure OpenAI)",
        "API 呼出単位課金。Vision: ~$1/1,000回。Speech: ~$1/音声1時間。Free 枠あり",
        "AWS: Rekognition, Transcribe, Comprehend, Translate / GCP: Vision AI, Speech-to-Text, NLP API")

    svc("Azure Bot Service",
        "チャットボット構築プラットフォーム。Bot Framework SDK + Azure AI サービス統合",
        "カスタマーサポートボット / FAQ ボット / Teams, Slack, Web 連携",
        "単純な LLM チャット(→Azure OpenAI 直接利用) / 音声のみ(→Speech Service)",
        "Standard チャンネル: 無料(Teams, Web)。Premium チャンネル: メッセージ課金",
        "AWS: Lex / GCP: Dialogflow")

    question("Azure OpenAI と直接 OpenAI API の違いは何か？"
             "エンタープライズで Azure OpenAI を選ぶ理由を3つ挙げよ。"
             "(ヒント: VNet統合, データの地理的制御, SLA, Microsoft 責任共有モデル)")

    # ================================================================
    # 7. ネットワーク
    # ================================================================
    section("7. ネットワーク (Networking)")

    print("""
  Azure ネットワークの基本構造:

    リージョン
    └─ VNet (仮想ネットワーク)
       ├─ サブネット A (Web 層)  ── NSG (ネットワークセキュリティグループ)
       ├─ サブネット B (App 層)  ── NSG
       └─ サブネット C (DB 層)   ── NSG + Private Endpoint

  VNet ピアリングでリージョン間接続、ExpressRoute でオンプレ接続。
    """)

    svc("Azure Virtual Network (VNet)",
        "Azure の基本ネットワーク。サブネット分割, NSG, ルートテーブル, VNet ピアリング",
        "ほぼ全ての Azure デプロイで必要。リソースのネットワーク分離とセキュリティ",
        "VNet 自体を使わないケースはほぼない(SaaS 利用のみの場合)",
        "VNet 自体は無料。VNet ピアリング: ~$0.01/GB(同一リージョン), ~$0.02/GB(クロスリージョン)",
        "AWS: VPC / GCP: VPC Network")

    svc("Azure Load Balancer",
        "L4 ロードバランサー。TCP/UDP 対応。Standard(ゾーン冗長) と Basic(無料) の2 SKU",
        "VM 間の負荷分散 / 高可用性構成 / 内部(Private)LB でマイクロサービス間通信",
        "HTTP/HTTPS ルーティング(→Application Gateway) / グローバル分散(→Front Door)",
        "Standard: ルール ~$0.025/h + データ処理 ~$0.005/GB。Basic: 無料",
        "AWS: NLB / GCP: Internal/External TCP/UDP Load Balancer")

    svc("Azure Application Gateway",
        "L7 ロードバランサー + WAF。SSL 終端, URL ベースルーティング, Cookie アフィニティ",
        "Web アプリの負荷分散 / WAF による Web 攻撃防御 / SSL オフロード / 複数サイトホスティング",
        "L4 負荷分散のみ(→Load Balancer) / グローバル分散(→Front Door)",
        "V2 Standard: ~$0.20/h + 容量ユニット課金。WAF V2: ~$0.36/h + 容量ユニット",
        "AWS: ALB + WAF / GCP: External HTTP(S) Load Balancer + Cloud Armor")

    svc("Azure Front Door",
        "グローバル L7 ロードバランサー + CDN + WAF。エニーキャストで最寄り POP にルーティング",
        "グローバル Web アプリ / マルチリージョン DR / SSL 終端 + WAF + CDN の統合",
        "単一リージョン(→Application Gateway) / 静的コンテンツのみ(→Azure CDN)",
        "Standard: ~$35/月(ベース) + リクエスト/データ転送課金。Premium: WAF 高度ルール付き",
        "AWS: CloudFront + WAF + Global Accelerator / GCP: Cloud CDN + Cloud Armor")

    svc("Azure CDN",
        "コンテンツ配信ネットワーク。Microsoft, Akamai, Verizon プロバイダー選択可能",
        "静的コンテンツ配信 / 動画ストリーミング / ダウンロード高速化",
        "動的コンテンツ中心(→Front Door) / WAF 必要(→Front Door Premium)",
        "Standard Microsoft: ~$0.081/GB(最初10TB)。リージョンにより異なる",
        "AWS: CloudFront / GCP: Cloud CDN")

    svc("Azure ExpressRoute",
        "専用回線でオンプレミス→Azure を接続。パブリックインターネット非経由",
        "ハイブリッドクラウド / 大量データ転送 / 低レイテンシ要件 / 金融系コンプライアンス",
        "小規模接続(→VPN Gateway) / テスト環境(コスト過大)",
        "50Mbps: ~$55/月(Metered)。1Gbps: ~$436/月。Unlimited プランあり。Global Reach 追加料金",
        "AWS: Direct Connect / GCP: Cloud Interconnect")

    svc("Azure DNS",
        "フルマネージド DNS ホスティング。エニーキャスト対応。Private DNS Zone あり",
        "ドメインの DNS 管理 / VNet 内プライベート名前解決",
        "ドメイン登録(→外部レジストラ。Azure DNS はホスティングのみ)",
        "ゾーン: ~$0.50/月。クエリ: ~$0.40/100万クエリ(最初10億)",
        "AWS: Route 53 / GCP: Cloud DNS")

    svc("Azure Private Link / Private Endpoint",
        "Azure サービスへのプライベート接続。VNet 内からパブリック IP を経由せずアクセス",
        "DB, Storage, Key Vault へのセキュアアクセス / データ流出防止 / コンプライアンス",
        "パブリックアクセスで十分な開発環境",
        "Private Endpoint: ~$0.01/h + データ処理 ~$0.01/GB",
        "AWS: PrivateLink + VPC Endpoint / GCP: Private Service Connect")

    subsection("ネットワークセキュリティ階層")

    print("""
  Azure ネットワークセキュリティは多層防御で設計する:

    第1層: Azure DDoS Protection (L3/L4 DDoS 防御)
    第2層: Front Door WAF / Application Gateway WAF (L7 防御)
    第3層: NSG (サブネット/NIC レベルのファイアウォール)
    第4層: Azure Firewall (中央集約型 L3-L7 ファイアウォール)
    第5層: Private Endpoint (パブリックIP排除)

  ▶ NSG vs Azure Firewall:
    - NSG: ステートフル L3/L4。サブネット単位。無料。基本的なIP/ポートフィルタ
    - Azure Firewall: L3-L7。FQDN フィルタ、脅威インテリジェンス、TLS インスペクション
    - 設計パターン: Hub-Spoke VNet で Hub に Azure Firewall を集約配置

  ▶ Hub-Spoke ネットワーク設計:
    Hub VNet
    ├── Azure Firewall (全トラフィック検査)
    ├── VPN Gateway / ExpressRoute Gateway
    └── Azure Bastion (踏み台ホスト)
         │ VNet Peering
    ├── Spoke VNet A (Web 層)
    ├── Spoke VNet B (App 層)
    └── Spoke VNet C (Data 層)
    """)

    task("Hub-Spoke アーキテクチャを Bicep で定義してみよう。"
         "Hub VNet に Azure Firewall, Spoke VNet に App Service (VNet 統合) を配置する構成で。")

    # ================================================================
    # 8. セキュリティ・ID
    # ================================================================
    section("8. セキュリティ・ID (Security & Identity)")

    print("""
  Azure セキュリティの最大の強み: Microsoft Entra ID (旧 Azure AD)
  - Microsoft 365, Azure, Dynamics 365 との統合
  - 条件付きアクセスポリシー
  - 世界最大の ID プロバイダーの一つ

  ゼロトラストの原則:
    明示的に検証 → 最小権限アクセス → 侵害を想定
    """)

    svc("Microsoft Entra ID (旧 Azure AD)",
        "クラウドベース ID・アクセス管理。SSO, MFA, 条件付きアクセス, B2B/B2C",
        "Azure リソースの認証認可 / Microsoft 365 統合 / エンタープライズ SSO / 外部 ID 管理",
        "オンプレ AD のみで完結する閉域環境(ただしハイブリッド推奨)",
        "Free: 基本機能。P1: ~$6/ユーザー/月(条件付きアクセス)。P2: ~$9/ユーザー/月(PIM, リスクベース)",
        "AWS: IAM Identity Center (旧 SSO) / GCP: Cloud Identity")

    svc("Azure Key Vault",
        "シークレット, 暗号鍵, 証明書の一元管理。HSM バックエンド対応",
        "API キー/接続文字列の安全な保管 / TLS 証明書管理 / 暗号鍵ローテーション / ディスク暗号化鍵",
        "アプリケーション設定のみ(→App Configuration) / 大量データ暗号化(→クライアント側暗号化)",
        "Standard: シークレット操作 ~$0.03/10,000操作。Premium(HSM): ~$1/鍵/月 + 操作課金",
        "AWS: Secrets Manager + KMS / GCP: Secret Manager + Cloud KMS")

    svc("Microsoft Defender for Cloud (旧 Azure Defender / Security Center)",
        "CSPM + CWPP。クラウドセキュリティ態勢管理と脅威保護。マルチクラウド対応(AWS/GCP も)",
        "セキュリティスコア評価 / 脆弱性スキャン / 脅威検出 / コンプライアンス評価",
        "基本的な監視のみ(→Azure Monitor)",
        "Free: セキュリティスコア + 推奨事項。Defender プラン: サーバー ~$15/月, DB ~$15/月 等サービス別",
        "AWS: Security Hub + GuardDuty / GCP: Security Command Center")

    svc("Azure Policy",
        "リソースのコンプライアンスをコードで強制。組み込みポリシー + カスタムポリシー",
        "タグ強制 / 許可リージョン制限 / SKU 制限 / 暗号化強制 / 監査ログ",
        "個別リソースの権限管理(→RBAC)",
        "無料(Azure Policy 自体)。ゲスト構成(VM 内評価): ~$0.04/サーバー/h",
        "AWS: Organizations SCP + Config Rules / GCP: Organization Policy")

    svc("Azure RBAC (ロールベースアクセス制御)",
        "Azure リソースへのきめ細かいアクセス制御。組み込みロール 70+ / カスタムロール対応",
        "最小権限の原則の実装 / チーム別アクセス制御 / サブスクリプション/RG/リソース レベル",
        "Azure 外のアプリケーション認可(→Entra ID アプリロール or カスタム実装)",
        "無料(Azure プラットフォーム機能)",
        "AWS: IAM Policy / GCP: IAM Roles")

    svc("Managed Identity (マネージド ID)",
        "Azure リソースに自動的に ID を付与。資格情報の管理不要でサービス間認証",
        "App Service → Key Vault / VM → Storage / Functions → SQL Database 等のサービス間認証",
        "Azure 外のリソースへの認証(→サービスプリンシパル or Workload Identity Federation)",
        "無料。Entra ID の機能として提供",
        "AWS: IAM Role (EC2/Lambda 用) / GCP: Service Account")

    question("Managed Identity のシステム割当とユーザー割当の違いは？"
             "複数のリソースで同じ ID を共有したい場合はどちらを使う？")

    # ================================================================
    # 9. 監視・運用
    # ================================================================
    section("9. 監視・運用 (Monitoring & Operations)")

    print("""
  Azure 監視の全体像:

    Azure Monitor (統合プラットフォーム)
    ├─ メトリクス → リアルタイム数値データ
    ├─ ログ(Log Analytics) → KQL でクエリ
    ├─ Application Insights → APM (アプリ性能監視)
    ├─ アラート → メトリクス/ログ条件でアクション実行
    └─ ダッシュボード → Azure Portal / Grafana 統合
    """)

    svc("Azure Monitor",
        "Azure の統合監視プラットフォーム。メトリクス, ログ, アラート, 自動スケールの基盤",
        "全ての Azure リソース監視。プラットフォームメトリクスは自動収集",
        "監視しないケースはない(常に有効にすべき)",
        "プラットフォームメトリクス: 無料。カスタムメトリクス: ~$0.258/メトリクス系列/月",
        "AWS: CloudWatch / GCP: Cloud Monitoring")

    svc("Application Insights",
        "APM (Application Performance Monitoring)。分散トレーシング, 依存関係マップ, スマート検出",
        "Web アプリの性能監視 / エラー追跡 / 分散トレーシング / ユーザー行動分析",
        "インフラのみの監視(→Azure Monitor メトリクス) / ログ集約のみ(→Log Analytics)",
        "データ取込: ~$2.30/GB(最初5GB/月無料)。保持: 最初90日無料, 以降 ~$0.10/GB/月",
        "AWS: X-Ray + CloudWatch Application Insights / GCP: Cloud Trace + Error Reporting")

    svc("Log Analytics (Azure Monitor Logs)",
        "ログデータの収集・分析基盤。Kusto Query Language (KQL) でクエリ。ワークスペース単位管理",
        "セキュリティログ分析(Sentinel) / インフラログ集約 / カスタムクエリ / 長期保持",
        "リアルタイムメトリクス監視(→Azure Monitor メトリクス)",
        "データ取込: ~$2.30/GB(最初5GB/日無料で31日保持)。Commitment Tier: 100GB/日 ~$196/日(割引あり)",
        "AWS: CloudWatch Logs + Logs Insights / GCP: Cloud Logging + Log Analytics")

    svc("Azure Automation",
        "ランブック(PowerShell/Python)による運用自動化。Update Management, 構成管理",
        "定期メンテナンスタスク / VM パッチ管理 / リソースの自動起動停止 / 構成ドリフト検出",
        "CI/CD パイプライン(→Azure DevOps / GitHub Actions) / IaC(→Bicep/Terraform)",
        "ジョブ実行: ~$0.002/分。Update Management: Log Analytics + VM エージェントで無料(一部)",
        "AWS: Systems Manager / GCP: Cloud Scheduler + Cloud Functions")

    svc("Azure Resource Manager (ARM) / Bicep",
        "Azure のインフラ管理レイヤー。ARM テンプレート(JSON) or Bicep(DSL) で IaC",
        "Azure リソースの IaC / 反復可能なデプロイ / 環境間の一貫性 / What-if 分析",
        "マルチクラウド IaC(→Terraform) / 手動操作で十分な検証環境",
        "無料。ARM/Bicep 自体に課金なし(デプロイされたリソースに課金)",
        "AWS: CloudFormation / GCP: Deployment Manager, Config Connector")

    question("KQL (Kusto Query Language) で Application Insights のリクエストログから"
             "レイテンシ P99 を計算するクエリを書いてみよう。"
             "ヒント: requests | summarize percentile(duration, 99) by bin(timestamp, 1h)")

    # ================================================================
    # 10. DevOps
    # ================================================================
    section("10. DevOps")

    print("""
  Azure の DevOps エコシステム:

    Azure DevOps (オールインワン)     GitHub (Microsoft 傘下)
    ├─ Repos (Git リポジトリ)          ├─ Repositories
    ├─ Pipelines (CI/CD)              ├─ Actions (CI/CD)
    ├─ Boards (作業管理)              ├─ Issues / Projects
    ├─ Artifacts (パッケージ管理)      ├─ Packages
    └─ Test Plans (テスト管理)         └─ Copilot

  多くの組織が GitHub + Azure Pipelines のハイブリッド、
  または GitHub Actions + Azure の組み合わせに移行中。
    """)

    svc("Azure DevOps - Repos",
        "Git リポジトリホスティング。ブランチポリシー, PR レビュー, TFVC サポート",
        "エンタープライズ Git / 厳格なブランチポリシー / Azure Pipelines との緊密な統合",
        "OSS プロジェクト / GitHub エコシステム活用(→GitHub)",
        "Basic プラン: 最初5ユーザー無料。追加ユーザー ~$6/月",
        "AWS: CodeCommit / GCP: Cloud Source Repositories / OSS: GitLab, Gitea")

    svc("Azure DevOps - Pipelines",
        "CI/CD パイプライン。YAML or Classic(GUI)。マルチステージ、マルチ環境、承認ゲート",
        "複雑な CI/CD / マルチステージデプロイ / エンタープライズ承認ワークフロー / Azure 統合",
        "シンプルな CI/CD(→GitHub Actions のほうが軽量) / 非 Azure 中心環境",
        "1並列ジョブ無料(1,800分/月)。追加並列ジョブ: MS ホスト ~$40/月、セルフホスト ~$15/月",
        "AWS: CodePipeline + CodeBuild / GCP: Cloud Build / OSS: Jenkins, GitLab CI")

    svc("Azure DevOps - Boards",
        "アジャイル作業管理。バックログ, スプリント, カンバン, カスタムプロセステンプレート",
        "エンタープライズアジャイル / SAFe 対応 / Azure Repos/Pipelines との統合",
        "軽量プロジェクト管理(→GitHub Issues/Projects) / 非開発チーム(→Jira)",
        "Basic プランに含まれる",
        "AWS: なし(Jira 等外部ツール) / GCP: なし / OSS: Jira, Linear, Notion")

    svc("Azure DevOps - Artifacts",
        "パッケージ管理。NuGet, npm, Python(pip), Maven, Universal Packages 対応",
        "プライベートパッケージレジストリ / ビルドアーティファクト管理 / 上流ソースのキャッシュ",
        "コンテナイメージ(→Azure Container Registry) / 単純なファイル保存(→Blob Storage)",
        "2GiB 無料。追加ストレージ: ~$2/GiB/月",
        "AWS: CodeArtifact / GCP: Artifact Registry / OSS: Nexus, Artifactory")

    svc("GitHub Actions (Azure 統合)",
        "GitHub ネイティブ CI/CD。Azure Login Action, Azure CLI Action で Azure と統合",
        "GitHub リポジトリの CI/CD / OSS プロジェクト / Azure へのデプロイ / Copilot 活用",
        "Azure DevOps Pipelines の高度な承認ワークフローが必要な場合",
        "Public repo: 無料。Private: 2,000分/月無料(Free), 3,000分/月(Pro)。追加 ~$0.008/分(Linux)",
        "AWS: CodePipeline / GCP: Cloud Build / OSS: Jenkins, GitLab CI")

    task("GitHub Actions で Azure App Service にデプロイする YAML ワークフローを書いてみよう。"
         "azure/webapps-deploy@v2 アクションと OIDC(OpenID Connect)認証を使う構成で。")

    subsection("Azure Container Registry (ACR)")

    svc("Azure Container Registry",
        "プライベートコンテナイメージレジストリ。Geo レプリケーション, Taskによる自動ビルド",
        "AKS / App Service / Functions のコンテナイメージ管理 / CI/CD パイプラインの成果物",
        "パブリックイメージのみ使う場合(→Docker Hub)",
        "Basic: ~$5/月(10GB)。Standard: ~$20/月(100GB)。Premium: ~$50/月(500GB, Geoレプリケーション)",
        "AWS: ECR / GCP: Artifact Registry / OSS: Harbor")

    subsection("Azure DevOps vs GitHub 選択基準")

    table(
        ["観点", "Azure DevOps", "GitHub"],
        [
            ["CI/CD", "Pipelines(高機能,承認ゲート)", "Actions(軽量,マーケットプレイス)"],
            ["プロジェクト管理", "Boards(Agile/Scrum/CMMI)", "Issues+Projects(軽量)"],
            ["対象", "エンタープライズ", "OSS + スタートアップ"],
            ["TFVC", "対応", "非対応"],
            ["Copilot", "なし", "GitHub Copilot"],
            ["料金", "5ユーザー無料+追加$6/月", "Free/Team($4/月)/Enterprise($21/月)"],
            ["推奨パターン", "大企業の内製開発", "モダンな開発チーム"],
        ]
    )

    print("""
  ▶ ハイブリッド構成(推奨パターン):
    - ソースコード: GitHub (Copilot, コードレビュー, OSS エコシステム)
    - CI/CD: GitHub Actions (Azure へのデプロイ)
    - プロジェクト管理: Azure DevOps Boards or GitHub Projects
    - パッケージ: Azure Artifacts or GitHub Packages
    - セキュリティ: GitHub Advanced Security (GHAS) + Defender for DevOps
    """)

    subsection("Infrastructure as Code 比較: Bicep vs Terraform")

    table(
        ["観点", "Bicep", "Terraform"],
        [
            ["対応クラウド", "Azure のみ", "マルチクラウド"],
            ["言語", "Bicep DSL(JSON派生)", "HCL"],
            ["状態管理", "ARM が管理(stateless)", "State ファイル必要"],
            ["プレビュー", "What-if", "Plan"],
            ["学習コスト", "低い(Azure開発者)", "中程度"],
            ["エコシステム", "Azure Verified Modules", "Terraform Registry(巨大)"],
            ["推奨", "Azure 専用環境", "マルチクラウド/既存TFチーム"],
        ]
    )

    # ================================================================
    # 11. AWS / GCP / Azure 対応マッピング表
    # ================================================================
    section("11. AWS / GCP / Azure 三大クラウド対応マッピング表")

    subsection("コンピュート")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["仮想マシン", "EC2", "Compute Engine", "Virtual Machines"],
            ["サーバーレス関数", "Lambda", "Cloud Functions", "Functions"],
            ["コンテナ(マネージド)", "ECS/Fargate", "Cloud Run", "Container Instances"],
            ["Kubernetes", "EKS", "GKE", "AKS"],
            ["PaaS", "Elastic Beanstalk", "App Engine", "App Service"],
            ["バッチ", "AWS Batch", "Batch", "Azure Batch"],
        ]
    )

    subsection("ストレージ")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["オブジェクト", "S3", "Cloud Storage", "Blob Storage"],
            ["ファイル共有", "EFS/FSx", "Filestore", "Azure Files"],
            ["ブロック", "EBS", "Persistent Disk", "Managed Disks"],
            ["データレイク", "S3+Lake Formation", "Cloud Storage+BigLake", "Data Lake Storage Gen2"],
        ]
    )

    subsection("データベース")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["RDB(マネージド)", "RDS/Aurora", "Cloud SQL/AlloyDB", "SQL Database/PostgreSQL Flex"],
            ["NoSQL(ドキュメント)", "DynamoDB", "Firestore", "Cosmos DB"],
            ["グローバル分散", "DynamoDB Global", "Cloud Spanner", "Cosmos DB"],
            ["キャッシュ", "ElastiCache", "Memorystore", "Cache for Redis"],
            ["DWH", "Redshift", "BigQuery", "Synapse Analytics"],
        ]
    )

    subsection("メッセージング")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["キュー", "SQS", "Cloud Tasks", "Service Bus Queue"],
            ["Pub/Sub", "SNS", "Pub/Sub", "Service Bus Topic/Event Grid"],
            ["ストリーミング", "Kinesis", "Pub/Sub", "Event Hubs"],
            ["イベントバス", "EventBridge", "Eventarc", "Event Grid"],
        ]
    )

    subsection("AI/ML")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["ML プラットフォーム", "SageMaker", "Vertex AI", "Azure ML"],
            ["LLM API", "Bedrock", "Vertex AI (Gemini)", "Azure OpenAI"],
            ["画像認識", "Rekognition", "Vision AI", "AI Vision"],
            ["音声認識", "Transcribe", "Speech-to-Text", "AI Speech"],
            ["自然言語", "Comprehend", "NLP API", "AI Language"],
        ]
    )

    subsection("ネットワーク")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["仮想ネットワーク", "VPC", "VPC Network", "VNet"],
            ["L4 LB", "NLB", "TCP/UDP LB", "Load Balancer"],
            ["L7 LB", "ALB", "HTTP(S) LB", "Application Gateway"],
            ["CDN", "CloudFront", "Cloud CDN", "Azure CDN/Front Door"],
            ["DNS", "Route 53", "Cloud DNS", "Azure DNS"],
            ["専用回線", "Direct Connect", "Interconnect", "ExpressRoute"],
            ["プライベート接続", "PrivateLink", "Private Service Connect", "Private Link"],
        ]
    )

    subsection("セキュリティ・ID")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["ID管理", "IAM/Identity Center", "Cloud Identity/IAM", "Entra ID"],
            ["シークレット管理", "Secrets Manager", "Secret Manager", "Key Vault"],
            ["CSPM", "Security Hub", "SCC", "Defender for Cloud"],
            ["ポリシー", "SCP/Config Rules", "Org Policy", "Azure Policy"],
            ["WAF", "WAF", "Cloud Armor", "Front Door WAF/App GW WAF"],
        ]
    )

    subsection("監視・DevOps")
    table(
        ["カテゴリ", "AWS", "GCP", "Azure"],
        [
            ["監視", "CloudWatch", "Cloud Monitoring", "Azure Monitor"],
            ["APM", "X-Ray", "Cloud Trace", "Application Insights"],
            ["ログ", "CloudWatch Logs", "Cloud Logging", "Log Analytics"],
            ["IaC", "CloudFormation", "Deployment Manager", "ARM/Bicep"],
            ["CI/CD", "CodePipeline", "Cloud Build", "Azure Pipelines/GitHub Actions"],
        ]
    )

    # ================================================================
    # 12. 設計パターン別サービス組み合わせ
    # ================================================================
    section("12. 設計パターン別サービス組み合わせ")

    subsection("パターン1: Web API (RESTful)")

    diagram([
        "クライアント",
        "  │",
        "  ▼",
        "Azure Front Door (CDN + WAF)",
        "  │",
        "  ▼",
        "Application Gateway (L7 LB + SSL終端)",
        "  │",
        "  ▼",
        "App Service / AKS (Web API)",
        "  │",
        "  ├──▶ Azure SQL Database (OLTP)",
        "  ├──▶ Azure Cache for Redis (キャッシュ)",
        "  └──▶ Blob Storage (静的ファイル)",
        "",
        "監視: Application Insights + Log Analytics",
        "認証: Entra ID + Managed Identity",
        "シークレット: Key Vault",
    ])

    print("""
  設計ポイント:
  - Front Door でグローバルトラフィック分散 + DDoS 保護
  - Application Gateway で URL ベースルーティング + WAF
  - App Service のデプロイスロットでブルーグリーンデプロイ
  - Managed Identity で Key Vault からシークレット取得(コード内に資格情報なし)
  - Application Insights の分散トレーシングで全リクエスト追跡
    """)

    subsection("パターン2: イベント駆動 (Event-Driven)")

    diagram([
        "イベント発生源(Blob, DB変更, IoT, カスタムアプリ)",
        "  │",
        "  ▼",
        "Event Grid (イベントルーティング)",
        "  │",
        "  ├──▶ Azure Functions (イベント処理)",
        "  │      ├──▶ Cosmos DB (状態保存)",
        "  │      └──▶ Service Bus Queue (後続処理)",
        "  │",
        "  ├──▶ Logic Apps (ワークフロー自動化)",
        "  │",
        "  └──▶ Event Hubs (大量イベント → Stream Analytics)",
        "",
        "デッドレター: Service Bus DLQ / Storage Account",
    ])

    print("""
  設計ポイント:
  - Event Grid で Azure リソースイベントを捕捉してルーティング
  - Functions は Consumption プランで完全従量課金
  - 処理失敗は Service Bus DLQ に退避してリトライ
  - Event Hubs は大量ストリームの場合に使用
  - Logic Apps は Salesforce, Office 365 等外部 SaaS 連携に最適
    """)

    subsection("パターン3: リアルタイムストリーミング")

    diagram([
        "IoT デバイス / アプリログ / クリックストリーム",
        "  │",
        "  ▼",
        "Event Hubs (Kafka互換, パーティション分散取込)",
        "  │",
        "  ├──▶ Stream Analytics (SQL ライクなリアルタイム集計)",
        "  │      ├──▶ Power BI (リアルタイムダッシュボード)",
        "  │      ├──▶ Cosmos DB (リアルタイム集計結果)",
        "  │      └──▶ Azure SQL (集計テーブル)",
        "  │",
        "  └──▶ Event Hubs Capture → Data Lake Storage Gen2 (生データ保存)",
        "         └──▶ Synapse / Databricks (バッチ分析)",
    ])

    print("""
  設計ポイント:
  - Event Hubs Capture で生データを Data Lake に自動保存(Lambda Architecture の Batch Layer)
  - Stream Analytics で時間ウィンドウ集計(タンブリング, ホッピング, スライディング)
  - Cosmos DB Change Feed で下流サービスへの変更伝播
  - Event Hubs のパーティション数でスケールアウト(作成後の増加は不可、設計時に決定)
    """)

    subsection("パターン4: ML パイプライン")

    diagram([
        "データソース (SQL DB, Blob, Data Lake)",
        "  │",
        "  ▼",
        "Data Factory (データ取込・前処理パイプライン)",
        "  │",
        "  ▼",
        "Data Lake Storage Gen2 (特徴量ストア / 学習データ)",
        "  │",
        "  ▼",
        "Azure Machine Learning",
        "  ├── AutoML (モデル選定自動化)",
        "  ├── Compute Cluster (分散学習)",
        "  ├── MLflow (実験追跡)",
        "  └── Model Registry (モデルバージョン管理)",
        "  │",
        "  ▼",
        "Managed Online Endpoint (推論 API)",
        "  ├── Blue/Green デプロイ (トラフィック分割)",
        "  └── Autoscale (負荷に応じてスケール)",
        "",
        "監視: Azure Monitor + Application Insights (モデルドリフト検出)",
    ])

    print("""
  設計ポイント:
  - Data Factory で定期的にデータ取込 → Data Lake にランディング
  - Azure ML パイプラインで前処理→学習→評価→登録を自動化
  - Managed Online Endpoint でブルーグリーンデプロイ(新モデルに段階的に切替)
  - Application Insights でレイテンシ、エラー率、入力データ分布を監視
  - Azure OpenAI と組み合わせた RAG パターンも可能
    """)

    subsection("パターン5: マイクロサービス")

    diagram([
        "クライアント",
        "  │",
        "  ▼",
        "Azure Front Door (グローバル LB)",
        "  │",
        "  ▼",
        "API Management (API Gateway, 認証, レート制限, 変換)",
        "  │",
        "  ▼",
        "AKS クラスタ",
        "  ├── Service A (注文) ──── Azure SQL Database",
        "  ├── Service B (在庫) ──── Cosmos DB",
        "  ├── Service C (通知) ──── SendGrid / Communication Services",
        "  └── Service D (検索) ──── Azure AI Search",
        "      │",
        "      ▼ (非同期通信)",
        "  Service Bus Topic/Subscription",
        "      │",
        "      ├── Service B が在庫更新イベントを Subscribe",
        "      └── Service C が注文確定イベントを Subscribe",
        "",
        "分散トレーシング: Application Insights (全サービス横断)",
        "構成管理: Azure App Configuration + Key Vault",
        "サービスメッシュ: Istio on AKS (mTLS, トラフィック制御)",
    ])

    print("""
  設計ポイント:
  - API Management で認証(OAuth2/JWT), レート制限, API バージョニング
  - AKS + Istio でサービスメッシュ(mTLS, カナリアデプロイ, サーキットブレーカー)
  - Service Bus Topic/Subscription で非同期イベント駆動通信(Pub/Sub)
  - SAGA パターンで分散トランザクション管理
  - App Configuration で機能フラグ管理(フィーチャーフラグ)
  - Dapr on AKS で言語非依存のマイクロサービスビルディングブロックも選択肢
    """)

    # ================================================================
    # 13. Azure 独自の強み
    # ================================================================
    section("13. Azure 独自の強み")

    subsection("13-1. Entra ID / Microsoft 365 統合")

    print("""
  Azure の最大の差別化ポイントは Microsoft エコシステムとの統合:

  ▶ Entra ID (旧 Azure AD)
    - 世界で最も使われている企業向け ID プロバイダー
    - Microsoft 365, Dynamics 365, Power Platform と SSO
    - 条件付きアクセス: デバイス状態, 場所, リスクレベルで認証ポリシーを動的制御
    - Privileged Identity Management (PIM): 特権ロールの時限昇格
    - B2C: コンシューマー向け ID 管理(ソーシャルログイン, カスタム UI)

  ▶ Microsoft 365 連携の実例:
    - Teams Bot → Azure Bot Service + Azure OpenAI で社内 Q&A ボット
    - SharePoint → Azure Functions → Cosmos DB でドキュメント自動分類
    - Outlook → Logic Apps → Service Bus でメール駆動ワークフロー
    - Power Automate → Azure SQL で業務データ自動化(ローコード)

  ▶ エンタープライズで Azure が選ばれる理由:
    - 既に Microsoft 365 を使っている → Entra ID でシームレスな SSO
    - Active Directory (オンプレ) → Entra ID Connect でハイブリッド ID
    - Windows Server ワークロード → Azure VM + Azure Hybrid Benefit (ライセンス持込割引)
    """)

    subsection("13-2. ハイブリッドクラウド: Azure Arc")

    print("""
  ▶ Azure Arc とは
    - オンプレミス, エッジ, 他クラウドのリソースを Azure Resource Manager で統合管理
    - 「Azure の管理プレーンを外に広げる」コンセプト

  ▶ Azure Arc 対応リソース:
    - Arc-enabled Servers: オンプレ/他クラウド VM を Azure から管理(ポリシー, 監視, Update)
    - Arc-enabled Kubernetes: 任意の K8s クラスタを Azure から管理(GitOps, Policy)
    - Arc-enabled Data Services: SQL Managed Instance, PostgreSQL をどこでも実行
    - Arc-enabled App Services: App Service, Functions をどこでも実行(プレビュー)

  ▶ ユースケース:
    - 金融機関: 規制でオンプレ必須だが、Azure Policy で統一ガバナンス
    - 製造業: エッジ(工場)で推論実行、Azure で学習(ML パイプライン)
    - マルチクラウド: AWS/GCP の VM も Azure Portal から一元監視

  ▶ 料金:
    - Arc-enabled Servers: 無料(管理機能)。Defender 等の追加サービスは有料
    - Arc-enabled Kubernetes: コントロールプレーン無料。GitOps 等の拡張機能は追加課金
    """)

    subsection("13-3. Azure OpenAI Service の差別化")

    print("""
  ▶ OpenAI 直接利用 vs Azure OpenAI の違い:

    ┌──────────────────┬─────────────────────┬─────────────────────┐
    │ 項目             │ OpenAI 直接          │ Azure OpenAI        │
    ├──────────────────┼─────────────────────┼─────────────────────┤
    │ データの地理的制御│ 制御困難             │ リージョン選択可能   │
    │ VNet 統合        │ 不可                 │ Private Endpoint 対応│
    │ SLA              │ なし                 │ 99.9% SLA           │
    │ コンテンツフィルタ│ 基本的               │ カスタマイズ可能     │
    │ Managed Identity │ 不可                 │ 対応(APIキー不要)   │
    │ 責任共有モデル    │ OpenAI のみ          │ Microsoft 責任範囲  │
    │ 監査ログ         │ 限定的               │ Azure Monitor 統合  │
    │ PTU(予約容量)    │ なし                 │ あり(安定スループット)│
    │ GDPR/HIPAA 等    │ 限定的               │ Microsoft 準拠証明  │
    └──────────────────┴─────────────────────┴─────────────────────┘

  ▶ Azure OpenAI + Azure AI Search で RAG パターン:
    1. ドキュメント → Azure AI Search にインデックス作成(ベクトル検索対応)
    2. ユーザークエリ → AI Search でセマンティック検索
    3. 検索結果 + クエリ → Azure OpenAI に送信
    4. GPT が検索結果に基づいて回答生成(ハルシネーション低減)

  ▶ On Your Data 機能:
    - Azure Portal から GUI で RAG 構築が可能
    - Blob Storage, AI Search, Cosmos DB をデータソースとして接続
    - Azure OpenAI Studio でノーコードで構築→API として公開
    """)

    # ================================================================
    # 14. 面接問題
    # ================================================================
    section("14. 面接問題 (System Design with Azure)")

    subsection("問題1: グローバル E コマースプラットフォーム")

    print("""
  問題:
    月間1億PV、日本・北米・欧州にユーザーがいるECサイトを
    Azure で設計せよ。要件:
    - 全リージョンで100ms以内のレスポンス
    - 在庫管理の整合性保証
    - ブラックフライデー等のトラフィックスパイク対応
    - PCI DSS 準拠

  解答のポイント:

  ▶ グローバルトラフィック分散:
    - Azure Front Door でエニーキャスト → 最寄りリージョンにルーティング
    - 静的コンテンツは Front Door 組込 CDN でキャッシュ

  ▶ アプリケーション層:
    - 各リージョンに AKS クラスタ(or App Service)をデプロイ
    - API Management でレート制限, OAuth2 認証
    - Azure Cache for Redis でセッション/カタログキャッシュ(Geo レプリケーション)

  ▶ データ層:
    - 商品カタログ: Cosmos DB (Session 整合性, マルチリージョン読取)
    - 在庫管理: Cosmos DB (Strong 整合性, 単一書込リージョン)
      → Strong にすると書込リージョン以外での読取レイテンシが増加
      → 代替案: 在庫は Azure SQL Database + 読取レプリカ、在庫予約は楽観的ロック
    - 注文履歴: Azure SQL Database (トランザクション保証)
    - 検索: Azure AI Search (商品検索, ファセット, オートコンプリート)

  ▶ 非同期処理:
    - 注文確定 → Service Bus Topic → 在庫更新, 決済, 通知の各 Subscriber
    - SAGA パターンで分散トランザクション(補償トランザクション)

  ▶ スパイク対応:
    - AKS の Cluster Autoscaler + HPA
    - Cosmos DB Autoscale (最大 RU/s 設定)
    - Event Hubs でイベントバッファリング

  ▶ セキュリティ (PCI DSS):
    - Front Door WAF で OWASP Top 10 防御
    - Private Endpoint で DB/Cache へのアクセス制限
    - Key Vault で暗号鍵管理 + Managed Identity
    - Defender for Cloud でコンプライアンススコア監視
    - Log Analytics で監査ログ一元管理
    """)

    subsection("問題2: リアルタイム IoT データ分析基盤")

    print("""
  問題:
    100万台の IoT デバイスから毎秒10万メッセージを受信し、
    リアルタイムで異常検知 + 長期分析を行うプラットフォームを設計せよ。

  解答のポイント:

  ▶ デバイス接続 & データ取込:
    - Azure IoT Hub (デバイス管理, 双方向通信, デバイス認証)
      → or Event Hubs (純粋なイベント取込のみなら安い)
    - プロトコル: MQTT / AMQP / HTTPS

  ▶ リアルタイム処理 (Hot Path):
    - Event Hubs (IoT Hub 組込 Event Hub エンドポイント)
    - Stream Analytics:
      - タンブリングウィンドウ(1分)で集計
      - 異常検知関数(AnomalyDetection_SpikeAndDip)
      - 閾値超過 → Azure Functions → 通知(Teams/SMS)
    - 出力: Cosmos DB (最新状態) + Power BI (ダッシュボード)

  ▶ 長期保存 & バッチ分析 (Cold Path):
    - Event Hubs Capture → Data Lake Storage Gen2 (Parquet 形式)
    - Synapse Spark Pool で日次バッチ集計
    - Synapse 専用 SQL Pool で長期分析クエリ
    - Databricks で ML モデル学習(予知保全)

  ▶ スケーリング:
    - Event Hubs: 32+ パーティション (毎秒10万メッセージ対応)
    - Stream Analytics: SU 自動スケール
    - Cosmos DB: Autoscale RU/s

  ▶ 監視:
    - Azure Monitor メトリクス(Event Hubs ラグ, Stream Analytics 遅延)
    - Application Insights(Functions エラー追跡)
    - アラート → Action Group → PagerDuty/Teams
    """)

    subsection("問題3: エンタープライズ生成 AI (RAG) プラットフォーム")

    print("""
  問題:
    社内ドキュメント(10万件)を検索し、Azure OpenAI で回答を生成する
    RAG (Retrieval-Augmented Generation) システムを設計せよ。
    要件: 社外にデータを出さない、監査ログ必須、1000人同時利用。

  解答のポイント:

  ▶ ドキュメント取込パイプライン:
    - ソース: SharePoint, Blob Storage, Azure SQL
    - Azure AI Document Intelligence (旧 Form Recognizer) で PDF/画像からテキスト抽出
    - Data Factory でスケジュール取込 → Blob Storage (ランディング)
    - Azure Functions でチャンク分割 + エンベディング生成
      (Azure OpenAI text-embedding-ada-002 / text-embedding-3-large)

  ▶ 検索インデックス:
    - Azure AI Search:
      - ベクトルフィールド + キーワードフィールド(ハイブリッド検索)
      - セマンティックランカーで精度向上
      - インデクサーで Blob Storage から自動取込可能
    - インデックスサイズ: Standard S1 (15M docs, 25GB)

  ▶ 推論 API:
    - Azure OpenAI (GPT-4o) on Azure Functions or App Service
    - システムプロンプトで「検索結果のみに基づいて回答」を指示
    - PTU (Provisioned Throughput Unit) で1000人同時利用に安定スループット確保

  ▶ セキュリティ:
    - 全サービスを VNet + Private Endpoint で閉域構成
    - Entra ID 認証 + Managed Identity (API キーなし)
    - Key Vault でシークレット管理
    - Azure OpenAI のコンテンツフィルタリング設定
    - Log Analytics で全リクエストの監査ログ

  ▶ パフォーマンス:
    - Azure Cache for Redis でプロンプトキャッシュ(同一質問の回答キャッシュ)
    - Semantic Cache: エンベディングの類似度で近い質問のキャッシュヒット

  ▶ コスト最適化:
    - PTU vs トークン課金のブレークイーブン分析
    - 不要なドキュメントの除外(インデックスサイズ削減)
    - レスポンスの max_tokens 制限
    """)

    # ================================================================
    # 15. Azure 認定資格ロードマップ
    # ================================================================
    section("15. Azure 認定資格ロードマップ")

    print("""
  Azure 認定資格の推奨学習パス:

  ▶ 基礎レベル:
    AZ-900: Azure Fundamentals
    → クラウド概念、Azure サービス概要、料金/SLA
    → 非エンジニアにも推奨

  ▶ アソシエイトレベル(実務者向け):
    AZ-104: Azure Administrator Associate
    → ID管理、ストレージ、ネットワーク、コンピュート管理
    → インフラエンジニア向け

    AZ-204: Azure Developer Associate
    → App Service, Functions, Cosmos DB, Storage, 認証
    → 開発者向け

    AZ-500: Azure Security Engineer Associate
    → Entra ID, Key Vault, Defender, ネットワークセキュリティ
    → セキュリティエンジニア向け

  ▶ エキスパートレベル:
    AZ-305: Azure Solutions Architect Expert (AZ-104 前提)
    → 設計パターン、HA/DR、コスト最適化、移行戦略
    → アーキテクト向け。本カタログの内容が直結

    AZ-400: DevOps Engineer Expert (AZ-104 or AZ-204 前提)
    → CI/CD, IaC, 監視, フィードバックループ

  ▶ スペシャリスト:
    DP-900 → DP-203: Data Engineer (Synapse, Data Factory, Databricks)
    AI-900 → AI-102: AI Engineer (Cognitive Services, Azure OpenAI)
    """)

    # ================================================================
    # 16. コスト最適化のベストプラクティス
    # ================================================================
    section("16. コスト最適化のベストプラクティス")

    print("""
  ▶ 1. 適切な SKU 選択:
    - 開発/テスト環境: Dev/Test 料金(最大55%割引, MSDN サブスクリプション)
    - VM: B シリーズ(バースト可能)を開発環境に使用
    - SQL Database: サーバーレスティア(使用時のみ課金, 自動一時停止)

  ▶ 2. 予約とコミットメント:
    - Reserved Instances (VM, SQL DB, Cosmos DB): 1年で~36%, 3年で~57%割引
    - Azure Savings Plan: コンピュートサービス横断で割引(VM, App Service, Functions Premium)
    - Cosmos DB Reserved Capacity: RU/s を予約して割引

  ▶ 3. 自動スケーリングと自動停止:
    - 開発VM の自動シャットダウン(Azure Automation or DevTest Labs)
    - AKS Cluster Autoscaler + HPA
    - SQL Database サーバーレス自動一時停止
    - Cosmos DB Autoscale(最大RU/s設定, 使用量に応じてスケール)

  ▶ 4. ストレージ最適化:
    - Blob ライフサイクル管理(Hot→Cool→Archive 自動移行)
    - 不要なスナップショット/ディスクの定期削除
    - Log Analytics データ保持期間の最適化(90日超はArchiveティアに)

  ▶ 5. 監視と可視化:
    - Azure Cost Management + Billing (無料)
    - 予算アラート設定(予算の80%, 100%で通知)
    - Azure Advisor のコスト推奨事項を定期レビュー
    - タグベースのコスト配分(部門, プロジェクト, 環境)

  ▶ 6. ネットワークコスト:
    - 同一リージョン内通信は受信無料、送信もVNet内無料
    - クロスリージョン/インターネット送信はGB課金
    - CDN/Front Door でオリジンへのリクエスト削減
    - Private Endpoint はデータ処理課金あり(注意)
    """)

    task("Azure Cost Management で「月末予測コストが予算の80%を超えたら"
         "Teams に通知」するアラートを設定してみよう。"
         "Action Group + Logic Apps or Azure Monitor アラートで構築する。")

    # ================================================================
    # まとめ
    # ================================================================
    section("まとめ: Azure サービス選択の指針")

    print("""
  1. コンピュート: 抽象度で選ぶ
     VM(フル制御) → AKS(K8s) → App Service(PaaS) → Functions(サーバーレス)

  2. ストレージ: データの性質で選ぶ
     オブジェクト→Blob / ファイル共有→Files / ブロック→Managed Disks / 分析→ADLS Gen2

  3. データベース: ワークロードで選ぶ
     OLTP(RDB)→SQL Database / グローバル NoSQL→Cosmos DB / キャッシュ→Redis

  4. メッセージング: 通信パターンで選ぶ
     シンプルキュー→Queue Storage / エンタープライズ→Service Bus / ストリーム→Event Hubs

  5. セキュリティ: ゼロトラストの3原則
     明示的に検証(Entra ID) → 最小権限(RBAC) → 侵害を想定(Defender for Cloud)

  6. Azure を選ぶべき状況:
     - Microsoft 365 を既に使っている(Entra ID 統合)
     - Windows Server / .NET ワークロード(Azure Hybrid Benefit)
     - ハイブリッドクラウド要件(Azure Arc)
     - エンタープライズ LLM 活用(Azure OpenAI + 閉域ネットワーク)
     - エンタープライズ契約(EA)で大幅割引が適用される

  7. Azure を選ばない状況:
     - AWS/GCP のエコシステムが既に確立(移行コスト大)
     - BigQuery レベルのサーバーレス DWH が必要(→GCP)
     - Lambda@Edge のようなエッジコンピューティング(→AWS)
    """)

    print(f"\n{SEP}")
    print("  Azure Services Catalog 完了")
    print(f"{SEP}\n")


if __name__ == "__main__":
    main()
