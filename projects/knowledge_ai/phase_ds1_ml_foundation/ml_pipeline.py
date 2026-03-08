"""
phase_ds1_ml_foundation/ml_pipeline.py
========================================
機械学習パイプライン - ノート自動タグ分類 & 品質予測

このフェーズで学ぶこと:
  - 特徴量エンジニアリング（テキスト → 数値）
  - 分類問題（タグ自動付与）
  - 回帰問題（閲覧数予測）
  - アンサンブル学習（Random Forest, Gradient Boosting, Voting）
  - モデル評価（交差検証, 混同行列, 特徴量重要度）

実行方法:
  pip install scikit-learn pandas numpy matplotlib seaborn
  python ml_pipeline.py

考えてほしい疑問:
  Q1. なぜ文字列のタグを直接モデルに渡せないのか？（特徴量エンジニアリングの必要性）
  Q2. 訓練精度が高くてもテスト精度が低い理由は？（過学習とは何か）
  Q3. Random Forest と Gradient Boosting の違いは何か？（並列 vs 逐次）
  Q4. データ量が少ないとき、どんな問題が起きるか？（バイアス-バリアンストレードオフ）
  Q5. クラスが不均衡なとき（タグAが1000件、タグBが10件）何が起きるか？
"""

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    r2_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ─── データ生成 ──────────────────────────────────────────────
# 実際はDBから取得するが、ここでは学習用の合成データを使う

SAMPLE_NOTES = [
    # (title, content, tag, view_count)
    ("Pythonの型ヒント完全ガイド", "TypedDictやProtocolを使った型安全なコードの書き方", "Python", 320),
    ("FastAPI入門", "Pydanticとの統合、非同期処理、依存性注入の仕組み", "Python", 280),
    ("scikit-learnで始める機械学習", "分類・回帰・クラスタリングの基礎から実践まで", "ML", 510),
    ("Random Forestの仕組みを理解する", "決定木のアンサンブルとバギングの直感的な説明", "ML", 430),
    ("勾配ブースティング徹底解説", "XGBoost, LightGBM, CatBoostの違いと使い分け", "ML", 490),
    ("Docker Composeで開発環境を構築", "マルチコンテナ構成とネットワーク設定", "Infra", 250),
    ("KubernetesのPodとDeployment", "コンテナオーケストレーションの基本概念", "Infra", 220),
    ("PostgreSQLのインデックス最適化", "B-treeとGINインデックスの使い分け方", "DB", 380),
    ("SQLのウィンドウ関数", "OVER句、PARTITION BY、ROW_NUMBERの実践例", "DB", 340),
    ("Transformerアーキテクチャ解説", "Self-AttentionとMulti-Head Attentionの数学的理解", "DL", 620),
    ("PyTorchで実装するCNN", "画像分類をゼロから実装する", "DL", 580),
    ("LSTMと時系列予測", "時系列データの前処理とモデル設計", "DL", 540),
    ("Terraformでインフラをコード化", "AWS VPCとECSのプロビジョニング", "Infra", 200),
    ("GitHubActionsでCI/CDパイプライン", "自動テストとECRへのデプロイ", "Infra", 260),
    ("Prometheusでメトリクス収集", "カスタムメトリクスとアラートルールの設定", "Infra", 180),
    ("特徴量エンジニアリングの技法", "カテゴリ変数の処理、欠損値対策、スケーリング", "ML", 460),
    ("交差検証と過学習対策", "K-Fold CVとハイパーパラメータチューニング", "ML", 400),
    ("ニューラルネットワークの最適化", "Adam, SGD, 学習率スケジューリングの比較", "DL", 560),
    ("Goの並行処理パターン", "goroutine、channel、sync.WaitGroupの使い方", "Go", 300),
    ("Go言語でHTTPサーバー", "net/httpとchi routerによるREST API実装", "Go", 270),
    ("JWTとOAuth2の仕組み", "認証フローとトークン検証の実装", "Security", 350),
    ("SQLインジェクション対策", "プレースホルダーとORMの使い方", "Security", 320),
    ("データパイプラインの設計", "Airflow DAGとdbtによるETL構築", "Data", 290),
    ("dbtでデータ変換", "CTEとウィンドウ関数を使ったモデル設計", "Data", 260),
    ("Next.jsのServer Components", "クライアントとサーバーの境界を理解する", "Frontend", 310),
    ("React HooksとState管理", "useState、useReducer、Context APIの使い分け", "Frontend", 280),
    ("OKR設計の実践", "テックリードとしての目標設定と計測", "PM", 240),
    ("アジャイル開発とスクラム", "スプリントプランニングとベロシティ計測", "PM", 210),
    ("ベクターデータベースの選択", "Pinecone, ChromaDB, pgvectorの比較", "ML", 520),
    ("RAGシステムの設計", "Retrieval精度とGeneration品質のバランス", "ML", 480),
]

# 追加データ（各クラスのサンプルを増やす）
EXTENDED_NOTES = SAMPLE_NOTES * 4  # 120サンプルに拡張


@dataclass
class ModelResult:
    """モデル評価結果を格納するデータクラス"""
    model_name: str
    cv_scores: list[float]
    test_accuracy: float
    classification_report_str: str
    confusion_mat: np.ndarray
    feature_importance: Optional[dict] = field(default=None)


# ─── 特徴量エンジニアリング ─────────────────────────────────

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    テキストデータから特徴量を作成する

    考えてほしい疑問:
      - なぜ title と content を別々に扱うか？（重み付けの違い）
      - TF-IDF とは何か？（単語の出現頻度と希少性）
    """
    df = df.copy()

    # テキスト特徴量（統計的）
    df["title_len"] = df["title"].str.len()
    df["content_len"] = df["content"].str.len()
    df["word_count"] = df["content"].str.split().str.len()

    # ノイズを加えて現実的なデータに
    rng = np.random.default_rng(42)
    df["view_count"] = df["view_count"] + rng.integers(-30, 30, size=len(df))
    df["view_count"] = df["view_count"].clip(lower=10)

    # 結合テキスト（TF-IDF 用）
    df["full_text"] = df["title"] + " " + df["content"]

    return df


# ─── 分類タスク: タグ自動付与 ─────────────────────────────────

def train_tag_classifier(df: pd.DataFrame) -> dict[str, ModelResult]:
    """
    ノートのタイトル+本文からタグを予測する多クラス分類器

    [実装してみよう]
      1. TfidfVectorizer のパラメータ（max_features, ngram_range）を変えて精度の変化を確認
      2. ストップワードを追加して不要な単語を除外
      3. LabelEncoder の代わりに OneHotEncoder を使ってみる
    """
    print("\n" + "═" * 60)
    print("📊 タスク1: タグ自動付与 (多クラス分類)")
    print("═" * 60)

    le = LabelEncoder()
    y = le.fit_transform(df["tag"])
    print(f"クラス数: {len(le.classes_)} → {list(le.classes_)}")

    X_text = df["full_text"]
    X_train, X_test, y_train, y_test = train_test_split(
        X_text, y, test_size=0.2, random_state=42, stratify=y
    )

    # ─── 3つのモデルを比較 ───────────────────────────────────
    models = {
        "Logistic Regression": Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000, C=1.0)),
        ]),
        "Random Forest": Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]),
        "Gradient Boosting": Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", GradientBoostingClassifier(n_estimators=100, random_state=42)),
        ]),
    }

    results = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, pipeline in models.items():
        # 交差検証でモデルを評価（テストデータを使わない）
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="accuracy")

        # テストデータで最終評価
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        report = classification_report(y_test, y_pred, target_names=le.classes_)
        cm = confusion_matrix(y_test, y_pred)

        result = ModelResult(
            model_name=name,
            cv_scores=cv_scores.tolist(),
            test_accuracy=float((y_pred == y_test).mean()),
            classification_report_str=report,
            confusion_mat=cm,
        )
        results[name] = result

        print(f"\n▶ {name}")
        print(f"  CV精度 (5-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        print(f"  テスト精度:      {result.test_accuracy:.3f}")

    # ─── アンサンブル (Voting Classifier) ───────────────────
    print("\n▶ Ensemble (Voting - 3モデルの多数決)")
    # [実装してみよう] soft voting (確率の平均) に変更してみる
    # hint: voting="soft" にするとより精度が上がることが多い
    voting_clf = VotingClassifier(
        estimators=[
            ("lr", models["Logistic Regression"]),
            ("rf", models["Random Forest"]),
            ("gb", models["Gradient Boosting"]),
        ],
        voting="hard",
    )
    cv_scores = cross_val_score(voting_clf, X_train, y_train, cv=cv, scoring="accuracy")
    voting_clf.fit(X_train, y_train)
    y_pred = voting_clf.predict(X_test)

    print(f"  CV精度 (5-fold): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"  テスト精度:      {(y_pred == y_test).mean():.3f}")

    # ─── 予測デモ ────────────────────────────────────────────
    best_model = models["Random Forest"]
    print("\n🔮 予測デモ（未知のノート）:")
    demo_texts = [
        "PyTorchでResNetを実装する 画像認識タスクで転移学習を活用",
        "AWSのVPCとサブネット設計 パブリックとプライベートの分離",
        "A/Bテストの統計的有意性 p値と検出力の正しい解釈",
    ]
    for text in demo_texts:
        pred_label = le.inverse_transform(best_model.predict([text]))[0]
        proba = best_model.predict_proba([text])[0]
        top_idx = proba.argsort()[-2:][::-1]
        top_labels = [(le.classes_[i], proba[i]) for i in top_idx]
        print(f"  「{text[:30]}...」")
        print(f"   → 予測: {pred_label} ({top_labels[0][1]:.1%}) | 2位: {top_labels[1][0]} ({top_labels[1][1]:.1%})")

    return results


# ─── 回帰タスク: 閲覧数予測 ─────────────────────────────────

def train_view_predictor(df: pd.DataFrame) -> None:
    """
    ノートの特徴量から閲覧数を予測する回帰モデル

    考えてほしい疑問:
      Q1. MAE と RMSE の違いは何か？どちらを使うべきか？
      Q2. R²スコアが負になることはあるか？（ある。何を意味するか？）
      Q3. 閲覧数は右に偏ったロングテール分布になりやすい → どう対処するか？
    """
    print("\n" + "═" * 60)
    print("📊 タスク2: 閲覧数予測 (回帰)")
    print("═" * 60)

    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

    features = ["title_len", "content_len", "word_count"]
    le = LabelEncoder()
    df = df.copy()
    df["tag_encoded"] = le.fit_transform(df["tag"])
    features.append("tag_encoded")

    X = df[features]
    y = df["view_count"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    regressors = {
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
    }

    for name, model in regressors.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        print(f"\n▶ {name}")
        print(f"  MAE: {mae:.1f}回（平均絶対誤差）")
        print(f"  R²:  {r2:.3f}（1.0が完璧な予測）")

        # 特徴量重要度
        importance = dict(zip(features, model.feature_importances_))
        sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        print("  特徴量重要度:")
        for feat, imp in sorted_imp:
            bar = "█" * int(imp * 40)
            print(f"    {feat:15s} {bar} ({imp:.3f})")


# ─── アンサンブル学習の深掘り ────────────────────────────────

def explain_ensemble_methods() -> None:
    """
    アンサンブル学習の3手法を視覚的に比較する

    [実装してみよう]
      1. Bagging: 自分でBootstrap samplingを実装してみる
      2. Boosting: 重み付きサンプリングのロジックを追う
      3. Stacking: 2層のモデルを組み合わせてみる
    """
    print("\n" + "═" * 60)
    print("📚 アンサンブル学習の3手法比較")
    print("═" * 60)

    table = [
        ("手法", "仕組み", "代表アルゴリズム", "特徴"),
        ("Bagging",
         "データをブートストラップサンプリングで\n複数サブセットに分け並列学習",
         "Random Forest",
         "分散を下げる・並列化可能"),
        ("Boosting",
         "前のモデルが間違えたサンプルに\n重みをかけて逐次学習",
         "XGBoost, LightGBM,\nGradient Boosting",
         "バイアスを下げる・直列学習"),
        ("Stacking",
         "複数モデルの予測結果を\nメタモデルの入力にする",
         "StackingClassifier",
         "多様なモデルを組み合わせ可能"),
        ("Voting",
         "複数モデルの予測結果を\n多数決または確率の平均で決定",
         "VotingClassifier",
         "シンプルで理解しやすい"),
    ]

    col_widths = [12, 32, 24, 22]
    sep = "┼".join("─" * (w + 2) for w in col_widths)

    for i, row in enumerate(table):
        if i == 0:
            print("┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐")
        else:
            print("├" + sep + "┤")

        first_lines = [cell.split("\n")[0] for cell in row]
        second_lines = [cell.split("\n")[1] if "\n" in cell else "" for cell in row]

        line1 = "│" + "│".join(f" {s:<{w}} " for s, w in zip(first_lines, col_widths)) + "│"
        print(line1)
        if any(second_lines):
            line2 = "│" + "│".join(f" {s:<{w}} " for s, w in zip(second_lines, col_widths)) + "│"
            print(line2)

    print("└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘")

    print("""
実務でのアドバイス:
  ・まず Gradient Boosting (LightGBM) を試す → 多くの場合で最強
  ・特徴量設計に8割の時間を使う → モデル選択より重要
  ・Kaggle では Stacking が定番 → ただし本番では過学習に注意
  ・ニューラルネットが強いのは「非構造化データ（画像・テキスト・音声）」
    → 表形式データでは依然 GBM 系が強い（2025年現在）
""")


# ─── メイン ──────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   Phase DS1: ML Foundation - ノート分類パイプライン   ║")
    print("╚═══════════════════════════════════════════════════════╝")

    # データ準備
    df = pd.DataFrame(EXTENDED_NOTES, columns=["title", "content", "tag", "view_count"])
    df = create_features(df)

    print(f"\n📦 データセット: {len(df)}件のノート / {df['tag'].nunique()}カテゴリ")
    print(df["tag"].value_counts().to_string())

    # タスク1: 分類
    train_tag_classifier(df)

    # タスク2: 回帰
    train_view_predictor(df)

    # アンサンブル解説
    explain_ensemble_methods()

    print("\n✅ 完了！次のステップ:")
    print("  → Phase DS2: PyTorch で深層学習を実装する")
    print("  → [実装してみよう] XGBoost / LightGBM を pip install して比較する")
    print("  → [実装してみよう] SHAP ライブラリで特徴量の影響を可視化する")


if __name__ == "__main__":
    main()
