"""
Email Assistant Module
======================
Gmail API integration for email management.
"""

from .gmail_client import GmailClient
from .rate_limiter import RateLimiter

__all__ = ['GmailClient', 'RateLimiter']
