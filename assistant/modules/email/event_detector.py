"""
Email Event Detection
=====================
Detects meetings, webinars, deadlines, and appointments from email content.

Features:
- Pattern-based event type detection
- Date/time extraction using dateutil
- URL extraction (Zoom, Meet, Teams links)
- Attendee extraction
- Location parsing

Event Types:
- meeting: In-person or virtual meetings
- webinar: Webinars, workshops, training sessions
- deadline: Project deadlines, due dates
- appointment: Scheduled appointments (doctor, dentist, etc.)
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dateutil import parser as date_parser
import logging

logger = logging.getLogger(__name__)

# Event type patterns
EVENT_PATTERNS = {
    "meeting": [
        r"\b(meeting|call|discussion|sync|standup|1:1|one[- ]on[- ]one)\b",
        r"\b(let'?s meet|join us|invite you|meeting invite)\b",
    ],
    "webinar": [
        r"\b(webinar|workshop|training session|seminar|live event|conference|presentation)\b",
        r"\b(register for|register now|join our live|attend our)\b",
        r"\b(info session|virtual event)\b",
    ],
    "deadline": [
        r"\b(deadline|due|submit|send by|respond by|reply by)\b",
        r"\b(expires?|expiration|last day|final day)\b",
    ],
    "appointment": [
        r"\b(appointment|booking|reservation|scheduled)\b",
        r"\b(doctor|dentist|consultation|checkup)\b",
    ],
}

# Sender patterns that indicate newsletters (not events)
NEWSLETTER_SENDER_PATTERNS = [
    r"newsletter@",
    r"@mail\.",
    r"@email\.",
    r"noreply@",
    r"milkroad",
    r"seekingalpha",
    r"investorplace",
    r"tradingdesk",
    r"behindthemarkets",
    r"foundr",
    r"beehiiv",
]

# Meeting URL patterns
URL_PATTERNS = {
    "zoom": r"https?://[\w.-]*zoom\.us/j/[\w?=&-]+",
    "google_meet": r"https?://meet\.google\.com/[\w-]+",
    "teams": r"https?://teams\.microsoft\.com/[\w?=&/-]+",
    "generic": r"https?://[\S]+",
}

# Date/time keyword patterns
DATE_KEYWORDS = [
    r"\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
    r"\b(today|tomorrow|tonight|next week|this week|next month)",
    r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}",
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
]

TIME_PATTERNS = [
    r"\b\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)",
    r"\b\d{1,2}\s*(?:am|pm|AM|PM)",
    r"\bat\s+\d{1,2}(?::\d{2})?",
]


def is_newsletter_sender(sender: str) -> bool:
    """Check if sender is a known newsletter source."""
    if not sender:
        return False
    sender_lower = sender.lower()
    for pattern in NEWSLETTER_SENDER_PATTERNS:
        if re.search(pattern, sender_lower):
            return True
    return False


def detect_event_type(text: str, sender: str = None) -> Optional[str]:
    """
    Detect the type of event from text.

    Args:
        text: Email subject + body text
        sender: Email sender address (optional, used to filter newsletters)

    Returns:
        Event type string or None if no event detected
    """
    # If sender is a known newsletter, skip event detection
    if sender and is_newsletter_sender(sender):
        return None

    text_lower = text.lower()

    # Score each event type
    scores = {}
    for event_type, patterns in EVENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            score += len(matches)
        scores[event_type] = score

    # Return event type with highest score (if > 0)
    max_score = max(scores.values())
    if max_score > 0:
        return max(scores, key=scores.get)

    return None


def extract_datetime(text: str, email_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Extract date/time from text using dateutil parser with improved logic.

    Args:
        text: Text containing date/time information
        email_date: Date the email was received (for context)

    Returns:
        datetime object or None if no date found
    """
    # Try to extract time first (more specific)
    time_match = None
    for pattern in TIME_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            time_match = matches[0]
            break

    # Try to find date patterns
    date_candidates = []
    for pattern in DATE_KEYWORDS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        date_candidates.extend(matches)

    # Combine date and time if both found
    if date_candidates and time_match:
        combined_text = f"{date_candidates[0]} {time_match}"
        try:
            dt = date_parser.parse(combined_text, fuzzy=True)

            # If date is in the past, try next occurrence
            now = datetime.now()
            if dt < now:
                # If it's a recent past date (within 7 days), move to next year
                if (now - dt).days < 7:
                    dt = dt.replace(year=now.year + 1)
                else:
                    # Add one week
                    dt += timedelta(days=7)

            return dt
        except (ValueError, TypeError):
            pass

    # Try parsing each date candidate with current time
    for candidate in date_candidates:
        try:
            dt = date_parser.parse(candidate, fuzzy=True)

            # If no time was in the original text, set to start of day
            if dt.time() == datetime.min.time():
                # If date is in past, try next occurrence
                now = datetime.now()
                if dt.date() < now.date():
                    # Check if it's a month/day pattern without year
                    if (now - dt).days < 365:
                        dt = dt.replace(year=now.year + 1)
                    else:
                        dt += timedelta(days=7)

            return dt

        except (ValueError, TypeError):
            continue

    # Last resort: try parsing the full text with better filtering
    try:
        dt = date_parser.parse(text, fuzzy=True)
        now = datetime.now()

        # Reject if date is significantly in the past (more than 2 hours ago)
        if dt < now - timedelta(hours=2):
            # Try to interpret as a future date by adjusting year
            if dt.month == now.month and dt.day < now.day:
                # Same month but past day - likely next year
                dt = dt.replace(year=now.year + 1)
            elif (now - dt).days < 60:
                # Recent past - likely next year
                dt = dt.replace(year=now.year + 1)
            else:
                return None

        return dt
    except:
        pass

    return None


def extract_meeting_urls(text: str) -> List[Dict[str, str]]:
    """
    Extract meeting URLs (Zoom, Google Meet, Teams, etc.).

    Args:
        text: Email body text

    Returns:
        List of dicts with 'type' and 'url' keys
    """
    urls = []

    for url_type, pattern in URL_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            urls.append({"type": url_type, "url": match})

    return urls


def extract_location(text: str) -> Optional[str]:
    """
    Extract physical location from text.

    Args:
        text: Email body text

    Returns:
        Location string or None
    """
    # Look for common location patterns
    location_patterns = [
        r"(?:location|where|address|venue):\s*([^\n]+)",
        r"(?:at|@)\s+([A-Z][^\n,]+(?:Room|Building|Street|Ave|Avenue|Road|Blvd))",
    ]

    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Limit length
            if len(location) < 100:
                return location

    return None


def extract_attendees(email_data: Dict) -> List[str]:
    """
    Extract attendee information from email headers and body.

    Args:
        email_data: Email dictionary with from_email, to_email, body_text

    Returns:
        List of email addresses
    """
    attendees = []

    # From sender
    from_email = email_data.get("from_email")
    if from_email:
        attendees.append(from_email)

    # Parse To: header if available
    to_email = email_data.get("to_email", "")
    # Simple split by comma
    if to_email:
        to_addresses = [addr.strip() for addr in to_email.split(",")]
        attendees.extend(to_addresses[:5])  # Limit to 5

    return list(set(attendees))  # Remove duplicates


def detect_event_from_email(email_data: Dict) -> Optional[Dict]:
    """
    Main function to detect event from email.

    Args:
        email_data: Dictionary with email fields (subject, body_text, from_email, etc.)

    Returns:
        Event dictionary or None if no event detected
    """
    subject = email_data.get("subject", "")
    body = email_data.get("body_text", "")
    from_email = email_data.get("from_email", "")

    # Combine subject and body for analysis
    full_text = f"{subject}\n\n{body}"

    # Detect event type (pass sender to filter out newsletters)
    event_type = detect_event_type(full_text, sender=from_email)
    if not event_type:
        return None  # No event detected (or is a newsletter)

    logger.info(f"📅 Detected {event_type} in email: {subject[:50]}...")

    # Extract date/time
    event_datetime = extract_datetime(full_text)

    # Extract URLs (for virtual meetings)
    urls = extract_meeting_urls(body)
    primary_url = urls[0]["url"] if urls else None

    # Extract location (for in-person meetings)
    location = extract_location(body)

    # If no physical location, check if it's virtual
    if not location and urls:
        location = f"Virtual ({urls[0]['type']})"

    # Extract attendees
    attendees = extract_attendees(email_data)

    # Build event data
    event_data = {
        "email_id": email_data.get("email_id"),
        "event_type": event_type,
        "title": subject,
        "date_time": event_datetime.isoformat() if event_datetime else None,
        "location": location,
        "url": primary_url,
        "attendees": ", ".join(attendees[:5]) if attendees else None,
        "confidence": _calculate_confidence(event_type, event_datetime, location or primary_url),
    }

    return event_data


def _calculate_confidence(event_type: str, has_datetime: bool, has_location: bool) -> str:
    """
    Calculate confidence level for detected event.

    Args:
        event_type: Detected event type
        has_datetime: Whether date/time was extracted
        has_location: Whether location/URL was found

    Returns:
        Confidence level: "high", "medium", "low"
    """
    score = 0

    # Event type detected
    score += 1

    # Date/time found
    if has_datetime:
        score += 2

    # Location or URL found
    if has_location:
        score += 1

    if score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


def batch_detect_events(emails: List[Dict]) -> List[Dict]:
    """
    Detect events from multiple emails.

    Args:
        emails: List of email dictionaries

    Returns:
        List of detected events (emails without events are excluded)
    """
    detected_events = []

    for email in emails:
        event = detect_event_from_email(email)
        if event:
            detected_events.append(event)

    logger.info(f"📅 Detected {len(detected_events)} events from {len(emails)} emails")

    return detected_events
