-- Phase 3.5: Proactive Discipline System
-- =======================================
-- Database migration for discipline features
-- Run with: sqlite3 assistant/data/memory.db < migrations/phase_3.5_discipline.sql

-- Daily reflections (evening planning + morning fallback)
CREATE TABLE IF NOT EXISTS daily_reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,  -- Date for which this plan applies
    planning_date DATE,  -- When this was planned (usually day before)

    -- Evening reflection (day before)
    what_went_well TEXT,
    what_got_in_way TEXT,
    one_thing_learned TEXT,

    -- Tomorrow's plan
    top_priorities TEXT,  -- JSON: ["Priority 1", "Priority 2", "Priority 3"]
    one_thing_great TEXT,  -- One thing to make tomorrow great

    -- Metadata
    evening_completed INTEGER DEFAULT 0,
    evening_completed_at TIMESTAMP,
    morning_fallback INTEGER DEFAULT 0,  -- 1 if plan created in morning
    completion_rate REAL,  -- % of priorities completed (calculated next day)

    -- Energy tracking (Tier 3)
    energy_am INTEGER CHECK(energy_am BETWEEN 1 AND 5),
    energy_pm INTEGER CHECK(energy_pm BETWEEN 1 AND 5),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_reflections_date ON daily_reflections(date);
CREATE INDEX IF NOT EXISTS idx_daily_reflections_planning_date ON daily_reflections(planning_date);

-- Time blocks (links assistant_items to calendar slots)
CREATE TABLE IF NOT EXISTS time_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,  -- References assistant_items.id
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER NOT NULL,
    calendar_event_id TEXT,  -- Google Calendar event ID
    calendar_synced INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(item_id, start_time)  -- Prevent double-booking same item
);

CREATE INDEX IF NOT EXISTS idx_time_blocks_item ON time_blocks(item_id);
CREATE INDEX IF NOT EXISTS idx_time_blocks_start ON time_blocks(start_time);

-- Habit chains (habit stacking)
CREATE TABLE IF NOT EXISTS habit_chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_habit TEXT NOT NULL,  -- Existing habit (e.g., "Pour morning coffee")
    new_habit TEXT NOT NULL,  -- New habit to stack (e.g., "Review Top 3 priorities")
    sequence_order INTEGER DEFAULT 1,  -- Order in chain
    active INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    last_completed DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_habit_chains_active ON habit_chains(active);

-- Habit completion log (daily tracking)
CREATE TABLE IF NOT EXISTS habit_completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_chain_id INTEGER NOT NULL REFERENCES habit_chains(id) ON DELETE CASCADE,
    completion_date DATE NOT NULL,
    completed INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(habit_chain_id, completion_date)
);

CREATE INDEX IF NOT EXISTS idx_habit_completions_date ON habit_completions(completion_date);

-- Implementation intentions (If-Then planning)
CREATE TABLE IF NOT EXISTS if_then_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_situation TEXT NOT NULL,  -- "If I feel overwhelmed"
    planned_action TEXT NOT NULL,  -- "Break into 3 micro-steps"
    item_id TEXT,  -- Optional link to assistant_items
    active INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_if_then_active ON if_then_plans(active);

-- Pomodoro sessions
CREATE TABLE IF NOT EXISTS pomodoro_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT,  -- References assistant_items.id
    duration_minutes INTEGER DEFAULT 25,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    completed INTEGER DEFAULT 0,
    interruptions INTEGER DEFAULT 0,
    accomplishment_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pomodoro_item ON pomodoro_sessions(item_id);
CREATE INDEX IF NOT EXISTS idx_pomodoro_started ON pomodoro_sessions(started_at);

-- Streaks (any tracked activity)
CREATE TABLE IF NOT EXISTS streaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity TEXT UNIQUE NOT NULL,  -- "Evening Planning", "Morning Coffee -> Review"
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_completed DATE,
    total_completions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_streaks_activity ON streaks(activity);

-- CBT thought logs (thought challenging)
CREATE TABLE IF NOT EXISTS thought_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT,  -- References assistant_items.id
    situation TEXT NOT NULL,
    automatic_thought TEXT NOT NULL,
    cognitive_distortion TEXT,
    evidence_for TEXT,
    evidence_against TEXT,
    reframe TEXT,
    outcome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_thought_logs_item ON thought_logs(item_id);
CREATE INDEX IF NOT EXISTS idx_thought_logs_created ON thought_logs(created_at);

-- Extend assistant_items with Eisenhower quadrant
-- Note: SQLite ALTER TABLE is limited, check if column exists first
-- This is handled in Python code if needed

-- Seed initial streaks for core activities
INSERT OR IGNORE INTO streaks (activity) VALUES ('Evening Planning');
INSERT OR IGNORE INTO streaks (activity) VALUES ('Morning Reflection');
INSERT OR IGNORE INTO streaks (activity) VALUES ('Weekly Review');

-- Done
SELECT 'Phase 3.5 migration complete. Tables created: daily_reflections, time_blocks, habit_chains, habit_completions, if_then_plans, pomodoro_sessions, streaks, thought_logs' AS status;
