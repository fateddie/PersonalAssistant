"""
Email Priority Calculator
=========================
Calculate email priority based on multiple factors.
"""

from datetime import datetime
from typing import Dict, Any


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
    except (ValueError, KeyError, AttributeError):
        pass

    # Categorize
    if score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    else:
        return "LOW"
