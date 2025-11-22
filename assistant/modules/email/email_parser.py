"""
Email Parser Utilities
======================
Functions for parsing and decoding email messages.
"""

import email
from email.header import decode_header
from email.message import Message
from typing import Optional, Tuple


def decode_email_header(header_value: Optional[str]) -> str:
    """Decode email header (handles UTF-8 encoding)"""
    if header_value is None:
        return ""

    decoded_parts = decode_header(header_value)
    decoded_str = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or "utf-8", errors="ignore")
        else:
            decoded_str += str(part)

    return decoded_str


def extract_email_body(msg: Message) -> Tuple[str, str]:
    """Extract text and HTML body from email message"""
    body_text = ""
    body_html = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            try:
                if content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                continue
    else:
        # Not multipart - just get the payload
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded_payload = payload.decode("utf-8", errors="ignore")
                if content_type == "text/plain":
                    body_text = decoded_payload
                elif content_type == "text/html":
                    body_html = decoded_payload
        except Exception:
            pass

    return body_text, body_html


def count_attachments(msg: Message) -> int:
    """Count the number of attachments in email"""
    count = 0
    if msg.is_multipart():
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                count += 1
    return count


def parse_email_address(address: str) -> Tuple[str, str]:
    """Parse email address into name and email parts"""
    if "<" in address and ">" in address:
        # Format: "Name <email@example.com>"
        name_part = address.split("<")[0].strip().strip('"')
        email_part = address.split("<")[1].split(">")[0].strip()
        return name_part, email_part
    else:
        # Just email address
        return "", address.strip()
