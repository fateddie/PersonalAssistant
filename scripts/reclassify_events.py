"""
Reclassify Email Events
========================
Updates existing assistant_items with improved classification.
Uses sender-based and event_type-based logic.
"""
import sqlite3
from pathlib import Path

MEMORY_DB = Path("assistant/data/memory.db")

# Known newsletter/promotional senders
NEWSLETTER_DOMAINS = [
    "beehiiv.com", "substack.com", "mailchimp.com", "sendgrid.net",
    "constantcontact.com", "hubspot.com", "sparkpost.com", "mailin.fr"
]


def classify_event(event_type: str, attendees: str, title: str) -> str:
    """Classify email event into appropriate type."""
    event_type_lower = (event_type or "").lower()
    attendees_lower = (attendees or "").lower()
    title_lower = (title or "").lower()

    # Known newsletter/promotional senders → webinar
    if any(domain in attendees_lower for domain in NEWSLETTER_DOMAINS):
        return "webinar"

    # Direct type mapping
    if "meeting" in event_type_lower or "call" in event_type_lower:
        return "meeting"
    elif "webinar" in event_type_lower:
        return "webinar"
    elif "deadline" in event_type_lower:
        return "deadline"
    elif "appointment" in event_type_lower:
        return "appointment"

    # Title-based fallback
    if any(kw in title_lower for kw in ["register", "join us", "live event", "workshop"]):
        return "webinar"
    if any(kw in title_lower for kw in ["deadline", "due", "expires", "last day"]):
        return "deadline"
    if any(kw in title_lower for kw in ["doctor", "dentist", "appointment", "booking"]):
        return "appointment"

    # Default: webinar for most promotional emails
    return "webinar"


def get_original_event_type(email_id: str, conn) -> str:
    """Get original event_type from detected_events table."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT event_type FROM detected_events WHERE email_id LIKE ?",
        (f"%{email_id}%",)
    )
    row = cursor.fetchone()
    return row[0] if row else None


def reclassify():
    """Reclassify all Gmail-sourced items."""
    print("=" * 60)
    print("RECLASSIFYING EMAIL EVENTS")
    print("=" * 60)

    conn = sqlite3.connect(MEMORY_DB)
    cursor = conn.cursor()

    # Get all Gmail items with current classification
    cursor.execute("""
        SELECT id, type, title, participants, gmail_thread_url
        FROM assistant_items
        WHERE source = 'gmail'
    """)
    gmail_items = cursor.fetchall()
    print(f"\nFound {len(gmail_items)} Gmail items to reclassify")

    # Track changes by type
    changes = {"unchanged": 0}

    for item_id, current_type, title, participants, gmail_url in gmail_items:
        # Extract email_id from gmail_url (rfc822msgid:XXX)
        email_id = None
        if gmail_url and "rfc822msgid:" in gmail_url:
            email_id = gmail_url.split("rfc822msgid:")[-1]

        # Get original event_type from detected_events
        original_type = get_original_event_type(email_id, conn) if email_id else None

        # Calculate new classification
        new_type = classify_event(original_type, participants, title)

        if current_type != new_type:
            # Update the item
            cursor.execute(
                "UPDATE assistant_items SET type = ? WHERE id = ?",
                (new_type, item_id)
            )
            change_key = f"{current_type} → {new_type}"
            changes[change_key] = changes.get(change_key, 0) + 1
            print(f"  {item_id[:20]}... : {current_type} → {new_type}")
        else:
            changes["unchanged"] += 1

    conn.commit()

    # Summary
    print("\n" + "=" * 60)
    print("RECLASSIFICATION SUMMARY")
    print("=" * 60)
    for change, count in sorted(changes.items()):
        print(f"  {change}: {count}")

    # Final counts
    cursor.execute("SELECT type, COUNT(*) FROM assistant_items GROUP BY type")
    print("\n  Final counts by type:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}")

    conn.close()
    print("\n✅ Reclassification complete!")


if __name__ == "__main__":
    reclassify()
