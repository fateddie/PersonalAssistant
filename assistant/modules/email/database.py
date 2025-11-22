"""
Email Database Operations
=========================
Database CRUD operations for email storage.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from sqlalchemy import create_engine, text

# Database connection (single source of truth)
_project_root = Path(__file__).parent.parent.parent.parent
_db_path = _project_root / "assistant" / "data" / "memory.db"
DB_PATH = f"sqlite:///{_db_path}"
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})

# Unified engine points to same database
unified_engine = engine


def check_email_exists(email_id: str) -> bool:
    """Check if email already exists in database"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM emails WHERE email_id = :eid"), {"eid": email_id}
        )
        count = result.scalar()
        return count > 0


def store_email(email_data: Dict[str, Any]) -> bool:
    """Store email in database (with deduplication)"""
    try:
        # Check if already exists
        if check_email_exists(email_data["email_id"]):
            return False  # Already stored

        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO emails (
                        email_id, from_name, from_email, to_email, subject,
                        date_received, body_text, body_html, attachments_count,
                        priority, is_read, folder
                    ) VALUES (
                        :email_id, :from_name, :from_email, :to_email, :subject,
                        :date_received, :body_text, :body_html, :attachments_count,
                        :priority, :is_read, :folder
                    )
                """
                ),
                {
                    "email_id": email_data["email_id"],
                    "from_name": email_data["from_name"],
                    "from_email": email_data["from_email"],
                    "to_email": email_data["to_email"],
                    "subject": email_data["subject"],
                    "date_received": email_data["date_received"],
                    "body_text": email_data["body_text"],
                    "body_html": email_data["body_html"],
                    "attachments_count": email_data["attachments_count"],
                    "priority": email_data["priority"],
                    "is_read": email_data["is_read"],
                    "folder": email_data["folder"],
                },
            )
        return True  # Newly stored
    except Exception as e:
        print(f"❌ Error storing email: {e}")
        return False


def update_email_summary(email_id: str, summary: str, action_items: List[str]) -> bool:
    """Update email summary and action items in database"""
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE emails
                    SET summary = :summary, action_items = :action_items
                    WHERE email_id = :email_id
                """
                ),
                {
                    "email_id": email_id,
                    "summary": summary,
                    "action_items": json.dumps(action_items),
                },
            )
        return True
    except Exception as e:
        print(f"❌ Error updating email summary: {e}")
        return False


def get_stored_emails(
    limit: int = 100, include_body: bool = False, include_summary: bool = True
) -> List[Dict[str, Any]]:
    """Get emails from database"""
    fields = """
        email_id, from_name, from_email, subject, date_received,
        priority, attachments_count, is_read, summary, action_items
    """
    if include_body:
        fields += ", body_text"

    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"""
                SELECT {fields}
                FROM emails
                ORDER BY date_received DESC
                LIMIT :limit
            """
            ),
            {"limit": limit},
        )

        emails = []
        for row in result:
            email_dict = {
                "email_id": row[0],
                "from_name": row[1],
                "from_email": row[2],
                "subject": row[3],
                "date_received": row[4],
                "priority": row[5],
                "attachments_count": row[6],
                "is_read": row[7],
            }

            if include_summary:
                email_dict["summary"] = row[8]
                # Parse action_items from JSON
                try:
                    email_dict["action_items"] = json.loads(row[9]) if row[9] else []
                except (json.JSONDecodeError, TypeError):
                    email_dict["action_items"] = []

            if include_body:
                email_dict["body_text"] = row[10] if include_body else None

            emails.append(email_dict)

        return emails
