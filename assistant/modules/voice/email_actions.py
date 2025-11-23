"""
Email Actions
=============
Email-related action functions.
"""

import requests
from typing import Dict

# Gmail client singleton
_gmail_client = None


def get_gmail_client():
    """Get Gmail client singleton (lazy load)"""
    global _gmail_client
    if _gmail_client is None:
        try:
            from assistant.modules.email_assistant.gmail_client import GmailClient

            _gmail_client = GmailClient()
        except Exception as e:
            print(f"⚠️ Gmail client not available: {e}")
    return _gmail_client


def search_emails(pending_data: Dict) -> str:
    """Search emails by category or query."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured. Please set up Gmail API authentication first."

    category = pending_data.get("category")
    query = pending_data.get("query", "")
    max_results = pending_data.get("max_results", 10)

    try:
        if category:
            emails = gmail.search_by_category(category, max_results)
        else:
            emails = gmail.list_emails(query=query, max_results=max_results)

        if not emails:
            return f"📭 No emails found{f' in {category}' if category else ''}."

        parts = [f"📧 **Found {len(emails)} emails{f' ({category})' if category else ''}:**\n"]
        for i, email in enumerate(emails, 1):
            unread = "🔵" if email.get("is_unread") else ""
            starred = "⭐" if email.get("is_starred") else ""
            subject = email.get("subject", "(No subject)")[:50]
            sender = email.get("from", "")[:30]
            parts.append(f"{i}. {unread}{starred} **{subject}**")
            parts.append(f"   From: {sender}")
            parts.append(f"   ID: `{email['id'][:20]}...`")

        return "\n".join(parts)

    except Exception as e:
        return f"❌ Error searching emails: {str(e)}"


def fetch_new_emails(pending_data: Dict) -> str:
    """Fetch new emails from Gmail."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured. Please set up Gmail API authentication first."

    max_results = pending_data.get("max_results", 20)

    try:
        emails = gmail.list_emails(query="is:inbox", max_results=max_results)
        unread_count = len([e for e in emails if e.get("is_unread")])
        return f"✅ Synced {len(emails)} emails from Gmail. {unread_count} unread."
    except Exception as e:
        return f"❌ Error fetching emails: {str(e)}"


def archive_email(pending_data: Dict) -> str:
    """Archive an email."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured."

    email_id = pending_data.get("email_id")
    if not email_id:
        return "❌ No email ID provided."

    try:
        if gmail.archive(email_id):
            return "✅ Email archived successfully."
        return "❌ Failed to archive email."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def delete_email(pending_data: Dict) -> str:
    """Delete (trash) an email."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured."

    email_id = pending_data.get("email_id")
    if not email_id:
        return "❌ No email ID provided."

    try:
        if gmail.trash(email_id):
            return "✅ Email moved to trash."
        return "❌ Failed to delete email."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def mark_email_read(pending_data: Dict) -> str:
    """Mark email as read."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured."

    email_id = pending_data.get("email_id")
    if gmail.mark_read(email_id):
        return "✅ Marked as read."
    return "❌ Failed to mark as read."


def mark_email_unread(pending_data: Dict) -> str:
    """Mark email as unread."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured."

    email_id = pending_data.get("email_id")
    if gmail.mark_unread(email_id):
        return "✅ Marked as unread."
    return "❌ Failed to mark as unread."


def star_email(pending_data: Dict) -> str:
    """Star an email."""
    gmail = get_gmail_client()
    if not gmail or not gmail.is_authenticated():
        return "❌ Gmail not configured."

    email_id = pending_data.get("email_id")
    if gmail.star(email_id):
        return "⭐ Email starred."
    return "❌ Failed to star email."


def detect_email_events(pending_data: Dict) -> str:
    """Detect events from emails via orchestrator."""
    try:
        max_emails = pending_data.get("max_emails", 50)
        response = requests.get(
            "http://localhost:8000/emails/detect-events", params={"limit": max_emails}, timeout=30
        )

        if response.status_code != 200:
            return "❌ Error detecting events. Is orchestrator running?"

        data = response.json()
        detected = data.get("detected", 0)
        events = data.get("events", [])

        if detected == 0:
            return "📭 No events detected in recent emails."

        parts = [f"📅 **Detected {detected} events from emails:**\n"]
        for event in events[:10]:
            title = event.get("title", "Untitled")[:50]
            event_type = event.get("event_type", "event")
            date_time = event.get("date_time", "")[:10]
            parts.append(f"• [{event_type}] {title} ({date_time})")

        return "\n".join(parts)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def list_pending_events(pending_data: Dict) -> str:
    """List events awaiting approval."""
    try:
        limit = pending_data.get("limit", 20)
        response = requests.get(
            "http://localhost:8000/emails/events",
            params={"status": "upcoming", "limit": limit},
            timeout=10,
        )

        if response.status_code != 200:
            return "❌ Error fetching events."

        data = response.json()
        events = data.get("events", [])

        if not events:
            return "📭 No pending events from emails."

        parts = [f"📅 **{len(events)} events awaiting action:**\n"]
        for event in events:
            eid = event.get("id", "")
            title = event.get("title", "Untitled")[:40]
            event_type = event.get("event_type", "event")
            event_date = event.get("date", "")
            parts.append(f"• **{title}** [{event_type}]")
            parts.append(f"  Date: {event_date} | ID: `{eid}`")

        return "\n".join(parts)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def approve_event(pending_data: Dict) -> str:
    """Approve an event from email."""
    event_id = pending_data.get("event_id")
    if not event_id:
        return "❌ No event ID provided."

    try:
        response = requests.post(
            f"http://localhost:8000/emails/events/{event_id}/approve", timeout=10
        )

        if response.status_code == 200:
            return "✅ Event approved!"
        return "❌ Failed to approve event."

    except Exception as e:
        return f"❌ Error: {str(e)}"


def reject_event(pending_data: Dict) -> str:
    """Reject an event from email."""
    event_id = pending_data.get("event_id")
    if not event_id:
        return "❌ No event ID provided."

    try:
        response = requests.post(
            f"http://localhost:8000/emails/events/{event_id}/reject", timeout=10
        )

        if response.status_code == 200:
            return "✅ Event dismissed."
        return "❌ Failed to reject event."

    except Exception as e:
        return f"❌ Error: {str(e)}"
