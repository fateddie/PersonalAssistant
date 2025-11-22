"""
Gmail IMAP Fetcher
==================
Connect to Gmail via IMAP and fetch emails.
"""

import imaplib
import email
import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from .email_parser import decode_email_header, extract_email_body, count_attachments, parse_email_address
from .database import store_email
from .priority import calculate_priority

# Load environment variables
config_dir = Path(__file__).parent.parent.parent.parent / "config" / ".env"
load_dotenv(config_dir)

# Gmail configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_IMAP_SERVER = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
GMAIL_IMAP_PORT = int(os.getenv("GMAIL_IMAP_PORT", "993"))
GMAIL_FETCH_LIMIT = int(os.getenv("GMAIL_FETCH_LIMIT", "100"))


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
                except (ValueError, TypeError):
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
        except Exception:
            pass

    return emails
