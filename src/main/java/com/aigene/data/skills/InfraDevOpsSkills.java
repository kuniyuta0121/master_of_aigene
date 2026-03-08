package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class InfraDevOpsSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("docker")
                .categoryId("INFRA_DEVOPS")
                .name("Docker・コンテナ化")
                .nameEn("Docker & Containerization")
                .shortDescription("アプリケーションのコンテナ化と効率的なDockerfile設計")
                .overview("""
                    Dockerはアプリケーションとその依存関係をコンテナとしてパッケージングし、
                    「どこでも同じように動く」環境を実現する技術。
                    Dockerfile設計・マルチステージビルド・Docker Composeによる
                    ローカル開発環境構築が基本スキルセット。
                    """)
                .whyItMatters("""
                    現代のバックエンド開発で避けて通れない標準技術。
                    「自分のPCでは動くのに本番で動かない」問題を根本解決する。
                    Kubernetesへの移行にも必須の前提知識。
                    """)
                .howToLearn("""
                    1. Dockerの公式チュートリアルをすべて実施
                    2. 既存PythonプロジェクトをDockerコンテナ化する
                    3. マルチステージビルドで本番イメージを最小化
                    4. Docker Composeで複数サービス（アプリ+DB+Redis）を管理
                    """)
                .keyTopics(List.of(
                    "Dockerfileの最適化（レイヤーキャッシュ・マルチステージ）",
                    "Docker Compose",
                    "コンテナネットワーク・ボリューム",
                    "Docker Hub / ECR へのイメージプッシュ",
                    "セキュリティ（非rootユーザー・イメージスキャン）"
                ))
                .prerequisites(List.of("Linux基礎", "コマンドライン操作"))
                .nextSkillIds(List.of("kubernetes", "cicd"))
                .resources(List.of(
                    "Docker公式ドキュメント (docs.docker.com)",
                    "書籍: 「Dockerコンテナ開発・環境構築の基本」",
                    "Play with Docker (ブラウザ上でDocker体験)"
                ))
                .difficulty(Difficulty.BEGINNER)
                .priority(Priority.CRITICAL)
                .estimatedHours(30)
                .build(),

            Skill.builder("kubernetes")
                .categoryId("INFRA_DEVOPS")
                .name("Kubernetes")
                .nameEn("Kubernetes")
                .shortDescription("コンテナオーケストレーションによる本番システムの運用管理")
                .overview("""
                    Kubernetesはコンテナのデプロイ・スケーリング・管理を自動化する
                    オープンソースのオーケストレーションシステム。
                    Pod・Deployment・Service・Ingressなどの基本リソースを理解し、
                    EKS/GKEなどマネージドKubernetesで本番運用するスキルが求められる。
                    """)
                .whyItMatters("""
                    中〜大規模システムのデファクトスタンダード。
                    AIワークロード（GPU Pod・推論サービス）の運用にも多用される。
                    テックリードやアーキテクトには設計判断力が必要。
                    """)
                .howToLearn("""
                    1. minikubeまたはKind でローカルK8s環境を構築
                    2. CKA（Certified Kubernetes Administrator）の学習範囲を網羅
                    3. HelmでアプリをK8sにデプロイする
                    4. HorizontalPodAutoscalerで自動スケーリングを設定
                    """)
                .keyTopics(List.of(
                    "Pod / Deployment / Service / Ingress",
                    "ConfigMap / Secret 管理",
                    "Helm チャート",
                    "HPA・VPA（自動スケーリング）",
                    "EKS / GKE マネージドK8s運用"
                ))
                .prerequisites(List.of("Docker", "Linux基礎", "YAML"))
                .nextSkillIds(List.of("cicd", "observability"))
                .resources(List.of(
                    "Kubernetes公式ドキュメント (kubernetes.io)",
                    "CKA試験対策コース (Udemy: Mumshad Mannambeth)",
                    "書籍: 「Kubernetes完全ガイド」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(100)
                .build(),

            Skill.builder("cicd")
                .categoryId("INFRA_DEVOPS")
                .name("CI/CDパイプライン")
                .nameEn("CI/CD Pipeline")
                .shortDescription("継続的インテグレーション・デリバリーによる開発サイクルの自動化")
                .overview("""
                    CI/CDとはコードコミットから本番デプロイまでを自動化する仕組み。
                    GitHub Actionsが最も普及しており、テスト→ビルド→コンテナ化→デプロイを
                    すべて自動化できる。GitOps（ArgoCD）と組み合わせると
                    Kubernetes環境への継続的デリバリーが実現できる。
                    """)
                .whyItMatters("""
                    「手動デプロイ」は品質事故の温床。CI/CDがないチームは
                    リリース頻度が下がり、バグ修正が遅くなる。
                    DevOps文化の核心でありPMとして開発速度を上げるために理解が必要。
                    """)
                .howToLearn("""
                    1. GitHub Actionsで既存プロジェクトのテスト自動化ワークフローを作成
                    2. DockerイメージビルドとECR/GCR へのpushを自動化
                    3. ArgoCD でGitOpsデプロイを設定
                    4. Dependabotで依存ライブラリの自動更新を有効化
                    """)
                .keyTopics(List.of(
                    "GitHub Actions ワークフロー設計",
                    "テスト・ビルド・Lintの自動化",
                    "コンテナイメージの自動ビルド・プッシュ",
                    "GitOps（ArgoCD/Flux）",
                    "セキュリティスキャン（Trivy・Snyk）の組み込み"
                ))
                .prerequisites(List.of("Git/GitHub", "Docker"))
                .nextSkillIds(List.of("iac", "observability"))
                .resources(List.of(
                    "GitHub Actions Documentation (公式)",
                    "ArgoCD Documentation (公式)",
                    "書籍: 「継続的デリバリー」(Jez Humble)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(50)
                .build(),

            Skill.builder("iac")
                .categoryId("INFRA_DEVOPS")
                .name("IaC（Infrastructure as Code）")
                .nameEn("Infrastructure as Code")
                .shortDescription("TerraformによるクラウドインフラのコードによるプロビジョニングとGitOps管理")
                .overview("""
                    IaCとはインフラ構成をコードで定義・管理する手法。
                    TerraformはAWS/GCP/Azureをまたいで使えるデファクトスタンダード。
                    Pulumiは一般プログラミング言語（Python/TypeScript）でIaCを書ける
                    新世代ツール。AWS CDKはPythonでAWSリソースを定義できる。
                    """)
                .whyItMatters("""
                    コンソールをポチポチした手動インフラ構築は再現性がなく、
                    レビューも困難。コードとしてGitで管理することで
                    インフラ変更の追跡・ロールバック・チームレビューが可能になる。
                    """)
                .howToLearn("""
                    1. Terraform Getting Startedチュートリアル（公式）を完走
                    2. 既存のAWS環境をTerraformに移行する
                    3. Terraform Cloud または S3バックエンドでstateを管理
                    4. TFLint・tfsecでコード品質・セキュリティをチェック
                    """)
                .keyTopics(List.of(
                    "Terraform基本構文（resource・variable・output・module）",
                    "stateファイル管理（remote backend）",
                    "Terraformモジュール設計",
                    "AWS CDK / Pulumiの位置付け",
                    "IaCのセキュリティスキャン"
                ))
                .prerequisites(List.of("AWSまたはGCP基礎", "Git/GitHub"))
                .resources(List.of(
                    "Terraform Documentation (developer.hashicorp.com)",
                    "書籍: 「Terraform: Up and Running」(Yevgeniy Brikman)",
                    "AWS CDK Workshop (公式)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("observability")
                .categoryId("INFRA_DEVOPS")
                .name("可観測性（Observability）")
                .nameEn("Observability")
                .shortDescription("メトリクス・ログ・トレースの三本柱で本番システムを透明化する")
                .overview("""
                    可観測性とは、システムの内部状態を外部出力（メトリクス・ログ・トレース）から
                    把握できる度合いのこと。Prometheus+GrafanaでKubernetesのメトリクスを可視化し、
                    OpenTelemetryで分散トレーシングを実装し、ELK Stackでログを集中管理するのが
                    現代的なオブザーバビリティスタック。
                    """)
                .whyItMatters("""
                    「障害を知るのがユーザーより遅い」状態を防ぐ。
                    LLMシステムの監視（レイテンシ・エラー率・コスト）にも応用できる。
                    SREになるためには必須スキル。
                    """)
                .howToLearn("""
                    1. Prometheus + Grafanaをローカルに構築しメトリクスを可視化
                    2. PythonアプリにOpenTelemetryを組み込んでトレース送信
                    3. CloudWatch / Cloud Monitoring でアラート設定
                    4. ダッシュボードとSLO（サービスレベル目標）を設定する
                    """)
                .keyTopics(List.of(
                    "メトリクス（Prometheus/CloudWatch）",
                    "ログ集中管理（ELK Stack/CloudWatch Logs）",
                    "分散トレーシング（OpenTelemetry/Jaeger）",
                    "SLI・SLO・エラーバジェット",
                    "アラート設計（ノイズを減らす）"
                ))
                .prerequisites(List.of("Kubernetes基礎", "クラウド基礎"))
                .resources(List.of(
                    "Prometheus Documentation (公式)",
                    "OpenTelemetry Documentation (公式)",
                    "書籍: 「Observability Engineering」(O'Reilly)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("sre")
                .categoryId("INFRA_DEVOPS")
                .name("SRE原則")
                .nameEn("Site Reliability Engineering")
                .shortDescription("Googleが確立したサービスの信頼性を工学的に高めるアプローチ")
                .overview("""
                    SRE（Site Reliability Engineering）はGoogleが提唱した、
                    ソフトウェアエンジニアリングの手法でシステムの信頼性を高める規律。
                    SLI/SLO/エラーバジェット・トイル削減・ポストモーテム文化・
                    カオスエンジニアリングが主要概念。
                    """)
                .whyItMatters("""
                    「サービスが落ちない」は当たり前ではなく、工学的アプローチの結果。
                    テックリード・PM・アーキテクトは信頼性要件を定義できる必要がある。
                    エラーバジェットによる機能開発と安定性のトレードオフ管理はPMに特に重要。
                    """)
                .howToLearn("""
                    1. 「SRE本」（Google著・無料公開）を読む
                    2. 自分のサービスにSLI/SLOを定義してみる
                    3. Game Dayを実施してカオスエンジニアリングを体験
                    4. ポストモーテムテンプレートを作り障害分析を習慣化
                    """)
                .keyTopics(List.of(
                    "SLI / SLO / エラーバジェット",
                    "トイル（Toil）の特定と削減",
                    "ポストモーテム（責任追及なし）文化",
                    "カオスエンジニアリング",
                    "オンコール設計とエスカレーションポリシー"
                ))
                .prerequisites(List.of("可観測性", "Kubernetes基礎"))
                .resources(List.of(
                    "Site Reliability Engineering (sre.google - 無料公開)",
                    "書籍: 「The Site Reliability Workbook」(Google)",
                    "Chaos Engineering (principlesofchaos.org)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.MEDIUM)
                .estimatedHours(60)
                .build()
        );
    }
}
