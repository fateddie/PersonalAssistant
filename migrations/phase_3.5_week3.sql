-- Phase 3.5 Week 3: Additional Schema Updates
-- ============================================
-- Run with: sqlite3 assistant/data/memory.db < migrations/phase_3.5_week3.sql

-- Add missing columns to habit_chains
ALTER TABLE habit_chains ADD COLUMN trigger_habit TEXT;
ALTER TABLE habit_chains ADD COLUMN time_of_day TEXT DEFAULT 'morning';
ALTER TABLE habit_chains ADD COLUMN description TEXT;
ALTER TABLE habit_chains ADD COLUMN total_attempts INTEGER DEFAULT 0;

-- Update existing rows to use new column name
UPDATE habit_chains SET trigger_habit = anchor_habit WHERE trigger_habit IS NULL;

-- Add chain_id column to habit_completions if referencing by different name
ALTER TABLE habit_completions ADD COLUMN chain_id INTEGER;
UPDATE habit_completions SET chain_id = habit_chain_id WHERE chain_id IS NULL;

-- Add missing columns to if_then_plans
ALTER TABLE if_then_plans ADD COLUMN if_situation TEXT;
ALTER TABLE if_then_plans ADD COLUMN then_action TEXT;
ALTER TABLE if_then_plans ADD COLUMN category TEXT DEFAULT 'general';
ALTER TABLE if_then_plans ADD COLUMN related_goal_id TEXT;
ALTER TABLE if_then_plans ADD COLUMN times_successful INTEGER DEFAULT 0;

-- Update existing rows
UPDATE if_then_plans SET if_situation = trigger_situation WHERE if_situation IS NULL;
UPDATE if_then_plans SET then_action = planned_action WHERE then_action IS NULL;

-- Update thought_logs for brain dump functionality
ALTER TABLE thought_logs ADD COLUMN content TEXT;
ALTER TABLE thought_logs ADD COLUMN captured_at TIMESTAMP;
ALTER TABLE thought_logs ADD COLUMN processed INTEGER DEFAULT 0;
ALTER TABLE thought_logs ADD COLUMN processed_at TIMESTAMP;
ALTER TABLE thought_logs ADD COLUMN action_taken TEXT;
ALTER TABLE thought_logs ADD COLUMN source TEXT DEFAULT 'manual';

-- Copy situation to content for existing records
UPDATE thought_logs SET content = situation WHERE content IS NULL AND situation IS NOT NULL;

-- Weekly reviews table
CREATE TABLE IF NOT EXISTS weekly_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    wins TEXT,  -- JSON array
    lessons TEXT,  -- JSON array
    next_week_focus TEXT,
    obstacles_anticipated TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(week_start)
);

CREATE INDEX IF NOT EXISTS idx_weekly_reviews_week ON weekly_reviews(week_start);

-- Seed weekly review streak
INSERT OR IGNORE INTO streaks (activity) VALUES ('Weekly Review');

SELECT 'Phase 3.5 Week 3 migration complete.' AS status;
