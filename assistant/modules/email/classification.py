"""
Email Classification
====================
Sender classification, goal matching, and event type classification.
"""

from datetime import datetime, date
from typing import Dict, Optional, Tuple
from urllib.parse import quote
from sqlalchemy import text

from .database import unified_engine

# Newsletter domains for classification
NEWSLETTER_DOMAINS = [
    "beehiiv.com", "substack.com", "mailchimp.com", "sendgrid.net",
    "constantcontact.com", "hubspot.com", "sparkpost.com", "mailin.fr"
]

# Sender categorization mapping (domain pattern -> (category, subcategory))
SENDER_CATEGORIES = {
    # Content Creation
    "foundr.com": ("content_creation", "course"),
    "beehiiv.com": ("content_creation", "newsletter"),
    "vidiq.com": ("content_creation", "youtube"),
    "vinhgiang.com": ("content_creation", "speaking"),
    "literallyacademy.com": ("content_creation", "course"),

    # Trading / Markets
    "seekingalpha.com": ("trading", "market_summary"),
    "investorplace.com": ("trading", "promotional"),
    "behindthemarkets.com": ("trading", "newsletter"),
    "theotrade.com": ("trading", "course"),
    "danelfin.com": ("trading", "signals"),
    "tradingdesk": ("trading", "newsletter"),
    "digitalassetdaily": ("trading", "crypto"),
    "thedefinvestor": ("trading", "crypto"),

    # Education / MOOC
    "berkeley.edu": ("education", "mooc"),
    "academia-mail.com": ("education", "research"),
    "newventureweekly": ("education", "startup"),

    # Tech
    "github.com": ("tech", "updates"),
    "gitguardian.com": ("tech", "security"),
    "techpresso": ("tech", "newsletter"),

    # Other services
    "google.com": ("service", "account"),
    "temu": ("shopping", "promotional"),
}

# Goal keyword mappings for matching emails to goals
GOAL_KEYWORDS = {
    "mooc": ["course", "lecture", "assignment", "berkeley", "agentx", "agentic", "deepmind", "competition"],
    "ai": ["machine learning", "neural", "llm", "gpt", "agent", "model"],
    "gym": ["workout", "fitness", "exercise", "training"],
    "guitar": ["music", "practice", "lesson", "chord"],
}


def classify_sender(email_address: str) -> Tuple[str, str]:
    """
    Classify sender by email domain into category and subcategory.
    Returns (category, subcategory) tuple.
    """
    if not email_address:
        return ("other", "unknown")

    email_lower = email_address.lower()

    # Check each pattern
    for pattern, (category, subcategory) in SENDER_CATEGORIES.items():
        if pattern in email_lower:
            return (category, subcategory)

    # Default classification based on domain type
    if any(domain in email_lower for domain in NEWSLETTER_DOMAINS):
        return ("content_creation", "newsletter")

    return ("other", "unknown")


def match_email_to_goal(title: str, body: str = "") -> Optional[str]:
    """
    Match email content against existing goals.
    Returns goal_id if a match is found, None otherwise.
    """
    content = f"{title} {body}".lower()

    try:
        with unified_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, description FROM assistant_items WHERE type = 'goal'")
            )
            goals = result.fetchall()

            for goal in goals:
                goal_id, goal_title, goal_desc = goal
                goal_title_lower = (goal_title or "").lower()

                # Direct title match
                if goal_title_lower in content:
                    print(f"📎 Matched email to goal '{goal_title}' (direct match)")
                    return goal_id

                # Check goal keywords
                for keyword, related_words in GOAL_KEYWORDS.items():
                    if keyword in goal_title_lower:
                        # Goal contains this keyword, check if email matches related words
                        if any(word in content for word in related_words):
                            print(f"📎 Matched email to goal '{goal_title}' (keyword: {keyword})")
                            return goal_id

    except Exception as e:
        print(f"⚠️ Error matching email to goal: {e}")

    return None


def classify_event_type(event_type: str, attendees: str, title: str) -> str:
    """
    Classify email event into appropriate type for unified API.

    Returns: appointment | meeting | webinar | deadline
    """
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


def store_to_unified_db(event_data: Dict) -> bool:
    """
    Store detected event directly to assistant_items (single source of truth).
    Uses improved classification and deduplication by gmail_thread_url.
    """
    try:
        email_id = event_data.get("email_id", "")

        # Build Gmail URL
        gmail_url = None
        if email_id:
            message_id = email_id.strip("<>")
            encoded_id = quote(message_id, safe='')
            gmail_url = f"https://mail.google.com/mail/u/0/#search/rfc822msgid:{encoded_id}"

        # Parse date_time
        event_date = date.today()
        start_time = None
        if event_data.get("date_time"):
            try:
                dt = datetime.fromisoformat(event_data["date_time"].replace("Z", "+00:00"))
                event_date = dt.date()
                start_time = dt.strftime("%H:%M")
            except (ValueError, AttributeError):
                pass

        # Classify event type
        item_type = classify_event_type(
            event_data.get("event_type"),
            event_data.get("attendees"),
            event_data.get("title")
        )

        # Match email to existing goals
        title = event_data.get("title", "")
        goal_id = match_email_to_goal(title)

        # Classify sender into category/subcategory
        sender_email = event_data.get("attendees", "")
        category, subcategory = classify_sender(sender_email)

        # Generate unique ID based on email_id
        item_id = f"email_{email_id.strip('<>').replace('@', '_at_')[:50]}"

        with unified_engine.begin() as conn:
            # Check if already exists by gmail_thread_url
            result = conn.execute(
                text("SELECT id FROM assistant_items WHERE gmail_thread_url = :url"),
                {"url": gmail_url}
            )
            if result.fetchone():
                return False  # Already exists - skip

            # Insert into assistant_items (single source of truth)
            conn.execute(
                text("""
                    INSERT INTO assistant_items (
                        id, type, title, date, start_time, status, source,
                        gmail_thread_url, location, participants, goal_id, priority,
                        category, subcategory, created_at, updated_at
                    ) VALUES (
                        :id, :type, :title, :date, :start_time, :status, :source,
                        :gmail_thread_url, :location, :participants, :goal_id, :priority,
                        :category, :subcategory, :created_at, :updated_at
                    )
                """),
                {
                    "id": item_id,
                    "type": item_type,
                    "title": title,
                    "date": event_date,
                    "start_time": start_time,
                    "status": "upcoming",
                    "source": "gmail",
                    "gmail_thread_url": gmail_url,
                    "location": event_data.get("location"),
                    "participants": sender_email,
                    "goal_id": goal_id,
                    "priority": "high" if goal_id else None,
                    "category": category,
                    "subcategory": subcategory,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )

        if category != "other":
            print(f"📧 Classified: {category}/{subcategory} - {title[:50]}...")

        return True

    except Exception as e:
        print(f"⚠️ Error storing to unified DB: {e}")
        return False


def store_detected_event(event_data: Dict) -> bool:
    """
    Store detected event directly to unified assistant_items database.
    This is the single source of truth - no more detected_events table.
    """
    return store_to_unified_db(event_data)
