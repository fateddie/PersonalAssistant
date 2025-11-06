"""
Email Module (Phase 2 - Week 1)
================================
Real Gmail IMAP integration with AI-powered summaries and priority detection.

Features:
- Connect to Gmail via IMAP
- Fetch and parse emails (HTML + text)
- Store in database with caching
- Priority detection (HIGH/MEDIUM/LOW)
- OpenAI-powered summarization
- Action item extraction
"""

import imaplib
import email
import os
import json
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Import OpenAI service
from .openai_service import (
    summarize_email,
    extract_action_items,
    generate_daily_email_overview,
    is_configured as openai_is_configured,
)

# Load environment variables
load_dotenv()

router = APIRouter()

# Database connection
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///assistant/data/memory.db")
engine = create_engine(DB_PATH.replace("sqlite:///", "sqlite:///"))

# Gmail configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_IMAP_SERVER = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
GMAIL_IMAP_PORT = int(os.getenv("GMAIL_IMAP_PORT", "993"))
GMAIL_FETCH_LIMIT = int(os.getenv("GMAIL_FETCH_LIMIT", "100"))


def register(app, publish, subscribe):
    """Register email module with the orchestrator"""
    app.include_router(router, prefix="/emails")


def decode_email_header(header_value: Optional[str]) -> str:
    """Decode email header (handles UTF-8 encoding)"""
    if header_value is None:
        return ""

    decoded_parts = decode_header(header_value)
    decoded_str = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded_str += str(part)

    return decoded_str


def extract_email_body(msg: email.message.Message) -> tuple[str, str]:
    """Extract text and HTML body from email message"""
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            try:
                if content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                continue
    else:
        # Not multipart - just get the payload
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded_payload = payload.decode("utf-8", errors="ignore")
                if content_type == "text/plain":
                    body_text = decoded_payload
                elif content_type == "text/html":
                    body_html = decoded_payload
        except Exception:
            pass

    return body_text, body_html


def count_attachments(msg: email.message.Message) -> int:
    """Count the number of attachments in email"""
    count = 0
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                count += 1
    return count


def parse_email_address(address: str) -> tuple[str, str]:
    """Parse email address into name and email parts"""
    if "<" in address and ">" in address:
        # Format: "Name <email@example.com>"
        name_part = address.split("<")[0].strip().strip('"')
        email_part = address.split("<")[1].split(">")[0].strip()
        return name_part, email_part
    else:
        # Just email address
        return "", address.strip()


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
                    "action_items": json.dumps(action_items),  # Store as JSON
                },
            )
        return True
    except Exception as e:
        print(f"❌ Error updating email summary: {e}")
        return False


def calculate_priority(email_data: Dict[str, Any]) -> str:
    """
    Calculate email priority based on multiple factors.

    Scoring:
    - Sender importance (0-40 points)
    - Subject keywords (0-30 points)
    - Action words (0-20 points)
    - Recency (0-10 points)

    Categories:
    - HIGH: 50+ points
    - MEDIUM: 25-49 points
    - LOW: 0-24 points
    """
    score = 0
    subject_lower = email_data["subject"].lower()
    body_lower = email_data["body_text"].lower()

    # Sender importance (basic check - can be enhanced with contact list)
    from_email = email_data["from_email"].lower()
    if any(domain in from_email for domain in ["@work.", "@company.", ".edu", ".gov"]):
        score += 20

    # Subject keywords (urgent indicators)
    urgent_keywords = ["urgent", "asap", "deadline", "important", "critical", "action required"]
    if any(keyword in subject_lower for keyword in urgent_keywords):
        score += 30

    # Action words
    action_words = ["review", "approve", "sign", "respond", "confirm", "verify"]
    if any(word in subject_lower or word in body_lower[:500] for word in action_words):
        score += 20

    # Recency (emails from today get bonus)
    try:
        email_date = datetime.fromisoformat(email_data["date_received"].replace("Z", "+00:00"))
        age_hours = (datetime.now() - email_date.replace(tzinfo=None)).total_seconds() / 3600
        if age_hours < 24:
            score += 10
        elif age_hours < 72:
            score += 5
    except:
        pass

    # Categorize
    if score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    else:
        return "LOW"


def connect_to_gmail() -> Optional[imaplib.IMAP4_SSL]:
    """Connect to Gmail IMAP server"""
    try:
        mail = imaplib.IMAP4_SSL(GMAIL_IMAP_SERVER, GMAIL_IMAP_PORT)
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        return mail
    except Exception as e:
        print(f"❌ Gmail connection error: {e}")
        return None


def fetch_emails(limit: int = GMAIL_FETCH_LIMIT) -> List[Dict[str, Any]]:
    """
    Fetch emails from Gmail IMAP.

    Args:
        limit: Maximum number of emails to fetch

    Returns:
        List of parsed email dictionaries
    """
    # Check if Gmail is configured
    if not GMAIL_EMAIL or GMAIL_EMAIL.startswith("your-"):
        print("⚠️  Gmail not configured. See docs/GMAIL_SETUP.md")
        return []

    # Connect to Gmail
    mail = connect_to_gmail()
    if not mail:
        return []

    emails = []

    try:
        # Select INBOX
        status, _ = mail.select("INBOX")
        if status != "OK":
            print("❌ Failed to select INBOX")
            return emails

        # Search for all emails
        status, message_ids = mail.search(None, "ALL")
        if status != "OK":
            print("❌ Search failed")
            return emails

        # Get email IDs (latest first)
        email_ids = message_ids[0].split()
        email_ids = email_ids[-limit:]  # Get last N emails
        email_ids.reverse()  # Most recent first

        print(f"📧 Fetching {len(email_ids)} emails from Gmail...")

        # Fetch each email
        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                # Parse email
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)

                # Extract fields
                subject = decode_email_header(msg.get("Subject", "(No subject)"))
                from_header = decode_email_header(msg.get("From", ""))
                to_header = decode_email_header(msg.get("To", ""))
                date_header = msg.get("Date", "")
                message_id = msg.get("Message-ID", f"local-{email_id.decode()}")

                # Parse addresses
                from_name, from_email_addr = parse_email_address(from_header)

                # Parse date
                try:
                    date_obj = parsedate_to_datetime(date_header)
                    date_str = date_obj.isoformat()
                except:
                    date_str = datetime.now().isoformat()

                # Extract body
                body_text, body_html = extract_email_body(msg)

                # Count attachments
                attachments = count_attachments(msg)

                # Build email dict
                email_data = {
                    "email_id": message_id,
                    "from_name": from_name,
                    "from_email": from_email_addr,
                    "to_email": to_header,
                    "subject": subject,
                    "date_received": date_str,
                    "body_text": body_text[:5000],  # Limit body size
                    "body_html": body_html[:10000],
                    "attachments_count": attachments,
                    "is_read": False,
                    "folder": "INBOX",
                }

                # Calculate priority
                email_data["priority"] = calculate_priority(email_data)

                # Store in database (skip if duplicate)
                if store_email(email_data):
                    emails.append(email_data)

            except Exception as e:
                print(f"⚠️  Error parsing email {email_id}: {e}")
                continue

        print(f"✓ Fetched {len(emails)} new emails")

    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass

    return emails


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
                except:
                    email_dict["action_items"] = []

            if include_body:
                email_dict["body_text"] = row[10] if include_body else None

            emails.append(email_dict)

        return emails


@router.get("/summarise")
def summarise_emails(fetch_new: bool = False, limit: int = 10, generate_ai_summary: bool = False):
    """
    Get email summary.

    Query params:
        fetch_new: If True, fetch new emails from Gmail
        limit: Number of emails to return
        generate_ai_summary: If True, generate AI-powered daily overview

    Returns:
        {
            "total": int,
            "by_priority": {"HIGH": int, "MEDIUM": int, "LOW": int},
            "emails": [...],
            "overview": str (if generate_ai_summary=True and OpenAI configured)
        }
    """
    # Fetch new emails if requested
    if fetch_new:
        fetch_emails()

    # Get stored emails
    emails = get_stored_emails(limit=limit)

    # Count by priority
    priority_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for email in emails:
        priority = email.get("priority", "MEDIUM")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    response = {"total": len(emails), "by_priority": priority_counts, "emails": emails}

    # Generate AI overview if requested and configured
    if generate_ai_summary and openai_is_configured():
        overview = generate_daily_email_overview(emails)
        if overview:
            response["overview"] = overview

    return response


@router.get("/fetch")
def fetch_new_emails(limit: int = GMAIL_FETCH_LIMIT):
    """
    Fetch new emails from Gmail.

    Query params:
        limit: Maximum number of emails to fetch

    Returns:
        {
            "fetched": int,
            "message": str
        }
    """
    emails = fetch_emails(limit=limit)

    return {"fetched": len(emails), "message": f"Successfully fetched {len(emails)} new emails"}


@router.post("/generate_summaries")
def generate_summaries_endpoint(limit: int = 10):
    """
    Generate AI summaries for stored emails that don't have summaries yet.

    Query params:
        limit: Maximum number of emails to summarize

    Returns:
        {
            "summarized": int,
            "message": str
        }
    """
    if not openai_is_configured():
        return {"summarized": 0, "message": "OpenAI not configured. Set OPENAI_API_KEY in .env"}

    # Get emails without summaries (include body for summarization)
    emails = get_stored_emails(limit=limit, include_body=True)

    # Filter emails that need summaries
    emails_to_summarize = [e for e in emails if not e.get("summary")]

    summarized_count = 0

    print(f"📝 Generating summaries for {len(emails_to_summarize)} emails...")

    for email_data in emails_to_summarize:
        # Generate summary
        summary = summarize_email(email_data)
        if not summary:
            continue

        # Extract action items
        action_items = extract_action_items(email_data)

        # Update database
        if update_email_summary(email_data["email_id"], summary, action_items):
            summarized_count += 1
            print(f"✓ Summarized: {email_data['subject'][:50]}...")

    print(f"✓ Generated {summarized_count} summaries")

    return {
        "summarized": summarized_count,
        "message": f"Successfully generated {summarized_count} AI summaries",
    }
