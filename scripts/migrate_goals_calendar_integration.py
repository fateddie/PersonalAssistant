#!/usr/bin/env python3
"""
Database Migration: Add Calendar Integration Fields to Goals

Adds fields to support linking goals to recurring Google Calendar events:
- recurring_days: comma-separated days (e.g., "mon,tue,thu,fri")
- calendar_event_template_id: links to recurring calendar series
- session_time_start: start time for calendar events (e.g., "07:30")
- session_time_end: end time for calendar events (e.g., "09:00")

Run: python scripts/migrate_goals_calendar_integration.py
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "assistant" / "data" / "memory.db"

def migrate():
    """Add calendar integration fields to goals table"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(goals)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        migrations_needed = []

        if "recurring_days" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE goals ADD COLUMN recurring_days TEXT DEFAULT NULL"
            )

        if "calendar_event_template_id" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE goals ADD COLUMN calendar_event_template_id TEXT DEFAULT NULL"
            )

        if "session_time_start" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE goals ADD COLUMN session_time_start TEXT DEFAULT NULL"
            )

        if "session_time_end" not in existing_columns:
            migrations_needed.append(
                "ALTER TABLE goals ADD COLUMN session_time_end TEXT DEFAULT NULL"
            )

        if not migrations_needed:
            print("✅ Goals table already has calendar integration fields. No migration needed.")
            return

        # Run migrations
        for migration in migrations_needed:
            print(f"Running: {migration}")
            cursor.execute(migration)

        conn.commit()
        print(f"\n✅ Successfully added {len(migrations_needed)} calendar integration fields to goals table.")

        # Verify
        cursor.execute("PRAGMA table_info(goals)")
        columns = cursor.fetchall()
        print("\n📋 Current goals table schema:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Starting goals calendar integration migration...\n")
    migrate()
    print("\n✅ Migration complete!")
