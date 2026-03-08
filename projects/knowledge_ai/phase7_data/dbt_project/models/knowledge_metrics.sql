-- Phase 7: dbt モデル - ナレッジメトリクス
-- ============================================
-- dbt はSQLをモジュール化・テスト可能にするツール。
-- このファイルが「1つのモデル（テーブル/ビュー）」を表す。
--
-- 考えてほしい疑問:
--   Q1. dbt の ref() 関数はなぜ直接テーブル名を書くより良いのか？
--   Q2. このモデルを materialized='view' から 'table' に変えるとどう変わるか？
--   Q3. dbt test でどんなテストができるか？（unique, not_null, relationships）
--
-- 実行方法:
--   dbt run --models knowledge_metrics
--   dbt test --models knowledge_metrics

{{ config(
    materialized='table',   -- テーブルとして物化（毎回再計算）
    tags=['daily', 'metrics']
) }}

WITH note_stats AS (
    -- ノートの基本統計
    SELECT
        DATE(created_at)                   AS created_date,
        COUNT(*)                           AS notes_count,
        AVG(LENGTH(content))               AS avg_content_length,
        COUNT(DISTINCT source_url) FILTER (WHERE source_url IS NOT NULL)
                                           AS notes_with_source_count
    FROM {{ ref('stg_notes') }}   -- staging モデルを参照（直接テーブル名を書かない）
    GROUP BY DATE(created_at)
),

tag_stats AS (
    -- タグの使用状況
    SELECT
        t.name                             AS tag_name,
        COUNT(nt.note_id)                  AS usage_count,
        COUNT(nt.note_id) * 100.0 / SUM(COUNT(nt.note_id)) OVER ()
                                           AS usage_percentage
    FROM {{ ref('stg_tags') }} t
    LEFT JOIN {{ ref('stg_note_tags') }} nt ON t.id = nt.tag_id
    GROUP BY t.name
),

cumulative AS (
    -- 累積ノート数（成長トレンド）
    SELECT
        created_date,
        notes_count,
        SUM(notes_count) OVER (ORDER BY created_date) AS cumulative_notes
    FROM note_stats
)

-- 最終モデル：日次サマリー
SELECT
    ns.created_date,
    ns.notes_count,
    ns.avg_content_length,
    ns.notes_with_source_count,
    cu.cumulative_notes,
    -- 前日比（ウィンドウ関数）
    ns.notes_count - LAG(ns.notes_count) OVER (ORDER BY ns.created_date)
                                           AS notes_count_delta
FROM note_stats ns
JOIN cumulative cu ON ns.created_date = cu.created_date
ORDER BY ns.created_date DESC
