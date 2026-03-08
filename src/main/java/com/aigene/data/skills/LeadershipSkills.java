package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class LeadershipSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("tech_leadership")
                .categoryId("LEADERSHIP")
                .name("テクニカルリーダーシップ")
                .nameEn("Technical Leadership")
                .shortDescription("技術的判断をチームに伝え、エンジニアの成長を支援するリーダーシップ")
                .overview("""
                    テクニカルリーダーシップとは肩書きではなく振る舞い。
                    技術的方向性を示す・コードレビューでメンタリングする・
                    技術的負債に声を上げる・アーキテクチャ決定を文書化（ADR）する・
                    チームの技術スタックを更新するロードマップを描くことが含まれる。
                    Staff Engineer・Principal Engineer への道に必須。
                    """)
                .whyItMatters("""
                    シニアエンジニアを超えてStaff/Principalになるための核心スキル。
                    PMへの移行においても、エンジニアチームと対等に話すために必要。
                    一人でコードを書ける力から「チームのアウトプットを最大化する力」への転換。
                    """)
                .howToLearn("""
                    1. 「Staff Engineer: Leadership Beyond the Management Track」を読む
                    2. アーキテクチャ決定記録（ADR）を書き始める
                    3. コードレビューのフィードバックを建設的にする練習
                    4. 技術的負債の可視化レポートを書いてチームに提案する
                    """)
                .keyTopics(List.of(
                    "アーキテクチャ決定記録（ADR）の書き方",
                    "技術ロードマップの策定",
                    "建設的なコードレビューとメンタリング",
                    "技術的負債の管理と優先順位付け",
                    "Staff Engineer vs Engineering Manager のパス選択"
                ))
                .prerequisites(List.of("シニアエンジニアレベルの技術スキル"))
                .nextSkillIds(List.of("team_building", "tech_pm"))
                .resources(List.of(
                    "書籍: 「Staff Engineer」(Will Larson)",
                    "書籍: 「An Elegant Puzzle」(Will Larson)",
                    "staffeng.com (Staff Engineerのインタビュー集)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build(),

            Skill.builder("business_acumen")
                .categoryId("LEADERSHIP")
                .name("ビジネス思考・財務理解")
                .nameEn("Business Acumen")
                .shortDescription("PLの読み方・ROI計算・事業モデルの理解でビジネス議論に参加する")
                .overview("""
                    エンジニアやPMがビジネス的に信頼されるためには、
                    損益計算書（P/L）の読み方・ROI（投資対効果）の計算・
                    ユニットエコノミクス（LTV・CAC）・事業モデルの理解が必要。
                    「この機能の開発コストに対して期待されるリターンは何か」を
                    語れることが経営層との対話に不可欠。
                    """)
                .whyItMatters("""
                    PMとして経営層に「なぜこの機能を作るべきか」を説明するとき、
                    ビジネス言語で話せないと予算が獲得できない。
                    エンジニアも自分の仕事が事業にどう貢献するかを理解することで
                    優先度判断の精度が上がる。
                    """)
                .howToLearn("""
                    1. 「MBAの財務・会計」入門書で基礎を固める
                    2. 上場企業のIR資料（決算説明書）を定期的に読む
                    3. 自社サービスのユニットエコノミクスを計算してみる
                    4. 「ビジネスモデル・ジェネレーション」でビジネスモデルを学ぶ
                    """)
                .keyTopics(List.of(
                    "財務三表の読み方（P/L・B/S・CF）",
                    "ROI・NPV・ペイバック期間",
                    "ユニットエコノミクス（LTV・CAC・チャーン）",
                    "ビジネスモデルキャンバス",
                    "SaaSメトリクス（ARR・MRR・NRR）"
                ))
                .prerequisites(List.of("ビジネス基礎"))
                .resources(List.of(
                    "書籍: 「新・企業価値評価」",
                    "書籍: 「ビジネスモデル・ジェネレーション」",
                    "a16z Podcast（シリコンバレーのビジネス思考）"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build(),

            Skill.builder("communication")
                .categoryId("LEADERSHIP")
                .name("技術コミュニケーション・説明力")
                .nameEn("Technical Communication")
                .shortDescription("技術を非技術者に分かりやすく伝え、文書で意思決定を推進する力")
                .overview("""
                    テクニカルライティングとプレゼンテーション力は、
                    シニアエンジニア・PM・テックリードに共通して求められる。
                    RFC（Request for Comments）・設計ドキュメント・障害報告・
                    技術ブログ・スライドを通じて思考を構造化し相手に伝える。
                    「Pyramid Principle」による論理構造が基礎。
                    """)
                .whyItMatters("""
                    どんなに良い技術を作っても、伝わらなければ存在しないに等しい。
                    PMにとって「言語化」はコアコンピタンス。
                    リモートワーク時代において非同期コミュニケーション力は重要性が増している。
                    """)
                .howToLearn("""
                    1. 「考える技術・書く技術」(バーバラ・ミント) でピラミッド構造を学ぶ
                    2. 技術ブログを月1回書く習慣を付ける
                    3. 設計ドキュメント（RFC・ADR）を社内で書いてフィードバックを得る
                    4. Notionで議事録・週次レポートのテンプレートを整備する
                    """)
                .keyTopics(List.of(
                    "ピラミッド原則（Pyramid Principle）",
                    "テクニカルライティング（RFC・ADR・設計ドキュメント）",
                    "プレゼンテーション設計（聴衆・目的・構造）",
                    "非同期コミュニケーション（Slack・Notion・Confluence）",
                    "エグゼクティブサマリーの書き方"
                ))
                .prerequisites(List.of("ビジネス基礎"))
                .resources(List.of(
                    "書籍: 「考える技術・書く技術」(バーバラ・ミント)",
                    "書籍: 「ライティングの哲学」",
                    "Google Technical Writing Course (無料)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(30)
                .build(),

            Skill.builder("team_building")
                .categoryId("LEADERSHIP")
                .name("チーム育成・メンタリング")
                .nameEn("Team Building & Mentoring")
                .shortDescription("1on1・フィードバック・心理的安全性でエンジニアチームの成長を加速させる")
                .overview("""
                    チームを育てる力は、テックリード・EM・シニアPMに求められる。
                    効果的な1on1の設計・建設的なフィードバックの与え方・
                    心理的安全性の構築・採用面接でのスキル評価が主な実践内容。
                    Google の Project Aristotle が明かした「心理的安全性が最重要」という
                    知見はチーム設計の基礎になっている。
                    """)
                .whyItMatters("""
                    40〜50年キャリアを続ける中で、個人の技術力より
                    「チームを機能させる力」の比重が大きくなる。
                    PMとして優秀なエンジニアを採用・育成・定着させることが
                    プロダクト成功の鍵になる。
                    """)
                .howToLearn("""
                    1. 「ピープルウェア」(DeMarco & Lister) を読む
                    2. 1on1を週次で実施し、コーチング手法を練習する
                    3. 「フィードバックの哲学」で建設的なフィードバックを学ぶ
                    4. 心理的安全性の測定・改善アクションを試みる
                    """)
                .keyTopics(List.of(
                    "効果的な1on1の設計（アジェンダ・傾聴・アクション）",
                    "心理的安全性の醸成",
                    "SBI（状況・行動・影響）フィードバックモデル",
                    "技術面接の設計と評価基準",
                    "コーチングとティーチングの使い分け"
                ))
                .prerequisites(List.of("コミュニケーション・説明力"))
                .resources(List.of(
                    "書籍: 「ピープルウェア」(Tom DeMarco)",
                    "書籍: 「エンジニアのためのマネジメントキャリアパス」(Camille Fournier)",
                    "re:Work (rework.withgoogle.com - Google公式・無料)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(40)
                .build(),

            Skill.builder("career_strategy")
                .categoryId("LEADERSHIP")
                .name("キャリア戦略")
                .nameEn("Career Strategy")
                .shortDescription("40〜50年食べていくためのキャリア設計・学習戦略・個人ブランディング")
                .overview("""
                    急速な技術変化の時代に「今の技術だけで40年食べる」は不可能。
                    学習し続ける仕組み・自分の市場価値の把握・個人ブランディング（ブログ・OSSコントリビュート）・
                    収入の多様化（副業・登壇・執筆）が長期キャリアの安定を支える。
                    T型（一分野の深さ + 広い知識）からπ型（二分野の深さ）への進化が理想。
                    """)
                .whyItMatters("""
                    AIが多くのエンジニアリングタスクを自動化する時代に、
                    「人間にしかできないこと」にフォーカスしたキャリア設計が必要。
                    PMへの移行・副業・個人ブランディングを戦略的に設計する。
                    """)
                .howToLearn("""
                    1. 「エンジニアリング組織論への招待」(広木大地) を読む
                    2. 3年・5年・10年のキャリアビジョンを書き出す
                    3. 技術ブログ・登壇・GitHub OSSでアウトプットを増やす
                    4. 転職市場の動向をLinkedIn・求人サイトで定点観測する
                    """)
                .keyTopics(List.of(
                    "T型・π型スキルセットの設計",
                    "個人ブランディング（ブログ・登壇・SNS）",
                    "技術変化への適応戦略（5年ごとのスキル棚卸し）",
                    "副業・フリーランスの検討",
                    "AI時代に価値を持つスキルの見極め"
                ))
                .prerequisites(List.of("技術コミュニケーション基礎"))
                .resources(List.of(
                    "書籍: 「エンジニアリング組織論への招待」(広木大地)",
                    "書籍: 「深く、速く、考える技術」",
                    "書籍: 「ライフ・シフト」(Andrew Scott)"
                ))
                .difficulty(Difficulty.BEGINNER)
                .priority(Priority.CRITICAL)
                .estimatedHours(20)
                .build()
        );
    }
}
