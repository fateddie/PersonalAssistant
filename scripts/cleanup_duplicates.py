"""
Cleanup Duplicates & Add Deduplication
=======================================
1. Remove duplicate entries from detected_events (keep oldest)
2. Add UNIQUE constraint on email_id
3. Remove duplicates from assistant_items
4. Re-run migration with clean data
"""
import sqlite3
from pathlib import Path

# Database paths - assistant_items is also in memory.db
MEMORY_DB = Path("assistant/data/memory.db")


def cleanup_detected_events():
    """Remove duplicate detected_events, keeping the oldest entry per email_id"""
    print("\n📧 Cleaning up detected_events table...")

    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()

    # Count before
    cursor.execute("SELECT COUNT(*) FROM detected_events")
    count_before = cursor.fetchone()[0]
    print(f"  Records before: {count_before}")

    # Count duplicates
    cursor.execute("""
        SELECT COUNT(*) FROM detected_events
        WHERE id NOT IN (
            SELECT MIN(id) FROM detected_events GROUP BY email_id
        )
    """)
    duplicates = cursor.fetchone()[0]
    print(f"  Duplicates to remove: {duplicates}")

    # Delete duplicates (keep oldest by MIN(id))
    cursor.execute("""
        DELETE FROM detected_events
        WHERE id NOT IN (
            SELECT MIN(id) FROM detected_events GROUP BY email_id
        )
    """)
    conn.commit()

    # Count after
    cursor.execute("SELECT COUNT(*) FROM detected_events")
    count_after = cursor.fetchone()[0]
    print(f"  Records after: {count_after}")

    # Add UNIQUE index if not exists
    try:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_detected_events_email_id
            ON detected_events(email_id)
        """)
        conn.commit()
        print("  ✅ UNIQUE index added on email_id")
    except Exception as e:
        print(f"  ⚠️ Index may already exist: {e}")

    conn.close()
    return count_before - count_after


def cleanup_assistant_items():
    """Remove duplicate assistant_items from gmail source"""
    print("\n📋 Cleaning up assistant_items table...")

    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assistant_items'")
    if not cursor.fetchone():
        print("  ⚠️ assistant_items table not found, skipping")
        conn.close()
        return 0

    # Count before
    cursor.execute("SELECT COUNT(*) FROM assistant_items WHERE source = 'gmail'")
    count_before = cursor.fetchone()[0]
    print(f"  Gmail records before: {count_before}")

    # Count duplicates by gmail_thread_url
    cursor.execute("""
        SELECT COUNT(*) FROM assistant_items
        WHERE source = 'gmail'
        AND id NOT IN (
            SELECT MIN(id) FROM assistant_items
            WHERE source = 'gmail'
            GROUP BY gmail_thread_url
        )
    """)
    duplicates = cursor.fetchone()[0]
    print(f"  Duplicates to remove: {duplicates}")

    # Delete duplicates
    cursor.execute("""
        DELETE FROM assistant_items
        WHERE source = 'gmail'
        AND id NOT IN (
            SELECT MIN(id) FROM assistant_items
            WHERE source = 'gmail'
            GROUP BY gmail_thread_url
        )
    """)
    conn.commit()

    # Count after
    cursor.execute("SELECT COUNT(*) FROM assistant_items WHERE source = 'gmail'")
    count_after = cursor.fetchone()[0]
    print(f"  Gmail records after: {count_after}")

    conn.close()
    return count_before - count_after


def show_summary():
    """Show summary of remaining data"""
    print("\n📊 Summary after cleanup:")

    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()

    # detected_events
    cursor.execute("SELECT event_type, COUNT(*) FROM detected_events GROUP BY event_type")
    print("\n  detected_events by type:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    # assistant_items
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assistant_items'")
    if cursor.fetchone():
        cursor.execute("SELECT type, COUNT(*) FROM assistant_items GROUP BY type")
        print("\n  assistant_items by type:")
        for row in cursor.fetchall():
            print(f"    {row[0]}: {row[1]}")

    conn.close()


def main():
    print("=" * 60)
    print("CLEANUP: Removing Duplicate Records")
    print("=" * 60)

    removed_events = cleanup_detected_events()
    removed_items = cleanup_assistant_items()

    show_summary()

    print("\n" + "=" * 60)
    print(f"CLEANUP COMPLETE")
    print(f"  Removed from detected_events: {removed_events}")
    print(f"  Removed from assistant_items: {removed_items}")
    print("=" * 60)


if __name__ == "__main__":
    main()
