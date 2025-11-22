"""
Parsing Utilities for Conversational AI
========================================
Day, time, and entity extraction from natural language.
"""

import re
from datetime import date, timedelta

# Day mapping
DAY_MAP = {
    'monday': 0, 'mon': 0, 'tuesday': 1, 'tue': 1, 'tues': 1,
    'wednesday': 2, 'wed': 2, 'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
    'friday': 4, 'fri': 4, 'saturday': 5, 'sat': 5, 'sunday': 6, 'sun': 6
}

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def parse_days(text: str) -> list:
    """Parse day specifications from text like 'weekdays except monday' or 'mon-fri'."""
    # Fix common typos
    text_lower = text.lower().replace('weekdasy', 'weekdays').replace('weekedays', 'weekdays')
    days = set()

    # Weekdays / weekends - check first
    if 'weekday' in text_lower:
        days = {0, 1, 2, 3, 4}  # Mon-Fri
    elif 'weekend' in text_lower:
        days = {5, 6}  # Sat-Sun
    elif 'everyday' in text_lower or 'every day' in text_lower or 'daily' in text_lower:
        days = {0, 1, 2, 3, 4, 5, 6}

    # Handle "except" exclusions - must come AFTER weekdays detection
    if days and 'except' in text_lower:
        except_match = re.search(r'except\s+(\w+(?:\s*,?\s*and\s*|\s*,?\s*\w+)*)', text_lower)
        if except_match:
            exclude_text = except_match.group(1)
            for day_name, day_num in DAY_MAP.items():
                if day_name in exclude_text:
                    days.discard(day_num)

    # If no weekday/weekend specified, look for specific days
    if not days:
        for day_name, day_num in DAY_MAP.items():
            if day_name in text_lower:
                days.add(day_num)

    return sorted(list(days))


def parse_time_range(text: str) -> tuple:
    """Parse time range from text like '7:30-9am' or '9.00 to 10:30'."""
    # Normalize: replace . with : for time (7.30 -> 7:30)
    normalized = re.sub(r'(\d{1,2})\.(\d{2})', r'\1:\2', text.lower())

    # Pattern: 7:30-9am, 7:30am-9am, 7:30 - 9:00 am, 9 to 10:30
    time_pattern = r'(\d{1,2}(?::\d{2})?)\s*(?:am|pm)?\s*(?:-|to)\s*(\d{1,2}(?::\d{2})?)\s*(am|pm)?'
    match = re.search(time_pattern, normalized)

    if match:
        start_str = match.group(1)
        end_str = match.group(2)
        period = match.group(3) or 'am'

        # Parse start time
        if ':' in start_str:
            start_parts = start_str.split(':')
            start_hour, start_min = int(start_parts[0]), int(start_parts[1])
        else:
            start_hour, start_min = int(start_str), 0

        # Parse end time
        if ':' in end_str:
            end_parts = end_str.split(':')
            end_hour, end_min = int(end_parts[0]), int(end_parts[1])
        else:
            end_hour, end_min = int(end_str), 0

        # Handle AM/PM - check for am/pm near start time too
        start_period = 'am'
        if re.search(rf'{start_str}\s*pm', normalized):
            start_period = 'pm'
        elif start_hour < end_hour and period == 'pm' and start_hour < 12:
            start_period = 'pm'  # Both in PM if end is PM and start < end

        # Convert to 24h
        if start_period == 'pm' and start_hour < 12:
            start_hour += 12
        if period == 'pm' and end_hour < 12:
            end_hour += 12
        if start_period == 'am' and start_hour == 12:
            start_hour = 0
        if period == 'am' and end_hour == 12:
            end_hour = 0

        return f"{start_hour:02d}:{start_min:02d}", f"{end_hour:02d}:{end_min:02d}"

    return None, None


def format_days_list(days: list) -> str:
    """Format list of day numbers to readable string."""
    if not days:
        return "no days specified"
    if days == [0, 1, 2, 3, 4]:
        return "weekdays"
    if days == [5, 6]:
        return "weekends"
    if days == [0, 1, 2, 3, 4, 5, 6]:
        return "every day"
    return ", ".join(DAY_NAMES[d] for d in days)


def format_time(time_str: str) -> str:
    """Format 24h time to 12h format."""
    if not time_str:
        return ""
    try:
        hour, minute = map(int, time_str.split(':'))
        period = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        if minute == 0:
            return f"{display_hour} {period}"
        return f"{display_hour}:{minute:02d} {period}"
    except:
        return time_str


def get_next_occurrence(day_num: int) -> date:
    """Get the next occurrence of a day of week."""
    today = date.today()
    days_ahead = day_num - today.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days=days_ahead)


def parse_end_date(text: str) -> date:
    """
    Parse end date from natural language or date string.

    Examples:
        "6 months" -> date 6 months from now
        "3 months" -> date 3 months from now
        "december" -> Dec 31 of current/next year
        "june 2025" -> June 30, 2025
        "2025-06-30" -> June 30, 2025
        "indefinitely" -> 1 year from now (practical limit)

    Returns:
        date object representing the end date
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    today = date.today()
    text_lower = text.lower().strip()

    # Try ISO format first (YYYY-MM-DD)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', text_lower):
        try:
            parsed_date = date.fromisoformat(text_lower)
            # IMPORTANT: Don't accept past dates - LLM may send outdated dates from training data
            if parsed_date < today:
                return today + relativedelta(months=6)
            return parsed_date
        except ValueError:
            pass

    # Handle "X months" pattern
    months_match = re.search(r'(\d+)\s*months?', text_lower)
    if months_match:
        months = int(months_match.group(1))
        return today + relativedelta(months=months)

    # Handle "X weeks" pattern
    weeks_match = re.search(r'(\d+)\s*weeks?', text_lower)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        return today + timedelta(weeks=weeks)

    # Handle "X years" pattern
    years_match = re.search(r'(\d+)\s*years?', text_lower)
    if years_match:
        years = int(years_match.group(1))
        return today + relativedelta(years=years)

    # Handle month names (with optional year)
    month_names = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }

    # Find month in text
    for month_name, month_num in month_names.items():
        if month_name in text_lower:
            # Look for year
            year_match = re.search(r'20\d{2}', text_lower)
            if year_match:
                year = int(year_match.group())
            else:
                # Use current year if month is ahead, otherwise next year
                year = today.year
                if month_num <= today.month:
                    year += 1

            # Get last day of that month
            if month_num == 12:
                end_date = date(year, 12, 31)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)

            # Sanity check: never return a past date
            if end_date < today:
                end_date = date(today.year + 1, month_num + 1, 1) - timedelta(days=1) if month_num < 12 else date(today.year + 1, 12, 31)

            return end_date

    # Handle "indefinitely", "ongoing", "no end" - default to 1 year
    if any(word in text_lower for word in ['indefinite', 'ongoing', 'no end', 'forever']):
        return today + relativedelta(years=1)

    # Default: 6 months from today
    return today + relativedelta(months=6)


def extract_item_details(message: str) -> dict:
    """Extract item details from natural language message."""
    message_lower = message.lower()
    details = {
        'action': None,
        'type': None,
        'title': None,
        'days': [],
        'start_time': None,
        'end_time': None,
        'date': None,
        'status': None,
    }

    # Detect action
    if any(w in message_lower for w in ['create', 'add', 'new', 'schedule', 'set up', 'make']):
        details['action'] = 'create'
    elif any(w in message_lower for w in ['show', 'list', 'what', 'get', 'display']):
        details['action'] = 'show'
    elif any(w in message_lower for w in ['check', 'scan', 'summarize', 'summary']):
        details['action'] = 'check'
    elif any(w in message_lower for w in ['mark', 'complete', 'done', 'finish']):
        details['action'] = 'complete'
    elif any(w in message_lower for w in ['delete', 'remove', 'cancel']):
        details['action'] = 'delete'

    # Detect type
    if 'goal' in message_lower:
        details['type'] = 'goal'
    elif 'session' in message_lower:
        details['type'] = 'session'
    elif 'task' in message_lower:
        details['type'] = 'task'
    elif 'meeting' in message_lower:
        details['type'] = 'meeting'
    elif 'webinar' in message_lower:
        details['type'] = 'webinar'
    elif 'email' in message_lower:
        details['type'] = 'email'
    elif 'appointment' in message_lower:
        details['type'] = 'appointment'

    # Detect date context
    if 'today' in message_lower:
        details['date'] = 'today'
    elif 'tomorrow' in message_lower:
        details['date'] = 'tomorrow'
    elif 'this week' in message_lower or 'upcoming' in message_lower:
        details['date'] = 'week'

    # Extract title - look for "for X" or "called X" patterns
    title_patterns = [
        r'(?:for|called|named|titled)\s+["\']?([^"\',.]+)["\']?',
        r'goal\s+(?:for\s+)?["\']?([^"\',.]+?)["\']?\s*(?:,|with|weekday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|$)',
        r'session\s+(?:for\s+)?["\']?([^"\',.]+?)["\']?\s*(?:,|on|at|$)',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, message_lower)
        if match:
            details['title'] = match.group(1).strip()
            break

    # Parse days and times
    details['days'] = parse_days(message)
    details['start_time'], details['end_time'] = parse_time_range(message)

    return details
