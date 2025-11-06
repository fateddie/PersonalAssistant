"""
OpenAI Summarization Service for Emails

Provides AI-powered email summaries and action item extraction using OpenAI API.

Features:
- Individual email summarization
- Batch email summarization
- Action item detection
- Caching to avoid re-summarization
- Rate limiting
- Error handling
"""

import os
import time
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "150"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Rate limiting
LAST_API_CALL = 0
MIN_CALL_INTERVAL = 0.5  # Seconds between API calls

# Initialize OpenAI client
client = None
if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your-"):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"⚠️  OpenAI client initialization failed: {e}")


def is_configured() -> bool:
    """Check if OpenAI is properly configured"""
    return client is not None


def rate_limit():
    """Implement rate limiting for API calls"""
    global LAST_API_CALL
    now = time.time()
    elapsed = now - LAST_API_CALL
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    LAST_API_CALL = time.time()


def summarize_email(email_data: Dict) -> Optional[str]:
    """
    Generate a concise summary of a single email.

    Args:
        email_data: Dictionary containing email fields (subject, body_text, from_email)

    Returns:
        Summary string (2-3 sentences) or None if failed
    """
    if not is_configured():
        return None

    # Check if already summarized (caching)
    if email_data.get("summary"):
        return email_data["summary"]

    subject = email_data.get("subject", "")
    body = email_data.get("body_text", "")
    from_email = email_data.get("from_email", "")

    # If body is empty, use subject
    if not body:
        body = subject

    # Truncate body to avoid token limits
    body = body[:2000]

    prompt = f"""Summarize this email in 2-3 concise sentences:

From: {from_email}
Subject: {subject}

{body}

Focus on:
1. The main purpose/topic
2. Any requests or action items
3. Key deadlines or dates

Summary:"""

    try:
        rate_limit()

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that creates concise, helpful summaries.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        print(f"⚠️  OpenAI summarization error: {e}")
        return None


def extract_action_items(email_data: Dict) -> List[str]:
    """
    Extract action items from email.

    Args:
        email_data: Dictionary containing email fields

    Returns:
        List of action items (empty list if none found or error)
    """
    if not is_configured():
        return []

    subject = email_data.get("subject", "")
    body = email_data.get("body_text", "")

    # If body is empty, use subject
    if not body:
        body = subject

    # Truncate body
    body = body[:2000]

    prompt = f"""Extract any action items from this email:

Subject: {subject}

{body}

List only specific actions required (e.g., "Review document", "Respond by Friday").
If no action items, respond with "None".

Action items:"""

    try:
        rate_limit()

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that identifies action items.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=OPENAI_TEMPERATURE,
        )

        result = response.choices[0].message.content.strip()

        # Parse action items
        if result.lower() == "none" or not result:
            return []

        # Split by newlines and clean
        items = []
        for line in result.split("\n"):
            line = line.strip()
            # Remove bullet points, numbers
            line = line.lstrip("•-*123456789. ")
            if line and len(line) > 3:
                items.append(line)

        return items[:5]  # Limit to 5 action items

    except Exception as e:
        print(f"⚠️  OpenAI action item extraction error: {e}")
        return []


def summarize_email_batch(emails: List[Dict]) -> Dict[str, str]:
    """
    Summarize multiple emails (for overview).

    Args:
        emails: List of email dictionaries

    Returns:
        Dictionary mapping email_id to summary
    """
    if not is_configured():
        return {}

    summaries = {}

    for email in emails:
        email_id = email.get("email_id")
        if not email_id:
            continue

        # Check if already summarized
        if email.get("summary"):
            summaries[email_id] = email["summary"]
        else:
            summary = summarize_email(email)
            if summary:
                summaries[email_id] = summary

    return summaries


def generate_daily_email_overview(emails: List[Dict]) -> Optional[str]:
    """
    Generate a daily overview of all emails.

    Args:
        emails: List of email dictionaries

    Returns:
        Overview string or None if failed
    """
    if not is_configured():
        return None

    if not emails:
        return "No emails today."

    # Build email list
    email_list = []
    for i, email in enumerate(emails[:10], 1):  # Limit to 10 emails
        from_name = email.get("from_name") or email.get("from_email", "Unknown")
        subject = email.get("subject", "(No subject)")
        priority = email.get("priority", "MEDIUM")
        email_list.append(f"{i}. [{priority}] {from_name}: {subject}")

    email_text = "\n".join(email_list)

    prompt = f"""Provide a brief overview of these {len(emails)} emails:

{email_text}

Give a 2-3 sentence summary highlighting:
1. Most important/urgent emails
2. Common themes
3. Overall volume and type (work, personal, marketing, etc.)

Overview:"""

    try:
        rate_limit()

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that provides daily email overviews.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=OPENAI_TEMPERATURE,
        )

        overview = response.choices[0].message.content.strip()
        return overview

    except Exception as e:
        print(f"⚠️  OpenAI overview generation error: {e}")
        return None
