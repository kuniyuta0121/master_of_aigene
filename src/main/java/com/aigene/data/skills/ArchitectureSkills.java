package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class ArchitectureSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("system_design")
                .categoryId("ARCHITECTURE")
                .name("システム設計")
                .nameEn("System Design")
                .shortDescription("大規模システムのスケーラビリティ・信頼性・可用性を実現する設計手法")
                .overview("""
                    システム設計とは、高トラフィック・大データ量・高可用性を要求するシステムを
                    どう構築するかを考える能力。ロードバランサー・CDN・データベースシャーディング・
                    キャッシュ設計・非同期処理・レートリミットなど様々なパターンを組み合わせる。
                    FAANG系企業の面接でも必須の技術項目。
                    """)
                .whyItMatters("""
                    シニアエンジニアやアーキテクトに最も求められる判断力。
                    「1億ユーザーのシステムをどう設計するか」という問いに答えられないと
                    技術的意思決定の場に参加できない。PMとしても要件定義でトレードオフを理解するために必要。
                    """)
                .howToLearn("""
                    1. 「System Design Interview」(Alex Xu) を全章読む
                    2. Googleのシステム設計事例（MapReduce・Bigtableの論文）を読む
                    3. Grokking the System Design Interview コースを受講
                    4. 実際のシステム（Twitter・Uber・YouTube）の設計を自分で考えてから記事を読む
                    """)
                .keyTopics(List.of(
                    "スケーラビリティ（水平/垂直スケーリング）",
                    "データベース設計（シャーディング・レプリケーション）",
                    "キャッシュ設計（Redis・CDN・ブラウザキャッシュ）",
                    "非同期処理とメッセージキュー",
                    "CAP定理と一貫性モデル"
                ))
                .prerequisites(List.of("データベース基礎", "ネットワーク基礎", "クラウド基礎"))
                .nextSkillIds(List.of("microservices", "event_driven"))
                .resources(List.of(
                    "書籍: 「System Design Interview Vol.1,2」(Alex Xu)",
                    "ByteByteGo Newsletter (byte-by-byte)",
                    "Grokking the System Design Interview (educative.io)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.CRITICAL)
                .estimatedHours(100)
                .build(),

            Skill.builder("microservices")
                .categoryId("ARCHITECTURE")
                .name("マイクロサービスアーキテクチャ")
                .nameEn("Microservices Architecture")
                .shortDescription("サービス分割設計・サービス間通信・データ整合性の実現パターン")
                .overview("""
                    マイクロサービスとは、大きなシステムを独立してデプロイ可能な小さな
                    サービス群に分割するアーキテクチャスタイル。
                    サービス境界（Bounded Context）の設計・API Gateway・
                    サービス間通信（REST/gRPC/メッセージング）・分散トランザクションが主な課題。
                    モノリスが先かマイクロサービスが先かの判断も重要。
                    """)
                .whyItMatters("""
                    中〜大規模プロダクトの標準的なアーキテクチャスタイル。
                    間違った分割をすると「分散モノリス」という最悪の状態になる。
                    アーキテクトやテックリードに必須の設計判断力。
                    """)
                .howToLearn("""
                    1. 「Building Microservices」(Sam Newman) を読む
                    2. モノリスをどう分割するか「Strangler Fig Pattern」を学ぶ
                    3. gRPCでサービス間通信を実装する
                    4. Sagaパターンで分散トランザクションを実装する
                    """)
                .keyTopics(List.of(
                    "Bounded Context（境界付きコンテキスト）の設計",
                    "API Gateway パターン",
                    "サービス間通信（REST vs gRPC vs メッセージング）",
                    "Sagaパターン（分散トランザクション）",
                    "サービスメッシュ（Istio）"
                ))
                .prerequisites(List.of("システム設計", "Docker", "REST API設計"))
                .resources(List.of(
                    "書籍: 「Building Microservices」2nd ed. (Sam Newman)",
                    "microservices.io (Chris Richardson のパターンカタログ)",
                    "書籍: 「マイクロサービスパターン」（Manning）"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("event_driven")
                .categoryId("ARCHITECTURE")
                .name("イベント駆動アーキテクチャ")
                .nameEn("Event-Driven Architecture")
                .shortDescription("イベントを中心にシステムを非同期・疎結合に設計するパターン")
                .overview("""
                    イベント駆動アーキテクチャ（EDA）では、システム内のビジネス上の出来事を
                    「イベント」として発行し、それを受け取ったサービスが自律的に反応する。
                    Event Sourcing（状態をイベントの蓄積として表現）・CQRS（コマンドとクエリの分離）・
                    Choreographyによるサービス協調が主要パターン。
                    """)
                .whyItMatters("""
                    AIエージェントのトリガー・リアルタイム処理・マイクロサービスの疎結合化に
                    イベント駆動は最適。Kafkaの普及でこのパターンが急速に広まっている。
                    非同期・非同期混在システムの設計に不可欠な概念。
                    """)
                .howToLearn("""
                    1. Event SourcingとCQRSの概念を「Implementing DDD」で学ぶ
                    2. KafkaでProducer/Consumerを実装してイベント駆動を体感
                    3. EventBridge / CloudEvents でイベントスキーマを設計
                    4. Sagaパターン（Choreographyスタイル）でEC注文フローを設計
                    """)
                .keyTopics(List.of(
                    "Event Sourcingパターン",
                    "CQRS（コマンドクエリ責務分離）",
                    "Choreography vs Orchestration",
                    "べき等性（Idempotency）の設計",
                    "Dead Letter Queue（DLQ）の設計"
                ))
                .prerequisites(List.of("マイクロサービスアーキテクチャ", "ストリーム処理基礎"))
                .resources(List.of(
                    "書籍: 「Designing Event-Driven Systems」(Ben Stopford・無料PDF)",
                    "CloudEvents Specification (cloudevents.io)",
                    "書籍: 「Enterprise Integration Patterns」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(70)
                .build(),

            Skill.builder("ddd")
                .categoryId("ARCHITECTURE")
                .name("ドメイン駆動設計（DDD）")
                .nameEn("Domain-Driven Design")
                .shortDescription("複雑なビジネスロジックをドメインモデルで表現する設計手法")
                .overview("""
                    DDDはビジネスの専門知識（ドメイン知識）をソフトウェアの設計に直接反映する手法。
                    ユビキタス言語・Bounded Context・エンティティ・値オブジェクト・
                    集約・ドメインサービス・リポジトリが主要パターン。
                    マイクロサービスの境界設計にも直接活用できる。
                    """)
                .whyItMatters("""
                    複雑なビジネスロジックをコードに正確に反映できないと、
                    バグが増え保守性が下がる。PMが「要件が変わった」と言ったとき
                    DDDを理解したエンジニアは変更箇所が明確に分かる。
                    """)
                .howToLearn("""
                    1. 「エリック・エバンスのドメイン駆動設計」（Blue Book）を読む
                    2. 「実践ドメイン駆動設計」（IDDD）でより実践的な内容を学ぶ
                    3. 自分の業務ドメインでBounded Contextマッピングを作成
                    4. 集約（Aggregate）設計の原則を実コードで実践
                    """)
                .keyTopics(List.of(
                    "ユビキタス言語（開発者とビジネスの共通言語）",
                    "Bounded Context とコンテキストマップ",
                    "エンティティ・値オブジェクト・集約の設計",
                    "ドメインサービス・ドメインイベント",
                    "DDDとマイクロサービスの境界設計への応用"
                ))
                .prerequisites(List.of("オブジェクト指向設計", "デザインパターン"))
                .resources(List.of(
                    "書籍: 「ドメイン駆動設計」(Eric Evans)",
                    "書籍: 「実践ドメイン駆動設計」(Vaughn Vernon)",
                    "DDD Community (dddcommunity.org)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("api_design")
                .categoryId("ARCHITECTURE")
                .name("API設計")
                .nameEn("API Design")
                .shortDescription("使いやすく変更に強いREST・gRPC・GraphQL APIの設計原則")
                .overview("""
                    APIは異なるシステム・チームを繋ぐ契約（Contract）。
                    RESTfulな設計原則・OpenAPI仕様によるドキュメント化・
                    gRPCによるパフォーマンス重視の内部API・GraphQLによる柔軟なクライアント対応、
                    それぞれの特性と使い分けを理解する必要がある。
                    APIバージョニング・後方互換性の維持も重要。
                    """)
                .whyItMatters("""
                    悪いAPI設計はシステム全体の技術的負債になる。
                    「使いにくいAPI」はフロントエンドやパートナー連携のコストを増やす。
                    PMとして機能開発のAPIを承認する立場でも理解が必要。
                    """)
                .howToLearn("""
                    1. 「Web API: The Good Parts」を読む
                    2. OpenAPI(Swagger)でAPIドキュメントをコードから生成する
                    3. gRPCでシンプルなサービス間通信を実装
                    4. GraphQLスキーマを設計してN+1問題を解決する
                    """)
                .keyTopics(List.of(
                    "RESTful設計原則（リソース設計・HTTPメソッド・ステータスコード）",
                    "OpenAPI（Swagger）仕様",
                    "gRPC・Protocol Buffers",
                    "GraphQL スキーマ設計・DataLoader",
                    "APIバージョニング戦略"
                ))
                .prerequisites(List.of("HTTP基礎", "プログラミング基礎"))
                .resources(List.of(
                    "書籍: 「Web API: The Good Parts」(水野貴明)",
                    "OpenAPI Specification (swagger.io/docs)",
                    "gRPC Documentation (grpc.io)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build()
        );
    }
}
