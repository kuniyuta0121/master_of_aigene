package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class ProgrammingSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("python_advanced")
                .categoryId("PROGRAMMING")
                .name("Pythonアドバンスド")
                .nameEn("Advanced Python")
                .shortDescription("非同期処理・型ヒント・デザインパターン・パフォーマンス最適化")
                .overview("""
                    Pythonを「書ける」から「設計できる」レベルに引き上げる技術群。
                    型ヒント（Type Hints）+mypy による静的型チェック・asyncio による非同期処理・
                    デコレータ・メタクラス・ジェネレータの深い理解・
                    パフォーマンスボトルネック特定と最適化が対象。
                    """)
                .whyItMatters("""
                    Pythonで書かれた小さなスクリプトと大規模サービスでは
                    求められるスキルが全く異なる。型ヒントがないコードは
                    チームでの開発でバグを増産する。AI時代にPythonはさらに重要性を増す。
                    """)
                .howToLearn("""
                    1. 「Fluent Python」（O'Reilly）を読む（特にデータモデルとasyncioの章）
                    2. 既存コードに型ヒントを追加してmypyを通す
                    3. asyncioを使った非同期APIクライアントを実装
                    4. cProfileでボトルネックを特定してNumPy/ベクトル演算で最適化
                    """)
                .keyTopics(List.of(
                    "型ヒント（Type Hints）・mypy・Pydantic",
                    "非同期処理（asyncio・async/await・aiohttp）",
                    "デコレータ・コンテキストマネージャー・メタクラス",
                    "ジェネレータ・イテレータ・内包表記の応用",
                    "パフォーマンス最適化（cProfile・NumPy・Cython）"
                ))
                .prerequisites(List.of("Python基礎（関数・クラス・モジュール）"))
                .nextSkillIds(List.of("ml_fundamentals", "data_pipeline"))
                .resources(List.of(
                    "書籍: 「Fluent Python」2nd ed. (Luciano Ramalho)",
                    "書籍: 「Python Cookbook」(O'Reilly)",
                    "Real Python (realpython.com - 実践的な記事が充実)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("go_lang")
                .categoryId("PROGRAMMING")
                .name("Go言語")
                .nameEn("Go (Golang)")
                .shortDescription("シンプルかつ高性能なクラウドネイティブ開発のためのGo言語")
                .overview("""
                    Goはコンパイル型・静的型付け・ガベージコレクション付きの言語で、
                    Googleが設計した。DockerやKubernetesがGoで書かれており、
                    クラウドネイティブ開発のデファクト言語のひとつ。
                    Goroutineによる並行処理がシンプルに書ける点が大きな強み。
                    """)
                .whyItMatters("""
                    マイクロサービスのAPIサーバー・CLI ツール・システムプログラミングで
                    Pythonより高性能が求められる場面でGoが選ばれる。
                    クラウドエコシステムのツールを読んだり改造するのにGoの理解が必要。
                    """)
                .howToLearn("""
                    1. Tour of Go (go.dev/tour) を全部やる
                    2. 「Go言語プログラミングエッセンス」を読む
                    3. 簡単なREST APIをnet/httpで実装する
                    4. Goroutineとchannelで並行処理を実装する
                    """)
                .keyTopics(List.of(
                    "Goroutineとchannelによる並行処理",
                    "インターフェースと型システム",
                    "エラーハンドリング（error型・errors.Is/As）",
                    "context パッケージ",
                    "testing パッケージとベンチマーク"
                ))
                .prerequisites(List.of("プログラミング基礎（任意言語）", "HTTP/REST基礎"))
                .resources(List.of(
                    "Tour of Go (go.dev/tour - 無料)",
                    "書籍: 「Go言語プログラミングエッセンス」(柴田芳樹)",
                    "書籍: 「The Go Programming Language」(Donovan & Kernighan)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.MEDIUM)
                .estimatedHours(60)
                .build(),

            Skill.builder("typescript")
                .categoryId("PROGRAMMING")
                .name("TypeScript")
                .nameEn("TypeScript")
                .shortDescription("JavaScriptに型安全性を加えた、現代のフロントエンド・バックエンド開発言語")
                .overview("""
                    TypeScriptはMicrosoftが開発したJavaScriptのスーパーセット。
                    静的型付けによりコンパイル時にバグを検出できる。
                    ReactやNext.jsのフロントエンド開発では今やデファクトスタンダード。
                    Node.js（Express/Hono）でのバックエンド開発にも広く使われる。
                    """)
                .whyItMatters("""
                    フロントエンドの経験があるなら習得コストは低い。
                    型システムの理解はJava・Goを学ぶ際にも役立つ。
                    フルスタック開発者・テックリードに求められることが多い。
                    """)
                .howToLearn("""
                    1. TypeScript公式ハンドブックを一通り読む
                    2. 既存のJSプロジェクトをTypeScriptに移行する
                    3. 型レベルプログラミング（Conditional Types・Template Literal Types）を学ぶ
                    4. tRPCでフルスタック型安全APIを実装する
                    """)
                .keyTopics(List.of(
                    "基本型・ユニオン型・インターセクション型",
                    "ジェネリクス（Generics）",
                    "型推論とany・unknownの使い分け",
                    "Utility Types（Partial・Pick・Omit・ReturnType）",
                    "型安全なAPI設計（Zodバリデーション）"
                ))
                .prerequisites(List.of("JavaScript基礎"))
                .resources(List.of(
                    "TypeScript Handbook (typescriptlang.org - 公式・無料)",
                    "Total TypeScript (totaltypescript.com)",
                    "書籍: 「プログラミングTypeScript」(O'Reilly)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(50)
                .build(),

            Skill.builder("algorithms")
                .categoryId("PROGRAMMING")
                .name("アルゴリズム・データ構造")
                .nameEn("Algorithms & Data Structures")
                .shortDescription("計算量の理解、主要データ構造、グラフ・動的計画法などの問題解決力")
                .overview("""
                    アルゴリズムとデータ構造は、効率的なプログラムを書くための基礎理論。
                    配列・連結リスト・スタック・キュー・木・グラフ・ハッシュテーブルの特性と
                    ソート・探索・動的計画法・グラフアルゴリズム（BFS/DFS/Dijkstra）の実装を理解する。
                    面接でも問われる普遍的な知識。
                    """)
                .whyItMatters("""
                    「なぜO(n²)ではなくO(n log n)を使うか」を判断できないと
                    大規模データで性能問題が起きる。FAANG系の採用面接でも必須。
                    データエンジニアリングやMLの実装にも計算量の理解は重要。
                    """)
                .howToLearn("""
                    1. 「アルゴリズムとデータ構造」(渡部有隆) を読む
                    2. LeetCode でEasyを50問・Mediumを30問解く
                    3. AtCoderのABC（A,B,C問題）を継続的に解く
                    4. 「アルゴリズムイントロダクション」で理論を補完
                    """)
                .keyTopics(List.of(
                    "計算量（時間・空間）のO記法",
                    "ソートアルゴリズム（クイックソート・マージソート・ヒープソート）",
                    "グラフアルゴリズム（BFS・DFS・Dijkstra・A*）",
                    "動的計画法（DP）",
                    "木（二分探索木・ヒープ・Trie）"
                ))
                .prerequisites(List.of("プログラミング基礎（任意言語）"))
                .resources(List.of(
                    "LeetCode (leetcode.com)",
                    "AtCoder (atcoder.jp)",
                    "書籍: 「アルゴリズムとデータ構造」(渡部有隆)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("design_patterns")
                .categoryId("PROGRAMMING")
                .name("デザインパターン")
                .nameEn("Design Patterns")
                .shortDescription("GoFデザインパターンと現代的なソフトウェア設計原則（SOLID）")
                .overview("""
                    デザインパターンはソフトウェア設計における再利用可能な解法のカタログ。
                    GoFの23パターン（生成・構造・振る舞い）とSOLID原則（単一責任・
                    開放閉鎖・リスコフ置換・インターフェース分離・依存性逆転）が基礎。
                    パターンを知ることより「いつ使うか・使わないか」の判断が重要。
                    """)
                .whyItMatters("""
                    設計の共通言語を持つことでコードレビューや設計議論が効率化する。
                    「ここはStrategyパターンにすべき」と言えれば設計議論が早くなる。
                    大規模システムのリファクタリングでパターンの適用が役立つ。
                    """)
                .howToLearn("""
                    1. 「オブジェクト指向における再利用のためのデザインパターン」(GoF本)
                    2. Refactoring.Guru でパターンを図解で学ぶ
                    3. 自分のコードでどのパターンが使えるか分析する
                    4. SOLID原則違反を見つけてリファクタリングする練習
                    """)
                .keyTopics(List.of(
                    "SOLID原則",
                    "生成パターン（Singleton・Factory・Builder・Prototype）",
                    "構造パターン（Adapter・Decorator・Facade・Proxy）",
                    "振る舞いパターン（Strategy・Observer・Command・Template Method）",
                    "Dependency Injection（DI）とIoC"
                ))
                .prerequisites(List.of("オブジェクト指向プログラミング"))
                .resources(List.of(
                    "Refactoring.Guru (refactoring.guru/design-patterns - 無料)",
                    "書籍: 「オブジェクト指向における再利用のためのデザインパターン」(GoF)",
                    "書籍: 「Clean Code」(Robert C. Martin)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(50)
                .build()
        );
    }
}
