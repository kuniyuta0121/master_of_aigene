package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class DataEngineeringSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("sql_advanced")
                .categoryId("DATA_ENG")
                .name("SQL高度活用")
                .nameEn("Advanced SQL")
                .shortDescription("ウィンドウ関数・CTEを使った高度なSQLと実行計画の最適化")
                .overview("""
                    基本的なSELECT/JOIN を超えた高度なSQL技術。
                    ウィンドウ関数（ROW_NUMBER/RANK/LAG/LEAD）・CTE（共通テーブル式）・
                    サブクエリ最適化・EXPLAIN ANALYZEによる実行計画チューニングが中心。
                    BigQuery/Redshift/Snowflakeなどモダンなデータウェアハウスでも同様に使える。
                    """)
                .whyItMatters("""
                    データを自分で分析できるエンジニアとPMは圧倒的に意思決定が速い。
                    「データ基盤チームに依頼してから2週間後に結果が来る」状態から脱却できる。
                    AI/MLの特徴量エンジニアリングにも高度なSQLが必要。
                    """)
                .howToLearn("""
                    1. Mode Analytics SQL Tutorial（ウィンドウ関数が充実）
                    2. LeetCode DatabaseセクションでSQLパズルを解く
                    3. 実業務のクエリを書き直してEXPLAIN ANALYZEで比較
                    4. BigQueryで実際のデータセットを分析する
                    """)
                .keyTopics(List.of(
                    "ウィンドウ関数（ROW_NUMBER, RANK, LAG, LEAD, SUM OVER）",
                    "CTE（WITH句）と再帰CTE",
                    "実行計画（EXPLAIN ANALYZE）の読み方",
                    "インデックス設計と選択性",
                    "BigQuery/Redshiftの方言とパーティション活用"
                ))
                .prerequisites(List.of("SQL基礎（SELECT/JOIN/GROUP BY）"))
                .nextSkillIds(List.of("data_pipeline", "nosql"))
                .resources(List.of(
                    "Mode SQL Tutorial (mode.com/sql-tutorial)",
                    "LeetCode Database Problems",
                    "Use The Index, Luke! (use-the-index-luke.com)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build(),

            Skill.builder("nosql")
                .categoryId("DATA_ENG")
                .name("NoSQLデータベース")
                .nameEn("NoSQL Databases")
                .shortDescription("DynamoDB・MongoDB・Redisの特性と使い分け、設計パターン")
                .overview("""
                    NoSQLはRDBMSの補完ではなく別の問題を解くためのツール。
                    DynamoDB（キー-バリュー/ドキュメント・超低レイテンシ・スケーラブル）、
                    MongoDB（柔軟なスキーマ・複雑なクエリ）、
                    Redis（インメモリ・キャッシュ・セッション管理）がそれぞれ異なる用途を持つ。
                    """)
                .whyItMatters("""
                    全てをRDBMSで解こうとするとスケーラビリティで限界が来る。
                    適切なDB選択はシステム設計の核心で、面接・設計議論でも頻出。
                    DynamoDBはAWS上のシステムで最も使われるNoSQL。
                    """)
                .howToLearn("""
                    1. DynamoDB: AWS公式のDynamoDB設計パターン資料を読む
                    2. 単一テーブル設計（Single-Table Design）を実装する
                    3. Redisでセッション管理・キャッシュ・Pub/Subを実装
                    4. MongoDBのAggregation Pipelineを習得
                    """)
                .keyTopics(List.of(
                    "CAP定理とデータ整合性モデル",
                    "DynamoDB: パーティションキー設計・GSI・単一テーブル設計",
                    "Redis: データ構造（String/Hash/List/Set/Sorted Set）",
                    "MongoDB: スキーマ設計・Aggregation Pipeline",
                    "キャッシュ戦略（Cache-Aside / Write-Through）"
                ))
                .prerequisites(List.of("SQL基礎", "データ構造の理解"))
                .resources(List.of(
                    "DynamoDB Best Practices (AWS公式)",
                    "書籍: 「The DynamoDB Book」(Alex DeBrie)",
                    "Redis University (university.redis.io)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("data_pipeline")
                .categoryId("DATA_ENG")
                .name("データパイプライン（Airflow・dbt）")
                .nameEn("Data Pipeline")
                .shortDescription("Apache AirflowによるETLワークフロー管理とdbtによるデータ変換")
                .overview("""
                    データパイプラインはデータソースからDWHへのETL（抽出・変換・ロード）を
                    自動化する仕組み。Apache Airflowはワークフローをコードで定義し
                    スケジュール管理と依存関係を制御する。dbt（data build tool）は
                    SQL変換をGit管理可能なモジュールとして定義できる現代的なツール。
                    """)
                .whyItMatters("""
                    「毎朝手でCSVをDL→加工→アップロード」という作業を自動化する。
                    データ分析基盤の構築はML特徴量生成・KPIダッシュボード・意思決定の基盤。
                    データエンジニアリングの中心スキル。
                    """)
                .howToLearn("""
                    1. Airflow公式チュートリアルでDAGを作成
                    2. dbtのGetting Startedを完走しモデルを作る
                    3. 実際のAPIからデータを取得してDWH（BigQuery等）に流す
                    4. dbt testとdocumentationを設定する
                    """)
                .keyTopics(List.of(
                    "Airflow: DAG・Operator・Sensor・XCom",
                    "dbt: model・test・source・macro",
                    "ETLとELTの違い",
                    "データ品質管理（Great Expectations）",
                    "クラウドネイティブなパイプライン（Glue/Dataflow）"
                ))
                .prerequisites(List.of("SQL中級", "Python基礎", "クラウド基礎"))
                .resources(List.of(
                    "Apache Airflow Documentation (公式)",
                    "dbt Documentation (docs.getdbt.com)",
                    "書籍: 「Fundamentals of Data Engineering」(O'Reilly)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(70)
                .build(),

            Skill.builder("stream_processing")
                .categoryId("DATA_ENG")
                .name("ストリーム処理（Kafka）")
                .nameEn("Stream Processing")
                .shortDescription("Apache Kafkaによるリアルタイムデータストリームの設計と運用")
                .overview("""
                    ストリーム処理はデータをバッチではなくリアルタイムで処理する手法。
                    Apache Kafkaは高スループット・高耐久性の分散メッセージングシステムで、
                    マイクロサービス間の非同期通信・ログ集約・リアルタイム分析の基盤として使われる。
                    Kafka Streams・Flink・Spark Streamingで処理を記述する。
                    """)
                .whyItMatters("""
                    不正検知・リアルタイムレコメンド・IoTデータ処理など
                    「今すぐ」データが必要なユースケースに不可欠。
                    マイクロサービスのイベント駆動アーキテクチャの基盤にもなる。
                    """)
                .howToLearn("""
                    1. Docker ComposeでKafkaをローカル起動しProducer/Consumerを実装
                    2. Kafka Connectでデータベースのデータを流す
                    3. Kafka Streamsで簡単なストリーム処理を実装
                    4. コンシューマグループとオフセット管理を理解する
                    """)
                .keyTopics(List.of(
                    "Kafkaアーキテクチャ（Broker/Topic/Partition/Offset）",
                    "Producer・Consumer・コンシューマグループ",
                    "Kafka Connect（データソース連携）",
                    "Kafka Streams / Flink",
                    "スキーマレジストリ（Avro/Protobuf）"
                ))
                .prerequisites(List.of("分散システム基礎", "データパイプライン基礎"))
                .resources(List.of(
                    "Confluent Kafka Tutorial (confluent.io/learn)",
                    "書籍: 「Kafka: The Definitive Guide」(O'Reilly)",
                    "Redpanda (Kafkaの軽量代替、ローカル開発向け)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.MEDIUM)
                .estimatedHours(80)
                .build(),

            Skill.builder("data_lakehouse")
                .categoryId("DATA_ENG")
                .name("データレイクハウス")
                .nameEn("Data Lakehouse")
                .shortDescription("Delta Lake・Apache IcebergによるデータレイクとDWHの融合アーキテクチャ")
                .overview("""
                    データレイクハウスはデータレイク（安価・柔軟）とDWH（構造化・高速クエリ）の
                    良いところを組み合わせたアーキテクチャ。
                    Delta Lake（Databricks）・Apache Iceberg・Apache Hudiが主要フォーマット。
                    ACIDトランザクション・タイムトラベル・スキーマ進化が主な機能。
                    """)
                .whyItMatters("""
                    大規模データを安価なオブジェクトストレージ（S3/GCS）に格納しつつ
                    DWH並みのクエリ性能を得る現代的アーキテクチャ。
                    MLの学習データ管理にも使われ、データエンジニアの必須知識になりつつある。
                    """)
                .howToLearn("""
                    1. Delta LakeのPySparkチュートリアルを実施
                    2. Apache Icebergの公式ドキュメントでテーブルフォーマットを理解
                    3. AWS Glue + Icebergで小規模なデータレイクを構築
                    4. タイムトラベル機能でデータの過去状態を参照する
                    """)
                .keyTopics(List.of(
                    "Deltaフォーマット（ACID・タイムトラベル）",
                    "Apache Iceberg アーキテクチャ",
                    "データレイク設計（Bronze/Silver/Gold レイヤー）",
                    "Apache Spark基礎",
                    "カタログ管理（AWS Glue Catalog / Unity Catalog）"
                ))
                .prerequisites(List.of("データパイプライン", "SQL中級", "クラウド基礎"))
                .resources(List.of(
                    "Delta Lake Documentation (delta.io)",
                    "Apache Iceberg Documentation (iceberg.apache.org)",
                    "書籍: 「Delta Lake: The Definitive Guide」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.MEDIUM)
                .estimatedHours(60)
                .build()
        );
    }
}
