#!/usr/bin/env python3
"""
LLM / NLP エンジニアリング ディープダイブ
=========================================
大規模言語モデルの内部構造・学習・推論を stdlib のみで実装・解説する。

カバー範囲:
  1. Tokenization (BPE 完全実装)
  2. Attention Mechanism (Scaled Dot-Product, Multi-Head, KV-Cache)
  3. LLM アーキテクチャ比較
  4. Decoding Strategies (Greedy / Beam / Top-K / Top-P / Temperature)
  5. Fine-tuning 手法 (LoRA シミュレーション)
  6. RLHF / DPO パイプライン
  7. 推論最適化 (量子化, Speculative Decoding)
  8. Evaluation メトリクス (Perplexity, BLEU, ROUGE)

実行: python llm_engineering.py
"""

import math
import random
import collections
import re
from typing import Dict, List, Tuple, Optional

random.seed(42)

# ============================================================
# 1. Tokenization — Character → Word → Subword の進化
# ============================================================

def demo_tokenization_evolution():
    """トークナイゼーションの進化を比較"""
    text = "unhappiness is not unchangeable"

    # --- Character-level ---
    # 長所: OOV なし / 短所: 系列長が爆発、意味を捉えにくい
    char_tokens = list(text)
    print(f"[Character-level] len={len(char_tokens)}")
    print(f"  tokens: {char_tokens[:15]}...")

    # --- Word-level ---
    # 長所: 意味単位 / 短所: 語彙が膨大、未知語に弱い
    word_tokens = text.split()
    print(f"\n[Word-level] len={len(word_tokens)}")
    print(f"  tokens: {word_tokens}")

    # --- Subword (BPE) ---
    # 長所: OOV 回避 + 合理的な語彙サイズ
    # "unhappiness" → ["un", "happiness"] のように頻出サブワードで分割
    print(f"\n[Subword (BPE)] → 下記の BPE 実装で詳細デモ")
    print()


class BPETokenizer:
    """
    Byte Pair Encoding 完全実装
    ===========================
    学習フェーズ:
      1. 全単語を文字レベルに分解 (+ 終端記号 </w>)
      2. 隣接ペアの出現頻度をカウント
      3. 最頻ペアをマージ → 語彙に追加
      4. 目標語彙サイズまで繰り返す
    """

    def __init__(self):
        self.merges: List[Tuple[str, str]] = []   # マージルール (順序付き)
        self.vocab: set = set()

    def _get_word_freqs(self, corpus: List[str]) -> Dict[tuple, int]:
        """コーパスを単語頻度 (文字タプル) に変換"""
        freqs: Dict[tuple, int] = collections.Counter()
        for sentence in corpus:
            for word in sentence.strip().split():
                # 各文字 + 終端記号
                chars = tuple(list(word) + ["</w>"])
                freqs[chars] += 1
        return freqs

    def _get_pair_freqs(self, word_freqs: Dict[tuple, int]) -> Dict[tuple, int]:
        """全単語の隣接ペア頻度を集計"""
        pairs: Dict[tuple, int] = collections.Counter()
        for word, freq in word_freqs.items():
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += freq
        return pairs

    def _merge_pair(self, pair: Tuple[str, str],
                    word_freqs: Dict[tuple, int]) -> Dict[tuple, int]:
        """最頻ペアをマージした新しい word_freqs を返す"""
        new_freqs: Dict[tuple, int] = {}
        bigram = pair
        for word, freq in word_freqs.items():
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and (word[i], word[i + 1]) == bigram:
                    new_word.append(word[i] + word[i + 1])
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_freqs[tuple(new_word)] = freq
        return new_freqs

    def train(self, corpus: List[str], num_merges: int = 20):
        """BPE 学習: num_merges 回マージを実行"""
        word_freqs = self._get_word_freqs(corpus)

        # 初期語彙 = 全文字 + </w>
        self.vocab = set()
        for word in word_freqs:
            for ch in word:
                self.vocab.add(ch)

        print(f"初期語彙サイズ: {len(self.vocab)}")

        for step in range(num_merges):
            pair_freqs = self._get_pair_freqs(word_freqs)
            if not pair_freqs:
                break
            best_pair = max(pair_freqs, key=pair_freqs.get)
            best_freq = pair_freqs[best_pair]

            self.merges.append(best_pair)
            merged_token = best_pair[0] + best_pair[1]
            self.vocab.add(merged_token)
            word_freqs = self._merge_pair(best_pair, word_freqs)

            if step < 10 or step == num_merges - 1:
                print(f"  merge {step+1:2d}: {best_pair} → '{merged_token}' "
                      f"(freq={best_freq})")

        print(f"最終語彙サイズ: {len(self.vocab)}")

    def encode(self, text: str) -> List[str]:
        """学習済みマージルールでテキストをトークン化"""
        tokens_per_word = []
        for word in text.strip().split():
            symbols = list(word) + ["</w>"]
            for pair in self.merges:
                i = 0
                while i < len(symbols) - 1:
                    if (symbols[i], symbols[i + 1]) == pair:
                        symbols[i] = symbols[i] + symbols[i + 1]
                        del symbols[i + 1]
                    else:
                        i += 1
            tokens_per_word.extend(symbols)
        return tokens_per_word

    def decode(self, tokens: List[str]) -> str:
        """トークン列 → テキスト復元"""
        text = "".join(tokens)
        text = text.replace("</w>", " ")
        return text.strip()


def demo_bpe():
    """BPE の学習・エンコード・デコードをデモ"""
    print("=" * 60)
    print("BPE (Byte Pair Encoding) 完全実装デモ")
    print("=" * 60)

    corpus = [
        "low low low low low",
        "lower lower lower",
        "newest newest newest newest",
        "widest widest",
        "new new new new new new",
    ]

    tokenizer = BPETokenizer()
    tokenizer.train(corpus, num_merges=15)

    test = "lowest newer"
    tokens = tokenizer.encode(test)
    decoded = tokenizer.decode(tokens)
    print(f"\nエンコード: '{test}' → {tokens}")
    print(f"デコード:   {tokens} → '{decoded}'")

    # --- Tokenizer 比較表 ---
    print(f"""
┌──────────────┬────────────────────────────────────────────────┐
│ 手法         │ 特徴                                           │
├──────────────┼────────────────────────────────────────────────┤
│ BPE          │ 頻度ベースでペアをマージ。GPT 系で使用         │
│ WordPiece    │ 尤度ベースでサブワード選択。BERT で使用        │
│              │ "##" プレフィクスで接続 (例: un + ##happy)      │
│ SentencePiece│ 言語非依存 (空白も特殊文字扱い)。T5/LLaMA     │
│ Tiktoken     │ BPE + バイトレベル。GPT-3.5/4。高速 Rust 実装  │
└──────────────┴────────────────────────────────────────────────┘

語彙サイズの影響:
  小さすぎ (< 8K)  → 未知語 (OOV) 増加、系列長増大
  適切     (32-64K) → サブワード粒度のバランス良好
  大きすぎ (> 128K) → 埋め込み行列が肥大 (vocab × d_model)
""")


# ============================================================
# 2. Attention Mechanism 詳解 (NumPy 不要版)
# ============================================================

def mat_mul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """行列積 (stdlib のみ)"""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    assert cols_a == rows_b, f"Shape mismatch: {cols_a} vs {rows_b}"
    result = [[0.0] * cols_b for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            s = 0.0
            for k in range(cols_a):
                s += a[i][k] * b[k][j]
            result[i][j] = s
    return result


def transpose(m: List[List[float]]) -> List[List[float]]:
    """転置"""
    rows, cols = len(m), len(m[0])
    return [[m[i][j] for i in range(rows)] for j in range(cols)]


def softmax_row(row: List[float]) -> List[float]:
    """数値安定な softmax (1 行)"""
    max_val = max(row)
    exps = [math.exp(x - max_val) for x in row]
    total = sum(exps)
    return [e / total for e in exps]


def softmax_matrix(m: List[List[float]]) -> List[List[float]]:
    """行列の各行に softmax"""
    return [softmax_row(row) for row in m]


def scaled_dot_product_attention(
    Q: List[List[float]],
    K: List[List[float]],
    V: List[List[float]],
    mask: Optional[List[List[float]]] = None
) -> List[List[float]]:
    """
    Scaled Dot-Product Attention
    ============================
    Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V

    - Q: (seq_len, d_k)  クエリ: 「何を探しているか」
    - K: (seq_len, d_k)  キー:   「何を持っているか」
    - V: (seq_len, d_v)  バリュー: 「実際の情報」
    - mask: Causal mask (decoder 用)
    """
    d_k = len(Q[0])
    scale = math.sqrt(d_k)

    # Q K^T → (seq_len, seq_len)
    K_T = transpose(K)
    scores = mat_mul(Q, K_T)

    # スケーリング
    for i in range(len(scores)):
        for j in range(len(scores[0])):
            scores[i][j] /= scale

    # Causal mask (未来のトークンを見えなくする)
    if mask is not None:
        for i in range(len(scores)):
            for j in range(len(scores[0])):
                if mask[i][j] == 0:
                    scores[i][j] = float('-inf')

    # Softmax → 注意重み
    weights = softmax_matrix(scores)

    # 重み × V
    output = mat_mul(weights, V)
    return output


def demo_attention():
    """Attention メカニズムのデモ"""
    print("=" * 60)
    print("Scaled Dot-Product Attention 実装デモ")
    print("=" * 60)

    # 3 トークン, d_k = d_v = 4
    random.seed(42)
    seq_len, d_k = 3, 4

    def rand_mat(r, c):
        return [[random.gauss(0, 0.5) for _ in range(c)] for _ in range(r)]

    Q = rand_mat(seq_len, d_k)
    K = rand_mat(seq_len, d_k)
    V = rand_mat(seq_len, d_k)

    # --- Self-Attention (マスクなし = Encoder) ---
    out = scaled_dot_product_attention(Q, K, V)
    print("\n[Encoder Self-Attention] (マスクなし)")
    for i, row in enumerate(out):
        print(f"  token {i}: [{', '.join(f'{v:.3f}' for v in row)}]")

    # --- Causal Attention (マスクあり = Decoder) ---
    causal_mask = [[1 if j <= i else 0 for j in range(seq_len)]
                   for i in range(seq_len)]
    out_causal = scaled_dot_product_attention(Q, K, V, mask=causal_mask)
    print("\n[Decoder Causal Attention] (下三角マスク)")
    for i, row in enumerate(out_causal):
        print(f"  token {i}: [{', '.join(f'{v:.3f}' for v in row)}]")


class MultiHeadAttention:
    """
    Multi-Head Attention
    ====================
    ヘッド分割の意味:
      - 各ヘッドが異なる「関係性」を学習
      - ヘッド1: 構文的依存 / ヘッド2: 意味的類似 / ヘッド3: 位置関係
      - h 個のヘッドの出力を concat → 線形変換
    """

    def __init__(self, d_model: int, n_heads: int):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        # 重みは乱数で初期化 (デモ用)
        random.seed(7)
        self.W_q = [[random.gauss(0, 0.1) for _ in range(d_model)]
                     for _ in range(d_model)]
        self.W_k = [[random.gauss(0, 0.1) for _ in range(d_model)]
                     for _ in range(d_model)]
        self.W_v = [[random.gauss(0, 0.1) for _ in range(d_model)]
                     for _ in range(d_model)]

    def forward(self, X: List[List[float]],
                mask=None) -> List[List[float]]:
        seq_len = len(X)
        Q_full = mat_mul(X, transpose(self.W_q))
        K_full = mat_mul(X, transpose(self.W_k))
        V_full = mat_mul(X, transpose(self.W_v))

        # ヘッド分割 → 各ヘッドで Attention → concat
        head_outputs = []
        for h in range(self.n_heads):
            start = h * self.d_k
            end = start + self.d_k
            Q_h = [row[start:end] for row in Q_full]
            K_h = [row[start:end] for row in K_full]
            V_h = [row[start:end] for row in V_full]
            out_h = scaled_dot_product_attention(Q_h, K_h, V_h, mask)
            head_outputs.append(out_h)

        # Concat
        result = []
        for i in range(seq_len):
            concat_row = []
            for h in range(self.n_heads):
                concat_row.extend(head_outputs[h][i])
            result.append(concat_row)
        return result


class KVCache:
    """
    KV-Cache (推論時の高速化)
    =========================
    問題: Autoregressive 生成では各ステップで全 K, V を再計算 → O(n²)
    解決: 過去の K, V をキャッシュし、新トークン分だけ計算

    ステップ t での計算:
      - K_cache = [K_1, K_2, ..., K_{t-1}]  (キャッシュ済み)
      - K_new = W_K × x_t               (新トークンの K のみ計算)
      - K_all = concat(K_cache, K_new)    (結合)
      - Q_new × K_all^T → attention
    """

    def __init__(self, d_k: int):
        self.d_k = d_k
        self.k_cache: List[List[float]] = []
        self.v_cache: List[List[float]] = []

    def update(self, k_new: List[float], v_new: List[float]):
        """新しい K, V をキャッシュに追加"""
        self.k_cache.append(k_new)
        self.v_cache.append(v_new)

    def get_attention(self, q: List[float]) -> List[float]:
        """キャッシュ済み K, V を使って attention 計算"""
        scale = math.sqrt(self.d_k)
        scores = []
        for k in self.k_cache:
            dot = sum(q_i * k_i for q_i, k_i in zip(q, k))
            scores.append(dot / scale)

        weights = softmax_row(scores)

        # 加重和
        result = [0.0] * self.d_k
        for w, v in zip(weights, self.v_cache):
            for j in range(self.d_k):
                result[j] += w * v[j]
        return result


def demo_kv_cache():
    """KV-Cache のデモ"""
    print("\n[KV-Cache デモ]")
    d_k = 4
    cache = KVCache(d_k)

    # 5 トークン分の K, V を順次追加
    random.seed(10)
    for t in range(5):
        k = [random.gauss(0, 1) for _ in range(d_k)]
        v = [random.gauss(0, 1) for _ in range(d_k)]
        cache.update(k, v)

    # 最新トークンの Q で attention
    q = [random.gauss(0, 1) for _ in range(d_k)]
    out = cache.get_attention(q)
    print(f"  キャッシュサイズ: {len(cache.k_cache)} トークン")
    print(f"  Attention 出力: [{', '.join(f'{v:.3f}' for v in out)}]")

    print("""
  KV-Cache の効果:
    Without cache: 各ステップ O(n × d) の K,V 再計算
    With cache:    各ステップ O(d) のみ (新トークン分)
    メモリ: O(n × d × 2 × num_layers) — 長文で GB 単位

  発展:
    MQA (Multi-Query Attention): K,V を全ヘッドで共有 → キャッシュ 1/h
    GQA (Grouped-Query Attention): K,V をグループ単位で共有 (MQA と MHA の中間)
    PagedAttention (vLLM): OS のページングのように KV を管理
""")


# ============================================================
# 3. LLM アーキテクチャ比較
# ============================================================

def show_architecture_comparison():
    """LLM アーキテクチャの比較"""
    print("=" * 60)
    print("LLM アーキテクチャ比較")
    print("=" * 60)
    print("""
┌─────────────────┬──────────────┬──────────────┬─────────────────┐
│                 │ Encoder-only │ Decoder-only │ Encoder-Decoder │
│                 │ (BERT)       │ (GPT)        │ (T5)            │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ Attention       │ 双方向       │ 左→右 (因果) │ Enc:双方向      │
│                 │              │              │ Dec:因果+Cross  │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ 学習目標        │ MLM          │ Next Token   │ Span Corruption │
│                 │ (穴埋め)     │ Prediction   │ (Denoising)     │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ 得意タスク      │ 分類, NER    │ テキスト生成 │ 翻訳, 要約      │
│                 │ 意味検索     │ 対話, コード │ Q&A             │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ 代表モデル      │ BERT,        │ GPT-4,       │ T5, BART,       │
│                 │ RoBERTa,     │ LLaMA,       │ Flan-T5,        │
│                 │ DeBERTa      │ Mistral      │ mBART           │
├─────────────────┼──────────────┼──────────────┼─────────────────┤
│ 現在の主流      │ 埋め込み用   │ ★ 最主流     │ 特定タスク      │
└─────────────────┴──────────────┴──────────────┴─────────────────┘

選択フローチャート:
  テキスト生成が必要? ─Yes─→ Decoder-only (GPT/LLaMA)
      │ No
  入出力が対? ─Yes─→ Encoder-Decoder (T5)
  (翻訳/要約)
      │ No
  テキスト理解/分類 → Encoder-only (BERT)
""")

    # パラメータ数の計算
    print("パラメータ数の内訳 (7B モデルの例):")
    d_model = 4096
    n_heads = 32
    n_layers = 32
    vocab_size = 32000
    d_ff = 11008  # LLaMA の FFN サイズ

    embedding = vocab_size * d_model
    attn_per_layer = 4 * d_model * d_model  # W_Q, W_K, W_V, W_O
    ffn_per_layer = 3 * d_model * d_ff      # gate, up, down (SwiGLU)
    total_per_layer = attn_per_layer + ffn_per_layer
    total = embedding + n_layers * total_per_layer

    print(f"  Embedding:       {embedding:>12,} ({embedding/1e9:.2f}B)")
    print(f"  Attention/layer: {attn_per_layer:>12,} ({attn_per_layer/1e6:.0f}M)")
    print(f"  FFN/layer:       {ffn_per_layer:>12,} ({ffn_per_layer/1e6:.0f}M)")
    print(f"  Total ({n_layers} layers): {total:>12,} ({total/1e9:.2f}B)")
    print(f"  FP16 メモリ:     {total * 2 / 1e9:.1f} GB")
    print()


# ============================================================
# 4. Decoding Strategies (実装付き)
# ============================================================

class SimpleLanguageModel:
    """
    デコーディング戦略デモ用の簡易言語モデル
    実際の LLM の代わりに、固定の確率分布を返す
    """

    def __init__(self):
        # 語彙: 簡易トークン
        self.vocab = ["the", "a", "cat", "dog", "sat", "ran",
                       "on", "in", "mat", "park", "big", "small",
                       "happy", "fast", "<eos>"]
        self.vocab_size = len(self.vocab)

        # 遷移確率 (簡易的なバイグラム)
        self.transitions: Dict[str, Dict[str, float]] = {
            "<start>": {"the": 0.4, "a": 0.3, "big": 0.1,
                        "small": 0.1, "happy": 0.1},
            "the": {"cat": 0.3, "dog": 0.3, "big": 0.15,
                    "small": 0.1, "fast": 0.05, "happy": 0.1},
            "a": {"cat": 0.3, "dog": 0.3, "big": 0.15,
                  "small": 0.15, "happy": 0.1},
            "cat": {"sat": 0.4, "ran": 0.3, "on": 0.1,
                    "in": 0.1, "<eos>": 0.1},
            "dog": {"sat": 0.3, "ran": 0.4, "on": 0.1,
                    "in": 0.1, "<eos>": 0.1},
            "sat": {"on": 0.5, "in": 0.3, "<eos>": 0.2},
            "ran": {"on": 0.3, "in": 0.4, "<eos>": 0.3},
            "on": {"the": 0.4, "a": 0.3, "mat": 0.2, "<eos>": 0.1},
            "in": {"the": 0.4, "a": 0.3, "park": 0.2, "<eos>": 0.1},
            "mat": {"<eos>": 1.0},
            "park": {"<eos>": 1.0},
        }

    def get_logits(self, last_token: str) -> List[float]:
        """最後のトークンから次トークンの logits (対数確率) を返す"""
        probs = {}
        trans = self.transitions.get(last_token, {"<eos>": 1.0})
        for token in self.vocab:
            probs[token] = trans.get(token, 0.001)

        total = sum(probs.values())
        logits = []
        for token in self.vocab:
            p = probs[token] / total
            logits.append(math.log(p + 1e-10))
        return logits


def apply_temperature(logits: List[float], temperature: float) -> List[float]:
    """
    Temperature Sampling
    ====================
    temperature < 1.0 → 分布がシャープに (決定的)
    temperature = 1.0 → 元の分布のまま
    temperature > 1.0 → 分布がフラットに (多様性↑)
    """
    if temperature <= 0:
        temperature = 1e-10
    return [l / temperature for l in logits]


def greedy_decode(model: SimpleLanguageModel, max_len: int = 8) -> List[str]:
    """
    Greedy Decoding: 常に最大確率のトークンを選択
    - 高速、決定的
    - 最適解を逃す可能性 (局所最適)
    """
    tokens = []
    last = "<start>"
    for _ in range(max_len):
        logits = model.get_logits(last)
        idx = logits.index(max(logits))
        token = model.vocab[idx]
        if token == "<eos>":
            break
        tokens.append(token)
        last = token
    return tokens


def beam_search(model: SimpleLanguageModel,
                beam_width: int = 3, max_len: int = 8) -> List[str]:
    """
    Beam Search: 上位 beam_width 個の候補を並行探索
    - Greedy より高品質
    - beam_width↑ → 品質↑ だが速度↓
    """
    # (累積対数確率, トークン列, 最後のトークン)
    beams = [(0.0, [], "<start>")]

    for _ in range(max_len):
        candidates = []
        for score, tokens, last in beams:
            if last == "<eos>" or (tokens and tokens[-1] == "<eos>"):
                candidates.append((score, tokens, "<eos>"))
                continue
            logits = model.get_logits(last)
            for idx, logit in enumerate(logits):
                new_token = model.vocab[idx]
                new_tokens = tokens + [new_token]
                candidates.append((score + logit, new_tokens, new_token))

        # 上位 beam_width を保持
        candidates.sort(key=lambda x: x[0], reverse=True)
        beams = candidates[:beam_width]

        # 全ビームが終了していたら停止
        if all(b[2] == "<eos>" for b in beams):
            break

    best = beams[0]
    result = [t for t in best[1] if t != "<eos>"]
    return result


def top_k_sampling(model: SimpleLanguageModel,
                   k: int = 5, temperature: float = 1.0,
                   max_len: int = 8) -> List[str]:
    """
    Top-K Sampling: 上位 K 個のトークンのみから確率的に選択
    - k が小さい → 品質重視
    - k が大きい → 多様性重視
    """
    tokens = []
    last = "<start>"
    for _ in range(max_len):
        logits = apply_temperature(model.get_logits(last), temperature)
        indexed = list(enumerate(logits))
        indexed.sort(key=lambda x: x[1], reverse=True)
        top_k_items = indexed[:k]

        # softmax over top-k
        max_l = max(l for _, l in top_k_items)
        exps = [(idx, math.exp(l - max_l)) for idx, l in top_k_items]
        total = sum(e for _, e in exps)
        probs = [(idx, e / total) for idx, e in exps]

        # サンプリング
        r = random.random()
        cumsum = 0.0
        chosen_idx = probs[0][0]
        for idx, p in probs:
            cumsum += p
            if r <= cumsum:
                chosen_idx = idx
                break

        token = model.vocab[chosen_idx]
        if token == "<eos>":
            break
        tokens.append(token)
        last = token
    return tokens


def top_p_sampling(model: SimpleLanguageModel,
                   p: float = 0.9, temperature: float = 1.0,
                   max_len: int = 8) -> List[str]:
    """
    Top-P (Nucleus) Sampling: 累積確率が p を超えるまでのトークンから選択
    - 動的に候補数が変わる (自信がある時は少数、不確かな時は多数)
    - Top-K より柔軟
    """
    tokens = []
    last = "<start>"
    for _ in range(max_len):
        logits = apply_temperature(model.get_logits(last), temperature)

        # softmax
        max_l = max(logits)
        exps = [math.exp(l - max_l) for l in logits]
        total = sum(exps)
        probs = [(i, e / total) for i, e in enumerate(exps)]

        # 確率降順ソート
        probs.sort(key=lambda x: x[1], reverse=True)

        # 累積確率が p を超えるまでのトークンを保持
        nucleus = []
        cumsum = 0.0
        for idx, prob in probs:
            nucleus.append((idx, prob))
            cumsum += prob
            if cumsum >= p:
                break

        # 再正規化してサンプリング
        total_n = sum(pr for _, pr in nucleus)
        r = random.random() * total_n
        cumsum = 0.0
        chosen_idx = nucleus[0][0]
        for idx, prob in nucleus:
            cumsum += prob
            if r <= cumsum:
                chosen_idx = idx
                break

        token = model.vocab[chosen_idx]
        if token == "<eos>":
            break
        tokens.append(token)
        last = token
    return tokens


def demo_decoding():
    """全デコーディング戦略の比較デモ"""
    print("=" * 60)
    print("Decoding Strategies 比較")
    print("=" * 60)

    model = SimpleLanguageModel()

    print(f"\nGreedy:        {' '.join(greedy_decode(model))}")
    print(f"Beam (w=3):    {' '.join(beam_search(model, beam_width=3))}")

    random.seed(42)
    print(f"Top-K (k=5):   {' '.join(top_k_sampling(model, k=5))}")
    random.seed(42)
    print(f"Top-P (p=0.9): {' '.join(top_p_sampling(model, p=0.9))}")

    # Temperature の効果
    print("\n--- Temperature の効果 (Top-K, k=5) ---")
    for temp in [0.1, 0.5, 1.0, 1.5, 2.0]:
        random.seed(42)
        result = top_k_sampling(model, k=5, temperature=temp)
        print(f"  T={temp:.1f}: {' '.join(result)}")

    print("""
┌──────────────┬──────┬──────┬──────┬────────────────────────┐
│ 手法         │ 品質 │ 多様 │ 速度 │ ユースケース           │
├──────────────┼──────┼──────┼──────┼────────────────────────┤
│ Greedy       │ ○    │ ×    │ ◎    │ 翻訳 (決定的出力)      │
│ Beam Search  │ ◎    │ △    │ △    │ 翻訳, 要約             │
│ Temperature  │ ○    │ ○    │ ◎    │ 創作, 対話             │
│ Top-K        │ ○    │ ○    │ ◎    │ 汎用テキスト生成       │
│ Top-P        │ ◎    │ ◎    │ ◎    │ ChatGPT デフォルト     │
└──────────────┴──────┴──────┴──────┴────────────────────────┘
""")


# ============================================================
# 5. Fine-tuning 手法 (LoRA シミュレーション)
# ============================================================

def demo_lora():
    """
    LoRA (Low-Rank Adaptation) シミュレーション
    ============================================
    アイデア: 巨大な重み行列 W を直接更新せず、
              低ランク行列 A, B で差分 ΔW = B × A を学習

    W' = W + ΔW = W + B × A
      W: (d × d) 元の重み (凍結)
      A: (d × r) ランク r の行列 (学習対象)
      B: (r × d) ランク r の行列 (学習対象)
      r << d (例: r=8, d=4096)
    """
    print("=" * 60)
    print("LoRA (Low-Rank Adaptation) シミュレーション")
    print("=" * 60)

    d = 16     # 元の次元 (実際は 4096)
    r = 4      # LoRA ランク (実際は 8-64)

    random.seed(42)

    # 元の重み行列 W (凍結)
    W = [[random.gauss(0, 0.1) for _ in range(d)] for _ in range(d)]

    # LoRA 行列 A, B (学習対象)
    # A は正規分布で初期化、B はゼロ初期化 (初期状態で ΔW = 0)
    A = [[random.gauss(0, 0.01) for _ in range(r)] for _ in range(d)]
    B = [[0.0 for _ in range(d)] for _ in range(r)]

    # ΔW = B × A → (d × d)
    # ここでは B^T(d×r) × A^T(r×d) ではなく A(d×r) × B(r×d) で計算
    delta_W = mat_mul(A, B)

    # W' = W + ΔW
    W_prime = [[W[i][j] + delta_W[i][j] for j in range(d)]
               for i in range(d)]

    # パラメータ数比較
    full_params = d * d
    lora_params = d * r * 2  # A + B
    ratio = lora_params / full_params * 100

    print(f"\n元の行列サイズ: {d}×{d} = {full_params} パラメータ")
    print(f"LoRA パラメータ: {d}×{r}×2 = {lora_params} パラメータ")
    print(f"削減率: {ratio:.1f}% (= {100-ratio:.1f}% 削減)")

    # 実際のモデルでの比較
    print(f"""
┌──────────────────┬──────────────┬──────────────┬───────────┐
│ 手法             │ 学習パラメータ│ メモリ (7B)  │ 学習時間  │
├──────────────────┼──────────────┼──────────────┼───────────┤
│ Full Fine-tuning │ 100%         │ ~28 GB       │ 基準      │
│ LoRA (r=8)       │ 0.1%         │ ~8 MB追加    │ 1/3       │
│ QLoRA (4-bit)    │ 0.1%         │ ~4 GB        │ 1/3       │
│ Prefix Tuning    │ 0.1%         │ ~数 MB       │ 1/4       │
│ Prompt Tuning    │ <0.01%       │ ~数 KB       │ 1/10      │
└──────────────────┴──────────────┴──────────────┴───────────┘

手法選択フローチャート:
  十分な GPU メモリ? ─No─→ QLoRA (4-bit 量子化 + LoRA)
      │ Yes
  タスク固有の深い適応が必要? ─Yes─→ Full Fine-tuning
      │ No
  複数タスクに使う? ─Yes─→ LoRA (アダプタ切替可能)
      │ No
  プロンプトだけで十分? ─Yes─→ Prompt Tuning
      │ No
  → LoRA (汎用的に最良)
""")


# ============================================================
# 6. RLHF / DPO パイプライン
# ============================================================

def demo_rlhf():
    """
    RLHF (Reinforcement Learning from Human Feedback)
    ==================================================
    3 ステップのパイプラインをシミュレーション
    """
    print("=" * 60)
    print("RLHF パイプライン シミュレーション")
    print("=" * 60)

    # --- Step 1: SFT (Supervised Fine-Tuning) ---
    print("\n[Step 1] SFT - 教師ありファインチューニング")
    print("  人手で作成した高品質 (instruction, response) ペアで学習")
    sft_data = [
        ("東京の天気は?", "東京の今日の天気は晴れです。最高気温は25度の予想です。"),
        ("Pythonでリスト反転", "reversed_list = my_list[::-1]"),
    ]
    for q, a in sft_data:
        print(f"  Q: {q}")
        print(f"  A: {a}")

    # --- Step 2: Reward Model ---
    print("\n[Step 2] Reward Model - 人間の選好を学習")
    print("  同じ質問に対する複数回答を人間がランク付け")

    comparison_data = [
        {
            "prompt": "AIの利点は?",
            "chosen":   "AIは効率化、予測分析、自動化などに貢献します。",    # 好ましい
            "rejected": "AIは最高です！何でもできます！すごい！",            # 好ましくない
        }
    ]

    # シンプルな報酬モデル (文の長さと具体性でスコア付け)
    def simple_reward(text: str) -> float:
        score = 0.0
        # 長すぎず短すぎない
        words = text.replace("、", " ").replace("。", " ").split()
        if 5 <= len(words) <= 30:
            score += 1.0
        # 具体的な単語があるか
        specific = ["効率", "分析", "自動化", "予測", "学習"]
        score += sum(0.5 for w in specific if w in text)
        # 感嘆符は減点 (過度なテンション)
        score -= text.count("！") * 0.3
        return score

    for data in comparison_data:
        r_chosen = simple_reward(data["chosen"])
        r_rejected = simple_reward(data["rejected"])
        print(f"  Prompt: {data['prompt']}")
        print(f"  Chosen  (R={r_chosen:.2f}): {data['chosen']}")
        print(f"  Rejected(R={r_rejected:.2f}): {data['rejected']}")

    # --- Step 3: PPO ---
    print("\n[Step 3] PPO - 方策最適化")
    print("  Reward Model のスコアを最大化するよう LLM を更新")
    print("  KL ダイバージェンス制約: SFT モデルから離れすぎない")
    print("  loss = -reward + β × KL(π_rlhf || π_sft)")

    # PPO シミュレーション
    random.seed(42)
    beta = 0.1  # KL ペナルティ係数
    print("\n  PPO 学習シミュレーション:")
    reward_history = []
    for epoch in range(5):
        reward = random.gauss(0.5 + epoch * 0.3, 0.2)
        kl_div = random.gauss(0.1 + epoch * 0.05, 0.05)
        total = reward - beta * kl_div
        reward_history.append(total)
        print(f"    Epoch {epoch+1}: reward={reward:.3f}, "
              f"KL={kl_div:.3f}, total={total:.3f}")

    # --- DPO ---
    print(f"""
[DPO (Direct Preference Optimization)]
  RLHF の簡略版 — Reward Model を明示的に学習せず、
  選好データから直接 LLM を最適化

  loss = -log σ(β (log π(y_w|x) - log π(y_l|x)
                    - log π_ref(y_w|x) + log π_ref(y_l|x)))

  利点:
    - Reward Model 不要 → パイプラインが簡潔
    - PPO の不安定性を回避
    - 計算コスト削減
  現在の主流: DPO → RLHF を置き換えつつある

RLHF パイプライン全体図:
  ┌──────────┐    ┌──────────────┐    ┌─────────────┐
  │ 事前学習  │───→│ SFT          │───→│ RLHF (PPO)  │
  │ (Base LM) │    │ (Instruction │    │ or DPO      │
  │           │    │  Tuning)     │    │             │
  └──────────┘    └──────────────┘    └─────────────┘
        ↓                ↓                   ↓
    GPT-3 Base      ChatGPT SFT       ChatGPT Final
""")


# ============================================================
# 7. 推論最適化
# ============================================================

def demo_quantization():
    """
    量子化 (Quantization) シミュレーション
    ======================================
    float32 → int8 への変換で推論を高速化・省メモリ化
    """
    print("=" * 60)
    print("量子化シミュレーション")
    print("=" * 60)

    # 元の重み (float32)
    random.seed(42)
    weights = [random.gauss(0, 0.5) for _ in range(20)]

    # --- Absmax 量子化 (INT8) ---
    def quantize_absmax(values: List[float], bits: int = 8):
        """Absmax 量子化: 最大絶対値でスケーリング"""
        max_abs = max(abs(v) for v in values)
        scale = (2 ** (bits - 1) - 1) / max_abs  # 127 / max_abs
        quantized = [max(-128, min(127, round(v * scale))) for v in values]
        return quantized, 1.0 / scale

    def dequantize(quantized: List[int], scale: float) -> List[float]:
        """逆量子化"""
        return [q * scale for q in quantized]

    q_int8, scale_8 = quantize_absmax(weights, bits=8)
    restored_8 = dequantize(q_int8, scale_8)

    # --- INT4 量子化 ---
    q_int4, scale_4 = quantize_absmax(weights, bits=4)
    restored_4 = dequantize(q_int4, scale_4)

    # 量子化誤差の計算
    def mse(original, restored):
        return sum((o - r) ** 2 for o, r in zip(original, restored)) / len(original)

    print("\n元の値 → INT8 → 復元 → INT4 → 復元:")
    for i in range(min(8, len(weights))):
        print(f"  {weights[i]:+.4f} → {q_int8[i]:+4d} → {restored_8[i]:+.4f}"
              f"  |  → {q_int4[i]:+3d} → {restored_4[i]:+.4f}")

    print(f"\n量子化誤差 (MSE):")
    print(f"  INT8: {mse(weights, restored_8):.6f}")
    print(f"  INT4: {mse(weights, restored_4):.6f}")
    print(f"  INT4/INT8 誤差比: {mse(weights, restored_4)/mse(weights, restored_8):.1f}x")

    print(f"""
量子化手法の比較:
┌────────────┬──────────┬───────────┬──────────────────────────┐
│ 手法       │ ビット数 │ メモリ削減│ 特徴                     │
├────────────┼──────────┼───────────┼──────────────────────────┤
│ FP16       │ 16       │ 2x        │ 学習・推論の標準         │
│ INT8       │ 8        │ 4x        │ 精度劣化ほぼなし         │
│ GPTQ       │ 4        │ 8x        │ 重みのみ量子化、高速     │
│ AWQ        │ 4        │ 8x        │ 重要な重みを保護         │
│ GGUF       │ 2-8      │ 4-16x     │ llama.cpp 用、CPU 推論   │
│ bitsandbytes│ 4 (NF4) │ 8x        │ QLoRA で使用             │
└────────────┴──────────┴───────────┴──────────────────────────┘

7B モデルのメモリ:
  FP32: 28 GB → FP16: 14 GB → INT8: 7 GB → INT4: 3.5 GB
""")


def demo_speculative_decoding():
    """
    Speculative Decoding シミュレーション
    =====================================
    小さなドラフトモデルで高速に候補生成 → 大モデルで検証
    """
    print("[Speculative Decoding]")

    # ドラフトモデル (小, 高速) と ターゲットモデル (大, 高精度) をシミュレート
    random.seed(42)
    vocab = ["the", "cat", "sat", "on", "mat"]

    # ドラフトモデル: 高速だがやや不正確
    draft_probs = {
        "<s>": [0.5, 0.2, 0.1, 0.1, 0.1],
        "the": [0.05, 0.4, 0.1, 0.2, 0.25],
        "cat": [0.1, 0.05, 0.5, 0.2, 0.15],
        "sat": [0.1, 0.05, 0.05, 0.6, 0.2],
        "on":  [0.5, 0.1, 0.05, 0.05, 0.3],
    }
    # ターゲットモデル: 高精度
    target_probs = {
        "<s>": [0.6, 0.15, 0.05, 0.1, 0.1],
        "the": [0.03, 0.45, 0.05, 0.17, 0.3],
        "cat": [0.08, 0.02, 0.55, 0.25, 0.1],
        "sat": [0.05, 0.03, 0.02, 0.7, 0.2],
        "on":  [0.55, 0.08, 0.02, 0.05, 0.3],
    }

    # ドラフトで K トークン一括生成 → ターゲットで検証
    K = 3  # 投機的生成するトークン数
    last = "<s>"
    draft_tokens = []

    for _ in range(K):
        probs = draft_probs.get(last, [0.2] * 5)
        r = random.random()
        cum = 0.0
        for i, p in enumerate(probs):
            cum += p
            if r <= cum:
                draft_tokens.append(vocab[i])
                last = vocab[i]
                break

    print(f"  ドラフト生成: {draft_tokens}")

    # ターゲットモデルで一括検証 (並列に全トークンを評価可能)
    accepted = 0
    last = "<s>"
    for token in draft_tokens:
        t_probs = target_probs.get(last, [0.2] * 5)
        d_probs = draft_probs.get(last, [0.2] * 5)
        idx = vocab.index(token)

        # 受理確率: min(1, p_target / p_draft)
        accept_prob = min(1.0, t_probs[idx] / (d_probs[idx] + 1e-10))
        if random.random() < accept_prob:
            accepted += 1
            last = token
        else:
            break

    print(f"  受理トークン数: {accepted}/{K}")
    print(f"  → ドラフト1回 + ターゲット1回で {accepted} トークン生成")
    print(f"  → 通常の {accepted}x 高速化 (理論上)")

    print("""
  Speculative Decoding のポイント:
    - ドラフトモデル: 小さく高速 (例: 1B) で K トークン生成
    - ターゲットモデル: 大きく高精度 (例: 70B) で一括検証
    - 出力品質はターゲットモデルと同一 (確率的に保証)
    - 速度: 2-3x 高速化が典型的

  Model Parallelism の種類:
    Tensor Parallel:   各層を GPU 間で分割 (行列演算を分割)
    Pipeline Parallel: 層ごとに異なる GPU に配置
    Data Parallel:     同じモデルを複数 GPU にコピー (バッチ分割)
""")


# ============================================================
# 8. Evaluation メトリクス
# ============================================================

def calc_perplexity(probs: List[float]) -> float:
    """
    Perplexity (パープレキシティ)
    =============================
    言語モデルの基本評価指標
    PPL = exp(-1/N × Σ log P(w_i))
    低い → モデルが「驚かない」 → 良いモデル
    """
    n = len(probs)
    log_sum = sum(math.log(p + 1e-10) for p in probs)
    return math.exp(-log_sum / n)


def calc_bleu(reference: List[str], hypothesis: List[str],
              max_n: int = 4) -> float:
    """
    BLEU (Bilingual Evaluation Understudy)
    =======================================
    機械翻訳の品質評価。n-gram の一致率を測定。

    BLEU = BP × exp(Σ w_n × log p_n)
      BP: Brevity Penalty (短すぎるペナルティ)
      p_n: n-gram precision
    """
    def get_ngrams(tokens, n):
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    precisions = []
    for n in range(1, max_n + 1):
        ref_ngrams = collections.Counter(get_ngrams(reference, n))
        hyp_ngrams = collections.Counter(get_ngrams(hypothesis, n))

        clipped = sum(min(count, ref_ngrams.get(ng, 0))
                      for ng, count in hyp_ngrams.items())
        total = max(sum(hyp_ngrams.values()), 1)
        precisions.append(clipped / total)

    # ゼロ精度の処理
    if any(p == 0 for p in precisions):
        return 0.0

    # 幾何平均
    log_avg = sum(math.log(p) for p in precisions) / max_n

    # Brevity Penalty
    bp = 1.0
    if len(hypothesis) < len(reference):
        bp = math.exp(1 - len(reference) / len(hypothesis))

    return bp * math.exp(log_avg)


def calc_rouge_n(reference: List[str], hypothesis: List[str],
                 n: int = 1) -> Dict[str, float]:
    """
    ROUGE-N (Recall-Oriented Understudy for Gisting Evaluation)
    ============================================================
    要約品質の評価。参照要約の n-gram がどれだけ再現されたか。
    BLEU は precision ベース、ROUGE は recall ベース。
    """
    def get_ngrams(tokens, n):
        return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

    ref_ngrams = collections.Counter(get_ngrams(reference, n))
    hyp_ngrams = collections.Counter(get_ngrams(hypothesis, n))

    overlap = sum(min(ref_ngrams[ng], hyp_ngrams.get(ng, 0))
                  for ng in ref_ngrams)

    recall = overlap / max(sum(ref_ngrams.values()), 1)
    precision = overlap / max(sum(hyp_ngrams.values()), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)

    return {"precision": precision, "recall": recall, "f1": f1}


def calc_rouge_l(reference: List[str], hypothesis: List[str]) -> Dict[str, float]:
    """
    ROUGE-L: 最長共通部分列 (LCS) ベースの評価
    """
    def lcs_length(x, y):
        m, n = len(x), len(y)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if x[i-1] == y[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        return dp[m][n]

    lcs = lcs_length(reference, hypothesis)
    recall = lcs / max(len(reference), 1)
    precision = lcs / max(len(hypothesis), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)
    return {"precision": precision, "recall": recall, "f1": f1}


def demo_evaluation():
    """評価メトリクスのデモ"""
    print("=" * 60)
    print("Evaluation メトリクス")
    print("=" * 60)

    # --- Perplexity ---
    print("\n[Perplexity]")
    good_probs = [0.8, 0.7, 0.9, 0.6, 0.85]   # 自信のある予測
    bad_probs = [0.1, 0.2, 0.15, 0.3, 0.1]     # 不確かな予測
    print(f"  良いモデル: PPL = {calc_perplexity(good_probs):.2f} (低い=良い)")
    print(f"  悪いモデル: PPL = {calc_perplexity(bad_probs):.2f}")
    print("  目安: GPT-3 ≈ 20, GPT-4 ≈ 8-10 (データセット依存)")

    # --- BLEU ---
    print("\n[BLEU Score]")
    ref = "the cat sat on the mat".split()
    hyp_good = "the cat sat on the mat".split()
    hyp_ok = "the cat is on the mat".split()
    hyp_bad = "a dog stood in the park".split()

    print(f"  参照: {' '.join(ref)}")
    print(f"  完全一致:  BLEU = {calc_bleu(ref, hyp_good):.4f}")
    print(f"  部分一致:  BLEU = {calc_bleu(ref, hyp_ok):.4f}")
    print(f"  不一致:    BLEU = {calc_bleu(ref, hyp_bad):.4f}")

    # --- ROUGE ---
    print("\n[ROUGE Score]")
    ref_summ = "the quick brown fox jumps over the lazy dog".split()
    hyp_summ = "the fast brown fox leaps over the dog".split()

    rouge1 = calc_rouge_n(ref_summ, hyp_summ, n=1)
    rouge2 = calc_rouge_n(ref_summ, hyp_summ, n=2)
    rouge_l = calc_rouge_l(ref_summ, hyp_summ)

    print(f"  参照:   {' '.join(ref_summ)}")
    print(f"  仮説:   {' '.join(hyp_summ)}")
    print(f"  ROUGE-1 F1: {rouge1['f1']:.4f}")
    print(f"  ROUGE-2 F1: {rouge2['f1']:.4f}")
    print(f"  ROUGE-L F1: {rouge_l['f1']:.4f}")

    print(f"""
┌──────────────┬────────────────────────────────────────────┐
│ メトリクス   │ 特徴・用途                                 │
├──────────────┼────────────────────────────────────────────┤
│ Perplexity   │ 言語モデルの内在的品質。低い=良い          │
│ BLEU         │ 翻訳品質 (precision ベース)                │
│ ROUGE        │ 要約品質 (recall ベース)                   │
│ BERTScore    │ 埋め込みの類似度。意味的一致を測定         │
│ LLM-as-Judge │ GPT-4 等で品質を評価。人間相関が高い       │
│ Hallucination│ 事実性検証。RAG ではソース照合で検出       │
└──────────────┴────────────────────────────────────────────┘

Hallucination 検出手法:
  1. ソース照合:   生成テキストとソース文書の整合性チェック
  2. 自己一貫性:   複数回生成して矛盾を検出
  3. NLI モデル:   含意関係を判定 (entailment / contradiction)
  4. Knowledge DB: 知識グラフとの照合
""")


# ============================================================
# 9. 学習優先度 (Tier)
# ============================================================

def show_learning_tiers():
    """LLM エンジニアリングの学習優先度"""
    print("=" * 60)
    print("LLM エンジニアリング 学習ロードマップ")
    print("=" * 60)
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tier 1: 必須基礎 (1-2週間)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  □ Tokenization (BPE の理解)
    → API 使用時のトークン数見積もり、コスト計算
  □ Transformer / Attention の概念理解
    → モデル選択の判断基準
  □ デコーディング戦略 (Temperature, Top-P)
    → API パラメータの適切な設定
  □ 主要メトリクス (Perplexity, BLEU, ROUGE)
    → モデル評価の基礎

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tier 2: 実務必須 (2-4週間)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  □ アーキテクチャ比較 (Encoder/Decoder/Enc-Dec)
    → タスクに応じたモデル選択
  □ LoRA / QLoRA ファインチューニング
    → 実務で最も使用頻度の高い学習手法
  □ 量子化 (INT8, INT4, GGUF)
    → モデルのデプロイ・コスト最適化
  □ RLHF / DPO の概念
    → ChatGPT 型モデルの仕組み理解

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tier 3: 実装力強化 (1-2ヶ月)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  □ KV-Cache / MQA / GQA
    → 推論最適化の深い理解
  □ Flash Attention
    → GPU メモリ効率の最適化
  □ Speculative Decoding
    → 推論速度の最適化
  □ Continuous Batching (vLLM)
    → サービング効率の最大化
  □ LLM-as-Judge / Hallucination 検出
    → 品質保証パイプライン構築

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tier 4: エキスパート (3ヶ月+)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  □ Model Parallelism (Tensor/Pipeline/Data)
    → 大規模モデルの分散学習・推論
  □ RLHF パイプライン構築 (PPO 実装)
    → 独自モデルのアラインメント
  □ カスタム Tokenizer 設計
    → ドメイン特化モデルの最適化
  □ BERTScore / 高度な評価パイプライン
    → 研究レベルの評価システム

PM 視点での活用:
  - Tier 1-2 は LLM プロダクト企画・判断に必須
  - コスト見積もり: トークン数 × モデルサイズ × 量子化
  - 品質 vs コストのトレードオフ判断
  - ファインチューニング要否の判断基準
""")


# ============================================================
# メイン実行
# ============================================================

def main():
    sections = [
        ("1. Tokenization の進化", demo_tokenization_evolution),
        ("1b. BPE 完全実装", demo_bpe),
        ("2. Attention Mechanism", demo_attention),
        ("2b. KV-Cache", demo_kv_cache),
        ("3. LLM アーキテクチャ比較", show_architecture_comparison),
        ("4. Decoding Strategies", demo_decoding),
        ("5. LoRA Fine-tuning", demo_lora),
        ("6. RLHF / DPO", demo_rlhf),
        ("7. 量子化", demo_quantization),
        ("7b. Speculative Decoding", demo_speculative_decoding),
        ("8. Evaluation メトリクス", demo_evaluation),
        ("9. 学習ロードマップ", show_learning_tiers),
    ]

    print("╔" + "═" * 58 + "╗")
    print("║  LLM / NLP エンジニアリング ディープダイブ              ║")
    print("║  Tokenization → Attention → Decoding → RLHF → 最適化  ║")
    print("╚" + "═" * 58 + "╝")
    print()

    for title, func in sections:
        print(f"\n{'━' * 60}")
        print(f"  {title}")
        print(f"{'━' * 60}\n")
        func()
        print()

    print("=" * 60)
    print("全セクション完了！")
    print("=" * 60)


if __name__ == "__main__":
    main()
