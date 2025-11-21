"""
Migration Script: Old DB → Unified AssistantItem
=================================================
Migrates data from legacy tables to unified assistant_items table

Source tables (assistant/data/memory.db):
- tasks → type=task
- calendar_events → type=appointment or meeting
- detected_events → type=appointment or meeting
- goals → type=goal

Target table (assistant_api.db):
- assistant_items (unified schema)
"""
import os
import sys
from datetime import datetime, date, time
from pathlib import Path
from urllib.parse import quote

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from assistant_api.app.db import engine as new_engine, Base
from assistant_api.app.models import ItemType, ItemStatus, ItemSource

# Source database
OLD_DB_PATH = "sqlite:///assistant/data/memory.db"
old_engine = create_engine(OLD_DB_PATH)


def parse_datetime_to_date_time(dt_str):
    """
    Parse datetime string to (date, time) tuple

    Returns: (date_obj, time_str or None)
    """
    if not dt_str:
        return date.today(), None

    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.date(), dt.strftime("%H:%M")
    except:
        # Fallback: try just date
        try:
            d = datetime.strptime(dt_str, "%Y-%m-%d").date()
            return d, None
        except:
            return date.today(), None


def migrate_tasks():
    """Migrate tasks table"""
    print("\n📋 Migrating tasks...")

    with old_engine.connect() as old_conn:
        tasks = old_conn.execute(text("SELECT * FROM tasks")).fetchall()

        migrated = 0
        for task in tasks:
            # Determine status
            if task.completed == 1:
                status = ItemStatus.done
            else:
                status = ItemStatus.upcoming

            # Parse deadline as date
            task_date = date.today()
            if task.deadline:
                try:
                    task_date = datetime.fromisoformat(task.deadline).date()
                except:
                    pass

            # Determine priority from importance/urgency
            priority = "med"
            if task.importance >= 8 or task.urgency >= 8:
                priority = "high"
            elif task.importance <= 3 and task.urgency <= 3:
                priority = "low"

            # Insert into new DB
            with new_engine.begin() as new_conn:
                new_conn.execute(
                    text("""
                        INSERT INTO assistant_items
                        (id, type, title, description, date, status, source, priority, created_at)
                        VALUES
                        (:id, :type, :title, :description, :date, :status, :source, :priority, :created_at)
                    """),
                    {
                        "id": f"task_{task.id}",
                        "type": ItemType.task.value,
                        "title": task.title,
                        "description": task.notes or f"Project: {task.project}, Category: {task.category}, Tags: {task.tags}".strip(", ") if any([task.notes, task.project, task.category, task.tags]) else None,
                        "date": task_date,
                        "status": status.value,
                        "source": ItemSource.manual.value,
                        "priority": priority,
                        "created_at": task.created_at or datetime.now()
                    }
                )
            migrated += 1

    print(f"  ✅ Migrated {migrated} tasks")
    return migrated


def migrate_calendar_events():
    """Migrate calendar_events table"""
    print("\n📅 Migrating calendar events...")

    with old_engine.connect() as old_conn:
        events = old_conn.execute(text("SELECT * FROM calendar_events")).fetchall()

        migrated = 0
        for event in events:
            # Parse start/end times
            event_date, start_time_str = parse_datetime_to_date_time(event.start_time)
            _, end_time_str = parse_datetime_to_date_time(event.end_time)

            # Determine type (meeting if has attendees, else appointment)
            item_type = ItemType.meeting if event.attendees else ItemType.appointment

            # Status: done if in past, upcoming otherwise
            status = ItemStatus.done if event_date < date.today() else ItemStatus.upcoming

            # Insert into new DB
            with new_engine.begin() as new_conn:
                new_conn.execute(
                    text("""
                        INSERT INTO assistant_items
                        (id, type, title, date, start_time, end_time, status, source,
                         calendar_event_url, location, participants, created_at)
                        VALUES
                        (:id, :type, :title, :date, :start_time, :end_time, :status, :source,
                         :calendar_event_url, :location, :participants, :created_at)
                    """),
                    {
                        "id": f"calendar_{event.id}",
                        "type": item_type.value,
                        "title": event.title,
                        "date": event_date,
                        "start_time": start_time_str,
                        "end_time": end_time_str,
                        "status": status.value,
                        "source": ItemSource.calendar.value,
                        "calendar_event_url": event.url,
                        "location": event.location,
                        "participants": event.attendees,
                        "created_at": event.synced_at or datetime.now()
                    }
                )
            migrated += 1

    print(f"  ✅ Migrated {migrated} calendar events")
    return migrated


def migrate_detected_events():
    """Migrate detected_events table (email events)"""
    print("\n📧 Migrating detected email events...")

    with old_engine.connect() as old_conn:
        events = old_conn.execute(text("SELECT * FROM detected_events")).fetchall()

        migrated = 0
        for event in events:
            # Skip if already rejected/hidden
            if event.approval_status == "rejected":
                continue

            # Parse datetime
            event_date, start_time_str = parse_datetime_to_date_time(event.date_time)

            # Determine type
            event_type_lower = (event.event_type or "").lower()
            if "meeting" in event_type_lower or "call" in event_type_lower:
                item_type = ItemType.meeting
            else:
                item_type = ItemType.appointment

            # Status based on approval and date
            if event.approval_status == "accepted":
                status = ItemStatus.done if event_date < date.today() else ItemStatus.upcoming
            else:
                status = ItemStatus.upcoming

            # Build Gmail URL from email_id
            # Use RFC822 Message-ID search for accurate linking
            gmail_url = None
            if event.email_id:
                # Strip < > brackets and URL encode
                message_id = event.email_id.strip("<>")
                encoded_id = quote(message_id, safe='')
                gmail_url = f"https://mail.google.com/mail/u/0/#search/rfc822msgid:{encoded_id}"

            # Insert into new DB
            with new_engine.begin() as new_conn:
                new_conn.execute(
                    text("""
                        INSERT INTO assistant_items
                        (id, type, title, date, start_time, status, source,
                         gmail_thread_url, location, participants, created_at)
                        VALUES
                        (:id, :type, :title, :date, :start_time, :status, :source,
                         :gmail_thread_url, :location, :participants, :created_at)
                    """),
                    {
                        "id": f"email_event_{event.id}",
                        "type": item_type.value,
                        "title": event.title,
                        "date": event_date,
                        "start_time": start_time_str,
                        "status": status.value,
                        "source": ItemSource.gmail.value,
                        "gmail_thread_url": gmail_url or event.url,
                        "location": event.location,
                        "participants": event.attendees,
                        "created_at": event.created_at or datetime.now()
                    }
                )
            migrated += 1

    print(f"  ✅ Migrated {migrated} email events")
    return migrated


def migrate_goals():
    """Migrate goals table"""
    print("\n🎯 Migrating goals...")

    with old_engine.connect() as old_conn:
        goals = old_conn.execute(text("SELECT * FROM goals")).fetchall()

        migrated = 0
        for goal in goals:
            # Status based on completed field
            status = ItemStatus.done if goal.completed == 1 else ItemStatus.in_progress

            # Description includes target
            description = f"Target: {goal.target_per_week} per week" if goal.target_per_week else None

            # Use last_update as date, fallback to today
            goal_date = date.today()
            if goal.last_update:
                try:
                    goal_date = datetime.fromisoformat(goal.last_update).date()
                except:
                    pass

            # Insert into new DB
            with new_engine.begin() as new_conn:
                new_conn.execute(
                    text("""
                        INSERT INTO assistant_items
                        (id, type, title, description, date, status, source, created_at)
                        VALUES
                        (:id, :type, :title, :description, :date, :status, :source, :created_at)
                    """),
                    {
                        "id": f"goal_{goal.id}",
                        "type": ItemType.goal.value,
                        "title": goal.name,
                        "description": description,
                        "date": goal_date,
                        "status": status.value,
                        "source": ItemSource.manual.value,
                        "created_at": goal.last_update or datetime.now()
                    }
                )
            migrated += 1

    print(f"  ✅ Migrated {migrated} goals")
    return migrated


def main():
    """Run migration"""
    print("=" * 60)
    print("MIGRATION: Legacy DB → Unified AssistantItem")
    print("=" * 60)

    # Drop existing tables and create fresh schema
    print("\n🔧 Dropping old schema and creating fresh database...")
    Base.metadata.drop_all(bind=new_engine)
    Base.metadata.create_all(bind=new_engine)
    print("  ✅ Fresh schema created")

    # Run migrations
    totals = {
        "tasks": migrate_tasks(),
        "calendar_events": migrate_calendar_events(),
        "email_events": migrate_detected_events(),
        "goals": migrate_goals()
    }

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    for table, count in totals.items():
        print(f"  {table:20s}: {count:4d} items")
    print(f"\n  {'TOTAL':20s}: {sum(totals.values()):4d} items")
    print("=" * 60)
    print("\n✅ Migration complete!")
    print(f"\n📁 New database: assistant_api.db")
    print(f"📁 Old database: assistant/data/memory.db (preserved)\n")


if __name__ == "__main__":
    main()
