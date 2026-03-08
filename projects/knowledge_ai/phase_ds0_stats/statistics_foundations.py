"""
phase_ds0_stats/statistics_foundations.py
========================================
統計・確率の基礎 - データサイエンティストの数学的土台

なぜこれが必要か:
  ML の面接では「このモデルの前提条件は何か？」
  「A/Bテストで何サンプル必要か？」
  「p値が0.05以下なら必ず正しいか？」が必ず聞かれる。
  数学的根拠なく ML を使っても、Google/IBM では通用しない。

このフェーズで学ぶこと:
  - 確率の基礎（条件付き確率・ベイズの定理）
  - 統計的推定（点推定・区間推定）
  - 仮説検定（p値・検出力・第一種/第二種誤り）
  - A/Bテストの正しい設計
  - 因果推論入門（相関と因果の違い）
  - 情報理論（エントロピー・KL divergence）

実行方法:
  pip install scipy numpy pandas
  python statistics_foundations.py

考えてほしい疑問:
  Q1. 「p値 < 0.05」だから効果があると言えるか？（多重検定問題）
  Q2. サンプルサイズを2倍にすると信頼区間の幅はどうなるか？（√2倍に縮む）
  Q3. 相関係数 0.9 の2変数は因果関係があるか？（アイスクリームと溺死者数）
  Q4. ベイズ推定と頻度主義の違いは何か？（事前分布の使い方）
  Q5. 決定木でエントロピーを最小化する理由は？
"""

import math
from dataclasses import dataclass

import numpy as np
from scipy import stats


# ─── 1. 確率の基礎 ──────────────────────────────────────────

def probability_fundamentals() -> None:
    """
    ベイズの定理 - ML理解の核心

    P(A|B) = P(B|A) * P(A) / P(B)

    実例: スパムフィルター
      P(スパム|"無料") = P("無料"|スパム) * P(スパム) / P("無料")
    """
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   Phase DS0: 統計・確率 基礎                          ║")
    print("╚═══════════════════════════════════════════════════════╝")

    print("\n📐 1. ベイズの定理")
    print("─" * 60)

    # 例: がん検診
    # 事前確率
    p_cancer = 0.001         # 人口の0.1%がこのがんを持つ
    p_positive_given_cancer = 0.99   # 感度（真陽性率）
    p_positive_given_no_cancer = 0.05  # 偽陽性率

    # P(陽性) = P(陽性|がん)*P(がん) + P(陽性|がんでない)*P(がんでない)
    p_positive = (p_positive_given_cancer * p_cancer +
                  p_positive_given_no_cancer * (1 - p_cancer))

    # P(がん|陽性) = ベイズ更新
    p_cancer_given_positive = (p_positive_given_cancer * p_cancer) / p_positive

    print(f"""
  [がん検診の例]
  事前確率: がんである確率 = {p_cancer:.1%}
  感度（陽性の場合、本当にがん）: {p_positive_given_cancer:.0%}
  偽陽性率: {p_positive_given_no_cancer:.0%}

  → 検査結果が「陽性」だったとき、本当にがんである確率は?
  答え: {p_cancer_given_positive:.1%}

  ← これが直感に反するのは「事前確率が低い」から
  ← 多くの人が「陽性なら99%がんだ」と誤解する（ベースレートの無視）

  ML への応用: ナイーブベイズ分類器はこの更新を繰り返す
  P(クラス|特徴量) ∝ P(特徴量|クラス) * P(クラス)
""")


# ─── 2. 統計的推定 ──────────────────────────────────────────

def statistical_estimation() -> None:
    print("\n📊 2. 統計的推定 - 信頼区間")
    print("─" * 60)

    # 例: 新機能のCTR（クリック率）を推定
    np.random.seed(42)
    n_users = 1000
    true_ctr = 0.12  # 真のCTR（実際には未知）

    # シミュレーション
    clicks = np.random.binomial(1, true_ctr, n_users)
    observed_ctr = clicks.mean()

    # 95% 信頼区間（Wilson区間 - 比率に対して正確）
    from scipy.stats import binom
    ci_low, ci_high = binom.interval(0.95, n_users, observed_ctr)
    ci_low /= n_users
    ci_high /= n_users

    print(f"""
  [新機能のCTR推定例]
  サンプルサイズ: {n_users:,} ユーザー
  真のCTR（未知）: {true_ctr:.1%}
  観測されたCTR: {observed_ctr:.1%}
  95%信頼区間: [{ci_low:.1%}, {ci_high:.1%}]

  解釈:
    「同じ実験を100回繰り返すと、95回はこの区間に真値が入る」
    ※「95%の確率で真値がこの区間内にある」は誤解（頻度主義では）

  サンプルサイズと精度の関係:
""")

    # サンプルサイズ vs 信頼区間の幅
    for n in [100, 1000, 10000, 100000]:
        ci = 2 * 1.96 * math.sqrt(true_ctr * (1 - true_ctr) / n)
        print(f"    n={n:>7,}: ±{ci:.1%} (区間幅 {ci*2:.1%})")

    print("""
  直感: サンプルを4倍にすると精度が2倍（√n に比例）
  テックリードとしての判断:
    「精度を1/10にするには100倍のサンプルが必要」
    → A/Bテストの期間設計で重要
""")


# ─── 3. 仮説検定 ──────────────────────────────────────────

@dataclass
class ABTestResult:
    p_value: float
    is_significant: bool
    effect_size: float
    required_sample_size: int
    observed_power: float


def hypothesis_testing() -> None:
    print("\n🔬 3. 仮説検定 & A/Bテスト設計")
    print("─" * 60)

    # シナリオ: 新UIのCTRが上がったか？
    np.random.seed(42)
    n_control = 5000
    n_treatment = 5000
    ctr_control = 0.10    # コントロール群: 10%
    ctr_treatment = 0.108  # 処理群: 10.8%（0.8%ポイントの改善）

    control = np.random.binomial(1, ctr_control, n_control)
    treatment = np.random.binomial(1, ctr_treatment, n_treatment)

    # t検定（比率の検定）
    t_stat, p_value = stats.ttest_ind(control, treatment)

    # 効果量（Cohen's d）
    pooled_std = math.sqrt((control.std()**2 + treatment.std()**2) / 2)
    cohens_d = (treatment.mean() - control.mean()) / pooled_std

    # 必要サンプルサイズ計算（検出力80%、α=0.05）
    from statsmodels.stats.power import TTestIndPower
    try:
        analysis = TTestIndPower()
        required_n = analysis.solve_power(
            effect_size=abs(cohens_d),
            alpha=0.05,
            power=0.80,
        )
    except Exception:
        required_n = int(16 / cohens_d**2)  # 近似計算

    result = ABTestResult(
        p_value=p_value,
        is_significant=p_value < 0.05,
        effect_size=cohens_d,
        required_sample_size=int(required_n),
        observed_power=0.0,
    )

    print(f"""
  [A/Bテスト例: 新UI vs 旧UI]
  コントロール群: CTR = {control.mean():.1%} (n={n_control:,})
  処理群:         CTR = {treatment.mean():.1%} (n={n_treatment:,})
  差分:           +{(treatment.mean()-control.mean()):.1%}ポイント

  統計検定結果:
    p値: {result.p_value:.4f} {'← 有意 (p < 0.05)' if result.is_significant else '← 非有意 (p >= 0.05)'}
    Cohen's d: {result.effect_size:.4f} ({'small' if abs(result.effect_size)<0.2 else 'medium' if abs(result.effect_size)<0.5 else 'large'})
    80%検出力に必要なサンプル数/群: {result.required_sample_size:,}

  ⚠️  p値の正しい解釈:
    p={result.p_value:.4f} の意味:
    「帰無仮説（差がない）が正しいとき、
     この程度以上の差が偶然起きる確率が {result.p_value:.1%}」

  よくある誤解:
    ❌ 「p < 0.05 なので効果がある」 → 実用的意義≠統計的有意性
    ❌ 「p > 0.05 なので効果がない」 → 非有意は「効果なし」の証明ではない
    ❌ 多重検定（10個テストして1個だけ有意） → Bonferroni補正が必要
""")

    print("  多重検定問題のシミュレーション:")
    rng = np.random.default_rng(42)
    false_positives = sum(
        stats.ttest_ind(rng.normal(0, 1, 100), rng.normal(0, 1, 100)).pvalue < 0.05
        for _ in range(1000)
    )
    print(f"    1000回独立なテストで帰無仮説が真のとき")
    print(f"    p < 0.05 になった回数: {false_positives}/1000 ({false_positives/10:.1f}%)")
    print(f"    → 約5%は「偶然有意」になる（第一種誤り α = 0.05）")


# ─── 4. 因果推論 ──────────────────────────────────────────

def causal_inference_intro() -> None:
    print("\n🔗 4. 因果推論 - 相関と因果の違い")
    print("─" * 60)
    print("""
  最も重要な概念: 相関 ≠ 因果

  古典的な例:
    「アイスクリームの売上」と「溺死者数」の相関係数 ≈ 0.9
    → 原因は「気温（交絡変数）」
    → アイスクリームを売るのをやめても溺死者は減らない

  ML への影響:
    ・モデルが高精度でも因果構造が間違っていれば介入に使えない
    ・特徴量に交絡変数が含まれると「公平でないモデル」になる

  因果推論のツールキット:
  ┌─────────────────────────────────────────────────────┐
  │ 手法               │ 使いどころ                     │
  ├─────────────────────────────────────────────────────│
  │ A/Bテスト（RCT）   │ ランダム化できるとき（最強）   │
  │ 差分の差分（DiD）   │ 施策前後を比較できるとき       │
  │ 操作変数法（IV）    │ ランダム化できないとき         │
  │ 回帰不連続（RDD）   │ 閾値で処置が決まるとき         │
  │ 傾向スコアマッチング│ 観察研究で交絡を制御           │
  └─────────────────────────────────────────────────────┘

  Googleの使い方:
    「クリック率が上がった」← モデルのせい? ユーザーの変化?
    → 差分の差分で「モデル変更の純粋な効果」を推定

  PMとしての判断:
    「相関があるからこの機能を作ろう」は危険
    「介入実験を設計して因果を確認してから投資判断する」が正解

  [実装してみよう]
    pip install causalml econml
    実際の傾向スコアマッチングを試す
""")


# ─── 5. 情報理論 ──────────────────────────────────────────

def information_theory() -> None:
    print("\n📡 5. 情報理論 - エントロピーとKL divergence")
    print("─" * 60)

    def entropy(probs: list[float]) -> float:
        """Shannon エントロピー: 不確実性の度合い"""
        return -sum(p * math.log2(p) for p in probs if p > 0)

    def kl_divergence(p: list[float], q: list[float]) -> float:
        """KL divergence: 2分布の「ズレ」を測る"""
        return sum(pi * math.log(pi / qi) for pi, qi in zip(p, q) if pi > 0 and qi > 0)

    print("""
  エントロピー = 情報量 = 不確実性

  コインの例:
""")
    scenarios = [
        ("完全に公平なコイン", [0.5, 0.5]),
        ("少し偏ったコイン", [0.7, 0.3]),
        ("完全に偏ったコイン", [1.0, 0.0]),
    ]
    for name, probs in scenarios:
        h = entropy(probs)
        bar = "█" * int(h * 20)
        print(f"    {name}: P={probs} H={h:.3f} {bar}")

    print("""
  直感: 予測できないほど情報量が多い（エントロピーが高い）

  ML での使われ方:
    ・決定木: エントロピーを最小化する特徴量で分割
    ・クロスエントロピー損失: 分類モデルの損失関数
    ・KL divergence: VAE、GAN、知識蒸留に使用
""")

    # 決定木のノード分割シミュレーション
    print("  決定木の分割基準（情報利得）の例:")
    print("  「MLノート」か「Infraノート」か → どの特徴量で分割する？")

    parent = [0.5, 0.5]  # 50:50
    split_good = ([0.9, 0.1], [0.1, 0.9])   # よい分割
    split_bad = ([0.6, 0.4], [0.4, 0.6])    # 悪い分割

    ig_good = entropy(parent) - 0.5 * (entropy(split_good[0]) + entropy(split_good[1]))
    ig_bad = entropy(parent) - 0.5 * (entropy(split_bad[0]) + entropy(split_bad[1]))

    print(f"    よい分割の情報利得: {ig_good:.3f}")
    print(f"    悪い分割の情報利得: {ig_bad:.3f}")
    print(f"    → 情報利得が最大の特徴量を選ぶ（決定木の学習原理）")

    # KL divergence の実例
    print("\n  KL divergence (モデル分布 q vs 真の分布 p):")
    p_true = [0.1, 0.4, 0.4, 0.1]  # 真の分布
    q_bad = [0.25, 0.25, 0.25, 0.25]  # 一様分布（悪いモデル）
    q_good = [0.12, 0.38, 0.38, 0.12]  # よいモデル

    print(f"    真の分布 p:  {p_true}")
    print(f"    一様分布 q:  KL(p||q) = {kl_divergence(p_true, q_bad):.3f}")
    print(f"    よいモデル q: KL(p||q) = {kl_divergence(p_true, q_good):.3f}")
    print(f"    → KL = 0 は p と q が同一分布（完璧なモデル）")


# ─── 6. 統計的機械学習との接続 ─────────────────────────────

def ml_statistics_connection() -> None:
    print("\n🔌 6. 統計学と機械学習の接続")
    print("─" * 60)
    print("""
  統計学の概念  ←→  機械学習の概念
  ─────────────────────────────────────────────────────
  最尤推定 (MLE)     → 損失関数の最小化
  事後確率最大化     → 正則化 (L2 = ガウス事前分布)
  ガウス混合モデル   → クラスタリング (k-means の確率版)
  線形回帰           → 最小二乗法 = ガウスノイズ仮定の MLE
  ロジスティック回帰 → 交差エントロピー損失の最小化
  ベイズ更新         → オンライン学習
  中心極限定理       → バッチ正規化の理論的根拠の一部
  信頼区間           → Dropout による不確実性推定
  ─────────────────────────────────────────────────────

  Google面接で実際に聞かれた質問:
    Q: 「正則化とベイズ推定の関係を説明してください」
    A: L2正則化は重みにガウス事前分布を仮定したMAP推定と等価
       L1正則化はラプラス事前分布に対応
       → 正則化を「ベイズの枠組みで理解している」かを確認している

    Q: 「交差エントロピー損失と MSE の違いと使い分けは？」
    A: 分類 → 交差エントロピー（確率的出力に適している）
       回帰 → MSE（連続値、ガウスノイズ仮定）
       → 損失関数の選択は「生成モデルの仮定」を反映している

    Q: 「過学習が起きているか判断するには？」
    A: 訓練誤差と検証誤差のギャップ、バイアス-バリアンストレードオフ、
       学習曲線の傾き → これを「統計的に」説明できるか

  テックリードとしての判断軸:
    「なぜこのモデルが機能するのか、統計的に説明できるか」
    ← ML を「使える」と「理解している」の境界線

  [実装してみよう]
    1. MLE を手動で実装（ガウス分布のパラメータ推定）
    2. Bayesian Linear Regression を PyMC または Stan で実装
    3. scipy.stats を使って検出力曲線をプロットする
""")


def main():
    probability_fundamentals()
    statistical_estimation()
    hypothesis_testing()
    causal_inference_intro()
    information_theory()
    ml_statistics_connection()

    print("\n" + "═" * 60)
    print("✅ 完了！次のステップ:")
    print("  → Phase DS1: ML基礎（統計の知識がモデル選択に活きる）")
    print("  → [実装してみよう] statsmodels でA/Bテストのサンプルサイズを計算する")
    print("  → [読む] 「統計学が最強の学問である」「岩波データサイエンス」")


if __name__ == "__main__":
    main()
