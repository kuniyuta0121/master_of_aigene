"""
Phase 2: RAG（検索拡張生成）サービス
========================================
学習目標:
  - Embedding → ベクターDB検索 → LLM生成 の3ステップを自分で実装する
  - チャンキング戦略の違いを体感する
  - RAGの品質がなぜ「検索精度」に左右されるかを理解する

考えてほしい疑問:
  Q1. なぜ全ノートをそのままLLMに渡さないのか？（コンテキスト長・コスト）
  Q2. チャンクサイズ（chunk_size）を大きくする/小さくすると何が変わるか？
  Q3. cosine similarity と dot product の違いは？どちらをいつ使うか？
  Q4. RAGの回答精度を測定するにはどんな指標（メトリクス）を使うか？

事前セットアップ:
  pip install langchain langchain-anthropic langchain-community chromadb
  export ANTHROPIC_API_KEY="your-key-here"
"""

import os
from dataclasses import dataclass
from typing import Optional

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage


@dataclass
class SearchResult:
    """ベクター検索の結果"""
    content: str
    source_title: str
    score: float      # 類似度スコア（高いほど関連性が高い）
    note_id: int


class EmbeddingService:
    """
    テキスト → ベクター変換サービス

    モデル選択の考え方:
      - OpenAI text-embedding-3-small: 高品質だがAPI費用がかかる
      - HuggingFace all-MiniLM-L6-v2: 無料・ローカル・日本語も動く（品質は落ちる）
      - HuggingFace multilingual-e5-small: 多言語特化（日本語に強い）

    [実装してみよう] multilingual-e5-small に切り替えて日本語の精度を比較する
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, query: str) -> list[float]:
        return self.model.embed_query(query)


class VectorStore:
    """
    ChromaDB を使ったベクターストア

    ChromaDB を選んだ理由:
      - ローカルで動く（API費用ゼロ）
      - Pythonから簡単に使える
      - 本番ではPinecone/Qdrantに切り替え可能（インターフェースは同じ）

    [考える] なぜベクターDBには通常のDB（SQLite等）ではなくHNSWインデックスを使うのか？
    """

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="knowledge_ai",
            metadata={"hnsw:space": "cosine"},  # コサイン類似度を使用
        )
        self.embedding_service = EmbeddingService()

    def add_note(self, note_id: int, title: str, content: str) -> None:
        """
        ノートをベクターストアに追加する。

        チャンキング戦略:
          - 長いテキストはそのままEmbeddingすると精度が下がる
          - RecursiveCharacterTextSplitter は段落→文→単語の順で分割する

        [実装してみよう] SemanticChunker（意味的にまとまったチャンク）に切り替えてみる
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,      # 1チャンクあたりの最大文字数
            chunk_overlap=50,    # チャンク間のオーバーラップ（文脈を保つため）
            separators=["\n\n", "\n", "。", "、", " "],
        )

        full_text = f"{title}\n\n{content}"
        chunks = splitter.split_text(full_text)

        # 各チャンクをEmbeddingしてDBに保存
        embeddings = self.embedding_service.embed(chunks)

        self.collection.upsert(
            ids=[f"note_{note_id}_chunk_{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"note_id": note_id, "title": title, "chunk_index": i}
                       for i in range(len(chunks))],
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        クエリに最も近いチャンクを検索する。

        [考える] top_k を大きくするとLLMの回答精度は上がるか？
        コスト・コンテキスト長とのトレードオフを考えてみよう。
        """
        query_embedding = self.embedding_service.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                search_results.append(SearchResult(
                    content=doc,
                    source_title=meta["title"],
                    score=1 - dist,  # distanceをsimilarityに変換
                    note_id=meta["note_id"],
                ))

        return search_results

    def delete_note(self, note_id: int) -> None:
        """ノート削除時にベクターDBからも削除する"""
        # note_id に一致するチャンクを全て削除
        existing = self.collection.get(where={"note_id": note_id})
        if existing["ids"]:
            self.collection.delete(ids=existing["ids"])


class RAGService:
    """
    RAGパイプライン全体の統合

    フロー:
    1. クエリをEmbeddingして類似チャンクを検索（Retrieve）
    2. 関連チャンクをLLMのコンテキストに注入（Augment）
    3. LLMが回答を生成（Generate）

    [実装してみよう]
    - スコアが低い（閾値以下の）チャンクは除外する
    - 同じノートのチャンクが複数hitした場合に重複をまとめる
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",  # 高速・低コスト
            api_key=os.environ["ANTHROPIC_API_KEY"],
            max_tokens=1024,
        )

    def answer(self, question: str, score_threshold: float = 0.3) -> dict:
        """
        質問に対してRAGで回答する。
        """
        # Step 1: 関連ノートを検索
        search_results = self.vector_store.search(question, top_k=5)

        # スコアが低すぎる結果は除外
        relevant = [r for r in search_results if r.score >= score_threshold]

        if not relevant:
            return {
                "answer": "関連するノートが見つかりませんでした。まずナレッジを追加してください。",
                "sources": [],
            }

        # Step 2: コンテキストを構築
        context = "\n\n---\n\n".join([
            f"[出典: {r.source_title}]\n{r.content}"
            for r in relevant
        ])

        # Step 3: LLMで回答生成
        messages = [
            SystemMessage(content="""あなたはユーザーのナレッジベースを参照して質問に答えるAIアシスタントです。
以下のルールに従ってください:
- 提供されたコンテキストの情報のみを使って回答してください
- コンテキストに回答がない場合は「ナレッジベースに情報がありません」と答えてください
- 回答には出典のタイトルを明記してください
- 日本語で回答してください"""),
            HumanMessage(content=f"""コンテキスト:
{context}

質問: {question}"""),
        ]

        response = self.llm.invoke(messages)

        return {
            "answer": response.content,
            "sources": [
                {"title": r.source_title, "score": round(r.score, 3), "note_id": r.note_id}
                for r in relevant
            ],
        }
