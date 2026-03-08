package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class PmSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("agile_scrum")
                .categoryId("PM")
                .name("アジャイル・スクラム")
                .nameEn("Agile / Scrum")
                .shortDescription("スクラムフレームワークによる反復型開発とアジャイルマインドセット")
                .overview("""
                    アジャイルは「計画より変化への対応」を優先する開発哲学。
                    スクラムはアジャイルの最も普及した実践フレームワークで、
                    スプリント（1〜4週間の開発サイクル）・デイリースクラム・スプリントレビュー・
                    レトロスペクティブで構成される。
                    Product Owner・Scrum Master・Development Teamの役割定義が重要。
                    """)
                .whyItMatters("""
                    PMを目指すなら必須中の必須。スクラムを知らずにPMにはなれない。
                    エンジニアとしてもスプリントでどう動くかを理解することで
                    チームへの貢献度が上がる。多くの企業でスクラムが採用されている。
                    """)
                .howToLearn("""
                    1. 「スクラムガイド」（公式・無料・日本語版あり）を読む
                    2. PSM I（Professional Scrum Master）を取得する
                    3. 現職でのスプリントを意識的に観察・改善提案する
                    4. 「SCRUM BOOT CAMP THE BOOK」を読む
                    """)
                .keyTopics(List.of(
                    "スクラムの3つの役割（PO・SM・Dev Team）",
                    "スプリント・バックログ・定義完了（DoD）",
                    "バックログリファインメントとストーリーポイント",
                    "ベロシティとキャパシティプランニング",
                    "カンバン・XP（エクストリームプログラミング）との違い"
                ))
                .prerequisites(List.of("ソフトウェア開発基礎"))
                .nextSkillIds(List.of("product_discovery", "stakeholder_mgmt"))
                .resources(List.of(
                    "Scrum Guide (scrumguides.org - 日本語版あり・無料)",
                    "書籍: 「SCRUM BOOT CAMP THE BOOK」(西村直人ほか)",
                    "PSM I 認定試験 (scrum.org)"
                ))
                .difficulty(Difficulty.BEGINNER)
                .priority(Priority.CRITICAL)
                .estimatedHours(30)
                .build(),

            Skill.builder("product_discovery")
                .categoryId("PM")
                .name("プロダクトディスカバリー")
                .nameEn("Product Discovery")
                .shortDescription("ユーザーインタビュー・仮説検証・MVPによる正しいものを正しく作る手法")
                .overview("""
                    プロダクトディスカバリーとは「何を作るべきか」を検証するプロセス。
                    ユーザーインタビュー・問題発見・仮説の設定・MVPによる検証・学習のループを
                    継続的に回す。Teresa Torresの「Continuous Discovery Habits」が現代的な教科書。
                    エンジニアがディスカバリーに関与することで、技術的実現可能性の観点が入る。
                    """)
                .whyItMatters("""
                    「誰も使わない機能を完璧に作った」という失敗を防ぐ。
                    PM志望者が最初に習得すべき最重要スキル。
                    エンジニアがこれを理解するだけで「なぜこの機能を作るのか」が明確になり
                    自律的な提案ができるようになる。
                    """)
                .howToLearn("""
                    1. 「Continuous Discovery Habits」(Teresa Torres) を読む
                    2. ユーザーインタビューを5名以上実施する
                    3. 機会ソリューションツリー（OST）を実際のプロダクトで作成
                    4. Jobs to be Done（JTBD）フレームワークを学ぶ
                    """)
                .keyTopics(List.of(
                    "ユーザーインタビューの設計と実施",
                    "Jobs to be Done（JTBD）",
                    "機会ソリューションツリー（OST）",
                    "MVP設計（最小限の学習を最大化する）",
                    "定量・定性データの組み合わせ"
                ))
                .prerequisites(List.of("アジャイル基礎"))
                .nextSkillIds(List.of("okr_metrics", "tech_pm"))
                .resources(List.of(
                    "書籍: 「Continuous Discovery Habits」(Teresa Torres)",
                    "書籍: 「INSPIRED」(Marty Cagan)",
                    "書籍: 「The Mom Test」(Rob Fitzpatrick)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(50)
                .build(),

            Skill.builder("okr_metrics")
                .categoryId("PM")
                .name("OKR・メトリクス設計")
                .nameEn("OKR & Metrics")
                .shortDescription("目標設定（OKR）と成果測定のための適切なメトリクス設計")
                .overview("""
                    OKR（Objectives and Key Results）はGoogleが普及させた目標管理フレームワーク。
                    Objective（定性的な野心的目標）とKey Results（定量的な達成指標）のセットで
                    チームの方向性を揃える。North Star Metric・AARRR・Pirate Metricsなど
                    プロダクト成長の測定フレームワークも重要。
                    """)
                .whyItMatters("""
                    「何のために作るのか」を数値で表現できないと、
                    機能追加が正しかったかどうか判断できない。
                    PMは常にビジネスインパクトで語る必要があり、OKRはその共通言語。
                    データエンジニアリングスキルと組み合わせると自力で分析できる。
                    """)
                .howToLearn("""
                    1. 「Measure What Matters」(John Doerr) を読む
                    2. 自分のチームのOKRを設定・レビューする実践
                    3. Google Analyticsでファネル分析・コホート分析を実施
                    4. North Star Metricを自分のプロダクトで定義する
                    """)
                .keyTopics(List.of(
                    "OKR設定の原則（野心的・測定可能）",
                    "North Star Metric の設計",
                    "AARRR（Acquisition・Activation・Retention・Revenue・Referral）",
                    "実験設計（A/Bテスト）",
                    "データダッシュボードの設計と運用"
                ))
                .prerequisites(List.of("プロダクトディスカバリー基礎", "SQL基礎"))
                .resources(List.of(
                    "書籍: 「Measure What Matters」(John Doerr)",
                    "書籍: 「Lean Analytics」(Ben Yoskovitz)",
                    "Amplitude・Mixpanel ドキュメント（プロダクト分析ツール）"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build(),

            Skill.builder("stakeholder_mgmt")
                .categoryId("PM")
                .name("ステークホルダー管理")
                .nameEn("Stakeholder Management")
                .shortDescription("経営・営業・エンジニアなど多様な関係者との合意形成と期待値管理")
                .overview("""
                    PMは常に複数のステークホルダー（経営・営業・エンジニア・デザイナー・
                    顧客）の間に立ち、それぞれ異なる期待値と優先度を持つ人々をまとめる。
                    ステークホルダーマップの作成・定期的なコミュニケーション計画・
                    意思決定会議の設計・期待値のリセットが主な実践。
                    """)
                .whyItMatters("""
                    PMとして最もつまずきやすい部分。
                    技術的に完璧なプロダクトを作っても、経営・営業が
                    「求めていたものと違う」と言う状況を防ぐのがステークホルダー管理。
                    エンジニアリングマネージャーにも同様に必要。
                    """)
                .howToLearn("""
                    1. 「Influence Without Authority」(Cohen & Bradford) を読む
                    2. ステークホルダーマップを実際に作成する
                    3. 週次・月次レポートの書き方を磨く
                    4. 困難なフィードバックを受けた経験を振り返り構造化する
                    """)
                .keyTopics(List.of(
                    "ステークホルダーマップの作成",
                    "コミュニケーション計画（誰に・何を・どの頻度で）",
                    "要求vs必要（Wants vs Needs）の分離",
                    "期待値のリセットと合意形成",
                    "経営層への報告・エスカレーション"
                ))
                .prerequisites(List.of("アジャイル・スクラム基礎"))
                .resources(List.of(
                    "書籍: 「Influence Without Authority」(Cohen & Bradford)",
                    "書籍: 「プロダクトマネジメント」(Melissa Perri)",
                    "書籍: 「エッセンシャル思考」(Greg McKeown)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(30)
                .build(),

            Skill.builder("tech_pm")
                .categoryId("PM")
                .name("テクニカルプロダクトマネジメント")
                .nameEn("Technical Product Management")
                .shortDescription("エンジニア出身のPMが持つ技術判断力とエンジニアチームとの協働スキル")
                .overview("""
                    テクニカルPMとは技術的な判断ができるPMのこと。
                    技術的負債の優先順位付け・APIの仕様策定への関与・
                    エンジニアの見積もりの妥当性判断・セキュリティ・
                    パフォーマンス要件の定義ができることが期待される。
                    エンジニア出身者の最大の強みを最大化するキャリアパス。
                    """)
                .whyItMatters("""
                    エンジニア経験のないPMがエンジニアチームから信頼を得るのは難しい。
                    あなたのエンジニア経験はPMとして圧倒的な差別化要因になる。
                    AIプロダクトの増加でテクニカルPMの需要は急増している。
                    """)
                .howToLearn("""
                    1. 「Inspired」(Marty Cagan) を読む
                    2. エンジニアとして設計決定に主体的に関与する経験を積む
                    3. 技術ロードマップと事業ロードマップを紐付けて説明する練習
                    4. 「Becoming a Technical Leader」(Gerald Weinberg) を読む
                    """)
                .keyTopics(List.of(
                    "技術的負債の可視化と優先順位付け",
                    "技術仕様書（TDD・RFC）の読み書き",
                    "エンジニア工数見積もりの理解と合意",
                    "AIプロダクトの要件定義（LLM・ML特有の考慮点）",
                    "ビルド・バイ・パートナーの意思決定"
                ))
                .prerequisites(List.of("プロダクトディスカバリー", "ステークホルダー管理", "開発経験"))
                .resources(List.of(
                    "書籍: 「INSPIRED」2nd ed. (Marty Cagan)",
                    "書籍: 「Continuous Discovery Habits」",
                    "書籍: 「プロダクトマネジメントのすべて」"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.CRITICAL)
                .estimatedHours(80)
                .build(),

            Skill.builder("product_strategy")
                .categoryId("PM")
                .name("プロダクト戦略")
                .nameEn("Product Strategy")
                .shortDescription("市場分析・競合理解・差別化戦略によるプロダクトの長期方向性の策定")
                .overview("""
                    プロダクト戦略とは「なぜこのプロダクトが市場で勝てるか」を定義すること。
                    市場規模（TAM/SAM/SOM）の分析・競合調査・差別化ポイントの明確化・
                    ビジョン→戦略→ロードマップへの落とし込みが主な内容。
                    Positioning by April Dunfordが戦略策定の最良の教科書。
                    """)
                .whyItMatters("""
                    「なんとなくいい機能を作り続ける」PMと「市場で勝つための選択と集中ができる」PMは
                    キャリアも責任も全く違う。シニアPM・CPOになるための必須スキル。
                    AI時代は市場変化が速く、戦略の見直し頻度も上がっている。
                    """)
                .howToLearn("""
                    1. 「Obviously Awesome」(April Dunford) でポジショニングを学ぶ
                    2. 「良い戦略、悪い戦略」(Richard Rumelt) を読む
                    3. 自社プロダクトのポジショニングマップを作成する
                    4. 競合の公開情報（IR・プレスリリース）から戦略を読む
                    """)
                .keyTopics(List.of(
                    "市場分析（TAM/SAM/SOM）",
                    "ポジショニング戦略",
                    "プロダクトビジョンとミッションの定義",
                    "ロードマップのコミュニケーション（Now/Next/Later）",
                    "競合分析フレームワーク"
                ))
                .prerequisites(List.of("プロダクトディスカバリー", "OKR・メトリクス設計"))
                .resources(List.of(
                    "書籍: 「Obviously Awesome」(April Dunford)",
                    "書籍: 「良い戦略、悪い戦略」(Richard Rumelt)",
                    "書籍: 「EMPOWERED」(Marty Cagan)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(50)
                .build()
        );
    }
}
