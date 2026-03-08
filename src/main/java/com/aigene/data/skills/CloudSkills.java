package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class CloudSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("aws_architecture")
                .categoryId("CLOUD")
                .name("AWSアーキテクチャ設計")
                .nameEn("AWS Architecture Design")
                .shortDescription("Well-Architectedフレームワークに基づくAWSシステム設計")
                .overview("""
                    AWSの個別サービス知識を超え、システム全体を設計する能力。
                    AWS Well-Architectedフレームワーク（信頼性・セキュリティ・コスト効率・
                    パフォーマンス・運用優秀性・持続可能性）の6柱に沿って設計する。
                    Solutions Architect Professional レベルの設計判断力が目標。
                    """)
                .whyItMatters("""
                    個別サービスを知っているだけでは設計者になれない。
                    「なぜECSでなくLambdaか」「なぜRDSでなくDynamoDBか」を
                    要件から即答できる設計力がシニアエンジニア・PMに求められる。
                    """)
                .howToLearn("""
                    1. AWS Well-Architected Framework を通読（無料PDF）
                    2. AWS Solutions Architect Associate → Professional の順に取得
                    3. AWS Architecture Centerのリファレンスアーキテクチャを読む
                    4. 実際のシステムをWhiteboardでAWSで設計する練習
                    """)
                .aiEraRelevance("""
                    BedrockやSageMakerなどAI/MLサービスが急拡大。
                    LLM活用システムのインフラ設計でAWS設計力は直結する。
                    """)
                .keyTopics(List.of(
                    "Well-Architectedフレームワーク6柱",
                    "ネットワーク設計（VPC・サブネット・セキュリティグループ）",
                    "高可用性設計（Multi-AZ・Auto Scaling）",
                    "マネージドサービス選定基準",
                    "AWS Bedrockを用いたAI基盤設計"
                ))
                .prerequisites(List.of("AWS基礎（EC2/S3/RDS）", "ネットワーク基礎"))
                .nextSkillIds(List.of("cloud_native", "finops"))
                .resources(List.of(
                    "AWS Well-Architected Framework (公式・無料)",
                    "AWS Solutions Architect 試験対策",
                    "書籍: 「Amazon Web Services 基礎からのネットワーク&サーバー構築」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.CRITICAL)
                .estimatedHours(120)
                .build(),

            Skill.builder("gcp_advanced")
                .categoryId("CLOUD")
                .name("GCP深化（BigQuery・Vertex AI）")
                .nameEn("GCP Advanced")
                .shortDescription("BigQueryによるデータ分析とVertex AIによるML基盤の活用")
                .overview("""
                    GCPの強みはデータ・AI領域。BigQueryはPB規模のデータをSQLで分析できる
                    フルマネージドDWH。Vertex AIはGoogleのML基盤サービスで、
                    モデルのトレーニング〜デプロイ〜監視を統合管理できる。
                    すでにGCP基礎があるなら、この二つを深掘りするのが最短ルート。
                    """)
                .whyItMatters("""
                    データドリブンな意思決定を実現するためのGCP活用は、
                    PMにとってもKPI分析・実験評価で直接役立つ。
                    Gemini APIはVertex AI経由で利用するためAI活用にも必須。
                    """)
                .howToLearn("""
                    1. BigQueryのハンズオン（Google Cloud Skills Boost）
                    2. BigQuery MLでSQLだけでMLモデルを作る
                    3. Vertex AI Workbenchで既存Pythonコードを動かす
                    4. GCP Professional Data Engineer の試験範囲を学ぶ
                    """)
                .keyTopics(List.of(
                    "BigQueryのパーティション・クラスタリング設計",
                    "BigQuery ML（SQLによるML）",
                    "Vertex AI Pipeline",
                    "Cloud Composerによるワークフロー管理",
                    "Gemini API (Vertex AI経由)"
                ))
                .prerequisites(List.of("GCP基礎", "SQL中級"))
                .nextSkillIds(List.of("data_pipeline", "mlops"))
                .resources(List.of(
                    "Google Cloud Skills Boost (公式ハンズオン)",
                    "BigQuery Documentation (公式)",
                    "書籍: 「BigQuery 詳細ガイド」"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("cloud_native")
                .categoryId("CLOUD")
                .name("クラウドネイティブパターン")
                .nameEn("Cloud Native Patterns")
                .shortDescription("コンテナ・マイクロサービス・サーバーレスを組み合わせたクラウドネイティブ設計")
                .overview("""
                    クラウドネイティブとは、クラウドの特性（弾力性・マネージドサービス・
                    スケーラビリティ）を最大限活用するアーキテクチャスタイル。
                    CNCF（Cloud Native Computing Foundation）が定義する
                    コンテナ・マイクロサービス・動的オーケストレーション・CI/CDが4本柱。
                    """)
                .whyItMatters("""
                    クラウド上で動くモダンシステムの標準設計スタイル。
                    「なぜKubernetesを使うか」「サーバーレスとコンテナをどう使い分けるか」を
                    答えられないと設計議論に参加できない。
                    """)
                .howToLearn("""
                    1. 「クラウドネイティブパターン」（Manning）を読む
                    2. CNCFのTrail Map（技術習得ロードマップ）に従って学ぶ
                    3. 小さなアプリをECS/Cloud Run → EKSに移行する実験
                    4. 12 Factor App原則をすべて理解する
                    """)
                .keyTopics(List.of(
                    "12 Factor App原則",
                    "コンテナ・Kubernetes基礎",
                    "サービスメッシュ（Istio/Linkerd）",
                    "サーバーレス（Lambda/Cloud Functions/Cloud Run）",
                    "GitOps（ArgoCD）"
                ))
                .prerequisites(List.of("Docker", "Kubernetes基礎", "AWSまたはGCP基礎"))
                .resources(List.of(
                    "CNCF Trail Map (公式)",
                    "The Twelve-Factor App (12factor.net)",
                    "書籍: 「Cloud Native Patterns」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("finops")
                .categoryId("CLOUD")
                .name("FinOps・クラウドコスト最適化")
                .nameEn("FinOps")
                .shortDescription("クラウドコストの可視化・最適化・ガバナンスの実践")
                .overview("""
                    FinOpsとはFinance + Devの組み合わせで、クラウドコストを組織全体で
                    可視化・最適化・予算管理する文化とプラクティスのこと。
                    コスト配賦・リソース最適化（Reserved Instance/Savings Plans）・
                    タグ付け戦略・予算アラートが主な実践内容。
                    """)
                .whyItMatters("""
                    クラウドの請求書が予算の3倍になった、という話はどの会社でも起きる。
                    PMとして「この機能追加でコストがどう変わるか」を語れないと
                    ビジネス判断ができない。PMに最も求められるクラウドスキルのひとつ。
                    """)
                .howToLearn("""
                    1. AWS Cost Explorerを使い倒して自社/個人のコスト分析
                    2. FinOps Foundation の FinOps Certified Practitioner を取得
                    3. Infracost でIaCのコスト変化を事前検出する
                    4. Spot Instanceの使い方とリスクを理解する
                    """)
                .keyTopics(List.of(
                    "クラウドコスト配賦とタグ付け戦略",
                    "Reserved Instance / Savings Plans",
                    "Spot / Preemptible Instance活用",
                    "コスト異常検知・アラート",
                    "FinOps文化の組織導入"
                ))
                .prerequisites(List.of("AWSまたはGCP基礎"))
                .resources(List.of(
                    "FinOps Foundation (finops.org)",
                    "AWS Cost Optimization Hub",
                    "Infracost (オープンソースツール)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.MEDIUM)
                .estimatedHours(30)
                .build(),

            Skill.builder("serverless")
                .categoryId("CLOUD")
                .name("サーバーレスアーキテクチャ")
                .nameEn("Serverless Architecture")
                .shortDescription("Lambda/Cloud Functionsを使ったイベント駆動型サーバーレス設計")
                .overview("""
                    サーバーレスとはインフラ管理をクラウドプロバイダーに完全委譲し、
                    コードのみに集中する開発スタイル。AWS Lambda・Google Cloud Functions・
                    API Gatewayを組み合わせてAPIやバッチ処理を構築する。
                    コールドスタート・タイムアウト・べき等性などの注意点がある。
                    """)
                .whyItMatters("""
                    小〜中規模のAPIやイベント処理では、EC2/ECSより圧倒的にコスト効率が良い。
                    AIエージェントのトリガーや非同期処理にも多用される。
                    適切に使えば運用コストを劇的に削減できる。
                    """)
                .howToLearn("""
                    1. AWS Lambda + API Gatewayで簡単なAPIを作る
                    2. Serverless Frameworkまたは AWS SAMで管理する
                    3. コールドスタート問題とProvisioned Concurrencyを理解する
                    4. EventBridge・SQS・SNSとLambdaを組み合わせたイベント設計
                    """)
                .keyTopics(List.of(
                    "AWS Lambda / Cloud Functions の動作原理",
                    "コールドスタートと対策",
                    "API Gateway設計",
                    "イベントソース連携（SQS/SNS/EventBridge）",
                    "Serverless Framework / AWS SAM"
                ))
                .prerequisites(List.of("AWSまたはGCP基礎", "Python基礎"))
                .resources(List.of(
                    "AWS Lambda Documentation",
                    "Serverless Framework (serverless.com)",
                    "書籍: 「AWS Lambda実践ガイド」"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(50)
                .build()
        );
    }
}
