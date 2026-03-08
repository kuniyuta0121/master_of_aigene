"""
phase_ds1_ml_foundation/ml_from_scratch.py
==========================================
ML アルゴリズムをゼロから実装する

なぜ「ゼロから」が重要か:
  Google/Tesla/IBM の ML 面接では
  「勾配降下法を実装してください」
  「バックプロパゲーションを数式で説明してください」
  「決定木の分割基準を自分で実装してください」
  が必ず出る。sklearn.fit() を呼ぶのは「使う」であり「理解する」ではない。

実装するアルゴリズム:
  1. 線形回帰         - 解析解 + 勾配降下法
  2. ロジスティック回帰 - 確率的勾配降下法 + 交差エントロピー
  3. 決定木            - 情報利得 + 再帰分割
  4. K-Means           - ロイドのアルゴリズム
  5. PCA               - 固有値分解 via SVD
  6. ナイーブベイズ     - テキスト分類への応用

実行方法:
  pip install numpy scipy  (標準的な科学計算のみ)
  python ml_from_scratch.py

考えてほしい疑問:
  Q1. 正規方程式 θ = (X^T X)^-1 X^T y は N=10^6 のとき使えるか？（逆行列の計算量）
  Q2. 学習率が大きすぎると何が起きるか？小さすぎると？
  Q3. 決定木はなぜ過学習しやすいか？ランダムフォレストはどう解決するか？
  Q4. K-Means の初期化に K-Means++ が必要な理由は？
  Q5. PCA の主成分は何を表すか？なぜ固有値の大きい方向が重要か？
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 線形回帰 (Linear Regression)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LinearRegression:
    """
    線形回帰: y = X θ + ε

    2つのアプローチを実装する:
      A) 解析解 (Normal Equation): θ = (X^T X)^-1 X^T y
         - 利点: 1回で解ける、ハイパーパラメータ不要
         - 欠点: 特徴量数 n が多いと (X^T X) の逆行列計算が O(n³)

      B) 勾配降下法 (Gradient Descent): θ := θ - α ∇L
         - 利点: n が大きくても使える、ミニバッチ化可能
         - 欠点: 学習率の調整が必要

    損失関数: L = (1/2N) Σ (y_pred - y_true)²  [MSE]
    勾配:     ∂L/∂θ = (1/N) X^T (Xθ - y)
    """

    def __init__(self, learning_rate: float = 0.01, n_iterations: int = 1000,
                 method: str = "gradient_descent"):
        self.lr = learning_rate
        self.n_iter = n_iterations
        self.method = method
        self.theta: NDArray | None = None
        self.loss_history: list[float] = []

    def _add_bias(self, X: NDArray) -> NDArray:
        """バイアス項 (切片) を追加: X → [1, x1, x2, ...]"""
        N = X.shape[0]
        return np.hstack([np.ones((N, 1)), X])

    def fit(self, X: NDArray, y: NDArray) -> "LinearRegression":
        X_b = self._add_bias(X)
        N, n_features = X_b.shape

        if self.method == "normal_equation":
            # 解析解: θ = (X^T X)^-1 X^T y
            # np.linalg.lstsq は数値的に安定（擬似逆行列）
            self.theta, _, _, _ = np.linalg.lstsq(X_b, y, rcond=None)

        elif self.method == "gradient_descent":
            # ランダム初期化（小さい値）
            rng = np.random.default_rng(42)
            self.theta = rng.normal(0, 0.01, n_features)

            for iteration in range(self.n_iter):
                y_pred = X_b @ self.theta           # 予測
                error = y_pred - y                   # 誤差
                gradient = (1 / N) * X_b.T @ error  # 勾配: ∂L/∂θ
                self.theta -= self.lr * gradient     # パラメータ更新

                # 損失を記録
                loss = np.mean(error**2) / 2
                self.loss_history.append(loss)

                # 収束チェック
                if iteration > 0 and abs(self.loss_history[-2] - loss) < 1e-8:
                    print(f"    収束: {iteration}ステップ")
                    break

        return self

    def predict(self, X: NDArray) -> NDArray:
        return self._add_bias(X) @ self.theta

    def score(self, X: NDArray, y: NDArray) -> float:
        """決定係数 R²"""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        return 1 - ss_res / ss_tot


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. ロジスティック回帰 (Logistic Regression)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LogisticRegression:
    """
    2値分類: P(y=1|x) = σ(θ^T x)

    シグモイド関数: σ(z) = 1 / (1 + e^-z)
      - 出力を [0, 1] に押し込む
      - σ'(z) = σ(z)(1 - σ(z))  ← 導関数が美しい

    損失関数（バイナリ交差エントロピー）:
      L = -(1/N) Σ [y log(ŷ) + (1-y) log(1-ŷ)]

    なぜ MSE でなく交差エントロピーを使うか？
      MSE + シグモイドは「勾配消失」が起きやすい
      交差エントロピーの勾配: ∂L/∂θ = (1/N) X^T (ŷ - y)
      ← 線形回帰と同じ形！（最尤推定の観点から美しい対称性）
    """

    def __init__(self, learning_rate: float = 0.1, n_iterations: int = 1000,
                 regularization: float = 0.0):
        self.lr = learning_rate
        self.n_iter = n_iterations
        self.reg = regularization  # L2 正則化強度
        self.theta: NDArray | None = None

    @staticmethod
    def _sigmoid(z: NDArray) -> NDArray:
        # 数値安定化: 非常に大きな負の値でオーバーフローしないようにクリップ
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def fit(self, X: NDArray, y: NDArray) -> "LogisticRegression":
        N, n_features = X.shape
        rng = np.random.default_rng(42)
        self.theta = rng.normal(0, 0.01, n_features + 1)

        X_b = np.hstack([np.ones((N, 1)), X])

        for _ in range(self.n_iter):
            z = X_b @ self.theta
            y_pred = self._sigmoid(z)                    # 予測確率
            error = y_pred - y                           # 誤差

            # 勾配: ∂L/∂θ = (1/N) X^T (ŷ - y) + λθ (正則化項)
            gradient = (1 / N) * X_b.T @ error
            if self.reg > 0:
                reg_term = self.reg * self.theta
                reg_term[0] = 0  # バイアス項は正則化しない
                gradient += reg_term

            self.theta -= self.lr * gradient

        return self

    def predict_proba(self, X: NDArray) -> NDArray:
        X_b = np.hstack([np.ones((X.shape[0], 1)), X])
        return self._sigmoid(X_b @ self.theta)

    def predict(self, X: NDArray, threshold: float = 0.5) -> NDArray:
        return (self.predict_proba(X) >= threshold).astype(int)

    def score(self, X: NDArray, y: NDArray) -> float:
        return np.mean(self.predict(X) == y)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 決定木 (Decision Tree)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DecisionTree:
    """
    決定木: 再帰的な分割によるルールベース分類器

    分割基準: 情報利得 (Information Gain)
      IG(S, A) = H(S) - Σ (|Sv|/|S|) H(Sv)
      H(S) = -Σ p_i log2(p_i)  ← エントロピー

    代替基準: ジニ不純度
      Gini(S) = 1 - Σ p_i²
      計算が軽い（log がない）→ sklearn のデフォルト

    なぜ過学習するか:
      制約なしで成長させると各葉に1サンプルだけ → 訓練精度100%
      → max_depth, min_samples_split で制御

    ランダムフォレストとの違い:
      ・1本の木 vs 多数の木のアンサンブル
      ・全特徴量使用 vs ランダム部分集合を各分割で使用
      ・高バリアンス vs バリアンスを平均化して低減
    """

    class _Node:
        def __init__(self, feature: int | None = None, threshold: float | None = None,
                     left=None, right=None, value=None):
            self.feature = feature      # 分割特徴量のインデックス
            self.threshold = threshold  # 分割閾値
            self.left = left            # 左部分木 (特徴量 <= 閾値)
            self.right = right          # 右部分木 (特徴量 > 閾値)
            self.value = value          # 葉ノードのクラス予測

    def __init__(self, max_depth: int = 10, min_samples_split: int = 2,
                 criterion: str = "entropy"):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.criterion = criterion
        self.root: DecisionTree._Node | None = None

    def _entropy(self, y: NDArray) -> float:
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return -np.sum(probs * np.log2(probs + 1e-10))

    def _gini(self, y: NDArray) -> float:
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1 - np.sum(probs ** 2)

    def _impurity(self, y: NDArray) -> float:
        return self._entropy(y) if self.criterion == "entropy" else self._gini(y)

    def _best_split(self, X: NDArray, y: NDArray) -> tuple[int, float, float]:
        """全特徴量・全閾値を走査して最良の分割を見つける"""
        best_gain = -1.0
        best_feature, best_threshold = 0, 0.0
        parent_impurity = self._impurity(y)
        N = len(y)

        for feature_idx in range(X.shape[1]):
            thresholds = np.unique(X[:, feature_idx])
            for threshold in thresholds:
                left_mask = X[:, feature_idx] <= threshold
                right_mask = ~left_mask
                if left_mask.sum() == 0 or right_mask.sum() == 0:
                    continue

                left_y, right_y = y[left_mask], y[right_mask]
                # 情報利得 = 親のエントロピー - 重み付き子エントロピーの和
                gain = (parent_impurity
                        - (len(left_y) / N) * self._impurity(left_y)
                        - (len(right_y) / N) * self._impurity(right_y))

                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold

        return best_feature, best_threshold, best_gain

    def _build(self, X: NDArray, y: NDArray, depth: int) -> "_Node":
        N, n_features = X.shape
        n_classes = len(np.unique(y))

        # 終端条件: 純粋なノード、深さ制限、最小サンプル数
        if (n_classes == 1 or depth >= self.max_depth
                or N < self.min_samples_split):
            # 最多数クラスで予測
            return self._Node(value=np.bincount(y).argmax())

        feature, threshold, gain = self._best_split(X, y)

        if gain <= 0:
            return self._Node(value=np.bincount(y).argmax())

        left_mask = X[:, feature] <= threshold
        left = self._build(X[left_mask], y[left_mask], depth + 1)
        right = self._build(X[~left_mask], y[~left_mask], depth + 1)

        return self._Node(feature=feature, threshold=threshold,
                          left=left, right=right)

    def fit(self, X: NDArray, y: NDArray) -> "DecisionTree":
        self.root = self._build(X, y.astype(int), 0)
        return self

    def _traverse(self, x: NDArray, node: "_Node") -> int:
        if node.value is not None:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._traverse(x, node.left)
        return self._traverse(x, node.right)

    def predict(self, X: NDArray) -> NDArray:
        return np.array([self._traverse(x, self.root) for x in X])

    def score(self, X: NDArray, y: NDArray) -> float:
        return np.mean(self.predict(X) == y)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. K-Means クラスタリング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class KMeans:
    """
    K-Means: 非階層クラスタリング（教師なし学習）

    ロイドのアルゴリズム:
      1. k個の重心をランダムに初期化
      2. 各点を最近傍の重心に割り当て
      3. 重心を各クラスターの平均に更新
      4. 収束するまで2-3を繰り返す

    収束の保証:
      ・各ステップでSSE（クラスター内二乗和）は単調減少
      ・局所最適に収束する（大域的最適の保証はない）
      → K-Means++ 初期化で局所最適を避ける

    K-Means++ 初期化:
      1. ランダムに1つ選ぶ
      2. 各点を「既存の重心からの距離の二乗」に比例した確率で選ぶ
      → 重心が均等に散らばりやすくなる
      → Lloyd's アルゴリズムより O(log k) 倍の精度

    考えてほしい疑問:
      ・k をどう決めるか？（エルボー法、シルエット係数）
      ・球形でないクラスター（三日月型）に弱い理由は？
      ・DBSCAN はどんな場合に K-Means より優れるか？
    """

    def __init__(self, k: int = 3, max_iter: int = 300, init: str = "kmeans++",
                 n_init: int = 10, tol: float = 1e-4):
        self.k = k
        self.max_iter = max_iter
        self.init = init
        self.n_init = n_init
        self.tol = tol
        self.centroids: NDArray | None = None
        self.labels_: NDArray | None = None
        self.inertia_: float = float("inf")

    def _init_centroids(self, X: NDArray, rng: np.random.Generator) -> NDArray:
        if self.init == "random":
            idx = rng.choice(len(X), self.k, replace=False)
            return X[idx].copy()

        # K-Means++ 初期化
        centroids = [X[rng.integers(len(X))]]
        for _ in range(1, self.k):
            # 各点から最近傍重心への距離²を計算
            dists = np.min(
                np.array([np.sum((X - c) ** 2, axis=1) for c in centroids]),
                axis=0
            )
            # 距離²に比例した確率でサンプリング
            probs = dists / dists.sum()
            centroids.append(X[rng.choice(len(X), p=probs)])
        return np.array(centroids)

    def _assign(self, X: NDArray, centroids: NDArray) -> NDArray:
        """各点を最近傍の重心に割り当てる"""
        # ブロードキャストで全距離を一度に計算
        distances = np.sum((X[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2, axis=2)
        return np.argmin(distances, axis=1)

    def _compute_inertia(self, X: NDArray, labels: NDArray, centroids: NDArray) -> float:
        """SSE: クラスター内の二乗距離の和"""
        return sum(np.sum((X[labels == k] - centroids[k]) ** 2)
                   for k in range(self.k))

    def fit(self, X: NDArray) -> "KMeans":
        rng = np.random.default_rng(42)
        best_inertia = float("inf")
        best_centroids = None
        best_labels = None

        # n_init 回試して最良の結果を採用（局所最適を避ける）
        for _ in range(self.n_init):
            centroids = self._init_centroids(X, rng)

            for _ in range(self.max_iter):
                labels = self._assign(X, centroids)
                new_centroids = np.array([
                    X[labels == k].mean(axis=0) if (labels == k).any() else centroids[k]
                    for k in range(self.k)
                ])

                # 収束チェック: 重心の移動量
                shift = np.max(np.linalg.norm(new_centroids - centroids, axis=1))
                centroids = new_centroids
                if shift < self.tol:
                    break

            inertia = self._compute_inertia(X, labels, centroids)
            if inertia < best_inertia:
                best_inertia = inertia
                best_centroids = centroids
                best_labels = labels

        self.centroids = best_centroids
        self.labels_ = best_labels
        self.inertia_ = best_inertia
        return self

    def predict(self, X: NDArray) -> NDArray:
        return self._assign(X, self.centroids)

    def elbow_plot(self, X: NDArray, k_range: range = range(1, 11)) -> dict[int, float]:
        """エルボー法: 適切な k を決める"""
        print("  エルボー法（SSE vs k）:")
        inertias = {}
        for k in k_range:
            km = KMeans(k=k, n_init=3)
            km.fit(X)
            inertias[k] = km.inertia_
            bar = "█" * int(40 - km.inertia_ / max(inertias.values()) * 30)
            print(f"    k={k}: SSE={km.inertia_:8.1f} {bar}")
        return inertias


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 主成分分析 (PCA)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PCA:
    """
    主成分分析: 高次元データを低次元に圧縮

    直感: データの「分散が最大の方向」を主成分として選ぶ
      第1主成分 = 分散が最大の方向
      第2主成分 = 第1と直交し、残りの分散が最大の方向
      ...

    数学的手順:
      1. データを標準化（平均0、分散1）
      2. 共分散行列 C = (1/N) X^T X を計算
      3. 固有値分解: C = V Λ V^T
      4. 固有値の大きい順に固有ベクトルを選ぶ
      5. データを選んだ固有ベクトルに射影

    SVD との関係:
      X = U Σ V^T
      共分散行列の固有ベクトル = V（右特異ベクトル）
      固有値 = Σ² / N
      → np.linalg.svd で数値的に安定した計算が可能

    考えてほしい疑問:
      ・「説明分散比」とは何か？
      ・何次元に落とすか決める基準は？（累積説明分散比 ≥ 95% が一般的）
      ・t-SNE や UMAP はなぜ PCA より可視化に向いているか？
        （PCA は線形変換のみ、t-SNE/UMAP は非線形）
    """

    def __init__(self, n_components: int | None = None):
        self.n_components = n_components
        self.components_: NDArray | None = None
        self.explained_variance_ratio_: NDArray | None = None
        self.mean_: NDArray | None = None

    def fit(self, X: NDArray) -> "PCA":
        self.mean_ = X.mean(axis=0)
        X_centered = X - self.mean_

        # SVD による固有値分解（数値安定性が高い）
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        # 各主成分の説明分散比
        eigenvalues = S ** 2 / (len(X) - 1)
        total_var = eigenvalues.sum()
        self.explained_variance_ratio_ = eigenvalues / total_var

        # 主成分（固有ベクトル）
        n = self.n_components or X.shape[1]
        self.components_ = Vt[:n]  # 各行が主成分方向

        return self

    def transform(self, X: NDArray) -> NDArray:
        """データを主成分空間に射影"""
        return (X - self.mean_) @ self.components_.T

    def fit_transform(self, X: NDArray) -> NDArray:
        return self.fit(X).transform(X)

    def inverse_transform(self, X_transformed: NDArray) -> NDArray:
        """圧縮されたデータを元の空間に戻す（近似復元）"""
        return X_transformed @ self.components_ + self.mean_

    def cumulative_variance_plot(self) -> None:
        cumvar = np.cumsum(self.explained_variance_ratio_)
        print("  累積説明分散比:")
        for i, (ratio, cum) in enumerate(
            zip(self.explained_variance_ratio_, cumvar), start=1
        ):
            bar = "█" * int(ratio * 100)
            print(f"    PC{i}: {ratio:.1%} | 累積: {cum:.1%} {bar}")
            if cum >= 0.95:
                print(f"    → {i}次元で95%の分散を説明できる")
                break


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. ナイーブベイズ (Naive Bayes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class NaiveBayes:
    """
    多項分布ナイーブベイズ: テキスト分類

    P(クラス|単語群) ∝ P(クラス) × Π P(単語|クラス)

    「ナイーブ」な仮定: 各単語は条件付き独立
      P(w1, w2, ..., wn | クラス) = Π P(wi | クラス)
      ← 実際には「機械」と「学習」は独立でないが、実用的には良く機能する

    ラプラス平滑化:
      P(w|クラス) = (count(w, クラス) + α) / (count(クラス) + α × |V|)
      α=1: ラプラス平滑化
      ← 訓練データで見たことのない単語の確率が0にならないように
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.class_log_prior_: dict[int, float] = {}
        self.feature_log_prob_: dict[int, NDArray] = {}
        self.classes_: NDArray | None = None

    def fit(self, X: NDArray, y: NDArray) -> "NaiveBayes":
        """
        X: (N, vocab_size) の単語カウント行列
        y: (N,) のクラスラベル
        """
        self.classes_ = np.unique(y)
        N = len(y)

        for c in self.classes_:
            X_c = X[y == c]
            # クラス事前確率（対数）
            self.class_log_prior_[c] = np.log(len(X_c) / N)
            # 単語の条件付き確率（ラプラス平滑化 + 対数）
            counts = X_c.sum(axis=0) + self.alpha
            self.feature_log_prob_[c] = np.log(counts / counts.sum())

        return self

    def predict_log_proba(self, X: NDArray) -> NDArray:
        """各クラスの対数事後確率を返す"""
        log_probs = np.column_stack([
            self.class_log_prior_[c] + X @ self.feature_log_prob_[c]
            for c in self.classes_
        ])
        return log_probs

    def predict(self, X: NDArray) -> NDArray:
        return self.classes_[np.argmax(self.predict_log_proba(X), axis=1)]

    def score(self, X: NDArray, y: NDArray) -> float:
        return np.mean(self.predict(X) == y)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト & デモ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_linear_regression() -> None:
    print("\n" + "═" * 60)
    print("📐 1. 線形回帰")
    print("─" * 60)

    rng = np.random.default_rng(42)
    # y = 3x1 + 2x2 + 1 + noise
    X = rng.normal(0, 1, (200, 2))
    y = 3 * X[:, 0] + 2 * X[:, 1] + 1 + rng.normal(0, 0.5, 200)

    X_train, X_test = X[:160], X[160:]
    y_train, y_test = y[:160], y[160:]

    for method in ["normal_equation", "gradient_descent"]:
        model = LinearRegression(learning_rate=0.1, n_iterations=1000, method=method)
        model.fit(X_train, y_train)
        r2 = model.score(X_test, y_test)
        print(f"  {method:25s}: R²={r2:.4f}, θ≈{model.theta.round(2)}")

    print("  ← θ = [切片≈1, 係数1≈3, 係数2≈2] が復元できているか確認")

    # sklearn との比較
    from sklearn.linear_model import LinearRegression as SkLearnLR
    sk_model = SkLearnLR().fit(X_train, y_train)
    print(f"  sklearn (参考):          R²={sk_model.score(X_test, y_test):.4f}")


def test_logistic_regression() -> None:
    print("\n" + "═" * 60)
    print("📊 2. ロジスティック回帰")
    print("─" * 60)

    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=500, n_features=4, random_state=42)
    X_train, X_test = X[:400], X[400:]
    y_train, y_test = y[:400], y[400:]

    # L2 正則化の効果を比較
    for reg in [0.0, 0.01, 0.1]:
        model = LogisticRegression(learning_rate=0.1, n_iterations=500, regularization=reg)
        model.fit(X_train, y_train)
        acc = model.score(X_test, y_test)
        print(f"  正則化 λ={reg:.2f}: 精度={acc:.3f}")

    from sklearn.linear_model import LogisticRegression as SkLR
    sk = SkLR(max_iter=500).fit(X_train, y_train)
    print(f"  sklearn (参考):  精度={sk.score(X_test, y_test):.3f}")


def test_decision_tree() -> None:
    print("\n" + "═" * 60)
    print("🌳 3. 決定木 - 過学習の観察")
    print("─" * 60)

    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=300, n_features=4, random_state=42)
    X_train, X_test = X[:240], X[240:]
    y_train, y_test = y[:240], y[240:]

    print("  max_depth | 訓練精度 | テスト精度 | 過学習ギャップ")
    print("  " + "─" * 48)
    for depth in [1, 2, 3, 5, 10, None]:
        model = DecisionTree(max_depth=depth or 100)
        model.fit(X_train, y_train)
        train_acc = model.score(X_train, y_train)
        test_acc = model.score(X_test, y_test)
        gap = train_acc - test_acc
        print(f"  depth={str(depth):4s}  | {train_acc:.3f}   | {test_acc:.3f}    | {gap:.3f} {'⚠️ 過学習' if gap > 0.1 else ''}")


def test_kmeans() -> None:
    print("\n" + "═" * 60)
    print("🔵 4. K-Means クラスタリング")
    print("─" * 60)

    from sklearn.datasets import make_blobs
    X, y_true = make_blobs(n_samples=300, centers=4, cluster_std=0.8, random_state=42)

    km = KMeans(k=4, init="kmeans++", n_init=5)
    km.fit(X)

    # 純度スコア（クラスターと真のラベルの対応）
    from scipy.stats import mode
    from sklearn.metrics import adjusted_rand_score

    ari = adjusted_rand_score(y_true, km.labels_)
    print(f"  K=4, K-Means++ 初期化")
    print(f"  SSE（慣性）: {km.inertia_:.2f}")
    print(f"  Adjusted Rand Index: {ari:.3f} (1.0が完璧)")

    km.elbow_plot(X, range(1, 7))


def test_pca() -> None:
    print("\n" + "═" * 60)
    print("📉 5. PCA - 次元削減")
    print("─" * 60)

    from sklearn.datasets import load_digits
    digits = load_digits()
    X = digits.data.astype(float)   # (1797, 64) - 8x8ピクセルの手書き数字
    print(f"  元の次元数: {X.shape[1]}次元 (8x8ピクセル)")

    pca = PCA(n_components=20)
    pca.fit(X)
    pca.cumulative_variance_plot()

    X_reduced = pca.transform(X)
    print(f"  圧縮後: {X_reduced.shape[1]}次元")

    # 圧縮 → 復元の誤差
    X_reconstructed = pca.inverse_transform(X_reduced)
    reconstruction_error = np.mean((X - X_reconstructed) ** 2)
    print(f"  再構成誤差 (MSE): {reconstruction_error:.4f}")

    # 圧縮したデータで分類精度はどう変わるか
    from sklearn.linear_model import LogisticRegression as SkLR
    from sklearn.model_selection import cross_val_score

    for n_comp in [10, 20, 40, 64]:
        pca_n = PCA(n_components=n_comp)
        X_n = pca_n.fit_transform(X)
        scores = cross_val_score(SkLR(max_iter=300), X_n, digits.target, cv=3)
        print(f"  {n_comp}次元: 分類精度={scores.mean():.3f}")


def test_naive_bayes() -> None:
    print("\n" + "═" * 60)
    print("📧 6. ナイーブベイズ - テキスト分類")
    print("─" * 60)

    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import CountVectorizer

    # 4カテゴリのみ使用
    categories = ["sci.med", "comp.graphics", "rec.sport.baseball", "talk.politics.misc"]
    train = fetch_20newsgroups(subset="train", categories=categories)
    test = fetch_20newsgroups(subset="test", categories=categories)

    vectorizer = CountVectorizer(max_features=5000, stop_words="english")
    X_train = vectorizer.fit_transform(train.data).toarray()
    X_test = vectorizer.transform(test.data).toarray()
    y_train = train.target
    y_test = test.target

    print(f"  訓練: {X_train.shape[0]}件, テスト: {X_test.shape[0]}件")
    print(f"  語彙数: {X_train.shape[1]:,}")

    for alpha in [0.001, 0.1, 1.0]:
        model = NaiveBayes(alpha=alpha)
        model.fit(X_train, y_train)
        acc = model.score(X_test, y_test)
        print(f"  α={alpha:.3f}: 精度={acc:.3f}")


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   ML from Scratch - アルゴリズムを数学から実装する         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("""
  学習のポイント:
    ・各アルゴリズムの「更新式」を暗記ではなく導出から理解する
    ・sklearn の実装と結果を比較して実装の正しさを確認する
    ・Google面接では「このアルゴリズムをゼロから実装してください」が出る
""")

    test_linear_regression()
    test_logistic_regression()
    test_decision_tree()
    test_kmeans()
    test_pca()
    test_naive_bayes()

    print("\n" + "═" * 60)
    print("✅ 完了！面接で「実装してください」と言われたとき:")
    print("   線形回帰: θ_new = θ - α * (1/N) * X^T(Xθ - y)")
    print("   ロジスティック: θ_new = θ - α * (1/N) * X^T(σ(Xθ) - y)")
    print("   決定木: 情報利得 = H(親) - Σ (|子|/|親|) * H(子)")
    print("   K-Means: 割り当て → 重心更新 → 収束まで繰り返す")
    print("   PCA: 共分散行列の固有値分解（または SVD）")
    print("\n[実装してみよう]")
    print("  1. ランダムフォレストを DecisionTree を使って実装（バギング）")
    print("  2. ミニバッチ SGD で LinearRegression を拡張")
    print("  3. SVM（サポートベクターマシン）のヒンジ損失を実装")


if __name__ == "__main__":
    main()
