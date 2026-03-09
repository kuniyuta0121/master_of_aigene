"""
phase_ds4_computer_vision/cv_from_scratch.py
=============================================
Computer Vision - CNN から Vision Transformer まで

なぜ CV が必要か:
  Tesla Autopilot: カメラ映像からリアルタイム物体検出
  Google: 画像検索・Google Lens・医療画像解析
  IBM: 製造業の外観検査・文書OCR

このフェーズで学ぶこと:
  1. 画像処理の基礎（フィルタリング・エッジ検出・データ拡張）
  2. CNN の仕組み（畳み込み・プーリング・チャネル）をゼロから
  3. 代表的アーキテクチャの進化（LeNet → ResNet → EfficientNet）
  4. 物体検出の仕組み（アンカーボックス・IoU・NMS）
  5. Vision Transformer（ViT）- なぜ Attention が画像にも有効か

実行方法:
  pip install torch torchvision matplotlib
  python cv_from_scratch.py

考えてほしい疑問:
  Q1. 畳み込みが全結合より優れる理由は？（局所性・パラメータ共有・平行移動不変性）
  Q2. プーリングの役割は？（ダウンサンプリング・位置不変性・計算量削減）
  Q3. ResNet のスキップ接続がなぜ深いネットワークを可能にするか？
  Q4. 物体検出で IoU が重要な理由は？（予測ボックスと正解の重なり度合い）
  Q5. Vision Transformer は CNN と比べて何が優れ、何が劣るか？
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 画像処理の基礎（NumPy のみ）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def convolution_2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    2D 畳み込みをゼロから実装（NumPy のみ）

    畳み込みの直感:
      ・小さな「フィルタ（カーネル）」を画像上でスライドさせる
      ・各位置でフィルタと画像の要素積の和を計算
      ・エッジ検出・ぼかし・シャープニングなどが可能

    CNN はこのカーネルの値を「自動的に学習する」
    """
    ih, iw = image.shape
    kh, kw = kernel.shape
    oh, ow = ih - kh + 1, iw - kw + 1

    output = np.zeros((oh, ow))
    for i in range(oh):
        for j in range(ow):
            # フィルタと画像のパッチの要素積の和
            output[i, j] = np.sum(image[i:i+kh, j:j+kw] * kernel)

    return output


def demo_image_processing() -> None:
    """画像フィルタリングのデモ"""
    print("\n" + "━" * 60)
    print("🖼️  1. 画像処理の基礎")
    print("━" * 60)

    # テスト画像（8×8 のグレースケール）
    image = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ], dtype=float)

    # 各種カーネル
    kernels = {
        "Sobel X (縦エッジ)": np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]),
        "Sobel Y (横エッジ)": np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]),
        "ぼかし (平均)":      np.ones((3, 3)) / 9,
        "シャープニング":     np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]),
    }

    for name, kernel in kernels.items():
        result = convolution_2d(image, kernel)
        print(f"\n  {name}: 出力形状 {result.shape}")
        print(f"    最大値={result.max():.2f}, 最小値={result.min():.2f}")

    print("""
  ポイント:
    ・Sobel フィルタ: エッジ（境界線）を検出
    ・ぼかし: ノイズ除去（前処理で使用）
    ・CNN は これらのカーネルの値を自動学習する
    ・初期層: エッジ検出 → 中間層: テクスチャ → 深い層: 物体の部品
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. CNN をゼロから構築 (PyTorch)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SimpleCNN(nn.Module):
    """
    シンプルな CNN (LeNet スタイル) - MNIST 手書き数字認識

    構造:
      入力 (1, 28, 28) → Conv → ReLU → Pool → Conv → ReLU → Pool → FC → FC → 出力 (10)

    各層の役割:
      Conv2d: 局所的なパターン（エッジ・角・テクスチャ）を検出
      ReLU: 非線形性（これがないと深い層も1層の線形変換と等価）
      MaxPool2d: 空間解像度を半分に → 計算量削減 + 位置の微小変化に頑健
      Flatten: 2Dの特徴マップを1Dのベクトルに
      Linear: 特徴量の組み合わせで最終分類

    パラメータ数の考え方:
      Conv2d(1, 16, 3): 1×16×3×3 + 16 = 160 パラメータ
      Linear(1600, 10): 1600×10 + 10 = 16010 パラメータ
      → FC層がパラメータの大部分を占める（これが問題）
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.features = nn.Sequential(
            # 第1畳み込みブロック: (1, 28, 28) → (16, 14, 14)
            nn.Conv2d(1, 16, kernel_size=3, padding=1),   # (1, 28, 28) → (16, 28, 28)
            nn.BatchNorm2d(16),                            # バッチ正規化（学習安定化）
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),                            # (16, 28, 28) → (16, 14, 14)

            # 第2畳み込みブロック: (16, 14, 14) → (32, 7, 7)
            nn.Conv2d(16, 32, kernel_size=3, padding=1),   # (16, 14, 14) → (32, 14, 14)
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),                            # (32, 14, 14) → (32, 7, 7)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),                                  # (32, 7, 7) → (1568)
            nn.Dropout(0.5),                               # 過学習防止
            nn.Linear(32 * 7 * 7, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. ResNet - 残差接続の威力
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ResidualBlock(nn.Module):
    """
    残差ブロック（Residual Block）

    核心: y = F(x) + x   （スキップ接続）

    なぜ革命的か:
      ・深いネットワーク（100層以上）を訓練可能に
      ・勾配消失問題を解決（勾配がスキップ接続を通って直接流れる）
      ・最悪でも「何もしない」（F(x)=0 なら y=x）を学習できる

    数学的理解:
      ∂L/∂x = ∂L/∂y × (∂F(x)/∂x + 1)
                                    ↑ この +1 が勾配消失を防ぐ

    考えてほしい疑問:
      ・スキップ接続がないとき（y = F(x)）深いほど精度が下がるのはなぜ？
      ・Pre-activation ResNet (BN→ReLU→Conv) が Post-activation より良い理由は？
    """

    def __init__(self, channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels, channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # F(x) + x  ← これがスキップ接続
        return F.relu(self.block(x) + x)


class MiniResNet(nn.Module):
    """
    ミニ ResNet: MNIST/CIFAR-10 用の小規模版

    本家 ResNet-50 との違い:
      ResNet-50: 50層, 25.6M パラメータ, ImageNet用
      MiniResNet: 8層, ~50K パラメータ, MNIST用

    アーキテクチャ進化の系譜:
      LeNet (1998) → AlexNet (2012) → VGG (2014) → GoogLeNet (2014)
      → ResNet (2015) → DenseNet (2017) → EfficientNet (2019)
      → Vision Transformer (2020) → Swin Transformer (2021)
    """

    def __init__(self, num_classes: int = 10):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1, bias=False),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
        )
        self.res_blocks = nn.Sequential(
            ResidualBlock(16),
            ResidualBlock(16),
        )
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),  # Global Average Pooling → (16, 1, 1)
            nn.Flatten(),
            nn.Linear(16, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.res_blocks(x)
        return self.head(x)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 物体検出の基礎概念
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def intersection_over_union(box1: np.ndarray, box2: np.ndarray) -> float:
    """
    IoU (Intersection over Union): 2つのバウンディングボックスの重なり度合い

    box: [x1, y1, x2, y2]  (左上, 右下)

    IoU = 交差面積 / 和面積
    IoU = 1.0: 完全一致
    IoU = 0.0: 重なりなし

    用途:
      ・予測ボックスと正解ボックスの評価
      ・NMS（非最大値抑制）で重複検出を除去
      ・mAP（平均精度）の計算
    """
    # 交差領域
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)

    # 各ボックスの面積
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    # 和面積 = 面積1 + 面積2 - 交差面積
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def non_max_suppression(
    boxes: np.ndarray,
    scores: np.ndarray,
    iou_threshold: float = 0.5,
) -> list[int]:
    """
    NMS (Non-Maximum Suppression): 重複する検出ボックスを除去

    物体検出モデルは1つの物体に対して複数のボックスを出力する。
    NMS で「最もスコアが高いボックス」だけを残す。

    アルゴリズム:
      1. スコアの高い順にソート
      2. 最高スコアのボックスを選択
      3. 選択したボックスと IoU > threshold のボックスを除去
      4. 残りがなくなるまで繰り返す

    考えてほしい疑問:
      ・iou_threshold を低くすると何が起きるか？（抑制が強い → 見逃し増加）
      ・Soft-NMS はどう改善するか？（スコアを下げるだけで除去しない）
    """
    order = scores.argsort()[::-1]
    keep = []

    while len(order) > 0:
        best_idx = order[0]
        keep.append(best_idx)

        if len(order) == 1:
            break

        remaining = order[1:]
        ious = np.array([
            intersection_over_union(boxes[best_idx], boxes[idx])
            for idx in remaining
        ])

        # IoU が閾値以下のボックスだけ残す
        order = remaining[ious <= iou_threshold]

    return keep


def demo_object_detection() -> None:
    print("\n" + "━" * 60)
    print("🎯 4. 物体検出の基礎")
    print("━" * 60)

    # IoU テスト
    box_gt = np.array([100, 100, 200, 200])   # 正解 (Ground Truth)
    box_p1 = np.array([110, 110, 210, 210])   # 予測1: ほぼ一致
    box_p2 = np.array([300, 300, 400, 400])   # 予測2: 全く重ならない
    box_p3 = np.array([150, 150, 250, 250])   # 予測3: 部分重なり

    print(f"  正解ボックス: {box_gt}")
    print(f"  予測1 (ほぼ一致): IoU = {intersection_over_union(box_gt, box_p1):.3f}")
    print(f"  予測2 (重ならない): IoU = {intersection_over_union(box_gt, box_p2):.3f}")
    print(f"  予測3 (部分重なり): IoU = {intersection_over_union(box_gt, box_p3):.3f}")

    # NMS テスト
    boxes = np.array([
        [100, 100, 200, 200],  # box 0
        [105, 105, 205, 205],  # box 1 (box 0 とほぼ同じ)
        [110, 110, 210, 210],  # box 2 (box 0 とほぼ同じ)
        [300, 300, 400, 400],  # box 3 (離れている)
    ])
    scores = np.array([0.9, 0.85, 0.7, 0.95])
    kept = non_max_suppression(boxes, scores, iou_threshold=0.5)
    print(f"\n  NMS 結果: 保持されたボックス = {kept}  (期待: [3, 0] = 最高スコア2つ)")

    print("""
  物体検出の主要アーキテクチャ:
  ┌───────────────────────────────────────────────────────────┐
  │ 手法           │ 速度    │ 精度    │ 用途               │
  ├───────────────────────────────────────────────────────────│
  │ YOLO v8        │ ★★★★★ │ ★★★★  │ リアルタイム検出    │
  │ Faster R-CNN   │ ★★★   │ ★★★★★│ 高精度検出          │
  │ SSD            │ ★★★★  │ ★★★   │ モバイル向け        │
  │ DETR           │ ★★★   │ ★★★★  │ Transformer ベース  │
  └───────────────────────────────────────────────────────────┘

  Tesla Autopilot での使われ方:
    ・8台のカメラから同時に物体検出
    ・歩行者・車両・信号・標識を区別
    ・リアルタイム推論（遅延 < 50ms）
    ・BEV (Bird's Eye View) へのプロジェクション
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Vision Transformer (ViT)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PatchEmbedding(nn.Module):
    """
    画像をパッチに分割して埋め込みベクトルに変換

    ViT の核心アイデア:
      画像 (H, W, C) → パッチ列 (N, P²C) → 線形射影 → (N, D)
      N = (H/P) × (W/P) = パッチ数
      P = パッチサイズ

    例: 224×224 画像, P=16 → 14×14 = 196 パッチ
    各パッチは「トークン」として Transformer に入力される
    ← NLP の「単語トークン」と同じ扱い！

    考えてほしい疑問:
      ・パッチサイズ P が小さいと何が起きるか？
        → パッチ数 N が増え、Attention の O(N²) 計算量が爆発
      ・CNN との違いは何か？
        → CNN: 局所的受容野が徐々に広がる
        → ViT: 最初から全パッチ間で Attention（グローバル）
    """

    def __init__(self, img_size: int = 28, patch_size: int = 7,
                 in_channels: int = 1, embed_dim: int = 64):
        super().__init__()
        self.num_patches = (img_size // patch_size) ** 2
        self.patch_size = patch_size

        # 畳み込みでパッチ分割と線形射影を同時に行う（効率的）
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # (B, C, H, W) → (B, D, H/P, W/P) → (B, N, D)
        x = self.proj(x)                    # (B, D, H/P, W/P)
        x = x.flatten(2).transpose(1, 2)    # (B, N, D)
        return x


class MiniViT(nn.Module):
    """
    ミニ Vision Transformer (ViT) - MNIST 手書き数字認識

    「An Image is Worth 16x16 Words」(Dosovitskiy et al., 2020)

    構造:
      1. 画像をパッチに分割
      2. 各パッチを線形射影で埋め込み
      3. [CLS] トークンを先頭に追加
      4. 位置埋め込みを加算
      5. Transformer Encoder で処理
      6. [CLS] トークンの出力で分類

    CNN vs ViT:
      ┌────────────────────────────────────────────┐
      │              │ CNN            │ ViT          │
      ├────────────────────────────────────────────│
      │ 帰納バイアス │ 局所性・平行移動│ なし（汎用） │
      │ データ効率   │ 少量で学習可能  │ 大量データ必要│
      │ 受容野       │ 段階的に拡大    │ 最初からグローバル│
      │ スケーリング │ 限界あり        │ スケールで向上│
      └────────────────────────────────────────────┘

    考えてほしい疑問:
      ・ViT が CNN より強くなるのはデータ量がどの程度のとき？
        → 約 1000万枚以上（JFT-300M で事前学習したとき最強）
      ・小規模データでは CNN が有利な理由は？
        → 局所性の帰納バイアスが正則化として機能する
    """

    def __init__(self, img_size: int = 28, patch_size: int = 7,
                 in_channels: int = 1, num_classes: int = 10,
                 embed_dim: int = 64, num_heads: int = 4,
                 num_layers: int = 2, dropout: float = 0.1):
        super().__init__()

        self.patch_embed = PatchEmbedding(img_size, patch_size, in_channels, embed_dim)
        num_patches = self.patch_embed.num_patches

        # [CLS] トークン: 分類に使う特殊トークン
        self.cls_token = nn.Parameter(torch.randn(1, 1, embed_dim) * 0.02)

        # 位置埋め込み（学習可能）
        self.pos_embed = nn.Parameter(
            torch.randn(1, num_patches + 1, embed_dim) * 0.02
        )

        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads,
            dim_feedforward=embed_dim * 4, dropout=dropout,
            activation="gelu", batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 分類ヘッド
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]

        # 1. パッチ分割 + 埋め込み: (B, N, D)
        x = self.patch_embed(x)

        # 2. [CLS] トークンを先頭に追加: (B, N+1, D)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)

        # 3. 位置埋め込みを加算
        x = x + self.pos_embed

        # 4. Transformer Encoder
        x = self.transformer(x)

        # 5. [CLS] トークンの出力で分類
        cls_output = self.norm(x[:, 0])  # 最初のトークン = [CLS]
        return self.head(cls_output)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. データ拡張（Data Augmentation）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def explain_data_augmentation() -> None:
    print("\n" + "━" * 60)
    print("🔄 6. データ拡張（Data Augmentation）")
    print("━" * 60)
    print("""
  なぜデータ拡張が重要か:
    ・モデルの汎化性能を向上（過学習を防ぐ）
    ・データ量が少ないとき特に効果的
    ・「異なる条件で撮影された画像」を擬似的に生成

  代表的な手法:
  ┌────────────────────────────────────────────────────┐
  │ 手法              │ 効果             │ コード例     │
  ├────────────────────────────────────────────────────│
  │ RandomFlip        │ 左右反転          │ ← 最も基本   │
  │ RandomRotation    │ 回転 (±15°)       │              │
  │ RandomCrop        │ ランダム切り取り  │              │
  │ ColorJitter       │ 明るさ・彩度変更  │              │
  │ RandomErasing     │ 矩形マスキング    │ ← Dropout 的 │
  │ Mixup             │ 2画像を混合       │ ← 正則化効果 │
  │ CutMix            │ 切り貼り          │ ← Mixup進化版│
  │ AugMax            │ 最悪ケース拡張    │ ← ロバスト性 │
  └────────────────────────────────────────────────────┘

  PyTorch での実装:
    from torchvision import transforms
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

  Tesla Autopilot での拡張:
    ・天候シミュレーション（雨・霧・逆光）
    ・時間帯変更（昼→夜）
    ・センサーノイズの付加
    ・レアイベント（動物の飛び出し等）の合成
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 学習 & 評価
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def train_and_compare() -> None:
    """CNN vs ResNet vs ViT を MNIST で比較"""
    print("\n" + "━" * 60)
    print("🏋️  CNN vs ResNet vs ViT ���比較 (MNIST)")
    print("━" * 60)

    from torchvision import datasets, transforms

    device = torch.device("mps" if torch.backends.mps.is_available()
                          else "cuda" if torch.cuda.is_available()
                          else "cpu")
    print(f"  デバイス: {device}")

    # データ
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])
    train_data = datasets.MNIST("./data", train=True, download=True, transform=transform)
    test_data = datasets.MNIST("./data", train=False, transform=transform)

    # 訓練データを小さくして速度を優先（デモ用）
    train_subset = torch.utils.data.Subset(train_data, range(5000))
    test_subset = torch.utils.data.Subset(test_data, range(1000))

    train_loader = DataLoader(train_subset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_subset, batch_size=256)

    models = {
        "SimpleCNN":  SimpleCNN(num_classes=10),
        "MiniResNet": MiniResNet(num_classes=10),
        "MiniViT":    MiniViT(num_classes=10),
    }

    results = {}
    for name, model in models.items():
        model = model.to(device)
        param_count = sum(p.numel() for p in model.parameters())
        optimizer = optim.Adam(model.parameters(), lr=1e-3)

        # 学習（3エポック - デモ用）
        model.train()
        for epoch in range(3):
            total_loss = 0
            for X, y in train_loader:
                X, y = X.to(device), y.to(device)
                optimizer.zero_grad()
                loss = F.cross_entropy(model(X), y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

        # 評価
        model.eval()
        correct = 0
        with torch.no_grad():
            for X, y in test_loader:
                X, y = X.to(device), y.to(device)
                correct += (model(X).argmax(1) == y).sum().item()
        acc = correct / len(test_subset)
        results[name] = (acc, param_count)
        print(f"  {name:12s}: 精度={acc:.3f}, パラメータ={param_count:,}")

    print("""
  考察:
    ・MNIST (28x28, 少量) では CNN が ViT と同等かやや優位
    ・ImageNet (224x224, 大量) では ViT が CNN を上回る
    ・ResNet はスキップ接続で深いネットワークを安定的に学習
    ・ViT の真価は大規模データ + 大規模モデルで発揮される
""")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Phase DS4: Computer Vision - CNN から ViT まで          ║")
    print("╚════════════════════════════════════════════════════════════╝")

    demo_image_processing()
    demo_object_detection()
    explain_data_augmentation()
    train_and_compare()

    print("━" * 60)
    print("✅ 完了！Google/Tesla/IBM 面接での想定Q&A:")
    print("""
  Q: 「CNN の畳み込み層は何を学習しているのか？」
  A: 初期層はエッジ・角を検出するフィルタ、中間層はテクスチャ、
     深い層は物体の部品（目・車輪など）を検出するフィルタを学習する。

  Q: 「ResNet のスキップ接続はなぜ有効か？」
  A: 勾配が恒等写像を通って直接流れるため勾配消失が起きない。
     最悪でも F(x)=0 を学習すれば x をそのまま通せる（劣化しない）。

  Q: 「YOLO と Faster R-CNN の違いは？」
  A: YOLO: 1段階（画像全体を一度に処理→高速だがやや低精度）
     Faster R-CNN: 2段階（領域提案→分類→高精度だが遅い）

  Q: 「ViT は CNN より常に優れているか？」
  A: いいえ。小規模データでは CNN が優位（帰納バイアスが正則化として機能）。
     大規模データ（1000万枚+）で ViT が CNN を上回る。

  [実装してみよう]
  1. CIFAR-10 で ResNet-18 を学習（torchvision.models.resnet18）
  2. YOLOv8 で webcam の物体検出（pip install ultralytics）
  3. Grad-CAM でCNNの注目領域を可視化
  4. HuggingFace の ViT で画像分類（transformers ライブラリ）
""")


if __name__ == "__main__":
    main()
