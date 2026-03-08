package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class FrontendSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("react_nextjs")
                .categoryId("FRONTEND")
                .name("React・Next.js")
                .nameEn("React / Next.js")
                .shortDescription("コンポーネント設計・状態管理・SSR/SSGを活用したモダンフロントエンド開発")
                .overview("""
                    Reactはコンポーネントベースのフロントエンドライブラリ。
                    Next.jsはReactをベースにSSR（サーバーサイドレンダリング）・SSG・
                    App Routerを提供するフルスタックフレームワーク。
                    TypeScriptと組み合わせた型安全な開発が現代の標準スタイル。
                    """)
                .whyItMatters("""
                    AIチャットUI・ダッシュボード・社内ツールをフロントエンドも含めて
                    自分で作れると市場価値が上がる。
                    PMとしてもフロントエンドの制約を理解することで現実的な要件定義ができる。
                    """)
                .howToLearn("""
                    1. React公式ドキュメント（react.dev）のチュートリアルを完走
                    2. Next.jsのApp Routerで簡単なWebアプリを作る
                    3. Zustand / Jotaiで状態管理を実装する
                    4. React Query（TanStack Query）でサーバーデータを管理する
                    """)
                .keyTopics(List.of(
                    "React コンポーネント・Hooks（useState/useEffect/useCallback）",
                    "Next.js App Router・Server Components",
                    "状態管理（Zustand / Jotai）",
                    "TanStack Query（非同期データ管理）",
                    "Tailwind CSS によるスタイリング"
                ))
                .prerequisites(List.of("JavaScript基礎", "TypeScript基礎", "HTML/CSS基礎"))
                .resources(List.of(
                    "React Documentation (react.dev - 公式・無料)",
                    "Next.js Documentation (nextjs.org - 公式・無料)",
                    "書籍: 「React実践の教科書」"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.MEDIUM)
                .estimatedHours(60)
                .build(),

            Skill.builder("web_performance")
                .categoryId("FRONTEND")
                .name("Webパフォーマンス最適化")
                .nameEn("Web Performance Optimization")
                .shortDescription("Core Web Vitals・バンドル最適化・画像最適化でUXとSEOを改善する")
                .overview("""
                    Webパフォーマンスはユーザー体験とSEOに直結する。
                    GoogleのCore Web Vitals（LCP・INP・CLS）が評価基準。
                    バンドルサイズ削減・コード分割・画像最適化・キャッシュ戦略・
                    Critical Rendering Pathの最適化が主な手法。
                    """)
                .whyItMatters("""
                    LCPが1秒遅いとコンバージョン率が7%落ちるという研究結果がある。
                    フロントエンドを触るなら必ず知っておくべきUX改善の直接手段。
                    """)
                .howToLearn("""
                    1. web.dev/performance でGoogle公式のコースを受講
                    2. Lighthouseで自分のサイトをスコア測定して改善する
                    3. Chrome DevToolsのPerformanceタブを使い倒す
                    4. Bundle Analyzerでwebpackバンドルを分析する
                    """)
                .keyTopics(List.of(
                    "Core Web Vitals（LCP・INP・CLS）",
                    "コード分割（Code Splitting）・遅延ロード",
                    "画像最適化（WebP・avif・next/image）",
                    "キャッシュ戦略（HTTP Cache・Service Worker）",
                    "Critical Rendering Path"
                ))
                .prerequisites(List.of("React・Next.js基礎", "HTTP基礎"))
                .resources(List.of(
                    "web.dev/performance (Google公式・無料)",
                    "書籍: 「ハイパフォーマンスブラウザネットワーキング」",
                    "PageSpeed Insights（無料計測ツール）"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.LOW)
                .estimatedHours(30)
                .build()
        );
    }
}
