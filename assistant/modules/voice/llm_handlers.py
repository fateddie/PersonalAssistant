"""
LLM Function Call Handlers
==========================
Process function calls from OpenAI and return structured responses.
"""

from typing import Dict, Optional


def process_function_call(function_name: str, args: Dict, assistant_text: Optional[str]) -> Dict:
    """Process the function call from LLM and return structured response."""

    response_text = assistant_text or ""

    # GOAL/TASK HANDLERS
    if function_name == "create_goal_with_sessions":
        return _handle_create_goal_with_sessions(args, response_text)
    elif function_name == "create_goal":
        return _handle_create_goal(args, response_text)
    elif function_name == "create_task":
        return _handle_create_task(args, response_text)
    elif function_name == "create_task_with_calendar":
        return _handle_create_task_with_calendar(args, response_text)

    # VIEW HANDLERS
    elif function_name == "show_items":
        return _handle_show_items(args, response_text)
    elif function_name == "check_emails":
        return _handle_check_emails(response_text)
    elif function_name == "daily_summary":
        return _handle_daily_summary(response_text)

    # CONFIRMATION HANDLERS
    elif function_name == "confirm_action":
        return _handle_confirm_action(args, response_text)
    elif function_name == "ask_for_info":
        return _handle_ask_for_info(args, response_text)

    # EMAIL HANDLERS
    elif function_name == "search_emails":
        return _handle_search_emails(args, response_text)
    elif function_name == "fetch_new_emails":
        return _handle_fetch_new_emails(args, response_text)
    elif function_name == "archive_email":
        return _handle_archive_email(args, response_text)
    elif function_name == "delete_email":
        return _handle_delete_email(args, response_text)
    elif function_name == "mark_email_read":
        return _handle_mark_email_read(args, response_text)
    elif function_name == "mark_email_unread":
        return _handle_mark_email_unread(args, response_text)
    elif function_name == "star_email":
        return _handle_star_email(args, response_text)
    elif function_name == "detect_email_events":
        return _handle_detect_email_events(args, response_text)
    elif function_name == "list_pending_events":
        return _handle_list_pending_events(args, response_text)
    elif function_name == "approve_event":
        return _handle_approve_event(args, response_text)
    elif function_name == "reject_event":
        return _handle_reject_event(args, response_text)

    # CALENDAR HANDLERS
    elif function_name == "list_calendar_events":
        return _handle_list_calendar_events(args, response_text)
    elif function_name == "calendar_status":
        return _handle_calendar_status(response_text)
    elif function_name == "check_calendar_conflicts":
        return _handle_check_calendar_conflicts(args, response_text)
    elif function_name == "hide_calendar_event":
        return _handle_hide_calendar_event(args, response_text)
    elif function_name == "delete_calendar_event":
        return _handle_delete_calendar_event(args, response_text)

    # Unknown function
    return {
        "action": "unknown",
        "response_text": response_text
        or "I'm not sure what you want me to do. Could you rephrase?",
        "needs_confirmation": False,
        "pending_data": None,
        "view": None,
    }


# GOAL/TASK HANDLERS


def _handle_create_goal_with_sessions(args: Dict, response_text: str) -> Dict:
    title = args.get("title", "").title()
    days = args.get("days", [])
    start_time = args.get("start_time", "09:00")
    end_time = args.get("end_time", "10:00")
    end_date = args.get("end_date", "6 months")
    category = args.get("category", "other")
    needs_confirmation = args.get("needs_confirmation", True)

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days_str = ", ".join(day_names[d] for d in days) if days else "no days"
    if days == [0, 1, 2, 3, 4]:
        days_str = "weekdays"

    if not response_text:
        response_text = f"I'll create goal **'{title}'** ({category}) with sessions on **{days_str}** from **{start_time}** to **{end_time}** for **{end_date}** and add them to your Google Calendar. Confirm?"

    return {
        "action": "create_goal_with_sessions",
        "response_text": response_text,
        "needs_confirmation": needs_confirmation,
        "pending_data": {
            "title": title,
            "days": days,
            "start_time": start_time,
            "end_time": end_time,
            "end_date": end_date,
            "category": category,
        },
        "view": None,
    }


def _handle_create_goal(args: Dict, response_text: str) -> Dict:
    title = args.get("title", "").title()
    category = args.get("category")
    needs_confirmation = args.get("needs_confirmation", True)

    if not response_text:
        response_text = f"I'll create goal **'{title}'**"
        if category:
            response_text += f" ({category})"
        response_text += ". Confirm?"

    return {
        "action": "create_goal",
        "response_text": response_text,
        "needs_confirmation": needs_confirmation,
        "pending_data": {"title": title, "category": category},
        "view": None,
    }


def _handle_create_task(args: Dict, response_text: str) -> Dict:
    title = args.get("title", "").title()
    needs_confirmation = args.get("needs_confirmation", True)

    if not response_text:
        response_text = f"I'll create task **'{title}'** for today. Confirm?"

    return {
        "action": "create_task",
        "response_text": response_text,
        "needs_confirmation": needs_confirmation,
        "pending_data": {"task_title": title},
        "view": None,
    }


def _handle_create_task_with_calendar(args: Dict, response_text: str) -> Dict:
    title = args.get("title", "").title()
    task_date = args.get("date", "today")
    start_time = args.get("start_time", "09:00")
    end_time = args.get("end_time", "10:00")
    needs_confirmation = args.get("needs_confirmation", True)

    date_display = task_date if task_date in ["today", "tomorrow"] else task_date

    if not response_text:
        response_text = f"I'll create task **'{title}'** for **{date_display}** from **{start_time}** to **{end_time}** and add it to your Google Calendar. Confirm?"

    return {
        "action": "create_task_with_calendar",
        "response_text": response_text,
        "needs_confirmation": needs_confirmation,
        "pending_data": {
            "task_title": title,
            "date": task_date,
            "start_time": start_time,
            "end_time": end_time,
        },
        "view": None,
    }


# VIEW HANDLERS


def _handle_show_items(args: Dict, response_text: str) -> Dict:
    view = args.get("view", "today")
    view_messages = {
        "today": "Here's what's on your schedule for today:",
        "goals": "Here are your current goals:",
        "tasks": "Here are your tasks:",
        "upcoming": "Here's what's coming up:",
    }
    return {
        "action": "show",
        "response_text": response_text or view_messages.get(view, "Here's your schedule:"),
        "needs_confirmation": False,
        "pending_data": None,
        "view": view,
    }


def _handle_check_emails(response_text: str) -> Dict:
    return {
        "action": "check_email",
        "response_text": response_text
        or "Let me check your emails and summarize what's important...",
        "needs_confirmation": False,
        "pending_data": None,
        "view": None,
    }


def _handle_daily_summary(response_text: str) -> Dict:
    return {
        "action": "daily_summary",
        "response_text": response_text or "Here's your daily overview:",
        "needs_confirmation": False,
        "pending_data": None,
        "view": None,
    }


# CONFIRMATION HANDLERS


def _handle_confirm_action(args: Dict, response_text: str) -> Dict:
    confirmed = args.get("confirmed", False)
    return {
        "action": "confirm_yes" if confirmed else "confirm_no",
        "response_text": response_text
        or ("Let me do that for you." if confirmed else "Okay, cancelled."),
        "needs_confirmation": False,
        "pending_data": None,
        "view": None,
    }


def _handle_ask_for_info(args: Dict, response_text: str) -> Dict:
    info_needed = args.get("info_needed", "")
    context = args.get("context", {})
    prompts = {
        "goal_name": "What would you like to call this goal?",
        "task_name": "What would you like to call this task?",
        "days": "What days would you like? (e.g., 'weekdays', 'mon wed fri', 'weekdays except wednesday')",
        "time": "What time? (e.g., '7:30-9am', '9 to 10:30')",
        "category": "What category? (educational, fitness, work, personal, creative, other)",
        "calendar_preference": "Would you like to block time in your calendar for this goal?",
        "email_id": "Which email? Please search for it first so I can get the ID.",
        "end_date": "How long would you like this to run? (e.g., '6 months', 'until March 2026', 'for 3 months')",
    }
    return {
        "action": "need_more_info",
        "response_text": response_text or prompts.get(info_needed, "Can you tell me more?"),
        "needs_confirmation": False,
        "pending_data": context,
        "view": None,
        "info_needed": info_needed,
    }


# EMAIL HANDLERS


def _handle_search_emails(args: Dict, response_text: str) -> Dict:
    category = args.get("category")
    query = args.get("query", "")
    max_results = args.get("max_results", 10)
    return {
        "action": "search_emails",
        "response_text": response_text
        or f"Searching emails{f' in {category}' if category else ''}...",
        "needs_confirmation": False,
        "pending_data": {"category": category, "query": query, "max_results": max_results},
        "view": None,
    }


def _handle_fetch_new_emails(args: Dict, response_text: str) -> Dict:
    max_results = args.get("max_results", 20)
    return {
        "action": "fetch_new_emails",
        "response_text": response_text or "Fetching new emails from Gmail...",
        "needs_confirmation": False,
        "pending_data": {"max_results": max_results},
        "view": None,
    }


def _handle_archive_email(args: Dict, response_text: str) -> Dict:
    email_id = args.get("email_id")
    email_subject = args.get("email_subject", "")
    return {
        "action": "archive_email",
        "response_text": response_text
        or f"I'll archive{f' \"{email_subject}\"' if email_subject else ' this email'}. Confirm?",
        "needs_confirmation": True,
        "pending_data": {"email_id": email_id, "email_subject": email_subject},
        "view": None,
    }


def _handle_delete_email(args: Dict, response_text: str) -> Dict:
    email_id = args.get("email_id")
    email_subject = args.get("email_subject", "")
    return {
        "action": "delete_email",
        "response_text": response_text
        or f"I'll delete{f' \"{email_subject}\"' if email_subject else ' this email'}. Confirm?",
        "needs_confirmation": True,
        "pending_data": {"email_id": email_id, "email_subject": email_subject},
        "view": None,
    }


def _handle_mark_email_read(args: Dict, response_text: str) -> Dict:
    return {
        "action": "mark_email_read",
        "response_text": response_text or "Marking email as read...",
        "needs_confirmation": False,
        "pending_data": {"email_id": args.get("email_id")},
        "view": None,
    }


def _handle_mark_email_unread(args: Dict, response_text: str) -> Dict:
    return {
        "action": "mark_email_unread",
        "response_text": response_text or "Marking email as unread...",
        "needs_confirmation": False,
        "pending_data": {"email_id": args.get("email_id")},
        "view": None,
    }


def _handle_star_email(args: Dict, response_text: str) -> Dict:
    return {
        "action": "star_email",
        "response_text": response_text or "Starring email...",
        "needs_confirmation": False,
        "pending_data": {"email_id": args.get("email_id")},
        "view": None,
    }


def _handle_detect_email_events(args: Dict, response_text: str) -> Dict:
    return {
        "action": "detect_email_events",
        "response_text": response_text
        or "Scanning emails for meetings, webinars, and deadlines...",
        "needs_confirmation": False,
        "pending_data": {"max_emails": args.get("max_emails", 50)},
        "view": None,
    }


def _handle_list_pending_events(args: Dict, response_text: str) -> Dict:
    return {
        "action": "list_pending_events",
        "response_text": response_text or "Here are the events detected from your emails:",
        "needs_confirmation": False,
        "pending_data": {"limit": args.get("limit", 20)},
        "view": None,
    }


def _handle_approve_event(args: Dict, response_text: str) -> Dict:
    return {
        "action": "approve_event",
        "response_text": response_text or "Approving event...",
        "needs_confirmation": False,
        "pending_data": {"event_id": args.get("event_id")},
        "view": None,
    }


def _handle_reject_event(args: Dict, response_text: str) -> Dict:
    return {
        "action": "reject_event",
        "response_text": response_text or "Rejecting event...",
        "needs_confirmation": False,
        "pending_data": {"event_id": args.get("event_id")},
        "view": None,
    }


# CALENDAR HANDLERS


def _handle_list_calendar_events(args: Dict, response_text: str) -> Dict:
    return {
        "action": "list_calendar_events",
        "response_text": response_text or "Here are your upcoming calendar events:",
        "needs_confirmation": False,
        "pending_data": {"max_results": args.get("max_results", 10)},
        "view": None,
    }


def _handle_calendar_status(response_text: str) -> Dict:
    return {
        "action": "calendar_status",
        "response_text": response_text or "Checking calendar status...",
        "needs_confirmation": False,
        "pending_data": {},
        "view": None,
    }


def _handle_check_calendar_conflicts(args: Dict, response_text: str) -> Dict:
    return {
        "action": "check_calendar_conflicts",
        "response_text": response_text or "Checking for conflicts...",
        "needs_confirmation": False,
        "pending_data": {"start_time": args.get("start_time"), "end_time": args.get("end_time")},
        "view": None,
    }


def _handle_hide_calendar_event(args: Dict, response_text: str) -> Dict:
    return {
        "action": "hide_calendar_event",
        "response_text": response_text or "I'll hide this event from display. Confirm?",
        "needs_confirmation": True,
        "pending_data": {"event_id": args.get("event_id")},
        "view": None,
    }


def _handle_delete_calendar_event(args: Dict, response_text: str) -> Dict:
    event_id = args.get("event_id")
    event_title = args.get("event_title")

    if event_title:
        msg = f'I\'ll delete all calendar events named **"{event_title}"** from Google Calendar. Confirm?'
    elif event_id:
        msg = "I'll delete this calendar event from Google Calendar. Confirm?"
    else:
        msg = "I'll delete this calendar event. Confirm?"

    return {
        "action": "delete_calendar_event",
        "response_text": response_text or msg,
        "needs_confirmation": True,
        "pending_data": {"event_id": event_id, "event_title": event_title},
        "view": None,
    }
