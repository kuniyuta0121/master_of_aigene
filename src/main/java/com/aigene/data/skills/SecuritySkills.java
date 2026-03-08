package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class SecuritySkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("owasp")
                .categoryId("SECURITY")
                .name("アプリケーションセキュリティ（OWASP）")
                .nameEn("Application Security / OWASP")
                .shortDescription("OWASP Top 10に基づくWebアプリのセキュリティ脆弱性と対策")
                .overview("""
                    OWASPはWebアプリケーションセキュリティの国際的非営利団体で、
                    「OWASP Top 10」は最も重大な脆弱性10種を定義する。
                    SQLインジェクション・XSS・CSRF・認証の不備・機密データの露出など、
                    知らずに作ると情報漏洩事故を起こす脆弱性のパターンと対策を学ぶ。
                    """)
                .whyItMatters("""
                    セキュリティは後付けでは高コスト。設計段階から組み込まないと
                    脆弱性が残り続ける。情報漏洩事故はエンジニアのキャリアリスクにもなる。
                    コードレビューでセキュリティ観点を持てることが今や標準要件。
                    """)
                .howToLearn("""
                    1. OWASP Top 10 公式ドキュメントを一通り読む
                    2. DVWA（Damn Vulnerable Web Application）でハンズオン学習
                    3. Burp Suite Community版でWebアプリの通信をインタセプトする
                    4. 自分のコードをSAST（Semgrep等）でスキャンする
                    """)
                .keyTopics(List.of(
                    "OWASP Top 10（SQLi・XSS・CSRF・IDOR・機密データ露出）",
                    "認証・認可の設計（JWT・OAuth2・RBAC）",
                    "セキュアなコーディング（入力バリデーション・パラメータ化クエリ）",
                    "静的解析（SAST）・動的解析（DAST）",
                    "依存ライブラリの脆弱性管理（Dependabot・Snyk）"
                ))
                .prerequisites(List.of("Web基礎（HTTP・HTML）", "バックエンド開発基礎"))
                .nextSkillIds(List.of("cloud_security", "threat_modeling"))
                .resources(List.of(
                    "OWASP Top 10 (owasp.org)",
                    "PortSwigger Web Security Academy (無料・充実)",
                    "書籍: 「体系的に学ぶ 安全なWebアプリケーションの作り方」(徳丸本)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(60)
                .build(),

            Skill.builder("cloud_security")
                .categoryId("SECURITY")
                .name("クラウドセキュリティ")
                .nameEn("Cloud Security")
                .shortDescription("IAM設計・ゼロトラスト・クラウドセキュリティアーキテクチャの実践")
                .overview("""
                    クラウドセキュリティはオンプレと異なる新しいリスクモデルを持つ。
                    AWS IAM の最小権限設計・VPCセキュリティ・暗号化（保存時・転送時）・
                    セキュリティグループ設計・CloudTrailによる監査ログが基本。
                    CSOPMツール（Prisma Cloud等）でクラウド全体の設定ミスを検出する。
                    """)
                .whyItMatters("""
                    S3バケットの公開設定ミスによる情報漏洩は後を絶たない。
                    クラウド利用が標準化した今、クラウドセキュリティは全エンジニアの必須知識。
                    AWSの設計書レビューでセキュリティ観点を持てることが求められる。
                    """)
                .howToLearn("""
                    1. AWS IAMのポリシー設計原則（最小権限）を実践
                    2. AWS Security HubとGuardDutyを有効化して脅威検出を体験
                    3. AWS Well-Architected Security Pillarを通読
                    4. Cloud Security Alliance (CSA) の資料を読む
                    """)
                .keyTopics(List.of(
                    "IAM設計（最小権限・役割分離・SCP）",
                    "ネットワークセキュリティ（VPC・SG・NACLs・VPC Endpoint）",
                    "暗号化（KMS・TLS・保存時暗号化）",
                    "セキュリティ監視（CloudTrail・GuardDuty・Security Hub）",
                    "ゼロトラストアーキテクチャ"
                ))
                .prerequisites(List.of("AWSまたはGCP基礎", "アプリケーションセキュリティ基礎"))
                .resources(List.of(
                    "AWS Security Documentation (公式)",
                    "Cloud Security Alliance (cloudsecurityalliance.org)",
                    "AWS Security Best Practices (Well-Architected)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("threat_modeling")
                .categoryId("SECURITY")
                .name("脅威モデリング")
                .nameEn("Threat Modeling")
                .shortDescription("設計段階でセキュリティリスクを特定・評価・対策するSTRIDE手法")
                .overview("""
                    脅威モデリングとは、システム設計の早期段階でセキュリティ上の脅威を
                    体系的に特定・評価・対策を決定するプロセス。
                    STRIDEフレームワーク（なりすまし・改ざん・否認・情報漏洩・DoS・権限昇格）で
                    脅威を分類し、DFD（データフロー図）を使って分析する。
                    """)
                .whyItMatters("""
                    開発後にセキュリティ問題を修正するコストは開発中の10〜100倍。
                    「Security by Design」を実践するための核心スキル。
                    シニアエンジニアやアーキテクトが主導するセキュリティレビューで必須。
                    """)
                .howToLearn("""
                    1. MicrosoftのSTRIDEモデルのドキュメントを読む
                    2. OWASP Threat Dragon でシンプルなシステムの脅威モデルを作成
                    3. チームで「悪役ハット」手法（Evil User Storiesの作成）を実施
                    4. PASTA（Process for Attack Simulation）も並行して学ぶ
                    """)
                .keyTopics(List.of(
                    "STRIDEフレームワーク",
                    "データフロー図（DFD）の作成",
                    "信頼境界（Trust Boundary）の定義",
                    "DREAD/CVSSによるリスク評価",
                    "対策とセキュリティ要件への反映"
                ))
                .prerequisites(List.of("アプリケーションセキュリティ基礎"))
                .resources(List.of(
                    "OWASP Threat Modeling (owasp.org)",
                    "書籍: 「Threat Modeling: Designing for Security」(Adam Shostack)",
                    "Microsoft Threat Modeling Tool"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.MEDIUM)
                .estimatedHours(30)
                .build()
        );
    }
}
