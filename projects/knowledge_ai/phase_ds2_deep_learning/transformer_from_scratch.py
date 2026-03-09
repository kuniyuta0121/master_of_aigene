"""
phase_ds2_deep_learning/transformer_from_scratch.py
====================================================
Transformer と Backpropagation をゼロから実装

なぜ「ゼロから」が不可欠か:
  「Attention Is All You Need」(2017) を読んで理解できるか？
  PyTorch の autograd が何をしているか説明できるか？
  Google Brain / DeepMind / Tesla AI の面接では
  「Backpropagation を数式で説明してください」
  「Self-Attention の計算量はなぜ O(n²) か？」
  「なぜ Positional Encoding が必要か？」
  が標準的な質問として出る。

実装内容:
  Part 1: Backpropagation from scratch (NumPy のみ)
            - 自動微分の仕組みを理解する
            - 各層の forward / backward を手動実装
  Part 2: Transformer Encoder from scratch (NumPy のみ)
            - Positional Encoding（なぜ必要か）
            - Scaled Dot-Product Attention（数式から実装）
            - Multi-Head Attention
            - Position-wise FFN
            - Layer Normalization
            - Residual Connection

実行方法:
  pip install numpy  (NumPy のみ)
  python transformer_from_scratch.py

考えてほしい疑問:
  Q1. なぜ attention score を √d_k で割るのか？
      → d_k が大きいとドット積が大きくなり softmax が飽和する（勾配消失）
  Q2. Multi-Head Attention のヘッド数を増やすと何が起きるか？
      → 異なる「注意パターン」を並列に学習できる
  Q3. Encoder と Decoder の違いは何か？
      → Decoder は自己回帰（causal mask）と交差注意を持つ
  Q4. BERT（Encoder のみ）と GPT（Decoder のみ）の設計思想の違いは？
  Q5. Flash Attention はなぜ速いか？（IO-aware計算）
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 1: Backpropagation from Scratch
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Tensor:
    """
    スカラー値の計算グラフノード（PyTorch の autograd の最小版）

    逆伝播（バックプロパゲーション）の仕組み:
      1. Forward: 各演算で計算結果と「どうやって微分するか」を記録
      2. Backward: 最終出力から連鎖律（Chain Rule）で勾配を逆伝播

    Chain Rule（連鎖律）:
      z = f(g(x)) のとき
      dz/dx = dz/dg * dg/dx
      ← この「掛け算の連鎖」がバックプロパゲーションの本質

    考えてほしい疑問:
      ・計算グラフとは何か？（数式を有向非巡回グラフとして表現）
      ・勾配の蓄積（+=）は何を意味するか？（1つのノードが複数に使われる場合）
    """

    def __init__(self, data: float, _children: tuple = (), label: str = ""):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(_children)
        self.label = label

    def __repr__(self):
        return f"Tensor({self.data:.4f}, grad={self.grad:.4f})"

    def __add__(self, other: "Tensor | float") -> "Tensor":
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data + other.data, (self, other))

        def _backward():
            # d(a+b)/da = 1, d(a+b)/db = 1
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: "Tensor | float") -> "Tensor":
        other = other if isinstance(other, Tensor) else Tensor(other)
        out = Tensor(self.data * other.data, (self, other))

        def _backward():
            # d(a*b)/da = b, d(a*b)/db = a
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def __pow__(self, exponent: float) -> "Tensor":
        out = Tensor(self.data ** exponent, (self,))

        def _backward():
            # d(x^n)/dx = n * x^(n-1)
            self.grad += exponent * (self.data ** (exponent - 1)) * out.grad

        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + (-other)

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def relu(self) -> "Tensor":
        out = Tensor(max(0.0, self.data), (self,))

        def _backward():
            # d(relu(x))/dx = 1 if x > 0 else 0
            self.grad += (out.data > 0) * out.grad

        out._backward = _backward
        return out

    def tanh(self) -> "Tensor":
        t = np.tanh(self.data)
        out = Tensor(t, (self,))

        def _backward():
            # d(tanh(x))/dx = 1 - tanh(x)²
            self.grad += (1 - t ** 2) * out.grad

        out._backward = _backward
        return out

    def log(self) -> "Tensor":
        out = Tensor(np.log(self.data + 1e-8), (self,))

        def _backward():
            self.grad += (1 / self.data) * out.grad

        out._backward = _backward
        return out

    def backward(self) -> None:
        """トポロジカルソートで逆順に backward を呼ぶ"""
        topo = []
        visited = set()

        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)

        self.grad = 1.0  # 最終出力のスカラーなので勾配は1
        for node in reversed(topo):
            node._backward()


def demo_backprop() -> None:
    """
    手動で計算した勾配と autograd の勾配を比較する

    例: L = ((x * w + b) - y)²  (1次元の線形回帰の損失)
    """
    print("━" * 60)
    print("📐 Part 1: Backpropagation from Scratch")
    print("━" * 60)

    x = Tensor(2.0, label="x")
    w = Tensor(3.0, label="w")   # 学習パラメータ
    b = Tensor(1.0, label="b")   # バイアス
    y = Tensor(10.0, label="y")  # 正解

    # Forward pass: L = (xw + b - y)²
    xw = x * w           # 6.0
    xw_b = xw + b        # 7.0
    diff = xw_b - y      # -3.0
    L = diff ** 2        # 9.0

    print(f"  Forward:  x={x.data}, w={w.data}, b={b.data}")
    print(f"  xw+b = {xw_b.data}, y = {y.data}")
    print(f"  L = (xw+b-y)² = {L.data}")

    # Backward pass
    L.backward()

    # 手動計算との照合
    # dL/dw = 2(xw+b-y) * x = 2(-3)(2) = -12
    # dL/db = 2(xw+b-y) = 2(-3) = -6
    print(f"\n  勾配 (autograd):  dL/dw = {w.grad:.1f},  dL/db = {b.grad:.1f}")
    print(f"  勾配 (手計算):    dL/dw = {2*(xw_b.data - y.data)*x.data:.1f}, dL/db = {2*(xw_b.data - y.data):.1f}")
    print("  ← 一致していれば実装が正しい")

    # 1ステップの勾配降下
    lr = 0.1
    w.data -= lr * w.grad
    b.data -= lr * b.grad
    print(f"\n  1ステップ後: w={w.data:.2f}, b={b.data:.2f}")
    print(f"  新しい L = {((x.data * w.data + b.data) - y.data)**2:.2f} (減少していればOK)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Part 2: Transformer from Scratch
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PositionalEncoding:
    """
    位置エンコーディング: トークンの「位置」情報を埋め込みに加える

    なぜ必要か:
      Transformer は RNN と違い、全トークンを並列処理する。
      「I love you」と「You love I」が同じ表現になってしまう。
      → 位置情報を何らかの形で注入する必要がある。

    数式（Vaswani et al. 2017）:
      PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
      PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

    なぜ sin/cos か？
      ・各位置のエンコーディングが一意（同じ値が繰り返さない）
      ・PE(pos+k) は PE(pos) の線形変換で表せる（相対位置を学習可能）
      ・モデルは訓練時より長いシーケンスを処理できる（外挿可能）
    """

    def __init__(self, d_model: int, max_seq_len: int = 5000):
        self.d_model = d_model

        # PE の計算 (max_seq_len, d_model)
        pos = np.arange(max_seq_len)[:, np.newaxis]       # (max_len, 1)
        dim = np.arange(0, d_model, 2)[np.newaxis, :]     # (1, d_model/2)
        angles = pos / (10000 ** (dim / d_model))          # (max_len, d_model/2)

        pe = np.zeros((max_seq_len, d_model))
        pe[:, 0::2] = np.sin(angles)   # 偶数次元: sin
        pe[:, 1::2] = np.cos(angles)   # 奇数次元: cos

        self.pe = pe  # (max_seq_len, d_model)

    def __call__(self, x: NDArray) -> NDArray:
        """x: (batch, seq_len, d_model)"""
        seq_len = x.shape[1]
        return x + self.pe[:seq_len]  # ブロードキャスト


def scaled_dot_product_attention(
    Q: NDArray,
    K: NDArray,
    V: NDArray,
    mask: NDArray | None = None,
) -> tuple[NDArray, NDArray]:
    """
    Scaled Dot-Product Attention

    Attention(Q, K, V) = softmax(QK^T / √d_k) V

    直感:
      ・Q (Query): 「何を探しているか」
      ・K (Key):   「何が格納されているか」
      ・V (Value): 「実際に取り出す情報」

      QK^T で「クエリとキーの類似度」を計算
      √d_k で正規化（次元数が大きいとドット積が大きくなりすぎる）
      softmax で確率分布に変換（注意の重みを合計1にする）
      V との重み付き和で「注目すべき情報」を取り出す

    計算量: O(n² d_k)  ← n はシーケンス長
      → GPT-4 が長文で遅い/高コストな根本原因

    Q, K, V: (batch, num_heads, seq_len, head_dim)
    """
    d_k = Q.shape[-1]

    # QK^T: (batch, heads, seq_len_q, seq_len_k)
    scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)

    # Causal mask: Decoder では未来のトークンを見ないようにする
    if mask is not None:
        scores = np.where(mask == 0, -1e9, scores)

    # softmax（数値安定化: 最大値を引く）
    scores_max = scores.max(axis=-1, keepdims=True)
    exp_scores = np.exp(scores - scores_max)
    attn_weights = exp_scores / exp_scores.sum(axis=-1, keepdims=True)  # (b, h, seq_q, seq_k)

    # V との重み付き和: (b, h, seq_q, head_dim)
    output = attn_weights @ V

    return output, attn_weights


class MultiHeadAttention:
    """
    Multi-Head Attention

    h 個の「Attention ヘッド」を並列に走らせ、結合する

    なぜ複数ヘッドが必要か:
      1つの Attention だけでは1種類の「注目パターン」しか学習できない
      → 構文関係・意味関係・位置関係など、異なる側面を並列に学習

    例 (d_model=512, num_heads=8):
      各ヘッドは d_k = 512/8 = 64 次元の空間で独立に Attention を計算
      → 8通りの異なる注目パターンを同時に学習

    パラメータ:
      W_Q, W_K, W_V: (d_model, d_model)  ← 全ヘッド分
      W_O: (d_model, d_model)            ← 出力の線形変換
    """

    def __init__(self, d_model: int, num_heads: int):
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        # 重み行列の初期化（Xavier 均一分布）
        scale = np.sqrt(2 / (d_model + d_model))
        rng = np.random.default_rng(42)
        self.W_Q = rng.uniform(-scale, scale, (d_model, d_model))
        self.W_K = rng.uniform(-scale, scale, (d_model, d_model))
        self.W_V = rng.uniform(-scale, scale, (d_model, d_model))
        self.W_O = rng.uniform(-scale, scale, (d_model, d_model))

    def split_heads(self, x: NDArray, batch_size: int) -> NDArray:
        """(batch, seq, d_model) → (batch, heads, seq, head_dim)"""
        x = x.reshape(batch_size, -1, self.num_heads, self.head_dim)
        return x.transpose(0, 2, 1, 3)

    def forward(self, query: NDArray, key: NDArray, value: NDArray,
                mask: NDArray | None = None) -> tuple[NDArray, NDArray]:
        """
        query, key, value: (batch, seq_len, d_model)
        """
        batch_size = query.shape[0]

        # 線形変換: (batch, seq, d_model) → (batch, seq, d_model)
        Q = query @ self.W_Q
        K = key @ self.W_K
        V = value @ self.W_V

        # ヘッドに分割: (batch, heads, seq, head_dim)
        Q = self.split_heads(Q, batch_size)
        K = self.split_heads(K, batch_size)
        V = self.split_heads(V, batch_size)

        # Scaled Dot-Product Attention (各ヘッドで並列)
        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)

        # ヘッドを結合: (batch, seq, d_model)
        attn_output = attn_output.transpose(0, 2, 1, 3)
        attn_output = attn_output.reshape(batch_size, -1, self.d_model)

        # 最終線形変換
        output = attn_output @ self.W_O

        return output, attn_weights


class LayerNorm:
    """
    Layer Normalization

    なぜ Batch Norm でなく Layer Norm か？
      Batch Norm: バッチ方向で正規化 → バッチサイズに依存
      Layer Norm: 各サンプルの特徴方向で正規化 → バッチサイズ不依存

      Transformer は可変長シーケンスを扱う → Layer Norm が適切

    数式:
      y = γ * (x - μ) / (σ + ε) + β
      γ, β: 学習可能なパラメータ（スケールとシフト）
    """

    def __init__(self, d_model: int, eps: float = 1e-6):
        self.gamma = np.ones(d_model)   # スケール
        self.beta = np.zeros(d_model)   # シフト
        self.eps = eps

    def forward(self, x: NDArray) -> NDArray:
        mean = x.mean(axis=-1, keepdims=True)
        std = x.std(axis=-1, keepdims=True)
        x_norm = (x - mean) / (std + self.eps)
        return self.gamma * x_norm + self.beta


class PositionWiseFFN:
    """
    Position-wise Feed-Forward Network

    FFN(x) = max(0, xW₁ + b₁)W₂ + b₂

    各位置に独立に適用される2層の MLP
    d_model → d_ff（通常 4×d_model）→ d_model

    なぜ Attention の後に FFN が必要か:
      Attention: トークン間の「関係性」を学習（グローバル情報の集約）
      FFN: 各トークンの表現を個別に変換（非線形変換・情報の精製）
      → 両方がそろって初めて Transformer が機能する
    """

    def __init__(self, d_model: int, d_ff: int):
        rng = np.random.default_rng(0)
        scale1 = np.sqrt(2 / (d_model + d_ff))
        scale2 = np.sqrt(2 / (d_ff + d_model))
        self.W1 = rng.uniform(-scale1, scale1, (d_model, d_ff))
        self.b1 = np.zeros(d_ff)
        self.W2 = rng.uniform(-scale2, scale2, (d_ff, d_model))
        self.b2 = np.zeros(d_model)

    def forward(self, x: NDArray) -> NDArray:
        # ReLU 活性化
        h = np.maximum(0, x @ self.W1 + self.b1)
        return h @ self.W2 + self.b2


class TransformerEncoderLayer:
    """
    Transformer Encoder の1層

    構造:
      x → [Multi-Head Attention] → Add & Norm → [FFN] → Add & Norm → output
                ↑ Residual Connection ↑               ↑ Residual Connection ↑

    Residual Connection:
      output = LayerNorm(x + SubLayer(x))
      ← なぜ重要か？深いネットワークで勾配消失を防ぐ
      ← ResNet と同じ発想（2015）をTransformerが継承
    """

    def __init__(self, d_model: int, num_heads: int, d_ff: int, dropout: float = 0.1):
        self.attn = MultiHeadAttention(d_model, num_heads)
        self.norm1 = LayerNorm(d_model)
        self.ffn = PositionWiseFFN(d_model, d_ff)
        self.norm2 = LayerNorm(d_model)
        self.dropout_rate = dropout

    def _dropout(self, x: NDArray, rng: np.random.Generator) -> NDArray:
        mask = rng.random(x.shape) > self.dropout_rate
        return x * mask / (1 - self.dropout_rate)

    def forward(self, x: NDArray, mask: NDArray | None = None,
                rng: np.random.Generator | None = None) -> tuple[NDArray, NDArray]:
        # Self-Attention + Residual + LayerNorm
        attn_out, attn_weights = self.attn.forward(x, x, x, mask)
        if rng is not None:
            attn_out = self._dropout(attn_out, rng)
        x = self.norm1.forward(x + attn_out)           # Add & Norm

        # FFN + Residual + LayerNorm
        ffn_out = self.ffn.forward(x)
        if rng is not None:
            ffn_out = self._dropout(ffn_out, rng)
        x = self.norm2.forward(x + ffn_out)            # Add & Norm

        return x, attn_weights


class TransformerEncoder:
    """
    Transformer Encoder （BERT のベースとなる構造）

    入力: トークンID (batch, seq_len)
    出力: コンテキスト化された表現 (batch, seq_len, d_model)

    BERT との違い:
      ・BERT: [CLS] トークンを先頭に追加し、分類に使用
      ・BERT: Masked Language Modeling で事前学習
      ・BERT: WordPiece tokenization

    GPT との違い:
      ・GPT: Decoder のみ（因果的注意マスク）
      ・GPT: 次トークン予測で事前学習（Causal LM）
      ・Encoder(BERT): 双方向 ↔ Decoder(GPT): 単方向
    """

    def __init__(self, vocab_size: int, d_model: int, num_heads: int,
                 d_ff: int, num_layers: int, max_seq_len: int = 512,
                 dropout: float = 0.1):
        rng = np.random.default_rng(42)
        # Token embedding (語彙 → ベクトル)
        self.embedding = rng.normal(0, d_model ** -0.5, (vocab_size, d_model))
        self.pos_encoding = PositionalEncoding(d_model, max_seq_len)
        self.layers = [
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ]
        self.norm = LayerNorm(d_model)
        self.d_model = d_model
        self.dropout_rate = dropout

    def forward(self, token_ids: NDArray, training: bool = False) -> tuple[NDArray, list]:
        """
        token_ids: (batch, seq_len)
        returns: (batch, seq_len, d_model), [attention weights per layer]
        """
        rng = np.random.default_rng() if training else None

        # Embedding + Positional Encoding
        x = self.embedding[token_ids]                    # (batch, seq, d_model)
        x = x * np.sqrt(self.d_model)                   # スケール（Vaswani et al.）
        x = self.pos_encoding(x)

        # Padding mask（0トークンを無視）
        pad_mask = (token_ids != 0)[:, np.newaxis, np.newaxis, :]  # (b, 1, 1, seq)

        all_attn_weights = []
        for layer in self.layers:
            x, attn_w = layer.forward(x, pad_mask, rng)
            all_attn_weights.append(attn_w)

        return self.norm.forward(x), all_attn_weights


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Demo & Analysis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_positional_encoding() -> None:
    print("\n" + "━" * 60)
    print("📍 Positional Encoding の可視化")
    print("━" * 60)

    pe_module = PositionalEncoding(d_model=8, max_seq_len=10)
    pe = pe_module.pe[:6, :8]  # 6位置 × 8次元

    print("  位置 (行) × 次元 (列) の sin/cos 値:")
    print("  " + " ".join(f"  dim{i}" for i in range(8)))
    for pos, row in enumerate(pe):
        vals = " ".join(f"{v:+.3f}" for v in row)
        print(f"  pos={pos}: {vals}")

    print("""
  観察ポイント:
    ・各行（位置）は異なるパターンを持つ
    ・隣接する位置は似たパターン（連続性）
    ・低次元: 周期が短い（細かい位置情報）
    ・高次元: 周期が長い（大まかな位置情報）
    ← これで「単語の位置」を保持しながら並列処理できる
""")


def demo_attention_visualization() -> None:
    print("\n" + "━" * 60)
    print("👁️  Attention の可視化")
    print("━" * 60)

    # ミニシナリオ: 「機械学習でPythonを使う」
    d_model = 16
    num_heads = 2
    rng = np.random.default_rng(0)

    seq_len = 4
    tokens = ["機械学習", "で", "Python", "を使う"]

    # ランダムな入力（実際はEmbedding層の出力）
    x = rng.normal(0, 1, (1, seq_len, d_model))  # batch=1

    attn = MultiHeadAttention(d_model=d_model, num_heads=num_heads)
    output, attn_weights = attn.forward(x, x, x)

    print(f"  入力: {tokens}")
    print(f"\n  Head 1 の注意マップ（行=Query、列=Key）:")
    head0_weights = attn_weights[0, 0]  # batch=0, head=0

    header = "         " + "  ".join(f"{t[:3]:4s}" for t in tokens)
    print("  " + header)
    for i, row_token in enumerate(tokens):
        row = "  ".join(f"{w:.2f}" for w in head0_weights[i])
        print(f"  {row_token[:4]:6s} [{row}]")

    print(f"\n  出力の形状: {output.shape}  (batch=1, seq={seq_len}, d_model={d_model})")
    print("""
  解釈:
    ・各行はそのトークンが「どのトークンに注目したか」
    ・対角線が高い → 自己参照が多い
    ・実際の訓練後のBERTでは意味的・構文的な注目パターンが出現する
""")


def demo_complexity_analysis() -> None:
    print("\n" + "━" * 60)
    print("⚡ 計算量の分析")
    print("━" * 60)
    print("""
  Transformer の計算量:
  ─────────────────────────────────────────────────────
  Attention:    O(n² d)   n=シーケンス長, d=次元数
  FFN:          O(n d²)   各位置独立

  シーケンス長 n が2倍になると Attention は4倍に！
  → GPT-3 (2048 tokens) → GPT-4 (128K tokens) は 4000倍の計算

  改善技術（面接でよく聞かれる）:
  ┌──────────────────────────────────────────────────────┐
  │ 技術              │ アイデア           │ 計算量       │
  ├──────────────────────────────────────────────────────│
  │ Flash Attention   │ IO-aware計算       │ O(n² d)      │
  │                   │ HBM往復を最小化     │ ただし高速   │
  ├──────────────────────────────────────────────────────│
  │ Sparse Attention  │ 全ペアでなく       │ O(n√n d)     │
  │                   │ 近傍のみ注目        │              │
  ├──────────────────────────────────────────────────────│
  │ Linear Attention  │ Attention を近似   │ O(n d²)      │
  │                   │ Kernel trick使用   │              │
  ├──────────────────────────────────────────────────────│
  │ Mamba (SSM)       │ Attentionを使わない│ O(n d²)      │
  │                   │ 状態空間モデル     │              │
  └──────────────────────────────────────────────────────┘

  BERT vs GPT の設計思想:
    BERT: Encoder only → 双方向文脈 → 文書理解・分類が得意
    GPT:  Decoder only → 因果的注意 → テキスト生成が得意
    T5:   Encoder + Decoder → 翻訳・要約が得意

  テスラ Autopilot での使われ方:
    ・カメラ映像を「視覚トークン」として扱う
    ・Vision Transformer (ViT) でシーン理解
    ・複数カメラの情報を Attention で統合
""")


def demo_full_encoder() -> None:
    print("\n" + "━" * 60)
    print("🤖 Transformer Encoder の動作確認")
    print("━" * 60)

    # ミニ設定（実際の BERT-base は d_model=768, heads=12, layers=12）
    vocab_size = 100
    d_model = 32
    num_heads = 4
    d_ff = 64
    num_layers = 2

    encoder = TransformerEncoder(
        vocab_size=vocab_size, d_model=d_model, num_heads=num_heads,
        d_ff=d_ff, num_layers=num_layers
    )

    # バッチサイズ2、シーケンス長5のトークン列
    token_ids = np.array([
        [1, 2, 3, 4, 5],      # 文1
        [6, 7, 8, 0, 0],      # 文2（0=PAD）
    ])

    output, attn_weights = encoder.forward(token_ids)

    print(f"  入力 token_ids shape: {token_ids.shape}")
    print(f"  出力 shape: {output.shape}  (batch=2, seq=5, d_model={d_model})")
    print(f"  各層の Attention 重み形状: {attn_weights[0].shape}  (batch, heads, seq, seq)")

    # BERT-base のパラメータ数と比較
    params_ours = (
        vocab_size * d_model +           # Embedding
        num_layers * (
            4 * d_model * d_model +     # QKV + O 行列
            2 * d_model * d_ff +        # FFN
            4 * d_model                  # LayerNorm
        )
    )
    params_bert = (
        30522 * 768 +                    # Vocabulary embedding
        12 * (4 * 768 * 768 + 2 * 768 * 3072 + 4 * 768)
    )
    print(f"\n  我々のモデルのパラメータ数: {params_ours:,}")
    print(f"  BERT-base のパラメータ数:  {params_bert:,} (~110M)")
    print(f"  GPT-3 のパラメータ数:      {175_000_000_000:,} (~175B)")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Transformer & Backprop from Scratch                      ║")
    print("╚════════════════════════════════════════════════════════════╝")

    demo_backprop()
    demo_positional_encoding()
    demo_attention_visualization()
    demo_full_encoder()
    demo_complexity_analysis()

    print("\n" + "═" * 60)
    print("✅ 完了！Google/Tesla/IBM 面接での想定Q&A:")
    print("""
  Q: 「Backpropagation を説明してください」
  A: 連鎖律（Chain Rule）を使って出力の損失を入力まで微分する。
     計算グラフをトポロジカル順に逆向きに辿り、各ノードで
     upstream_grad × local_grad を蓄積する。

  Q: 「Self-Attention の計算量はなぜ O(n²) か？」
  A: QK^T の計算で n×n の行列積を計算するから。
     シーケンス長が2倍になると計算量は4倍。
     これが長文処理のボトルネック。

  Q: 「Positional Encoding がなければ何が起きるか？」
  A: "I love you" と "You love I" が同じ表現になる。
     語順が失われ、文法的・意味的な情報が消える。

  Q: 「BERT と GPT の違いを説明してください」
  A: BERTはEncoder only（双方向Attention）、GPTはDecoder only
     （因果的Attention）。BERTは文書理解、GPTは生成タスク向け。
""")
    print("  [実装してみよう]")
    print("  1. Causal Mask を実装して GPT スタイルの Decoder を作る")
    print("  2. 上の TransformerEncoder に分類ヘッドをつけて学習させる")
    print("  3. Flash Attention のアイデア（タイリング計算）を疑似実装する")


if __name__ == "__main__":
    main()
