"""
AI Service for Email Processing
================================
Configurable AI backend supporting both HuggingFace (local) and OpenAI (API).

Features:
- Dual provider support (HuggingFace + OpenAI)
- Graceful fallback if HuggingFace unavailable
- Cost tracking and transparency
- Email summarization
- Action item extraction
- Event detection support

Configuration (config/.env):
    AI_PROVIDER=hybrid  # Options: huggingface, openai, hybrid
    HF_MODEL=facebook/bart-large-cnn
    OPENAI_FALLBACK=true
"""

import os
import time
import logging
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from config/.env
config_dir = Path(__file__).parent.parent.parent.parent / "config" / ".env"
load_dotenv(config_dir)

# Configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "hybrid")  # huggingface, openai, hybrid
HF_MODEL = os.getenv("HF_MODEL", "facebook/bart-large-cnn")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_FALLBACK = os.getenv("OPENAI_FALLBACK", "true").lower() == "true"

# Rate limiting
LAST_API_CALL = 0
MIN_CALL_INTERVAL = 0.5

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI providers
openai_client = None
hf_summarizer = None
use_huggingface = False


def _init_openai():
    """Initialize OpenAI client"""
    global openai_client
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your-"):
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("✅ OpenAI client initialized")
            return True
        except Exception as e:
            logger.warning(f"⚠️  OpenAI initialization failed: {e}")
            return False
    return False


def _init_huggingface():
    """Initialize HuggingFace summarization pipeline"""
    global hf_summarizer, use_huggingface

    # Skip if provider is set to openai only
    if AI_PROVIDER == "openai":
        logger.info("ℹ️  AI_PROVIDER=openai, skipping HuggingFace initialization")
        return False

    try:
        from transformers import pipeline

        logger.info(f"Loading HuggingFace model: {HF_MODEL}...")
        hf_summarizer = pipeline(
            "summarization",
            model=HF_MODEL,
            device=-1  # CPU (use 0 for GPU if available)
        )
        use_huggingface = True
        logger.info(f"✅ HuggingFace model loaded: {HF_MODEL}")
        return True

    except ImportError:
        logger.warning("⚠️  transformers library not installed. Install with: pip install transformers torch")
        return False
    except Exception as e:
        logger.warning(f"⚠️  HuggingFace initialization failed: {e}")
        return False


# Initialize on module load
openai_available = _init_openai()
hf_available = _init_huggingface()


def is_configured() -> bool:
    """Check if at least one AI provider is configured"""
    return openai_available or hf_available


def get_active_provider() -> str:
    """Get the currently active AI provider"""
    if AI_PROVIDER == "openai" and openai_available:
        return "openai"
    elif AI_PROVIDER == "huggingface" and hf_available:
        return "huggingface"
    elif AI_PROVIDER == "hybrid":
        if hf_available:
            return "huggingface"
        elif openai_available:
            return "openai_fallback"

    # Fallback logic
    if hf_available:
        return "huggingface"
    elif openai_available:
        return "openai_fallback"

    return "none"


def rate_limit():
    """Implement rate limiting for API calls"""
    global LAST_API_CALL
    now = time.time()
    elapsed = now - LAST_API_CALL
    if elapsed < MIN_CALL_INTERVAL:
        time.sleep(MIN_CALL_INTERVAL - elapsed)
    LAST_API_CALL = time.time()


def summarize_with_huggingface(text: str, max_length: int = 130) -> Optional[str]:
    """
    Summarize text using HuggingFace model (local, free).

    Args:
        text: Text to summarize
        max_length: Maximum summary length in tokens

    Returns:
        Summary string or None if failed
    """
    if not hf_summarizer:
        return None

    try:
        # Truncate input to model's max length (1024 tokens for BART)
        text = text[:4000]  # ~1000 tokens

        # Generate summary
        result = hf_summarizer(
            text,
            max_length=max_length,
            min_length=30,
            do_sample=False,
            truncation=True
        )

        summary = result[0]['summary_text']
        logger.info(f"✅ HuggingFace summarization: {len(text)} chars → {len(summary)} chars")
        return summary

    except Exception as e:
        logger.error(f"❌ HuggingFace summarization error: {e}")
        return None


def summarize_with_openai(text: str, max_tokens: int = 150) -> Optional[str]:
    """
    Summarize text using OpenAI API.

    Args:
        text: Text to summarize
        max_tokens: Maximum summary length in tokens

    Returns:
        Summary string or None if failed
    """
    if not openai_client:
        return None

    try:
        rate_limit()

        # Truncate text
        text = text[:2000]

        prompt = f"""Summarize this email in 2-3 concise sentences:

{text}

Focus on:
1. The main purpose/topic
2. Any requests or action items
3. Key deadlines or dates

Summary:"""

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that creates concise, helpful summaries."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"✅ OpenAI summarization: {len(text)} chars → {len(summary)} chars")
        return summary

    except Exception as e:
        logger.error(f"❌ OpenAI summarization error: {e}")
        return None


def summarize_email(email_data: Dict) -> Optional[str]:
    """
    Summarize email using configured AI provider with fallback.

    Args:
        email_data: Dictionary containing email fields (subject, body_text, from_email)

    Returns:
        Summary string or None if all methods failed
    """
    if not is_configured():
        logger.warning("⚠️  No AI provider configured")
        return None

    # Check if already summarized (caching)
    if email_data.get("summary"):
        return email_data["summary"]

    subject = email_data.get("subject", "")
    body = email_data.get("body_text", "")

    # If body is empty, use subject
    if not body:
        body = subject

    # Prepare text for summarization
    text = f"Subject: {subject}\n\n{body}"

    # Try providers based on configuration
    provider = get_active_provider()
    summary = None
    cost = "$0"

    if provider == "huggingface":
        summary = summarize_with_huggingface(text)
        cost = "$0 (local)"

        # Fallback to OpenAI if HF fails and fallback enabled
        if not summary and OPENAI_FALLBACK and openai_available:
            logger.warning("⚠️  HuggingFace failed, falling back to OpenAI")
            summary = summarize_with_openai(text)
            provider = "openai_fallback"
            cost = "~$0.02"

    elif provider in ["openai", "openai_fallback"]:
        summary = summarize_with_openai(text)
        cost = "~$0.02"

    # Add audit trail to email_data
    email_data["_ai_provider"] = provider
    email_data["_ai_cost"] = cost

    return summary


def extract_action_items(email_data: Dict) -> List[str]:
    """
    Extract action items from email using OpenAI.

    Note: This requires complex reasoning, so we use OpenAI even in hybrid mode.
    HuggingFace alternatives (like T5) can be added later if needed.

    Args:
        email_data: Dictionary containing email fields

    Returns:
        List of action items (empty if none found or OpenAI unavailable)
    """
    if not openai_client:
        return []

    subject = email_data.get("subject", "")
    body = email_data.get("body_text", "")

    if not body:
        body = subject

    # Truncate
    body = body[:2000]

    prompt = f"""Extract any action items from this email:

Subject: {subject}

{body}

List only specific actions required (e.g., "Review document", "Respond by Friday").
If no action items, respond with "None".

Action items:"""

    try:
        rate_limit()

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that identifies action items."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.3
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
        logger.error(f"❌ Action item extraction error: {e}")
        return []


def generate_daily_email_overview(emails: List[Dict]) -> Optional[str]:
    """
    Generate a daily overview of all emails using OpenAI.

    Args:
        emails: List of email dictionaries

    Returns:
        Overview string or None if failed
    """
    if not openai_client:
        return None

    if not emails:
        return "No emails today."

    # Build email list
    email_list = []
    for i, email in enumerate(emails[:10], 1):
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

        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an email assistant that provides daily email overviews."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.3
        )

        overview = response.choices[0].message.content.strip()
        return overview

    except Exception as e:
        logger.error(f"❌ Overview generation error: {e}")
        return None


def get_provider_status() -> Dict:
    """Get status of all AI providers (for debugging/transparency)"""
    return {
        "configured_provider": AI_PROVIDER,
        "active_provider": get_active_provider(),
        "openai_available": openai_available,
        "huggingface_available": hf_available,
        "hf_model": HF_MODEL if hf_available else None,
        "openai_model": OPENAI_MODEL if openai_available else None,
        "fallback_enabled": OPENAI_FALLBACK
    }
