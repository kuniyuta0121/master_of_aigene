package com.aigene.data.skills;

import com.aigene.model.Difficulty;
import com.aigene.model.Priority;
import com.aigene.model.Skill;

import java.util.List;

public class AiMlSkills {

    public static List<Skill> get() {
        return List.of(

            Skill.builder("ml_fundamentals")
                .categoryId("AI_ML")
                .name("機械学習基礎")
                .nameEn("Machine Learning Fundamentals")
                .shortDescription("教師あり・なし学習、評価指標、モデル選択の基礎")
                .overview("""
                    機械学習とは、データからパターンを学習してタスクを実行するアルゴリズムの総称。
                    線形回帰・ロジスティック回帰・決定木・ランダムフォレスト・SVMなど
                    古典的アルゴリズムの理解は、LLM全盛の時代でも必須の基盤知識。
                    scikit-learnを使えばPythonで素早く試作できる。
                    """)
                .whyItMatters("""
                    AIエンジニアやPMがLLM以外のアプローチを判断する際に必要。
                    「なぜニューラルネットでなく決定木を使うか」を説明できないと
                    技術選定や要件定義で誤った判断をしかねない。
                    """)
                .howToLearn("""
                    1. 「ゼロから作るDeep Learning」の前半（ML基礎）を読む
                    2. Kaggleのチュートリアルで実データを触る
                    3. scikit-learnの公式ドキュメントを一通り読む
                    4. 精度・再現率・F1スコア・ROC曲線を手計算で理解する
                    """)
                .aiEraRelevance("""
                    LLMがすべてを解決するわけではない。画像分類・異常検知・需要予測など
                    古典的MLが今でも主役の領域は多い。LLMとの組み合わせ判断も重要。
                    """)
                .keyTopics(List.of(
                    "教師あり学習（回帰・分類）",
                    "教師なし学習（クラスタリング・次元削減）",
                    "モデル評価（交差検証・過学習対策）",
                    "特徴量エンジニアリング",
                    "scikit-learn実装"
                ))
                .prerequisites(List.of("Python基礎", "統計基礎（平均・分散・確率）"))
                .nextSkillIds(List.of("deep_learning", "mlops"))
                .resources(List.of(
                    "Kaggle Learn: Intro to Machine Learning",
                    "書籍: 「Hands-On Machine Learning with Scikit-Learn」",
                    "Google Machine Learning Crash Course (無料)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(60)
                .build(),

            Skill.builder("deep_learning")
                .categoryId("AI_ML")
                .name("深層学習")
                .nameEn("Deep Learning")
                .shortDescription("ニューラルネットワーク、CNN、RNN、Transformerの理解と実装")
                .overview("""
                    深層学習はニューラルネットワークを多層化した手法で、画像・音声・テキスト処理で
                    革命的な成果を上げている。PyTorchまたはTensorFlowで実装する。
                    Transformerアーキテクチャの理解はLLM時代に特に重要。
                    """)
                .whyItMatters("""
                    LLMはTransformerの上に成り立つ。内部を理解せずに使うと、
                    ハルシネーション・コンテキスト長・埋め込みの概念が理解できず
                    システム設計や品質改善で行き詰まる。
                    """)
                .howToLearn("""
                    1. 「ゼロから作るDeep Learning」シリーズを完走
                    2. PyTorchのチュートリアルで実装練習
                    3. 「Attention is All You Need」論文を読む（Transformer原論文）
                    4. HuggingFaceのtransformersライブラリを触る
                    """)
                .aiEraRelevance("""
                    ChatGPT・Gemini・Claudeすべてのベースがこの技術。
                    ファインチューニング・LoRAの理解にも必要。
                    2024年以降はマルチモーダルモデルの理解も重要になっている。
                    """)
                .keyTopics(List.of(
                    "ニューラルネットワークの基礎（順伝播・逆伝播）",
                    "CNN（畳み込みニューラルネットワーク）",
                    "RNN・LSTM（系列データ処理）",
                    "Transformerアーキテクチャ・Attention機構",
                    "PyTorchによる実装"
                ))
                .prerequisites(List.of("機械学習基礎", "線形代数基礎", "Python中級"))
                .nextSkillIds(List.of("llm_usage", "mlops"))
                .resources(List.of(
                    "書籍: 「ゼロから作るDeep Learning」(斎藤康毅)",
                    "fast.ai: Practical Deep Learning for Coders",
                    "論文: Attention is All You Need (2017)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(100)
                .build(),

            Skill.builder("llm_usage")
                .categoryId("AI_ML")
                .name("LLM活用・プロンプトエンジニアリング")
                .nameEn("LLM & Prompt Engineering")
                .shortDescription("LLMの効果的な活用方法と高品質なプロンプト設計")
                .overview("""
                    Large Language Model (LLM) はテキスト生成・要約・分類・コード生成など
                    幅広いタスクをこなせる汎用AIモデル。
                    プロンプトエンジニアリングとは、望ましい出力を得るための入力設計技術。
                    Few-shot・Chain-of-Thought・System Promptの設計が核心。
                    """)
                .whyItMatters("""
                    AIツールを使いこなせるエンジニアと使えないエンジニアで
                    生産性が10倍以上変わる時代に突入している。
                    PMとしても、AI機能の要件定義にはLLMの特性理解が必須。
                    """)
                .howToLearn("""
                    1. OpenAI / Anthropic のプロンプトエンジニアリングガイドを読む
                    2. Claude・GPT-4を使い倒して特性を体感する
                    3. Promptfooでプロンプトのバージョン管理と評価を行う
                    4. 実業務の自動化タスクを1つLLMで解決してみる
                    """)
                .aiEraRelevance("""
                    AI時代の「Excelスキル」に相当する必須ビジネススキル。
                    エンジニアだけでなく全職種に求められるが、
                    エンジニアはAPI連携・システム組み込みまで習得すべき。
                    """)
                .keyTopics(List.of(
                    "Zero-shot / Few-shot プロンプティング",
                    "Chain-of-Thought (CoT) プロンプティング",
                    "System Prompt設計",
                    "トークン管理・コスト最適化",
                    "Claude / GPT / Gemini APIの活用"
                ))
                .prerequisites(List.of("Python基礎", "REST API理解"))
                .nextSkillIds(List.of("rag", "ai_agents"))
                .resources(List.of(
                    "Anthropic Prompt Engineering Guide (公式)",
                    "OpenAI Prompt Engineering Guide (公式)",
                    "Promptingguide.ai (無料サイト)"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(40)
                .build(),

            Skill.builder("rag")
                .categoryId("AI_ML")
                .name("RAG（検索拡張生成）")
                .nameEn("Retrieval Augmented Generation")
                .shortDescription("外部知識をLLMに組み込む検索拡張生成の設計と実装")
                .overview("""
                    RAGとは、LLMの知識カットオフや社内ドキュメント参照の限界を克服するため、
                    外部データベースから関連文書を検索してLLMのコンテキストに注入する手法。
                    埋め込みモデル（Embedding）→ベクターDB検索→LLM生成 のパイプラインが基本。
                    """)
                .whyItMatters("""
                    社内ドキュメントQ&A・コードレビュー支援・ナレッジベース構築など
                    企業のAI活用で最も使われるパターン。
                    ファインチューニングより低コストで知識を更新できるため主流になっている。
                    """)
                .howToLearn("""
                    1. LangChain / LlamaIndexのドキュメントでRAGパイプラインを実装
                    2. ChromaDB や Pinecone でベクター検索を体験
                    3. チャンキング戦略（固定サイズ・セマンティック）を比較実験
                    4. 評価指標（RAGAS）でRAGの品質を測定する
                    """)
                .aiEraRelevance("""
                    2024〜2025年に急速に普及した企業AI活用の中心技術。
                    GraphRAG・Adaptive RAGなど進化が速く、継続的学習が必要。
                    """)
                .keyTopics(List.of(
                    "Embeddingモデル（OpenAI / Sentence-BERT）",
                    "ベクターデータベース（ChromaDB, Pinecone, pgvector）",
                    "チャンキング戦略",
                    "リランキング（Reranking）",
                    "RAGの評価（RAGAS フレームワーク）"
                ))
                .prerequisites(List.of("LLM活用・プロンプトエンジニアリング", "Python中級"))
                .nextSkillIds(List.of("ai_agents", "vector_db"))
                .resources(List.of(
                    "LangChain Documentation (公式)",
                    "LlamaIndex Documentation (公式)",
                    "書籍: 「RAG駆動開発」"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.CRITICAL)
                .estimatedHours(60)
                .build(),

            Skill.builder("ai_agents")
                .categoryId("AI_ML")
                .name("AIエージェント開発")
                .nameEn("AI Agent Development")
                .shortDescription("自律的にタスクを実行するAIエージェントの設計と実装")
                .overview("""
                    AIエージェントとは、LLMが外部ツール（検索・コード実行・API呼び出し）を
                    自律的に使いながら複雑なタスクを完遂するシステム。
                    ReActパターン・ツール使用・マルチエージェント協調が核心的な概念。
                    LangGraph・AutoGen・CrewAIなどのフレームワークが存在する。
                    """)
                .whyItMatters("""
                    Claude Code自体がAIエージェントの実例。
                    2025年以降「エージェントが人間の代わりに作業する」時代が本格化。
                    エンジニアはエージェントを使う側だけでなく、設計する側になれる必要がある。
                    """)
                .howToLearn("""
                    1. LangGraphの公式チュートリアルでステートマシン型エージェントを実装
                    2. Tool CallingのAPIを直接触り、ツール定義の書き方を習得
                    3. マルチエージェントシステムを小さなタスクで自作する
                    4. エージェントの評価・デバッグ方法（LangSmith等）を学ぶ
                    """)
                .aiEraRelevance("""
                    「AIエージェントエンジニア」はAI時代の新職種。
                    既存のSWEが最も自然に移行できる領域のひとつ。
                    エージェントのオーケストレーション設計はアーキテクチャスキルと直結する。
                    """)
                .keyTopics(List.of(
                    "ReActフレームワーク（Reasoning + Acting）",
                    "Tool Calling / Function Calling",
                    "メモリ管理（短期・長期）",
                    "マルチエージェント協調",
                    "LangGraph / AutoGen / CrewAI"
                ))
                .prerequisites(List.of("RAG", "LLM活用・プロンプトエンジニアリング"))
                .nextSkillIds(List.of("mlops"))
                .resources(List.of(
                    "LangGraph Documentation (公式)",
                    "Anthropic Agent Patterns Guide",
                    "AutoGen Documentation (Microsoft)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("mlops")
                .categoryId("AI_ML")
                .name("MLOps")
                .nameEn("MLOps / LLMOps")
                .shortDescription("機械学習モデルの本番運用・監視・継続的改善の仕組み")
                .overview("""
                    MLOpsとはMLシステムの開発〜本番運用を効率化するプラクティスの総称。
                    モデル管理（MLflow）・パイプライン自動化（Kubeflow/Airflow）・
                    モデル監視（データドリフト検出）・CI/CDをMLに適用する手法を含む。
                    LLMOpsはLLMに特化した評価・ファインチューニング・デプロイを扱う。
                    """)
                .whyItMatters("""
                    「動くモデルを作る」と「ビジネスで使い続けるモデルを運用する」は全く別物。
                    MLOpsなしではモデルの陳腐化・障害対応・再現性確保が困難になる。
                    PMとして機能開発のロードマップを引くにも理解が必要。
                    """)
                .howToLearn("""
                    1. MLflowをローカルで立ち上げ、実験管理を体験
                    2. GitHub ActionsでML学習パイプラインのCI/CDを構築
                    3. Evidently AIでデータドリフト監視を実装
                    4. LLMOps: LangSmith / Langfuse でLLMトレーシングを設定
                    """)
                .aiEraRelevance("""
                    LLMを本番投入するには評価・監視・コスト管理が不可欠。
                    LLMOpsツール（Langfuse・Phoenix・Arize）の市場が急成長中。
                    """)
                .keyTopics(List.of(
                    "実験管理（MLflow, Weights & Biases）",
                    "モデルレジストリ・バージョン管理",
                    "特徴量ストア",
                    "モデル監視・ドリフト検出",
                    "LLMOps（評価・トレーシング・ファインチューニング管理）"
                ))
                .prerequisites(List.of("機械学習基礎", "Docker", "CI/CD"))
                .nextSkillIds(List.of())
                .resources(List.of(
                    "MLflow Documentation (公式)",
                    "書籍: 「Designing Machine Learning Systems」(Chip Huyen)",
                    "Langfuse Documentation (LLMOps)"
                ))
                .difficulty(Difficulty.ADVANCED)
                .priority(Priority.HIGH)
                .estimatedHours(80)
                .build(),

            Skill.builder("vector_db")
                .categoryId("AI_ML")
                .name("ベクターデータベース")
                .nameEn("Vector Database")
                .shortDescription("高次元ベクトルの近似最近傍探索（ANN）と主要DBの使い方")
                .overview("""
                    ベクターDBはEmbeddingベクトルを高速に検索するための専用データベース。
                    Pinecone・Weaviate・Qdrant・Milvusなどの専用製品と、
                    pgvector（PostgreSQL拡張）・ChromaDB（軽量ローカル）がある。
                    インデックス手法（HNSW・IVF）の理解が性能チューニングに重要。
                    """)
                .whyItMatters("""
                    RAGとセマンティック検索の基盤技術。
                    従来のキーワード検索では不可能な「意味的類似性による検索」を実現する。
                    AI機能を持つ製品の設計でほぼ必ず登場する技術。
                    """)
                .howToLearn("""
                    1. ChromaDBでローカル環境にベクターDBを構築
                    2. OpenAI EmbeddingsまたはSentence-BERTでベクター化を実装
                    3. HNSWとIVFのインデックス違いを実測で比較
                    4. pgvectorをPostgreSQLに追加してSQL経由で検索
                    """)
                .keyTopics(List.of(
                    "Embeddingとベクター空間",
                    "近似最近傍探索（ANN）アルゴリズム",
                    "HNSW / IVFインデックス",
                    "主要製品比較（Pinecone, Qdrant, pgvector, ChromaDB）",
                    "ハイブリッド検索（キーワード+ベクター）"
                ))
                .prerequisites(List.of("RAG", "データベース基礎"))
                .resources(List.of(
                    "Qdrant Documentation (公式)",
                    "pgvector GitHub README",
                    "ChromaDB Getting Started"
                ))
                .difficulty(Difficulty.INTERMEDIATE)
                .priority(Priority.HIGH)
                .estimatedHours(30)
                .build()
        );
    }
}
