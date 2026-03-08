"""
phase_ds3_mlops/mlops_pipeline.py
========================================
MLOps パイプライン - 実験管理・モデル本番化・モニタリング

このフェーズで学ぶこと:
  - 実験管理 (MLflow): ハイパーパラメータ・メトリクス・モデルを追跡
  - モデルバージョン管理: 本番モデルの切り替えとロールバック
  - データドリフト検知: 本番データが学習データと乖離していないか監視
  - モデルのFastAPI化: ML推論をAPIとして提供する
  - A/Bテスト: 新モデルを安全に本番投入する

実行方法:
  pip install mlflow scikit-learn pandas numpy
  python mlops_pipeline.py

  # MLflow UI を起動して実験結果を確認
  mlflow ui  # http://localhost:5000

考えてほしい疑問:
  Q1. なぜ実験管理ツールが必要か？（Jupyter Notebookだけでは何が困るか）
  Q2. モデルのバージョン管理と Git でのコードバージョン管理の違いは？
  Q3. 本番モデルの精度が下がり始めたとき、何が原因として考えられるか？
  Q4. A/Bテストでモデルを入れ替えるとき、何のリスクを考慮すべきか？
  Q5. テックリードとして、DS チームにどんな MLOps インフラを整備すべきか？
"""

import json
import os
import pickle
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

# MLflow はオプション（インストールされていない場合はモック）
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("⚠️  MLflow が未インストール。実験ログはローカルファイルに保存します。")
    print("   pip install mlflow  でフルMLOps体験が可能です。\n")


# ─── データ（Phase DS1 と同じ） ──────────────────────────────
RAW_DATA = [
    ("Pythonの型ヒント完全ガイド TypedDictやProtocol", "Python"),
    ("FastAPI入門 Pydanticとの統合 非同期処理", "Python"),
    ("scikit-learnで始める機械学習 分類 回帰 クラスタリング", "ML"),
    ("Random Forestの仕組み 決定木のアンサンブルとバギング", "ML"),
    ("勾配ブースティング XGBoost LightGBM CatBoostの違い", "ML"),
    ("Docker Composeで開発環境を構築 マルチコンテナ構成", "Infra"),
    ("KubernetesのPodとDeployment コンテナオーケストレーション", "Infra"),
    ("PostgreSQLのインデックス最適化 B-treeとGINインデックス", "DB"),
    ("SQLのウィンドウ関数 OVER句 PARTITION BY ROW_NUMBER", "DB"),
    ("Transformerアーキテクチャ Self-AttentionとMulti-Head", "DL"),
    ("PyTorchで実装するCNN 画像分類をゼロから", "DL"),
    ("JWTとOAuth2の仕組み 認証フローとトークン検証", "Security"),
    ("データパイプライン Airflow DAGとdbt ETL構築", "Data"),
    ("Goの並行処理パターン goroutine channel WaitGroup", "Go"),
    ("Next.jsのServer Components クライアントとサーバーの境界", "Frontend"),
    ("OKR設計の実践 テックリードとしての目標設定", "PM"),
    ("特徴量エンジニアリング カテゴリ変数 欠損値 スケーリング", "ML"),
    ("ベクターデータベース Pinecone ChromaDB pgvectorの比較", "ML"),
    ("RAGシステムの設計 Retrieval精度とGeneration品質", "ML"),
    ("Pythonの非同期処理 asyncio awaitの仕組み", "Python"),
]
DATA = RAW_DATA * 6  # 120サンプル


# ─── 実験管理モジュール ───────────────────────────────────────

@dataclass
class ExperimentResult:
    """1回の実験結果を記録するデータクラス"""
    run_id: str
    model_name: str
    params: dict[str, Any]
    metrics: dict[str, float]
    timestamp: str
    model_path: str = ""


class LocalExperimentTracker:
    """
    MLflow のないローカル環境向け実験トラッカー
    実体は JSON ファイルへの保存

    本番では mlflow.start_run() / mlflow.log_param() / mlflow.log_metric() を使う
    """
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.log_dir = f"./mlruns/{experiment_name}"
        os.makedirs(self.log_dir, exist_ok=True)
        self.runs: list[ExperimentResult] = []

    def log_run(self, model_name: str, params: dict, metrics: dict,
                model: Any = None) -> str:
        run_id = f"run_{len(self.runs):03d}_{datetime.now().strftime('%H%M%S')}"

        # モデルを pickle で保存
        model_path = ""
        if model is not None:
            model_path = f"{self.log_dir}/{run_id}.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)

        result = ExperimentResult(
            run_id=run_id,
            model_name=model_name,
            params=params,
            metrics=metrics,
            timestamp=datetime.now().isoformat(),
            model_path=model_path,
        )
        self.runs.append(result)

        # JSON に保存（実験の再現性を担保）
        log_path = f"{self.log_dir}/{run_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

        return run_id

    def best_run(self, metric: str = "val_accuracy") -> ExperimentResult:
        return max(self.runs, key=lambda r: r.metrics.get(metric, 0))

    def compare(self) -> pd.DataFrame:
        records = []
        for r in self.runs:
            row = {"run_id": r.run_id, "model": r.model_name, **r.metrics, **r.params}
            records.append(row)
        return pd.DataFrame(records)


def run_experiments(tracker, X_train, X_test, y_train, y_test) -> None:
    """
    複数のモデル・ハイパーパラメータの組み合わせを実験する

    実務での考え方:
      - 実験は再現可能でなければならない（乱数シード固定）
      - パラメータとメトリクスは必ずログに残す（"なぜこのモデルにしたか"）
      - 実験 ID とコードの commit hash を紐付けると完璧
    """
    print("\n" + "═" * 60)
    print("🧪 実験管理: ハイパーパラメータ探索")
    print("═" * 60)

    experiments = [
        ("Logistic Regression", {"C": 0.1}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=300)),
            ("clf", LogisticRegression(C=0.1, max_iter=1000)),
        ])),
        ("Logistic Regression", {"C": 1.0}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=300)),
            ("clf", LogisticRegression(C=1.0, max_iter=1000)),
        ])),
        ("Logistic Regression", {"C": 10.0}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=300)),
            ("clf", LogisticRegression(C=10.0, max_iter=1000)),
        ])),
        ("Random Forest", {"n_estimators": 50, "max_depth": 5}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)),
        ])),
        ("Random Forest", {"n_estimators": 100, "max_depth": None}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ])),
        ("Gradient Boosting", {"n_estimators": 100, "lr": 0.1}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)),
        ])),
        ("Gradient Boosting", {"n_estimators": 200, "lr": 0.05}, Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500)),
            ("clf", GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, random_state=42)),
        ])),
    ]

    if MLFLOW_AVAILABLE:
        mlflow.set_experiment(tracker.experiment_name)

    for model_name, params, pipeline in experiments:
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        metrics = {
            "val_accuracy": accuracy_score(y_test, y_pred),
            "val_f1_macro": f1_score(y_test, y_pred, average="macro"),
            "val_precision": precision_score(y_test, y_pred, average="macro"),
            "val_recall": recall_score(y_test, y_pred, average="macro"),
        }

        if MLFLOW_AVAILABLE:
            with mlflow.start_run(run_name=f"{model_name}_{params}"):
                mlflow.log_params(params)
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(pipeline, "model")
                run_id = mlflow.active_run().info.run_id
        else:
            run_id = tracker.log_run(model_name, params, metrics, pipeline)

        print(f"  {run_id[:20]:20s} | {model_name:20s} | acc={metrics['val_accuracy']:.3f} f1={metrics['val_f1_macro']:.3f}")

    # 実験比較テーブル
    if not MLFLOW_AVAILABLE:
        df = tracker.compare()
        print("\n📊 実験比較テーブル:")
        display_cols = ["model", "val_accuracy", "val_f1_macro"]
        available = [c for c in display_cols if c in df.columns]
        print(df[available].sort_values("val_accuracy", ascending=False).to_string(index=False))


# ─── データドリフト検知 ──────────────────────────────────────

def detect_data_drift(train_df: pd.DataFrame, production_df: pd.DataFrame) -> None:
    """
    本番データが学習データと乖離していないかを検知する

    考えてほしい疑問:
      - ドリフトが発生したとき、モデルに何が起きるか？
      - PSI（Population Stability Index）とは何か？
      - ドリフトを検知したら何をすべきか？（モデル再学習 or アラート）

    [実装してみよう]
      evidently ライブラリを使ったより本格的なドリフト検知
      pip install evidently
    """
    print("\n" + "═" * 60)
    print("📡 データドリフト検知")
    print("═" * 60)

    def psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
        """Population Stability Index: 分布の変化を数値化"""
        eps = 1e-8
        expected_perc = np.histogram(expected, bins=buckets)[0] / len(expected) + eps
        actual_perc = np.histogram(actual, bins=buckets, range=(expected.min(), expected.max()))[0] / len(actual) + eps
        return float(np.sum((actual_perc - expected_perc) * np.log(actual_perc / expected_perc)))

    # テキスト長の分布変化を検知
    train_lengths = train_df["text"].str.len().values
    prod_lengths = production_df["text"].str.len().values

    psi_score = psi(train_lengths, prod_lengths)

    print(f"\n  テキスト長の分布:")
    print(f"    学習データ: 平均 {train_lengths.mean():.1f}文字, 中央値 {np.median(train_lengths):.1f}文字")
    print(f"    本番データ: 平均 {prod_lengths.mean():.1f}文字, 中央値 {np.median(prod_lengths):.1f}文字")
    print(f"\n  PSI スコア: {psi_score:.4f}")

    # PSI の解釈
    if psi_score < 0.1:
        status = "✅ 正常（分布変化なし）"
    elif psi_score < 0.2:
        status = "⚠️  軽微な変化（監視継続）"
    else:
        status = "🚨 大きな変化（モデル再学習を検討）"

    print(f"  判定: {status}")
    print(f"""
  PSI 解釈基準:
    < 0.10 : 分布変化なし → 再学習不要
    0.10-0.25: 軽微な変化 → 監視継続
    > 0.25 : 大きな変化 → モデル再学習が必要

  実務では以下も監視する:
    - 予測ラベルの分布変化（コンセプトドリフト）
    - モデルの予測確信度（confidence）の低下
    - 実際の正解率のモニタリング（ラベル収集が可能な場合）
""")


# ─── モデルのAPI化（FastAPI） ─────────────────────────────────

FASTAPI_EXAMPLE = '''
# phase_ds3_mlops/model_server.py
"""
学習済みモデルを FastAPI で提供する
実務ではこれを Docker コンテナ化して ECS/Cloud Run にデプロイする

実行: uvicorn model_server:app --reload
"""
from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import os

app = FastAPI(title="Tag Classifier API")

# モデルをメモリに読み込む（起動時1回だけ）
MODEL_PATH = os.getenv("MODEL_PATH", "best_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    tag: str
    confidence: float
    model_version: str = "v1.0"

@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    # 予測
    proba = model.predict_proba([req.text])[0]
    tag_idx = proba.argmax()
    confidence = float(proba[tag_idx])

    return PredictResponse(
        tag=model.classes_[tag_idx],
        confidence=confidence,
    )

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

# 考えてほしい疑問:
#   Q1. バッチ予測 vs オンライン予測の違いは？（コスト・レイテンシ）
#   Q2. モデルを Blue/Green デプロイするにはどうするか？
#   Q3. 予測ログをどこに保存すべきか？（ドリフト検知のため）
'''


# ─── A/Bテスト設計 ──────────────────────────────────────────

def explain_ab_testing() -> None:
    """
    新モデルを安全に本番投入するための A/B テスト設計

    テックリード・PMとしての判断:
      - いつ A/B テストを終了するか（統計的有意性）
      - ビジネスメトリクスと ML メトリクスの両方を見る
    """
    print("\n" + "═" * 60)
    print("🔬 A/Bテスト設計: モデルの安全な本番投入")
    print("═" * 60)

    print("""
戦略: Canary Release (段階的ロールアウト)

  Day 1:  新モデルに 5% のトラフィックを流す
  Day 3:  問題なければ 20% に拡大
  Day 7:  問題なければ 50% に拡大
  Day 14: 100% 切り替え or ロールバック

見るべきメトリクス:
  ML メトリクス: 予測精度, 信頼度スコア分布
  ビジネスメトリクス: タグ付けの修正率, 検索ヒット率
  インフラメトリクス: レイテンシ, エラー率, CPU使用率

実装イメージ（api_gateway側）:
  import random

  def route_request(user_id: str) -> str:
      # ユーザーIDで安定したハッシュ（同じユーザーは常に同じモデル）
      if hash(user_id) % 100 < CANARY_PERCENTAGE:
          return "model_v2"  # 新モデル
      return "model_v1"      # 現行モデル

テックリードとしての判断軸:
  ✅ 新モデルを投入すべき条件:
     - 精度が統計的有意に改善（p < 0.05）
     - ビジネスメトリクスが改善または横ばい
     - レイテンシが SLO 内（p95 < 200ms 等）

  ❌ ロールバックすべき条件:
     - エラーレートが閾値超過（> 1%）
     - ユーザー不満の急増（サポートチケット）
     - 特定セグメントで精度が大きく劣化
""")


# ─── MLOps 成熟度モデル ──────────────────────────────────────

def explain_mlops_maturity() -> None:
    print("\n" + "═" * 60)
    print("📈 MLOps 成熟度レベル（Google の定義）")
    print("═" * 60)

    levels = [
        ("Level 0", "手動プロセス",
         "Jupyterで実験 → 手動でスクリプト化 → 手動デプロイ\n"
         "多くのスタートアップの初期状態"),
        ("Level 1", "ML パイプライン自動化",
         "データ → 学習 → 評価 → デプロイ が自動化\n"
         "継続的学習（新データで自動再学習）が可能"),
        ("Level 2", "CI/CD パイプライン自動化",
         "コード変更 → 自動テスト → 自動デプロイ → 自動監視\n"
         "モデルのバージョン管理とロールバックが即座に可能"),
    ]

    for level, name, description in levels:
        print(f"\n  {level}: {name}")
        for line in description.split("\n"):
            print(f"    {line}")

    print("""
テックリードとしての現実的なアドバイス:
  多くの会社は Level 0〜1 の間にいる。
  まず Level 1 を目指す: 学習・評価・デプロイの自動化だけでも
  チームの生産性は劇的に向上する。

  優先順位:
    1. 実験の再現性（MLflow, DVC）
    2. モデルの自動テスト（精度のリグレッションテスト）
    3. 本番モニタリング（ドリフト検知）
    4. 継続的学習パイプライン
""")


# ─── メイン ──────────────────────────────────────────────────

def main():
    print("╔═══════════════════════════════════════════════════════╗")
    print("║   Phase DS3: MLOps - 実験管理・本番化・モニタリング   ║")
    print("╚═══════════════════════════════════════════════════════╝")

    # データ準備
    df = pd.DataFrame(DATA, columns=["text", "tag"])
    labels = df["tag"].values
    texts = df["text"].values

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"\n📦 データ: 訓練 {len(X_train)}件 / テスト {len(X_test)}件")

    # ─── 実験管理 ────────────────────────────────
    tracker = LocalExperimentTracker("note_tag_classifier")
    train_df = pd.DataFrame({"text": X_train})
    run_experiments(tracker, X_train, X_test, y_train, y_test)

    # ─── ベストモデルの登録 ───────────────────────
    if not MLFLOW_AVAILABLE:
        best = tracker.best_run()
        print(f"\n🏆 ベストモデル: {best.model_name}")
        print(f"   精度: {best.metrics['val_accuracy']:.3f}")
        print(f"   実験ログ: {best.model_path}")

    # ─── データドリフト検知 ───────────────────────
    # 本番データを模倣（テキストが長くなっているとする）
    production_texts = [t + " 詳細な解説と実装例を含む" for t in X_test]
    prod_df = pd.DataFrame({"text": production_texts})
    train_df_full = pd.DataFrame({"text": X_train})
    detect_data_drift(train_df_full, prod_df)

    # ─── API化の説明 ──────────────────────────────
    print("\n" + "═" * 60)
    print("🚀 モデルのAPI化 (FastAPI)")
    print("─" * 60)
    print(FASTAPI_EXAMPLE)

    # ─── A/Bテスト設計 ───────────────────────────
    explain_ab_testing()

    # ─── MLOps成熟度 ─────────────────────────────
    explain_mlops_maturity()

    # ─── 全体まとめ ──────────────────────────────
    print("═" * 60)
    print("🎯 データサイエンティスト → テックリード/PM への道")
    print("─" * 60)
    print("""
  あなたが今習得したスキルの位置づけ:

  DS1 (ML基礎)     → データを理解し、適切なモデルを選択できる
  DS2 (深層学習)   → NLP・画像等の非構造化データを扱える
  DS3 (MLOps)      → MLプロジェクトを本番で動かし続けられる

  テックリードとしての付加価値:
    ・DS チームと Eng チームの橋渡し
    ・ML システムのアーキテクチャ設計（Phase 1-10 の知識が活きる）
    ・実験コストとビジネス価値のトレードオフ判断

  PMとしての付加価値:
    ・ML プロジェクトの現実的なスコープ設定
    ・「精度 99% 達成まで待つ」vs「精度 85% で今すぐリリース」の判断
    ・A/B テスト設計とビジネスメトリクスの定義

  次のステップ:
    → techcorp_sim のシナリオ3（データパイプライン障害）を解く
    → Kaggle でコンペに参加してフィードバックを得る
    → MLflow UI (http://localhost:5000) で実験を可視化する
""")


if __name__ == "__main__":
    main()
