#!/usr/bin/env python3
"""
Database Migration: Add Approval Status Fields
================================================
Adds status/approval fields to tasks and goals tables for unified approval system.

Changes:
- tasks: Add 'status' field (values: 'pending', 'active', 'rejected')
- goals: Add 'status' field (values: 'pending', 'active', 'archived', 'rejected')
- Create hidden_calendar_events table for hiding calendar events

Run: python scripts/migrate_add_approval_status.py
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "assistant" / "data" / "memory.db"

def migrate():
    """Run database migrations"""
    print("🔄 Starting database migration...")
    print(f"📂 Database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add status field to tasks table (if not exists)
        print("\n1️⃣ Adding 'status' field to tasks table...")
        try:
            cursor.execute("""
                ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'active'
            """)
            print("   ✅ Added status field to tasks")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠️  status field already exists in tasks")
            else:
                raise

        # 2. Add status field to goals table (if not exists)
        print("\n2️⃣ Adding 'status' field to goals table...")
        try:
            cursor.execute("""
                ALTER TABLE goals ADD COLUMN status TEXT DEFAULT 'active'
            """)
            print("   ✅ Added status field to goals")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("   ⚠️  status field already exists in goals")
            else:
                raise

        # 3. Create hidden_calendar_events table (if not exists)
        print("\n3️⃣ Creating hidden_calendar_events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hidden_calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_event_id TEXT UNIQUE NOT NULL,
                event_title TEXT,
                hidden_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                hidden_by TEXT DEFAULT 'user'
            )
        """)
        print("   ✅ Created hidden_calendar_events table")

        # Commit changes
        conn.commit()

        # Verify changes
        print("\n✅ Migration completed successfully!")
        print("\n📊 Verification:")

        # Check tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        tasks_columns = [row[1] for row in cursor.fetchall()]
        print(f"   tasks columns: {', '.join(tasks_columns)}")

        # Check goals table
        cursor.execute("PRAGMA table_info(goals)")
        goals_columns = [row[1] for row in cursor.fetchall()]
        print(f"   goals columns: {', '.join(goals_columns)}")

        # Check hidden_calendar_events table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hidden_calendar_events'")
        if cursor.fetchone():
            print("   hidden_calendar_events: ✓ Created")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def rollback():
    """Rollback migrations (for testing)"""
    print("🔄 Rolling back migrations...")
    print(f"📂 Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Note: SQLite doesn't support DROP COLUMN
        # We would need to recreate tables to remove columns

        # Drop hidden_calendar_events table
        cursor.execute("DROP TABLE IF EXISTS hidden_calendar_events")
        print("   ✅ Dropped hidden_calendar_events table")

        conn.commit()
        print("✅ Rollback completed")

    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback()
    else:
        success = migrate()
        sys.exit(0 if success else 1)
