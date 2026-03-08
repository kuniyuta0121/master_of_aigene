"""
Phase 7: Apache Airflow DAG - ナレッジ分析パイプライン
=======================================================
学習目標:
  - DAG（有向非巡回グラフ）でデータ処理の依存関係を定義する
  - タスクの成功・失敗・リトライを Airflow が管理する仕組みを理解する
  - ETL（Extract → Transform → Load）の各ステップを分離する

考えてほしい疑問:
  Q1. DAGに「非巡回（Acyclic）」が求められる理由は？（循環するとどうなるか）
  Q2. このパイプラインが毎日0時に実行された場合、タスクが失敗したとき何が起きるか？
  Q3. task_1 >> task_2 と task_1 >> [task_2, task_3] の違いは？（並列実行）
  Q4. なぜ Airflow タスク内でDBの接続情報を直接書かないのか？（Connections機能）

実行方法（ローカル）:
  docker run -p 8080:8080 apache/airflow:2.10.0 standalone
  → http://localhost:8080 でUI確認（admin/admin）
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


# DAGのデフォルト設定
default_args = {
    "owner": "knowledge_ai",
    "depends_on_past": False,     # 前日のタスクが成功でなくても実行する
    "retries": 2,                 # 失敗時に2回リトライ
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["alert@example.com"],
}

dag = DAG(
    dag_id="knowledge_analytics",
    description="ナレッジDBを分析してKPIを計算する日次パイプライン",
    default_args=default_args,
    schedule="0 1 * * *",        # 毎日午前1時に実行（cron形式）
    start_date=datetime(2025, 1, 1),
    catchup=False,               # 過去の未実行分を埋めない
    tags=["analytics", "daily"],
)


# --- タスク定義 ---

def extract_notes(**context) -> None:
    """
    Step 1: PostgreSQL からノートデータを抽出する

    XCom（Cross Communication）でタスク間データを受け渡す。
    [考える] XComは小さいデータ向け。大きいデータはS3/GCSを経由すべき理由は？
    """
    hook = PostgresHook(postgres_conn_id="knowledge_ai_db")  # Airflow Connections で定義
    records = hook.get_records("""
        SELECT
            id,
            title,
            LENGTH(content) AS content_length,
            created_at,
            updated_at
        FROM notes
        WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
        ORDER BY created_at
    """)

    # XCom でデータを次のタスクに渡す
    context["task_instance"].xcom_push(key="notes", value=records)
    print(f"✓ {len(records)} 件のノートを抽出しました")


def calculate_kpis(**context) -> None:
    """
    Step 2: KPIを計算する（Transform）

    今日実装するKPI:
    - 1日あたりのノート作成数
    - 平均コンテンツ長
    - タグ別の記事数分布

    [実装してみよう]
    - ノートの「学習継続日数（Streak）」を計算する
    - 最も使われているタグ TOP10 を集計する
    """
    ti = context["task_instance"]
    notes = ti.xcom_pull(key="notes", task_ids="extract_notes")

    if not notes:
        print("今日作成されたノートはありません")
        return

    kpis = {
        "date": datetime.utcnow().date().isoformat(),
        "notes_created_today": len(notes),
        "avg_content_length": sum(n[2] for n in notes) / len(notes),
        "max_content_length": max(n[2] for n in notes),
    }

    print(f"KPI: {kpis}")
    ti.xcom_push(key="kpis", value=kpis)


def load_to_analytics_db(**context) -> None:
    """
    Step 3: 集計結果をアナリティクス用テーブルに保存する（Load）

    [実装してみよう] BigQuery や Redshift に書き込んで
    Looker StudioやMetabaseでダッシュボードを作る
    """
    ti = context["task_instance"]
    kpis = ti.xcom_pull(key="kpis", task_ids="calculate_kpis")

    if not kpis:
        return

    hook = PostgresHook(postgres_conn_id="knowledge_ai_db")
    hook.run("""
        INSERT INTO daily_kpis (date, notes_created, avg_content_length, max_content_length)
        VALUES (%(date)s, %(notes_created_today)s, %(avg_content_length)s, %(max_content_length)s)
        ON CONFLICT (date) DO UPDATE
        SET notes_created = EXCLUDED.notes_created,
            avg_content_length = EXCLUDED.avg_content_length
    """, parameters=kpis)

    print("✓ KPIをDBに保存しました")


# --- タスクの依存関係（DAG の構造定義） ---

extract_task = PythonOperator(
    task_id="extract_notes",
    python_callable=extract_notes,
    dag=dag,
)

calculate_task = PythonOperator(
    task_id="calculate_kpis",
    python_callable=calculate_kpis,
    dag=dag,
)

load_task = PythonOperator(
    task_id="load_to_analytics_db",
    python_callable=load_to_analytics_db,
    dag=dag,
)

# extract → calculate → load の順に実行
extract_task >> calculate_task >> load_task
