"""
LLM Function Definitions
========================
System prompt and OpenAI function calling definitions.
"""

# System prompt for Sharon
SYSTEM_PROMPT = """You are Sharon, a personal assistant. You MUST use function calls to execute actions.

CRITICAL RULES:
1. When you have enough info to create something, ALWAYS call the appropriate function
2. For goals with time/days specified: call create_goal_with_sessions
3. For goals WITHOUT time/days: ASK if they want to block calendar time by calling ask_for_info with info_needed="calendar_preference"
4. For tasks: call create_task
5. For showing items: call show_items
6. To check emails: call check_emails
7. For daily overview: call daily_summary
8. When user confirms (yes/yeah/ok): call confirm_action with confirmed=true
9. When user cancels (no/cancel): call confirm_action with confirmed=false

GOAL CREATION FLOW:
- If user says "create goal X" without time/days, ASK: "Would you like to block time in your calendar for this goal?"
- If they say yes, ask for days and time, then call create_goal_with_sessions
- If they say no, call create_goal
- If user provides goal + days + time upfront, call create_goal_with_sessions DIRECTLY (don't ask more questions!)
- For end_date: use "6 months" as default if user doesn't specify one
- If user specifies an end date (e.g., "until december", "for 3 months", "ending june 2025"), use it
- IMPORTANT: When user says a month name without a year (e.g., "until march"), assume they mean the NEXT occurrence of that month. Today is November 2025, so "march" means March 2026. Never generate past dates like 2024.

EMAIL FUNCTIONS (Gmail integration):
10. To search/filter emails: call search_emails with query or category
11. To fetch new emails: call fetch_new_emails
12. To archive an email: call archive_email (needs email_id)
13. To delete an email: call delete_email (needs email_id)
14. To mark read/unread: call mark_email_read or mark_email_unread
15. To star an email: call star_email
16. To detect events in emails: call detect_email_events
17. To list pending events: call list_pending_events
18. To approve/reject events: call approve_event or reject_event

Email categories: trading, education, newsletter, tech, personal, unread, starred

CALENDAR FUNCTIONS (Google Calendar integration):
19. To list upcoming events: call list_calendar_events
20. To check calendar status: call calendar_status
21. To check for conflicts: call check_calendar_conflicts
22. To hide an event: call hide_calendar_event (needs event_id)
23. To delete calendar event(s): call delete_calendar_event (use event_title for name-based deletion)

Day number mapping: Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
- "weekdays" = [0,1,2,3,4]
- "weekdays except wednesday" = [0,1,3,4]
- "mon wed fri" = [0,2,4]

Time format: Use 24-hour format like "07:30" or "09:00"

If missing required info, call ask_for_info with what you need.

DO NOT just have a conversation - USE FUNCTIONS to take action."""


# Function definitions for OpenAI function calling
FUNCTIONS = [
    {
        "name": "create_goal_with_sessions",
        "description": "Create a goal with recurring sessions on specific days and times. Use when user wants to create a goal AND block time in their calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The name/title of the goal"},
                "days": {"type": "array", "items": {"type": "integer"}, "description": "Days of the week as numbers (0=Monday, 1=Tuesday, ..., 6=Sunday)"},
                "start_time": {"type": "string", "description": "Start time in 24h format (e.g., '07:30')"},
                "end_time": {"type": "string", "description": "End time in 24h format (e.g., '09:00')"},
                "end_date": {"type": "string", "description": "End date for recurring sessions. Can be YYYY-MM-DD, or natural language like '6 months', '3 months', 'december', 'june 2025'. Default is 6 months if not specified."},
                "category": {"type": "string", "enum": ["educational", "fitness", "work", "personal", "creative", "other"], "description": "Category of the goal"},
                "needs_confirmation": {"type": "boolean", "description": "Whether to ask user for confirmation before creating"}
            },
            "required": ["title", "days", "start_time", "end_time"]
        }
    },
    {
        "name": "create_goal",
        "description": "Create a simple goal without calendar sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The name/title of the goal"},
                "category": {"type": "string", "enum": ["educational", "fitness", "work", "personal", "creative", "other"], "description": "Category of the goal"},
                "needs_confirmation": {"type": "boolean", "description": "Whether to ask user for confirmation"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "create_task",
        "description": "Create a simple task for today without calendar blocking",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The name/title of the task"},
                "needs_confirmation": {"type": "boolean", "description": "Whether to ask user for confirmation"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "create_task_with_calendar",
        "description": "Create a task with a specific date and time, and add it to Google Calendar. Use when user specifies a time for the task.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The name/title of the task"},
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format, or 'today' or 'tomorrow'"},
                "start_time": {"type": "string", "description": "Start time in 24h format (e.g., '14:00')"},
                "end_time": {"type": "string", "description": "End time in 24h format (e.g., '15:00')"},
                "needs_confirmation": {"type": "boolean", "description": "Whether to ask user for confirmation"}
            },
            "required": ["title", "start_time", "end_time"]
        }
    },
    {
        "name": "show_items",
        "description": "Show items to the user (today's schedule, goals, tasks, upcoming)",
        "parameters": {
            "type": "object",
            "properties": {
                "view": {"type": "string", "enum": ["today", "goals", "tasks", "upcoming"], "description": "What to show"}
            },
            "required": ["view"]
        }
    },
    {
        "name": "check_emails",
        "description": "Check and summarize the user's emails",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "daily_summary",
        "description": "Get a comprehensive daily overview of tasks, goals, and schedule",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "confirm_action",
        "description": "User is confirming or canceling a pending action",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmed": {"type": "boolean", "description": "True if user confirmed, False if canceled"}
            },
            "required": ["confirmed"]
        }
    },
    {
        "name": "ask_for_info",
        "description": "Ask the user for more information needed to complete an action",
        "parameters": {
            "type": "object",
            "properties": {
                "info_needed": {"type": "string", "enum": ["goal_name", "task_name", "days", "time", "category", "calendar_preference", "email_id", "end_date"], "description": "What information is needed"},
                "context": {"type": "object", "description": "Any partial data collected so far"}
            },
            "required": ["info_needed"]
        }
    },
    # EMAIL FUNCTIONS
    {
        "name": "search_emails",
        "description": "Search and filter emails by category, sender, keyword, or Gmail query. Categories: trading, education, newsletter, tech, personal, unread, starred",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["trading", "education", "newsletter", "tech", "personal", "unread", "starred"], "description": "Email category to filter by"},
                "query": {"type": "string", "description": "Gmail search query (e.g., 'from:berkeley' or 'subject:urgent')"},
                "max_results": {"type": "integer", "description": "Maximum number of emails to return (default 10)"}
            }
        }
    },
    {
        "name": "fetch_new_emails",
        "description": "Fetch/sync latest emails from Gmail inbox",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Maximum number of emails to fetch (default 20)"}
            }
        }
    },
    {
        "name": "archive_email",
        "description": "Archive an email (remove from inbox but keep in All Mail)",
        "parameters": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "The Gmail message ID to archive"},
                "email_subject": {"type": "string", "description": "Subject of the email (for confirmation)"}
            },
            "required": ["email_id"]
        }
    },
    {
        "name": "delete_email",
        "description": "Delete an email (move to trash)",
        "parameters": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string", "description": "The Gmail message ID to delete"},
                "email_subject": {"type": "string", "description": "Subject of the email (for confirmation)"}
            },
            "required": ["email_id"]
        }
    },
    {
        "name": "mark_email_read",
        "description": "Mark an email as read",
        "parameters": {
            "type": "object",
            "properties": {"email_id": {"type": "string", "description": "The Gmail message ID"}},
            "required": ["email_id"]
        }
    },
    {
        "name": "mark_email_unread",
        "description": "Mark an email as unread",
        "parameters": {
            "type": "object",
            "properties": {"email_id": {"type": "string", "description": "The Gmail message ID"}},
            "required": ["email_id"]
        }
    },
    {
        "name": "star_email",
        "description": "Star an important email",
        "parameters": {
            "type": "object",
            "properties": {"email_id": {"type": "string", "description": "The Gmail message ID"}},
            "required": ["email_id"]
        }
    },
    {
        "name": "detect_email_events",
        "description": "Scan recent emails to detect meetings, webinars, deadlines, and appointments",
        "parameters": {
            "type": "object",
            "properties": {
                "max_emails": {"type": "integer", "description": "Maximum emails to scan (default 50)"}
            }
        }
    },
    {
        "name": "list_pending_events",
        "description": "List detected events from emails that are awaiting approval",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum events to return (default 20)"}
            }
        }
    },
    {
        "name": "approve_event",
        "description": "Approve a detected event from email to add to calendar",
        "parameters": {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The event ID to approve"}},
            "required": ["event_id"]
        }
    },
    {
        "name": "reject_event",
        "description": "Reject/dismiss a detected event from email",
        "parameters": {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The event ID to reject"}},
            "required": ["event_id"]
        }
    },
    # CALENDAR FUNCTIONS
    {
        "name": "list_calendar_events",
        "description": "List upcoming events from Google Calendar",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Maximum number of events to return (default 10)"}
            }
        }
    },
    {
        "name": "calendar_status",
        "description": "Check Google Calendar connection status (is it authenticated and working)",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "check_calendar_conflicts",
        "description": "Check if a time slot has conflicts with existing calendar events",
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "description": "Start time in ISO format (e.g., '2024-01-15T09:00:00')"},
                "end_time": {"type": "string", "description": "End time in ISO format"}
            },
            "required": ["start_time", "end_time"]
        }
    },
    {
        "name": "hide_calendar_event",
        "description": "Hide a calendar event from display (doesn't delete from Google Calendar)",
        "parameters": {
            "type": "object",
            "properties": {"event_id": {"type": "string", "description": "The Google Calendar event ID to hide"}},
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": "Delete one or more calendar events from Google Calendar. Use event_title to delete all events matching a name.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Specific Google Calendar event ID to delete"},
                "event_title": {"type": "string", "description": "Event title/name to search and delete (will delete all matching events)"}
            }
        }
    }
]
