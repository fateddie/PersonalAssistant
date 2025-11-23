"""
Gmail API Client
================
Gmail API wrapper with authentication, rate limiting, and error handling.
Supports read, archive, delete, mark read/unread, star operations.
"""

import base64
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

from .rate_limiter import RateLimiter

# Load environment variables
project_root = Path(__file__).parent.parent.parent.parent
env_local = project_root / ".env.local"
env_file = project_root / ".env"
config_env = project_root / "config" / ".env"

if env_local.exists():
    load_dotenv(env_local)
if config_env.exists():
    load_dotenv(config_env)
load_dotenv(env_file)

# Token storage (same pattern as calendar module)
TOKEN_FILE = project_root / "config" / "gmail_token.json"
CREDENTIALS_FILE = project_root / "config" / "credentials.json"

# Check for alternate credential locations
if not CREDENTIALS_FILE.exists():
    alt_creds = project_root / "credentials.json"
    if alt_creds.exists():
        CREDENTIALS_FILE = alt_creds


class GmailClient:
    """Gmail API wrapper with authentication, rate limiting, error handling"""

    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        self.service = None
        self.rate_limiter = RateLimiter(max_calls=100, period=60)
        self._initialize_service()

    def _initialize_service(self):
        """Initialize Gmail service if credentials exist"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request

            creds = None

            # Load existing token
            if TOKEN_FILE.exists():
                with open(TOKEN_FILE, "r") as token:
                    creds_data = json.load(token)
                    creds = Credentials.from_authorized_user_info(creds_data, self.scopes)

            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())

            if creds and creds.valid:
                self.service = build("gmail", "v1", credentials=creds)
                print("✅ Gmail API service initialized")
            else:
                print("⚠️  Gmail not authenticated. Run OAuth flow first.")

        except ImportError:
            print("⚠️  google-api-python-client not installed")
        except Exception as e:
            print(f"⚠️  Gmail initialization error: {e}")

    def is_authenticated(self) -> bool:
        """Check if Gmail API is authenticated"""
        return self.service is not None

    def list_emails(self, query: str = "", max_results: int = 20) -> List[Dict]:
        """
        List emails matching query.

        Args:
            query: Gmail search query (e.g., "from:example@gmail.com", "is:unread")
            max_results: Maximum emails to return

        Returns: List of email metadata (no body)
        """
        if not self.service:
            return []

        self.rate_limiter.wait_if_needed()

        try:
            from googleapiclient.errors import HttpError

            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                self.rate_limiter.wait_if_needed()
                metadata = (
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=msg["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )

                headers = {h["name"]: h["value"] for h in metadata["payload"]["headers"]}
                labels = metadata.get("labelIds", [])

                emails.append(
                    {
                        "id": msg["id"],
                        "thread_id": msg["threadId"],
                        "subject": headers.get("Subject", "(No subject)"),
                        "from": headers.get("From", ""),
                        "date": headers.get("Date", ""),
                        "is_unread": "UNREAD" in labels,
                        "is_starred": "STARRED" in labels,
                    }
                )

            return emails

        except Exception as e:
            print(f"❌ Error listing emails: {e}")
            return []

    def fetch_email_body(self, message_id: str) -> Dict:
        """
        Fetch full email body on-demand.

        Returns: {
            'body_text': str,
            'body_html': str,
            'subject': str,
            'from': str,
            'date': str
        }
        """
        if not self.service:
            return {"error": "Gmail not authenticated"}

        self.rate_limiter.wait_if_needed()

        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            # Parse headers
            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}

            # Extract body
            body_text = ""
            body_html = ""

            def extract_body(payload):
                nonlocal body_text, body_html
                if "parts" in payload:
                    for part in payload["parts"]:
                        extract_body(part)
                elif "body" in payload and "data" in payload["body"]:
                    data = payload["body"]["data"]
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    if payload.get("mimeType") == "text/plain":
                        body_text = decoded
                    elif payload.get("mimeType") == "text/html":
                        body_html = decoded

            extract_body(message["payload"])

            return {
                "body_text": body_text,
                "body_html": body_html,
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
            }

        except Exception as e:
            print(f"❌ Error fetching email {message_id}: {e}")
            return {"error": str(e)}

    def search_by_category(self, category: str, max_results: int = 10) -> List[Dict]:
        """
        Search emails by predefined category.

        Categories: trading, education, newsletter, tech, personal
        """
        category_queries = {
            "trading": "from:(seekingalpha OR investorplace OR theotrade OR danelfin OR behindthemarkets)",
            "education": "from:(berkeley OR coursera OR edx OR udemy OR academia)",
            "newsletter": "from:(substack OR beehiiv OR mailchimp) OR subject:newsletter",
            "tech": "from:(github OR gitguardian OR techpresso)",
            "personal": "is:important -from:(noreply OR newsletter)",
            "unread": "is:unread",
            "starred": "is:starred",
        }

        query = category_queries.get(category.lower(), category)
        return self.list_emails(query=query, max_results=max_results)

    def archive(self, message_id: str) -> bool:
        """Archive email (remove INBOX label)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
            ).execute()
            print(f"✅ Archived email {message_id}")
            return True

        except Exception as e:
            print(f"❌ Error archiving email {message_id}: {e}")
            return False

    def trash(self, message_id: str) -> bool:
        """Move email to trash"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().trash(userId="me", id=message_id).execute()
            print(f"✅ Trashed email {message_id}")
            return True

        except Exception as e:
            print(f"❌ Error trashing email {message_id}: {e}")
            return False

    def delete_permanently(self, message_id: str) -> bool:
        """Permanently delete email (use with caution!)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().delete(userId="me", id=message_id).execute()
            print(f"✅ Permanently deleted email {message_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting email {message_id}: {e}")
            return False

    def mark_read(self, message_id: str) -> bool:
        """Mark email as read (remove UNREAD label)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return True

        except Exception as e:
            print(f"❌ Error marking read {message_id}: {e}")
            return False

    def mark_unread(self, message_id: str) -> bool:
        """Mark email as unread (add UNREAD label)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
            ).execute()
            return True

        except Exception as e:
            print(f"❌ Error marking unread {message_id}: {e}")
            return False

    def star(self, message_id: str) -> bool:
        """Star email (add STARRED label)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": ["STARRED"]}
            ).execute()
            print(f"✅ Starred email {message_id}")
            return True

        except Exception as e:
            print(f"❌ Error starring {message_id}: {e}")
            return False

    def unstar(self, message_id: str) -> bool:
        """Unstar email (remove STARRED label)"""
        if not self.service:
            return False

        self.rate_limiter.wait_if_needed()

        try:
            self.service.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["STARRED"]}
            ).execute()
            return True

        except Exception as e:
            print(f"❌ Error unstarring {message_id}: {e}")
            return False

    def get_unsubscribe_link(self, message_id: str) -> Optional[str]:
        """
        Get unsubscribe link from email headers.
        Returns the List-Unsubscribe URL if available.
        """
        if not self.service:
            return None

        self.rate_limiter.wait_if_needed()

        try:
            message = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["List-Unsubscribe"],
                )
                .execute()
            )

            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
            unsubscribe = headers.get("List-Unsubscribe", "")

            # Parse the header (usually contains <mailto:...> or <http://...>)
            import re

            http_match = re.search(r"<(https?://[^>]+)>", unsubscribe)
            if http_match:
                return http_match.group(1)

            return None

        except Exception as e:
            print(f"❌ Error getting unsubscribe link: {e}")
            return None


# Singleton instance
_gmail_client = None


def get_gmail_client() -> GmailClient:
    """Get or create Gmail client singleton"""
    global _gmail_client
    if _gmail_client is None:
        _gmail_client = GmailClient()
    return _gmail_client
