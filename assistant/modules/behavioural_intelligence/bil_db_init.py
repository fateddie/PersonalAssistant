"""
BIL Database Initialization (Phase 3.5)
=======================================
Auto-creates required tables if they don't exist.
Called on module import.
"""

from sqlalchemy import create_engine, text
from pathlib import Path

DB_PATH = "assistant/data/memory.db"


def init_discipline_tables():
    """Create all Phase 3.5 discipline tables if they don't exist."""
    engine = create_engine(f"sqlite:///{DB_PATH}")

    # Ensure data directory exists
    Path("assistant/data").mkdir(parents=True, exist_ok=True)

    with engine.begin() as conn:
        # Daily reflections
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS daily_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                planning_date DATE,
                what_went_well TEXT,
                what_got_in_way TEXT,
                one_thing_learned TEXT,
                top_priorities TEXT,
                one_thing_great TEXT,
                evening_completed INTEGER DEFAULT 0,
                evening_completed_at TIMESTAMP,
                morning_fallback INTEGER DEFAULT 0,
                completion_rate REAL,
                energy_am INTEGER CHECK(energy_am BETWEEN 1 AND 5),
                energy_pm INTEGER CHECK(energy_pm BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Time blocks
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS time_blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                duration_minutes INTEGER NOT NULL,
                calendar_event_id TEXT,
                calendar_synced INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id, start_time)
            )
        """
            )
        )

        # Habit chains
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS habit_chains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trigger_habit TEXT NOT NULL,
                new_habit TEXT NOT NULL,
                time_of_day TEXT DEFAULT 'morning',
                description TEXT,
                active INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                total_attempts INTEGER DEFAULT 0,
                last_completed DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Habit completions
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                completed INTEGER DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chain_id, completion_date)
            )
        """
            )
        )

        # If-Then plans
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS if_then_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                if_situation TEXT NOT NULL,
                then_action TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                related_goal_id TEXT,
                active INTEGER DEFAULT 1,
                times_used INTEGER DEFAULT 0,
                times_successful INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Thought logs (for brain dump and CBT)
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS thought_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                captured_at TIMESTAMP,
                processed INTEGER DEFAULT 0,
                processed_at TIMESTAMP,
                action_taken TEXT,
                source TEXT DEFAULT 'manual',
                item_id TEXT,
                situation TEXT,
                automatic_thought TEXT,
                cognitive_distortion TEXT,
                evidence_for TEXT,
                evidence_against TEXT,
                reframe TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Pomodoro sessions
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT,
                duration_minutes INTEGER DEFAULT 25,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                completed INTEGER DEFAULT 0,
                interruptions INTEGER DEFAULT 0,
                accomplishment_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Streaks
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity TEXT UNIQUE NOT NULL,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_completed DATE,
                total_completions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Weekly reviews
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS weekly_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start DATE NOT NULL,
                week_end DATE NOT NULL,
                wins TEXT,
                lessons TEXT,
                next_week_focus TEXT,
                obstacles_anticipated TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(week_start)
            )
        """
            )
        )

        # Seed initial streaks
        conn.execute(
            text(
                """
            INSERT OR IGNORE INTO streaks (activity) VALUES ('Evening Planning')
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT OR IGNORE INTO streaks (activity) VALUES ('Morning Reflection')
        """
            )
        )
        conn.execute(
            text(
                """
            INSERT OR IGNORE INTO streaks (activity) VALUES ('Weekly Review')
        """
            )
        )

        # Add quadrant column to assistant_items if it doesn't exist
        try:
            conn.execute(
                text(
                    """
                ALTER TABLE assistant_items ADD COLUMN quadrant TEXT
            """
                )
            )
        except:
            pass  # Column already exists


# Auto-initialize on import
init_discipline_tables()
