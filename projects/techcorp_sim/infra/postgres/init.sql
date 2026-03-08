-- TechCorp データベース初期化
-- このスキーマ設計にも意図的な問題が含まれている（シナリオ3で発見する）

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role        VARCHAR(20) DEFAULT 'user',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notes (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    content     TEXT NOT NULL,
    view_count  INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
    -- [問題] インデックスがない → created_at での ORDER BY が遅い
    -- [実装してみよう] CREATE INDEX idx_notes_created_at ON notes(created_at DESC);
);

-- [設計問題] タグを別テーブルに正規化せず JSON カラムで持っている
-- メリット: シンプル  デメリット: タグ単位のクエリが遅い（GINインデックスが必要）
ALTER TABLE notes ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';

CREATE TABLE IF NOT EXISTS daily_stats (
    id          SERIAL PRIMARY KEY,
    stat_date   DATE UNIQUE NOT NULL,
    notes_count INTEGER DEFAULT 0,
    users_count INTEGER DEFAULT 0,
    total_views INTEGER DEFAULT 0,
    calculated_at TIMESTAMP DEFAULT NOW()
);

-- サンプルデータ（シミュレーション用）
INSERT INTO users (email, password_hash, role) VALUES
    ('alice@techcorp.com', '$2b$12$placeholder_hash_alice', 'admin'),
    ('bob@techcorp.com',   '$2b$12$placeholder_hash_bob',   'user'),
    ('charlie@techcorp.com','$2b$12$placeholder_hash_charlie','user')
ON CONFLICT DO NOTHING;

-- シミュレーション用の大量データ（N+1問題を体感するため）
INSERT INTO notes (user_id, title, content, tags, view_count)
SELECT
    (ARRAY[1,2,3])[floor(random()*3+1)],
    'Note #' || generate_series,
    repeat('Lorem ipsum dolor sit amet. ', 50),
    ('["tag' || (floor(random()*5+1))::text || '","tag' || (floor(random()*5+1))::text || '"]')::jsonb,
    floor(random()*1000)::int
FROM generate_series(1, 500)
ON CONFLICT DO NOTHING;

-- アナリティクス用テーブル
CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    event_type  VARCHAR(50) NOT NULL,
    user_id     INTEGER,
    note_id     INTEGER,
    metadata    JSONB DEFAULT '{}',
    occurred_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes USING GIN(tags);
