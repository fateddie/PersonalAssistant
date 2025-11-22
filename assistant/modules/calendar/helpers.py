"""
Calendar Helper Functions - Pure functions for recurring event management

These are pure functions (no I/O, no side effects) for easier testing.
Used by calendar module to generate recurring calendar events for goals.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
import re


def parse_recurring_days(text: str) -> List[str]:
    """
    Extract days of week from natural language text.

    Examples:
        "every monday and wednesday" -> ["mon", "wed"]
        "mon/wed/fri" -> ["mon", "wed", "fri"]
        "monday, wednesday, friday" -> ["mon", "wed", "fri"]
        "weekdays" -> ["mon", "tue", "wed", "thu", "fri"]
        "every day" -> ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    Args:
        text: Natural language description of recurring days

    Returns:
        List of lowercase 3-letter day abbreviations: ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        Empty list if no days found.
    """
    if not text:
        return []

    text_lower = text.lower()

    # Handle special cases
    if "every day" in text_lower or "daily" in text_lower:
        return ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    if "weekday" in text_lower:
        return ["mon", "tue", "wed", "thu", "fri"]

    if "weekend" in text_lower:
        return ["sat", "sun"]

    # Day mappings (full name and abbreviations)
    day_mappings = {
        "monday": "mon", "mon": "mon",
        "tuesday": "tue", "tue": "tue", "tues": "tue",
        "wednesday": "wed", "wed": "wed",
        "thursday": "thu", "thu": "thu", "thur": "thu", "thurs": "thu",
        "friday": "fri", "fri": "fri",
        "saturday": "sat", "sat": "sat",
        "sunday": "sun", "sun": "sun",
    }

    # Extract all day mentions from text
    found_days = []
    for full_name, abbrev in day_mappings.items():
        if full_name in text_lower:
            if abbrev not in found_days:
                found_days.append(abbrev)

    # Order by week (mon -> sun)
    day_order = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    found_days.sort(key=lambda d: day_order.index(d))

    return found_days


def generate_event_dates(
    start_date: date,
    days_of_week: List[str],
    num_weeks: int = 4
) -> List[date]:
    """
    Generate list of dates for recurring events.

    Pure function: Given a start date and days of week, generate all matching dates
    for the next N weeks.

    Args:
        start_date: Starting date (inclusive)
        days_of_week: List of 3-letter day abbreviations (e.g., ["mon", "wed", "fri"])
        num_weeks: Number of weeks ahead to generate (default 4)

    Returns:
        Sorted list of dates matching the specified days of week

    Examples:
        >>> start = date(2025, 1, 6)  # Monday
        >>> generate_event_dates(start, ["mon", "wed"], num_weeks=2)
        [date(2025, 1, 6), date(2025, 1, 8), date(2025, 1, 13), date(2025, 1, 15)]
    """
    if not days_of_week or num_weeks <= 0:
        return []

    # Map day abbreviations to weekday numbers (0=Monday, 6=Sunday)
    day_to_weekday = {
        "mon": 0, "tue": 1, "wed": 2, "thu": 3,
        "fri": 4, "sat": 5, "sun": 6
    }

    target_weekdays = set()
    for day in days_of_week:
        if day in day_to_weekday:
            target_weekdays.add(day_to_weekday[day])

    if not target_weekdays:
        return []

    # Generate dates
    dates = []
    end_date = start_date + timedelta(weeks=num_weeks)

    current = start_date
    while current < end_date:
        if current.weekday() in target_weekdays:
            dates.append(current)
        current += timedelta(days=1)

    return dates


def format_time_for_calendar(time_str: str) -> Optional[str]:
    """
    Parse and validate time string, return in HH:MM 24-hour format.

    Examples:
        "7:30am" -> "07:30"
        "7:30 AM" -> "07:30"
        "19:30" -> "19:30"
        "7pm" -> "19:00"
        "7.30" -> "07:30"  (European format with dots)

    Args:
        time_str: Time in various formats (12-hour or 24-hour)

    Returns:
        Time in HH:MM 24-hour format, or None if invalid
    """
    if not time_str:
        return None

    time_str = time_str.strip().lower()

    # Support European format with dots (7.30 -> 7:30)
    time_str = time_str.replace('.', ':')

    # Try 24-hour format first (HH:MM)
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        try:
            parsed = datetime.strptime(time_str, '%H:%M')
            return parsed.strftime('%H:%M')
        except ValueError:
            return None

    # Try 12-hour format with am/pm
    # Patterns: "7:30am", "7:30 am", "7am"
    match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        meridiem = match.group(3)

        if hour < 1 or hour > 12 or minute < 0 or minute > 59:
            return None

        # Convert to 24-hour
        if meridiem == 'pm' and hour != 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


def validate_calendar_config(
    recurring_days: str,
    session_time_start: str,
    session_time_end: str
) -> Dict[str, str]:
    """
    Validate calendar configuration before saving.

    Returns:
        Dict with "valid": bool and "error": Optional[str]
    """
    # Parse days
    days = parse_recurring_days(recurring_days)
    if not days:
        return {"valid": False, "error": "No valid days found in recurring pattern"}

    # Parse and validate times
    start_time = format_time_for_calendar(session_time_start)
    if not start_time:
        return {"valid": False, "error": f"Invalid start time format: {session_time_start}"}

    end_time = format_time_for_calendar(session_time_end)
    if not end_time:
        return {"valid": False, "error": f"Invalid end time format: {session_time_end}"}

    # Validate end time is after start time
    if end_time <= start_time:
        return {"valid": False, "error": "End time must be after start time"}

    return {
        "valid": True,
        "parsed_days": days,
        "formatted_start": start_time,
        "formatted_end": end_time
    }
