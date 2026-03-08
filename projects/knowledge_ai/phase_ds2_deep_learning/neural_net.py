"""
phase_ds2_deep_learning/neural_net.py
========================================
PyTorch で実装する深層学習 - テキスト分類 & Attention

このフェーズで学ぶこと:
  - ニューラルネットワークの基礎（順伝播・逆伝播）
  - テキストの埋め込み表現（Embedding層）
  - LSTM（時系列・文脈を考慮したモデル）
  - Attention機構（なぜTransformerが強いのか）
  - 転移学習（事前学習済みモデルの活用）

実行方法:
  pip install torch torchvision
  python neural_net.py

考えてほしい疑問:
  Q1. なぜ「活性化関数」が必要か？（線形変換だけでは何ができないか）
  Q2. バッチ正規化は何を解決するか？（勾配消失・学習の不安定さ）
  Q3. Attention は何を「注意」しているのか？（クエリ・キー・バリューの意味）
  Q4. 事前学習済みモデル（BERT等）の転移学習が強い理由は？
  Q5. エポック数を増やすと必ず精度が上がるか？（過学習の検出方法）
"""

import math
import warnings
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

warnings.filterwarnings("ignore")

# ─── ハイパーパラメータ ─────────────────────────────────────
@dataclass
class Config:
    vocab_size: int = 5000
    embed_dim: int = 64
    hidden_dim: int = 128
    num_classes: int = 9       # タグの種類数
    max_seq_len: int = 50
    batch_size: int = 16
    epochs: int = 20
    lr: float = 0.001
    dropout: float = 0.3


# ─── データセット ──────────────────────────────────────────

# Phase DS1 と同じデータを使用
RAW_DATA = [
    ("Pythonの型ヒント完全ガイド TypedDictやProtocolを使った型安全なコード", "Python"),
    ("FastAPI入門 Pydanticとの統合 非同期処理 依存性注入", "Python"),
    ("scikit-learnで始める機械学習 分類 回帰 クラスタリングの基礎", "ML"),
    ("Random Forestの仕組み 決定木のアンサンブルとバギング", "ML"),
    ("勾配ブースティング徹底解説 XGBoost LightGBM CatBoostの違い", "ML"),
    ("Docker Composeで開発環境を構築 マルチコンテナ構成とネットワーク", "Infra"),
    ("KubernetesのPodとDeployment コンテナオーケストレーションの基本", "Infra"),
    ("PostgreSQLのインデックス最適化 B-treeとGINインデックス", "DB"),
    ("SQLのウィンドウ関数 OVER句 PARTITION BY ROW_NUMBER", "DB"),
    ("Transformerアーキテクチャ Self-AttentionとMulti-Head Attention", "DL"),
    ("PyTorchで実装するCNN 画像分類をゼロから実装する", "DL"),
    ("LSTMと時系列予測 時系列データの前処理とモデル設計", "DL"),
    ("Terraformでインフラをコード化 AWS VPCとECS", "Infra"),
    ("JWTとOAuth2の仕組み 認証フローとトークン検証", "Security"),
    ("SQLインジェクション対策 プレースホルダーとORM", "Security"),
    ("データパイプラインの設計 Airflow DAGとdbt", "Data"),
    ("Goの並行処理パターン goroutine channel sync.WaitGroup", "Go"),
    ("Go言語でHTTPサーバー net/httpとchi router REST API", "Go"),
    ("Next.jsのServer Components クライアントとサーバーの境界", "Frontend"),
    ("React HooksとState管理 useState useReducer Context API", "Frontend"),
    ("OKR設計の実践 テックリードとしての目標設定と計測", "PM"),
    ("アジャイル開発とスクラム スプリントプランニングとベロシティ", "PM"),
    ("特徴量エンジニアリングの技法 カテゴリ変数 欠損値 スケーリング", "ML"),
    ("ベクターデータベースの選択 Pinecone ChromaDB pgvectorの比較", "ML"),
    ("RAGシステムの設計 Retrieval精度とGeneration品質のバランス", "ML"),
    ("Pythonの非同期処理 asyncio awaitの仕組みとイベントループ", "Python"),
    ("ニューラルネットワークの最適化 Adam SGD 学習率スケジューリング", "DL"),
    ("セキュリティ監査の手順 OWASPトップ10と脆弱性スキャン", "Security"),
    ("dbtでデータ変換 CTEとウィンドウ関数を使ったモデル設計", "Data"),
    ("テックリードのコミュニケーション術 1on1とフィードバックの技法", "PM"),
]

# データ拡張（各クラス最低5件以上確保）
AUGMENTED_DATA = RAW_DATA * 6  # 180サンプル


class SimpleTokenizer:
    """
    シンプルなホワイトスペーストークナイザー
    実務では BertTokenizer や tiktoken を使う

    [実装してみよう] 文字単位のトークナイザーを実装する（日本語向け）
    """
    def __init__(self, vocab_size: int = 5000):
        self.vocab_size = vocab_size
        self.word2idx: dict[str, int] = {"<PAD>": 0, "<UNK>": 1}
        self.idx2word: dict[int, str] = {0: "<PAD>", 1: "<UNK>"}

    def build_vocab(self, texts: list[str]) -> None:
        from collections import Counter
        word_counts = Counter()
        for text in texts:
            word_counts.update(text.split())

        for word, _ in word_counts.most_common(self.vocab_size - 2):
            idx = len(self.word2idx)
            self.word2idx[word] = idx
            self.idx2word[idx] = word

    def encode(self, text: str, max_len: int) -> list[int]:
        tokens = [self.word2idx.get(w, 1) for w in text.split()]  # 1 = <UNK>
        # パディングまたはトランケーション
        if len(tokens) < max_len:
            tokens += [0] * (max_len - len(tokens))  # 0 = <PAD>
        else:
            tokens = tokens[:max_len]
        return tokens


class NoteDataset(Dataset):
    def __init__(self, data: list[tuple[str, str]], tokenizer: SimpleTokenizer,
                 label2idx: dict[str, int], max_len: int):
        self.data = data
        self.tokenizer = tokenizer
        self.label2idx = label2idx
        self.max_len = max_len

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        text, label = self.data[idx]
        tokens = self.tokenizer.encode(text, self.max_len)
        return (
            torch.tensor(tokens, dtype=torch.long),
            torch.tensor(self.label2idx[label], dtype=torch.long),
        )


# ─── モデル定義 ────────────────────────────────────────────

class SimpleNN(nn.Module):
    """
    最もシンプルなニューラルネット: Embedding → 平均プーリング → FC層

    考えてほしい疑問:
      - なぜ Embedding 層を使うのか？（one-hotの問題点は？）
      - 平均プーリングの問題は何か？（語順が失われる）
    """
    def __init__(self, cfg: Config):
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(cfg.dropout)
        self.fc = nn.Sequential(
            nn.Linear(cfg.embed_dim, cfg.hidden_dim),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.hidden_dim, cfg.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len)
        embedded = self.embedding(x)          # (batch, seq_len, embed_dim)
        # パディングを除外して平均（語順を無視するので BoW に近い）
        mask = (x != 0).float().unsqueeze(-1)
        pooled = (embedded * mask).sum(1) / mask.sum(1).clamp(min=1)  # (batch, embed_dim)
        return self.fc(self.dropout(pooled))


class LSTMClassifier(nn.Module):
    """
    LSTM: 語順と文脈を考慮したテキスト分類

    考えてほしい疑問:
      - bidirectional=True にすると何が変わるか？
      - LSTM が「長期依存関係」を学習できる仕組みは？（セル状態とゲート）
      - num_layers=2 の LSTM で何が起きるか？

    [実装してみよう]
      GRU（GatedRecurrentUnit）に置き換えて速度と精度を比較する
    """
    def __init__(self, cfg: Config):
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=cfg.embed_dim,
            hidden_size=cfg.hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=cfg.dropout,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(cfg.dropout)
        self.fc = nn.Linear(cfg.hidden_dim * 2, cfg.num_classes)  # *2 for bidirectional

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded = self.dropout(self.embedding(x))          # (batch, seq, embed)
        output, (hidden, _) = self.lstm(embedded)           # output: (batch, seq, hidden*2)
        # 最後の hidden state を使用（前向き + 後ろ向き）
        last_hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)  # (batch, hidden*2)
        return self.fc(self.dropout(last_hidden))


class SelfAttentionClassifier(nn.Module):
    """
    Self-Attention: Transformer の核心部分

    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V

    考えてほしい疑問:
      - Q, K, V はそれぞれ何を表すか？（検索クエリ・キー・値）
      - sqrt(d_k) で割る理由は？（ドット積が大きくなりすぎるのを防ぐ）
      - Multi-Head Attention は Single-Head より何が優れているか？

    [実装してみよう]
      Positional Encoding を追加して語順を考慮させる
      hint: sin/cos 関数を使って位置情報をエンコード
    """
    def __init__(self, cfg: Config):
        super().__init__()
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.embed_dim, padding_idx=0)
        self.attention = nn.MultiheadAttention(
            embed_dim=cfg.embed_dim,
            num_heads=4,  # embed_dim must be divisible by num_heads
            dropout=cfg.dropout,
            batch_first=True,
        )
        self.norm = nn.LayerNorm(cfg.embed_dim)
        self.dropout = nn.Dropout(cfg.dropout)
        self.fc = nn.Sequential(
            nn.Linear(cfg.embed_dim, cfg.hidden_dim),
            nn.GELU(),  # GPTシリーズが採用する活性化関数
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.hidden_dim, cfg.num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(x)                        # (batch, seq, embed)

        # Self-Attention: 各トークンが他のトークンに「注意」する
        # padding mask: PAD トークンを無視
        key_padding_mask = (x == 0)
        attn_out, _ = self.attention(
            embedded, embedded, embedded,
            key_padding_mask=key_padding_mask,
        )

        # Residual Connection + Layer Norm（Transformerの基本構造）
        out = self.norm(embedded + self.dropout(attn_out))  # (batch, seq, embed)

        # CLSトークンの代わりに平均プーリング
        mask = (~key_padding_mask).float().unsqueeze(-1)
        pooled = (out * mask).sum(1) / mask.sum(1).clamp(min=1)

        return self.fc(pooled)


# ─── 学習・評価ループ ────────────────────────────────────────

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    cfg: Config,
    device: torch.device,
) -> tuple[list[float], list[float]]:
    """
    学習ループ。実務では PyTorch Lightning か Hugging Face Trainer を使うことが多い。

    [実装してみよう]
      1. Early Stopping を実装する（val_loss が改善しなくなったら学習停止）
      2. Learning Rate Scheduler を追加する（CosineAnnealingLR等）
      3. TensorBoard にロスをプロットする
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=cfg.lr, weight_decay=1e-4)
    # 学習率スケジューリング（10エポックごとに0.5倍）
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    train_losses, val_accs = [], []

    for epoch in range(cfg.epochs):
        # ─── 訓練フェーズ ────────────────────────
        model.train()
        total_loss = 0.0
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(X)
            loss = criterion(logits, y)
            loss.backward()
            # 勾配クリッピング（勾配爆発を防ぐ）
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()
        avg_loss = total_loss / len(train_loader)
        train_losses.append(avg_loss)

        # ─── 評価フェーズ ────────────────────────
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device)
                logits = model(X)
                preds = logits.argmax(dim=1)
                correct += (preds == y).sum().item()
                total += y.size(0)

        val_acc = correct / total
        val_accs.append(val_acc)

        if (epoch + 1) % 5 == 0:
            print(f"  Epoch {epoch+1:2d}/{cfg.epochs} | Loss: {avg_loss:.4f} | Val Acc: {val_acc:.3f}")

    return train_losses, val_accs


# ─── メイン ──────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   Phase DS2: Deep Learning - テキスト分類 (PyTorch)   ║")
    print("╚═══════════════════════════════════════════════════════╝")

    cfg = Config()
    device = torch.device("mps" if torch.backends.mps.is_available()
                          else "cuda" if torch.cuda.is_available()
                          else "cpu")
    print(f"\n🖥️  使用デバイス: {device}")

    # ─── データ準備 ────────────────────────────
    labels = sorted(set(label for _, label in AUGMENTED_DATA))
    label2idx = {label: i for i, label in enumerate(labels)}
    cfg.num_classes = len(labels)
    print(f"📦 データ: {len(AUGMENTED_DATA)}件 / クラス: {labels}")

    tokenizer = SimpleTokenizer(cfg.vocab_size)
    tokenizer.build_vocab([text for text, _ in AUGMENTED_DATA])
    print(f"📝 語彙サイズ: {len(tokenizer.word2idx)}語")

    # 訓練/検証分割（8:2）
    split = int(len(AUGMENTED_DATA) * 0.8)
    import random
    random.seed(42)
    shuffled = AUGMENTED_DATA.copy()
    random.shuffle(shuffled)
    train_data, val_data = shuffled[:split], shuffled[split:]

    train_dataset = NoteDataset(train_data, tokenizer, label2idx, cfg.max_seq_len)
    val_dataset = NoteDataset(val_data, tokenizer, label2idx, cfg.max_seq_len)
    train_loader = DataLoader(train_dataset, batch_size=cfg.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=cfg.batch_size)

    # ─── 3つのアーキテクチャを比較 ────────────
    architectures = [
        ("Simple NN (平均プーリング)", SimpleNN(cfg)),
        ("LSTM (Bidirectional)", LSTMClassifier(cfg)),
        ("Self-Attention (Transformer風)", SelfAttentionClassifier(cfg)),
    ]

    results = {}
    for name, model in architectures:
        model = model.to(device)
        param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\n{'═' * 60}")
        print(f"▶ {name} (パラメータ数: {param_count:,})")
        print("─" * 60)

        train_losses, val_accs = train_model(model, train_loader, val_loader, cfg, device)

        final_acc = val_accs[-1]
        results[name] = final_acc
        print(f"  ✅ 最終検証精度: {final_acc:.3f}")

    # ─── 結果比較 ──────────────────────────────
    print("\n" + "═" * 60)
    print("📊 アーキテクチャ比較サマリー")
    print("─" * 60)
    for name, acc in sorted(results.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(acc * 30)
        print(f"  {name[:35]:35s} {bar} {acc:.3f}")

    # ─── 転移学習の説明 ──────────────────────────
    print("\n" + "═" * 60)
    print("📚 転移学習（Fine-tuning）について")
    print("─" * 60)
    print("""
実務での標準的なアプローチ（2025年現在）:

1. 事前学習済みモデルを使う
   from transformers import AutoTokenizer, AutoModelForSequenceClassification
   model = AutoModelForSequenceClassification.from_pretrained("cl-tohoku/bert-base-japanese")

2. 最終層だけ Fine-tuning（少ないデータでも動く）
   # BERT の重みは固定、分類層だけ学習
   for param in model.bert.parameters():
       param.requires_grad = False

3. なぜ強いのか？
   - BERT はウィキペディア等の大量テキストで「言語を理解」している
   - あなたのデータはタスク固有の「パターン」を学ぶだけでよい
   - 10件のデータでも動く（ゼロから学習なら数千件必要）

[実装してみよう]
   pip install transformers sentence-transformers
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer("intfloat/multilingual-e5-small")
   embeddings = model.encode(["Pythonの型ヒント", "機械学習の基礎"])
   → これが Phase 2 の RAG で使っている埋め込みの実体！
""")

    print("✅ 完了！次のステップ:")
    print("  → Phase DS3: MLflow で実験管理 & モデル本番化")
    print("  → [実装してみよう] sentence-transformers で埋め込みを取得して")
    print("     コサイン類似度によるノート検索を実装する")


if __name__ == "__main__":
    main()
