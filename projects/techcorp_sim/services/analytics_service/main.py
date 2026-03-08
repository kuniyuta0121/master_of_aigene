"""
Analytics Service - データパイプライン + 統計API
================================================
[BUG-09] except Exception: pass → エラーをサイレントに握りつぶす
         統計が更新されなくても誰も気づかない
[BUG-10] スケジューラーがなく、手動でエンドポイントを叩かないと集計されない
         修正方法: APScheduler または Airflow で定期実行する
[BUG-11] DB接続をリクエストごとに生成・クローズしていない（接続リーク）
"""

import asyncio
import os
import time
from datetime import date, datetime

import uvicorn
from fastapi import FastAPI, Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./analytics.db")
engine = create_engine(DATABASE_URL)

app = FastAPI(title="Analytics Service")

PIPELINE_RUNS    = Counter("analytics_pipeline_runs_total", "Pipeline runs", ["status"])
PIPELINE_DURATION = Gauge("analytics_pipeline_duration_seconds", "Last pipeline duration")
STATS_NOTES_COUNT = Gauge("analytics_notes_total", "Total notes count")


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics_service"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/pipeline/run")
def run_pipeline():
    """
    データ集計パイプラインを手動実行する。

    ★ [BUG-09] エラーをサイレントに握りつぶしている ★
    本番でこれが起きると:
    - 統計ダッシュボードが古いデータを表示し続ける
    - 誰も気づかない（アラートがない）
    - PMが間違ったデータで意思決定する
    """
    start = time.time()
    db = engine.connect()  # [BUG-11] 接続がリークする（context managerを使うべき）
    try:
        # Step 1: ノート統計の集計
        stats = db.execute(text("""
            SELECT
                COUNT(*) as total_notes,
                SUM(view_count) as total_views,
                COUNT(DISTINCT user_id) as active_users
            FROM notes
        """)).fetchone()

        # Step 2: 日次統計テーブルへのupsert
        db.execute(text("""
            INSERT INTO daily_stats (stat_date, notes_count, total_views, calculated_at)
            VALUES (:date, :notes, :views, NOW())
            ON CONFLICT (stat_date)
            DO UPDATE SET
                notes_count = EXCLUDED.notes_count,
                total_views = EXCLUDED.total_views,
                calculated_at = NOW()
        """), {
            "date": date.today().isoformat(),
            "notes": stats.total_notes,
            "views": stats.total_views or 0,
        })
        db.commit()

        duration = time.time() - start
        PIPELINE_RUNS.labels("success").inc()
        PIPELINE_DURATION.set(duration)
        STATS_NOTES_COUNT.set(stats.total_notes)

        return {
            "status": "success",
            "duration_seconds": round(duration, 3),
            "stats": {"total_notes": stats.total_notes, "total_views": stats.total_views},
        }

    except Exception:
        # ★ [BUG-09] ここが問題！ エラーを完全に無視している ★
        # 修正方法:
        #   except Exception as e:
        #       PIPELINE_RUNS.labels("failure").inc()
        #       logger.error("Pipeline failed", exc_info=True)
        #       raise HTTPException(status_code=500, detail=str(e))
        pass
    finally:
        db.close()


@app.get("/stats/daily")
def daily_stats(days: int = 30):
    """過去N日間の日次統計を返す"""
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT stat_date, notes_count, total_views, calculated_at
            FROM daily_stats
            ORDER BY stat_date DESC
            LIMIT :days
        """), {"days": days}).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


@app.get("/stats/summary")
def summary_stats():
    """現在の集計サマリーを返す"""
    with engine.connect() as db:
        result = db.execute(text("""
            SELECT
                COUNT(*) as total_notes,
                SUM(view_count) as total_views,
                AVG(view_count)::float as avg_views_per_note,
                MAX(created_at) as latest_note_at
            FROM notes
        """)).fetchone()
    return dict(result._mapping)


@app.get("/stats/trending")
def trending_notes(limit: int = 10):
    """閲覧数上位ノートのランキング"""
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT id, title, view_count, created_at
            FROM notes
            ORDER BY view_count DESC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
    return {"items": [dict(r._mapping) for r in rows]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003)
